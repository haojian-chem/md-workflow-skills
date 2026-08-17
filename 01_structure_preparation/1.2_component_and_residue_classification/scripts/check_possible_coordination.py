#!/usr/bin/env python3
"""Check possible metal coordination and apply the result to current observations."""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationToolError,
    parse_structure,
    read_yaml_strict,
    require_sha256,
    sha256_file,
    validate_document,
    validate_possible_coordination,
    verify_source_format,
)
from explicit_relations import collect_explicit_relations, explicit_evidence_for_pair
from observation_state import (
    apply_relation_result,
    commit_yaml_pair,
    load_relation_decisions,
    observations_lock,
)
from selection_identity import coordination_relation_id, endpoint_id_from_source_identity
from structure_records import (
    AtomRecord,
    ResidueRecord,
    atoms_matching,
    build_chain_index_resolver,
    collect_selected_model,
    current_residue_identity,
    distance_angstrom,
    endpoint_dict,
    resolve_chain_index,
    source_residue_identity,
)

VERSION = "1.1.0"


def _required_mapping(document: dict[str, Any], key: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise ClassificationToolError(f"config field {key!r} must be a mapping")
    return value


def _required_path(mapping: dict[str, Any], key: str) -> Path:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ClassificationToolError(f"config field {key!r} must be a non-empty path")
    return Path(value).resolve()


def _nullable_path(mapping: dict[str, Any], key: str) -> Path | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ClassificationToolError(f"config field {key!r} must be null or a path")
    return Path(value).resolve()


def _residue_chain_index(
    resolver: dict[tuple[str | None, str, str | None, str], int],
    residue: ResidueRecord,
) -> int:
    exact = (
        residue.source_chain_id,
        residue.source_resid_number,
        residue.insertion_code,
        residue.residue_name,
    )
    if exact in resolver:
        return resolver[exact]
    grouped = (None, "*", None, residue.residue_name)
    if grouped in resolver:
        return resolver[grouped]
    raise ClassificationToolError(
        "classification observations do not provide chain_index for "
        f"{residue.source_chain_id}:{residue.source_resid_number}:"
        f"{residue.residue_name}"
    )


def _issue_entry(
    endpoint_role: str,
    residue: ResidueRecord,
    atom_name: str,
    issue_type: str,
    resolver: dict[tuple[str | None, str, str | None, str], int],
) -> dict[str, Any]:
    return {
        "endpoint_role": endpoint_role,
        "chain_index": _residue_chain_index(resolver, residue),
        "source_identity": source_residue_identity(residue),
        "current_identity": current_residue_identity(residue),
        "source_chain_id": residue.source_chain_id,
        "source_resid": {
            "number": residue.source_resid_number,
            "insertion_code": residue.insertion_code,
        },
        "residue_name": residue.residue_name,
        "atom_name": atom_name,
        "issue_type": issue_type,
    }


def _pair_candidates(metals: list[AtomRecord], donors: list[AtomRecord]):
    seen: set[tuple[tuple, tuple]] = set()
    for metal, donor in itertools.product(metals, donors):
        if metal.atom_key == donor.atom_key or metal.base_atom_key == donor.base_atom_key:
            continue
        key = (metal.atom_key, donor.atom_key)
        if key in seen:
            continue
        seen.add(key)
        yield metal, donor


def _explicit_summary(evidence) -> dict[str, Any]:
    if not evidence:
        return {"status": "ABSENT", "source_type": None, "relation_type": None}
    source_types = sorted({item.source_type for item in evidence})
    relation_types = sorted({item.relation_type for item in evidence})
    return {
        "status": "PRESENT" if len(relation_types) == 1 else "AMBIGUOUS",
        "source_type": ",".join(source_types),
        "relation_type": (
            relation_types[0]
            if len(relation_types) == 1
            else "MULTIPLE:" + ",".join(relation_types)
        ),
    }


def _range_status(distance: float, minimum: float, maximum: float) -> str:
    if distance < minimum:
        return "BELOW_MINIMUM"
    if distance > maximum:
        return "ABOVE_MAXIMUM"
    return "WITHIN_RANGE"


def _element_issue(atom: AtomRecord, expected: str) -> str | None:
    if atom.element is None:
        return "ELEMENT_UNRESOLVED"
    if atom.element != expected:
        return "ELEMENT_MISMATCH"
    return None


def _application_status(status: str, promote: bool) -> str:
    if not promote:
        return "NOT_APPLICABLE"
    if status == "CONFIRMED_BY_STRUCTURE":
        return "ELIGIBLE"
    if status == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE":
        return "PENDING_CONFIRMATION"
    return "NOT_APPLICABLE"


def _relation_id(metal: dict[str, Any], donor: dict[str, Any]) -> str:
    return coordination_relation_id(
        endpoint_id_from_source_identity(metal["source_identity"]),
        endpoint_id_from_source_identity(donor["source_identity"]),
    )


def _not_performed_output(
    structure: dict[str, Any], observations_path: Path
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "status": "NOT_PERFORMED",
        "reason": "DEFINITION_FILE_NOT_PROVIDED",
        "input": {
            "structure_path": str(Path(structure["path"]).resolve()),
            "structure_sha256": structure["sha256"],
            "selected_model_id": str(structure["selected_model_id"]),
            "definition_path": None,
            "definition_sha256": None,
            "observations_path": str(observations_path),
        },
        "definition_results": [],
    }


def build_result(
    config: dict[str, Any],
    script_dir: Path,
    observations: dict[str, Any],
) -> tuple[dict[str, Any], Path, Path]:
    structure_config = _required_mapping(config, "structure")
    definition_config = _required_mapping(config, "possible_coordination")
    observations_config = _required_mapping(config, "classification_observations")
    output_config = _required_mapping(config, "output")

    structure_path = _required_path(structure_config, "path")
    structure_hash = str(structure_config.get("sha256", ""))
    source_format = str(structure_config.get("source_format", ""))
    selected_model_id = str(structure_config.get("selected_model_id", ""))
    require_sha256(structure_path, structure_hash)
    obs_input = observations.get("input", {})
    if (
        obs_input.get("structure_sha256") != structure_hash
        or str(obs_input.get("selected_model_id")) != selected_model_id
    ):
        raise ClassificationToolError(
            "classification observations do not match structure and selected model"
        )

    observations_path = _required_path(observations_config, "path")
    output_path = _required_path(output_config, "path")
    output_schema = Path(
        output_config.get(
            "schema",
            script_dir.parent / "schemas/possible_coordination_result.schema.yaml",
        )
    ).resolve()
    definition_path = _nullable_path(definition_config, "path")
    if definition_path is None:
        return _not_performed_output(structure_config, observations_path), output_path, output_schema

    definition_hash = str(definition_config.get("sha256", ""))
    require_sha256(definition_path, definition_hash)
    definition_schema = Path(
        definition_config.get(
            "schema",
            script_dir.parent / "schemas/possible_coordination.schema.yaml",
        )
    ).resolve()
    definitions = read_yaml_strict(definition_path)
    validate_document(definitions, definition_schema)
    validate_possible_coordination(definitions)

    structure = parse_structure(structure_path)
    verify_source_format(structure_path, structure, source_format)
    _model, residues, atoms_by_serial = collect_selected_model(structure, selected_model_id)
    residue_lookup = {residue.residue_key: residue for residue in residues}
    resolver = build_chain_index_resolver(observations)
    specific_relations, base_relations = collect_explicit_relations(
        structure, selected_model_id, residues, atoms_by_serial
    )

    definition_results: list[dict[str, Any]] = []
    for definition_index, definition in enumerate(definitions["possible_coordination"], start=1):
        metal_def, donor_def = definition["metal"], definition["donor"]
        metal_residues, metal_atoms, metal_missing = atoms_matching(
            residues, metal_def["residue_name"], metal_def["atom_name"]
        )
        donor_residues, donor_atoms, donor_missing = atoms_matching(
            residues, donor_def["residue_name"], donor_def["atom_name"]
        )
        missing_partner = None
        if not metal_residues and not donor_residues:
            missing_partner = "BOTH"
        elif not metal_residues:
            missing_partner = "METAL"
        elif not donor_residues:
            missing_partner = "DONOR"
        issue_instances = [
            *(
                _issue_entry("METAL", item, metal_def["atom_name"], "ATOM_NOT_FOUND", resolver)
                for item in metal_missing
            ),
            *(
                _issue_entry("DONOR", item, donor_def["atom_name"], "ATOM_NOT_FOUND", resolver)
                for item in donor_missing
            ),
        ]
        for role, atoms, definition_endpoint in (
            ("METAL", metal_atoms, metal_def),
            ("DONOR", donor_atoms, donor_def),
        ):
            for atom in atoms:
                issue = _element_issue(atom, definition_endpoint["element"])
                if issue:
                    issue_instances.append(
                        _issue_entry(
                            role,
                            residue_lookup[atom.residue_key],
                            atom.atom_name,
                            issue,
                            resolver,
                        )
                    )

        minimum = float(definition["distance_range_angstrom"]["minimum"])
        maximum = float(definition["distance_range_angstrom"]["maximum"])
        promote = bool(definition["topology_effect"]["promote_nonstandard_to_linked"])
        pair_results: list[dict[str, Any]] = []
        omitted_distances: list[float] = []
        considered_pair_count = 0
        if missing_partner is None:
            for metal, donor in _pair_candidates(metal_atoms, donor_atoms):
                considered_pair_count += 1
                metal_endpoint = endpoint_dict(
                    metal,
                    resolve_chain_index(resolver, metal),
                    include_element=True,
                    expected_element=metal_def["element"],
                )
                donor_endpoint = endpoint_dict(
                    donor,
                    resolve_chain_index(resolver, donor),
                    include_element=True,
                    expected_element=donor_def["element"],
                )
                evidence = explicit_evidence_for_pair(
                    metal, donor, specific_relations, base_relations
                )
                explicit = _explicit_summary(evidence)
                element_issue = _element_issue(metal, metal_def["element"]) or _element_issue(
                    donor, donor_def["element"]
                )
                metal_multiple = residue_lookup[metal.residue_key].has_multiple_conformations
                donor_multiple = residue_lookup[donor.residue_key].has_multiple_conformations
                altloc_specific = bool(evidence) and all(item.altloc_specific for item in evidence)
                if element_issue:
                    geometry = None
                    if evidence:
                        status = "COORDINATION_DEFINITION_CONFLICT"
                        detail = f"{element_issue}_WITH_EXPLICIT_RELATION"
                        confirmation_required = True
                    else:
                        status, detail, confirmation_required = element_issue, element_issue, False
                elif (metal_multiple or donor_multiple) and not altloc_specific:
                    geometry = None
                    status = "GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS"
                    detail = "MULTIPLE_CONFORMATIONS_PRESENT"
                    confirmation_required = False
                else:
                    distance = distance_angstrom(metal, donor)
                    range_status = _range_status(distance, minimum, maximum)
                    geometry = {
                        "distance_angstrom": round(distance, 6),
                        "configured_range": {"minimum": minimum, "maximum": maximum},
                        "range_status": range_status,
                    }
                    relation_types = {item.relation_type for item in evidence}
                    if evidence:
                        if relation_types == {"METAL_COORDINATION"} and range_status == "WITHIN_RANGE":
                            status, detail, confirmation_required = "CONFIRMED_BY_STRUCTURE", None, False
                        else:
                            status = "COORDINATION_DEFINITION_CONFLICT"
                            detail = (
                                "EXPLICIT_RELATION_TYPE_CONFLICT"
                                if relation_types != {"METAL_COORDINATION"}
                                else f"EXPLICIT_RELATION_{range_status}"
                            )
                            confirmation_required = True
                    elif range_status == "WITHIN_RANGE":
                        status, detail, confirmation_required = (
                            "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE", None, True
                        )
                    else:
                        status, detail, confirmation_required = (
                            "NOT_GEOMETRICALLY_SUPPORTED", range_status, False
                        )
                        if range_status == "ABOVE_MAXIMUM":
                            omitted_distances.append(distance)
                            continue
                pair_results.append(
                    {
                        "relation_id": _relation_id(metal_endpoint, donor_endpoint),
                        "metal": metal_endpoint,
                        "donor": donor_endpoint,
                        "explicit_coordination": explicit,
                        "geometry": geometry,
                        "status": status,
                        "detail": detail,
                        "confirmation_required": confirmation_required,
                        "topology_effect_evaluation": {
                            "promote_nonstandard_to_linked": promote,
                            "application_status": _application_status(status, promote),
                        },
                    }
                )
        definition_status = (
            "PARTNER_NOT_FOUND"
            if missing_partner is not None
            else "ATOM_NOT_FOUND"
            if not metal_atoms or not donor_atoms
            else "ELEMENT_ISSUES"
            if any(
                item["issue_type"] in {"ELEMENT_MISMATCH", "ELEMENT_UNRESOLVED"}
                for item in issue_instances
            )
            else "EVALUATED"
        )
        definition_results.append(
            {
                "definition_index": definition_index,
                "label": definition.get("label"),
                "definition": {
                    "metal": metal_def,
                    "donor": donor_def,
                    "distance_range_angstrom": {"minimum": minimum, "maximum": maximum},
                    "topology_effect": {"promote_nonstandard_to_linked": promote},
                },
                "definition_status": definition_status,
                "missing_partner": missing_partner,
                "matching_summary": {
                    "metal_residue_count": len(metal_residues),
                    "metal_atom_count": len(metal_atoms),
                    "donor_residue_count": len(donor_residues),
                    "donor_atom_count": len(donor_atoms),
                    "considered_pair_count": considered_pair_count,
                    "recorded_pair_count": len(pair_results),
                    "omitted_above_maximum_pair_count": len(omitted_distances),
                },
                "issue_instances": issue_instances,
                "pair_results": pair_results,
                "omitted_above_maximum_pairs": {
                    "count": len(omitted_distances),
                    "minimum_distance_angstrom": round(min(omitted_distances), 6) if omitted_distances else None,
                    "maximum_distance_angstrom": round(max(omitted_distances), 6) if omitted_distances else None,
                },
            }
        )
    if sha256_file(structure_path) != structure_hash:
        raise ClassificationToolError("input structure changed during coordination checking")
    return {
        "schema_version": "1.0",
        "status": "COMPLETED",
        "reason": None,
        "input": {
            "structure_path": str(structure_path),
            "structure_sha256": structure_hash,
            "selected_model_id": selected_model_id,
            "definition_path": str(definition_path),
            "definition_sha256": definition_hash,
            "observations_path": str(observations_path),
        },
        "definition_results": definition_results,
    }, output_path, output_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    try:
        config = read_yaml_strict(args.config.resolve())
        if not isinstance(config, dict):
            raise ClassificationToolError("config must be a YAML mapping")
        validate_document(
            config,
            script_dir.parent / "schemas/possible_coordination_check_config.schema.yaml",
        )
        observations_config = _required_mapping(config, "classification_observations")
        observations_path = _required_path(observations_config, "path")
        observations_schema = Path(
            observations_config.get(
                "schema",
                script_dir.parent / "schemas/classification_observations.schema.yaml",
            )
        ).resolve()
        with observations_lock(observations_path):
            observations = read_yaml_strict(observations_path)
            validate_document(observations, observations_schema)
            result, output_path, output_schema = build_result(config, script_dir, observations)
            validate_document(result, output_schema)
            decisions_config = config.get("relation_decisions")
            decisions_path = (
                _required_path(decisions_config, "path")
                if isinstance(decisions_config, dict)
                else None
            )
            decisions = load_relation_decisions(
                decisions_path,
                observations,
                Path(
                    decisions_config.get(
                        "schema",
                        script_dir.parent / "schemas/relation_decisions.schema.yaml",
                    )
                ).resolve()
                if isinstance(decisions_config, dict)
                else script_dir.parent / "schemas/relation_decisions.schema.yaml",
                validate_document,
            )
            updated = apply_relation_result(
                observations,
                result,
                "METAL_COORDINATION",
                output_path,
                decisions,
            )
            validate_document(updated, observations_schema)
            commit_yaml_pair(output_path, result, observations_path, updated)
        return 0
    except ClassificationToolError as exc:
        print(f"check_possible_coordination.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"check_possible_coordination.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

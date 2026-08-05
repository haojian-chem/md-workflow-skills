#!/usr/bin/env python3
"""Check possible covalent connections and apply the result to current observations."""
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
    validate_possible_connections,
    verify_source_format,
)
from explicit_relations import collect_explicit_relations, explicit_evidence_for_pair
from observation_state import (
    apply_relation_result,
    commit_yaml_pair,
    load_relation_decisions,
    observations_lock,
)
from selection_identity import (
    covalent_relation_id,
    endpoint_id_from_source_identity,
)
from structure_records import (
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
COVALENT_RELATION_TYPES = {"COVALENT", "DISULFIDE", "GLYCOSIDIC"}


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


def _missing_atom_entry(
    residue: ResidueRecord,
    atom_name: str,
    resolver: dict[tuple[str | None, str, str | None, str], int],
) -> dict[str, Any]:
    return {
        "chain_index": _residue_chain_index(resolver, residue),
        "source_identity": source_residue_identity(residue),
        "current_identity": current_residue_identity(residue),
        "source_chain_id": residue.source_chain_id,
        "source_resid": {
            "number": residue.source_resid_number,
            "insertion_code": residue.insertion_code,
        },
        "residue_name": residue.residue_name,
        "missing_atom_name": atom_name,
    }


def _pair_candidates(first_atoms: list, second_atoms: list, same_definition: bool):
    seen: set[tuple[tuple, tuple]] = set()
    raw_pairs = (
        itertools.combinations(first_atoms, 2)
        if same_definition
        else itertools.product(first_atoms, second_atoms)
    )
    for first, second in raw_pairs:
        if first.atom_key == second.atom_key or first.base_atom_key == second.base_atom_key:
            continue
        key = (
            (first.atom_key, second.atom_key)
            if first.atom_key <= second.atom_key
            else (second.atom_key, first.atom_key)
        )
        if key in seen:
            continue
        seen.add(key)
        yield first, second


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


def _relation_id(first: dict[str, Any], second: dict[str, Any]) -> str:
    return covalent_relation_id(
        endpoint_id_from_source_identity(first["source_identity"]),
        endpoint_id_from_source_identity(second["source_identity"]),
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
    definition_config = _required_mapping(config, "possible_connections")
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
            script_dir.parent / "schemas/possible_connections_result.schema.yaml",
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
            script_dir.parent / "schemas/possible_connections.schema.yaml",
        )
    ).resolve()
    definitions = read_yaml_strict(definition_path)
    validate_document(definitions, definition_schema)
    validate_possible_connections(definitions)

    structure = parse_structure(structure_path)
    verify_source_format(structure_path, structure, source_format)
    _model, residues, atoms_by_serial = collect_selected_model(structure, selected_model_id)
    residue_lookup = {residue.residue_key: residue for residue in residues}
    resolver = build_chain_index_resolver(observations)
    specific_relations, base_relations = collect_explicit_relations(
        structure, selected_model_id, residues, atoms_by_serial
    )

    definition_results: list[dict[str, Any]] = []
    for definition_index, definition in enumerate(definitions["possible_connections"], start=1):
        first_def, second_def = definition["partner_1"], definition["partner_2"]
        first_residues, first_atoms, first_missing = atoms_matching(
            residues, first_def["residue_name"], first_def["atom_name"]
        )
        second_residues, second_atoms, second_missing = atoms_matching(
            residues, second_def["residue_name"], second_def["atom_name"]
        )
        missing_partner = None
        if not first_residues and not second_residues:
            missing_partner = "BOTH"
        elif not first_residues:
            missing_partner = "PARTNER_1"
        elif not second_residues:
            missing_partner = "PARTNER_2"
        atom_not_found_instances = [
            *(
                _missing_atom_entry(item, first_def["atom_name"], resolver)
                for item in first_missing
            ),
            *(
                _missing_atom_entry(item, second_def["atom_name"], resolver)
                for item in second_missing
            ),
        ]
        minimum = float(definition["distance_range_angstrom"]["minimum"])
        maximum = float(definition["distance_range_angstrom"]["maximum"])
        pair_results: list[dict[str, Any]] = []
        omitted_distances: list[float] = []
        considered_pair_count = 0
        if missing_partner is None:
            for first, second in _pair_candidates(
                first_atoms, second_atoms, first_def == second_def
            ):
                considered_pair_count += 1
                first_endpoint = endpoint_dict(first, resolve_chain_index(resolver, first))
                second_endpoint = endpoint_dict(second, resolve_chain_index(resolver, second))
                evidence = explicit_evidence_for_pair(
                    first, second, specific_relations, base_relations
                )
                explicit = _explicit_summary(evidence)
                first_multiple = residue_lookup[first.residue_key].has_multiple_conformations
                second_multiple = residue_lookup[second.residue_key].has_multiple_conformations
                altloc_specific = bool(evidence) and all(item.altloc_specific for item in evidence)
                if (first_multiple or second_multiple) and not altloc_specific:
                    geometry = None
                    status = "GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS"
                    detail = "MULTIPLE_CONFORMATIONS_PRESENT"
                    confirmation_required = False
                    applicable = False
                else:
                    distance = distance_angstrom(first, second)
                    range_status = _range_status(distance, minimum, maximum)
                    geometry = {
                        "distance_angstrom": round(distance, 6),
                        "configured_range": {"minimum": minimum, "maximum": maximum},
                        "range_status": range_status,
                    }
                    relation_types = {item.relation_type for item in evidence}
                    if evidence:
                        if relation_types.issubset(COVALENT_RELATION_TYPES) and range_status == "WITHIN_RANGE":
                            status, detail, confirmation_required, applicable = (
                                "CONFIRMED_BY_STRUCTURE", None, False, True
                            )
                        else:
                            status = "CONNECTION_DEFINITION_CONFLICT"
                            detail = (
                                "EXPLICIT_RELATION_TYPE_CONFLICT"
                                if not relation_types.issubset(COVALENT_RELATION_TYPES)
                                else f"EXPLICIT_RELATION_{range_status}"
                            )
                            confirmation_required, applicable = True, False
                    elif range_status == "WITHIN_RANGE":
                        status, detail, confirmation_required, applicable = (
                            "GEOMETRY_SUPPORTED_CANDIDATE", None, True, False
                        )
                    else:
                        status, detail, confirmation_required, applicable = (
                            "NOT_GEOMETRICALLY_SUPPORTED", range_status, False, False
                        )
                        if range_status == "ABOVE_MAXIMUM":
                            omitted_distances.append(distance)
                            continue
                pair_results.append(
                    {
                        "relation_id": _relation_id(first_endpoint, second_endpoint),
                        "partner_1": first_endpoint,
                        "partner_2": second_endpoint,
                        "explicit_connection": explicit,
                        "geometry": geometry,
                        "status": status,
                        "detail": detail,
                        "confirmation_required": confirmation_required,
                        "topology_effect_candidate": {
                            "relation_type": "COVALENT_CONNECTION",
                            "applicable": applicable,
                        },
                    }
                )
        definition_status = (
            "PARTNER_NOT_FOUND"
            if missing_partner is not None
            else "ATOM_NOT_FOUND"
            if not first_atoms or not second_atoms
            else "EVALUATED"
        )
        definition_results.append(
            {
                "definition_index": definition_index,
                "label": definition.get("label"),
                "definition": {
                    "partner_1": first_def,
                    "partner_2": second_def,
                    "distance_range_angstrom": {"minimum": minimum, "maximum": maximum},
                },
                "definition_status": definition_status,
                "missing_partner": missing_partner,
                "matching_summary": {
                    "partner_1_residue_count": len(first_residues),
                    "partner_1_atom_count": len(first_atoms),
                    "partner_2_residue_count": len(second_residues),
                    "partner_2_atom_count": len(second_atoms),
                    "considered_pair_count": considered_pair_count,
                    "recorded_pair_count": len(pair_results),
                    "omitted_above_maximum_pair_count": len(omitted_distances),
                },
                "atom_not_found_instances": atom_not_found_instances,
                "pair_results": pair_results,
                "omitted_above_maximum_pairs": {
                    "count": len(omitted_distances),
                    "minimum_distance_angstrom": round(min(omitted_distances), 6) if omitted_distances else None,
                    "maximum_distance_angstrom": round(max(omitted_distances), 6) if omitted_distances else None,
                },
            }
        )
    if sha256_file(structure_path) != structure_hash:
        raise ClassificationToolError("input structure changed during connection checking")
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
            script_dir.parent / "schemas/possible_connections_check_config.schema.yaml",
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
            result, output_path, output_schema = build_result(
                config, script_dir, observations
            )
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
                "COVALENT_CONNECTION",
                output_path,
                decisions,
            )
            validate_document(updated, observations_schema)
            commit_yaml_pair(output_path, result, observations_path, updated)
        return 0
    except ClassificationToolError as exc:
        print(f"check_possible_connections.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"check_possible_connections.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

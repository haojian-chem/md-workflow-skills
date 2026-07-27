#!/usr/bin/env python3
"""Check project-defined possible metal coordination relationships."""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationError,
    atomic_yaml,
    distance_angstrom,
    format_float,
    load_yaml,
    normalize_element_symbol,
    require_hash,
    validate_document,
)
from relation_common import (
    atom_endpoint,
    collect_relation_residues,
    explicit_relation_index,
    geometry_range,
    matching_residues,
    pair_key,
)

VERSION = "1.0.0"


def _definition_key(item: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        item["metal"]["residue_name"],
        item["metal"]["atom_name"],
        item["donor"]["residue_name"],
        item["donor"]["atom_name"],
    )


def _participant_pairs(
    metals: list[dict[str, Any]], donors: list[dict[str, Any]]
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen: set[tuple[Any, ...]] = set()
    for metal_item, donor_item in itertools.product(metals, donors):
        key = (
            metal_item["residue"]["source_chain_id"],
            metal_item["residue"]["source_resid"]["number"],
            metal_item["residue"]["source_resid"]["insertion_code"],
            donor_item["residue"]["source_chain_id"],
            donor_item["residue"]["source_resid"]["number"],
            donor_item["residue"]["source_resid"]["insertion_code"],
        )
        if key in seen:
            continue
        seen.add(key)
        pairs.append((metal_item, donor_item))
    return pairs


def check(config: dict[str, Any]) -> dict[str, Any]:
    structure_cfg = config["structure"]
    structure_path = Path(structure_cfg["path"])
    structure_hash = require_hash(structure_path, structure_cfg.get("sha256"), "structure")
    selected_model_id = str(structure_cfg["selected_model_id"])

    observations_cfg = config["classification_observations"]
    observations_path = Path(observations_cfg["path"])
    observations_hash = require_hash(
        observations_path, observations_cfg.get("sha256"), "classification observations"
    )
    observations = load_yaml(observations_path)
    run_context = observations.get("run_context", {})
    if str(run_context.get("selected_model_id")) != selected_model_id:
        raise ClassificationError("selected model differs from classification observations")
    if run_context.get("input_structure_sha256") != structure_hash:
        raise ClassificationError("structure hash differs from classification observations")

    definition_cfg = config.get("possible_coordination") or {}
    if not definition_cfg.get("path"):
        return {
            "schema_version": "1.0",
            "tool": {"name": "check_possible_coordination", "version": VERSION},
            "status": "NOT_PERFORMED",
            "reason": "DEFINITION_FILE_NOT_PROVIDED",
            "input": {
                "structure_path": str(structure_path),
                "structure_sha256": structure_hash,
                "selected_model_id": selected_model_id,
                "definition_path": None,
                "definition_sha256": None,
                "observations_path": str(observations_path),
                "observations_sha256": observations_hash,
            },
            "definition_results": [],
            "summary": {"definition_count": 0, "confirmation_required_count": 0},
        }
    definition_path = Path(definition_cfg["path"])
    definition_hash = require_hash(
        definition_path, definition_cfg.get("sha256"), "possible coordination"
    )
    definitions_doc = load_yaml(definition_path)
    definitions = definitions_doc.get("possible_coordination", [])
    seen_definitions: set[tuple[str, str, str, str]] = set()
    for item in definitions:
        key = _definition_key(item)
        if key in seen_definitions:
            raise ClassificationError(f"DUPLICATE_COORDINATION_DEFINITION: {key}")
        seen_definitions.add(key)

    structure, model, residues, serial_map = collect_relation_residues(
        structure_path, selected_model_id, observations
    )
    explicit_index = explicit_relation_index(structure, model, residues, serial_map, structure_path)

    definition_results: list[dict[str, Any]] = []
    confirmation_count = 0
    for definition_index, definition in enumerate(definitions, start=1):
        metal_spec = definition["metal"]
        donor_spec = definition["donor"]
        expected_metal_element = normalize_element_symbol(metal_spec["element"])
        expected_donor_element = normalize_element_symbol(donor_spec["element"])
        minimum = float(definition["distance_range_angstrom"]["minimum"])
        maximum = float(definition["distance_range_angstrom"]["maximum"])
        if minimum < 0 or maximum <= minimum:
            raise ClassificationError(
                f"invalid distance range in definition {definition_index}: "
                f"minimum={minimum}, maximum={maximum}"
            )
        promote = bool(definition["topology_effect"]["promote_nonstandard_to_linked"])

        metal_valid, metal_missing = matching_residues(
            residues, metal_spec["residue_name"], metal_spec["atom_name"]
        )
        donor_valid, donor_missing = matching_residues(
            residues, donor_spec["residue_name"], donor_spec["atom_name"]
        )
        metal_residue_count = sum(
            1 for residue in residues if residue["residue_name"] == metal_spec["residue_name"]
        )
        donor_residue_count = sum(
            1 for residue in residues if residue["residue_name"] == donor_spec["residue_name"]
        )
        element_issues: list[dict[str, Any]] = []
        for role, participants, expected in (
            ("METAL", metal_valid, expected_metal_element),
            ("DONOR", donor_valid, expected_donor_element),
        ):
            for participant in participants:
                for atom in participant["atoms"]:
                    observed_element = normalize_element_symbol(atom.get("element"))
                    if observed_element != expected:
                        element_issues.append(
                            {
                                "role": role,
                                "endpoint": atom_endpoint(atom),
                                "expected_element": expected,
                                "observed_element": observed_element,
                                "status": "ELEMENT_UNRESOLVED"
                                if observed_element is None
                                else "ELEMENT_MISMATCH",
                            }
                        )

        result: dict[str, Any] = {
            "definition_index": definition_index,
            "label": definition.get("label"),
            "definition": definition,
            "matching_summary": {
                "metal_residue_count": metal_residue_count,
                "metal_atom_count": len(metal_valid),
                "donor_residue_count": donor_residue_count,
                "donor_atom_count": len(donor_valid),
                "evaluated_pair_count": 0,
            },
            "atom_not_found_instances": metal_missing + donor_missing,
            "element_issue_instances": element_issues,
            "pair_results": [],
            "omitted_above_maximum_pairs": {
                "count": 0,
                "minimum_distance_angstrom": None,
                "maximum_distance_angstrom": None,
            },
        }
        if metal_residue_count == 0 or donor_residue_count == 0:
            if metal_residue_count == 0 and donor_residue_count == 0:
                missing_partner = "BOTH"
            elif metal_residue_count == 0:
                missing_partner = "METAL"
            else:
                missing_partner = "DONOR"
            result.update(
                status="PARTNER_NOT_FOUND",
                missing_partner=missing_partner,
                confirmation_required=False,
            )
            definition_results.append(result)
            continue

        pairs = _participant_pairs(metal_valid, donor_valid)
        result["matching_summary"]["evaluated_pair_count"] = len(pairs)
        above_distances: list[float] = []
        for metal_item, donor_item in pairs:
            metal_residue = metal_item["residue"]
            donor_residue = donor_item["residue"]
            atom_pairs = [
                (metal_atom, donor_atom)
                for metal_atom in metal_item["atoms"]
                for donor_atom in donor_item["atoms"]
                if metal_atom is not donor_atom
            ]
            explicit_atom_pairs = [
                (metal_atom, donor_atom, explicit_index[pair_key(metal_atom, donor_atom)])
                for metal_atom, donor_atom in atom_pairs
                if pair_key(metal_atom, donor_atom) in explicit_index
            ]
            if explicit_atom_pairs:
                pairs_to_record = explicit_atom_pairs
            elif atom_pairs:
                pairs_to_record = [(atom_pairs[0][0], atom_pairs[0][1], [])]
            else:
                pairs_to_record = []
            if not pairs_to_record:
                continue
            if not explicit_atom_pairs and (
                metal_residue["multiple_conformations"]
                or donor_residue["multiple_conformations"]
                or len(atom_pairs) != 1
            ):
                metal_atom = metal_item["atoms"][0]
                donor_atom = donor_item["atoms"][0]
                result["pair_results"].append(
                    {
                        "metal": atom_endpoint(metal_atom),
                        "donor": atom_endpoint(donor_atom),
                        "explicit_coordination": {"status": "ABSENT", "records": []},
                        "element_observation": {
                            "metal_expected": expected_metal_element,
                            "metal_observed": metal_atom.get("element"),
                            "donor_expected": expected_donor_element,
                            "donor_observed": donor_atom.get("element"),
                        },
                        "geometry": {
                            "distance_angstrom": None,
                            "configured_range": {"minimum": minimum, "maximum": maximum},
                            "range_status": "NOT_EVALUATED",
                        },
                        "status": "GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS",
                        "confirmation_required": False,
                        "topology_effect_evaluation": {
                            "promote_nonstandard_to_linked": promote,
                            "application_status": "NOT_APPLICABLE",
                        },
                    }
                )
                continue

            for metal_atom, donor_atom, explicit_records in pairs_to_record:
                metal_observed = normalize_element_symbol(metal_atom.get("element"))
                donor_observed = normalize_element_symbol(donor_atom.get("element"))
                elements_resolved = metal_observed is not None and donor_observed is not None
                elements_match = (
                    metal_observed == expected_metal_element
                    and donor_observed == expected_donor_element
                )
                has_explicit = bool(explicit_records)
                explicit_types = {record["relation_type"] for record in explicit_records}
                explicit_is_coordination = "METAL_COORDINATION" in explicit_types

                if not elements_resolved or not elements_match:
                    status = (
                        "COORDINATION_DEFINITION_CONFLICT"
                        if has_explicit
                        else "ELEMENT_UNRESOLVED"
                        if not elements_resolved
                        else "ELEMENT_MISMATCH"
                    )
                    confirmation_required = has_explicit
                    confirmation_count += int(confirmation_required)
                    result["pair_results"].append(
                        {
                            "metal": atom_endpoint(metal_atom),
                            "donor": atom_endpoint(donor_atom),
                            "explicit_coordination": {
                                "status": "PRESENT" if has_explicit else "ABSENT",
                                "records": explicit_records,
                            },
                            "element_observation": {
                                "metal_expected": expected_metal_element,
                                "metal_observed": metal_observed,
                                "donor_expected": expected_donor_element,
                                "donor_observed": donor_observed,
                            },
                            "geometry": {
                                "distance_angstrom": None,
                                "configured_range": {"minimum": minimum, "maximum": maximum},
                                "range_status": "NOT_EVALUATED",
                            },
                            "status": status,
                            "conflict_type": "ELEMENT_MISMATCH_WITH_EXPLICIT_RELATION"
                            if has_explicit
                            else None,
                            "confirmation_required": confirmation_required,
                            "topology_effect_evaluation": {
                                "promote_nonstandard_to_linked": promote,
                                "application_status": "NOT_APPLICABLE",
                            },
                        }
                    )
                    continue

                distance = distance_angstrom(metal_atom["atom"], donor_atom["atom"])
                range_status = geometry_range(distance, minimum, maximum)
                if has_explicit:
                    status = (
                        "CONFIRMED_BY_STRUCTURE"
                        if explicit_is_coordination and range_status == "WITHIN_RANGE"
                        else "COORDINATION_DEFINITION_CONFLICT"
                    )
                    confirmation_required = status == "COORDINATION_DEFINITION_CONFLICT"
                    confirmation_count += int(confirmation_required)
                    application_status = (
                        "ELIGIBLE"
                        if status == "CONFIRMED_BY_STRUCTURE" and promote
                        else "NOT_APPLICABLE"
                    )
                    result["pair_results"].append(
                        {
                            "metal": atom_endpoint(metal_atom),
                            "donor": atom_endpoint(donor_atom),
                            "explicit_coordination": {
                                "status": "PRESENT",
                                "records": explicit_records,
                            },
                            "element_observation": {
                                "metal_expected": expected_metal_element,
                                "metal_observed": metal_observed,
                                "donor_expected": expected_donor_element,
                                "donor_observed": donor_observed,
                            },
                            "geometry": {
                                "distance_angstrom": format_float(distance),
                                "configured_range": {"minimum": minimum, "maximum": maximum},
                                "range_status": range_status,
                            },
                            "status": status,
                            "conflict_type": None
                            if status == "CONFIRMED_BY_STRUCTURE"
                            else "EXPLICIT_RELATION_OUTSIDE_DISTANCE_RANGE"
                            if explicit_is_coordination
                            else "EXPLICIT_RELATION_TYPE_AMBIGUOUS",
                            "confirmation_required": confirmation_required,
                            "topology_effect_evaluation": {
                                "promote_nonstandard_to_linked": promote,
                                "application_status": application_status,
                            },
                        }
                    )
                    continue

                if range_status == "WITHIN_RANGE":
                    status = "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"
                    confirmation_required = True
                    application_status = "PENDING_CONFIRMATION" if promote else "NOT_APPLICABLE"
                    confirmation_count += 1
                else:
                    status = "NOT_GEOMETRICALLY_SUPPORTED"
                    confirmation_required = False
                    application_status = "NOT_APPLICABLE"
                if range_status == "ABOVE_MAXIMUM":
                    above_distances.append(distance)
                    continue
                result["pair_results"].append(
                    {
                        "metal": atom_endpoint(metal_atom),
                        "donor": atom_endpoint(donor_atom),
                        "explicit_coordination": {"status": "ABSENT", "records": []},
                        "element_observation": {
                            "metal_expected": expected_metal_element,
                            "metal_observed": metal_observed,
                            "donor_expected": expected_donor_element,
                            "donor_observed": donor_observed,
                        },
                        "geometry": {
                            "distance_angstrom": format_float(distance),
                            "configured_range": {"minimum": minimum, "maximum": maximum},
                            "range_status": range_status,
                        },
                        "status": status,
                        "detail": range_status if status == "NOT_GEOMETRICALLY_SUPPORTED" else None,
                        "confirmation_required": confirmation_required,
                        "topology_effect_evaluation": {
                            "promote_nonstandard_to_linked": promote,
                            "application_status": application_status,
                        },
                    }
                )
        if above_distances:
            result["omitted_above_maximum_pairs"] = {
                "count": len(above_distances),
                "minimum_distance_angstrom": format_float(min(above_distances)),
                "maximum_distance_angstrom": format_float(max(above_distances)),
            }
        if result["pair_results"]:
            result["status"] = "CHECKED"
        elif result["atom_not_found_instances"]:
            result["status"] = "ATOM_NOT_FOUND"
        else:
            result["status"] = "CHECKED"
        result["confirmation_required"] = any(
            item["confirmation_required"] for item in result["pair_results"]
        )
        definition_results.append(result)

    return {
        "schema_version": "1.0",
        "tool": {"name": "check_possible_coordination", "version": VERSION},
        "status": "COMPLETED",
        "reason": None,
        "input": {
            "structure_path": str(structure_path),
            "structure_sha256": structure_hash,
            "selected_model_id": selected_model_id,
            "definition_path": str(definition_path),
            "definition_sha256": definition_hash,
            "observations_path": str(observations_path),
            "observations_sha256": observations_hash,
        },
        "definition_results": definition_results,
        "summary": {
            "definition_count": len(definition_results),
            "confirmation_required_count": confirmation_count,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--definition-schema", type=Path, required=True)
    parser.add_argument("--result-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_yaml(args.config)
        definition_cfg = config.get("possible_coordination") or {}
        if definition_cfg.get("path"):
            validate_document(load_yaml(Path(definition_cfg["path"])), args.definition_schema)
        result = check(config)
        validate_document(result, args.result_schema)
        atomic_yaml(args.output, result)
    except (ClassificationError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

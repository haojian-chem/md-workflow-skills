#!/usr/bin/env python3
"""Check project-defined possible covalent connections for one selected model."""
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


def _definition_key(item: dict[str, Any]) -> tuple[tuple[str, str], tuple[str, str]]:
    left = (item["partner_1"]["residue_name"], item["partner_1"]["atom_name"])
    right = (item["partner_2"]["residue_name"], item["partner_2"]["atom_name"])
    return tuple(sorted((left, right)))  # type: ignore[return-value]


def _participant_pairs(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    same_spec: bool,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen: set[tuple[Any, ...]] = set()
    if same_spec:
        iterator = itertools.combinations(left, 2)
    else:
        iterator = itertools.product(left, right)
    for left_item, right_item in iterator:
        left_residue = left_item["residue"]
        right_residue = right_item["residue"]
        # Same residue is allowed only when the requested atom names differ.
        key = (
            left_residue["source_chain_id"],
            left_residue["source_resid"]["number"],
            left_residue["source_resid"]["insertion_code"],
            left_residue["residue_name"],
            right_residue["source_chain_id"],
            right_residue["source_resid"]["number"],
            right_residue["source_resid"]["insertion_code"],
            right_residue["residue_name"],
        )
        if same_spec and left_residue is right_residue:
            continue
        if key in seen:
            continue
        seen.add(key)
        pairs.append((left_item, right_item))
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

    definition_cfg = config.get("possible_connections") or {}
    if not definition_cfg.get("path"):
        return {
            "schema_version": "1.0",
            "tool": {"name": "check_possible_connections", "version": VERSION},
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
    definition_hash = require_hash(definition_path, definition_cfg.get("sha256"), "possible connections")
    definitions_doc = load_yaml(definition_path)
    definitions = definitions_doc.get("possible_connections", [])
    seen_definitions: set[tuple[Any, ...]] = set()
    for item in definitions:
        key = _definition_key(item)
        if key in seen_definitions:
            raise ClassificationError(f"DUPLICATE_CONNECTION_DEFINITION: {key}")
        seen_definitions.add(key)

    structure, model, residues, serial_map = collect_relation_residues(
        structure_path, selected_model_id, observations
    )
    explicit_index = explicit_relation_index(structure, model, residues, serial_map, structure_path)

    definition_results: list[dict[str, Any]] = []
    confirmation_count = 0
    for definition_index, definition in enumerate(definitions, start=1):
        left_spec = definition["partner_1"]
        right_spec = definition["partner_2"]
        minimum = float(definition["distance_range_angstrom"]["minimum"])
        maximum = float(definition["distance_range_angstrom"]["maximum"])
        if minimum < 0 or maximum <= minimum:
            raise ClassificationError(
                f"invalid distance range in definition {definition_index}: "
                f"minimum={minimum}, maximum={maximum}"
            )
        left_valid, left_missing = matching_residues(
            residues, left_spec["residue_name"], left_spec["atom_name"]
        )
        right_valid, right_missing = matching_residues(
            residues, right_spec["residue_name"], right_spec["atom_name"]
        )
        left_residue_count = sum(1 for r in residues if r["residue_name"] == left_spec["residue_name"])
        right_residue_count = sum(1 for r in residues if r["residue_name"] == right_spec["residue_name"])
        result: dict[str, Any] = {
            "definition_index": definition_index,
            "label": definition.get("label"),
            "definition": definition,
            "matching_summary": {
                "partner_1_residue_count": left_residue_count,
                "partner_1_atom_count": len(left_valid),
                "partner_2_residue_count": right_residue_count,
                "partner_2_atom_count": len(right_valid),
                "evaluated_pair_count": 0,
            },
            "atom_not_found_instances": left_missing + right_missing,
            "pair_results": [],
            "omitted_above_maximum_pairs": {
                "count": 0,
                "minimum_distance_angstrom": None,
                "maximum_distance_angstrom": None,
            },
        }
        if left_residue_count == 0 or right_residue_count == 0:
            if left_residue_count == 0 and right_residue_count == 0:
                missing_partner = "BOTH"
            elif left_residue_count == 0:
                missing_partner = "PARTNER_1"
            else:
                missing_partner = "PARTNER_2"
            result.update(
                status="PARTNER_NOT_FOUND",
                missing_partner=missing_partner,
                confirmation_required=False,
            )
            definition_results.append(result)
            continue

        same_spec = left_spec == right_spec
        pairs = _participant_pairs(left_valid, right_valid, same_spec)
        result["matching_summary"]["evaluated_pair_count"] = len(pairs)
        above_distances: list[float] = []
        for left_item, right_item in pairs:
            left_residue = left_item["residue"]
            right_residue = right_item["residue"]
            atom_pairs = [
                (atom_a, atom_b)
                for atom_a in left_item["atoms"]
                for atom_b in right_item["atoms"]
                if atom_a is not atom_b
            ]
            explicit_atom_pairs = [
                (a, b, explicit_index[pair_key(a, b)])
                for a, b in atom_pairs
                if pair_key(a, b) in explicit_index
            ]
            if explicit_atom_pairs:
                for atom_a, atom_b, explicit_records in explicit_atom_pairs:
                    distance = distance_angstrom(atom_a["atom"], atom_b["atom"])
                    range_status = geometry_range(distance, minimum, maximum)
                    relation_types = {record["relation_type"] for record in explicit_records}
                    is_covalent = bool(relation_types & {"COVALENT", "DISULFIDE"})
                    status = (
                        "CONFIRMED_BY_STRUCTURE"
                        if is_covalent and range_status == "WITHIN_RANGE"
                        else "CONNECTION_DEFINITION_CONFLICT"
                    )
                    confirmation_required = status == "CONNECTION_DEFINITION_CONFLICT"
                    confirmation_count += int(confirmation_required)
                    result["pair_results"].append(
                        {
                            "partner_1": atom_endpoint(atom_a),
                            "partner_2": atom_endpoint(atom_b),
                            "explicit_connection": {
                                "status": "PRESENT",
                                "records": explicit_records,
                            },
                            "geometry": {
                                "distance_angstrom": format_float(distance),
                                "configured_range": {"minimum": minimum, "maximum": maximum},
                                "range_status": range_status,
                            },
                            "status": status,
                            "confirmation_required": confirmation_required,
                            "topology_effect_candidate": {
                                "relation_type": "COVALENT_CONNECTION",
                                "applicable": status == "CONFIRMED_BY_STRUCTURE",
                            },
                        }
                    )
                continue

            if left_residue["multiple_conformations"] or right_residue["multiple_conformations"] or len(atom_pairs) != 1:
                atom_a = left_item["atoms"][0]
                atom_b = right_item["atoms"][0]
                result["pair_results"].append(
                    {
                        "partner_1": atom_endpoint(atom_a),
                        "partner_2": atom_endpoint(atom_b),
                        "explicit_connection": {"status": "ABSENT", "records": []},
                        "geometry": {
                            "distance_angstrom": None,
                            "configured_range": {"minimum": minimum, "maximum": maximum},
                            "range_status": "NOT_EVALUATED",
                        },
                        "status": "GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS",
                        "confirmation_required": False,
                        "topology_effect_candidate": {
                            "relation_type": "COVALENT_CONNECTION",
                            "applicable": False,
                        },
                    }
                )
                continue

            atom_a, atom_b = atom_pairs[0]
            distance = distance_angstrom(atom_a["atom"], atom_b["atom"])
            range_status = geometry_range(distance, minimum, maximum)
            if range_status == "WITHIN_RANGE":
                status = "GEOMETRY_SUPPORTED_CANDIDATE"
                confirmation_required = True
                confirmation_count += 1
            else:
                status = "NOT_GEOMETRICALLY_SUPPORTED"
                confirmation_required = False
            if range_status == "ABOVE_MAXIMUM":
                above_distances.append(distance)
                continue
            result["pair_results"].append(
                {
                    "partner_1": atom_endpoint(atom_a),
                    "partner_2": atom_endpoint(atom_b),
                    "explicit_connection": {"status": "ABSENT", "records": []},
                    "geometry": {
                        "distance_angstrom": format_float(distance),
                        "configured_range": {"minimum": minimum, "maximum": maximum},
                        "range_status": range_status,
                    },
                    "status": status,
                    "detail": range_status if status == "NOT_GEOMETRICALLY_SUPPORTED" else None,
                    "confirmation_required": confirmation_required,
                    "topology_effect_candidate": {
                        "relation_type": "COVALENT_CONNECTION",
                        "applicable": False,
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
        "tool": {"name": "check_possible_connections", "version": VERSION},
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
        definition_cfg = config.get("possible_connections") or {}
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

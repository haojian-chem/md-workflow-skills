#!/usr/bin/env python3
"""Independently validate chain/component selection fidelity."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import gemmi

REPO_ROOT = Path(__file__).resolve().parents[3]
OPERATION_SCRIPTS = REPO_ROOT / "02_operations/chain_and_component_selection/scripts"
if str(OPERATION_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(OPERATION_SCRIPTS))

from selection_common import (
    AtomSnapshot,
    SelectionToolError,
    atom_snapshots,
    atom_stable_key,
    atomic_write_yaml,
    build_selection_plan,
    close_enough,
    file_identity,
    find_atom_cra,
    parse_structure,
    read_yaml_strict,
    require_sha256,
    selected_model,
    sha256_file,
    validate_document,
)

VERSION = "1.0.0-draft"


def _required_path(config: dict[str, Any], key: str) -> Path:
    value = config.get(key)
    if not isinstance(value, str) or not value:
        raise SelectionToolError("VALIDATOR_INPUT_INCOMPLETE", f"config field {key!r} must be a path", blocked=True)
    return Path(value).resolve()


def _report_base(spec: dict[str, Any] | None, status: str, outcome_code: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "tool_version": VERSION,
        "task_id": spec.get("task_id", "UNKNOWN") if isinstance(spec, dict) else "UNKNOWN",
        "workstream_id": spec.get("workstream_id", "UNKNOWN") if isinstance(spec, dict) else "UNKNOWN",
        "status": status,
        "outcome_code": outcome_code,
        "message": message,
        "checks": {},
        "differences": [],
        "warnings": [],
        "validated_files": [],
    }


def _output_format(path: Path, manifest: dict[str, Any]) -> str:
    format_name = manifest["output_structure"]["format"]
    suffix = path.suffix.lower()
    if format_name == "PDB" and suffix not in {".pdb", ".ent"}:
        raise SelectionToolError("OUTPUT_FORMAT_MISMATCH", f"manifest says PDB but path is {path}")
    if format_name == "MMCIF" and suffix not in {".cif", ".mmcif"}:
        raise SelectionToolError("OUTPUT_FORMAT_MISMATCH", f"manifest says MMCIF but path is {path}")
    return format_name


def _mapping_check(mapping: dict[str, Any], expected: list[AtomSnapshot], actual: list[AtomSnapshot]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    rows = mapping["atom_mappings"]
    if len(rows) != len(expected) or len(rows) != len(actual):
        differences.append({"check": "atom_mapping_count", "expected": len(expected), "actual": len(rows)})
        return differences
    seen_source: set[tuple[Any, ...]] = set()
    seen_output: set[tuple[Any, ...]] = set()
    for index, (row, source_atom, output_atom) in enumerate(zip(rows, expected, actual, strict=True)):
        source_key = atom_stable_key(row["source"])
        output_key = atom_stable_key(row["output"])
        if source_key in seen_source or output_key in seen_output:
            differences.append({"check": "mapping_one_to_one", "index": index, "source": row["source"], "output": row["output"]})
        seen_source.add(source_key)
        seen_output.add(output_key)
        if row["source"] != source_atom.identity:
            differences.append({"check": "mapping_source_identity", "index": index, "expected": source_atom.identity, "actual": row["source"]})
        if row["output"] != output_atom.identity:
            differences.append({"check": "mapping_output_identity", "index": index, "expected": output_atom.identity, "actual": row["output"]})
    return differences


def _attribute_check(expected: list[AtomSnapshot], actual: list[AtomSnapshot], format_name: str) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    coordinate_tolerance = 6e-4 if format_name == "PDB" else 1e-6
    occupancy_tolerance = 6e-3 if format_name == "PDB" else 1e-6
    b_tolerance = 6e-3 if format_name == "PDB" else 1e-6
    for index, (source_atom, output_atom) in enumerate(zip(expected, actual, strict=True)):
        if atom_stable_key(source_atom.identity) != atom_stable_key(output_atom.identity):
            differences.append({"check": "atom_identity", "index": index, "expected": source_atom.identity, "actual": output_atom.identity})
            continue
        for field, first, second, tolerance in (
            ("x", source_atom.x, output_atom.x, coordinate_tolerance),
            ("y", source_atom.y, output_atom.y, coordinate_tolerance),
            ("z", source_atom.z, output_atom.z, coordinate_tolerance),
            ("occupancy", source_atom.occupancy, output_atom.occupancy, occupancy_tolerance),
            ("b_iso", source_atom.b_iso, output_atom.b_iso, b_tolerance),
        ):
            if not close_enough(first, second, tolerance):
                differences.append({"check": "atom_attribute", "index": index, "field": field, "expected": first, "actual": second, "tolerance": tolerance})
        if source_atom.charge != output_atom.charge:
            differences.append({"check": "atom_charge", "index": index, "expected": source_atom.charge, "actual": output_atom.charge})
    return differences


def _connection_check(output: gemmi.Structure, classification: dict[str, Any], selected_components: set[str]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    model = output[0]
    for relation in [
        *classification["confirmed_relations"]["covalent_connections"],
        *classification["confirmed_relations"]["metal_coordination"],
    ]:
        both = relation["endpoint_1"]["component_id"] in selected_components and relation["endpoint_2"]["component_id"] in selected_components
        if not both:
            continue
        try:
            chain1, residue1, atom1 = find_atom_cra(model, relation["endpoint_1"])
            chain2, residue2, atom2 = find_atom_cra(model, relation["endpoint_2"])
            addr1 = gemmi.make_address(chain1, residue1, atom1)
            addr2 = gemmi.make_address(chain2, residue2, atom2)
            if output.find_connection(addr1, addr2) is None:
                differences.append({"check": "explicit_connection", "relation_id": relation["relation_id"], "message": "selected confirmed relation missing from output"})
        except SelectionToolError as exc:
            differences.append({"check": "explicit_connection", "relation_id": relation["relation_id"], "message": str(exc)})
    return differences


def validate_run(config: dict[str, Any], script_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_document(config, script_dir.parent / "schemas/selection_validation_config.schema.yaml", code="VALIDATOR_INPUT_INCOMPLETE")
    spec_path = _required_path(config, "selection_spec_path")
    classification_path = _required_path(config, "classification_result_path")
    candidate_path = _required_path(config, "candidate_structure_path")
    manifest_path = _required_path(config, "selection_manifest_path")
    mapping_path = _required_path(config, "selection_mapping_path")
    operation_report_path = _required_path(config, "operation_report_path")
    validation_report_path = _required_path(config, "validation_report_path")
    validation_result_path = _required_path(config, "validation_result_path")

    spec = read_yaml_strict(spec_path)
    classification = read_yaml_strict(classification_path)
    manifest = read_yaml_strict(manifest_path)
    mapping = read_yaml_strict(mapping_path)
    operation_report = read_yaml_strict(operation_report_path)
    validate_document(spec, script_dir.parents[2] / "02_operations/chain_and_component_selection/schemas/selection_spec.schema.yaml")
    validate_document(classification, script_dir.parents[2] / "02_validators/component_and_residue_classification_validator/schemas/classification_result.schema.yaml")
    validate_document(manifest, script_dir.parents[2] / "02_operations/chain_and_component_selection/schemas/selection_manifest.schema.yaml", code="MANIFEST_OR_HASH_MISMATCH")
    validate_document(mapping, script_dir.parents[2] / "02_operations/chain_and_component_selection/schemas/selection_mapping.schema.yaml", code="ATOM_MAPPING_MISMATCH")
    validate_document(operation_report, script_dir.parents[2] / "02_operations/chain_and_component_selection/schemas/selection_operation_report.schema.yaml", code="VALIDATOR_INPUT_INCOMPLETE")
    if operation_report["status"] != "DONE":
        raise SelectionToolError("VALIDATOR_INPUT_INCOMPLETE", "operation did not complete successfully", blocked=True)

    source_path = Path(spec["source_structure"]["path"]).resolve()
    require_sha256(source_path, spec["source_structure"]["sha256"], "MANIFEST_OR_HASH_MISMATCH")
    require_sha256(classification_path, spec["classification_result"]["sha256"], "MANIFEST_OR_HASH_MISMATCH")
    require_sha256(candidate_path, manifest["output_structure"]["sha256"], "MANIFEST_OR_HASH_MISMATCH")
    require_sha256(spec_path, manifest["selection_spec"]["sha256"], "MANIFEST_OR_HASH_MISMATCH")
    if mapping["output_structure"]["sha256"] != manifest["output_structure"]["sha256"]:
        raise SelectionToolError("MANIFEST_OR_HASH_MISMATCH", "mapping and manifest output hashes differ")
    if mapping["source_structure"]["sha256"] != manifest["source_structure"]["sha256"]:
        raise SelectionToolError("MANIFEST_OR_HASH_MISMATCH", "mapping and manifest source hashes differ")
    expected_paths = {
        "source_structure": source_path,
        "classification_result": classification_path,
        "selection_spec": spec_path,
        "output_structure": candidate_path,
    }
    for field, path in expected_paths.items():
        if Path(manifest[field]["path"]).resolve() != path or manifest[field]["sha256"] != sha256_file(path):
            raise SelectionToolError("MANIFEST_OR_HASH_MISMATCH", f"manifest {field} identity differs from actual file")
    if manifest["task_id"] != spec["task_id"] or manifest["workstream_id"] != spec["workstream_id"]:
        raise SelectionToolError("MANIFEST_OR_HASH_MISMATCH", "manifest task/workstream IDs differ from selection spec")
    if mapping["task_id"] != spec["task_id"] or mapping["workstream_id"] != spec["workstream_id"]:
        raise SelectionToolError("MANIFEST_OR_HASH_MISMATCH", "mapping task/workstream IDs differ from selection spec")
    created = {Path(item["path"]).resolve(): item["sha256"] for item in operation_report["created_files"]}
    for path in (candidate_path, manifest_path, mapping_path):
        if created.get(path) != sha256_file(path):
            raise SelectionToolError("MANIFEST_OR_HASH_MISMATCH", f"operation report file identity missing or stale: {path}")

    try:
        plan = build_selection_plan(classification, spec)
    except SelectionToolError as exc:
        if exc.code == "SELECTION_BREAKS_CONFIRMED_COVALENT_LINK":
            raise SelectionToolError("INVALID_SELECTION_SPEC_COVALENT_BREAK", str(exc)) from exc
        raise
    source = parse_structure(source_path)
    candidate = parse_structure(candidate_path)
    source_model = selected_model(source, str(spec["selected_model_id"]))
    candidate_model = selected_model(candidate, str(spec["selected_model_id"]))
    if len(candidate) != 1:
        raise SelectionToolError("SELECTED_SET_MISMATCH", f"candidate contains {len(candidate)} models, expected one")
    expected_atoms = atom_snapshots(source_model, plan.selected_residue_keys)
    actual_atoms = atom_snapshots(candidate_model)

    differences: list[dict[str, Any]] = []
    checks: dict[str, str] = {}
    if len(expected_atoms) != len(actual_atoms):
        differences.append({"check": "selected_atom_count", "expected": len(expected_atoms), "actual": len(actual_atoms)})
        checks["selected_set"] = "FAIL"
    else:
        checks["selected_set"] = "PASS"
        differences.extend(_attribute_check(expected_atoms, actual_atoms, _output_format(candidate_path, manifest)))
    mapping_diffs = _mapping_check(mapping, expected_atoms, actual_atoms) if len(expected_atoms) == len(actual_atoms) else [{"check": "mapping_skipped_due_to_count_mismatch"}]
    differences.extend(mapping_diffs)
    checks["atom_mapping"] = "PASS" if not mapping_diffs else "FAIL"
    checks["coordinates_and_attributes"] = "PASS" if not any(item["check"] in {"atom_identity", "atom_attribute", "atom_charge"} for item in differences) else "FAIL"
    connection_diffs = _connection_check(candidate, classification, set(plan.selected_component_ids))
    differences.extend(connection_diffs)
    checks["explicit_connections"] = "PASS" if not connection_diffs else "FAIL"

    expected_manifest = {
        "requested_component_ids": list(spec["selected_component_ids"]),
        "actual_component_ids": plan.selected_component_ids,
        "selected_residue_ids": plan.selected_residue_ids,
        "excluded_residue_ids": plan.excluded_residue_ids,
        "preserved_explicit_connections": plan.preserved_relations,
        "excluded_explicit_connections": plan.excluded_relations,
        "cross_boundary_coordination_relations": plan.cross_boundary_coordination,
        "cross_boundary_covalent_candidates": plan.cross_boundary_covalent_candidates,
        "resolved_decision_ids": list(spec["resolved_decision_ids"]),
        "policies": dict(spec["policies"]),
    }
    for field, expected_value in expected_manifest.items():
        if manifest[field] != expected_value:
            differences.append({"check": "manifest_field", "field": field, "expected": expected_value, "actual": manifest[field]})
    all_source_atoms = atom_snapshots(source_model)
    expected_counts = {
        "source_component_count": len(classification["chain_groups"]),
        "selected_component_count": len(plan.selected_component_ids),
        "excluded_component_count": len(plan.excluded_component_ids),
        "source_residue_count": sum(record["presence_status"] == "OBSERVED" for record in classification["residue_records"]),
        "selected_residue_count": len(plan.selected_residue_ids),
        "excluded_residue_count": len(plan.excluded_residue_ids),
        "source_atom_count": len(all_source_atoms),
        "selected_atom_count": len(expected_atoms),
        "excluded_atom_count": len(all_source_atoms) - len(expected_atoms),
    }
    if manifest["counts"] != expected_counts:
        differences.append({"check": "manifest_counts", "expected": expected_counts, "actual": manifest["counts"]})
    checks["manifest"] = "PASS" if not any(item["check"].startswith("manifest") for item in differences) else "FAIL"
    checks["hashes"] = "PASS"

    warnings = list(manifest["warnings"])
    if manifest["output_structure"]["format"] == "PDB":
        warnings.append("PDB numeric fields validated with explicit rounding tolerances")
    if differences:
        if any(item["check"] in {"atom_mapping_count", "mapping_one_to_one", "mapping_source_identity", "mapping_output_identity", "mapping_skipped_due_to_count_mismatch"} for item in differences):
            outcome = "ATOM_MAPPING_MISMATCH"
        elif any(item["check"] in {"atom_identity", "selected_atom_count"} for item in differences):
            outcome = "SELECTED_SET_MISMATCH"
        elif any(item["check"] in {"atom_attribute", "atom_charge"} for item in differences):
            outcome = "COORDINATE_OR_ATTRIBUTE_CHANGED"
        elif any(item["check"] == "explicit_connection" for item in differences):
            outcome = "EXPLICIT_CONNECTION_MISMATCH"
        else:
            outcome = "MANIFEST_OR_HASH_MISMATCH"
        status = "FAILED"
    else:
        outcome = "SELECTION_VALIDATED_WITH_WARNINGS" if warnings else "SELECTION_VALIDATED"
        status = "DONE"

    report = _report_base(spec, status, outcome, "selection validation completed")
    report.update(
        {
            "checks": checks,
            "differences": differences,
            "warnings": sorted(set(warnings)),
            "validated_files": [
                file_identity(candidate_path, include_size=True),
                file_identity(manifest_path, include_size=True),
                file_identity(mapping_path, include_size=True),
            ],
        }
    )
    validate_document(report, script_dir.parent / "schemas/selection_validation_report.schema.yaml", code="SELECTION_VALIDATOR_INTERNAL_FAILURE")
    atomic_write_yaml(validation_report_path, report)
    result = {
        "schema_version": 1,
        "task_id": spec["task_id"],
        "workstream_id": spec["workstream_id"],
        "status": status,
        "outcome_code": outcome,
        "validation_report": file_identity(validation_report_path),
        "validated_files": report["validated_files"],
        "warnings": report["warnings"],
    }
    validate_document(result, script_dir.parent / "schemas/selection_validation_result.schema.yaml", code="SELECTION_VALIDATOR_INTERNAL_FAILURE")
    atomic_write_yaml(validation_result_path, result)
    if differences:
        raise SelectionToolError(outcome, f"selection validation found {len(differences)} difference(s)")
    return report, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    try:
        config = read_yaml_strict(Path(args.config).resolve())
        validate_run(config, Path(__file__).resolve().parent)
        return 0
    except SelectionToolError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2 if exc.blocked else 1
    except Exception as exc:
        print(f"SELECTION_VALIDATOR_INTERNAL_FAILURE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

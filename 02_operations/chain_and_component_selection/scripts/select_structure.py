#!/usr/bin/env python3
"""Deterministically select complete classified components from one structure model."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import gemmi

from selection_common import (
    SelectionToolError,
    add_selected_connections,
    atom_snapshots,
    atomic_replace_file,
    atomic_write_yaml,
    build_selection_plan,
    file_identity,
    parse_structure,
    pdb_identifier_issues,
    read_yaml_strict,
    require_sha256,
    residue_key,
    selected_model,
    tmp_structure_path,
    validate_document,
    write_structure,
)

VERSION = "1.0.0-draft"


def _required_path(config: dict[str, Any], key: str) -> Path:
    value = config.get(key)
    if not isinstance(value, str) or not value:
        raise SelectionToolError("SELECTION_SPEC_MISSING_OR_INVALID", f"config field {key!r} must be a non-empty path", blocked=True)
    return Path(value).resolve()


def _output_paths(config: dict[str, Any]) -> tuple[Path, Path, Path]:
    output = config.get("output")
    if not isinstance(output, dict):
        raise SelectionToolError("SELECTION_SPEC_MISSING_OR_INVALID", "config.output must be a mapping", blocked=True)
    return (
        Path(output["manifest_path"]).resolve(),
        Path(output["mapping_path"]).resolve(),
        Path(output["report_path"]).resolve(),
    )


def _report_base(spec: dict[str, Any] | None, status: str, outcome_code: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "tool_version": VERSION,
        "task_id": spec.get("task_id", "UNKNOWN") if isinstance(spec, dict) else "UNKNOWN",
        "workstream_id": spec.get("workstream_id", "UNKNOWN") if isinstance(spec, dict) else "UNKNOWN",
        "status": status,
        "outcome_code": outcome_code,
        "message": message,
        "created_files": [],
        "warnings": [],
        "blocking_issues": [],
    }


def _write_failure_report(report_path: Path | None, spec: dict[str, Any] | None, error: SelectionToolError) -> None:
    if report_path is None:
        return
    report = _report_base(spec, "BLOCKED" if error.blocked else "FAILED", error.code, str(error))
    if error.blocked:
        report["blocking_issues"] = [{"code": error.code, "message": str(error)}]
    atomic_write_yaml(report_path, report)


def _copy_selected_structure(
    source: gemmi.Structure,
    selected_model_id: str,
    selected_residue_keys: set[tuple[str, str, str, str | None, str]],
    classification: dict[str, Any],
    selected_component_ids: set[str],
) -> gemmi.Structure:
    model = selected_model(source, selected_model_id)
    matched: set[tuple[str, str, str, str | None, str]] = set()
    for chain in model:
        for residue in chain:
            key = residue_key(model, chain, residue)
            residue.flag = "s" if key in selected_residue_keys else "\x00"
            if key in selected_residue_keys:
                matched.add(key)
    missing = sorted(selected_residue_keys - matched)
    if missing:
        raise SelectionToolError(
            "SELECTION_REFERENCES_UNKNOWN_OBJECT",
            f"classification selected residues not found in source structure: {missing}",
            blocked=True,
        )
    selection = gemmi.Selection().set_residue_flags("s")
    output = selection.copy_structure_selection(source)
    if len(output) != 1 or output[0].count_atom_sites() == 0:
        raise SelectionToolError("SELECTION_REFERENCES_UNKNOWN_OBJECT", "selection did not produce exactly one non-empty model", blocked=True)
    output.connections.clear()
    try:
        output.clear_conect()
    except Exception:
        pass
    try:
        output.entities.clear()
        output.setup_entities()
    except Exception:
        pass
    add_selected_connections(output, classification, selected_component_ids)
    return output


def run(config: dict[str, Any], script_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_document(config, script_dir.parent / "schemas/selection_operation_config.schema.yaml")
    spec_path = _required_path(config, "selection_spec_path")
    classification_path = _required_path(config, "classification_result_path")
    manifest_path, mapping_path, report_path = _output_paths(config)

    spec = read_yaml_strict(spec_path)
    classification = read_yaml_strict(classification_path)
    validate_document(spec, script_dir.parent / "schemas/selection_spec.schema.yaml")
    classification_schema = script_dir.parents[2] / "02_validators/component_and_residue_classification_validator/schemas/classification_result.schema.yaml"
    validate_document(classification, classification_schema)

    source_path = Path(spec["source_structure"]["path"]).resolve()
    output_path = Path(spec["output"]["path"]).resolve()
    if source_path == output_path:
        raise SelectionToolError("OUTPUT_CONFLICT", "source and output structure paths must differ", blocked=True)
    for path in (output_path, manifest_path, mapping_path):
        if path.exists():
            raise SelectionToolError("OUTPUT_CONFLICT", f"refusing to overwrite existing output: {path}", blocked=True)

    require_sha256(source_path, spec["source_structure"]["sha256"])
    require_sha256(classification_path, spec["classification_result"]["sha256"])
    if Path(spec["classification_result"]["path"]).resolve() != classification_path:
        raise SelectionToolError("SOURCE_OR_CLASSIFICATION_HASH_MISMATCH", "selection spec classification path differs from config path", blocked=True)
    class_source = classification["source_structure"]
    if Path(class_source["path"]).resolve() != source_path or class_source["sha256"] != spec["source_structure"]["sha256"]:
        raise SelectionToolError("SOURCE_OR_CLASSIFICATION_HASH_MISMATCH", "classification result and selection spec reference different source structures", blocked=True)
    if str(classification["selected_model_id"]) != str(spec["selected_model_id"]):
        raise SelectionToolError("SELECTION_REFERENCES_UNKNOWN_OBJECT", "selection spec model differs from classification model", blocked=True)
    if classification["result_status"] != "COMPLETE" or classification["unresolved_items"]:
        raise SelectionToolError("SELECTION_SPEC_MISSING_OR_INVALID", "classification result is not complete", blocked=True)

    plan = build_selection_plan(classification, spec)
    source = parse_structure(source_path)
    source_model = selected_model(source, str(spec["selected_model_id"]))
    source_atoms = atom_snapshots(source_model)
    selected_source_atoms = atom_snapshots(source_model, plan.selected_residue_keys)
    selected_structure = _copy_selected_structure(
        source,
        str(spec["selected_model_id"]),
        plan.selected_residue_keys,
        classification,
        set(plan.selected_component_ids),
    )

    output_format = spec["output"]["format"]
    suffix = output_path.suffix.lower()
    if output_format == "PDB" and suffix not in {".pdb", ".ent"}:
        raise SelectionToolError("OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS", f"PDB output path must end in .pdb or .ent: {output_path}", blocked=True)
    if output_format == "MMCIF" and suffix not in {".cif", ".mmcif"}:
        raise SelectionToolError("OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS", f"MMCIF output path must end in .cif or .mmcif: {output_path}", blocked=True)
    warnings: list[str] = []
    if output_format == "PDB":
        issues = pdb_identifier_issues(selected_structure[0])
        if issues:
            raise SelectionToolError(
                "OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS",
                "PDB cannot losslessly represent selected identifiers: " + "; ".join(issues),
                blocked=True,
            )
    elif classification["source_structure"]["source_format"] == "AF3_CIF":
        warnings.append("AF3_CIF output is normalized to coordinate mmCIF; AF3-specific non-coordinate categories are not preserved")

    tmp_output = tmp_structure_path(output_path)
    tmp_output.parent.mkdir(parents=True, exist_ok=True)
    write_structure(selected_structure, tmp_output, output_format)
    parsed_output = parse_structure(tmp_output)
    output_model = selected_model(parsed_output, str(spec["selected_model_id"]))
    output_atoms = atom_snapshots(output_model)
    if len(output_atoms) != len(selected_source_atoms):
        tmp_output.unlink(missing_ok=True)
        raise SelectionToolError("SELECTION_INTERNAL_FAILURE", "written structure atom count differs from selected source atom count")
    for source_atom, output_atom in zip(selected_source_atoms, output_atoms, strict=True):
        source_key = tuple(value for key, value in source_atom.identity.items() if key != "serial")
        output_key = tuple(value for key, value in output_atom.identity.items() if key != "serial")
        if source_key != output_key:
            tmp_output.unlink(missing_ok=True)
            raise SelectionToolError("SELECTION_INTERNAL_FAILURE", f"written atom identity changed: {source_atom.identity} -> {output_atom.identity}")

    atomic_replace_file(tmp_output, output_path)
    output_identity = file_identity(output_path, include_size=True, format_name=output_format)
    source_identity = file_identity(source_path)
    classification_identity = file_identity(classification_path)
    spec_identity = file_identity(spec_path)

    mapping = {
        "schema_version": 1,
        "task_id": spec["task_id"],
        "workstream_id": spec["workstream_id"],
        "source_structure": source_identity,
        "output_structure": {"path": output_identity["path"], "sha256": output_identity["sha256"]},
        "atom_mappings": [
            {"source": source_atom.identity, "output": output_atom.identity}
            for source_atom, output_atom in zip(selected_source_atoms, output_atoms, strict=True)
        ],
    }
    validate_document(mapping, script_dir.parent / "schemas/selection_mapping.schema.yaml")
    atomic_write_yaml(mapping_path, mapping)

    manifest = {
        "schema_version": 1,
        "task_id": spec["task_id"],
        "workstream_id": spec["workstream_id"],
        "source_structure": source_identity,
        "classification_result": classification_identity,
        "selection_spec": spec_identity,
        "output_structure": output_identity,
        "selected_model_id": str(spec["selected_model_id"]),
        "requested_component_ids": list(spec["selected_component_ids"]),
        "actual_component_ids": plan.selected_component_ids,
        "selected_residue_ids": plan.selected_residue_ids,
        "excluded_residue_ids": plan.excluded_residue_ids,
        "counts": {
            "source_component_count": len(classification["chain_groups"]),
            "selected_component_count": len(plan.selected_component_ids),
            "excluded_component_count": len(plan.excluded_component_ids),
            "source_residue_count": sum(record["presence_status"] == "OBSERVED" for record in classification["residue_records"]),
            "selected_residue_count": len(plan.selected_residue_ids),
            "excluded_residue_count": len(plan.excluded_residue_ids),
            "source_atom_count": len(source_atoms),
            "selected_atom_count": len(selected_source_atoms),
            "excluded_atom_count": len(source_atoms) - len(selected_source_atoms),
        },
        "preserved_explicit_connections": plan.preserved_relations,
        "excluded_explicit_connections": plan.excluded_relations,
        "cross_boundary_coordination_relations": plan.cross_boundary_coordination,
        "cross_boundary_covalent_candidates": plan.cross_boundary_covalent_candidates,
        "resolved_decision_ids": list(spec["resolved_decision_ids"]),
        "policies": dict(spec["policies"]),
        "warnings": warnings,
    }
    validate_document(manifest, script_dir.parent / "schemas/selection_manifest.schema.yaml")
    atomic_write_yaml(manifest_path, manifest)

    report = _report_base(spec, "DONE", "SELECTION_APPLIED_WITH_WARNINGS" if warnings else "SELECTION_APPLIED", "selection completed")
    report.update(
        {
            "selected_component_ids": plan.selected_component_ids,
            "selected_residue_ids": plan.selected_residue_ids,
            "created_files": [
                file_identity(output_path, include_size=True),
                file_identity(manifest_path, include_size=True),
                file_identity(mapping_path, include_size=True),
            ],
            "warnings": warnings,
        }
    )
    validate_document(report, script_dir.parent / "schemas/selection_operation_report.schema.yaml")
    atomic_write_yaml(report_path, report)
    return manifest, mapping, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    report_path: Path | None = None
    spec: dict[str, Any] | None = None
    try:
        config = read_yaml_strict(config_path)
        output = config.get("output") if isinstance(config, dict) else None
        if isinstance(output, dict) and isinstance(output.get("report_path"), str):
            report_path = Path(output["report_path"]).resolve()
        if isinstance(config, dict) and isinstance(config.get("selection_spec_path"), str):
            candidate = Path(config["selection_spec_path"]).resolve()
            if candidate.is_file():
                loaded = read_yaml_strict(candidate)
                if isinstance(loaded, dict):
                    spec = loaded
        run(config, Path(__file__).resolve().parent)
        return 0
    except SelectionToolError as exc:
        _write_failure_report(report_path, spec, exc)
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2 if exc.blocked else 1
    except Exception as exc:
        error = SelectionToolError("SELECTION_INTERNAL_FAILURE", str(exc))
        _write_failure_report(report_path, spec, error)
        print(f"{error.code}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build shared subagent_result v2 for chain/component selection task units."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from selection_common import (
    SelectionToolError,
    atomic_write_yaml,
    read_yaml_strict,
    sha256_file,
    validate_document,
)

OPERATION_SKILL = "chain_and_component_selection"
VALIDATOR_SKILL = "chain_and_component_selection_validator"
WORKFLOW_NAME = "structure_preparation_workflow"
VERSION = "1.0.0"
ACCEPTED_OUTCOMES = {"SELECTION_VALIDATED", "SELECTION_VALIDATED_WITH_WARNINGS"}


def _shared_validator(contract_dir: Path, schema_name: str) -> Draft202012Validator:
    resources = []
    for path in sorted(contract_dir.glob("*.schema.yaml")):
        schema = read_yaml_strict(path)
        identifier = schema.get("$id")
        if isinstance(identifier, str):
            resources.append((identifier, Resource.from_contents(schema)))
    target = read_yaml_strict(contract_dir / schema_name)
    Draft202012Validator.check_schema(target)
    return Draft202012Validator(target, registry=Registry().with_resources(resources))


def _validate_shared(document: dict[str, Any], contract_dir: Path, schema_name: str) -> None:
    errors = sorted(
        _shared_validator(contract_dir, schema_name).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = []
        for error in errors[:20]:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{location}: {error.message}")
        raise SelectionToolError(
            "SHARED_RESULT_CONTRACT_INVALID",
            f"shared contract validation failed for {schema_name}: " + "; ".join(details),
        )


def _file_record(path: Path, task_id: str, role: str, state: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise SelectionToolError("SHARED_RESULT_INPUT_INCOMPLETE", f"expected output is not a regular file: {path}")
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "state": state,
        "role": role,
        "source_task": task_id,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256_file(path),
    }


def _warnings(messages: list[str], affected_paths: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "code": "SELECTION_WARNING",
            "message": message,
            "affected_paths": affected_paths,
        }
        for message in messages
    ]


def build(args: argparse.Namespace) -> dict[str, Any]:
    task_path = args.task.resolve()
    candidate_path = args.candidate.resolve()
    manifest_path = args.manifest.resolve()
    mapping_path = args.mapping.resolve()
    operation_report_path = args.operation_report.resolve()
    validation_report_path = args.validation_report.resolve()
    validation_result_path = args.validation_result.resolve()
    contract_dir = args.contract_dir.resolve()
    operation_schema_dir = args.operation_schema_dir.resolve()
    validator_schema_dir = args.validator_schema_dir.resolve()

    task = read_yaml_strict(task_path)
    _validate_shared(task, contract_dir, "subagent_task.schema.yaml")
    if task["workflow_name"] != WORKFLOW_NAME:
        raise SelectionToolError("SHARED_RESULT_TASK_MISMATCH", f"unexpected workflow_name: {task['workflow_name']}")
    if task["task_unit"]["mode"] != "OPERATION_WITH_VALIDATOR":
        raise SelectionToolError("SHARED_RESULT_TASK_MISMATCH", "selection task must use OPERATION_WITH_VALIDATOR")
    operation_ref = task["task_unit"]["operation"] or {}
    validator_ref = task["task_unit"]["validator"] or {}
    if operation_ref.get("skill_name") != OPERATION_SKILL:
        raise SelectionToolError("SHARED_RESULT_TASK_MISMATCH", "task operation does not reference chain_and_component_selection")
    if validator_ref.get("skill_name") != VALIDATOR_SKILL:
        raise SelectionToolError("SHARED_RESULT_TASK_MISMATCH", "task validator does not reference chain_and_component_selection_validator")

    manifest = read_yaml_strict(manifest_path)
    mapping = read_yaml_strict(mapping_path)
    operation_report = read_yaml_strict(operation_report_path)
    validation_report = read_yaml_strict(validation_report_path)
    validation_result = read_yaml_strict(validation_result_path)
    validate_document(manifest, operation_schema_dir / "selection_manifest.schema.yaml")
    validate_document(mapping, operation_schema_dir / "selection_mapping.schema.yaml")
    validate_document(operation_report, operation_schema_dir / "selection_operation_report.schema.yaml")
    validate_document(validation_report, validator_schema_dir / "selection_validation_report.schema.yaml")
    validate_document(validation_result, validator_schema_dir / "selection_validation_result.schema.yaml")

    for document_name, document in (
        ("manifest", manifest),
        ("mapping", mapping),
        ("operation report", operation_report),
        ("validation report", validation_report),
        ("validation result", validation_result),
    ):
        if document["task_id"] != task["task_id"] or document["workstream_id"] != task["workstream_id"]:
            raise SelectionToolError("SHARED_RESULT_TASK_MISMATCH", f"{document_name} task/workstream IDs differ")
    if operation_report["status"] != "DONE":
        raise SelectionToolError("SHARED_RESULT_INPUT_INCOMPLETE", "Operation report is not DONE")
    if validation_result["status"] != "DONE" or validation_result["outcome_code"] not in ACCEPTED_OUTCOMES:
        raise SelectionToolError("SHARED_RESULT_VALIDATION_NOT_ACCEPTED", "Validator did not accept the candidate structure")

    candidate_hash = sha256_file(candidate_path)
    if manifest["output_structure"]["sha256"] != candidate_hash:
        raise SelectionToolError("SHARED_RESULT_INPUT_INCOMPLETE", "candidate hash differs from manifest")
    validated_hashes = {item["sha256"] for item in validation_result["validated_files"]}
    for path in (candidate_path, manifest_path, mapping_path):
        if sha256_file(path) not in validated_hashes:
            raise SelectionToolError("SHARED_RESULT_VALIDATION_NOT_ACCEPTED", f"Validator result does not cover {path}")

    task_id = task["task_id"]
    operation_created = [
        _file_record(candidate_path, task_id, "selected_structure_candidate", "present_unvalidated"),
        _file_record(manifest_path, task_id, "selection_manifest", "present_unvalidated"),
        _file_record(mapping_path, task_id, "selection_mapping", "present_unvalidated"),
        _file_record(operation_report_path, task_id, "selection_operation_report", "present_unvalidated"),
    ]
    validated_candidate = _file_record(candidate_path, task_id, "selected_structure_candidate", "present_validated")
    validated_manifest = _file_record(manifest_path, task_id, "selection_manifest", "present_validated")
    validated_mapping = _file_record(mapping_path, task_id, "selection_mapping", "present_validated")
    validation_created = [
        _file_record(validation_report_path, task_id, "selection_validation_report", "present_validated"),
        _file_record(validation_result_path, task_id, "selection_validation_result", "present_validated"),
    ]
    affected_paths = [str(candidate_path), str(manifest_path), str(mapping_path)]
    operation_warnings = _warnings(operation_report["warnings"], affected_paths)
    validation_warnings = _warnings(validation_result["warnings"], affected_paths)
    counts = manifest["counts"]
    operation_summary = (
        f"Selected {counts['selected_component_count']} component(s), "
        f"{counts['selected_residue_count']} residue(s), and "
        f"{counts['selected_atom_count']} atom(s)."
    )
    validation_summary = (
        "Selection fidelity validated with warnings."
        if validation_result["outcome_code"] == "SELECTION_VALIDATED_WITH_WARNINGS"
        else "Selection fidelity validated."
    )
    derived_ids = sorted(
        {
            item["artifact_set_id"]
            for item in task["current_valid_files"]
            if isinstance(item.get("artifact_set_id"), str) and item["artifact_set_id"]
        }
    )
    shared_result = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": task["workstream_id"],
        "task_unit_mode": "OPERATION_WITH_VALIDATOR",
        "status": "DONE",
        "execution_summary": operation_summary + " " + validation_summary,
        "operation_result": {
            "skill_name": OPERATION_SKILL,
            "status": "DONE",
            "summary": operation_summary,
            "outcome_code": operation_report["outcome_code"],
            "key_findings": [
                f"selected components: {counts['selected_component_count']}",
                f"selected residues: {counts['selected_residue_count']}",
                f"selected atoms: {counts['selected_atom_count']}",
                f"excluded components: {counts['excluded_component_count']}",
            ],
            "created_files": operation_created,
            "modified_files": [],
            "validated_files": [],
            "warnings": operation_warnings,
            "failure": None,
            "detail_files": {
                "log_file": None,
                "report_file": str(operation_report_path),
                "result_data_file": str(manifest_path),
            },
        },
        "validation_result": {
            "skill_name": VALIDATOR_SKILL,
            "status": "DONE",
            "summary": validation_summary,
            "outcome_code": validation_result["outcome_code"],
            "key_findings": [
                f"validated candidate SHA-256: {candidate_hash}",
                f"validation checks: {validation_report['checks']}",
                f"reported differences: {len(validation_report['differences'])}",
            ],
            "created_files": validation_created,
            "modified_files": [],
            "validated_files": [validated_candidate, validated_manifest, validated_mapping],
            "warnings": validation_warnings,
            "failure": None,
            "detail_files": {
                "log_file": None,
                "report_file": str(validation_report_path),
                "result_data_file": str(validation_result_path),
            },
        },
        "artifact_candidates": [
            {
                "artifact_type": "STRUCTURE",
                "files": [validated_candidate],
                "derived_from_artifact_set_ids": derived_ids,
            }
        ],
        "confirmation_items": [],
        "warnings": [*operation_warnings, *validation_warnings],
        "failure": None,
        "next_step_recommendation": "Return the validated STRUCTURE candidate to structure_preparation_workflow for the next substep.",
    }
    _validate_shared(shared_result, contract_dir, "subagent_result.schema.yaml")
    return shared_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--operation-report", required=True, type=Path)
    parser.add_argument("--validation-report", required=True, type=Path)
    parser.add_argument("--validation-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--contract-dir", type=Path, default=Path(__file__).resolve().parents[3] / "03_contracts")
    parser.add_argument("--operation-schema-dir", type=Path, default=Path(__file__).resolve().parent.parent / "schemas")
    parser.add_argument("--validator-schema-dir", type=Path, default=Path(__file__).resolve().parents[3] / "02_validators/chain_and_component_selection_validator/schemas")
    args = parser.parse_args()
    try:
        result = build(args)
        atomic_write_yaml(args.output.resolve(), result)
        return 0
    except SelectionToolError as exc:
        print(f"{exc.code}: {exc}")
        return 1
    except Exception as exc:
        print(f"SHARED_RESULT_INTERNAL_FAILURE: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

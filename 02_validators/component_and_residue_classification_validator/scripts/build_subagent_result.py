#!/usr/bin/env python3
"""Build shared subagent_result v2 from component-classification v1.2 outputs."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    read_yaml_strict,
    sha256_file,
    validate_document,
)

SKILL_NAME = "component_and_residue_classification_validator"
WORKFLOW_NAME = "structure_preparation_workflow"
VERSION = "0.2.0-draft"


def _shared_validator(contract_dir: Path, schema_name: str) -> Draft202012Validator:
    resources = []
    for path in sorted(contract_dir.glob("*.schema.yaml")):
        schema = read_yaml_strict(path)
        identifier = schema.get("$id")
        if isinstance(identifier, str):
            resources.append((identifier, Resource.from_contents(schema)))
    target = read_yaml_strict(contract_dir / schema_name)
    Draft202012Validator.check_schema(target)
    registry = Registry().with_resources(resources)
    return Draft202012Validator(target, registry=registry)


def _validate_shared(document: dict[str, Any], contract_dir: Path, schema_name: str) -> None:
    validator = _shared_validator(contract_dir, schema_name)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = []
        for error in errors[:20]:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{location}: {error.message}")
        raise ClassificationToolError(
            f"shared contract validation failed for {schema_name}: "
            + "; ".join(details)
        )


def _file_record(path: Path, task_id: str, role: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ClassificationToolError(f"expected output is not a regular file: {path}")
    return {
        "path": str(path.resolve()),
        "state": "present_validated",
        "role": role,
        "source_task": task_id,
        "size_bytes": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(
            path.stat().st_mtime,
            timezone.utc,
        ).isoformat(),
        "sha256": sha256_file(path),
    }


def _affected_records(subject: dict[str, Any]) -> list[str]:
    records: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            if "residue_name" in value and "source_resid" in value:
                source_resid = value["source_resid"]
                number = source_resid.get("number") if isinstance(source_resid, dict) else None
                insertion = source_resid.get("insertion_code") if isinstance(source_resid, dict) else None
                chain = value.get("source_chain_id")
                atom = value.get("atom_name")
                label = f"chain={chain!r}/res={number}{insertion or ''}/{value['residue_name']}"
                if atom is not None:
                    label += f"/atom={atom}"
                records.append(label)
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(subject)
    if not records:
        records.append(json.dumps(subject, sort_keys=True, ensure_ascii=False))
    return sorted(set(records))


def _confirmation_items(
    task: dict[str, Any],
    confirmations: dict[str, Any],
) -> list[dict[str, Any]]:
    items = []
    for request in confirmations["requests"]:
        request_index = int(request["request_index"])
        request_type = request["request_type"]
        items.append(
            {
                "schema_version": 2,
                "decision_id": (
                    f"{task['task_id']}:component-classification:{request_index}"
                ),
                "scope": "WORKSTREAM",
                "workstream_id": task["workstream_id"],
                "source_task_id": task["task_id"],
                "category": request_type,
                "question": (
                    f"How should classification request {request_index} "
                    f"({request_type}) be resolved?"
                ),
                "reason": request["reason"],
                "affected_records": _affected_records(request["subject"]),
                "available_options": list(request["allowed_decisions"]),
                "recommended_option": None,
                "blocking": True,
            }
        )
    return items


def _key_findings(result: dict[str, Any]) -> list[str]:
    summary = result["summary"]
    return [
        f"selected model: {result['selected_model_id']}",
        f"classification mode: {result['classification_mode']}",
        f"chain groups: {summary['chain_group_count']}",
        f"standard residues: {summary['standard_residue_count']}",
        (
            "covalently linked nonstandard residues: "
            f"{summary['covalently_linked_nonstandard_count']}"
        ),
        f"independent nonstandard residues: {summary['independent_nonstandard_count']}",
        f"missing residues recorded: {summary['missing_residue_count']}",
        f"heavy-atom issues: {summary['heavy_atom_issue_count']}",
        f"unresolved confirmation items: {summary['unresolved_item_count']}",
    ]


def build(args: argparse.Namespace) -> dict[str, Any]:
    task_path = args.task.resolve()
    result_path = args.classification_result.resolve()
    confirmation_path = args.confirmation_requests.resolve()
    report_path = args.report.resolve()
    log_path = args.log.resolve() if args.log is not None else None
    contract_dir = args.contract_dir.resolve()
    local_schema_dir = args.local_schema_dir.resolve()

    task = read_yaml_strict(task_path)
    _validate_shared(task, contract_dir, "subagent_task.schema.yaml")
    if task["workflow_name"] != WORKFLOW_NAME:
        raise ClassificationToolError(
            f"unexpected workflow_name: {task['workflow_name']}"
        )
    if task["task_unit"]["mode"] != "VALIDATOR":
        raise ClassificationToolError("classification task must use VALIDATOR mode")
    validator_ref = task["task_unit"].get("validator") or {}
    if validator_ref.get("skill_name") != SKILL_NAME:
        raise ClassificationToolError(
            "task validator skill does not reference this classification Validator"
        )

    result = read_yaml_strict(result_path)
    confirmations = read_yaml_strict(confirmation_path)
    validate_document(
        result,
        local_schema_dir / "classification_result.schema.yaml",
    )
    validate_document(
        confirmations,
        local_schema_dir / "confirmation_requests.schema.yaml",
    )
    if result["summary"]["unresolved_item_count"] != len(
        confirmations["requests"]
    ):
        raise ClassificationToolError(
            "classification result and confirmation request counts differ"
        )
    expected_status = (
        "PENDING_USER_CONFIRMATION"
        if confirmations["requests"]
        else "COMPLETE"
    )
    if result["result_status"] != expected_status:
        raise ClassificationToolError(
            "classification result status is inconsistent with confirmation requests"
        )

    output_files = [
        _file_record(confirmation_path, task["task_id"], "confirmation_requests"),
        _file_record(result_path, task["task_id"], "classification_result"),
        _file_record(report_path, task["task_id"], "classification_report"),
    ]
    if log_path is not None and log_path.exists():
        output_files.append(
            _file_record(log_path, task["task_id"], "classification_log")
        )

    confirmation_items = _confirmation_items(task, confirmations)
    outcome_code = (
        "CLASSIFICATION_DECISION_REQUIRED"
        if confirmation_items
        else "CLASSIFIED_CLEAR"
    )
    summary = (
        "Component and residue classification completed; user decisions are required."
        if confirmation_items
        else "Component and residue classification completed without pending decisions."
    )
    shared_result = {
        "schema_version": 2,
        "task_id": task["task_id"],
        "workstream_id": task["workstream_id"],
        "task_unit_mode": "VALIDATOR",
        "status": "DONE",
        "execution_summary": summary,
        "operation_result": None,
        "validation_result": {
            "skill_name": SKILL_NAME,
            "status": "DONE",
            "summary": summary,
            "outcome_code": outcome_code,
            "key_findings": _key_findings(result),
            "created_files": output_files,
            "modified_files": [],
            "validated_files": output_files,
            "warnings": [],
            "failure": None,
            "detail_files": {
                "log_file": str(log_path) if log_path is not None else None,
                "report_file": str(report_path),
                "result_data_file": str(result_path),
            },
        },
        "artifact_candidates": [],
        "confirmation_items": confirmation_items,
        "warnings": [],
        "failure": None,
        "next_step_recommendation": (
            "Pause the Workstream and resolve every returned confirmation item."
            if confirmation_items
            else "Return control to structure_preparation_workflow for its next decision."
        ),
    }
    _validate_shared(shared_result, contract_dir, "subagent_result.schema.yaml")
    return shared_result


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--classification-result", type=Path, required=True)
    parser.add_argument("--confirmation-requests", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--contract-dir",
        type=Path,
        default=repo_root / "03_contracts",
    )
    parser.add_argument(
        "--local-schema-dir",
        type=Path,
        default=script_dir.parent / "schemas",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        document = build(args)
        atomic_write_yaml(args.output.resolve(), document)
        return 0
    except ClassificationToolError as exc:
        print(f"build_subagent_result.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"build_subagent_result.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

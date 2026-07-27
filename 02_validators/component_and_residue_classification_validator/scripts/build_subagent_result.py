#!/usr/bin/env python3
"""Build shared subagent_result v2 for the 1.2 classification Validator."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import RefResolver, validators

from classification_common import ClassificationError, load_yaml, sha256, validate_document

SKILL_NAME = "component_and_residue_classification_validator"
WORKFLOW_NAME = "structure_preparation_workflow"


class ResultBuildError(ClassificationError):
    pass


def _atomic_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(temporary, path)


def _resolve(project_root: Path, value: str) -> Path:
    path = Path(value)
    return (project_root / path).resolve() if not path.is_absolute() else path.resolve()


def _permission_root(project_root: Path, value: str) -> Path:
    cleaned = value.strip()
    for suffix in ("/**", "/*"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return _resolve(project_root, cleaned)


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _matches_permission(path: Path, entries: list[Any], project_root: Path) -> bool:
    for entry in entries:
        if isinstance(entry, str) and entry.strip():
            root = _permission_root(project_root, entry)
            if path.resolve() == root or _within(path, root):
                return True
    return False


def _validate_task(task: dict[str, Any]) -> None:
    if task.get("workflow_name") != WORKFLOW_NAME:
        raise ResultBuildError(f"unexpected workflow_name: {task.get('workflow_name')!r}")
    task_unit = task.get("task_unit") or {}
    if task_unit.get("mode") != "VALIDATOR" or task_unit.get("operation") is not None:
        raise ResultBuildError("task_unit must be VALIDATOR with operation: null")
    validator = task_unit.get("validator") or {}
    if validator.get("skill_name") != SKILL_NAME or validator.get("skill_layer") != "validator":
        raise ResultBuildError("task validator ref does not identify this Validator")
    if task.get("result_contract") != "03_contracts/subagent_result.schema.yaml":
        raise ResultBuildError("unexpected result_contract")


def _enforce_permissions(task: dict[str, Any], paths: list[Path], output_path: Path | None = None) -> None:
    project_root = Path(task["project_root"]).resolve()
    permissions = task.get("permissions") or {}
    allowed_write = permissions.get("allowed_write_paths", [])
    forbidden = permissions.get("forbidden_paths", [])
    for path in [*paths, *([output_path] if output_path is not None else [])]:
        if _matches_permission(path, forbidden, project_root):
            raise ResultBuildError(f"path is inside task forbidden paths: {path}")
    for path in paths:
        if not _matches_permission(path, allowed_write, project_root):
            raise ResultBuildError(f"classification output is outside allowed_write_paths: {path}")


def _file_record(path: Path, task_id: str, role: str, *, state: str = "present_validated") -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ResultBuildError(f"expected regular output file: {path}")
    return {
        "path": str(path),
        "state": state,
        "role": role,
        "source_task": task_id,
        "size_bytes": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "sha256": sha256(path),
    }


def _input_structure_record(task: dict[str, Any], model_scope: dict[str, Any]) -> dict[str, Any]:
    project_root = Path(task["project_root"]).resolve()
    source = model_scope["input_structure"]
    path = _resolve(project_root, source["path"])
    if not path.is_file() or path.is_symlink():
        raise ResultBuildError("model_scope input structure is not a regular file")
    actual_hash = sha256(path)
    if actual_hash != source["sha256"]:
        raise ResultBuildError("input structure hash no longer matches model_scope")
    matches = [
        record
        for record in task.get("current_valid_files", [])
        if isinstance(record, dict)
        and isinstance(record.get("path"), str)
        and _resolve(project_root, record["path"]) == path
    ]
    if len(matches) != 1:
        raise ResultBuildError(f"input structure must match one current_valid_files record; found {len(matches)}")
    record = dict(matches[0])
    record.update(
        path=str(path),
        sha256=actual_hash,
        size_bytes=path.stat().st_size,
        modified_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    )
    record["notes"] = "classification evidence generated; STRUCTURE scientific validation status unchanged"
    return record


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return cleaned or "item"


def _subject_locations(subject: dict[str, Any]) -> list[str]:
    locations: list[str] = []
    for key in ("partner_1", "partner_2", "metal", "donor", "endpoint"):
        item = subject.get(key)
        if not isinstance(item, dict):
            continue
        resid = item.get("source_resid") or {}
        locations.append(
            f"chain_index={item.get('chain_index')};source_chain_id={item.get('source_chain_id')!r};"
            f"residue={item.get('residue_name')}:{resid.get('number')}{resid.get('insertion_code') or ''};"
            f"atom={item.get('atom_name')}"
        )
    if not locations:
        locations.append(yaml.safe_dump(subject, sort_keys=True, allow_unicode=True).strip())
    return locations


def _confirmation_items(
    requests: dict[str, Any], task_id: str, workstream_id: str
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for request in requests.get("requests", []):
        index = int(request["request_index"])
        request_type = str(request["request_type"])
        subject = request.get("subject") or {}
        items.append(
            {
                "schema_version": 2,
                "decision_id": f"decision_{_safe_id(task_id)}_classification_{index:04d}",
                "scope": "WORKSTREAM",
                "workstream_id": workstream_id,
                "source_task_id": task_id,
                "category": request_type,
                "question": f"How should classification request {index} ({request_type}) be resolved?",
                "reason": f"The completed 1.2 scan found an unresolved item from {request.get('source')}",
                "affected_records": _subject_locations(subject),
                "available_options": [str(value) for value in request.get("allowed_decisions", [])],
                "recommended_option": None,
                "blocking": True,
            }
        )
    return items


def _load_schema_bundle(contracts_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    schemas: dict[str, Any] = {}
    store: dict[str, Any] = {}
    for path in sorted(contracts_dir.glob("*.schema.yaml")):
        schema = load_yaml(path)
        if not isinstance(schema, dict):
            raise ResultBuildError(f"invalid shared schema: {path}")
        schemas[path.name] = schema
        store[path.name] = schema
        store[path.resolve().as_uri()] = schema
        if isinstance(schema.get("$id"), str):
            store[schema["$id"]] = schema
    return schemas, store


def _validate_shared(document: dict[str, Any], contracts_dir: Path) -> None:
    schemas, store = _load_schema_bundle(contracts_dir)
    schema = schemas.get("subagent_result.schema.yaml")
    if schema is None:
        raise ResultBuildError("subagent_result.schema.yaml is missing")
    cls = validators.validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema, resolver=RefResolver.from_schema(schema, store=store))
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
            for error in errors[:20]
        )
        raise ResultBuildError(f"subagent_result validation failed: {details}")


def build_result(
    task_path: Path,
    classification_path: Path,
    confirmation_path: Path,
    report_path: Path,
    model_scope_path: Path,
    detail_paths: list[Path],
    contracts_dir: Path,
    classification_schema: Path,
    confirmation_schema: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    task = load_yaml(task_path)
    _validate_task(task)
    classification = load_yaml(classification_path)
    confirmations = load_yaml(confirmation_path)
    model_scope = load_yaml(model_scope_path)
    validate_document(classification, classification_schema)
    validate_document(confirmations, confirmation_schema)

    all_business_paths = [classification_path, confirmation_path, report_path, model_scope_path, *detail_paths]
    _enforce_permissions(task, all_business_paths, output_path)
    task_id = str(task["task_id"])
    workstream_id = str(task["workstream_id"])
    input_record = _input_structure_record(task, model_scope)

    role_by_name = {
        "model_scope.yaml": "classification_model_scope",
        "classification_observations.yaml": "classification_observations",
        "reference_manifest.yaml": "classification_reference_manifest",
        "possible_connections_result.yaml": "possible_connections_result",
        "possible_coordination_result.yaml": "possible_coordination_result",
        "confirmation_requests.yaml": "classification_confirmation_requests",
        "classification_result.yaml": "classification_result",
        "classification_report.md": "classification_report",
    }
    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for path in all_business_paths:
        resolved = path.resolve()
        if resolved not in seen:
            unique_paths.append(resolved)
            seen.add(resolved)
    output_records = [
        _file_record(path, task_id, role_by_name.get(path.name, "classification_detail"))
        for path in unique_paths
    ]

    decision_items = _confirmation_items(confirmations, task_id, workstream_id)
    pending = classification["result_status"] == "PENDING_USER_CONFIRMATION"
    if pending != bool(decision_items):
        raise ResultBuildError("classification_result and confirmation_requests are inconsistent")
    outcome = "CLASSIFICATION_DECISION_REQUIRED" if pending else "CLASSIFIED_CLEAR"
    summary_counts = classification.get("summary", {})
    relations = classification.get("confirmed_relations", [])
    key_findings = [
        f"selected model: {classification['selected_model_id']}",
        f"chain groups: {summary_counts.get('chain_group_count', len(classification.get('chain_groups', [])))}",
        f"confirmed covalent connections: {sum(1 for relation in relations if relation.get('relation_type') == 'COVALENT_CONNECTION')}",
        f"confirmed metal coordination relations: {sum(1 for relation in relations if relation.get('relation_type') == 'METAL_COORDINATION')}",
        f"pending confirmations: {len(decision_items)}",
    ]
    component_result = {
        "skill_name": SKILL_NAME,
        "status": "DONE",
        "summary": "Completed the full 1.2 model/component/residue classification scan."
        if not pending
        else "Completed the full 1.2 scan and accumulated unresolved items for Manager confirmation.",
        "outcome_code": outcome,
        "key_findings": key_findings,
        "created_files": output_records,
        "modified_files": [],
        "validated_files": [input_record, *output_records],
        "warnings": [],
        "failure": None,
        "detail_files": {
            "log_file": task.get("detail_output_paths", {}).get("log_file"),
            "report_file": str(report_path),
            "result_data_file": str(classification_path),
        },
    }
    result = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": workstream_id,
        "task_unit_mode": "VALIDATOR",
        "status": "DONE",
        "execution_summary": component_result["summary"],
        "operation_result": None,
        "validation_result": component_result,
        "artifact_candidates": [],
        "confirmation_items": decision_items,
        "warnings": [],
        "failure": None,
        "next_step_recommendation": "Pause the Workstream and resolve all classification confirmation items."
        if pending
        else "Return to structure_preparation_workflow for the next execution decision.",
    }
    _validate_shared(result, contracts_dir)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--confirmations", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--model-scope", type=Path, required=True)
    parser.add_argument("--detail", type=Path, action="append", default=[])
    parser.add_argument("--contracts-dir", type=Path, required=True)
    parser.add_argument("--classification-schema", type=Path, required=True)
    parser.add_argument("--confirmation-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = build_result(
            args.task,
            args.classification,
            args.confirmations,
            args.report,
            args.model_scope,
            args.detail,
            args.contracts_dir,
            args.classification_schema,
            args.confirmation_schema,
            args.output,
        )
        _atomic_yaml(args.output, result)
    except (ResultBuildError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

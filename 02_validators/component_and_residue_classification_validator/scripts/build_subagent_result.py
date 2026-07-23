#!/usr/bin/env python3
"""Build and validate subagent_result v2 from classification output and task.yaml."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import RefResolver, validators

SKILL_NAME = "component_and_residue_classification_validator"
WORKFLOW_NAME = "structure_preparation_workflow"


class ResultBuildError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def atomic_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    os.replace(temp, path)


def resolve_project_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def permission_base(project_root: Path, value: str) -> Path:
    cleaned = value.strip()
    for suffix in ("/**", "/*"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return resolve_project_path(project_root, cleaned)


def path_allowed(path: Path, entries: list[Any], project_root: Path) -> bool:
    for entry in entries:
        if not isinstance(entry, str) or not entry.strip():
            continue
        base = permission_base(project_root, entry)
        if path.resolve() == base or path_is_within(path, base):
            return True
    return False


def enforce_task_permissions(
    task: dict[str, Any],
    project_root: Path,
    input_path: Path,
    write_paths: list[Path],
) -> None:
    permissions = task.get("permissions")
    if not isinstance(permissions, dict):
        raise ResultBuildError("task.permissions is missing")
    allowed_read = permissions.get("allowed_read_paths", [])
    allowed_write = permissions.get("allowed_write_paths", [])
    forbidden = permissions.get("forbidden_paths", [])
    if not path_allowed(input_path, allowed_read, project_root):
        raise ResultBuildError("input structure is outside task allowed_read_paths")
    for path in [input_path, *write_paths]:
        if path_allowed(path, forbidden, project_root):
            raise ResultBuildError(f"path is inside task forbidden_paths: {path}")
    for path in write_paths:
        if not path_allowed(path, allowed_write, project_root):
            raise ResultBuildError(f"output path is outside task allowed_write_paths: {path}")


def ensure_regular_file(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ResultBuildError(f"{label} must not be a symlink: {path}")
    if not path.is_file():
        raise ResultBuildError(f"{label} is not a regular file: {path}")


def load_schema_bundle(contracts_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    schemas: dict[str, Any] = {}
    store: dict[str, Any] = {}
    for path in sorted(contracts_dir.glob("*.schema.yaml")):
        schema = load_yaml(path)
        if not isinstance(schema, dict):
            raise ResultBuildError(f"schema is not a mapping: {path}")
        schemas[path.name] = schema
        store[path.name] = schema
        store[path.resolve().as_uri()] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            store[schema_id] = schema
    if not schemas:
        raise ResultBuildError(f"no shared schemas found: {contracts_dir}")
    return schemas, store


def validate_document(
    document: Any,
    schema_name: str,
    schemas: dict[str, Any],
    store: dict[str, Any],
) -> None:
    schema = schemas.get(schema_name)
    if schema is None:
        raise ResultBuildError(f"missing schema: {schema_name}")
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    resolver = RefResolver.from_schema(schema, store=store)
    validator = validator_class(schema, resolver=resolver)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        messages = []
        for error in errors[:20]:
            location = ".".join(str(item) for item in error.absolute_path) or "$"
            messages.append(f"{location}: {error.message}")
        raise ResultBuildError(f"{schema_name} validation failed: {'; '.join(messages)}")


def validate_local_classification(document: Any, schema_path: Path) -> None:
    schema = load_yaml(schema_path)
    if not isinstance(schema, dict):
        raise ResultBuildError(f"classification schema is not a mapping: {schema_path}")
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        messages = []
        for error in errors[:20]:
            location = ".".join(str(item) for item in error.absolute_path) or "$"
            messages.append(f"{location}: {error.message}")
        raise ResultBuildError(f"classification output validation failed: {'; '.join(messages)}")


def validate_task_semantics(task: dict[str, Any]) -> None:
    if task.get("workflow_name") != WORKFLOW_NAME:
        raise ResultBuildError(
            f"unexpected workflow_name: {task.get('workflow_name')!r}; expected {WORKFLOW_NAME}"
        )
    task_unit = task.get("task_unit")
    if not isinstance(task_unit, dict) or task_unit.get("mode") != "VALIDATOR":
        raise ResultBuildError("task_unit.mode must be VALIDATOR")
    if task_unit.get("operation") is not None:
        raise ResultBuildError("VALIDATOR task must have operation: null")
    validator_ref = task_unit.get("validator")
    if not isinstance(validator_ref, dict):
        raise ResultBuildError("VALIDATOR task is missing validator ref")
    if validator_ref.get("skill_name") != SKILL_NAME:
        raise ResultBuildError(
            f"validator skill mismatch: {validator_ref.get('skill_name')!r}"
        )
    if validator_ref.get("skill_layer") != "validator":
        raise ResultBuildError("validator skill_layer must be validator")
    if task.get("result_contract") != "03_contracts/subagent_result.schema.yaml":
        raise ResultBuildError("unexpected result_contract")


def find_input_record(
    task: dict[str, Any],
    project_root: Path,
    classification: dict[str, Any],
) -> dict[str, Any]:
    input_structure = classification.get("input_structure")
    if not isinstance(input_structure, dict):
        raise ResultBuildError("classification input_structure is missing")
    raw_path = input_structure.get("path")
    expected_hash = input_structure.get("sha256")
    if not isinstance(raw_path, str) or not isinstance(expected_hash, str):
        raise ResultBuildError("classification input_structure path/sha256 is invalid")
    actual_path = resolve_project_path(project_root, raw_path)
    ensure_regular_file(actual_path, "input structure")
    actual_hash = sha256(actual_path)
    if actual_hash.lower() != expected_hash.lower():
        raise ResultBuildError("input structure SHA-256 no longer matches classification output")

    matches = []
    for record in task.get("current_valid_files", []):
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            continue
        if resolve_project_path(project_root, record["path"]) == actual_path:
            matches.append(record)
    if len(matches) != 1:
        raise ResultBuildError(
            f"classification input must match exactly one task.current_valid_files record; found {len(matches)}"
        )

    record = dict(matches[0])
    record["sha256"] = actual_hash
    record["size_bytes"] = actual_path.stat().st_size
    record["modified_at"] = iso_mtime(actual_path)
    note = "classified by component_and_residue_classification_validator; structure scientific status unchanged"
    existing_note = record.get("notes")
    record["notes"] = f"{existing_note}; {note}" if existing_note else note
    return record


def check_detail_paths(
    task: dict[str, Any],
    project_root: Path,
    classification_path: Path,
    report_path: Path,
) -> dict[str, str | None]:
    details = task.get("detail_output_paths")
    if not isinstance(details, dict):
        raise ResultBuildError("task.detail_output_paths is missing")
    raw_report = details.get("report_file")
    raw_data = details.get("result_data_file")
    if not isinstance(raw_report, str) or not isinstance(raw_data, str):
        raise ResultBuildError("task report_file and result_data_file must be non-null strings")
    if resolve_project_path(project_root, raw_report) != report_path.resolve():
        raise ResultBuildError("report path does not match task.detail_output_paths.report_file")
    if resolve_project_path(project_root, raw_data) != classification_path.resolve():
        raise ResultBuildError(
            "classification path does not match task.detail_output_paths.result_data_file"
        )
    ensure_regular_file(report_path, "classification report")
    ensure_regular_file(classification_path, "classification result data")
    log_file = details.get("log_file")
    if log_file is not None and not isinstance(log_file, str):
        raise ResultBuildError("task.detail_output_paths.log_file must be string or null")
    return {
        "log_file": log_file,
        "report_file": raw_report,
        "result_data_file": raw_data,
    }


def file_record(path: Path, display_path: str, task_id: str, role: str) -> dict[str, Any]:
    return {
        "path": display_path,
        "state": "present_validated",
        "role": role,
        "source_task": task_id,
        "size_bytes": path.stat().st_size,
        "modified_at": iso_mtime(path),
        "sha256": sha256(path),
    }


def warning_objects(messages: list[Any], affected_paths: list[str]) -> list[dict[str, Any]]:
    result = []
    for index, message in enumerate(messages, start=1):
        if not isinstance(message, str) or not message.strip():
            continue
        result.append(
            {
                "code": f"CLASSIFICATION_WARNING_{index:03d}",
                "message": message.strip(),
                "affected_paths": affected_paths,
            }
        )
    return result


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return cleaned or "item"


def confirmation_items(
    ambiguities: list[Any],
    task_id: str,
    workstream_id: str,
) -> list[dict[str, Any]]:
    result = []
    used: set[str] = set()
    for index, item in enumerate(ambiguities, start=1):
        if not isinstance(item, dict):
            raise ResultBuildError(f"ambiguity {index} is not a mapping")
        source_id = str(item.get("ambiguity_id") or f"ambiguity_{index:04d}")
        decision_id = f"decision_{safe_id(task_id)}_{safe_id(source_id)}"
        if decision_id in used:
            decision_id = f"{decision_id}_{index}"
        used.add(decision_id)
        question = item.get("question")
        reason = item.get("reason")
        if not isinstance(question, str) or not question.strip():
            raise ResultBuildError(f"ambiguity {source_id} has no question")
        if not isinstance(reason, str) or not reason.strip():
            raise ResultBuildError(f"ambiguity {source_id} has no reason")
        affected = item.get("affected_object_ids", [])
        options = item.get("options", [])
        if not isinstance(affected, list) or not all(isinstance(v, str) for v in affected):
            raise ResultBuildError(f"ambiguity {source_id} affected_object_ids is invalid")
        if not isinstance(options, list) or not all(isinstance(v, str) for v in options):
            raise ResultBuildError(f"ambiguity {source_id} options is invalid")
        result.append(
            {
                "schema_version": 2,
                "decision_id": decision_id,
                "scope": "WORKSTREAM",
                "workstream_id": workstream_id,
                "source_task_id": task_id,
                "category": str(item.get("category") or "CLASSIFICATION"),
                "question": question.strip(),
                "reason": reason.strip(),
                "affected_records": affected,
                "available_options": options,
                "recommended_option": item.get("recommended_option"),
                "blocking": bool(item.get("blocking", True)),
            }
        )
    return result


def build_summary(classification: dict[str, Any]) -> tuple[str, list[str]]:
    summary = classification.get("summary")
    if not isinstance(summary, dict):
        raise ResultBuildError("classification summary is missing")
    execution_summary = (
        f"完成组分与残基分类：{summary.get('model_count', 0)} 个模型、"
        f"{summary.get('chain_count', 0)} 条链、{summary.get('component_count', 0)} 个组分、"
        f"{summary.get('residue_count', 0)} 个残基；"
        f"blocking 歧义 {summary.get('blocking_ambiguity_count', 0)} 项。"
    )
    key_findings = [
        (
            "残基分类："
            f"标准 {summary.get('standard_residue_count', 0)}，"
            f"相连非标准 {summary.get('covalently_linked_nonstandard_count', 0)}，"
            f"独立非标准 {summary.get('independent_nonstandard_count', 0)}，"
            f"溶剂 {summary.get('solvent_count', 0)}，"
            f"离子 {summary.get('ion_count', 0)}，"
            f"未知 {summary.get('unknown_count', 0)}。"
        ),
        (
            "连接证据："
            f"显式连接 {len(classification.get('explicit_connections', []))}，"
            f"几何共价候选 {len(classification.get('covalent_candidates', []))}，"
            f"配位候选 {len(classification.get('coordination_candidates', []))}。"
        ),
        f"分类 outcome：{classification.get('outcome_code')}",
    ]
    return execution_summary, key_findings


def output_conflict(path: Path, task_id: str) -> None:
    if not path.exists():
        return
    if path.is_symlink() or not path.is_file():
        raise ResultBuildError(f"output path is not a regular file: {path}")
    old = load_yaml(path)
    if not isinstance(old, dict) or old.get("task_id") != task_id:
        raise ResultBuildError(f"output belongs to another task and will not be overwritten: {path}")


def build_result(
    task_path: Path,
    classification_path: Path,
    report_path: Path,
    contracts_dir: Path,
    classification_schema: Path,
) -> dict[str, Any]:
    ensure_regular_file(task_path, "task")
    ensure_regular_file(classification_path, "classification result data")
    ensure_regular_file(report_path, "classification report")

    schemas, store = load_schema_bundle(contracts_dir)
    task = load_yaml(task_path)
    if not isinstance(task, dict):
        raise ResultBuildError("task.yaml is not a mapping")
    validate_document(task, "subagent_task.schema.yaml", schemas, store)
    validate_task_semantics(task)

    classification = load_yaml(classification_path)
    if not isinstance(classification, dict):
        raise ResultBuildError("classification result data is not a mapping")
    validate_local_classification(classification, classification_schema)

    if classification.get("task_id") != task.get("task_id"):
        raise ResultBuildError("classification task_id does not match task.yaml")
    if classification.get("workstream_id") != task.get("workstream_id"):
        raise ResultBuildError("classification workstream_id does not match task.yaml")

    project_root = Path(task["project_root"]).resolve()
    if not project_root.is_dir():
        raise ResultBuildError(f"project_root is not a directory: {project_root}")

    details = check_detail_paths(
        task,
        project_root,
        classification_path,
        report_path,
    )
    input_record = find_input_record(task, project_root, classification)
    input_actual = resolve_project_path(project_root, input_record["path"])
    enforce_task_permissions(
        task,
        project_root,
        input_actual,
        [classification_path.resolve(), report_path.resolve()],
    )

    report_record = file_record(
        report_path,
        str(details["report_file"]),
        task["task_id"],
        "component_and_residue_classification_report",
    )
    data_record = file_record(
        classification_path,
        str(details["result_data_file"]),
        task["task_id"],
        "component_and_residue_classification_result_data",
    )

    warnings = warning_objects(
        classification.get("warnings", []),
        [str(details["report_file"]), str(details["result_data_file"])],
    )
    decisions = confirmation_items(
        classification.get("ambiguities", []),
        task["task_id"],
        task["workstream_id"],
    )
    execution_summary, key_findings = build_summary(classification)
    outcome = classification.get("outcome_code")
    allowed_success = {
        "CLASSIFIED_CLEAR",
        "CLASSIFIED_WITH_WARNINGS",
        "CLASSIFICATION_DECISION_REQUIRED",
    }
    if outcome not in allowed_success:
        raise ResultBuildError(
            f"classification outcome cannot be wrapped as successful result: {outcome}"
        )
    blocking_decisions = [item for item in decisions if item["blocking"]]
    if outcome == "CLASSIFICATION_DECISION_REQUIRED" and not blocking_decisions:
        raise ResultBuildError(
            "CLASSIFICATION_DECISION_REQUIRED requires at least one blocking confirmation item"
        )
    if outcome != "CLASSIFICATION_DECISION_REQUIRED" and blocking_decisions:
        raise ResultBuildError(
            f"outcome {outcome} is inconsistent with blocking classification decisions"
        )

    recommendation = (
        "暂停并解析 blocking classification decisions；完成后重新请求 structure_preparation_workflow。"
        if blocking_decisions
        else "进入 1.3 chain_and_component_selection。"
    )
    component_result = {
        "skill_name": SKILL_NAME,
        "status": "DONE",
        "summary": execution_summary,
        "outcome_code": outcome,
        "key_findings": key_findings,
        "created_files": [report_record, data_record],
        "modified_files": [],
        "validated_files": [input_record],
        "warnings": warnings,
        "failure": None,
        "detail_files": details,
    }
    result = {
        "schema_version": 2,
        "task_id": task["task_id"],
        "workstream_id": task["workstream_id"],
        "task_unit_mode": "VALIDATOR",
        "status": "DONE",
        "execution_summary": execution_summary,
        "operation_result": None,
        "validation_result": component_result,
        "artifact_candidates": [],
        "confirmation_items": decisions,
        "warnings": warnings,
        "failure": None,
        "next_step_recommendation": recommendation,
    }
    validate_document(result, "subagent_result.schema.yaml", schemas, store)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    skill_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--classification", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--contracts-dir", required=True, type=Path)
    parser.add_argument(
        "--classification-schema",
        type=Path,
        default=skill_root / "schemas/classification_outputs.schema.yaml",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = build_result(
            args.task.resolve(),
            args.classification.resolve(),
            args.report.resolve(),
            args.contracts_dir.resolve(),
            args.classification_schema.resolve(),
        )
        if args.output:
            output = args.output.resolve()
            task = load_yaml(args.task.resolve())
            project_root = Path(task["project_root"]).resolve()
            permissions = task.get("permissions", {})
            if path_allowed(output, permissions.get("forbidden_paths", []), project_root):
                raise ResultBuildError(
                    "subagent wrapper must not write shared result into task forbidden paths"
                )
            if not path_allowed(output, permissions.get("allowed_write_paths", []), project_root):
                raise ResultBuildError(
                    "subagent wrapper output is outside task allowed_write_paths"
                )
            output_conflict(output, result["task_id"])
            atomic_yaml(output, result)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except ResultBuildError as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except Exception as error:
        print(
            json.dumps(
                {"status": "FAILED", "error": f"internal failure: {error}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

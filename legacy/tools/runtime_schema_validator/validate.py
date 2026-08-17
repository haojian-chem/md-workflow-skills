#!/usr/bin/env python3
"""Deterministic runtime schema validator for MD workflow projects.

Exit codes:
  0: validation passed
  1: validation or direct-reference checks failed
  2: tool/configuration failure
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import RefResolver, validators


@dataclass(frozen=True)
class ValidationTarget:
    actual_path: Path
    logical_path: Path
    schema_name: str
    kind: str = "yaml"


@dataclass(frozen=True)
class ValidatedDocument:
    actual_path: Path
    logical_path: Path
    schema_name: str
    document: Any


class ToolError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json_lines(path: Path) -> list[tuple[int, Any]]:
    rows: list[tuple[int, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            rows.append((line_number, json.loads(raw)))
    return rows


def load_markdown_front_matter(path: Path) -> Any:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ToolError(f"missing YAML front matter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ToolError(f"unterminated YAML front matter: {path}") from exc
    return yaml.safe_load("\n".join(lines[1:end]))


def schema_bundle_hash(schema_files: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(schema_files, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_schema_bundle(contracts_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[Path]]:
    schema_files = sorted(contracts_dir.glob("*.schema.yaml"))
    if not schema_files:
        raise ToolError(f"no schema files found in {contracts_dir}")

    schemas: dict[str, Any] = {}
    store: dict[str, Any] = {}
    for path in schema_files:
        document = load_yaml(path)
        if not isinstance(document, dict):
            raise ToolError(f"schema is not a mapping: {path}")
        schemas[path.name] = document
        store[path.name] = document
        store[path.resolve().as_uri()] = document
        schema_id = document.get("$id")
        if isinstance(schema_id, str) and schema_id:
            store[schema_id] = document
    return schemas, store, schema_files


def ensure_schema_meta_validated(
    schemas: dict[str, Any],
    schema_files: list[Path],
    cache_dir: Path,
    force: bool,
) -> tuple[str, bool]:
    bundle_hash = schema_bundle_hash(schema_files)
    cache_file = cache_dir / f"{bundle_hash}.json"
    if not force and cache_file.is_file():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("schema_bundle_hash") == bundle_hash and cached.get("status") == "PASS":
                return bundle_hash, True
        except (OSError, json.JSONDecodeError):
            pass

    for schema_name, schema in schemas.items():
        validator_class = validators.validator_for(schema)
        try:
            validator_class.check_schema(schema)
        except Exception as exc:
            raise ToolError(f"schema meta-validation failed for {schema_name}: {exc}") from exc

    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_bundle_hash": bundle_hash,
        "status": "PASS",
        "schema_count": len(schemas),
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }
    temp = cache_file.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, cache_file)
    return bundle_hash, False


def normalize_project_path(project_root: Path, path: Path) -> Path:
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def infer_schema_name(project_root: Path, logical_path: Path) -> str | None:
    try:
        relative = logical_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        relative = logical_path

    name = logical_path.name
    parts = relative.parts
    relative_text = relative.as_posix()

    if name == "project_state.yaml":
        return "project_state.schema.yaml"
    if len(parts) >= 3 and parts[:2] == ("00_project_state", "workstreams") and logical_path.suffix in {".yaml", ".yml"}:
        return "workstream_state.schema.yaml"
    if name == "task.yaml":
        return "subagent_task.schema.yaml"
    if name == "result.yaml":
        return "subagent_result.schema.yaml"
    if "/routes/" in f"/{relative_text}":
        return "route_record.schema.yaml"
    if "/decisions/" in f"/{relative_text}":
        return "decision_record.schema.yaml"
    if "/submissions/" in f"/{relative_text}":
        return "submission_record.schema.yaml"
    if "/artifacts/" in f"/{relative_text}":
        return "artifact_set.schema.yaml"
    if relative_text.startswith("00_project_records/state_snapshots/") and logical_path.suffix in {".yaml", ".yml"}:
        return "state_snapshot.schema.yaml"
    if relative_text.startswith("00_project_records/manager/sessions/") and logical_path.suffix == ".md":
        return "manager_session.schema.yaml"
    if name == "project_events.jsonl":
        return "project_event.schema.yaml"
    return None


def target_kind(path: Path) -> str:
    if path.suffix == ".jsonl":
        return "jsonl"
    if path.suffix == ".md":
        return "markdown"
    return "yaml"


def parse_path_map(values: list[str], project_root: Path, label: str) -> dict[Path, str]:
    mapping: dict[Path, str] = {}
    for value in values:
        if "=" not in value:
            raise ToolError(f"invalid {label} value, expected PATH=VALUE: {value}")
        raw_path, mapped = value.split("=", 1)
        actual = normalize_project_path(project_root, Path(raw_path))
        mapping[actual] = mapped.strip()
    return mapping


def discover_full_targets(project_root: Path) -> list[ValidationTarget]:
    candidates: list[Path] = []
    project_state = project_root / "00_project_state/project_state.yaml"
    if project_state.is_file():
        candidates.append(project_state)

    patterns = [
        "00_project_state/workstreams/*.yaml",
        "00_project_records/workstreams/*/routes/*.yaml",
        "00_project_records/workstreams/*/tasks/*/task.yaml",
        "00_project_records/workstreams/*/tasks/*/result.yaml",
        "00_project_records/workstreams/*/decisions/*.yaml",
        "00_project_records/workstreams/*/submissions/*.yaml",
        "00_project_records/workstreams/*/artifacts/*.yaml",
        "00_project_records/state_snapshots/*.yaml",
        "00_project_records/manager/sessions/*.md",
        "00_project_records/events/project_events.jsonl",
    ]
    for pattern in patterns:
        candidates.extend(project_root.glob(pattern))

    targets: list[ValidationTarget] = []
    seen: set[Path] = set()
    for path in candidates:
        actual = path.resolve()
        if actual in seen or not path.is_file() or path.is_symlink():
            continue
        seen.add(actual)
        schema_name = infer_schema_name(project_root, actual)
        if schema_name:
            targets.append(
                ValidationTarget(
                    actual_path=actual,
                    logical_path=actual,
                    schema_name=schema_name,
                    kind=target_kind(actual),
                )
            )
    return sorted(targets, key=lambda item: item.logical_path.as_posix())


def discover_changed_targets(
    project_root: Path,
    changed: list[str],
    schema_overrides: dict[Path, str],
    logical_overrides: dict[Path, str],
) -> list[ValidationTarget]:
    targets: list[ValidationTarget] = []
    for raw in changed:
        actual = normalize_project_path(project_root, Path(raw))
        if not actual.is_file():
            raise ToolError(f"changed path is not a regular file: {actual}")
        if actual.is_symlink():
            raise ToolError(f"symlink target is not accepted: {actual}")

        raw_logical = logical_overrides.get(actual)
        logical = normalize_project_path(project_root, Path(raw_logical)) if raw_logical else actual
        schema_name = schema_overrides.get(actual) or infer_schema_name(project_root, logical)
        if not schema_name:
            raise ToolError(f"no runtime schema mapping for changed path: {actual}; logical path: {logical}")
        targets.append(
            ValidationTarget(
                actual_path=actual,
                logical_path=logical,
                schema_name=schema_name,
                kind=target_kind(logical),
            )
        )
    return targets


def merge_targets(primary: list[ValidationTarget], overlay: list[ValidationTarget]) -> list[ValidationTarget]:
    by_logical: dict[Path, ValidationTarget] = {item.logical_path: item for item in primary}
    for item in overlay:
        by_logical[item.logical_path] = item
    return sorted(by_logical.values(), key=lambda item: item.logical_path.as_posix())


def format_error_path(path: Iterable[Any]) -> str:
    parts = [str(item) for item in path]
    return ".".join(parts) if parts else "$"


def validate_document(
    document: Any,
    schema_name: str,
    schemas: dict[str, Any],
    store: dict[str, Any],
) -> list[dict[str, str]]:
    if schema_name not in schemas:
        raise ToolError(f"schema not found: {schema_name}")
    schema = schemas[schema_name]
    validator_class = validators.validator_for(schema)
    resolver = RefResolver.from_schema(schema, store=store)
    validator = validator_class(schema, resolver=resolver)
    return [
        {
            "instance_path": format_error_path(error.absolute_path),
            "schema_path": format_error_path(error.absolute_schema_path),
            "message": error.message,
        }
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]


def read_target_documents(target: ValidationTarget) -> list[tuple[str, Any]]:
    if target.kind == "jsonl":
        return [(f"line:{number}", document) for number, document in load_json_lines(target.actual_path)]
    if target.kind == "markdown":
        return [("front_matter", load_markdown_front_matter(target.actual_path))]
    return [("document", load_yaml(target.actual_path))]


def collect_existing_record_ids(project_root: Path) -> dict[str, set[str]]:
    ids: dict[str, set[str]] = {
        "task": set(),
        "route": set(),
        "artifact": set(),
        "decision": set(),
        "submission": set(),
        "event": set(),
    }
    patterns = {
        "task": ("00_project_records/workstreams/*/tasks/*/task.yaml", "task_id"),
        "route": ("00_project_records/workstreams/*/routes/*.yaml", "route_id"),
        "artifact": ("00_project_records/workstreams/*/artifacts/*.yaml", "artifact_set_id"),
        "decision": ("00_project_records/workstreams/*/decisions/*.yaml", "decision_id"),
        "submission": ("00_project_records/workstreams/*/submissions/*.yaml", "submission_id"),
    }
    for kind, (pattern, field) in patterns.items():
        for path in project_root.glob(pattern):
            try:
                data = load_yaml(path)
            except Exception:
                continue
            value = data.get(field) if isinstance(data, dict) else None
            if isinstance(value, str):
                ids[kind].add(value)

    events_path = project_root / "00_project_records/events/project_events.jsonl"
    if events_path.is_file():
        try:
            for _, event in load_json_lines(events_path):
                value = event.get("event_id") if isinstance(event, dict) else None
                if isinstance(value, str):
                    ids["event"].add(value)
        except Exception:
            pass
    return ids


def add_candidate_ids(ids: dict[str, set[str]], documents: list[ValidatedDocument]) -> None:
    schema_to_id = {
        "subagent_task.schema.yaml": ("task", "task_id"),
        "route_record.schema.yaml": ("route", "route_id"),
        "artifact_set.schema.yaml": ("artifact", "artifact_set_id"),
        "decision_record.schema.yaml": ("decision", "decision_id"),
        "submission_record.schema.yaml": ("submission", "submission_id"),
        "project_event.schema.yaml": ("event", "event_id"),
    }
    for item in documents:
        mapping = schema_to_id.get(item.schema_name)
        if not mapping or not isinstance(item.document, dict):
            continue
        kind, field = mapping
        value = item.document.get(field)
        if isinstance(value, str):
            ids[kind].add(value)


def add_missing_reference(
    errors: list[dict[str, str]],
    source: ValidatedDocument,
    field: str,
    value: str,
    target_kind: str,
) -> None:
    errors.append(
        {
            "file": str(source.actual_path),
            "logical_path": str(source.logical_path),
            "instance_path": field,
            "schema_path": "direct_reference",
            "message": f"missing {target_kind} reference: {value}",
        }
    )


def check_direct_references(
    project_root: Path,
    documents: list[ValidatedDocument],
) -> list[dict[str, str]]:
    ids = collect_existing_record_ids(project_root)
    add_candidate_ids(ids, documents)
    candidate_logical_paths = {item.logical_path.resolve() for item in documents}
    errors: list[dict[str, str]] = []

    for item in documents:
        data = item.document
        if not isinstance(data, dict):
            continue

        if item.schema_name == "project_state.schema.yaml":
            for workstream in data.get("workstreams", []):
                if not isinstance(workstream, dict):
                    continue
                state_path = workstream.get("state_path")
                if not isinstance(state_path, str):
                    continue
                target = normalize_project_path(project_root, Path(state_path))
                if not target.is_file() and target not in candidate_logical_paths:
                    add_missing_reference(errors, item, "workstreams[].state_path", state_path, "workstream state path")

        elif item.schema_name == "workstream_state.schema.yaml":
            for field, kind in (
                ("active_route_id", "route"),
                ("active_task_id", "task"),
                ("last_event_id", "event"),
            ):
                value = data.get(field)
                if isinstance(value, str) and value not in ids[kind]:
                    add_missing_reference(errors, item, field, value, kind)
            for value in data.get("pending_decision_ids", []):
                if isinstance(value, str) and value not in ids["decision"]:
                    add_missing_reference(errors, item, "pending_decision_ids", value, "decision")
            for value in data.get("active_submission_ids", []):
                if isinstance(value, str) and value not in ids["submission"]:
                    add_missing_reference(errors, item, "active_submission_ids", value, "submission")
            artifact_groups = data.get("current_artifact_set_ids", {})
            if isinstance(artifact_groups, dict):
                for group, values in artifact_groups.items():
                    if isinstance(values, list):
                        for value in values:
                            if isinstance(value, str) and value not in ids["artifact"]:
                                add_missing_reference(errors, item, f"current_artifact_set_ids.{group}", value, "artifact")

        elif item.schema_name == "subagent_result.schema.yaml":
            task_id = data.get("task_id")
            if isinstance(task_id, str) and task_id not in ids["task"]:
                add_missing_reference(errors, item, "task_id", task_id, "task")

        elif item.schema_name == "artifact_set.schema.yaml":
            for field in ("created_by_task_id", "validator_task_id"):
                value = data.get(field)
                if isinstance(value, str) and value not in ids["task"]:
                    add_missing_reference(errors, item, field, value, "task")
            supersedes = data.get("supersedes")
            if isinstance(supersedes, str) and supersedes not in ids["artifact"]:
                add_missing_reference(errors, item, "supersedes", supersedes, "artifact")
            for value in data.get("derived_from", []):
                if isinstance(value, str) and value not in ids["artifact"]:
                    add_missing_reference(errors, item, "derived_from", value, "artifact")

        elif item.schema_name == "route_record.schema.yaml":
            scope_resolution = data.get("scope_resolution", {})
            if isinstance(scope_resolution, dict):
                event_id = scope_resolution.get("resolved_event_id")
                if isinstance(event_id, str) and event_id not in ids["event"]:
                    add_missing_reference(errors, item, "scope_resolution.resolved_event_id", event_id, "event")
                decision_id = scope_resolution.get("decision_id")
                if isinstance(decision_id, str) and decision_id not in ids["decision"]:
                    add_missing_reference(errors, item, "scope_resolution.decision_id", decision_id, "decision")

    return errors


def emit(payload: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_suffix(output.suffix + ".tmp")
        temp.write_text(text + "\n", encoding="utf-8")
        os.replace(temp, output)
    print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("FAST", "FULL"))
    parser.add_argument("--changed", nargs="*", default=[])
    parser.add_argument("--schema-map", action="append", default=[], metavar="PATH=SCHEMA")
    parser.add_argument("--logical-map", action="append", default=[], metavar="PATH=PROJECT_PATH")
    parser.add_argument("--contracts-dir", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force-schema-check", action="store_true")
    parser.add_argument("--skip-reference-check", action="store_true")
    return parser


def main() -> int:
    started = time.perf_counter()
    args = build_parser().parse_args()
    project_root = args.project_root.resolve()
    contracts_dir = (args.contracts_dir or project_root / "03_contracts").resolve()
    cache_dir = (args.cache_dir or project_root / ".md_workflow_cache/runtime_schema_validator").resolve()

    try:
        if not project_root.is_dir():
            raise ToolError(f"project root is not a directory: {project_root}")
        schemas, store, schema_files = load_schema_bundle(contracts_dir)
        bundle_hash, cache_hit = ensure_schema_meta_validated(
            schemas, schema_files, cache_dir, args.force_schema_check
        )

        schema_overrides = parse_path_map(args.schema_map, project_root, "--schema-map")
        logical_overrides = parse_path_map(args.logical_map, project_root, "--logical-map")
        changed_targets = discover_changed_targets(
            project_root, args.changed, schema_overrides, logical_overrides
        ) if args.changed else []

        if args.mode == "FAST":
            if not changed_targets:
                raise ToolError("FAST mode requires at least one valid --changed path")
            targets = changed_targets
        else:
            targets = merge_targets(discover_full_targets(project_root), changed_targets)

        errors: list[dict[str, str]] = []
        validated: list[dict[str, str]] = []
        documents: list[ValidatedDocument] = []

        for target in targets:
            try:
                target_documents = read_target_documents(target)
                for label, document in target_documents:
                    for error in validate_document(document, target.schema_name, schemas, store):
                        error["file"] = str(target.actual_path)
                        error["logical_path"] = str(target.logical_path)
                        error["document"] = label
                        errors.append(error)
                    documents.append(
                        ValidatedDocument(
                            actual_path=target.actual_path,
                            logical_path=target.logical_path,
                            schema_name=target.schema_name,
                            document=document,
                        )
                    )
                validated.append(
                    {
                        "path": str(target.actual_path),
                        "logical_path": str(target.logical_path),
                        "schema": target.schema_name,
                    }
                )
            except Exception as exc:
                errors.append(
                    {
                        "file": str(target.actual_path),
                        "logical_path": str(target.logical_path),
                        "instance_path": "$",
                        "schema_path": target.schema_name,
                        "message": str(exc),
                    }
                )

        if not args.skip_reference_check:
            errors.extend(check_direct_references(project_root, documents))

        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        status = "PASS" if not errors else "FAIL"
        emit(
            {
                "status": status,
                "mode": args.mode,
                "schema_bundle_hash": bundle_hash,
                "schema_cache_hit": cache_hit,
                "validated": validated,
                "errors": errors,
                "warnings": [],
                "elapsed_ms": elapsed_ms,
            },
            args.output,
        )
        return 0 if status == "PASS" else 1

    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        emit(
            {
                "status": "ERROR",
                "mode": args.mode,
                "schema_bundle_hash": None,
                "schema_cache_hit": False,
                "validated": [],
                "errors": [{"message": str(exc)}],
                "warnings": [],
                "elapsed_ms": elapsed_ms,
            },
            args.output,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())

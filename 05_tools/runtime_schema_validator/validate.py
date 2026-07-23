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
    path: Path
    schema_name: str
    kind: str = "yaml"


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
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
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

    by_name: dict[str, Any] = {}
    store: dict[str, Any] = {}
    for path in schema_files:
        document = load_yaml(path)
        if not isinstance(document, dict):
            raise ToolError(f"schema is not a mapping: {path}")
        by_name[path.name] = document
        store[path.name] = document
        store[path.resolve().as_uri()] = document
        schema_id = document.get("$id")
        if isinstance(schema_id, str) and schema_id:
            store[schema_id] = document
    return by_name, store, schema_files


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
        except Exception as exc:  # jsonschema exposes several subclasses
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


def infer_schema_name(project_root: Path, path: Path) -> str | None:
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        relative = path

    name = path.name
    parts = relative.parts
    relative_text = relative.as_posix()

    if name == "project_state.yaml":
        return "project_state.schema.yaml"
    if len(parts) >= 3 and parts[:2] == ("00_project_state", "workstreams") and path.suffix in {".yaml", ".yml"}:
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
    if relative_text.startswith("00_project_records/state_snapshots/") and path.suffix in {".yaml", ".yml"}:
        return "state_snapshot.schema.yaml"
    if relative_text.startswith("00_project_records/manager/sessions/") and path.suffix == ".md":
        return "manager_session.schema.yaml"
    if name == "project_events.jsonl":
        return "project_event.schema.yaml"
    return None


def discover_full_targets(project_root: Path) -> list[ValidationTarget]:
    candidates: list[Path] = []
    fixed = project_root / "00_project_state" / "project_state.yaml"
    if fixed.is_file():
        candidates.append(fixed)

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
        resolved = path.resolve()
        if resolved in seen or not path.is_file() or path.is_symlink():
            continue
        seen.add(resolved)
        schema_name = infer_schema_name(project_root, path)
        if schema_name:
            kind = "jsonl" if path.suffix == ".jsonl" else "markdown" if path.suffix == ".md" else "yaml"
            targets.append(ValidationTarget(path=path, schema_name=schema_name, kind=kind))
    return sorted(targets, key=lambda target: target.path.as_posix())


def parse_schema_overrides(values: list[str], project_root: Path) -> dict[Path, str]:
    overrides: dict[Path, str] = {}
    for value in values:
        if "=" not in value:
            raise ToolError(f"invalid --schema-map value, expected PATH=SCHEMA: {value}")
        raw_path, schema_name = value.split("=", 1)
        path = Path(raw_path)
        if not path.is_absolute():
            path = project_root / path
        overrides[path.resolve()] = schema_name.strip()
    return overrides


def discover_fast_targets(
    project_root: Path,
    changed: list[str],
    overrides: dict[Path, str],
) -> tuple[list[ValidationTarget], list[str]]:
    targets: list[ValidationTarget] = []
    warnings: list[str] = []
    for raw in changed:
        path = Path(raw)
        if not path.is_absolute():
            path = project_root / path
        path = path.resolve()
        if not path.exists():
            warnings.append(f"changed path does not exist and was not validated: {path}")
            continue
        if path.is_symlink():
            raise ToolError(f"symlink target is not accepted: {path}")
        schema_name = overrides.get(path) or infer_schema_name(project_root, path)
        if not schema_name:
            warnings.append(f"no runtime schema mapping for changed path: {path}")
            continue
        kind = "jsonl" if path.suffix == ".jsonl" else "markdown" if path.suffix == ".md" else "yaml"
        targets.append(ValidationTarget(path=path, schema_name=schema_name, kind=kind))
    return targets, warnings


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
    errors: list[dict[str, str]] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path)):
        errors.append(
            {
                "instance_path": format_error_path(error.absolute_path),
                "schema_path": format_error_path(error.absolute_schema_path),
                "message": error.message,
            }
        )
    return errors


def read_target_documents(target: ValidationTarget) -> list[tuple[str, Any]]:
    if target.kind == "jsonl":
        return [(f"line:{line_number}", document) for line_number, document in load_json_lines(target.path)]
    if target.kind == "markdown":
        return [("front_matter", load_markdown_front_matter(target.path))]
    return [("document", load_yaml(target.path))]


def collect_record_ids(project_root: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {
        "task": set(),
        "route": set(),
        "artifact": set(),
        "decision": set(),
        "submission": set(),
        "event": set(),
    }
    file_patterns = {
        "task": "00_project_records/workstreams/*/tasks/*/task.yaml",
        "route": "00_project_records/workstreams/*/routes/*.yaml",
        "artifact": "00_project_records/workstreams/*/artifacts/*.yaml",
        "decision": "00_project_records/workstreams/*/decisions/*.yaml",
        "submission": "00_project_records/workstreams/*/submissions/*.yaml",
    }
    id_fields = {
        "task": "task_id",
        "route": "route_id",
        "artifact": "artifact_set_id",
        "decision": "decision_id",
        "submission": "submission_id",
    }
    for kind, pattern in file_patterns.items():
        for path in project_root.glob(pattern):
            try:
                data = load_yaml(path)
            except Exception:
                continue
            value = data.get(id_fields[kind]) if isinstance(data, dict) else None
            if isinstance(value, str):
                result[kind].add(value)

    events_path = project_root / "00_project_records/events/project_events.jsonl"
    if events_path.is_file():
        try:
            for _, event in load_json_lines(events_path):
                if isinstance(event, dict) and isinstance(event.get("event_id"), str):
                    result["event"].add(event["event_id"])
        except Exception:
            pass
    return result


def add_missing_reference(
    errors: list[dict[str, str]],
    source: Path,
    field: str,
    value: str,
    target_kind: str,
) -> None:
    errors.append(
        {
            "file": str(source),
            "instance_path": field,
            "schema_path": "direct_reference",
            "message": f"missing {target_kind} reference: {value}",
        }
    )


def check_direct_references(
    project_root: Path,
    validated_documents: list[tuple[Path, Any]],
) -> list[dict[str, str]]:
    ids = collect_record_ids(project_root)
    errors: list[dict[str, str]] = []

    for path, data in validated_documents:
        if not isinstance(data, dict):
            continue
        schema_name = infer_schema_name(project_root, path)

        if schema_name == "project_state.schema.yaml":
            for item in data.get("workstreams", []):
                if not isinstance(item, dict):
                    continue
                state_path = item.get("state_path")
                if isinstance(state_path, str) and not (project_root / state_path).is_file():
                    add_missing_reference(errors, path, "workstreams[].state_path", state_path, "workstream state path")

        elif schema_name == "workstream_state.schema.yaml":
            reference_fields = [
                ("active_route_id", "route"),
                ("active_task_id", "task"),
                ("last_event_id", "event"),
            ]
            for field, kind in reference_fields:
                value = data.get(field)
                if isinstance(value, str) and value not in ids[kind]:
                    add_missing_reference(errors, path, field, value, kind)
            for value in data.get("pending_decision_ids", []):
                if isinstance(value, str) and value not in ids["decision"]:
                    add_missing_reference(errors, path, "pending_decision_ids", value, "decision")
            for value in data.get("active_submission_ids", []):
                if isinstance(value, str) and value not in ids["submission"]:
                    add_missing_reference(errors, path, "active_submission_ids", value, "submission")
            artifact_groups = data.get("current_artifact_set_ids", {})
            if isinstance(artifact_groups, dict):
                for group, values in artifact_groups.items():
                    if not isinstance(values, list):
                        continue
                    for value in values:
                        if isinstance(value, str) and value not in ids["artifact"]:
                            add_missing_reference(errors, path, f"current_artifact_set_ids.{group}", value, "artifact")

        elif schema_name == "subagent_result.schema.yaml":
            task_id = data.get("task_id")
            if isinstance(task_id, str) and task_id not in ids["task"]:
                add_missing_reference(errors, path, "task_id", task_id, "task")

        elif schema_name == "artifact_set.schema.yaml":
            for field in ("created_by_task_id", "validator_task_id"):
                value = data.get(field)
                if isinstance(value, str) and value not in ids["task"]:
                    add_missing_reference(errors, path, field, value, "task")
            supersedes = data.get("supersedes")
            if isinstance(supersedes, str) and supersedes not in ids["artifact"]:
                add_missing_reference(errors, path, "supersedes", supersedes, "artifact")
            for value in data.get("derived_from", []):
                if isinstance(value, str) and value not in ids["artifact"]:
                    add_missing_reference(errors, path, "derived_from", value, "artifact")

        elif schema_name == "route_record.schema.yaml":
            scope_resolution = data.get("scope_resolution", {})
            if isinstance(scope_resolution, dict):
                event_id = scope_resolution.get("resolved_event_id")
                if isinstance(event_id, str) and event_id not in ids["event"]:
                    add_missing_reference(errors, path, "scope_resolution.resolved_event_id", event_id, "event")
                decision_id = scope_resolution.get("decision_id")
                if isinstance(decision_id, str) and decision_id not in ids["decision"]:
                    add_missing_reference(errors, path, "scope_resolution.decision_id", decision_id, "decision")

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

        overrides = parse_schema_overrides(args.schema_map, project_root)
        warnings: list[str] = []
        if args.mode == "FAST":
            if not args.changed:
                raise ToolError("FAST mode requires at least one --changed path")
            targets, fast_warnings = discover_fast_targets(project_root, args.changed, overrides)
            warnings.extend(fast_warnings)
        else:
            targets = discover_full_targets(project_root)

        errors: list[dict[str, str]] = []
        validated: list[dict[str, str]] = []
        validated_documents: list[tuple[Path, Any]] = []

        for target in targets:
            try:
                documents = read_target_documents(target)
                for label, document in documents:
                    document_errors = validate_document(document, target.schema_name, schemas, store)
                    for item in document_errors:
                        item["file"] = str(target.path)
                        item["document"] = label
                        errors.append(item)
                    validated_documents.append((target.path, document))
                validated.append({"path": str(target.path), "schema": target.schema_name})
            except Exception as exc:
                errors.append(
                    {
                        "file": str(target.path),
                        "instance_path": "$",
                        "schema_path": target.schema_name,
                        "message": str(exc),
                    }
                )

        if not args.skip_reference_check:
            errors.extend(check_direct_references(project_root, validated_documents))

        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        status = "PASS" if not errors else "FAIL"
        payload = {
            "status": status,
            "mode": args.mode,
            "schema_bundle_hash": bundle_hash,
            "schema_cache_hit": cache_hit,
            "validated": validated,
            "errors": errors,
            "warnings": warnings,
            "elapsed_ms": elapsed_ms,
        }
        emit(payload, args.output)
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

#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

import yaml

VERSION = "0.1.0"
SUPPORTED_STEP = "source_recognition"
SOURCE_ROLE = "source_candidate"


class ToolError(RuntimeError):
    pass


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ToolError(f"required YAML is not a regular file: {path}")
    obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ToolError(f"YAML root must be a mapping: {path}")
    return obj


def skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_inside(root: Path, value: str, label: str) -> Path:
    p = Path(value)
    target = p.resolve(strict=False) if p.is_absolute() else (root / p).resolve(strict=False)
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ToolError(f"{label} escapes project root: {value}") from exc
    return target


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def source_record(project_root: Path, source: Path) -> dict[str, Any]:
    if not source.is_file() or source.is_symlink():
        raise ToolError(f"source candidate is not a regular file: {source}")
    return {
        "path": rel(project_root, source),
        "state": "present_unvalidated",
        "role": SOURCE_ROLE,
        "size_bytes": source.stat().st_size,
        "modified_at": mtime(source),
        "sha256": sha256(source),
        "notes": "bounded raw source candidate packaged by runtime_task_builder",
    }


def find_step(route: dict[str, Any], step_id: str) -> dict[str, Any]:
    steps = route.get("steps")
    if not isinstance(steps, list):
        raise ToolError("route.steps is missing")
    matches = [x for x in steps if isinstance(x, dict) and x.get("step_id") == step_id]
    if len(matches) != 1:
        raise ToolError(f"route must contain exactly one {step_id} step")
    return matches[0]


def skill_ref(value: Any, layer: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ToolError("route skill ref must be a mapping")
    name = value.get("skill_name")
    path = value.get("skill_path")
    if not isinstance(name, str) or not name or not isinstance(path, str) or not path:
        raise ToolError("route skill ref is incomplete")
    return {"skill_name": name, "skill_path": path, "skill_layer": layer}


def validate_runtime_spec(step_id: str) -> None:
    spec_path = skill_root() / "runtime/workflows/structure_preparation.runtime.yaml"
    spec = load_yaml(spec_path)
    nodes = spec.get("nodes")
    if not isinstance(nodes, list):
        raise ToolError("runtime structure preparation spec has no nodes")
    node = next((x for x in nodes if isinstance(x, dict) and x.get("name") == step_id), None)
    if not node:
        raise ToolError(f"runtime spec does not contain node {step_id}")
    if node.get("preferred_backend") != "DETERMINISTIC":
        raise ToolError(f"runtime node {step_id} is not deterministic")
    if node.get("deterministic_tool") != "source_recognition_deterministic":
        raise ToolError("source recognition deterministic capability mismatch")


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def validate_candidate(project_root: Path, candidate: Path, logical_task: Path) -> dict[str, Any]:
    validator = skill_root() / "05_tools/runtime_schema_validator/validate.py"
    contracts = skill_root() / "03_contracts"
    cmd = [
        sys.executable,
        str(validator),
        "--project-root", str(project_root),
        "--mode", "FAST",
        "--changed", str(candidate),
        "--schema-map", f"{candidate}=subagent_task.schema.yaml",
        "--logical-map", f"{candidate}={logical_task}",
        "--contracts-dir", str(contracts),
        "--skip-reference-check",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if not proc.stdout:
        raise ToolError(f"runtime_schema_validator produced no output: {proc.stderr}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ToolError(f"cannot parse runtime_schema_validator output: {exc}") from exc
    if proc.returncode != 0 or payload.get("status") != "PASS":
        raise ToolError(f"task candidate validation failed: {payload.get('errors')}")
    return payload


def build(project_root: Path, route_path: Path, sources: list[str], step_id: str) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    project_root = project_root.resolve()
    if not project_root.is_dir():
        raise ToolError(f"project root is not a directory: {project_root}")
    if step_id != SUPPORTED_STEP:
        raise ToolError(f"v{VERSION} supports only {SUPPORTED_STEP}")
    validate_runtime_spec(step_id)

    route_path = route_path.resolve()
    try:
        route_path.relative_to(project_root)
    except ValueError as exc:
        raise ToolError("route path must be inside project root") from exc
    route = load_yaml(route_path)
    route_id = route.get("route_id")
    workstream_id = route.get("workstream_id")
    if not isinstance(route_id, str) or not route_id or not isinstance(workstream_id, str) or not workstream_id:
        raise ToolError("route_id/workstream_id missing")
    step = find_step(route, step_id)
    if step.get("task_unit_mode") != "OPERATION":
        raise ToolError("source_recognition route step must be OPERATION")
    sequence = step.get("sequence")
    workflow_name = step.get("workflow_name")
    work_directory = step.get("work_directory")
    if not isinstance(sequence, int) or sequence < 1:
        raise ToolError("route step sequence is invalid")
    if not isinstance(workflow_name, str) or not workflow_name or not isinstance(work_directory, str) or not work_directory:
        raise ToolError("route step workflow/work_directory is invalid")

    bounded: list[Path] = []
    seen: set[Path] = set()
    for value in sources:
        source = resolve_inside(project_root, value, "source candidate")
        if source not in seen:
            bounded.append(source)
            seen.add(source)
    if not bounded:
        raise ToolError("at least one explicit bounded source path is required")

    task_id = f"task_{route_id}_{sequence:04d}"
    task_path = project_root / f"00_project_records/workstreams/{workstream_id}/tasks/{task_id}/task.yaml"
    workdir = resolve_inside(project_root, work_directory, "work_directory")
    records = [source_record(project_root, source) for source in bounded]
    read_paths = sorted({rel(project_root, source) for source in bounded})

    task = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": workstream_id,
        "workflow_name": workflow_name,
        "route_id": route_id,
        "sequence": sequence,
        "task_unit": {
            "mode": "OPERATION",
            "operation": skill_ref(step.get("operation"), "operation"),
            "validator": None,
        },
        "project_root": str(project_root),
        "work_directory": rel(project_root, workdir),
        "permissions": {
            "allowed_read_paths": read_paths,
            "allowed_write_paths": [rel(project_root, workdir)],
            "forbidden_paths": ["00_project_state", "00_project_records"],
        },
        "current_valid_files": records,
        "upstream_summary": "bounded raw source candidates packaged deterministically from explicit local source paths",
        "user_decisions": [],
        "required_outputs": step.get("expected_outputs") if isinstance(step.get("expected_outputs"), list) else ["STRUCTURE"],
        "detail_output_paths": {
            "log_file": f"{rel(project_root, workdir)}/source_recognition.log",
            "report_file": f"{rel(project_root, workdir)}/source_recognition_report.yaml",
            "result_data_file": None,
        },
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }

    text = yaml.safe_dump(task, allow_unicode=True, sort_keys=False, width=1000)
    if not text.endswith("\n"):
        text += "\n"
    if task_path.exists():
        existing = task_path.read_text(encoding="utf-8")
        if existing != text:
            raise ToolError(f"task already exists with different content: {task_path}")
        return task, task_path, {"status": "REUSED", "elapsed_ms": 0.0}

    task_path.parent.mkdir(parents=True, exist_ok=True)
    candidate = task_path.parent / ".task.candidate.yaml"
    candidate.write_text(text, encoding="utf-8")
    try:
        validation = validate_candidate(project_root, candidate, task_path)
        atomic_text(task_path, text)
    finally:
        if candidate.exists():
            candidate.unlink()
    return task, task_path, validation


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build a deterministic runtime task for supported route nodes")
    p.add_argument("--project-root", required=True, type=Path)
    p.add_argument("--route", required=True, type=Path)
    p.add_argument("--source", action="append", default=[])
    p.add_argument("--step-id", default=SUPPORTED_STEP)
    return p


def main() -> int:
    started = time.perf_counter()
    args = parser().parse_args()
    try:
        _, task_path, validation = build(args.project_root, args.route, args.source, args.step_id)
        emit({
            "status": "PASS",
            "tool": "runtime_task_builder",
            "version": VERSION,
            "step_id": args.step_id,
            "task_path": str(task_path),
            "validation_status": validation.get("status"),
            "validation_elapsed_ms": validation.get("elapsed_ms"),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        })
        return 0
    except Exception as exc:
        emit({
            "status": "ERROR",
            "tool": "runtime_task_builder",
            "version": VERSION,
            "step_id": args.step_id,
            "error": str(exc),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        })
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

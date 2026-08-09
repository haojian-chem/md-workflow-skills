#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

import yaml

VERSION = "0.1.0"
PROTOCOL_REL = "00_manager/md_workflow_manager/references/project_initialization_protocol.md"
PROTOCOL_BLOB = "5894fab5449080d5709e3ce10a08292aaa3a56b3"


class ToolError(RuntimeError):
    pass


def skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def check_semantic_guard() -> None:
    path = skill_root() / PROTOCOL_REL
    if not path.is_file() or path.is_symlink():
        raise ToolError(f"initialization protocol missing: {path}")
    actual = git_blob_sha(path.read_bytes())
    if actual != PROTOCOL_BLOB:
        raise ToolError(f"INITIALIZATION_PROTOCOL_GUARD_MISMATCH: expected {PROTOCOL_BLOB}, got {actual}")


def slug(value: str, limit: int = 24) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return (text or "project")[:limit]


def derive_ids(root: Path) -> tuple[str, str]:
    base = slug(root.name)
    digest = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:8]
    return f"proj_{base}_{digest}", f"ws_0001_{base[:12]}"


def dump_yaml_bytes(obj: Any) -> bytes:
    text = yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=1000)
    return (text if text.endswith("\n") else text + "\n").encode()


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def atomic_install(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ToolError(f"target already exists: {target}")
    os.replace(source, target)


def append_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        raise ToolError("NEW initialization refuses to append to a pre-existing non-empty event log")
    payload = "".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n" for e in events).encode()
    temp = path.with_name(f".{path.name}.init.tmp")
    write_bytes(temp, payload)
    os.replace(temp, path)


def run_fast_validator(project_root: Path, p_candidate: Path, ws_candidate: Path, ws_id: str) -> dict[str, Any]:
    validator = skill_root() / "05_tools/runtime_schema_validator/validate.py"
    cmd = [
        sys.executable, str(validator),
        "--project-root", str(project_root),
        "--contracts-dir", str(skill_root() / "03_contracts"),
        "--mode", "FAST",
        "--changed", str(p_candidate), str(ws_candidate),
        "--logical-map", f"{p_candidate}=00_project_state/project_state.yaml",
        "--logical-map", f"{ws_candidate}=00_project_state/workstreams/{ws_id}.yaml",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if not proc.stdout:
        raise ToolError(f"runtime_schema_validator produced no output: {proc.stderr}")
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ToolError(f"cannot parse validator output: {exc}") from exc
    if proc.returncode != 0 or out.get("status") != "PASS":
        raise ToolError(f"INIT_CANDIDATE_VALIDATION failed: {json.dumps(out, ensure_ascii=False)}")
    return out


def make_objects(project_root: Path, project_id: str, ws_id: str, title: str, purpose: str, stamp: str) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    project = {
        "schema_version": 2,
        "project": {
            "project_id": project_id,
            "skill_architecture_root": str(skill_root()),
            "md_project_root": str(project_root),
        },
        "entry_state": "RESUMABLE",
        "focus": {"target_type": "WORKSTREAM", "workstream_id": ws_id, "reason": "USER_SELECTED", "selected_at": stamp},
        "related_workstreams": [],
        "workstreams": [{"workstream_id": ws_id, "state_path": f"00_project_state/workstreams/{ws_id}.yaml"}],
        "pending_project_decision_ids": [],
        "last_project_event_id": None,
        "last_updated_by": "md_workflow_manager",
        "last_updated_at": stamp,
    }
    ws = {
        "schema_version": 1,
        "workstream_id": ws_id,
        "title": title,
        "purpose": purpose,
        "origin": {"parent_workstream_id": None, "fork_reason": None, "forked_from_artifact_set_ids": []},
        "current_position": {"workflow_name": None, "substep": None, "task_id": None},
        "lifecycle_status": "OPEN",
        "activity_status": "IDLE",
        "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
        "active_route_id": None,
        "active_task_id": None,
        "current_artifact_set_ids": {"structure": [], "topology": [], "system": [], "md_input": [], "md_output": [], "analysis_result": []},
        "pending_decision_ids": [],
        "active_submission_ids": [],
        "last_event_id": None,
        "last_updated_by": "md_workflow_manager",
        "last_updated_at": stamp,
    }
    events = [
        {
            "schema_version": 1,
            "event_id": f"evt_init_entry_{hashlib.sha256((project_id + stamp).encode()).hexdigest()[:12]}",
            "timestamp": stamp,
            "event_type": "ENTRY_STATE_EVALUATED",
            "scope": "PROJECT",
            "workstream_id": None,
            "actor": "MANAGER",
            "object_type": "PROJECT",
            "object_id": project_id,
            "summary": "Entry state evaluated as NEW",
            "previous_state": None,
            "new_state": "NEW",
            "record_paths": ["00_project_state/project_state.yaml"],
            "related_event_ids": [],
        },
        {
            "schema_version": 1,
            "event_id": f"evt_init_project_{hashlib.sha256((ws_id + stamp).encode()).hexdigest()[:12]}",
            "timestamp": stamp,
            "event_type": "PROJECT_INITIALIZED",
            "scope": "PROJECT",
            "workstream_id": None,
            "actor": "MANAGER",
            "object_type": "PROJECT",
            "object_id": project_id,
            "summary": "Project management skeleton initialized",
            "previous_state": "NEW",
            "new_state": "RESUMABLE",
            "record_paths": ["00_project_state/project_state.yaml", f"00_project_state/workstreams/{ws_id}.yaml"],
            "related_event_ids": [],
        },
    ]
    return project, ws, events


def initialize(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    check_semantic_guard()
    root = args.project_root.resolve()
    if not root.is_dir():
        raise ToolError(f"project_root is not a directory: {root}")
    formal_project = root / "00_project_state/project_state.yaml"
    if formal_project.exists():
        return {"status": "BLOCKED", "reason": "PROJECT_STATE_ALREADY_EXISTS", "project_state": str(formal_project)}

    for rel in [
        "00_project_state/workstreams", "00_project_records/events", "00_project_records/workstreams",
        "01_structure_preparation", "02_topology_preparation", "03_md_preparation", "04_md_simulation", "05_analysis",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)

    derived_project_id, derived_ws_id = derive_ids(root)
    project_id = args.project_id or derived_project_id
    ws_id = args.workstream_id or derived_ws_id
    stamp = datetime.now(timezone.utc).isoformat()
    title = args.title or "initial workstream"
    purpose = args.purpose or "initial MD workflow"
    project, ws, events = make_objects(root, project_id, ws_id, title, purpose, stamp)

    temp_root = Path(tempfile.mkdtemp(prefix=".runtime_project_initializer_", dir=str(root / "00_project_state")))
    p_candidate = temp_root / "project_state.yaml"
    ws_candidate = temp_root / "workstream_state.yaml"
    write_bytes(p_candidate, dump_yaml_bytes(project))
    write_bytes(ws_candidate, dump_yaml_bytes(ws))
    validator = run_fast_validator(root, p_candidate, ws_candidate, ws_id)

    formal_ws = root / f"00_project_state/workstreams/{ws_id}.yaml"
    event_log = root / "00_project_records/events/project_events.jsonl"
    committed: list[Path] = []
    try:
        atomic_install(ws_candidate, formal_ws)
        committed.append(formal_ws)
        atomic_install(p_candidate, formal_project)
        committed.append(formal_project)
        append_events(event_log, events)
        committed.append(event_log)
    except Exception:
        for path in reversed(committed):
            try:
                path.unlink()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    if yaml.safe_load(formal_project.read_text()).get("entry_state") != "RESUMABLE":
        raise ToolError("post-commit verification failed: entry_state is not RESUMABLE")
    if formal_project.read_bytes() != dump_yaml_bytes(project) or formal_ws.read_bytes() != dump_yaml_bytes(ws):
        raise ToolError("post-commit verification failed: committed state differs from validated candidate")
    rows = [json.loads(line) for line in event_log.read_text().splitlines() if line.strip()]
    if [r.get("event_type") for r in rows[-2:]] != ["ENTRY_STATE_EVALUATED", "PROJECT_INITIALIZED"]:
        raise ToolError("post-commit verification failed: initialization events missing")

    return {
        "status": "INITIALIZED",
        "project_id": project_id,
        "workstream_id": ws_id,
        "project_state_path": str(formal_project.relative_to(root)),
        "workstream_state_path": str(formal_ws.relative_to(root)),
        "event_log_path": str(event_log.relative_to(root)),
        "validation": {"mode": "FAST", "status": validator.get("status"), "elapsed_ms": validator.get("elapsed_ms")},
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--project-root", required=True, type=Path)
    p.add_argument("--project-id")
    p.add_argument("--workstream-id")
    p.add_argument("--title")
    p.add_argument("--purpose")
    return p


def main() -> int:
    try:
        out = initialize(parser().parse_args())
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out.get("status") in {"INITIALIZED", "BLOCKED"} else 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())

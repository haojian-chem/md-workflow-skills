#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import fnmatch
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
import uuid

import yaml

PASS = 0
VALIDATION_FAILURE = 1
TOOL_FAILURE = 2

STATUS_EVENT = {
    "DONE": "TASK_DONE",
    "BLOCKED": "TASK_BLOCKED",
    "FAILED": "TASK_FAILED",
    "CANCELLED": "TASK_CANCELLED",
}
ARTIFACT_GROUP = {
    "STRUCTURE": "structure",
    "TOPOLOGY": "topology",
    "SYSTEM": "system",
    "MD_INPUT": "md_input",
    "MD_OUTPUT": "md_output",
    "ANALYSIS_RESULT": "analysis_result",
}
SEMANTIC_STATE_FIELDS = {"lifecycle_status", "activity_status", "hold_reason", "active_route_id"}
BACKENDS = {"DETERMINISTIC", "AGENT_TASK", "AGENT_SEQUENCE"}


class CommitterError(RuntimeError):
    pass


class ValidationBlocked(RuntimeError):
    def __init__(self, validation: dict[str, Any]):
        super().__init__("candidate FAST validation failed")
        self.validation = validation


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CommitterError(f"cannot parse YAML {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise CommitterError(f"YAML root must be a mapping: {path}")
    return obj


def yaml_bytes(obj: Any) -> bytes:
    text = yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, default_flow_style=False, width=1000)
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CommitterError(f"{label} must be a non-empty string")
    if value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
        raise CommitterError(f"unsafe {label}: {value!r}")
    return value


def safe_project_path(project_root: Path, rel: str, label: str) -> Path:
    p = Path(rel)
    if p.is_absolute() or any(part == ".." for part in p.parts):
        raise CommitterError(f"{label} must be a safe project-relative path: {rel}")
    root = project_root.resolve()
    target = (root / p).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise CommitterError(f"{label} escapes project root: {rel}") from exc
    cursor = root
    for part in p.parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise CommitterError(f"symlink parent is not allowed for {label}: {cursor}")
    if target.exists() and target.is_symlink():
        raise CommitterError(f"symlink target is not allowed for {label}: {target}")
    return target


def relpath(project_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(project_root.resolve()).as_posix()


def authorized(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(rel, pattern) for pattern in patterns)


def require_authorized(rel: str, patterns: list[str]) -> None:
    if not authorized(rel, patterns):
        raise CommitterError(f"management path is not authorized by commit_request: {rel}")


def validate_request_shape(req: dict[str, Any]) -> None:
    required = [
        "schema_version", "task_identity", "workstream_id", "route_id", "route_node_id",
        "execution_backend", "responsibility_result", "semantic_state_delta", "artifact_updates",
        "decision_updates", "submission_updates", "route_progression", "allowed_management_paths",
    ]
    missing = [x for x in required if x not in req]
    if missing:
        raise CommitterError(f"commit_request missing keys: {', '.join(missing)}")
    if req["schema_version"] != 1:
        raise CommitterError("unsupported commit_request schema_version")
    if not isinstance(req["task_identity"], dict):
        raise CommitterError("task_identity must be a mapping")
    safe_id(req["task_identity"].get("task_id"), "task_id")
    if req["task_identity"].get("task_unit_mode") not in {"OPERATION", "VALIDATOR", "OPERATION_WITH_VALIDATOR"}:
        raise CommitterError("task_identity.task_unit_mode is invalid")
    safe_id(req["workstream_id"], "workstream_id")
    if req["route_id"] is not None:
        safe_id(req["route_id"], "route_id")
    if req["route_node_id"] is not None and not isinstance(req["route_node_id"], str):
        raise CommitterError("route_node_id must be string or null")
    if req["execution_backend"] not in BACKENDS:
        raise CommitterError("execution_backend is invalid")
    if not isinstance(req["responsibility_result"], dict):
        raise CommitterError("responsibility_result must be a mapping")
    if not isinstance(req["semantic_state_delta"], dict):
        raise CommitterError("semantic_state_delta must be a mapping")
    unknown = set(req["semantic_state_delta"]) - SEMANTIC_STATE_FIELDS
    if unknown:
        raise CommitterError(f"semantic_state_delta contains unsupported fields: {sorted(unknown)}")
    for key in ("artifact_updates", "decision_updates", "submission_updates", "allowed_management_paths"):
        if not isinstance(req[key], list):
            raise CommitterError(f"{key} must be a list")
    if not req["allowed_management_paths"] or not all(isinstance(x, str) and x for x in req["allowed_management_paths"]):
        raise CommitterError("allowed_management_paths must contain at least one non-empty pattern")
    rp = req["route_progression"]
    if not isinstance(rp, dict) or rp.get("action") not in {"KEEP", "SET"}:
        raise CommitterError("route_progression.action must be KEEP or SET")
    if rp["action"] == "SET":
        pos = rp.get("position")
        if not isinstance(pos, dict) or set(pos) != {"workflow_name", "substep", "task_id"}:
            raise CommitterError("route_progression.position must contain workflow_name, substep and task_id")
        for field in ("workflow_name", "substep", "task_id"):
            if pos[field] is not None and not isinstance(pos[field], str):
                raise CommitterError(f"route_progression.position.{field} must be string or null")
    if "timestamp" in req and req["timestamp"] is not None and not isinstance(req["timestamp"], str):
        raise CommitterError("timestamp must be string or null")
    if "terminal_event_id" in req and req["terminal_event_id"] is not None:
        safe_id(req["terminal_event_id"], "terminal_event_id")


def verify_task_and_state(project_root: Path, req: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    ws = req["workstream_id"]
    task_id = req["task_identity"]["task_id"]
    task_path = safe_project_path(project_root, f"00_project_records/workstreams/{ws}/tasks/{task_id}/task.yaml", "task record")
    state_path = safe_project_path(project_root, f"00_project_state/workstreams/{ws}.yaml", "workstream state")
    if not task_path.is_file() or task_path.is_symlink():
        raise CommitterError(f"immutable task record is missing: {relpath(project_root, task_path)}")
    if not state_path.is_file() or state_path.is_symlink():
        raise CommitterError(f"workstream state is missing: {relpath(project_root, state_path)}")
    task = load_yaml(task_path)
    state = load_yaml(state_path)
    result = req["responsibility_result"]
    if task.get("task_id") != task_id or task.get("workstream_id") != ws:
        raise CommitterError("task record identity does not match commit_request")
    task_mode = ((task.get("task_unit") or {}).get("mode"))
    if task_mode != req["task_identity"]["task_unit_mode"]:
        raise CommitterError("task record mode does not match task_identity")
    if task.get("route_id") != req["route_id"]:
        raise CommitterError("task record route_id does not match commit_request")
    if state.get("workstream_id") != ws:
        raise CommitterError("workstream state identity does not match commit_request")
    if state.get("active_route_id") != req["route_id"]:
        raise CommitterError("workstream active_route_id does not match commit_request route_id")
    if result.get("task_id") != task_id or result.get("workstream_id") != ws:
        raise CommitterError("responsibility_result identity does not match commit_request")
    if result.get("task_unit_mode") != req["task_identity"]["task_unit_mode"]:
        raise CommitterError("responsibility_result mode does not match task_identity")
    status = result.get("status")
    if status not in STATUS_EVENT:
        raise CommitterError(f"responsibility_result.status is invalid: {status!r}")
    active_task = state.get("active_task_id")
    if active_task not in (None, task_id):
        raise CommitterError(f"workstream has a different active_task_id: {active_task}")
    return task, state, task_path, state_path


def validate_status_delta(status: str, state: dict[str, Any], delta: dict[str, Any], task_id: str) -> None:
    new_activity = delta.get("activity_status", state.get("activity_status"))
    new_hold = delta.get("hold_reason", state.get("hold_reason"))
    if status == "BLOCKED":
        if new_activity != "WAITING" or not isinstance(new_hold, dict) or new_hold.get("type") in (None, "NONE"):
            raise CommitterError("BLOCKED closure requires explicit WAITING activity_status and non-NONE hold_reason")
    if status == "FAILED" and new_activity != "FAILED":
        raise CommitterError("FAILED closure requires explicit activity_status: FAILED")
    if state.get("active_task_id") == task_id and state.get("activity_status") == "EXECUTING" and new_activity == "EXECUTING":
        raise CommitterError("closing an EXECUTING task requires explicit non-EXECUTING activity_status")


def file_record_to_identity(project_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise CommitterError("artifact candidate file record must contain path")
    path = safe_project_path(project_root, record["path"], "artifact file")
    if not path.is_file() or path.is_symlink():
        raise CommitterError(f"artifact candidate file is missing or invalid: {record['path']}")
    stat = path.stat()
    if "size_bytes" in record and record["size_bytes"] != stat.st_size:
        raise CommitterError(f"artifact file size does not match responsibility_result: {record['path']}")
    out: dict[str, Any] = {"path": record["path"]}
    for key in ("role", "size_bytes", "modified_at", "sha256", "notes"):
        if key in record:
            out[key] = record[key]
    if "size_bytes" not in out:
        out["size_bytes"] = stat.st_size
    if "modified_at" not in out:
        out["modified_at"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    return out


def build_artifact_records(project_root: Path, req: dict[str, Any], state: dict[str, Any], timestamp: str) -> tuple[list[tuple[str, dict[str, Any]]], dict[str, Any], list[str]]:
    result = req["responsibility_result"]
    candidates = result.get("artifact_candidates")
    if not isinstance(candidates, list):
        raise CommitterError("responsibility_result.artifact_candidates must be a list")
    updated_state = copy.deepcopy(state)
    records: list[tuple[str, dict[str, Any]]] = []
    ids: list[str] = []
    seen_ids: set[str] = set()
    for update in req["artifact_updates"]:
        if not isinstance(update, dict):
            raise CommitterError("artifact_updates items must be mappings")
        required = {"candidate_index", "artifact_set_id", "validation_status", "validator_task_id", "supersedes", "notes", "current_state_action"}
        missing = required - set(update)
        if missing:
            raise CommitterError(f"artifact update missing fields: {sorted(missing)}")
        index = update["candidate_index"]
        if not isinstance(index, int) or index < 0 or index >= len(candidates):
            raise CommitterError(f"artifact candidate_index out of range: {index!r}")
        artifact_id = safe_id(update["artifact_set_id"], "artifact_set_id")
        if artifact_id in seen_ids:
            raise CommitterError(f"duplicate artifact_set_id in request: {artifact_id}")
        seen_ids.add(artifact_id)
        candidate = candidates[index]
        if not isinstance(candidate, dict) or candidate.get("artifact_type") not in ARTIFACT_GROUP:
            raise CommitterError(f"invalid artifact candidate at index {index}")
        validation_status = update["validation_status"]
        if validation_status not in {"UNVALIDATED", "VALIDATED", "INVALIDATED"}:
            raise CommitterError(f"invalid validation_status for {artifact_id}")
        validator_task_id = update["validator_task_id"]
        if validator_task_id is not None:
            safe_id(validator_task_id, "validator_task_id")
        if validation_status == "VALIDATED" and validator_task_id is None:
            raise CommitterError(f"VALIDATED artifact requires explicit validator_task_id: {artifact_id}")
        if not isinstance(update["supersedes"], list) or not all(isinstance(x, str) and x for x in update["supersedes"]):
            raise CommitterError("artifact supersedes must be a list of IDs")
        action = update["current_state_action"]
        if action not in {"NONE", "ADD", "REPLACE_TYPE"}:
            raise CommitterError(f"invalid current_state_action: {action}")
        files = candidate.get("files")
        if not isinstance(files, list) or not files:
            raise CommitterError(f"artifact candidate has no files: index {index}")
        record = {
            "schema_version": 1,
            "artifact_set_id": artifact_id,
            "artifact_type": candidate["artifact_type"],
            "workstream_id": req["workstream_id"],
            "created_at": timestamp,
            "created_by_task_id": req["task_identity"]["task_id"],
            "derived_from_artifact_set_ids": copy.deepcopy(candidate.get("derived_from_artifact_set_ids", [])),
            "files": [file_record_to_identity(project_root, f) for f in files],
            "validation_status": validation_status,
            "validator_task_id": validator_task_id,
            "supersedes": copy.deepcopy(update["supersedes"]),
            "notes": update["notes"],
        }
        rel = f"00_project_records/workstreams/{req['workstream_id']}/artifacts/{artifact_id}.yaml"
        records.append((rel, record))
        ids.append(artifact_id)
        group = ARTIFACT_GROUP[candidate["artifact_type"]]
        groups = updated_state.get("current_artifact_set_ids")
        if not isinstance(groups, dict) or group not in groups or not isinstance(groups[group], list):
            raise CommitterError("workstream state current_artifact_set_ids is invalid")
        if action == "ADD" and artifact_id not in groups[group]:
            groups[group].append(artifact_id)
        elif action == "REPLACE_TYPE":
            groups[group] = [artifact_id]
    return records, updated_state, ids


def build_explicit_records(req: dict[str, Any], state: dict[str, Any], key: str, id_field: str, dirname: str, state_list: str, action_field: str) -> tuple[list[tuple[str, dict[str, Any]]], dict[str, Any], list[str]]:
    updated = copy.deepcopy(state)
    records: list[tuple[str, dict[str, Any]]] = []
    ids: list[str] = []
    for update in req[key]:
        if not isinstance(update, dict) or not isinstance(update.get("record"), dict):
            raise CommitterError(f"{key} item requires full record mapping")
        record = copy.deepcopy(update["record"])
        record_id = safe_id(record.get(id_field), id_field)
        if record.get("workstream_id") != req["workstream_id"]:
            raise CommitterError(f"{key} record workstream_id mismatch: {record_id}")
        action = update.get(action_field)
        if action not in {"NONE", "ADD", "REMOVE"}:
            raise CommitterError(f"{key}.{action_field} must be NONE, ADD or REMOVE")
        rel = f"00_project_records/workstreams/{req['workstream_id']}/{dirname}/{record_id}.yaml"
        records.append((rel, record))
        ids.append(record_id)
        values = updated.get(state_list)
        if not isinstance(values, list):
            raise CommitterError(f"workstream state {state_list} must be a list")
        if action == "ADD" and record_id not in values:
            values.append(record_id)
        elif action == "REMOVE":
            updated[state_list] = [x for x in values if x != record_id]
    return records, updated, ids


def event_exists(events_path: Path, event_id: str) -> bool:
    if not events_path.is_file():
        return False
    try:
        for raw in events_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            obj = json.loads(raw)
            if isinstance(obj, dict) and obj.get("event_id") == event_id:
                return True
    except Exception as exc:
        raise CommitterError(f"cannot inspect existing event log: {exc}") from exc
    return False


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def prepare_candidates(project_root: Path, req: dict[str, Any]) -> dict[str, Any]:
    validate_request_shape(req)
    _task, original_state, _task_path, state_path = verify_task_and_state(project_root, req)
    status = req["responsibility_result"]["status"]
    validate_status_delta(status, original_state, req["semantic_state_delta"], req["task_identity"]["task_id"])
    timestamp = req.get("timestamp") or utc_now()
    event_id = req.get("terminal_event_id") or f"evt_{re.sub(r'[^A-Za-z0-9_.-]+', '_', req['task_identity']['task_id'])}_{status.lower()}"
    safe_id(event_id, "terminal_event_id")
    events_path = safe_project_path(project_root, "00_project_records/events/project_events.jsonl", "event log")
    if event_exists(events_path, event_id):
        raise CommitterError(f"terminal event ID already exists: {event_id}")

    state_after_semantic = copy.deepcopy(original_state)
    for key, value in req["semantic_state_delta"].items():
        state_after_semantic[key] = copy.deepcopy(value)

    artifact_records, state_after_artifacts, artifact_ids = build_artifact_records(project_root, req, state_after_semantic, timestamp)
    decision_records, state_after_decisions, decision_ids = build_explicit_records(req, state_after_artifacts, "decision_updates", "decision_id", "decisions", "pending_decision_ids", "pending_action")
    submission_records, state_after_submissions, submission_ids = build_explicit_records(req, state_after_decisions, "submission_updates", "submission_id", "submissions", "active_submission_ids", "active_action")

    state = copy.deepcopy(state_after_submissions)
    rp = req["route_progression"]
    if rp["action"] == "SET":
        state["current_position"] = copy.deepcopy(rp["position"])
    if state.get("active_task_id") == req["task_identity"]["task_id"]:
        state["active_task_id"] = None
    state["last_event_id"] = event_id
    state["last_updated_by"] = "md_workflow_manager/runtime_record_committer"
    state["last_updated_at"] = timestamp

    result_rel = f"00_project_records/workstreams/{req['workstream_id']}/tasks/{req['task_identity']['task_id']}/result.yaml"
    state_rel = relpath(project_root, state_path)
    immutable_records: list[tuple[str, dict[str, Any]]] = [(result_rel, copy.deepcopy(req["responsibility_result"]))]
    immutable_records.extend(artifact_records)
    immutable_records.extend(decision_records)
    immutable_records.extend(submission_records)

    patterns = req["allowed_management_paths"]
    for logical_rel, _ in immutable_records:
        require_authorized(logical_rel, patterns)
    require_authorized(state_rel, patterns)
    require_authorized("00_project_records/events/project_events.jsonl", patterns)

    final_targets = [safe_project_path(project_root, logical_rel, "record target") for logical_rel, _ in immutable_records]
    for target in final_targets:
        if target.exists():
            raise CommitterError(f"immutable record target already exists: {relpath(project_root, target)}")

    event = {
        "schema_version": 1,
        "event_id": event_id,
        "timestamp": timestamp,
        "event_type": STATUS_EVENT[status],
        "scope": "WORKSTREAM",
        "workstream_id": req["workstream_id"],
        "actor": "MANAGER",
        "object_type": "TASK",
        "object_id": req["task_identity"]["task_id"],
        "summary": f"Task {req['task_identity']['task_id']} closed with {status}.",
        "record_paths": [logical_rel for logical_rel, _ in immutable_records] + [state_rel],
        "related_event_ids": [],
    }

    txid = f"tx_{re.sub(r'[^A-Za-z0-9_.-]+', '_', req['task_identity']['task_id'])}_{uuid.uuid4().hex[:12]}"
    temp_root = safe_project_path(project_root, f"00_project_records/.runtime_record_committer/{txid}", "transaction directory")
    temp_root.mkdir(parents=True, exist_ok=False)
    candidate_entries: list[dict[str, Any]] = []
    for idx, (logical_rel, obj) in enumerate(immutable_records):
        cand = temp_root / f"record_{idx:03d}.yaml"
        cand.write_bytes(yaml_bytes(obj))
        candidate_entries.append({
            "candidate": cand,
            "logical_rel": logical_rel,
            "target": safe_project_path(project_root, logical_rel, "record target"),
            "kind": "immutable",
            "expected_sha256": sha256_bytes(cand.read_bytes()),
        })
    state_candidate = temp_root / "workstream_state.yaml"
    state_candidate.write_bytes(yaml_bytes(state))
    candidate_entries.append({
        "candidate": state_candidate,
        "logical_rel": state_rel,
        "target": state_path,
        "kind": "state",
        "expected_sha256": sha256_bytes(state_candidate.read_bytes()),
    })
    event_candidate = temp_root / "event_line.jsonl"
    event_bytes = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    event_candidate.write_bytes(event_bytes)
    candidate_entries.append({
        "candidate": event_candidate,
        "logical_rel": "00_project_records/events/project_events.jsonl",
        "target": events_path,
        "kind": "event",
        "expected_sha256": sha256_bytes(event_candidate.read_bytes()),
    })

    return {
        "temp_root": temp_root,
        "entries": candidate_entries,
        "event": event,
        "event_bytes": event_bytes,
        "state": state,
        "original_state_bytes": state_path.read_bytes(),
        "artifact_ids": artifact_ids,
        "decision_ids": decision_ids,
        "submission_ids": submission_ids,
        "timestamp": timestamp,
        "event_id": event_id,
        "result_rel": result_rel,
        "state_rel": state_rel,
    }


def run_fast_validation(skill_root: Path, project_root: Path, prepared: dict[str, Any]) -> dict[str, Any]:
    validator = skill_root / "05_tools/runtime_schema_validator/validate.py"
    contracts = skill_root / "03_contracts"
    if not validator.is_file() or validator.is_symlink():
        raise CommitterError(f"ACTIVE runtime schema validator entrypoint missing: {validator}")
    if not contracts.is_dir():
        raise CommitterError(f"contracts directory missing: {contracts}")
    changed = [str(entry["candidate"]) for entry in prepared["entries"]]
    cmd = [sys.executable, str(validator), "--project-root", str(project_root), "--contracts-dir", str(contracts), "--mode", "FAST", "--changed", *changed]
    for entry in prepared["entries"]:
        cmd.extend(["--logical-map", f"{entry['candidate']}={entry['logical_rel']}"])
    proc = subprocess.run(cmd, text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout)
    except Exception as exc:
        raise CommitterError(f"runtime_schema_validator returned non-JSON output: {proc.stdout[:300]!r}; stderr={proc.stderr[:300]!r}") from exc
    if proc.returncode == 0 and payload.get("status") == "PASS":
        return payload
    if proc.returncode == 1 or payload.get("status") == "FAIL":
        raise ValidationBlocked(payload)
    raise CommitterError(f"runtime_schema_validator error: {payload}")


def controlled_commit(project_root: Path, prepared: dict[str, Any], fail_after_step: int | None = None) -> list[str]:
    entries = prepared["entries"]
    immutable = [entry for entry in entries if entry["kind"] == "immutable"]
    state_entry = next(entry for entry in entries if entry["kind"] == "state")
    event_entry = next(entry for entry in entries if entry["kind"] == "event")
    created: list[Path] = []
    state_replaced = False
    event_target: Path = event_entry["target"]
    event_existed = event_target.exists()
    event_size = event_target.stat().st_size if event_existed else 0
    changed: list[str] = []
    step = 0

    def checkpoint() -> None:
        nonlocal step
        step += 1
        if fail_after_step is not None and step == fail_after_step:
            raise OSError(f"synthetic commit failure at step {step}")

    try:
        for entry in immutable:
            target: Path = entry["target"]
            if target.exists():
                raise CommitterError(f"immutable target appeared during commit: {relpath(project_root, target)}")
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(entry["candidate"], target)
            created.append(target)
            changed.append(relpath(project_root, target))
            checkpoint()

        event_target.parent.mkdir(parents=True, exist_ok=True)
        with event_target.open("ab") as handle:
            handle.write(prepared["event_bytes"])
            handle.flush()
            os.fsync(handle.fileno())
        changed.append(relpath(project_root, event_target))
        checkpoint()

        state_target: Path = state_entry["target"]
        state_target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(state_entry["candidate"], state_target)
        state_replaced = True
        changed.append(relpath(project_root, state_target))
        checkpoint()

        for target in created:
            expected_entry = next(entry for entry in immutable if entry["target"] == target)
            if sha256_bytes(target.read_bytes()) != expected_entry["expected_sha256"]:
                raise OSError(f"record verification failed: {target}")
        if sha256_bytes(state_target.read_bytes()) != state_entry["expected_sha256"]:
            raise OSError("workstream state verification failed")
        if not event_target.read_bytes().endswith(prepared["event_bytes"]):
            raise OSError("event append verification failed")
        return changed
    except Exception as exc:
        rollback_errors: list[str] = []
        try:
            if state_replaced:
                atomic_write(state_entry["target"], prepared["original_state_bytes"])
        except Exception as rollback_exc:
            rollback_errors.append(f"state rollback failed: {rollback_exc}")
        try:
            if event_target.exists():
                if event_existed:
                    with event_target.open("r+b") as handle:
                        handle.truncate(event_size)
                        handle.flush()
                        os.fsync(handle.fileno())
                else:
                    event_target.unlink()
        except Exception as rollback_exc:
            rollback_errors.append(f"event rollback failed: {rollback_exc}")
        for target in reversed(created):
            try:
                if target.exists():
                    target.unlink()
            except Exception as rollback_exc:
                rollback_errors.append(f"record rollback failed {target}: {rollback_exc}")
        suffix = f"; rollback errors: {rollback_errors}" if rollback_errors else "; rollback completed"
        raise CommitterError(f"controlled commit failed: {exc}{suffix}") from exc


def cleanup(prepared: dict[str, Any] | None) -> None:
    if not prepared:
        return
    root = prepared.get("temp_root")
    if isinstance(root, Path) and root.exists():
        shutil.rmtree(root, ignore_errors=True)
    parent = root.parent if isinstance(root, Path) else None
    if parent and parent.exists():
        try:
            parent.rmdir()
        except OSError:
            pass


def run(project_root: Path, skill_root: Path, request_path: Path) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    prepared: dict[str, Any] | None = None
    req: dict[str, Any] | None = None
    try:
        if not project_root.is_dir():
            raise CommitterError(f"project root is not a directory: {project_root}")
        if not skill_root.is_dir():
            raise CommitterError(f"skill root is not a directory: {skill_root}")
        req = load_yaml(request_path)
        prepared = prepare_candidates(project_root, req)
        validation = run_fast_validation(skill_root, project_root, prepared)
        changed = controlled_commit(project_root, prepared)
        receipt = {
            "status": "COMMITTED",
            "task_id": req["task_identity"]["task_id"],
            "workstream_id": req["workstream_id"],
            "changed_paths": changed,
            "terminal_event_id": prepared["event_id"],
            "artifact_record_ids": prepared["artifact_ids"],
            "decision_record_ids": prepared["decision_ids"],
            "submission_record_ids": prepared["submission_ids"],
            "workstream_state_changed": True,
            "project_state_changed": False,
            "validation_status": "PASS",
            "next_route_position": prepared["state"].get("current_position"),
            "warnings": validation.get("warnings", []),
            "validator_elapsed_ms": validation.get("elapsed_ms"),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        return PASS, receipt
    except ValidationBlocked as exc:
        receipt = {
            "status": "BLOCKED",
            "task_id": ((req or {}).get("task_identity") or {}).get("task_id"),
            "workstream_id": (req or {}).get("workstream_id"),
            "changed_paths": [],
            "terminal_event_id": prepared.get("event_id") if prepared else None,
            "artifact_record_ids": prepared.get("artifact_ids", []) if prepared else [],
            "decision_record_ids": prepared.get("decision_ids", []) if prepared else [],
            "submission_record_ids": prepared.get("submission_ids", []) if prepared else [],
            "workstream_state_changed": False,
            "project_state_changed": False,
            "validation_status": "FAIL",
            "next_route_position": None,
            "warnings": exc.validation.get("warnings", []),
            "validation_errors": exc.validation.get("errors", []),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        return VALIDATION_FAILURE, receipt
    except Exception as exc:
        receipt = {
            "status": "ERROR",
            "task_id": ((req or {}).get("task_identity") or {}).get("task_id"),
            "workstream_id": (req or {}).get("workstream_id"),
            "changed_paths": [],
            "terminal_event_id": prepared.get("event_id") if prepared else None,
            "artifact_record_ids": prepared.get("artifact_ids", []) if prepared else [],
            "decision_record_ids": prepared.get("decision_ids", []) if prepared else [],
            "submission_record_ids": prepared.get("submission_ids", []) if prepared else [],
            "workstream_state_changed": False,
            "project_state_changed": False,
            "validation_status": "ERROR",
            "next_route_position": None,
            "warnings": [],
            "errors": [str(exc)],
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        return TOOL_FAILURE, receipt
    finally:
        cleanup(prepared)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministically close an ordinary MD workflow task")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code, receipt = run(Path(args.project_root).resolve(), Path(args.skill_root).resolve(), Path(args.request).resolve())
    text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

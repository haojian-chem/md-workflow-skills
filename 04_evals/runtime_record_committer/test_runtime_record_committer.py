import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "05_tools/runtime_record_committer/commit_records.py"


def load_module():
    spec = importlib.util.spec_from_file_location("runtime_record_committer", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def fixed_time():
    return "2026-08-09T09:00:00+00:00"


def make_project(root: Path, task_id="task_0001"):
    ws = "ws_0001_test"
    artifact_file = root / "01_structure_preparation/01_source_recognition/input.pdb"
    artifact_file.parent.mkdir(parents=True, exist_ok=True)
    artifact_file.write_text("ATOM      1  CA  ALA A   1       0.000   0.000   0.000\nEND\n", encoding="utf-8")
    raw = artifact_file.read_bytes()
    stat = artifact_file.stat()
    file_record = {
        "path": artifact_file.relative_to(root).as_posix(),
        "state": "present_unvalidated",
        "role": "selected_source_structure",
        "source_task": task_id,
        "size_bytes": stat.st_size,
        "modified_at": fixed_time(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "notes": "fixture",
    }
    task = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": ws,
        "workflow_name": "structure_preparation_workflow",
        "route_id": None,
        "sequence": 1,
        "task_unit": {
            "mode": "OPERATION",
            "operation": {"skill_name": "source_recognition", "skill_path": "02_operations/source_recognition", "skill_layer": "operation"},
            "validator": None,
        },
        "project_root": str(root),
        "work_directory": "01_structure_preparation/01_source_recognition",
        "permissions": {
            "allowed_read_paths": [str(root)],
            "allowed_write_paths": [str(root / "01_structure_preparation")],
            "forbidden_paths": [str(root / "00_project_state"), str(root / "00_project_records")],
        },
        "current_valid_files": [],
        "upstream_summary": "fixture",
        "user_decisions": [],
        "required_outputs": ["STRUCTURE"],
        "detail_output_paths": {"log_file": None, "report_file": None, "result_data_file": None},
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }
    state = {
        "schema_version": 1,
        "workstream_id": ws,
        "title": "fixture",
        "purpose": "runtime record committer test",
        "origin": {"parent_workstream_id": None, "fork_reason": None, "forked_from_artifact_set_ids": []},
        "current_position": {"workflow_name": "structure_preparation_workflow", "substep": "source_recognition", "task_id": task_id},
        "lifecycle_status": "OPEN",
        "activity_status": "IDLE",
        "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
        "active_route_id": None,
        "active_task_id": None,
        "current_artifact_set_ids": {"structure": [], "topology": [], "system": [], "md_input": [], "md_output": [], "analysis_result": []},
        "pending_decision_ids": [],
        "active_submission_ids": [],
        "last_event_id": None,
        "last_updated_by": "fixture",
        "last_updated_at": fixed_time(),
    }
    dump(root / f"00_project_records/workstreams/{ws}/tasks/{task_id}/task.yaml", task)
    dump(root / f"00_project_state/workstreams/{ws}.yaml", state)
    (root / "00_project_records/events").mkdir(parents=True, exist_ok=True)
    return ws, file_record, state


def component_result(file_record=None):
    return {
        "skill_name": "source_recognition",
        "status": "DONE",
        "summary": "fixture operation finished",
        "outcome_code": "SOURCE_SELECTED",
        "key_findings": [],
        "created_files": [file_record] if file_record else [],
        "modified_files": [],
        "validated_files": [],
        "warnings": [],
        "failure": None,
        "detail_files": {"log_file": None, "report_file": None, "result_data_file": None},
    }


def result(task_id, ws, status="DONE", file_record=None):
    op = component_result(file_record)
    op["status"] = status
    if status == "FAILED":
        op["failure"] = {"failure_type": "FIXTURE_FAILURE", "failure_reason": "fixture", "recoverable": True, "blocked_by": []}
    return {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": ws,
        "task_unit_mode": "OPERATION",
        "status": status,
        "execution_summary": f"fixture {status}",
        "operation_result": op,
        "validation_result": None,
        "artifact_candidates": ([{"artifact_type": "STRUCTURE", "files": [file_record], "derived_from_artifact_set_ids": []}] if file_record else []),
        "confirmation_items": [],
        "warnings": [],
        "failure": ({"failure_type": "FIXTURE_FAILURE", "failure_reason": "fixture", "recoverable": True, "blocked_by": []} if status == "FAILED" else None),
        "next_step_recommendation": "",
    }


def request(task_id, ws, responsibility_result, **overrides):
    req = {
        "schema_version": 1,
        "task_identity": {"task_id": task_id, "task_unit_mode": "OPERATION"},
        "workstream_id": ws,
        "route_id": None,
        "route_node_id": "1.1",
        "execution_backend": "AGENT_TASK",
        "responsibility_result": responsibility_result,
        "semantic_state_delta": {
            "activity_status": "READY",
            "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
        },
        "artifact_updates": [],
        "decision_updates": [],
        "submission_updates": [],
        "route_progression": {"action": "SET", "position": {"workflow_name": "structure_preparation_workflow", "substep": "component_and_residue_classification", "task_id": None}},
        "allowed_management_paths": ["00_project_records/**", "00_project_state/**"],
        "timestamp": fixed_time(),
    }
    req.update(overrides)
    return req


def run_cli(root: Path, req):
    req_path = root / "commit_request.yaml"
    dump(req_path, req)
    proc = subprocess.run([sys.executable, str(TOOL), "--project-root", str(root), "--skill-root", str(REPO_ROOT), "--request", str(req_path)], text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_done_artifact_and_real_fast_validator(tmp_path):
    ws, file_record, _ = make_project(tmp_path)
    rr = result("task_0001", ws, "DONE", file_record)
    req = request("task_0001", ws, rr)
    req["artifact_updates"] = [{
        "candidate_index": 0,
        "artifact_set_id": "aset_0001_structure",
        "validation_status": "UNVALIDATED",
        "validator_task_id": None,
        "supersedes": [],
        "notes": "fixture",
        "current_state_action": "REPLACE_TYPE",
    }]
    code, receipt = run_cli(tmp_path, req)
    assert code == 0, receipt
    assert receipt["status"] == "COMMITTED"
    assert receipt["validation_status"] == "PASS"
    result_path = tmp_path / f"00_project_records/workstreams/{ws}/tasks/task_0001/result.yaml"
    artifact_path = tmp_path / f"00_project_records/workstreams/{ws}/artifacts/aset_0001_structure.yaml"
    assert result_path.is_file() and artifact_path.is_file()
    state = yaml.safe_load((tmp_path / f"00_project_state/workstreams/{ws}.yaml").read_text())
    assert state["current_artifact_set_ids"]["structure"] == ["aset_0001_structure"]
    assert state["current_position"]["substep"] == "component_and_residue_classification"
    events = [json.loads(x) for x in (tmp_path / "00_project_records/events/project_events.jsonl").read_text().splitlines() if x]
    assert events[-1]["event_type"] == "TASK_DONE"


def test_blocked_closure(tmp_path):
    ws, _, _ = make_project(tmp_path)
    rr = result("task_0001", ws, "BLOCKED")
    req = request("task_0001", ws, rr, semantic_state_delta={
        "activity_status": "WAITING",
        "hold_reason": {"type": "USER_DECISION", "details": "fixture decision", "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
    }, route_progression={"action": "KEEP"})
    code, receipt = run_cli(tmp_path, req)
    assert code == 0, receipt
    state = yaml.safe_load((tmp_path / f"00_project_state/workstreams/{ws}.yaml").read_text())
    assert state["activity_status"] == "WAITING"
    event = json.loads((tmp_path / "00_project_records/events/project_events.jsonl").read_text().strip())
    assert event["event_type"] == "TASK_BLOCKED"


def test_failed_closure(tmp_path):
    ws, _, _ = make_project(tmp_path)
    rr = result("task_0001", ws, "FAILED")
    req = request("task_0001", ws, rr, semantic_state_delta={
        "activity_status": "FAILED",
        "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
    }, route_progression={"action": "KEEP"})
    code, receipt = run_cli(tmp_path, req)
    assert code == 0, receipt
    state = yaml.safe_load((tmp_path / f"00_project_state/workstreams/{ws}.yaml").read_text())
    assert state["activity_status"] == "FAILED"


def test_project_state_not_rewritten(tmp_path):
    ws, _, _ = make_project(tmp_path)
    project_state = tmp_path / "00_project_state/project_state.yaml"
    project_state.write_bytes(b"sentinel: keep-me\n")
    before = project_state.read_bytes()
    code, receipt = run_cli(tmp_path, request("task_0001", ws, result("task_0001", ws)))
    assert code == 0, receipt
    assert project_state.read_bytes() == before
    assert receipt["project_state_changed"] is False


def test_invalid_semantic_delta_fails_before_writes(tmp_path):
    ws, _, _ = make_project(tmp_path)
    req = request("task_0001", ws, result("task_0001", ws))
    req["semantic_state_delta"]["title"] = "not allowed"
    code, receipt = run_cli(tmp_path, req)
    assert code == 2
    assert receipt["status"] == "ERROR"
    assert not (tmp_path / f"00_project_records/workstreams/{ws}/tasks/task_0001/result.yaml").exists()
    assert not (tmp_path / "00_project_records/events/project_events.jsonl").exists()


def test_real_fast_validator_blocks_malformed_result(tmp_path):
    ws, _, _ = make_project(tmp_path)
    rr = result("task_0001", ws)
    del rr["execution_summary"]
    code, receipt = run_cli(tmp_path, request("task_0001", ws, rr))
    assert code == 1, receipt
    assert receipt["status"] == "BLOCKED"
    assert receipt["validation_status"] == "FAIL"
    assert not (tmp_path / f"00_project_records/workstreams/{ws}/tasks/task_0001/result.yaml").exists()


def test_partial_commit_rolls_back(tmp_path):
    ws, _, _ = make_project(tmp_path)
    req = request("task_0001", ws, result("task_0001", ws), route_progression={"action": "KEEP"})
    module = load_module()
    prepared = module.prepare_candidates(tmp_path, req)
    state_path = tmp_path / f"00_project_state/workstreams/{ws}.yaml"
    before = state_path.read_bytes()
    with pytest.raises(module.CommitterError):
        module.controlled_commit(tmp_path, prepared, fail_after_step=2)
    assert state_path.read_bytes() == before
    assert not (tmp_path / f"00_project_records/workstreams/{ws}/tasks/task_0001/result.yaml").exists()
    assert not (tmp_path / "00_project_records/events/project_events.jsonl").exists()
    module.cleanup(prepared)

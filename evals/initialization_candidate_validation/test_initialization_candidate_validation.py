import json
from pathlib import Path
import statistics
import subprocess
import sys

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "05_tools/runtime_schema_validator/validate.py"
CONTRACTS = REPO_ROOT / "03_contracts"
STAMP = "2026-08-09T09:00:00+00:00"


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def candidates(root: Path, *, broken_project=False, include_ws=True, active_route=None):
    ws_id = "ws_0001_test"
    project = {
        "schema_version": 2,
        "project": {
            "project_id": "proj_test",
            "skill_architecture_root": str(REPO_ROOT),
            "md_project_root": str(root),
        },
        "entry_state": "RESUMABLE",
        "focus": {"target_type": "WORKSTREAM", "workstream_id": ws_id, "reason": "USER_SELECTED", "selected_at": STAMP},
        "related_workstreams": [],
        "workstreams": [{"workstream_id": ws_id, "state_path": f"00_project_state/workstreams/{ws_id}.yaml"}],
        "pending_project_decision_ids": [],
        "last_project_event_id": None,
        "last_updated_by": "md_workflow_manager",
        "last_updated_at": STAMP,
    }
    if broken_project:
        project.pop("entry_state")
    ws = {
        "schema_version": 1,
        "workstream_id": ws_id,
        "title": "initial workstream",
        "purpose": "fixture",
        "origin": {"parent_workstream_id": None, "fork_reason": None, "forked_from_artifact_set_ids": []},
        "current_position": {"workflow_name": None, "substep": None, "task_id": None},
        "lifecycle_status": "OPEN",
        "activity_status": "IDLE",
        "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
        "active_route_id": active_route,
        "active_task_id": None,
        "current_artifact_set_ids": {"structure": [], "topology": [], "system": [], "md_input": [], "md_output": [], "analysis_result": []},
        "pending_decision_ids": [],
        "active_submission_ids": [],
        "last_event_id": None,
        "last_updated_by": "md_workflow_manager",
        "last_updated_at": STAMP,
    }
    p_candidate = root / ".init_candidates/project_state.yaml"
    ws_candidate = root / ".init_candidates/workstream_state.yaml"
    dump(p_candidate, project)
    if include_ws:
        dump(ws_candidate, ws)
    return p_candidate, ws_candidate, ws_id


def run_validator(root: Path, mode: str, p_candidate: Path, ws_candidate: Path | None, ws_id: str):
    changed = [p_candidate]
    maps = [(p_candidate, "00_project_state/project_state.yaml")]
    if ws_candidate is not None:
        changed.append(ws_candidate)
        maps.append((ws_candidate, f"00_project_state/workstreams/{ws_id}.yaml"))
    cmd = [sys.executable, str(VALIDATOR), "--project-root", str(root), "--contracts-dir", str(CONTRACTS), "--mode", mode, "--changed", *map(str, changed)]
    for actual, logical in maps:
        cmd += ["--logical-map", f"{actual}={logical}"]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_restricted_fast_valid_initial_candidates_match_full(tmp_path):
    p, ws, ws_id = candidates(tmp_path)
    fast_code, fast = run_validator(tmp_path, "FAST", p, ws, ws_id)
    full_code, full = run_validator(tmp_path, "FULL", p, ws, ws_id)
    assert fast_code == 0 and fast["status"] == "PASS"
    assert full_code == 0 and full["status"] == "PASS"
    assert len(fast["validated"]) == 2


def test_schema_invalid_candidate_fails_restricted_fast_and_full(tmp_path):
    p, ws, ws_id = candidates(tmp_path, broken_project=True)
    fast_code, fast = run_validator(tmp_path, "FAST", p, ws, ws_id)
    full_code, full = run_validator(tmp_path, "FULL", p, ws, ws_id)
    assert fast_code == 1 and fast["status"] == "FAIL"
    assert full_code == 1 and full["status"] == "FAIL"


def test_missing_initial_workstream_reference_fails(tmp_path):
    p, ws, ws_id = candidates(tmp_path, include_ws=False)
    code, out = run_validator(tmp_path, "FAST", p, None, ws_id)
    assert code == 1 and out["status"] == "FAIL"
    assert any("workstream state path" in e.get("message", "") for e in out["errors"])


def test_active_route_without_route_record_fails(tmp_path):
    p, ws, ws_id = candidates(tmp_path, active_route="route_should_not_exist")
    code, out = run_validator(tmp_path, "FAST", p, ws, ws_id)
    assert code == 1 and out["status"] == "FAIL"
    assert any("missing route reference" in e.get("message", "") for e in out["errors"])


def test_business_structure_content_is_not_an_init_validation_target(tmp_path):
    p, ws, ws_id = candidates(tmp_path)
    pdb = tmp_path / "input.pdb"
    pdb.write_bytes(b"not-even-a-valid-pdb\x00\xff" * 1000)
    code, out = run_validator(tmp_path, "FAST", p, ws, ws_id)
    assert code == 0 and out["status"] == "PASS"
    validated = {Path(x["logical_path"]).name for x in out["validated"]}
    assert validated == {"project_state.yaml", f"{ws_id}.yaml"}


def test_restricted_fast_does_not_turn_unrelated_record_into_validation_target(tmp_path):
    p, ws, ws_id = candidates(tmp_path)
    unrelated = tmp_path / "00_project_records/workstreams/old/tasks/old/task.yaml"
    unrelated.parent.mkdir(parents=True, exist_ok=True)
    unrelated.write_text("this: is not a valid task record\n", encoding="utf-8")
    fast_code, fast = run_validator(tmp_path, "FAST", p, ws, ws_id)
    full_code, full = run_validator(tmp_path, "FULL", p, ws, ws_id)
    assert fast_code == 0 and fast["status"] == "PASS"
    assert full_code == 1 and full["status"] == "FAIL"
    assert len(fast["validated"]) == 2


def test_candidate_validation_benchmark(tmp_path):
    samples = []
    for index in range(8):
        root = tmp_path / f"bench_{index}"
        root.mkdir()
        p, ws, ws_id = candidates(root)
        code, out = run_validator(root, "FAST", p, ws, ws_id)
        assert code == 0, out
        samples.append(float(out["elapsed_ms"]))
    assert statistics.median(samples) < 1000

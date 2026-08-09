import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "05_tools/source_recognition_deterministic/run.py"
FAST_TOOL = REPO_ROOT / "05_tools/route_fast_path_evaluator/evaluate.py"
RUNTIME_SPEC = REPO_ROOT / "runtime/workflows/structure_preparation.runtime.yaml"
R4_HELPERS = REPO_ROOT / "04_evals/runtime_record_committer/test_runtime_record_committer.py"
STAMP = "2026-08-09T09:00:00+00:00"


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def source_record(path: Path, root: Path, role="source_candidate"):
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "state": "present_unvalidated",
        "role": role,
        "size_bytes": len(data),
        "modified_at": STAMP,
        "sha256": hashlib.sha256(data).hexdigest(),
        "notes": "fixture source",
    }


def base_state(ws="ws_0001_test", route_id=None, task_id="task_0001"):
    return {
        "schema_version": 1,
        "workstream_id": ws,
        "title": "fixture",
        "purpose": "source recognition deterministic test",
        "origin": {"parent_workstream_id": None, "fork_reason": None, "forked_from_artifact_set_ids": []},
        "current_position": {"workflow_name": "structure_preparation_workflow", "substep": "source_recognition", "task_id": task_id},
        "lifecycle_status": "OPEN",
        "activity_status": "IDLE",
        "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
        "active_route_id": route_id,
        "active_task_id": None,
        "current_artifact_set_ids": {"structure": [], "topology": [], "system": [], "md_input": [], "md_output": [], "analysis_result": []},
        "pending_decision_ids": [],
        "active_submission_ids": [],
        "last_event_id": None,
        "last_updated_by": "fixture",
        "last_updated_at": STAMP,
    }


def make_task(root: Path, candidates, *, route_id=None, allowed_read=None, task_id="task_0001"):
    ws = "ws_0001_test"
    workdir = root / "01_structure_preparation/01_source_recognition"
    workdir.mkdir(parents=True, exist_ok=True)
    task = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": ws,
        "workflow_name": "structure_preparation_workflow",
        "route_id": route_id,
        "sequence": 1,
        "task_unit": {
            "mode": "OPERATION",
            "operation": {"skill_name": "source_recognition", "skill_path": "02_operations/source_recognition", "skill_layer": "operation"},
            "validator": None,
        },
        "project_root": str(root),
        "work_directory": "01_structure_preparation/01_source_recognition",
        "permissions": {
            "allowed_read_paths": [str(x) for x in (allowed_read or [root / "raw"])],
            "allowed_write_paths": [str(workdir)],
            "forbidden_paths": [str(root / "00_project_state"), str(root / "00_project_records")],
        },
        "current_valid_files": [source_record(path, root) for path in candidates],
        "upstream_summary": "bounded raw source candidates",
        "user_decisions": [],
        "required_outputs": ["STRUCTURE"],
        "detail_output_paths": {"log_file": None, "report_file": None, "result_data_file": None},
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }
    task_path = root / f"00_project_records/workstreams/{ws}/tasks/{task_id}/task.yaml"
    dump(task_path, task)
    dump(root / f"00_project_state/workstreams/{ws}.yaml", base_state(ws, route_id, task_id))
    (root / "00_project_records/events").mkdir(parents=True, exist_ok=True)
    return task_path, ws


def pdb(path: Path, residue="ALA"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"HEADER    FIXTURE\nATOM      1  CA  {residue} A   1       0.000   0.000   0.000\nEND\n", encoding="utf-8")
    return path


def cif(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("data_fixture\nloop_\n_atom_site.group_PDB\n_atom_site.id\nATOM 1\n", encoding="utf-8")
    return path


def run_tool(task_path: Path):
    proc = subprocess.run([sys.executable, str(TOOL), "--task", str(task_path)], text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_unique_pdb_copy_done(tmp_path):
    source = pdb(tmp_path / "raw/input.pdb")
    task_path, _ = make_task(tmp_path, [source])
    code, out = run_tool(task_path)
    assert code == 0 and out["status"] == "DONE"
    target = tmp_path / "01_structure_preparation/01_source_recognition/input.pdb"
    assert target.read_bytes() == source.read_bytes()
    assert out["artifact_candidates"][0]["artifact_type"] == "STRUCTURE"
    assert out["operation_result"]["skill_name"] == "source_recognition"
    report = yaml.safe_load((target.parent / "source_recognition_report.yaml").read_text())
    assert report["action"] == "COPIED"


def test_unique_cif_copy_done(tmp_path):
    source = cif(tmp_path / "raw/input.cif")
    task_path, _ = make_task(tmp_path, [source])
    code, out = run_tool(task_path)
    assert code == 0 and out["status"] == "DONE"
    assert (tmp_path / "01_structure_preparation/01_source_recognition/input.cif").is_file()


def test_identical_destination_reused(tmp_path):
    source = pdb(tmp_path / "raw/input.pdb")
    work = tmp_path / "01_structure_preparation/01_source_recognition"
    work.mkdir(parents=True, exist_ok=True)
    (work / "input.pdb").write_bytes(source.read_bytes())
    task_path, _ = make_task(tmp_path, [source])
    code, out = run_tool(task_path)
    assert code == 0 and out["status"] == "DONE"
    assert out["operation_result"]["created_files"] == []
    report = yaml.safe_load((work / "source_recognition_report.yaml").read_text())
    assert report["action"] == "REUSED_IDENTICAL_COPY"


def test_multiple_valid_candidates_block_with_confirmation(tmp_path):
    a = pdb(tmp_path / "raw/a.pdb", "ALA")
    b = pdb(tmp_path / "raw/b.pdb", "GLY")
    task_path, _ = make_task(tmp_path, [a, b])
    code, out = run_tool(task_path)
    assert code == 0 and out["status"] == "BLOCKED"
    assert len(out["confirmation_items"]) == 1
    assert out["confirmation_items"][0]["category"] == "SOURCE_SELECTION"
    assert not (tmp_path / "01_structure_preparation/01_source_recognition/a.pdb").exists()
    assert not (tmp_path / "01_structure_preparation/01_source_recognition/b.pdb").exists()


def test_no_valid_candidate_blocks_without_copy(tmp_path):
    bad = tmp_path / "raw/bad.pdb"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("this is not PDB content\n", encoding="utf-8")
    task_path, _ = make_task(tmp_path, [bad])
    code, out = run_tool(task_path)
    assert code == 0 and out["status"] == "BLOCKED"
    assert out["operation_result"]["outcome_code"] == "NO_VALID_SOURCE"


def test_different_destination_blocks_without_overwrite(tmp_path):
    source = pdb(tmp_path / "raw/input.pdb", "ALA")
    work = tmp_path / "01_structure_preparation/01_source_recognition"
    work.mkdir(parents=True, exist_ok=True)
    target = pdb(work / "input.pdb", "GLY")
    before = target.read_bytes()
    task_path, _ = make_task(tmp_path, [source])
    code, out = run_tool(task_path)
    assert code == 0 and out["status"] == "BLOCKED"
    assert out["operation_result"]["outcome_code"] == "DESTINATION_CONFLICT"
    assert target.read_bytes() == before


def test_unauthorized_source_fails(tmp_path):
    source = pdb(tmp_path / "raw/input.pdb")
    denied = tmp_path / "different_read_root"
    denied.mkdir()
    task_path, _ = make_task(tmp_path, [source], allowed_read=[denied])
    code, out = run_tool(task_path)
    assert code == 2 and out["status"] == "FAILED"
    assert "outside authorized read scope" in out["failure"]["failure_reason"]


def route_record(ws):
    return {
        "schema_version": 3,
        "route_id": "route_0001",
        "workstream_id": ws,
        "created_at": STAMP,
        "created_by": "MANAGER",
        "supersedes": None,
        "planning_status": "COMPLETE",
        "scope_resolution": {"source": "USER_REQUEST", "resolved_event_id": "evt_scope", "decision_id": None},
        "scope": {"start": {"workflow_name": "structure_preparation_workflow", "substep": "source_recognition", "artifact_set_id": None, "point_kind": "SPECIFIC_SUBSTEP"}, "end": {"workflow_name": "structure_preparation_workflow", "substep": "component_and_residue_classification", "artifact_set_id": None, "point_kind": "SPECIFIC_SUBSTEP"}},
        "source_fragments": [{"fragment_id": "frag_1", "workflow_name": "structure_preparation_workflow", "workflow_path": "01_workflows/structure_preparation_workflow", "workflow_revision": None, "fragment_status": "COMPLETE"}],
        "steps": [
            {"sequence": 1, "workflow_name": "structure_preparation_workflow", "step_id": "source_recognition", "task_name": "source_recognition", "task_unit_mode": "OPERATION", "operation": {"skill_name": "source_recognition", "skill_path": "02_operations/source_recognition"}, "validator": None, "necessity": "REQUIRED", "condition": None, "work_directory": "01_structure_preparation/01_source_recognition", "prerequisites": [], "expected_outputs": ["STRUCTURE"], "gate_requirements": ["DONE"]},
            {"sequence": 2, "workflow_name": "structure_preparation_workflow", "step_id": "component_and_residue_classification", "task_name": "component_and_residue_classification", "task_unit_mode": "VALIDATOR", "operation": None, "validator": {"skill_name": "component_and_residue_classification_validator", "skill_path": "02_validators/component_and_residue_classification_validator"}, "necessity": "REQUIRED", "condition": None, "work_directory": "01_structure_preparation/02_component_and_residue_classification", "prerequisites": ["source_recognition"], "expected_outputs": ["classification_result"], "gate_requirements": ["CLASSIFIED"]},
        ],
        "change_reason": ["fixture"],
        "assumptions": [],
        "conditional_steps": [],
        "known_blockers": [],
        "stop_conditions": ["scope end"],
    }


def test_deterministic_1_1_to_r5_to_r4_integration(tmp_path):
    source = pdb(tmp_path / "raw/input.pdb")
    task_path, ws = make_task(tmp_path, [source], route_id="route_0001")
    route_path = tmp_path / f"00_project_records/workstreams/{ws}/routes/route_0001.yaml"
    dump(route_path, route_record(ws))

    code, responsibility = run_tool(task_path)
    assert code == 0 and responsibility["status"] == "DONE"
    responsibility_path = tmp_path / "responsibility.yaml"
    dump(responsibility_path, responsibility)

    context = {
        "schema_version": 1,
        "current_step_id": "source_recognition",
        "task_id": "task_0001",
        "gate_status": "PASS",
        "artifact_interface_status": "MATCH",
        "artifact_lineage_status": "OK",
        "route_affecting_evidence": False,
        "conditional_evidence_changed": False,
        "unexpected_output": False,
        "user_instruction_changed": False,
        "recovery_status": "NONE",
        "high_risk_barrier": False,
        "next_inputs_status": "READY",
        "next_condition_status": "NOT_APPLICABLE",
    }
    context_path = tmp_path / "fast_context.yaml"
    dump(context_path, context)
    state_path = tmp_path / f"00_project_state/workstreams/{ws}.yaml"
    proc = subprocess.run([sys.executable, str(FAST_TOOL), "--route", str(route_path), "--workstream-state", str(state_path), "--result", str(responsibility_path), "--runtime-spec", str(RUNTIME_SPEC), "--context", str(context_path)], text=True, capture_output=True)
    fast = json.loads(proc.stdout)
    assert proc.returncode == 0 and fast["decision"] == "ADVANCE"

    spec = importlib.util.spec_from_file_location("rrc_helpers", R4_HELPERS)
    helpers = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(helpers)
    req = helpers.request("task_0001", ws, responsibility, route_id="route_0001", route_progression={"action": "SET", "position": fast["next_route_position"]})
    req["artifact_updates"] = [{
        "candidate_index": 0,
        "artifact_set_id": "aset_0001_structure",
        "validation_status": "UNVALIDATED",
        "validator_task_id": None,
        "supersedes": [],
        "notes": "deterministic 1.1 output",
        "current_state_action": "REPLACE_TYPE",
    }]
    commit_code, receipt = helpers.run_cli(tmp_path, req)
    assert commit_code == 0, receipt
    final_state = yaml.safe_load(state_path.read_text())
    assert final_state["current_position"]["substep"] == "component_and_residue_classification"
    assert final_state["current_artifact_set_ids"]["structure"] == ["aset_0001_structure"]
    assert (tmp_path / f"00_project_records/workstreams/{ws}/tasks/task_0001/result.yaml").is_file()

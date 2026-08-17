import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "05_tools/route_fast_path_evaluator/evaluate.py"
RUNTIME_SPEC = REPO_ROOT / "runtime/workflows/structure_preparation.runtime.yaml"


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")


def step(seq, step_id, task_name, mode="OPERATION", necessity="REQUIRED"):
    op = {"skill_name": "source_recognition", "skill_path": "02_operations/source_recognition"} if mode != "VALIDATOR" else None
    val = {"skill_name": "component_and_residue_classification_validator", "skill_path": "02_validators/component_and_residue_classification_validator"} if mode != "OPERATION" else None
    return {"sequence": seq, "workflow_name": "structure_preparation_workflow", "step_id": step_id, "task_name": task_name, "task_unit_mode": mode, "operation": op, "validator": val, "necessity": necessity, "condition": None if necessity == "REQUIRED" else "fixture condition", "work_directory": f"01_structure_preparation/{seq:02d}_{task_name}", "prerequisites": [], "expected_outputs": ["STRUCTURE"], "gate_requirements": ["DONE"]}


def route(steps, status="COMPLETE", blockers=None):
    return {"schema_version": 3, "route_id": "route_0001", "workstream_id": "ws_0001_test", "created_at": "2026-08-09T09:00:00+00:00", "created_by": "MANAGER", "supersedes": None, "planning_status": status, "scope_resolution": {"source": "USER_REQUEST", "resolved_event_id": "evt_scope", "decision_id": None}, "scope": {"start": {"workflow_name": "structure_preparation_workflow", "substep": steps[0]["task_name"], "artifact_set_id": None, "point_kind": "SPECIFIC_SUBSTEP"}, "end": {"workflow_name": "structure_preparation_workflow", "substep": steps[-1]["task_name"], "artifact_set_id": None, "point_kind": "SPECIFIC_SUBSTEP"}}, "source_fragments": [{"fragment_id": "frag_1", "workflow_name": "structure_preparation_workflow", "workflow_path": "01_workflows/structure_preparation_workflow", "workflow_revision": None, "fragment_status": status}], "steps": steps, "change_reason": ["fixture"], "assumptions": [], "conditional_steps": [x["step_id"] for x in steps if x["necessity"] == "CONDITIONAL"], "known_blockers": blockers or [], "stop_conditions": ["scope end"]}


def state(substep="source_recognition", task_id="task_0001"):
    return {"schema_version": 1, "workstream_id": "ws_0001_test", "title": "fixture", "purpose": "fixture", "origin": {"parent_workstream_id": None, "fork_reason": None, "forked_from_artifact_set_ids": []}, "current_position": {"workflow_name": "structure_preparation_workflow", "substep": substep, "task_id": task_id}, "lifecycle_status": "OPEN", "activity_status": "IDLE", "hold_reason": {"type": "NONE", "details": None, "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None}, "active_route_id": "route_0001", "active_task_id": None, "current_artifact_set_ids": {"structure": [], "topology": [], "system": [], "md_input": [], "md_output": [], "analysis_result": []}, "pending_decision_ids": [], "active_submission_ids": [], "last_event_id": None, "last_updated_by": "fixture", "last_updated_at": "2026-08-09T09:00:00+00:00"}


def result(status="DONE", confirmations=None, failure=None):
    return {"schema_version": 2, "task_id": "task_0001", "workstream_id": "ws_0001_test", "task_unit_mode": "OPERATION", "status": status, "execution_summary": "fixture", "operation_result": {"skill_name": "source_recognition", "status": status, "summary": "fixture", "outcome_code": "SOURCE_SELECTED", "key_findings": [], "created_files": [], "modified_files": [], "validated_files": [], "warnings": [], "failure": failure, "detail_files": {"log_file": None, "report_file": None, "result_data_file": None}}, "validation_result": None, "artifact_candidates": [], "confirmation_items": confirmations or [], "warnings": [], "failure": failure, "next_step_recommendation": ""}


def context(**kw):
    obj = {"schema_version": 1, "current_step_id": "source_recognition", "task_id": "task_0001", "gate_status": "PASS", "artifact_interface_status": "MATCH", "artifact_lineage_status": "OK", "route_affecting_evidence": False, "conditional_evidence_changed": False, "unexpected_output": False, "user_instruction_changed": False, "recovery_status": "NONE", "high_risk_barrier": False, "next_inputs_status": "READY", "next_condition_status": "NOT_APPLICABLE"}
    obj.update(kw)
    return obj


def run_eval(tmp_path, route_obj, state_obj=None, result_obj=None, context_obj=None):
    paths = {"route": tmp_path / "route.yaml", "state": tmp_path / "state.yaml", "result": tmp_path / "result.yaml", "context": tmp_path / "context.yaml"}
    dump(paths["route"], route_obj)
    dump(paths["state"], state_obj or state())
    dump(paths["result"], result_obj or result())
    dump(paths["context"], context_obj or context())
    proc = subprocess.run([sys.executable, str(TOOL), "--route", str(paths["route"]), "--workstream-state", str(paths["state"]), "--result", str(paths["result"]), "--runtime-spec", str(RUNTIME_SPEC), "--context", str(paths["context"])], text=True, capture_output=True)
    return proc.returncode, json.loads(proc.stdout)


def base_steps(next_necessity="REQUIRED"):
    return [step(1, "source_recognition", "source_recognition"), step(2, "component_and_residue_classification", "component_and_residue_classification", "VALIDATOR", next_necessity)]


def test_required_next_advances(tmp_path):
    code, out = run_eval(tmp_path, route(base_steps()))
    assert code == 0 and out["decision"] == "ADVANCE"
    assert out["to_step_id"] == "component_and_residue_classification"


def test_scope_end_stops(tmp_path):
    code, out = run_eval(tmp_path, route([base_steps()[0]]))
    assert code == 0 and out["decision"] == "STOP_SCOPE"


def test_conditional_unknown_reenters(tmp_path):
    code, out = run_eval(tmp_path, route(base_steps("CONDITIONAL")), context_obj=context(next_condition_status="UNKNOWN"))
    assert code == 0 and out["decision"] == "REENTER_WORKFLOW"


def test_conditional_true_advances(tmp_path):
    code, out = run_eval(tmp_path, route(base_steps("CONDITIONAL")), context_obj=context(next_condition_status="TRUE"))
    assert code == 0 and out["decision"] == "ADVANCE"


def test_confirmation_reenters(tmp_path):
    confirmation = {"schema_version": 2, "decision_id": "dec_1", "scope": "WORKSTREAM", "workstream_id": "ws_0001_test", "source_task_id": "task_0001", "category": "fixture", "question": "choose?", "reason": "fixture", "affected_records": [], "available_options": [], "recommended_option": None, "blocking": True}
    code, out = run_eval(tmp_path, route(base_steps()), result_obj=result(confirmations=[confirmation]))
    assert code == 0 and out["decision"] == "REENTER_WORKFLOW"


def test_route_affecting_evidence_reenters(tmp_path):
    code, out = run_eval(tmp_path, route(base_steps()), context_obj=context(route_affecting_evidence=True))
    assert code == 0 and out["decision"] == "REENTER_WORKFLOW"


def test_recovery_blocks(tmp_path):
    code, out = run_eval(tmp_path, route(base_steps()), context_obj=context(recovery_status="WORKSTREAM"))
    assert code == 0 and out["decision"] == "BLOCKED"


def test_position_conflict_blocks(tmp_path):
    code, out = run_eval(tmp_path, route(base_steps()), state_obj=state(substep="wrong"))
    assert code == 0 and out["decision"] == "BLOCKED"


def test_partial_route_boundary_blocks(tmp_path):
    blocker = {"code": "WF_MISSING", "reason": "next workflow missing", "blocking_scope": "WORKFLOW_BOUNDARY", "workflow_name": "topology_preparation_workflow"}
    code, out = run_eval(tmp_path, route([base_steps()[0]], status="PARTIAL", blockers=[blocker]))
    assert code == 0 and out["decision"] == "BLOCKED"


def test_r4_committer_integration_advances_state(tmp_path):
    helper_path = REPO_ROOT / "04_evals/runtime_record_committer/test_runtime_record_committer.py"
    spec = importlib.util.spec_from_file_location("rrc_helpers", helper_path)
    helpers = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(helpers)
    ws, _, _ = helpers.make_project(tmp_path)
    route_obj = route(base_steps())
    route_path = tmp_path / f"00_project_records/workstreams/{ws}/routes/route_0001.yaml"
    dump(route_path, route_obj)
    task_path = tmp_path / f"00_project_records/workstreams/{ws}/tasks/task_0001/task.yaml"
    task_obj = yaml.safe_load(task_path.read_text())
    task_obj["route_id"] = "route_0001"
    dump(task_path, task_obj)
    state_path = tmp_path / f"00_project_state/workstreams/{ws}.yaml"
    state_obj = yaml.safe_load(state_path.read_text())
    state_obj["active_route_id"] = "route_0001"
    dump(state_path, state_obj)
    responsibility = helpers.result("task_0001", ws)
    result_path = tmp_path / "responsibility_result.yaml"
    dump(result_path, responsibility)
    ctx_path = tmp_path / "fast_context.yaml"
    dump(ctx_path, context())
    proc = subprocess.run([sys.executable, str(TOOL), "--route", str(route_path), "--workstream-state", str(state_path), "--result", str(result_path), "--runtime-spec", str(RUNTIME_SPEC), "--context", str(ctx_path)], text=True, capture_output=True)
    fast = json.loads(proc.stdout)
    assert proc.returncode == 0 and fast["decision"] == "ADVANCE"
    commit_req = helpers.request("task_0001", ws, responsibility, route_id="route_0001", route_progression={"action": "SET", "position": fast["next_route_position"]})
    code, receipt = helpers.run_cli(tmp_path, commit_req)
    assert code == 0, receipt
    final_state = yaml.safe_load(state_path.read_text())
    assert final_state["current_position"]["substep"] == "component_and_residue_classification"

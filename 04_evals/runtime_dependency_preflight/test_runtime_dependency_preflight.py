import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "05_tools/runtime_dependency_preflight/check.py"
R4 = REPO_ROOT / "05_tools/runtime_record_committer/commit_records.py"
REAL_MANIFEST = "02_validators/component_and_residue_classification_validator/references/runtime_dependencies.json"
STAMP = "2026-08-09T09:00:00+00:00"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def dump_yaml(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def run_preflight(skill_root: Path, manifest: str, task_id="task_0002", ws="ws_0001_test", mode="VALIDATOR"):
    proc = subprocess.run([
        sys.executable, str(TOOL),
        "--skill-root", str(skill_root),
        "--manifest", manifest,
        "--task-id", task_id,
        "--workstream-id", ws,
        "--task-unit-mode", mode,
    ], text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def make_manifest(root: Path, dependencies, *, corrupt_owner_guard=False, corrupt_requirements_guard=False):
    owner = root / "owner/SKILL.md"
    requirements = root / "owner/requirements.txt"
    owner.parent.mkdir(parents=True, exist_ok=True)
    owner.write_text("fixture owner\n", encoding="utf-8")
    requirements.write_text("fixture requirements\n", encoding="utf-8")
    owner_sha = git_blob_sha(owner.read_bytes())
    req_sha = git_blob_sha(requirements.read_bytes())
    manifest = {
        "schema_version": 1,
        "owner_skill": {
            "skill_name": "component_and_residue_classification_validator",
            "path": "owner/SKILL.md",
            "expected_git_blob_sha": ("0" * 40 if corrupt_owner_guard else owner_sha),
            "task_unit_mode": "VALIDATOR",
        },
        "requirements_source": {
            "path": "owner/requirements.txt",
            "expected_git_blob_sha": ("1" * 40 if corrupt_requirements_guard else req_sha),
        },
        "dependencies": dependencies,
        "blocked_outcome": {
            "outcome_code": "MISSING_RUNTIME_DEPENDENCY",
            "summary": "fixture dependency blocker",
        },
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return "manifest.json"


def test_real_stage_1_2_manifest_passes(tmp_path):
    code, out = run_preflight(REPO_ROOT, REAL_MANIFEST)
    assert code == 0, out
    assert out["status"] == "PASS"
    assert out["responsibility_result"] is None
    names = {x["import_name"] for x in out["dependencies"]}
    assert names == {"gemmi", "yaml", "jsonschema", "referencing"}
    assert all(x["status"] == "PASS" for x in out["dependencies"])


def test_missing_dependency_returns_structured_blocker(tmp_path):
    manifest = make_manifest(tmp_path, [{"import_name": "definitely_missing_md_workflow_package", "distribution_name": "definitely-missing-md-workflow-package", "version_spec": ">=1,<2"}])
    code, out = run_preflight(tmp_path, manifest)
    assert code == 0
    assert out["status"] == "BLOCKED"
    assert out["blocked_dependencies"][0]["status"] == "MISSING_OR_IMPORT_FAILED"
    rr = out["responsibility_result"]
    assert rr["status"] == "BLOCKED"
    assert rr["task_unit_mode"] == "VALIDATOR"
    assert rr["validation_result"]["skill_name"] == "component_and_residue_classification_validator"
    assert rr["validation_result"]["outcome_code"] == "MISSING_RUNTIME_DEPENDENCY"


def test_incompatible_version_returns_blocked(tmp_path):
    manifest = make_manifest(tmp_path, [{"import_name": "yaml", "distribution_name": "PyYAML", "version_spec": "<1"}])
    code, out = run_preflight(tmp_path, manifest)
    assert code == 0 and out["status"] == "BLOCKED"
    assert out["blocked_dependencies"][0]["status"] == "VERSION_INCOMPATIBLE"


def test_owner_guard_mismatch_is_error(tmp_path):
    manifest = make_manifest(tmp_path, [{"import_name": "json", "distribution_name": "PyYAML", "version_spec": ">=6,<7"}], corrupt_owner_guard=True)
    code, out = run_preflight(tmp_path, manifest)
    assert code == 2 and out["status"] == "ERROR"
    assert "OWNER_SKILL_GUARD_MISMATCH" in out["errors"][0]


def test_requirements_guard_mismatch_is_error(tmp_path):
    manifest = make_manifest(tmp_path, [{"import_name": "json", "distribution_name": "PyYAML", "version_spec": ">=6,<7"}], corrupt_requirements_guard=True)
    code, out = run_preflight(tmp_path, manifest)
    assert code == 2 and out["status"] == "ERROR"
    assert "REQUIREMENTS_SOURCE_GUARD_MISMATCH" in out["errors"][0]


def make_project(root: Path):
    ws = "ws_0001_test"
    task_id = "task_0002"
    task = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": ws,
        "workflow_name": "structure_preparation_workflow",
        "route_id": None,
        "sequence": 2,
        "task_unit": {
            "mode": "VALIDATOR",
            "operation": None,
            "validator": {"skill_name": "component_and_residue_classification_validator", "skill_path": "02_validators/component_and_residue_classification_validator", "skill_layer": "validator"},
        },
        "project_root": str(root),
        "work_directory": "01_structure_preparation/02_component_and_residue_classification",
        "permissions": {
            "allowed_read_paths": [str(root)],
            "allowed_write_paths": [str(root / "01_structure_preparation/02_component_and_residue_classification")],
            "forbidden_paths": [str(root / "00_project_state"), str(root / "00_project_records")],
        },
        "current_valid_files": [],
        "upstream_summary": "fixture",
        "user_decisions": [],
        "required_outputs": ["classification_result"],
        "detail_output_paths": {"log_file": None, "report_file": None, "result_data_file": None},
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }
    state = {
        "schema_version": 1,
        "workstream_id": ws,
        "title": "fixture",
        "purpose": "dependency preflight test",
        "origin": {"parent_workstream_id": None, "fork_reason": None, "forked_from_artifact_set_ids": []},
        "current_position": {"workflow_name": "structure_preparation_workflow", "substep": "component_and_residue_classification", "task_id": task_id},
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
        "last_updated_at": STAMP,
    }
    dump_yaml(root / f"00_project_records/workstreams/{ws}/tasks/{task_id}/task.yaml", task)
    dump_yaml(root / f"00_project_state/workstreams/{ws}.yaml", state)
    (root / "00_project_records/events").mkdir(parents=True, exist_ok=True)
    return ws, task_id


def test_dependency_blocker_closes_via_active_r4(tmp_path):
    skill_fixture = tmp_path / "skill_fixture"
    skill_fixture.mkdir()
    manifest = make_manifest(skill_fixture, [{"import_name": "definitely_missing_md_workflow_package", "distribution_name": "definitely-missing-md-workflow-package", "version_spec": ">=1,<2"}])
    code, preflight = run_preflight(skill_fixture, manifest)
    assert code == 0 and preflight["status"] == "BLOCKED"

    project = tmp_path / "project"
    project.mkdir()
    ws, task_id = make_project(project)
    request = {
        "schema_version": 1,
        "task_identity": {"task_id": task_id, "task_unit_mode": "VALIDATOR"},
        "workstream_id": ws,
        "route_id": None,
        "route_node_id": "1.2",
        "execution_backend": "AGENT_TASK",
        "responsibility_result": preflight["responsibility_result"],
        "semantic_state_delta": {
            "activity_status": "WAITING",
            "hold_reason": {"type": "DEPENDENCY", "details": "Python runtime dependency preflight blocked before Agent start", "decision_id": None, "dependency_workstream_id": None, "required_artifact_set_id": None},
        },
        "artifact_updates": [],
        "decision_updates": [],
        "submission_updates": [],
        "route_progression": {"action": "KEEP"},
        "allowed_management_paths": ["00_project_records/**", "00_project_state/**"],
        "timestamp": STAMP,
    }
    req_path = project / "commit_request.yaml"
    dump_yaml(req_path, request)
    proc = subprocess.run([sys.executable, str(R4), "--project-root", str(project), "--skill-root", str(REPO_ROOT), "--request", str(req_path)], text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    assert proc.returncode == 0, receipt
    state = yaml.safe_load((project / f"00_project_state/workstreams/{ws}.yaml").read_text())
    assert state["activity_status"] == "WAITING"
    assert state["hold_reason"]["type"] == "DEPENDENCY"
    result_path = project / f"00_project_records/workstreams/{ws}/tasks/{task_id}/result.yaml"
    result_obj = yaml.safe_load(result_path.read_text())
    assert result_obj["validation_result"]["outcome_code"] == "MISSING_RUNTIME_DEPENDENCY"

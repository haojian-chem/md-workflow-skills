import json
from pathlib import Path
import subprocess
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = REPO_ROOT / "05_tools/runtime_task_builder/build_task.py"
SOURCE_TOOL = REPO_ROOT / "05_tools/source_recognition_deterministic/run.py"


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def pdb(path: Path, residue="ALA"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"HEADER    FIXTURE\nATOM      1  CA  {residue} A   1       0.000   0.000   0.000\nEND\n",
        encoding="utf-8",
    )
    return path


def route(root: Path):
    ws = "ws_0001_test"
    path = root / f"00_project_records/workstreams/{ws}/routes/route_0001.yaml"
    dump(path, {
        "schema_version": 3,
        "route_id": "route_0001",
        "workstream_id": ws,
        "created_at": "2026-08-10T00:00:00+00:00",
        "created_by": "MANAGER",
        "supersedes": None,
        "planning_status": "COMPLETE",
        "scope_resolution": {"source": "USER_REQUEST", "resolved_event_id": "evt_scope", "decision_id": None},
        "scope": {
            "start": {"workflow_name": "structure_preparation_workflow", "substep": "source_recognition", "artifact_set_id": None, "point_kind": "SPECIFIC_SUBSTEP"},
            "end": {"workflow_name": "structure_preparation_workflow", "substep": "component_and_residue_classification", "artifact_set_id": None, "point_kind": "SPECIFIC_SUBSTEP"},
        },
        "source_fragments": [],
        "steps": [{
            "sequence": 1,
            "workflow_name": "structure_preparation_workflow",
            "step_id": "source_recognition",
            "task_name": "source_recognition",
            "task_unit_mode": "OPERATION",
            "operation": {"skill_name": "source_recognition", "skill_path": "02_operations/source_recognition"},
            "validator": None,
            "necessity": "REQUIRED",
            "condition": None,
            "work_directory": "01_structure_preparation/01_source_recognition",
            "prerequisites": [],
            "expected_outputs": ["STRUCTURE"],
            "gate_requirements": ["DONE"],
        }],
        "change_reason": ["fixture"],
        "assumptions": [],
        "conditional_steps": [],
        "known_blockers": [],
        "stop_conditions": [],
    })
    return path


def run_builder(root: Path, route_path: Path, sources):
    cmd = [sys.executable, str(BUILDER), "--project-root", str(root), "--route", str(route_path)]
    for src in sources:
        cmd += ["--source", str(src)]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_unique_source_builds_schema_valid_task(tmp_path):
    src = pdb(tmp_path / "input.pdb")
    route_path = route(tmp_path)
    code, out = run_builder(tmp_path, route_path, [src])
    assert code == 0 and out["status"] == "PASS"
    task = yaml.safe_load(Path(out["task_path"]).read_text())
    assert task["task_unit"]["operation"]["skill_name"] == "source_recognition"
    assert task["current_valid_files"][0]["role"] == "source_candidate"
    assert task["current_valid_files"][0]["path"] == "input.pdb"
    assert task["permissions"]["allowed_read_paths"] == ["input.pdb"]
    assert out["validation_status"] == "PASS"


def test_multiple_candidates_are_packaged_without_agent_decision(tmp_path):
    a = pdb(tmp_path / "a.pdb", "ALA")
    b = pdb(tmp_path / "b.pdb", "GLY")
    route_path = route(tmp_path)
    code, out = run_builder(tmp_path, route_path, [a, b])
    assert code == 0
    task = yaml.safe_load(Path(out["task_path"]).read_text())
    assert len(task["current_valid_files"]) == 2
    assert all(x["role"] == "source_candidate" for x in task["current_valid_files"])


def test_builder_to_source_tool_unique_path(tmp_path):
    src = pdb(tmp_path / "input.pdb")
    route_path = route(tmp_path)
    code, out = run_builder(tmp_path, route_path, [src])
    assert code == 0
    proc = subprocess.run([sys.executable, str(SOURCE_TOOL), "--task", out["task_path"]], text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    result = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert result["status"] == "DONE"
    assert (tmp_path / "01_structure_preparation/01_source_recognition/input.pdb").is_file()


def test_builder_to_source_tool_multiple_candidates_blocks_without_agent(tmp_path):
    a = pdb(tmp_path / "a.pdb", "ALA")
    b = pdb(tmp_path / "b.pdb", "GLY")
    route_path = route(tmp_path)
    code, out = run_builder(tmp_path, route_path, [a, b])
    assert code == 0
    proc = subprocess.run([sys.executable, str(SOURCE_TOOL), "--task", out["task_path"]], text=True, capture_output=True)
    result = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert result["status"] == "BLOCKED"
    assert result["confirmation_items"][0]["category"] == "SOURCE_SELECTION"


def test_source_outside_project_is_rejected(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    route_path = route(project)
    outside = pdb(tmp_path / "outside.pdb")
    code, out = run_builder(project, route_path, [outside])
    assert code == 2
    assert out["status"] == "ERROR"
    assert "escapes project root" in out["error"]

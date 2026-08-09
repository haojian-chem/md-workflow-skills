import json
from pathlib import Path
import subprocess
import sys

import yaml

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "05_tools/runtime_project_initializer/initialize.py"
VALIDATOR = REPO / "05_tools/runtime_schema_validator/validate.py"


def run(root: Path):
    proc = subprocess.run([sys.executable, str(TOOL), "--project-root", str(root)], text=True, capture_output=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_fresh_project_initializes_without_business_parsing(tmp_path):
    bad = tmp_path / "raw_input.pdb"
    bad.write_bytes(b"not-a-pdb\x00\xff" * 1000)
    before = bad.read_bytes()
    code, out = run(tmp_path)
    assert code == 0 and out["status"] == "INITIALIZED"
    assert bad.read_bytes() == before
    project = yaml.safe_load((tmp_path / "00_project_state/project_state.yaml").read_text())
    ws = yaml.safe_load((tmp_path / out["workstream_state_path"]).read_text())
    assert project["entry_state"] == "RESUMABLE"
    assert ws["activity_status"] == "IDLE"
    assert ws["active_route_id"] is None
    events = [json.loads(x) for x in (tmp_path / "00_project_records/events/project_events.jsonl").read_text().splitlines()]
    assert [x["event_type"] for x in events] == ["ENTRY_STATE_EVALUATED", "PROJECT_INITIALIZED"]


def test_existing_project_state_blocks_without_overwrite(tmp_path):
    target = tmp_path / "00_project_state/project_state.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("sentinel: true\n")
    before = target.read_bytes()
    code, out = run(tmp_path)
    assert code == 0 and out["status"] == "BLOCKED"
    assert target.read_bytes() == before


def test_final_runtime_objects_validate(tmp_path):
    code, out = run(tmp_path)
    assert code == 0
    project = tmp_path / out["project_state_path"]
    ws = tmp_path / out["workstream_state_path"]
    events = tmp_path / out["event_log_path"]
    proc = subprocess.run([
        sys.executable, str(VALIDATOR), "--project-root", str(tmp_path),
        "--contracts-dir", str(REPO / "03_contracts"), "--mode", "FAST",
        "--changed", str(project), str(ws), str(events)
    ], text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"


def test_initializer_does_not_create_route_task_or_snapshot(tmp_path):
    code, out = run(tmp_path)
    assert code == 0
    assert not list(tmp_path.glob("00_project_records/workstreams/**/routes/*.yaml"))
    assert not list(tmp_path.glob("00_project_records/workstreams/**/tasks/**/task.yaml"))
    assert not list(tmp_path.glob("00_project_records/state_snapshots/**"))

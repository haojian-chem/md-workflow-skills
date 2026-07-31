from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_chain_and_component_selection import (  # noqa: E402
    prepare_case,
    run_script,
    sha256,
    write_yaml,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SELECT_SCRIPT = REPO_ROOT / "02_operations/chain_and_component_selection/scripts/select_structure.py"
VALIDATE_SCRIPT = REPO_ROOT / "02_validators/chain_and_component_selection_validator/scripts/validate_selection.py"
BUILDER = REPO_ROOT / "02_operations/chain_and_component_selection/scripts/build_subagent_result.py"
RUNTIME_VALIDATOR = REPO_ROOT / "05_tools/runtime_schema_validator/validate.py"
CONTRACTS = REPO_ROOT / "03_contracts"

TASK_ID = "selection-task-1"
WORKSTREAM_ID = "structure-preparation"
SOURCE_ARTIFACT_ID = "artifact-structure-source"
SELECTED_ARTIFACT_ID = "artifact-structure-selected"
START_EVENT_ID = "event-selection-started"
DONE_EVENT_ID = "event-selection-done"
START_TIME = "2026-07-31T02:00:00+00:00"
DONE_TIME = "2026-07-31T02:01:00+00:00"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def file_identity(path: Path, role: str | None = None) -> dict:
    stat = path.stat()
    output = {
        "path": str(path.resolve()),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": digest(path),
    }
    if role is not None:
        output["role"] = role
    return output


def task_document(project_root: Path, work_directory: Path, case: dict[str, Path], result_path: Path) -> dict:
    return {
        "schema_version": 2,
        "task_id": TASK_ID,
        "workstream_id": WORKSTREAM_ID,
        "workflow_name": "structure_preparation_workflow",
        "route_id": None,
        "sequence": 3,
        "task_unit": {
            "mode": "OPERATION_WITH_VALIDATOR",
            "operation": {
                "skill_name": "chain_and_component_selection",
                "skill_path": "02_operations/chain_and_component_selection",
                "skill_layer": "operation",
            },
            "validator": {
                "skill_name": "chain_and_component_selection_validator",
                "skill_path": "02_validators/chain_and_component_selection_validator",
                "skill_layer": "validator",
            },
        },
        "project_root": str(project_root),
        "work_directory": str(work_directory),
        "permissions": {
            "allowed_read_paths": [str(case["source"]), str(case["classification"]), str(work_directory)],
            "allowed_write_paths": [str(work_directory)],
            "forbidden_paths": [
                str(project_root / "00_project_state"),
                str(project_root / "00_project_records"),
            ],
        },
        "current_valid_files": [
            {
                "path": str(case["source"]),
                "state": "present_validated",
                "role": "source_structure",
                "artifact_set_id": SOURCE_ARTIFACT_ID,
                "sha256": sha256(case["source"]),
            },
            {
                "path": str(case["classification"]),
                "state": "present_validated",
                "role": "classification_result",
                "sha256": sha256(case["classification"]),
            },
        ],
        "upstream_summary": "v1.2 classification complete; explicit component selection recorded.",
        "user_decisions": [{"decision_id": "decision-1", "summary": "Retain polymer and covalently linked ligand."}],
        "required_outputs": [
            str(case["output"]),
            str(case["manifest"]),
            str(case["mapping"]),
            str(result_path),
        ],
        "detail_output_paths": {
            "log_file": None,
            "report_file": str(case["validation_report"]),
            "result_data_file": str(result_path),
        },
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }


def workstream_state(*, terminal: bool) -> dict:
    return {
        "schema_version": 1,
        "workstream_id": WORKSTREAM_ID,
        "title": "Structure preparation",
        "purpose": "Prepare a validated selected structure",
        "origin": {
            "parent_workstream_id": None,
            "fork_reason": None,
            "forked_from_artifact_set_ids": [],
        },
        "current_position": {
            "workflow_name": "structure_preparation_workflow",
            "substep": "1.4 altloc_occupancy_resolution" if terminal else "1.3 chain_and_component_selection",
            "task_id": None if terminal else TASK_ID,
        },
        "lifecycle_status": "OPEN",
        "activity_status": "READY" if terminal else "EXECUTING",
        "hold_reason": {
            "type": "NONE",
            "details": None,
            "decision_id": None,
            "dependency_workstream_id": None,
            "required_artifact_set_id": None,
        },
        "active_route_id": None,
        "active_task_id": None if terminal else TASK_ID,
        "current_artifact_set_ids": {
            "structure": [SELECTED_ARTIFACT_ID] if terminal else [SOURCE_ARTIFACT_ID],
            "topology": [],
            "system": [],
            "md_input": [],
            "md_output": [],
            "analysis_result": [],
        },
        "pending_decision_ids": [],
        "active_submission_ids": [],
        "last_event_id": DONE_EVENT_ID if terminal else START_EVENT_ID,
        "last_updated_by": "md_workflow_manager",
        "last_updated_at": DONE_TIME if terminal else START_TIME,
    }


def event(event_id: str, event_type: str, timestamp: str, summary: str, record_paths: list[str]) -> dict:
    return {
        "schema_version": 1,
        "event_id": event_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "scope": "WORKSTREAM",
        "workstream_id": WORKSTREAM_ID,
        "actor": "MANAGER",
        "object_type": "task",
        "object_id": TASK_ID,
        "summary": summary,
        "previous_state": None if event_type == "TASK_STARTED" else {"substep": "1.3 chain_and_component_selection", "task_id": TASK_ID},
        "new_state": {"substep": "1.3 chain_and_component_selection", "task_id": TASK_ID} if event_type == "TASK_STARTED" else {"substep": "1.4 altloc_occupancy_resolution", "task_id": None},
        "record_paths": record_paths,
        "related_event_ids": [] if event_type == "TASK_STARTED" else [START_EVENT_ID],
    }


def source_artifact(case: dict[str, Path]) -> dict:
    return {
        "schema_version": 1,
        "artifact_set_id": SOURCE_ARTIFACT_ID,
        "artifact_type": "STRUCTURE",
        "workstream_id": WORKSTREAM_ID,
        "created_at": START_TIME,
        "created_by_task_id": None,
        "derived_from_artifact_set_ids": [],
        "files": [file_identity(case["source"], "source_structure")],
        "validation_status": "VALIDATED",
        "validator_task_id": TASK_ID,
        "supersedes": [],
        "notes": "validated source fixture for selection closure test",
    }


def selected_artifact(case: dict[str, Path]) -> dict:
    return {
        "schema_version": 1,
        "artifact_set_id": SELECTED_ARTIFACT_ID,
        "artifact_type": "STRUCTURE",
        "workstream_id": WORKSTREAM_ID,
        "created_at": DONE_TIME,
        "created_by_task_id": TASK_ID,
        "derived_from_artifact_set_ids": [SOURCE_ARTIFACT_ID],
        "files": [file_identity(case["output"], "selected_structure")],
        "validation_status": "VALIDATED",
        "validator_task_id": TASK_ID,
        "supersedes": [],
        "notes": "validated chain/component selection output",
    }


def management_snapshot(project_root: Path) -> dict[str, str]:
    output: dict[str, str] = {}
    for directory in ("00_project_state", "00_project_records"):
        root = project_root / directory
        if root.exists():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    output[str(path.relative_to(project_root))] = digest(path)
    return output


def atomic_commit(candidate: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(candidate, destination)


def test_manager_fast_validation_atomic_artifact_registration_and_closure(tmp_path: Path) -> None:
    project_root = tmp_path / "md_project"
    work_directory = project_root / "01_structure_preparation/03_chain_and_component_selection"
    work_directory.mkdir(parents=True)
    case = prepare_case(work_directory, output_format="MMCIF")

    task_directory = project_root / "00_project_records/workstreams" / WORKSTREAM_ID / "tasks" / TASK_ID
    task_path = task_directory / "task.yaml"
    result_logical_path = task_directory / "result.yaml"
    artifact_directory = project_root / "00_project_records/workstreams" / WORKSTREAM_ID / "artifacts"
    source_artifact_path = artifact_directory / f"{SOURCE_ARTIFACT_ID}.yaml"
    artifact_logical_path = artifact_directory / f"{SELECTED_ARTIFACT_ID}.yaml"
    state_logical_path = project_root / "00_project_state/workstreams" / f"{WORKSTREAM_ID}.yaml"
    events_logical_path = project_root / "00_project_records/events/project_events.jsonl"

    task_directory.mkdir(parents=True, exist_ok=True)
    artifact_directory.mkdir(parents=True, exist_ok=True)
    state_logical_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(task_path, task_document(project_root, work_directory, case, result_logical_path))
    write_yaml(source_artifact_path, source_artifact(case))
    write_yaml(state_logical_path, workstream_state(terminal=False))
    write_jsonl(
        events_logical_path,
        [event(START_EVENT_ID, "TASK_STARTED", START_TIME, "Selection task started.", [str(task_path.relative_to(project_root))])],
    )

    assert run_script(SELECT_SCRIPT, case["operation_config"]).returncode == 0
    assert run_script(VALIDATE_SCRIPT, case["validator_config"]).returncode == 0
    before_wrapper = management_snapshot(project_root)
    result_candidate = work_directory / "subagent_result.candidate.yaml"
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--task", str(task_path),
            "--candidate", str(case["output"]),
            "--manifest", str(case["manifest"]),
            "--mapping", str(case["mapping"]),
            "--operation-report", str(case["operation_report"]),
            "--validation-report", str(case["validation_report"]),
            "--validation-result", str(case["validation_result"]),
            "--output", str(result_candidate),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert management_snapshot(project_root) == before_wrapper

    candidate_root = project_root / ".manager_candidates/selection_closure"
    artifact_candidate = candidate_root / "artifact.yaml"
    state_candidate = candidate_root / "workstream_state.yaml"
    events_candidate = candidate_root / "project_events.jsonl"
    write_yaml(artifact_candidate, selected_artifact(case))
    write_yaml(state_candidate, workstream_state(terminal=True))
    write_jsonl(
        events_candidate,
        [
            event(START_EVENT_ID, "TASK_STARTED", START_TIME, "Selection task started.", [str(task_path.relative_to(project_root))]),
            event(
                DONE_EVENT_ID,
                "TASK_DONE",
                DONE_TIME,
                "Chain/component selection and dedicated validation completed; STRUCTURE artifact registered.",
                [
                    str(result_logical_path.relative_to(project_root)),
                    str(artifact_logical_path.relative_to(project_root)),
                    str(state_logical_path.relative_to(project_root)),
                ],
            ),
        ],
    )

    fast_output = candidate_root / "fast_validation.json"
    fast = subprocess.run(
        [
            sys.executable,
            str(RUNTIME_VALIDATOR),
            "--project-root", str(project_root),
            "--contracts-dir", str(CONTRACTS),
            "--cache-dir", str(project_root / ".md_workflow_cache/runtime_schema_validator"),
            "--mode", "FAST",
            "--changed", str(result_candidate), str(artifact_candidate), str(state_candidate), str(events_candidate),
            "--logical-map", f"{result_candidate}={result_logical_path.relative_to(project_root)}",
            "--logical-map", f"{artifact_candidate}={artifact_logical_path.relative_to(project_root)}",
            "--logical-map", f"{state_candidate}={state_logical_path.relative_to(project_root)}",
            "--logical-map", f"{events_candidate}={events_logical_path.relative_to(project_root)}",
            "--output", str(fast_output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert fast.returncode == 0, fast.stdout + fast.stderr
    fast_document = json.loads(fast_output.read_text(encoding="utf-8"))
    assert fast_document["status"] == "PASS"
    assert fast_document["errors"] == []
    assert len(fast_document["validated"]) == 4

    atomic_commit(result_candidate, result_logical_path)
    atomic_commit(artifact_candidate, artifact_logical_path)
    atomic_commit(state_candidate, state_logical_path)
    atomic_commit(events_candidate, events_logical_path)

    committed_result = yaml.safe_load(result_logical_path.read_text(encoding="utf-8"))
    committed_artifact = yaml.safe_load(artifact_logical_path.read_text(encoding="utf-8"))
    committed_state = yaml.safe_load(state_logical_path.read_text(encoding="utf-8"))
    committed_events = [json.loads(line) for line in events_logical_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert committed_result["status"] == "DONE"
    assert committed_result["artifact_candidates"][0]["files"][0]["state"] == "present_validated"
    assert committed_artifact["validation_status"] == "VALIDATED"
    assert committed_artifact["files"][0]["sha256"] == sha256(case["output"])
    assert committed_state["active_task_id"] is None
    assert committed_state["activity_status"] == "READY"
    assert committed_state["current_position"] == {
        "workflow_name": "structure_preparation_workflow",
        "substep": "1.4 altloc_occupancy_resolution",
        "task_id": None,
    }
    assert committed_state["current_artifact_set_ids"]["structure"] == [SELECTED_ARTIFACT_ID]
    assert committed_state["last_event_id"] == DONE_EVENT_ID
    assert committed_events[-1]["event_type"] == "TASK_DONE"
    assert committed_events[-1]["record_paths"] == [
        str(result_logical_path.relative_to(project_root)),
        str(artifact_logical_path.relative_to(project_root)),
        str(state_logical_path.relative_to(project_root)),
    ]

    validation_outcome = committed_result["validation_result"]["outcome_code"]
    closure = (
        "Task result:\n"
        "1.3 chain_and_component_selection — DONE\n\n"
        "Checks:\n"
        f"Validator outcome {validation_outcome}; FAST runtime validation passed\n\n"
        "Action / Output:\n"
        f"{case['output']}, {case['manifest']}, {case['mapping']}\n\n"
        "Artifact status:\n"
        f"{SELECTED_ARTIFACT_ID} — VALIDATED\n\n"
        "Warnings:\n"
        "none\n\n"
        "Report:\n"
        f"{case['validation_report']}\n\n"
        "Next:\n"
        "1.4 altloc_occupancy_resolution"
    )
    for heading in ("Task result:", "Checks:", "Action / Output:", "Artifact status:", "Warnings:", "Report:", "Next:"):
        assert heading in closure
    assert "1.3 chain_and_component_selection — DONE" in closure
    assert "SELECTION_VALIDATED" in closure
    assert "FAST runtime validation passed" in closure
    assert f"{SELECTED_ARTIFACT_ID} — VALIDATED" in closure
    assert closure.endswith("1.4 altloc_occupancy_resolution")

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
WRAPPER = SKILL_ROOT / "scripts/build_subagent_result.py"
RUNTIME_VALIDATOR = REPO_ROOT / "05_tools/runtime_schema_validator/validate.py"
CONTRACTS = REPO_ROOT / "03_contracts"

TASK_ID = "task_ws_0001_0002_component_classification"
WORKSTREAM_ID = "ws_0001_main"
ROUTE_ID = "route_ws_0001_r001"
SCOPE_EVENT_ID = "evt_ws_0001_scope_resolved"
TERMINAL_EVENT_ID = "evt_ws_0001_task_0002_done"
TIMESTAMP = "2026-07-28T00:00:00+00:00"


def write_yaml(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path, role: str) -> dict:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "state": "present_validated",
        "role": role,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": digest(path),
    }


def management_snapshot(project_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for directory in ("00_project_state", "00_project_records"):
        root = project_root / directory
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                result[str(path.relative_to(project_root))] = digest(path)
    return result


def route_document(work_directory: Path) -> dict:
    return {
        "schema_version": 3,
        "route_id": ROUTE_ID,
        "workstream_id": WORKSTREAM_ID,
        "created_at": TIMESTAMP,
        "created_by": "MANAGER",
        "supersedes": None,
        "planning_status": "COMPLETE",
        "scope_resolution": {
            "source": "USER_REQUEST",
            "resolved_event_id": SCOPE_EVENT_ID,
            "decision_id": None,
        },
        "scope": {
            "start": {
                "workflow_name": "structure_preparation_workflow",
                "substep": "1.2 component_and_residue_classification",
                "artifact_set_id": None,
                "point_kind": "SPECIFIC_SUBSTEP",
            },
            "end": {
                "workflow_name": "structure_preparation_workflow",
                "substep": "1.3 chain_and_component_selection",
                "artifact_set_id": None,
                "point_kind": "SPECIFIC_SUBSTEP",
            },
        },
        "source_fragments": [
            {
                "fragment_id": "fragment_structure_preparation_001",
                "workflow_name": "structure_preparation_workflow",
                "workflow_path": "01_workflows/structure_preparation_workflow/SKILL.md",
                "workflow_revision": None,
                "fragment_status": "COMPLETE",
            }
        ],
        "steps": [
            {
                "sequence": 1,
                "workflow_name": "structure_preparation_workflow",
                "step_id": "1.2",
                "task_name": "component_and_residue_classification",
                "task_unit_mode": "VALIDATOR",
                "operation": None,
                "validator": {
                    "skill_name": "component_and_residue_classification_validator",
                    "skill_path": "02_validators/component_and_residue_classification_validator",
                },
                "necessity": "REQUIRED",
                "condition": None,
                "work_directory": str(work_directory),
                "prerequisites": ["source recognition completed"],
                "expected_outputs": ["classification_result.yaml"],
                "gate_requirements": ["classification result integrated"],
            },
            {
                "sequence": 2,
                "workflow_name": "structure_preparation_workflow",
                "step_id": "1.3",
                "task_name": "chain_and_component_selection",
                "task_unit_mode": "OPERATION_WITH_VALIDATOR",
                "operation": {
                    "skill_name": "chain_and_component_selection",
                    "skill_path": "02_operations/chain_and_component_selection",
                },
                "validator": {
                    "skill_name": "chain_and_component_selection_validator",
                    "skill_path": "02_validators/chain_and_component_selection_validator",
                },
                "necessity": "REQUIRED",
                "condition": None,
                "work_directory": str(work_directory.parent / "03_chain_and_component_selection"),
                "prerequisites": ["component classification completed"],
                "expected_outputs": ["selected_structure"],
                "gate_requirements": ["selection fidelity validated"],
            },
        ],
        "change_reason": ["initial user-authorized structure-preparation route"],
        "assumptions": [],
        "conditional_steps": [],
        "known_blockers": [],
        "stop_conditions": ["stop after 1.3 closure"],
    }


def task_document(project_root: Path, work_directory: Path, structure: Path) -> dict:
    report = work_directory / "classification_report.md"
    result_data = work_directory / "classification_result.yaml"
    return {
        "schema_version": 2,
        "task_id": TASK_ID,
        "workstream_id": WORKSTREAM_ID,
        "workflow_name": "structure_preparation_workflow",
        "route_id": ROUTE_ID,
        "sequence": 2,
        "task_unit": {
            "mode": "VALIDATOR",
            "operation": None,
            "validator": {
                "skill_name": "component_and_residue_classification_validator",
                "skill_path": "02_validators/component_and_residue_classification_validator",
                "skill_layer": "validator",
            },
        },
        "project_root": str(project_root),
        "work_directory": str(work_directory),
        "permissions": {
            "allowed_read_paths": [str(structure), str(work_directory)],
            "allowed_write_paths": [str(work_directory)],
            "forbidden_paths": [
                str(project_root / "00_project_state"),
                str(project_root / "00_project_records"),
            ],
        },
        "current_valid_files": [file_record(structure, "recognized_structure")],
        "upstream_summary": "source recognition completed and input structure validated",
        "user_decisions": [],
        "required_outputs": [
            "classification_result.yaml",
            "classification_report.md",
            "confirmation_requests.yaml",
        ],
        "detail_output_paths": {
            "log_file": None,
            "report_file": str(report),
            "result_data_file": str(result_data),
        },
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }


def classification_result() -> dict:
    return {
        "schema_version": "1.0",
        "result_status": "COMPLETE",
        "selected_model_id": "1",
        "classification_mode": "REGISTRY",
        "source_structure": {
            "path": "/fixtures/source.pdb",
            "sha256": "6" * 64,
            "source_format": "PDB",
        },
        "source_hashes": {
            "model_scope": "0" * 64,
            "classification_observations": "1" * 64,
            "reference_manifest": "2" * 64,
            "possible_connections_result": "3" * 64,
            "possible_coordination_result": "4" * 64,
            "confirmation_requests": "5" * 64,
        },
        "chain_groups": [],
        "residue_records": [],
        "confirmed_relations": {
            "covalent_connections": [],
            "metal_coordination": [],
        },
        "rejected_candidates": {
            "covalent_connections": [],
            "metal_coordination": [],
        },
        "unresolved_items": [],
        "summary": {
            "chain_group_count": 0,
            "standard_residue_count": 0,
            "topology_linked_nonstandard_count": 0,
            "independent_nonstandard_count": 0,
            "solvent_component_count": 0,
            "ion_component_count": 0,
            "multiple_conformation_residue_count": 0,
            "missing_residue_count": 0,
            "heavy_atom_issue_count": 0,
            "unresolved_item_count": 0,
        },
    }


def initial_workstream_state() -> dict:
    return {
        "schema_version": 1,
        "workstream_id": WORKSTREAM_ID,
        "title": "Main structure preparation",
        "purpose": "Prepare and validate the selected molecular structure",
        "origin": {
            "parent_workstream_id": None,
            "fork_reason": None,
            "forked_from_artifact_set_ids": [],
        },
        "current_position": {
            "workflow_name": "structure_preparation_workflow",
            "substep": "1.2 component_and_residue_classification",
            "task_id": TASK_ID,
        },
        "lifecycle_status": "OPEN",
        "activity_status": "READY",
        "hold_reason": {
            "type": "NONE",
            "details": None,
            "decision_id": None,
            "dependency_workstream_id": None,
            "required_artifact_set_id": None,
        },
        "active_route_id": ROUTE_ID,
        "active_task_id": None,
        "current_artifact_set_ids": {
            "structure": [],
            "topology": [],
            "system": [],
            "md_input": [],
            "md_output": [],
            "analysis_result": [],
        },
        "pending_decision_ids": [],
        "active_submission_ids": [],
        "last_event_id": SCOPE_EVENT_ID,
        "last_updated_by": "md_workflow_manager",
        "last_updated_at": TIMESTAMP,
    }


def terminal_workstream_state() -> dict:
    document = initial_workstream_state()
    document["current_position"] = {
        "workflow_name": "structure_preparation_workflow",
        "substep": "1.3 chain_and_component_selection",
        "task_id": None,
    }
    document["activity_status"] = "READY"
    document["active_task_id"] = None
    document["last_event_id"] = TERMINAL_EVENT_ID
    document["last_updated_at"] = "2026-07-28T00:01:00+00:00"
    return document


def scope_event() -> dict:
    return {
        "schema_version": 1,
        "event_id": SCOPE_EVENT_ID,
        "timestamp": TIMESTAMP,
        "event_type": "ROUTE_SCOPE_RESOLVED",
        "scope": "WORKSTREAM",
        "workstream_id": WORKSTREAM_ID,
        "actor": "MANAGER",
        "object_type": "route",
        "object_id": ROUTE_ID,
        "summary": "User-authorized route scope resolved through substep 1.3.",
        "previous_state": None,
        "new_state": {"route_id": ROUTE_ID},
        "record_paths": [
            f"00_project_records/workstreams/{WORKSTREAM_ID}/routes/{ROUTE_ID}.yaml"
        ],
        "related_event_ids": [],
    }


def terminal_event(result_logical_path: Path, state_logical_path: Path) -> dict:
    return {
        "schema_version": 1,
        "event_id": TERMINAL_EVENT_ID,
        "timestamp": "2026-07-28T00:01:00+00:00",
        "event_type": "TASK_DONE",
        "scope": "WORKSTREAM",
        "workstream_id": WORKSTREAM_ID,
        "actor": "MANAGER",
        "object_type": "task",
        "object_id": TASK_ID,
        "summary": "Component and residue classification Validator completed and FAST validation passed.",
        "previous_state": {
            "substep": "1.2 component_and_residue_classification",
            "task_id": TASK_ID,
        },
        "new_state": {
            "substep": "1.3 chain_and_component_selection",
            "task_id": None,
        },
        "record_paths": [
            str(result_logical_path),
            str(state_logical_path),
        ],
        "related_event_ids": [SCOPE_EVENT_ID],
    }


def render_closure(result: dict, report_path: Path) -> str:
    validation = result["validation_result"]
    warnings = validation["warnings"] or result["warnings"]
    warning_text = "none" if not warnings else "; ".join(item["message"] for item in warnings)
    return (
        "Task result:\n"
        "1.2 component_and_residue_classification — DONE\n\n"
        "Checks:\n"
        f"Validator outcome {validation['outcome_code']}; FAST runtime validation passed\n\n"
        "Action / Output:\n"
        "classification_result.yaml, confirmation_requests.yaml, classification_report.md\n\n"
        "Artifact status:\n"
        "none\n\n"
        "Warnings:\n"
        f"{warning_text}\n\n"
        "Report:\n"
        f"{report_path}\n\n"
        "Next:\n"
        "1.3 chain_and_component_selection"
    )


def atomic_commit(candidate: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(candidate, destination)


def test_manager_task_wrapper_fast_validation_and_closure(tmp_path: Path) -> None:
    project_root = tmp_path / "md_project"
    work_directory = project_root / "01_structure_preparation/02_component_and_residue_classification"
    work_directory.mkdir(parents=True)
    structure = project_root / "01_structure_preparation/01_source_recognition/input.pdb"
    structure.parent.mkdir(parents=True)
    structure.write_text(
        "ATOM      1  CA  GLY A   1       0.000   0.000   0.000  1.00 20.00           C\nEND\n",
        encoding="utf-8",
    )

    task_directory = (
        project_root
        / "00_project_records/workstreams"
        / WORKSTREAM_ID
        / "tasks"
        / TASK_ID
    )
    task_path = task_directory / "task.yaml"
    result_logical_path = task_directory / "result.yaml"
    route_path = (
        project_root
        / "00_project_records/workstreams"
        / WORKSTREAM_ID
        / "routes"
        / f"{ROUTE_ID}.yaml"
    )
    state_logical_path = project_root / "00_project_state/workstreams" / f"{WORKSTREAM_ID}.yaml"
    events_logical_path = project_root / "00_project_records/events/project_events.jsonl"

    write_yaml(route_path, route_document(work_directory))
    write_yaml(task_path, task_document(project_root, work_directory, structure))
    write_yaml(state_logical_path, initial_workstream_state())
    write_jsonl(events_logical_path, [scope_event()])

    classification_result_path = work_directory / "classification_result.yaml"
    confirmations_path = work_directory / "confirmation_requests.yaml"
    report_path = work_directory / "classification_report.md"
    write_yaml(classification_result_path, classification_result())
    write_yaml(
        confirmations_path,
        {
            "schema_version": "1.0",
            "status": "NO_CONFIRMATION_REQUIRED",
            "requests": [],
        },
    )
    report_path.write_text("# Component and residue classification report\n", encoding="utf-8")

    management_before_wrapper = management_snapshot(project_root)
    result_candidate = work_directory / "subagent_result.candidate.yaml"
    wrapper = subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--task",
            str(task_path),
            "--classification-result",
            str(classification_result_path),
            "--confirmation-requests",
            str(confirmations_path),
            "--report",
            str(report_path),
            "--output",
            str(result_candidate),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert wrapper.returncode == 0, wrapper.stderr
    assert result_candidate.is_file()
    assert management_snapshot(project_root) == management_before_wrapper

    result_document = yaml.safe_load(result_candidate.read_text(encoding="utf-8"))
    assert result_document["status"] == "DONE"
    assert result_document["validation_result"]["outcome_code"] == "CLASSIFIED_CLEAR"
    assert result_document["confirmation_items"] == []
    assert result_document["artifact_candidates"] == []

    candidate_root = project_root / ".manager_candidates/task_0002_closure"
    state_candidate = candidate_root / "workstream_state.yaml"
    events_candidate = candidate_root / "project_events.jsonl"
    write_yaml(state_candidate, terminal_workstream_state())
    write_jsonl(
        events_candidate,
        [scope_event(), terminal_event(result_logical_path.relative_to(project_root), state_logical_path.relative_to(project_root))],
    )

    fast_output = candidate_root / "fast_validation.json"
    fast = subprocess.run(
        [
            sys.executable,
            str(RUNTIME_VALIDATOR),
            "--project-root",
            str(project_root),
            "--contracts-dir",
            str(CONTRACTS),
            "--cache-dir",
            str(project_root / ".md_workflow_cache/runtime_schema_validator"),
            "--mode",
            "FAST",
            "--changed",
            str(result_candidate),
            str(state_candidate),
            str(events_candidate),
            "--logical-map",
            f"{result_candidate}={result_logical_path.relative_to(project_root)}",
            "--logical-map",
            f"{state_candidate}={state_logical_path.relative_to(project_root)}",
            "--logical-map",
            f"{events_candidate}={events_logical_path.relative_to(project_root)}",
            "--output",
            str(fast_output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert fast.returncode == 0, fast.stdout + fast.stderr
    fast_document = json.loads(fast_output.read_text(encoding="utf-8"))
    assert fast_document["status"] == "PASS"
    assert fast_document["mode"] == "FAST"
    assert fast_document["errors"] == []
    assert len(fast_document["validated"]) == 3
    assert {
        Path(item["logical_path"]).resolve()
        for item in fast_document["validated"]
    } == {
        result_logical_path.resolve(),
        state_logical_path.resolve(),
        events_logical_path.resolve(),
    }

    atomic_commit(result_candidate, result_logical_path)
    atomic_commit(state_candidate, state_logical_path)
    atomic_commit(events_candidate, events_logical_path)

    assert result_logical_path.is_file()
    committed_result = yaml.safe_load(result_logical_path.read_text(encoding="utf-8"))
    committed_state = yaml.safe_load(state_logical_path.read_text(encoding="utf-8"))
    committed_events = [
        json.loads(line)
        for line in events_logical_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert committed_result["status"] == "DONE"
    assert committed_state["active_task_id"] is None
    assert committed_state["activity_status"] == "READY"
    assert committed_state["current_position"] == {
        "workflow_name": "structure_preparation_workflow",
        "substep": "1.3 chain_and_component_selection",
        "task_id": None,
    }
    assert committed_state["last_event_id"] == TERMINAL_EVENT_ID
    assert committed_events[-1]["event_type"] == "TASK_DONE"
    assert committed_events[-1]["object_id"] == TASK_ID
    assert committed_events[-1]["record_paths"] == [
        str(result_logical_path.relative_to(project_root)),
        str(state_logical_path.relative_to(project_root)),
    ]

    closure = render_closure(committed_result, report_path)
    for heading in (
        "Task result:",
        "Checks:",
        "Action / Output:",
        "Artifact status:",
        "Warnings:",
        "Report:",
        "Next:",
    ):
        assert heading in closure
    assert "1.2 component_and_residue_classification — DONE" in closure
    assert "CLASSIFIED_CLEAR" in closure
    assert "FAST runtime validation passed" in closure
    assert "Artifact status:\nnone" in closure
    assert str(report_path) in closure
    assert closure.endswith("1.3 chain_and_component_selection")

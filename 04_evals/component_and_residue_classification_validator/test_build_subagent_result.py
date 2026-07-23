from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
WRAPPER = SKILL_ROOT / "scripts/build_subagent_result.py"
RUNTIME_VALIDATOR = REPO_ROOT / "05_tools/runtime_schema_validator/validate.py"
CONTRACTS = REPO_ROOT / "03_contracts"
CLASSIFICATION_SCHEMA = SKILL_ROOT / "schemas/classification_outputs.schema.yaml"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("build_subagent_result", WRAPPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_wrapper()


def write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classification_payload(
    structure: Path,
    *,
    outcome: str = "CLASSIFIED_CLEAR",
    blocking: bool = False,
) -> dict:
    ambiguities = []
    if blocking:
        ambiguities.append(
            {
                "ambiguity_id": "ambiguity_0001",
                "blocking": True,
                "category": "COVALENT_LINKAGE",
                "question": "Is the geometry-only contact a covalent connection?",
                "reason": "The topology route would change but no explicit bond record exists.",
                "affected_object_ids": ["model:1/chain:A/res:LIG:101"],
                "options": [
                    "treat as covalently linked",
                    "treat as independent",
                    "provide corrected connectivity",
                ],
                "recommended_option": None,
            }
        )
    return {
        "schema_version": 1,
        "task_id": "task_0001",
        "workstream_id": "ws_0001",
        "input_structure": {
            "path": str(structure),
            "sha256": file_hash(structure),
            "format": "PDB",
        },
        "outcome_code": outcome,
        "summary": {
            "model_count": 1,
            "chain_count": 1,
            "component_count": 1,
            "residue_count": 1,
            "standard_residue_count": 1,
            "covalently_linked_nonstandard_count": 0,
            "independent_nonstandard_count": 0,
            "solvent_count": 0,
            "ion_count": 0,
            "unknown_count": 0,
            "blocking_ambiguity_count": 1 if blocking else 0,
        },
        "models": [
            {
                "model_id": "1",
                "chain_count": 1,
                "residue_count": 1,
                "atom_count": 1,
                "classification_signature": "0" * 64,
            }
        ],
        "chains": [
            {
                "model_id": "1",
                "chain_id": "A",
                "entity_id": "1",
                "polymer_class": "PROTEIN",
                "residue_count": 1,
                "standard_residue_count": 1,
                "nonstandard_residue_count": 0,
                "confidence": "HIGH",
                "evidence": ["synthetic test"],
            }
        ],
        "components": [
            {
                "component_id": "model:1/chain:A/polymer",
                "model_id": "1",
                "chain_ids": ["A"],
                "residue_ids": ["model:1/chain:A/res:ALA:1"],
                "polymer_class": "PROTEIN",
                "topology_class": "STANDARD_RESIDUE",
                "component_role": "POLYMER",
                "confidence": "HIGH",
                "evidence": ["synthetic test"],
                "decision_required": False,
            }
        ],
        "residues": [
            {
                "residue_id": "model:1/chain:A/res:ALA:1",
                "model_id": "1",
                "chain_id": "A",
                "entity_id": "1",
                "residue_name": "ALA",
                "residue_number": "1",
                "insertion_code": None,
                "atom_count": 1,
                "polymer_class": "PROTEIN",
                "topology_class": "STANDARD_RESIDUE",
                "component_role": "POLYMER",
                "canonical_parent": "ALA",
                "confidence": "HIGH",
                "evidence": ["synthetic test"],
                "decision_required": False,
            }
        ],
        "explicit_connections": [],
        "covalent_candidates": [],
        "coordination_candidates": [],
        "ambiguities": ambiguities,
        "warnings": [],
    }


def prepare_project(
    tmp_path: Path,
    *,
    outcome: str = "CLASSIFIED_CLEAR",
    blocking: bool = False,
) -> tuple[Path, Path, Path, Path]:
    project = tmp_path / "project"
    source = project / "01_structure_preparation/01_source_recognition/input.pdb"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N\nEND\n",
        encoding="utf-8",
    )
    work = project / "01_structure_preparation/02_component_and_residue_classification"
    work.mkdir(parents=True, exist_ok=True)
    report = work / "component_and_residue_classification_report.yaml"
    data = work / "classification_result.yaml"
    write_yaml(
        report,
        {
            "schema_version": 1,
            "skill_name": "component_and_residue_classification_validator",
            "classification": {"task_id": "task_0001"},
        },
    )
    write_yaml(data, classification_payload(source, outcome=outcome, blocking=blocking))

    task = {
        "schema_version": 2,
        "task_id": "task_0001",
        "workstream_id": "ws_0001",
        "workflow_name": "structure_preparation_workflow",
        "route_id": "route_0001",
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
        "project_root": str(project),
        "work_directory": str(work),
        "permissions": {
            "allowed_read_paths": [str(source)],
            "allowed_write_paths": [str(work)],
            "forbidden_paths": [
                str(project / "00_project_state/**"),
                str(project / "00_project_records/**"),
            ],
        },
        "current_valid_files": [
            {
                "path": str(source),
                "state": "present_unvalidated",
                "role": "source_recognition_output",
                "sha256": file_hash(source),
            }
        ],
        "upstream_summary": "source_recognition completed; STRUCTURE remains UNVALIDATED",
        "user_decisions": [],
        "required_outputs": [
            "component_and_residue_classification_report.yaml",
            "classification_result.yaml",
        ],
        "detail_output_paths": {
            "log_file": None,
            "report_file": str(report),
            "result_data_file": str(data),
        },
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }
    task_path = (
        project
        / "00_project_records/workstreams/ws_0001/tasks/task_0001/task.yaml"
    )
    write_yaml(task_path, task)
    return project, task_path, data, report


def test_clear_result_matches_shared_contract(tmp_path: Path) -> None:
    _, task, data, report = prepare_project(tmp_path)
    result = MODULE.build_result(task, data, report, CONTRACTS, CLASSIFICATION_SCHEMA)

    assert result["status"] == "DONE"
    assert result["task_unit_mode"] == "VALIDATOR"
    assert result["operation_result"] is None
    assert result["artifact_candidates"] == []
    assert result["confirmation_items"] == []
    assert result["validation_result"]["validated_files"][0]["state"] == "present_unvalidated"
    assert "1.3 chain_and_component_selection" in result["next_step_recommendation"]


def test_blocking_classification_decision_is_done_with_confirmation(tmp_path: Path) -> None:
    _, task, data, report = prepare_project(
        tmp_path,
        outcome="CLASSIFICATION_DECISION_REQUIRED",
        blocking=True,
    )
    result = MODULE.build_result(task, data, report, CONTRACTS, CLASSIFICATION_SCHEMA)

    assert result["status"] == "DONE"
    assert result["validation_result"]["outcome_code"] == "CLASSIFICATION_DECISION_REQUIRED"
    assert len(result["confirmation_items"]) == 1
    decision = result["confirmation_items"][0]
    assert decision["blocking"] is True
    assert decision["scope"] == "WORKSTREAM"
    assert decision["source_task_id"] == "task_0001"
    assert "暂停" in result["next_step_recommendation"]


def test_outcome_and_blocking_decisions_must_be_consistent(tmp_path: Path) -> None:
    _, task, data, report = prepare_project(tmp_path, blocking=True)
    with pytest.raises(MODULE.ResultBuildError, match="inconsistent"):
        MODULE.build_result(task, data, report, CONTRACTS, CLASSIFICATION_SCHEMA)


def test_wrapper_does_not_write_management_paths(tmp_path: Path) -> None:
    project, task, data, report = prepare_project(tmp_path)
    forbidden_output = project / "00_project_records/result.yaml"
    completed = subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--task",
            str(task),
            "--classification",
            str(data),
            "--report",
            str(report),
            "--contracts-dir",
            str(CONTRACTS),
            "--output",
            str(forbidden_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "forbidden paths" in completed.stderr
    assert not forbidden_output.exists()


def test_manager_candidate_passes_active_fast_validator(tmp_path: Path) -> None:
    project, task, data, report = prepare_project(tmp_path)
    result = MODULE.build_result(task, data, report, CONTRACTS, CLASSIFICATION_SCHEMA)
    candidate = project / ".manager_candidates/task_0001/result.yaml"
    write_yaml(candidate, result)
    logical = "00_project_records/workstreams/ws_0001/tasks/task_0001/result.yaml"

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNTIME_VALIDATOR),
            "--project-root",
            str(project),
            "--contracts-dir",
            str(CONTRACTS),
            "--mode",
            "FAST",
            "--changed",
            str(candidate),
            "--logical-map",
            f"{candidate}={logical}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "PASS"
    assert payload["mode"] == "FAST"
    assert any(item["logical_path"].endswith(logical) for item in payload["validated"])

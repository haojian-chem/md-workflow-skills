from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
WRAPPER = SKILL_ROOT / "scripts/build_subagent_result.py"
RELATION_ID = "relation:v1/type/METAL_COORDINATION/endpoints/" + "a" * 64


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def task_document(tmp_path: Path) -> dict:
    return {
        "schema_version": 2,
        "task_id": "task-classify-001",
        "workstream_id": "workstream-001",
        "workflow_name": "structure_preparation_workflow",
        "route_id": "route-001",
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
        "project_root": str(tmp_path),
        "work_directory": str(tmp_path),
        "permissions": {
            "allowed_read_paths": [str(tmp_path)],
            "allowed_write_paths": [str(tmp_path)],
            "forbidden_paths": [str(tmp_path / "00_project_state"), str(tmp_path / "00_project_records")],
        },
        "current_valid_files": [],
        "upstream_summary": "source recognition completed",
        "user_decisions": [],
        "required_outputs": ["classification_result.yaml", "classification_report.md", "confirmation_requests.yaml"],
        "detail_output_paths": {
            "log_file": None,
            "report_file": str(tmp_path / "classification_report.md"),
            "result_data_file": str(tmp_path / "classification_result.yaml"),
        },
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }


def classification_result(status: str, unresolved_count: int) -> dict:
    return {
        "schema_version": "1.0",
        "result_status": status,
        "selected_model_id": "1",
        "classification_mode": "REGISTRY",
        "source_structure": {"path": "/fixtures/source.pdb", "sha256": "6" * 64, "source_format": "PDB"},
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
        "confirmed_relations": {"covalent_connections": [], "metal_coordination": []},
        "rejected_candidates": {"covalent_connections": [], "metal_coordination": []},
        "unresolved_items": [
            {
                "request_index": 1,
                "request_type": "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
                "relation_id": RELATION_ID,
                "subject": {},
            }
        ] if unresolved_count else [],
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
            "unresolved_item_count": unresolved_count,
        },
    }


def run_wrapper(tmp_path: Path, result: dict, confirmations: dict) -> subprocess.CompletedProcess[str]:
    task_path = tmp_path / "task.yaml"
    result_path = tmp_path / "classification_result.yaml"
    confirmation_path = tmp_path / "confirmation_requests.yaml"
    report_path = tmp_path / "classification_report.md"
    output_path = tmp_path / "subagent_result.yaml"
    write_yaml(task_path, task_document(tmp_path))
    write_yaml(result_path, result)
    write_yaml(confirmation_path, confirmations)
    report_path.write_text("# Classification report\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(WRAPPER), "--task", str(task_path), "--classification-result", str(result_path), "--confirmation-requests", str(confirmation_path), "--report", str(report_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_wrapper_builds_clear_validator_result(tmp_path: Path) -> None:
    completed = run_wrapper(
        tmp_path,
        classification_result("COMPLETE", 0),
        {"schema_version": "1.0", "status": "NO_CONFIRMATION_REQUIRED", "requests": []},
    )
    assert completed.returncode == 0, completed.stderr
    output = yaml.safe_load((tmp_path / "subagent_result.yaml").read_text(encoding="utf-8"))
    assert output["status"] == "DONE"
    assert output["validation_result"]["outcome_code"] == "CLASSIFIED_CLEAR"
    assert output["confirmation_items"] == []


def test_wrapper_converts_relation_request_to_blocking_confirmation_item(tmp_path: Path) -> None:
    request = {
        "request_index": 1,
        "request_type": "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
        "relation_id": RELATION_ID,
        "subject": {
            "metal": {"chain_index": 2, "source_chain_id": "B", "source_resid": {"number": "501", "insertion_code": None}, "residue_name": "HEM", "atom_name": "FE"},
            "donor": {"chain_index": 1, "source_chain_id": "A", "source_resid": {"number": "42", "insertion_code": None}, "residue_name": "CYS", "atom_name": "SG"},
        },
        "evidence": {"distance_angstrom": 2.3},
        "reason": "geometry supports a coordination candidate",
        "allowed_decisions": ["CONFIRMED", "REJECTED"],
    }
    completed = run_wrapper(
        tmp_path,
        classification_result("PENDING_USER_CONFIRMATION", 1),
        {"schema_version": "1.0", "status": "USER_CONFIRMATION_REQUIRED", "requests": [request]},
    )
    assert completed.returncode == 0, completed.stderr
    output = yaml.safe_load((tmp_path / "subagent_result.yaml").read_text(encoding="utf-8"))
    assert output["validation_result"]["outcome_code"] == "CLASSIFICATION_DECISION_REQUIRED"
    item = output["confirmation_items"][0]
    assert item["blocking"] is True
    assert item["category"] == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"
    assert item["available_options"] == ["CONFIRMED", "REJECTED"]
    assert any("HEM" in record for record in item["affected_records"])

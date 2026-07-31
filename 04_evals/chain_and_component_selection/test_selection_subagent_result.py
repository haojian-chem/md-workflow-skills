from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

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
BUILDER = REPO_ROOT / "02_operations/chain_and_component_selection/scripts/build_subagent_result.py"
SELECT_SCRIPT = REPO_ROOT / "02_operations/chain_and_component_selection/scripts/select_structure.py"
VALIDATE_SCRIPT = REPO_ROOT / "02_validators/chain_and_component_selection_validator/scripts/validate_selection.py"
CONTRACT_DIR = REPO_ROOT / "03_contracts"


def validate_shared(document: dict, schema_name: str) -> None:
    resources = []
    for path in sorted(CONTRACT_DIR.glob("*.schema.yaml")):
        schema = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(schema.get("$id"), str):
            resources.append((schema["$id"], Resource.from_contents(schema)))
    schema = yaml.safe_load((CONTRACT_DIR / schema_name).read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, registry=Registry().with_resources(resources)).iter_errors(document))
    assert errors == []


def test_builds_valid_operation_with_validator_shared_result(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, output_format="MMCIF")
    assert run_script(SELECT_SCRIPT, case["operation_config"]).returncode == 0
    assert run_script(VALIDATE_SCRIPT, case["validator_config"]).returncode == 0

    task = tmp_path / "subagent_task.yaml"
    shared_result = tmp_path / "subagent_result.yaml"
    write_yaml(
        task,
        {
            "schema_version": 2,
            "task_id": "selection-task-1",
            "workstream_id": "structure-preparation",
            "workflow_name": "structure_preparation_workflow",
            "route_id": "route-1",
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
            "project_root": str(tmp_path),
            "work_directory": str(tmp_path),
            "permissions": {
                "allowed_read_paths": [str(case["source"]), str(case["classification"])],
                "allowed_write_paths": [str(tmp_path)],
                "forbidden_paths": [str(tmp_path / "forbidden")],
            },
            "current_valid_files": [
                {
                    "path": str(case["source"]),
                    "state": "present_validated",
                    "role": "source_structure",
                    "artifact_set_id": "source-artifact-set",
                    "sha256": sha256(case["source"]),
                },
                {
                    "path": str(case["classification"]),
                    "state": "present_validated",
                    "role": "classification_result",
                    "sha256": sha256(case["classification"]),
                },
            ],
            "upstream_summary": "v1.2 classification is complete and the user selected compA and compB.",
            "user_decisions": [{"decision_id": "decision-1", "summary": "Keep polymer and covalently linked ligand."}],
            "required_outputs": [
                str(case["output"]),
                str(case["manifest"]),
                str(case["mapping"]),
                str(shared_result),
            ],
            "detail_output_paths": {
                "log_file": None,
                "report_file": str(case["validation_report"]),
                "result_data_file": str(shared_result),
            },
            "result_contract": "03_contracts/subagent_result.schema.yaml",
        },
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--task", str(task),
            "--candidate", str(case["output"]),
            "--manifest", str(case["manifest"]),
            "--mapping", str(case["mapping"]),
            "--operation-report", str(case["operation_report"]),
            "--validation-report", str(case["validation_report"]),
            "--validation-result", str(case["validation_result"]),
            "--output", str(shared_result),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    document = yaml.safe_load(shared_result.read_text(encoding="utf-8"))
    validate_shared(document, "subagent_result.schema.yaml")
    assert document["status"] == "DONE"
    assert document["task_unit_mode"] == "OPERATION_WITH_VALIDATOR"
    assert document["operation_result"]["created_files"][0]["state"] == "present_unvalidated"
    assert document["validation_result"]["validated_files"][0]["state"] == "present_validated"
    artifact = document["artifact_candidates"][0]
    assert artifact["artifact_type"] == "STRUCTURE"
    assert artifact["files"][0]["path"] == str(case["output"].resolve())
    assert artifact["files"][0]["state"] == "present_validated"
    assert artifact["derived_from_artifact_set_ids"] == ["source-artifact-set"]


def test_builder_rejects_unaccepted_validation(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, output_format="MMCIF")
    assert run_script(SELECT_SCRIPT, case["operation_config"]).returncode == 0
    assert run_script(VALIDATE_SCRIPT, case["validator_config"]).returncode == 0
    validation_result = yaml.safe_load(case["validation_result"].read_text(encoding="utf-8"))
    validation_result["status"] = "FAILED"
    validation_result["outcome_code"] = "COORDINATE_OR_ATTRIBUTE_CHANGED"
    write_yaml(case["validation_result"], validation_result)

    task = tmp_path / "subagent_task.yaml"
    write_yaml(
        task,
        {
            "schema_version": 2,
            "task_id": "selection-task-1",
            "workstream_id": "structure-preparation",
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
            "project_root": str(tmp_path),
            "work_directory": str(tmp_path),
            "permissions": {
                "allowed_read_paths": [str(tmp_path)],
                "allowed_write_paths": [str(tmp_path)],
                "forbidden_paths": [],
            },
            "current_valid_files": [],
            "upstream_summary": "selection failed validation",
            "user_decisions": [],
            "required_outputs": [],
            "detail_output_paths": {"log_file": None, "report_file": None, "result_data_file": None},
            "result_contract": "03_contracts/subagent_result.schema.yaml",
        },
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--task", str(task),
            "--candidate", str(case["output"]),
            "--manifest", str(case["manifest"]),
            "--mapping", str(case["mapping"]),
            "--operation-report", str(case["operation_report"]),
            "--validation-report", str(case["validation_report"]),
            "--validation-result", str(case["validation_result"]),
            "--output", str(tmp_path / "subagent_result.yaml"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert "SHARED_RESULT_VALIDATION_NOT_ACCEPTED" in completed.stdout
    assert not (tmp_path / "subagent_result.yaml").exists()

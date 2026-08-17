from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from skill_1_2_state_fixtures import (
    current_observations,
    digest,
    group,
    model_scope,
    reference_manifest,
    residue_record,
    write_yaml,
)

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"

CONNECTION_PDB = """\
ATOM      1  N   CYS A  42      -2.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  CYS A  42      -1.000   0.000   0.000  1.00 20.00           C
ATOM      3  SG  CYS A  42       0.000   0.000   0.000  1.00 20.00           S
HETATM    4 C1   LIG B 501       1.800   0.000   0.000  1.00 20.00           C
END
"""

COORDINATION_PDB = """\
ATOM      1  N   CYS A  42      -2.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  CYS A  42      -1.000   0.000   0.000  1.00 20.00           C
ATOM      3  C   CYS A  42       0.000   0.000   0.000  1.00 20.00           C
ATOM      4  SG  CYS A  42       0.000   0.000   0.000  1.00 20.00           S
HETATM    5 FE   HEM B 501       2.300   0.000   0.000  1.00 20.00          FE
END
"""


def run_script(name: str, config: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), "--config", str(config), *extra],
        text=True,
        capture_output=True,
        check=False,
    )


def write_initial_observations(path: Path, structure: Path, nonstandard: str) -> None:
    groups = [
        group(1, "POLYMER_CHAIN", source_chain_id="A", entity_id="1"),
        group(2, "INDEPENDENT_COMPONENT", source_chain_id="B", entity_id="2", residue_name=nonstandard),
    ]
    records = [
        residue_record(1, "A", "42", "CYS", "POLYMER", "STANDARD_RESIDUE", primary_source="SKILL_REGISTRY"),
        residue_record(2, "B", "501", nonstandard, "NONPOLYMER", "INDEPENDENT_NONSTANDARD", primary_source="PROJECT_DEFINITION"),
    ]
    write_yaml(path, current_observations(structure, groups, records))


def test_geometry_supported_covalent_candidate_updates_current_state(tmp_path: Path) -> None:
    structure = tmp_path / "connection.pdb"
    structure.write_text(CONNECTION_PDB, encoding="utf-8")
    observations_path = tmp_path / "classification_observations.yaml"
    write_initial_observations(observations_path, structure, "LIG")
    definitions = tmp_path / "possible_connections.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_connections": [
                {
                    "label": "LIG_CYS",
                    "partner_1": {"residue_name": "LIG", "atom_name": "C1"},
                    "partner_2": {"residue_name": "CYS", "atom_name": "SG"},
                    "distance_range_angstrom": {"minimum": 1.5, "maximum": 2.2},
                }
            ],
        },
    )
    result_path = tmp_path / "possible_connections_result.yaml"
    config = tmp_path / "connection_config.yaml"
    write_yaml(
        config,
        {
            "structure": {"path": str(structure), "sha256": digest(structure), "source_format": "PDB", "selected_model_id": "1"},
            "possible_connections": {"path": str(definitions), "sha256": digest(definitions)},
            "classification_observations": {"path": str(observations_path)},
            "output": {"path": str(result_path)},
        },
    )
    completed = run_script("check_possible_connections.py", config)
    assert completed.returncode == 0, completed.stderr
    result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    pair = result["definition_results"][0]["pair_results"][0]
    assert pair["status"] == "GEOMETRY_SUPPORTED_CANDIDATE"
    assert pair["relation_id"].startswith("relation:v1/type/COVALENT_CONNECTION/")
    observations = yaml.safe_load(observations_path.read_text(encoding="utf-8"))
    assert observations["completed_checks"]["possible_connections"] == "COMPLETED"
    assert observations["connection_observations"][0]["status"] == "CANDIDATE"
    assert observations["connection_observations"][0]["confirmation_status"] == "PENDING_CONFIRMATION"
    assert observations["check_outputs"]["possible_connections"]["sha256"] == digest(result_path)


def test_recorded_coordination_decision_is_applied_before_final_contract(tmp_path: Path) -> None:
    structure = tmp_path / "coordination.pdb"
    structure.write_text(COORDINATION_PDB, encoding="utf-8")
    observations_path = tmp_path / "classification_observations.yaml"
    write_initial_observations(observations_path, structure, "HEM")

    connection_result = tmp_path / "possible_connections_result.yaml"
    connection_config = tmp_path / "connection_config.yaml"
    write_yaml(
        connection_config,
        {
            "structure": {"path": str(structure), "sha256": digest(structure), "source_format": "PDB", "selected_model_id": "1"},
            "possible_connections": {"path": None},
            "classification_observations": {"path": str(observations_path)},
            "output": {"path": str(connection_result)},
        },
    )
    completed = run_script("check_possible_connections.py", connection_config)
    assert completed.returncode == 0, completed.stderr

    definitions = tmp_path / "possible_coordination.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_coordination": [
                {
                    "label": "HEM_FE_CYS",
                    "metal": {"residue_name": "HEM", "atom_name": "FE", "element": "Fe"},
                    "donor": {"residue_name": "CYS", "atom_name": "SG", "element": "S"},
                    "distance_range_angstrom": {"minimum": 1.8, "maximum": 2.7},
                    "topology_effect": {"promote_nonstandard_to_linked": True},
                }
            ],
        },
    )
    coordination_result = tmp_path / "possible_coordination_result.yaml"
    coordination_config = tmp_path / "coordination_config.yaml"
    base_coordination_config = {
        "structure": {"path": str(structure), "sha256": digest(structure), "source_format": "PDB", "selected_model_id": "1"},
        "possible_coordination": {"path": str(definitions), "sha256": digest(definitions)},
        "classification_observations": {"path": str(observations_path)},
        "output": {"path": str(coordination_result)},
    }
    write_yaml(coordination_config, base_coordination_config)
    completed = run_script("check_possible_coordination.py", coordination_config)
    assert completed.returncode == 0, completed.stderr

    model_scope_path = tmp_path / "model_scope.yaml"
    manifest_path = tmp_path / "reference_manifest.yaml"
    write_yaml(model_scope_path, model_scope(structure))
    write_yaml(manifest_path, reference_manifest(definitions))
    first_confirmation = tmp_path / "confirmation_requests.r001.yaml"
    first_result = tmp_path / "classification_result.r001.yaml"
    first_report = tmp_path / "classification_report.r001.md"
    builder_config = tmp_path / "builder.r001.yaml"
    write_yaml(
        builder_config,
        {
            "model_scope": {"path": str(model_scope_path), "sha256": digest(model_scope_path)},
            "classification_observations": {"path": str(observations_path)},
            "reference_manifest": {"path": str(manifest_path), "sha256": digest(manifest_path)},
            "output": {
                "confirmation_requests_path": str(first_confirmation),
                "classification_result_path": str(first_result),
                "classification_report_path": str(first_report),
            },
        },
    )
    completed = run_script("build_classification_result.py", builder_config)
    assert completed.returncode == 0, completed.stderr
    requests = yaml.safe_load(first_confirmation.read_text(encoding="utf-8"))
    assert requests["status"] == "USER_CONFIRMATION_REQUIRED"
    assert requests["requests"][0]["relation_id"].startswith("relation:v1/type/METAL_COORDINATION/")

    decisions_path = tmp_path / "relation_decisions.yaml"
    record_config = tmp_path / "record_decision.yaml"
    write_yaml(
        record_config,
        {
            "confirmation_requests": {"path": str(first_confirmation), "sha256": digest(first_confirmation)},
            "classification_observations": {"path": str(observations_path)},
            "relation_decisions": {"path": str(decisions_path)},
            "decisions": [{"request_index": 1, "decision": "CONFIRMED"}],
        },
    )
    completed = run_script("record_relation_decisions.py", record_config)
    assert completed.returncode == 0, completed.stderr

    write_yaml(
        coordination_config,
        {**base_coordination_config, "relation_decisions": {"path": str(decisions_path)}},
    )
    completed = run_script("check_possible_coordination.py", coordination_config)
    assert completed.returncode == 0, completed.stderr
    observations = yaml.safe_load(observations_path.read_text(encoding="utf-8"))
    heme = next(record for record in observations["residue_records"] if record["residue_name"] == "HEM")
    assert heme["chain_index"] == 1
    assert heme["classification_observation"]["topology_class"] == "TOPOLOGY_LINKED_NONSTANDARD"
    assert observations["coordination_observations"][0]["confirmation_status"] == "CONFIRMED_BY_USER"

    final_confirmation = tmp_path / "confirmation_requests.r002.yaml"
    final_result = tmp_path / "classification_result.r002.yaml"
    final_report = tmp_path / "classification_report.r002.md"
    final_builder_config = tmp_path / "builder.r002.yaml"
    write_yaml(
        final_builder_config,
        {
            "model_scope": {"path": str(model_scope_path), "sha256": digest(model_scope_path)},
            "classification_observations": {"path": str(observations_path)},
            "reference_manifest": {"path": str(manifest_path), "sha256": digest(manifest_path)},
            "output": {
                "confirmation_requests_path": str(final_confirmation),
                "classification_result_path": str(final_result),
                "classification_report_path": str(final_report),
            },
        },
    )
    completed = run_script("build_classification_result.py", final_builder_config)
    assert completed.returncode == 0, completed.stderr
    result = yaml.safe_load(final_result.read_text(encoding="utf-8"))
    assert result["result_status"] == "COMPLETE"
    assert result["confirmed_relations"]["metal_coordination"][0]["topology_effect_applied"] is True

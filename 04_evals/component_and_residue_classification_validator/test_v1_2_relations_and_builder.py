from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"

COORDINATION_PDB = """\
ATOM      1  N   CYS A  42      -2.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  CYS A  42      -1.000   0.000   0.000  1.00 20.00           C
ATOM      3  C   CYS A  42       0.000   0.000   0.000  1.00 20.00           C
ATOM      4  SG  CYS A  42       0.000   0.000   0.000  1.00 20.00           S
HETATM    5 FE   HEM B 501       2.300   0.000   0.000  1.00 20.00          FE
END
"""

CONNECTION_PDB = """\
ATOM      1  N   CYS A  42      -2.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  CYS A  42      -1.000   0.000   0.000  1.00 20.00           C
ATOM      3  SG  CYS A  42       0.000   0.000   0.000  1.00 20.00           S
HETATM    4 C1   LIG B 501       1.800   0.000   0.000  1.00 20.00           C
END
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def heavy(status: str = "HEAVY_ATOMS_COMPLETE") -> dict:
    return {
        "status": status,
        "reference_type": None,
        "reference_name": None,
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": None,
    }


def observations(structure: Path, nonstandard_name: str) -> dict:
    return {
        "schema_version": "1.0",
        "input": {
            "structure_path": str(structure.resolve()),
            "structure_sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
            "classification_mode": "REGISTRY",
        },
        "entities": [],
        "chain_groups": [
            {
                "chain_index": 1,
                "grouping_status": "BASELINE",
                "group_type": "POLYMER_CHAIN",
                "source_chain_id": "A",
                "entity_id": "1",
                "instance_count": 1,
                "source_associations": [],
            },
            {
                "chain_index": 2,
                "grouping_status": "BASELINE",
                "group_type": "INDEPENDENT_COMPONENT",
                "source_chain_id": "B",
                "entity_id": "2",
                "residue_name": nonstandard_name,
                "instance_count": 1,
                "source_associations": [],
            },
        ],
        "residue_records": [
            {
                "chain_index": 1,
                "source_chain_id": "A",
                "source_resid": {"number": "42", "insertion_code": None},
                "residue_name": "CYS",
                "presence_status": "OBSERVED",
                "sequence_position": None,
                "classification_observation": {
                    "polymer_class": "POLYMER",
                    "topology_class": "STANDARD_RESIDUE",
                    "resolution_status": "RESOLVED",
                    "primary_source": "SKILL_REGISTRY",
                    "evidence": ["fixture"],
                },
                "conformation_observation": {
                    "status": "SINGLE_CONFORMATION",
                    "altloc_ids": [],
                },
                "heavy_atom_check": heavy(),
            },
            {
                "chain_index": 2,
                "source_chain_id": "B",
                "source_resid": {"number": "501", "insertion_code": None},
                "residue_name": nonstandard_name,
                "presence_status": "OBSERVED",
                "sequence_position": None,
                "classification_observation": {
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "INDEPENDENT_NONSTANDARD",
                    "resolution_status": "RESOLVED",
                    "primary_source": "PROJECT_DEFINITION",
                    "evidence": ["fixture"],
                },
                "conformation_observation": {
                    "status": "SINGLE_CONFORMATION",
                    "altloc_ids": [],
                },
                "heavy_atom_check": heavy(),
            },
        ],
        "missing_residue_checks": [],
        "unresolved_observations": [],
        "summary": {
            "entity_count": 0,
            "chain_group_count": 2,
            "recorded_residue_count": 2,
            "observed_residue_count": 2,
            "missing_expected_residue_count": 0,
            "unresolved_observation_count": 0,
            "multiple_conformation_residue_count": 0,
            "heavy_atom_issue_count": 0,
        },
    }


def run_script(name: str, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_geometry_supported_covalent_candidate(tmp_path: Path) -> None:
    structure = tmp_path / "connection.pdb"
    structure.write_text(CONNECTION_PDB, encoding="utf-8")
    obs_path = tmp_path / "classification_observations.yaml"
    write_yaml(obs_path, observations(structure, "LIG"))
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
    output = tmp_path / "possible_connections_result.yaml"
    config = tmp_path / "connection_config.yaml"
    write_yaml(
        config,
        {
            "structure": {
                "path": str(structure),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "possible_connections": {
                "path": str(definitions),
                "sha256": digest(definitions),
            },
            "classification_observations": {
                "path": str(obs_path),
                "sha256": digest(obs_path),
            },
            "output": {"path": str(output)},
        },
    )
    completed = run_script("check_possible_connections.py", config)
    assert completed.returncode == 0, completed.stderr
    document = yaml.safe_load(output.read_text(encoding="utf-8"))
    pair = document["definition_results"][0]["pair_results"][0]
    assert pair["status"] == "GEOMETRY_SUPPORTED_CANDIDATE"
    assert pair["confirmation_required"] is True


def test_coordination_confirmation_promotes_heme_in_final_result(tmp_path: Path) -> None:
    structure = tmp_path / "coordination.pdb"
    structure.write_text(COORDINATION_PDB, encoding="utf-8")
    obs_path = tmp_path / "classification_observations.yaml"
    write_yaml(obs_path, observations(structure, "HEM"))
    definitions = tmp_path / "possible_coordination.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_coordination": [
                {
                    "label": "HEM_FE_CYS",
                    "metal": {
                        "residue_name": "HEM",
                        "atom_name": "FE",
                        "element": "Fe",
                    },
                    "donor": {
                        "residue_name": "CYS",
                        "atom_name": "SG",
                        "element": "S",
                    },
                    "distance_range_angstrom": {"minimum": 1.8, "maximum": 2.7},
                    "topology_effect": {
                        "promote_nonstandard_to_linked": True
                    },
                }
            ],
        },
    )
    coord_result = tmp_path / "possible_coordination_result.yaml"
    coord_config = tmp_path / "coord_config.yaml"
    write_yaml(
        coord_config,
        {
            "structure": {
                "path": str(structure),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "possible_coordination": {
                "path": str(definitions),
                "sha256": digest(definitions),
            },
            "classification_observations": {
                "path": str(obs_path),
                "sha256": digest(obs_path),
            },
            "output": {"path": str(coord_result)},
        },
    )
    completed = run_script("check_possible_coordination.py", coord_config)
    assert completed.returncode == 0, completed.stderr
    coordination = yaml.safe_load(coord_result.read_text(encoding="utf-8"))
    pair = coordination["definition_results"][0]["pair_results"][0]
    assert pair["status"] == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"
    assert pair["topology_effect_evaluation"]["application_status"] == "PENDING_CONFIRMATION"

    model_scope = tmp_path / "model_scope.yaml"
    write_yaml(
        model_scope,
        {
            "schema_version": "1.0",
            "input_structure": {
                "path": str(structure.resolve()),
                "sha256": digest(structure),
                "source_format": "PDB",
            },
            "model_count": 1,
            "models": [
                {
                    "model_id": "1",
                    "chain_count": 2,
                    "residue_count": 2,
                    "atom_count": 5,
                }
            ],
            "selection": {"status": "AUTO_SELECTED", "selected_model_id": "1"},
        },
    )
    manifest = tmp_path / "reference_manifest.yaml"
    write_yaml(
        manifest,
        {
            "schema_version": "1.0",
            "classification_mode": "REGISTRY",
            "project_files": {
                "residue_definitions": {
                    "path": None,
                    "sha256": None,
                    "status": "NOT_PROVIDED",
                }
            },
            "skill_references": [],
            "force_field": None,
            "ccd_components": [],
            "sequence_references": [],
            "relation_definition_files": {
                "possible_connections": {
                    "path": None,
                    "sha256": None,
                    "status": "NOT_PROVIDED",
                },
                "possible_coordination": {
                    "path": None,
                    "sha256": None,
                    "status": "NOT_PROVIDED",
                },
            },
        },
    )
    connection_result = tmp_path / "possible_connections_result.yaml"
    write_yaml(
        connection_result,
        {
            "schema_version": "1.0",
            "status": "NOT_PERFORMED",
            "reason": "DEFINITION_FILE_NOT_PROVIDED",
            "input": {
                "structure_path": str(structure.resolve()),
                "structure_sha256": digest(structure),
                "selected_model_id": "1",
                "definition_path": None,
                "definition_sha256": None,
                "observations_path": str(obs_path.resolve()),
                "observations_sha256": digest(obs_path),
            },
            "definition_results": [],
        },
    )

    first_confirmation = tmp_path / "confirmation_requests.r001.yaml"
    first_result = tmp_path / "classification_result.r001.yaml"
    first_report = tmp_path / "classification_report.r001.md"
    first_config = tmp_path / "builder.r001.yaml"
    common_builder = {
        "model_scope": {"path": str(model_scope), "sha256": digest(model_scope)},
        "classification_observations": {
            "path": str(obs_path),
            "sha256": digest(obs_path),
        },
        "reference_manifest": {"path": str(manifest), "sha256": digest(manifest)},
        "possible_connections_result": {
            "path": str(connection_result),
            "sha256": digest(connection_result),
        },
        "possible_coordination_result": {
            "path": str(coord_result),
            "sha256": digest(coord_result),
        },
    }
    write_yaml(
        first_config,
        {
            **common_builder,
            "output": {
                "confirmation_requests_path": str(first_confirmation),
                "classification_result_path": str(first_result),
                "classification_report_path": str(first_report),
            },
        },
    )
    completed = run_script("build_classification_result.py", first_config)
    assert completed.returncode == 0, completed.stderr
    first_confirmation_doc = yaml.safe_load(
        first_confirmation.read_text(encoding="utf-8")
    )
    assert first_confirmation_doc["status"] == "USER_CONFIRMATION_REQUIRED"
    assert first_confirmation_doc["requests"][0]["request_type"] == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"

    second_confirmation = tmp_path / "confirmation_requests.r002.yaml"
    second_result = tmp_path / "classification_result.r002.yaml"
    second_report = tmp_path / "classification_report.r002.md"
    second_config = tmp_path / "builder.r002.yaml"
    write_yaml(
        second_config,
        {
            **common_builder,
            "decision_source": {
                "confirmation_requests_path": str(first_confirmation),
                "confirmation_requests_sha256": digest(first_confirmation),
                "decisions": [{"request_index": 1, "decision": "CONFIRM"}],
            },
            "output": {
                "confirmation_requests_path": str(second_confirmation),
                "classification_result_path": str(second_result),
                "classification_report_path": str(second_report),
            },
        },
    )
    completed = run_script("build_classification_result.py", second_config)
    assert completed.returncode == 0, completed.stderr
    result = yaml.safe_load(second_result.read_text(encoding="utf-8"))
    assert result["result_status"] == "COMPLETE"
    heme = next(
        record for record in result["residue_records"] if record["residue_name"] == "HEM"
    )
    assert heme["chain_index"] == 1
    assert heme["classification"]["topology_class"] == "COVALENTLY_LINKED_NONSTANDARD"
    assert result["confirmed_relations"]["metal_coordination"][0][
        "relation_type"
    ] == "METAL_COORDINATION"

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def run_script(name: str, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )


def pdb_atom(
    record: str,
    serial: int,
    atom_name: str,
    residue_name: str,
    chain_id: str,
    residue_number: int,
    x: float,
    element: str,
) -> str:
    return (
        f"{record:<6}{serial:>5} {atom_name:^4} {residue_name:>3} {chain_id}{residue_number:>4}    "
        f"{x:>8.3f}{0.0:>8.3f}{0.0:>8.3f}{1.0:>6.2f}{20.0:>6.2f}          {element:>2}\n"
    )


def write_structure(
    path: Path,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
    metal_residue: str,
    metal_atom: str,
    metal_element: str,
    distance: float,
) -> None:
    lines = [
        pdb_atom("ATOM", 1, "N", donor_residue, "A", 42, -2.0, "N"),
        pdb_atom("ATOM", 2, "CA", donor_residue, "A", 42, -1.0, "C"),
        pdb_atom("ATOM", 3, "C", donor_residue, "A", 42, -0.2, "C"),
        pdb_atom("ATOM", 4, donor_atom, donor_residue, "A", 42, 0.0, donor_element),
        pdb_atom("HETATM", 5, metal_atom, metal_residue, "B", 501, distance, metal_element),
        "END\n",
    ]
    path.write_text("".join(lines), encoding="utf-8")


def heavy() -> dict:
    return {
        "status": "HEAVY_ATOMS_COMPLETE",
        "reference_type": None,
        "reference_name": None,
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": None,
    }


def classification_record(
    chain_index: int,
    source_chain_id: str,
    source_resid: str,
    residue_name: str,
    polymer_class: str,
    topology_class: str,
) -> dict:
    return {
        "chain_index": chain_index,
        "source_chain_id": source_chain_id,
        "source_resid": {"number": source_resid, "insertion_code": None},
        "residue_name": residue_name,
        "presence_status": "OBSERVED",
        "sequence_position": None,
        "classification_observation": {
            "polymer_class": polymer_class,
            "topology_class": topology_class,
            "resolution_status": "RESOLVED",
            "primary_source": "PROJECT_DEFINITION" if chain_index == 2 else "SKILL_REGISTRY",
            "evidence": ["coordination topology matrix fixture"],
        },
        "conformation_observation": {
            "status": "SINGLE_CONFORMATION",
            "altloc_ids": [],
        },
        "heavy_atom_check": heavy(),
    }


def observations(
    structure: Path,
    donor_residue: str,
    metal_residue: str,
    *,
    promote: bool,
) -> dict:
    metal_group_type = "INDEPENDENT_COMPONENT" if promote else "ION_GROUP"
    metal_group = {
        "chain_index": 2,
        "grouping_status": "BASELINE",
        "group_type": metal_group_type,
        "source_chain_id": "B" if promote else None,
        "entity_id": "2",
        "residue_name": metal_residue,
        "instance_count": 1,
        "source_associations": [],
    }
    records = [
        classification_record(
            1,
            "A",
            "42",
            donor_residue,
            "POLYMER",
            "STANDARD_RESIDUE",
        )
    ]
    if promote:
        records.append(
            classification_record(
                2,
                "B",
                "501",
                metal_residue,
                "NONPOLYMER",
                "INDEPENDENT_NONSTANDARD",
            )
        )
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
            metal_group,
        ],
        "residue_records": records,
        "missing_residue_checks": [],
        "unresolved_observations": [],
        "summary": {
            "entity_count": 0,
            "chain_group_count": 2,
            "recorded_residue_count": len(records),
            "observed_residue_count": len(records),
            "missing_expected_residue_count": 0,
            "unresolved_observation_count": 0,
            "multiple_conformation_residue_count": 0,
            "heavy_atom_issue_count": 0,
        },
    }


def base_documents(tmp_path: Path, structure: Path, observations_path: Path) -> tuple[Path, Path, Path]:
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
                "observations_path": str(observations_path.resolve()),
                "observations_sha256": digest(observations_path),
            },
            "definition_results": [],
        },
    )
    return model_scope, manifest, connection_result


def run_confirmed_coordination(
    tmp_path: Path,
    *,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
    metal_residue: str,
    metal_atom: str,
    metal_element: str,
    distance: float,
    minimum: float,
    maximum: float,
    promote: bool,
) -> tuple[dict, dict]:
    structure = tmp_path / f"{metal_residue}_{donor_residue}.pdb"
    write_structure(
        structure,
        donor_residue,
        donor_atom,
        donor_element,
        metal_residue,
        metal_atom,
        metal_element,
        distance,
    )
    observations_path = tmp_path / "classification_observations.yaml"
    write_yaml(
        observations_path,
        observations(structure, donor_residue, metal_residue, promote=promote),
    )
    definitions = tmp_path / "possible_coordination.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_coordination": [
                {
                    "label": f"{metal_residue}_{metal_atom}_{donor_residue}_{donor_atom}",
                    "metal": {
                        "residue_name": metal_residue,
                        "atom_name": metal_atom,
                        "element": metal_element,
                    },
                    "donor": {
                        "residue_name": donor_residue,
                        "atom_name": donor_atom,
                        "element": donor_element,
                    },
                    "distance_range_angstrom": {
                        "minimum": minimum,
                        "maximum": maximum,
                    },
                    "topology_effect": {
                        "promote_nonstandard_to_linked": promote,
                    },
                }
            ],
        },
    )
    coordination_result = tmp_path / "possible_coordination_result.yaml"
    coordination_config = tmp_path / "coordination_config.yaml"
    write_yaml(
        coordination_config,
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
                "path": str(observations_path),
                "sha256": digest(observations_path),
            },
            "output": {"path": str(coordination_result)},
        },
    )
    completed = run_script("check_possible_coordination.py", coordination_config)
    assert completed.returncode == 0, completed.stderr
    coordination = yaml.safe_load(coordination_result.read_text(encoding="utf-8"))
    pair = coordination["definition_results"][0]["pair_results"][0]
    assert pair["status"] == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"
    assert pair["confirmation_required"] is True
    assert pair["topology_effect_evaluation"]["application_status"] == (
        "PENDING_CONFIRMATION" if promote else "NOT_APPLICABLE"
    )

    model_scope, manifest, connection_result = base_documents(
        tmp_path,
        structure,
        observations_path,
    )
    common_builder = {
        "model_scope": {"path": str(model_scope), "sha256": digest(model_scope)},
        "classification_observations": {
            "path": str(observations_path),
            "sha256": digest(observations_path),
        },
        "reference_manifest": {"path": str(manifest), "sha256": digest(manifest)},
        "possible_connections_result": {
            "path": str(connection_result),
            "sha256": digest(connection_result),
        },
        "possible_coordination_result": {
            "path": str(coordination_result),
            "sha256": digest(coordination_result),
        },
    }

    first_confirmation = tmp_path / "confirmation_requests.r001.yaml"
    first_result = tmp_path / "classification_result.r001.yaml"
    first_report = tmp_path / "classification_report.r001.md"
    first_config = tmp_path / "builder.r001.yaml"
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
    requests = yaml.safe_load(first_confirmation.read_text(encoding="utf-8"))
    assert requests["status"] == "USER_CONFIRMATION_REQUIRED"
    assert len(requests["requests"]) == 1
    assert requests["requests"][0]["request_type"] == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"

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
    return coordination, result


@pytest.mark.parametrize(
    (
        "metal_residue",
        "metal_atom",
        "metal_element",
        "donor_residue",
        "donor_atom",
        "donor_element",
        "maximum",
    ),
    [
        ("MG", "MG", "Mg", "ASP", "OD1", "O", 2.5),
        ("ZN", "ZN", "Zn", "HIE", "NE2", "N", 2.6),
    ],
)
def test_confirmed_mg_zn_coordination_does_not_promote_topology(
    tmp_path: Path,
    metal_residue: str,
    metal_atom: str,
    metal_element: str,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
    maximum: float,
) -> None:
    _coordination, result = run_confirmed_coordination(
        tmp_path,
        donor_residue=donor_residue,
        donor_atom=donor_atom,
        donor_element=donor_element,
        metal_residue=metal_residue,
        metal_atom=metal_atom,
        metal_element=metal_element,
        distance=2.1,
        minimum=1.7,
        maximum=maximum,
        promote=False,
    )

    relation = result["confirmed_relations"]["metal_coordination"][0]
    assert relation["evidence_status"] == "CONFIRMED_BY_USER"
    assert relation["topology_effect_applied"] is False
    groups = {group["group_type"]: group for group in result["chain_groups"]}
    assert "POLYMER_CHAIN" in groups
    assert "ION_GROUP" in groups
    assert groups["ION_GROUP"]["chain_index"] == 2
    assert not any(
        group["group_type"] in {
            "LINKED_NONSTANDARD_GROUP",
            "MULTICHAIN_LINKED_COMPONENT",
        }
        for group in result["chain_groups"]
    )
    donor = next(record for record in result["residue_records"] if record["residue_name"] == donor_residue)
    assert donor["chain_index"] == 1
    assert donor["classification"]["topology_class"] == "STANDARD_RESIDUE"


@pytest.mark.parametrize(
    ("donor_residue", "donor_atom", "donor_element", "distance"),
    [
        ("CYS", "SG", "S", 2.3),
        ("HIE", "NE2", "N", 2.1),
    ],
)
def test_confirmed_heme_coordination_promotes_heme_into_polymer_chain(
    tmp_path: Path,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
    distance: float,
) -> None:
    _coordination, result = run_confirmed_coordination(
        tmp_path,
        donor_residue=donor_residue,
        donor_atom=donor_atom,
        donor_element=donor_element,
        metal_residue="HEM",
        metal_atom="FE",
        metal_element="Fe",
        distance=distance,
        minimum=1.8,
        maximum=2.7,
        promote=True,
    )

    relation = result["confirmed_relations"]["metal_coordination"][0]
    assert relation["evidence_status"] == "CONFIRMED_BY_USER"
    assert relation["topology_effect_applied"] is True
    heme = next(record for record in result["residue_records"] if record["residue_name"] == "HEM")
    assert heme["chain_index"] == 1
    assert heme["classification"]["polymer_class"] == "NONPOLYMER"
    assert heme["classification"]["topology_class"] == "COVALENTLY_LINKED_NONSTANDARD"
    assert not any(
        group["group_type"] == "INDEPENDENT_COMPONENT"
        and group.get("residue_name") == "HEM"
        for group in result["chain_groups"]
    )

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from skill_1_2_state_fixtures import current_observations, digest, group, residue_record, write_yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "02_validators/component_and_residue_classification_validator/scripts"


def pdb_atom(record: str, serial: int, atom: str, residue: str, chain: str, resid: int, x: float, element: str) -> str:
    return (
        f"{record:<6}{serial:>5} {atom:^4} {residue:>3} {chain}{resid:>4}    "
        f"{x:>8.3f}{0.0:>8.3f}{0.0:>8.3f}{1.0:>6.2f}{20.0:>6.2f}          {element:>2}\n"
    )


def run_case(
    tmp_path: Path,
    *,
    metal_residue: str,
    metal_atom: str,
    metal_element: str,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
    promote: bool,
) -> dict:
    structure = tmp_path / "coordination.pdb"
    structure.write_text(
        "".join(
            [
                pdb_atom("ATOM", 1, "N", donor_residue, "A", 42, -2.0, "N"),
                pdb_atom("ATOM", 2, "CA", donor_residue, "A", 42, -1.0, "C"),
                pdb_atom("ATOM", 3, donor_atom, donor_residue, "A", 42, 0.0, donor_element),
                pdb_atom("HETATM", 4, metal_atom, metal_residue, "B", 501, 2.1, metal_element),
                "END\n",
            ]
        ),
        encoding="utf-8",
    )
    metal_group_type = "INDEPENDENT_COMPONENT" if promote else "ION_GROUP"
    groups = [
        group(1, "POLYMER_CHAIN", source_chain_id="A", entity_id="1"),
        group(2, metal_group_type, source_chain_id="B" if promote else None, entity_id="2", residue_name=metal_residue),
    ]
    records = [
        residue_record(1, "A", "42", donor_residue, "POLYMER", "STANDARD_RESIDUE", primary_source="SKILL_REGISTRY"),
        residue_record(2, "B", "501", metal_residue, "NONPOLYMER", "INDEPENDENT_NONSTANDARD" if promote else "ION_COMPONENT", primary_source="PROJECT_DEFINITION"),
    ]
    observations_path = tmp_path / "classification_observations.yaml"
    write_yaml(observations_path, current_observations(structure, groups, records))
    definitions = tmp_path / "possible_coordination.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_coordination": [
                {
                    "label": "matrix",
                    "metal": {"residue_name": metal_residue, "atom_name": metal_atom, "element": metal_element},
                    "donor": {"residue_name": donor_residue, "atom_name": donor_atom, "element": donor_element},
                    "distance_range_angstrom": {"minimum": 1.7, "maximum": 2.7},
                    "topology_effect": {"promote_nonstandard_to_linked": promote},
                }
            ],
        },
    )
    result_path = tmp_path / "possible_coordination_result.yaml"
    config = tmp_path / "coordination_config.yaml"
    write_yaml(
        config,
        {
            "structure": {"path": str(structure), "sha256": digest(structure), "source_format": "PDB", "selected_model_id": "1"},
            "possible_coordination": {"path": str(definitions), "sha256": digest(definitions)},
            "classification_observations": {"path": str(observations_path)},
            "output": {"path": str(result_path)},
        },
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_possible_coordination.py"), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    candidate = yaml.safe_load(result_path.read_text(encoding="utf-8"))["definition_results"][0]["pair_results"][0]
    relation_id = candidate["relation_id"]
    decisions = tmp_path / "relation_decisions.yaml"
    write_yaml(
        decisions,
        {
            "schema_version": "1.0",
            "structure": {"structure_sha256": digest(structure), "selected_model_id": "1"},
            "decisions": [{"relation_id": relation_id, "relation_kind": "METAL_COORDINATION", "decision": "CONFIRMED"}],
        },
    )
    write_yaml(
        config,
        {
            "structure": {"path": str(structure), "sha256": digest(structure), "source_format": "PDB", "selected_model_id": "1"},
            "possible_coordination": {"path": str(definitions), "sha256": digest(definitions)},
            "classification_observations": {"path": str(observations_path)},
            "relation_decisions": {"path": str(decisions)},
            "output": {"path": str(result_path)},
        },
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_possible_coordination.py"), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return yaml.safe_load(observations_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("metal_residue", "metal_atom", "metal_element", "donor_residue", "donor_atom", "donor_element"),
    [("MG", "MG", "Mg", "ASP", "OD1", "O"), ("ZN", "ZN", "Zn", "HIE", "NE2", "N")],
)
def test_confirmed_ion_coordination_does_not_promote_topology(
    tmp_path: Path,
    metal_residue: str,
    metal_atom: str,
    metal_element: str,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
) -> None:
    observations = run_case(
        tmp_path,
        metal_residue=metal_residue,
        metal_atom=metal_atom,
        metal_element=metal_element,
        donor_residue=donor_residue,
        donor_atom=donor_atom,
        donor_element=donor_element,
        promote=False,
    )
    relation = observations["coordination_observations"][0]
    assert relation["status"] == "CONFIRMED"
    assert relation["topology_effect"]["status"] == "NOT_APPLICABLE"
    ion = next(record for record in observations["residue_records"] if record["residue_name"] == metal_residue)
    assert ion["chain_index"] == 2
    assert ion["classification_observation"]["topology_class"] == "ION_COMPONENT"


@pytest.mark.parametrize(("donor_residue", "donor_atom", "donor_element"), [("CYS", "SG", "S"), ("HIE", "NE2", "N")])
def test_confirmed_heme_coordination_promotes_heme_into_polymer_chain(
    tmp_path: Path,
    donor_residue: str,
    donor_atom: str,
    donor_element: str,
) -> None:
    observations = run_case(
        tmp_path,
        metal_residue="HEM",
        metal_atom="FE",
        metal_element="Fe",
        donor_residue=donor_residue,
        donor_atom=donor_atom,
        donor_element=donor_element,
        promote=True,
    )
    relation = observations["coordination_observations"][0]
    assert relation["status"] == "CONFIRMED"
    assert relation["topology_effect"]["status"] == "APPLIED"
    heme = next(record for record in observations["residue_records"] if record["residue_name"] == "HEM")
    assert heme["chain_index"] == 1
    assert heme["classification_observation"]["topology_class"] == "TOPOLOGY_LINKED_NONSTANDARD"

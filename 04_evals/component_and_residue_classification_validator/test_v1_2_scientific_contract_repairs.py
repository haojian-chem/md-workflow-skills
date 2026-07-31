from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from ccd_reference import CcdTemplate, compare_ccd_heavy_atoms
from classification_engine import execute_classification
from selection_identity import endpoint_id_from_source_identity


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_ccd(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """data_LIG
_chem_comp.id LIG
loop_
_chem_comp_atom.comp_id
_chem_comp_atom.atom_id
_chem_comp_atom.alt_atom_id
_chem_comp_atom.type_symbol
LIG C1 C01 C
LIG O1 O1 O
""",
        encoding="utf-8",
    )


def test_ccd_mapping_preserves_raw_exact_differences(tmp_path: Path) -> None:
    ccd = tmp_path / "LIG.cif"
    write_ccd(ccd)
    template = CcdTemplate(
        component_id="LIG",
        snapshot_path=ccd,
        snapshot_sha256=digest(ccd),
        atom_names=("C1", "O1"),
        heavy_atom_names=("C1", "O1"),
        alternate_atom_names={"C01": "C1"},
    )
    missing, unexpected, mappings = compare_ccd_heavy_atoms(["C01", "N1"], template)
    assert missing == ["C1", "O1"]
    assert unexpected == ["C01", "N1"]
    assert mappings == [{
        "structure_atom_name": "C01",
        "ccd_atom_id": "C1",
        "mapping_source": "CCD_ALTERNATE_ATOM_NAME",
    }]


def test_heavy_atom_findings_are_parallel_and_raw_comparison_is_retained(tmp_path: Path) -> None:
    structure = tmp_path / "lig.pdb"
    structure.write_text(
        "HETATM    1  C01 LIG A   1       0.000   0.000   0.000  1.00 20.00           C\n"
        "HETATM    2  N1  LIG A   1       1.000   0.000   0.000  1.00 20.00           N\n"
        "END\n",
        encoding="utf-8",
    )
    local = tmp_path / "ccd"
    write_ccd(local / "LIG.cif")
    project = tmp_path / "project.yaml"
    project.write_text(
        yaml.safe_dump({
  "schema_version": "1.0",
  "residue_definitions": [{
      "residue_name": "LIG",
      "polymer_class": "NONPOLYMER",
      "topology_class": "INDEPENDENT_NONSTANDARD",
      "ccd_id": "LIG",
  }],
        }, sort_keys=False),
        encoding="utf-8",
    )
    config = {
        "structure": {
  "path": str(structure),
  "sha256": digest(structure),
  "source_format": "PDB",
  "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "project_residue_definitions": {"path": str(project), "sha256": digest(project)},
        "ccd": {"local_reference_dirs": [str(local)], "retrieval_policy": "CACHE_ONLY"},
        "output": {
  "observations_path": str(tmp_path / "observations.yaml"),
  "reference_manifest_path": str(tmp_path / "manifest.yaml"),
        },
    }
    observations, _manifest, *_ = execute_classification(config, SCRIPTS)
    check = observations["residue_records"][0]["heavy_atom_check"]
    assert check["execution_status"] == "COMPLETED"
    assert set(check["findings"]) == {
        "MISSING_EXPECTED_HEAVY_ATOMS",
        "UNEXPECTED_HEAVY_ATOMS",
        "ATOM_NAME_MAPPING_REQUIRED",
    }
    assert check["exact_comparison"] == {
        "missing_expected_atom_names": ["C1", "O1"],
        "unexpected_observed_atom_names": ["C01", "N1"],
    }
    assert check["mapping_resolution_status"] == "PENDING_CONFIRMATION"
    assert check["effective_comparison"] is None
    assert any(item["issue_type"] == "ATOM_NAME_MAPPING_REQUIRED" for item in observations["unresolved_observations"])


def test_endpoint_id_distinguishes_altloc() -> None:
    base = {
        "source_model_id": "1",
        "source_chain_id": "A",
        "source_resid": {"number": "1", "insertion_code": None},
        "source_residue_name": "LIG",
        "source_atom_name": "C1",
    }
    first = endpoint_id_from_source_identity({**base, "source_altloc_id": "A"})
    second = endpoint_id_from_source_identity({**base, "source_altloc_id": "B"})
    assert first != second


def test_terminal_caps_are_independent_baseline_registry() -> None:
    linked = yaml.safe_load((SKILL / "references/topology_linked_nonstandard_residue_registry.yaml").read_text())
    independent = yaml.safe_load((SKILL / "references/independent_nonstandard_residue_registry.yaml").read_text())
    linked_names = {item["residue_name"] for item in linked["residue_definitions"]}
    independent_by_name = {item["residue_name"]: item for item in independent["residue_definitions"]}
    assert not {"ACE", "NME", "NH2"}.intersection(linked_names)
    for name in ("ACE", "NME", "NH2"):
        assert independent_by_name[name]["topology_class"] == "INDEPENDENT_NONSTANDARD"

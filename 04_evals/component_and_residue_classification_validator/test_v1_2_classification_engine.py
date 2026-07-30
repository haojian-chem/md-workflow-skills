from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification

STRUCTURE = """\
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       1.400   1.500   0.000  1.00 20.00           C
HETATM    6 FE   Hem B 501       8.000   0.000   0.000  1.00 20.00          FE
HETATM    7 FE   HEM C 502      12.000   0.000   0.000  1.00 20.00          FE
HETATM    8  C1  LIG D 503      16.000   0.000   0.000  1.00 20.00           C
END
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def write_ccd(path: Path, component_id: str, atoms: list[tuple[str, str]]) -> None:
    rows = "\n".join(
        f"{component_id} {atom_name} {atom_name} {element}"
        for atom_name, element in atoms
    )
    path.write_text(
        f"""data_{component_id}
_chem_comp.id {component_id}
loop_
_chem_comp_atom.comp_id
_chem_comp_atom.atom_id
_chem_comp_atom.alt_atom_id
_chem_comp_atom.type_symbol
{rows}
""",
        encoding="utf-8",
    )


def test_registry_mode_is_case_sensitive_and_uses_local_ccd_first(tmp_path: Path) -> None:
    structure = tmp_path / "case_sensitive.pdb"
    structure.write_text(STRUCTURE, encoding="utf-8")
    project = tmp_path / "project_residue_definitions.yaml"
    write_yaml(
        project,
        {
            "schema_version": "1.0",
            "residue_definitions": [
                {
                    "residue_name": "Hem",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "INDEPENDENT_NONSTANDARD",
                    "ccd_id": "HEM",
                },
                {
                    "residue_name": "HEM",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "INDEPENDENT_NONSTANDARD",
                    "ccd_id": "HEM",
                },
                {
                    "residue_name": "LIG",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "TOPOLOGY_LINKED_NONSTANDARD",
                    "ccd_id": "LIG",
                },
            ],
        },
    )
    local_ccd = tmp_path / "local_ccd"
    local_ccd.mkdir()
    write_ccd(
        local_ccd / "ALA.cif",
        "ALA",
        [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")],
    )
    write_ccd(local_ccd / "HEM.cif", "HEM", [("FE", "Fe")])
    write_ccd(local_ccd / "LIG.cif", "LIG", [("C1", "C")])
    observations_path = tmp_path / "classification_observations.yaml"
    manifest_path = tmp_path / "reference_manifest.yaml"
    config = {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "project_residue_definitions": {
            "path": str(project),
            "sha256": digest(project),
        },
        "ccd": {
            "local_reference_dirs": [str(local_ccd)],
            "retrieval_policy": "CACHE_ONLY",
        },
        "output": {
            "observations_path": str(observations_path),
            "reference_manifest_path": str(manifest_path),
        },
    }
    observations, manifest, *_ = execute_classification(config, SCRIPTS)
    records = {record["residue_name"]: record for record in observations["residue_records"]}
    assert records["ALA"]["classification_observation"]["topology_class"] == "STANDARD_RESIDUE"
    assert records["ALA"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"
    assert records["Hem"]["classification_observation"]["topology_class"] == "INDEPENDENT_NONSTANDARD"
    assert records["HEM"]["classification_observation"]["topology_class"] == "INDEPENDENT_NONSTANDARD"
    assert records["LIG"]["classification_observation"]["topology_class"] == "TOPOLOGY_LINKED_NONSTANDARD"
    assert records["Hem"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"
    assert records["HEM"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"
    assert records["LIG"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"
    heme_manifest = next(
        item for item in manifest["ccd_components"] if item["component_id"] == "HEM"
    )
    assert heme_manifest["mapped_residue_names"] == ["HEM", "Hem"]
    assert heme_manifest["retrieval"]["source"] == "LOCAL_REFERENCE_DIRECTORY"
    assert Path(heme_manifest["project_snapshot"]["path"]).is_file()


def test_force_field_mode_uses_exact_rtp_template_for_standard_heavy_atoms(tmp_path: Path) -> None:
    structure = tmp_path / "alanine.pdb"
    structure.write_text(
        """ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
END
""",
        encoding="utf-8",
    )
    force_field = tmp_path / "test.ff"
    force_field.mkdir()
    (force_field / "aminoacids.rtp").write_text(
        """[ bondedtypes ]
1 1 9 4 1 3 1 0
[ ALA ]
 [ atoms ]
 N   N   -0.3  1
 CA  CT   0.1  2
 C   C    0.5  3
 O   O   -0.3  4
 CB  CT   0.0  5
 [ bonds ]
 N CA
 CA C
 C O
 CA CB
[ NALA ]
 [ atoms ]
 N   N   -0.3  1
 CA  CT   0.1  2
 C   C    0.5  3
 O   O   -0.3  4
 CB  CT   0.0  5
 [ bonds ]
 N CA
 CA C
 C O
 CA CB
""",
        encoding="utf-8",
    )
    observations_path = tmp_path / "classification_observations.yaml"
    manifest_path = tmp_path / "reference_manifest.yaml"
    config = {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "FORCE_FIELD_ANALYSIS"},
        "force_field": {
            "root_path": str(force_field),
            "terminal_template_mappings": [
                {
                    "terminal_role": "N_TERMINUS",
                    "source_residue_name": "ALA",
                    "rtp_residue_name": "NALA",
                }
            ],
        },
        "ccd": {"retrieval_policy": "CACHE_ONLY"},
        "output": {
            "observations_path": str(observations_path),
            "reference_manifest_path": str(manifest_path),
        },
    }
    observations, manifest, *_ = execute_classification(config, SCRIPTS)
    record = observations["residue_records"][0]
    assert record["classification_observation"]["primary_source"] == "FORCE_FIELD"
    assert record["classification_observation"]["topology_class"] == "STANDARD_RESIDUE"
    assert record["heavy_atom_check"]["reference_type"] == "RTP"
    assert record["heavy_atom_check"]["reference_name"] == "NALA"
    assert record["heavy_atom_check"]["status"] == "MISSING_EXPECTED_HEAVY_ATOMS"
    assert record["heavy_atom_check"]["missing_atoms"] == ["CB"]
    assert manifest["force_field"]["status"] == "LOADED"

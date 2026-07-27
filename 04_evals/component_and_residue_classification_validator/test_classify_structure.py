from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPT = SKILL_ROOT / "scripts/classify_structure.py"

STRUCTURE = """\
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       1.400   1.500   0.000  1.00 20.00           C
HETATM    6 FE   HEM B 501       8.000   0.000   0.000  1.00 20.00          FE
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


def make_config(tmp_path: Path, structure_hash: str) -> tuple[Path, Path, Path]:
    structure = tmp_path / "structure.pdb"
    if not structure.exists():
        structure.write_text(STRUCTURE, encoding="utf-8")
    project = tmp_path / "project_residue_definitions.yaml"
    write_yaml(
        project,
        {
            "schema_version": "1.0",
            "residue_definitions": [
                {
                    "residue_name": "HEM",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "INDEPENDENT_NONSTANDARD",
                    "ccd_id": "HEM",
                }
            ],
        },
    )
    local_ccd = tmp_path / "local_ccd"
    local_ccd.mkdir(exist_ok=True)
    write_ccd(
        local_ccd / "ALA.cif",
        "ALA",
        [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")],
    )
    write_ccd(local_ccd / "HEM.cif", "HEM", [("FE", "Fe")])
    observations = tmp_path / "classification_observations.yaml"
    manifest = tmp_path / "reference_manifest.yaml"
    config = tmp_path / "classification_config.yaml"
    write_yaml(
        config,
        {
            "structure": {
                "path": str(structure),
                "sha256": structure_hash,
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
                "observations_path": str(observations),
                "reference_manifest_path": str(manifest),
            },
        },
    )
    return config, observations, manifest


def run_classifier(config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_v1_2_cli_writes_observations_and_reference_manifest(tmp_path: Path) -> None:
    structure = tmp_path / "structure.pdb"
    structure.write_text(STRUCTURE, encoding="utf-8")
    config, observations_path, manifest_path = make_config(tmp_path, digest(structure))

    completed = run_classifier(config)
    assert completed.returncode == 0, completed.stderr
    observations = yaml.safe_load(observations_path.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    records = {
        record["residue_name"]: record for record in observations["residue_records"]
    }
    assert records["ALA"]["classification_observation"]["topology_class"] == "STANDARD_RESIDUE"
    assert records["ALA"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"
    assert records["HEM"]["classification_observation"]["topology_class"] == "INDEPENDENT_NONSTANDARD"
    assert records["HEM"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"
    assert manifest["classification_mode"] == "REGISTRY"
    assert {item["component_id"] for item in manifest["ccd_components"]} == {"ALA", "HEM"}


def test_v1_2_cli_rejects_structure_hash_mismatch_without_outputs(tmp_path: Path) -> None:
    structure = tmp_path / "structure.pdb"
    structure.write_text(STRUCTURE, encoding="utf-8")
    config, observations_path, manifest_path = make_config(tmp_path, "0" * 64)

    completed = run_classifier(config)
    assert completed.returncode == 2
    assert "SHA-256 mismatch" in completed.stderr
    assert not observations_path.exists()
    assert not manifest_path.exists()

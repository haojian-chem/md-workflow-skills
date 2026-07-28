from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
REAL_FF_ROOT = Path(os.environ.get("V1_2_REAL_GROMACS_FF_ROOT", ""))

pytestmark = pytest.mark.skipif(
    not REAL_FF_ROOT.is_dir(),
    reason="set V1_2_REAL_GROMACS_FF_ROOT to a distributed GROMACS force-field directory",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def pdb_atom(
    serial: int,
    atom_name: str,
    residue_name: str,
    residue_number: int,
    x: float,
    y: float,
    element: str,
) -> str:
    return (
        f"ATOM  {serial:5d} {atom_name:^4} {residue_name:>3} A{residue_number:4d}    "
        f"{x:8.3f}{y:8.3f}{0.0:8.3f}{1.0:6.2f}{20.0:6.2f}          {element:>2}\n"
    )


def write_three_residue_peptide(path: Path) -> None:
    atoms = [
        (1, "N", "GLY", 1, 0.0, 0.0, "N"),
        (2, "CA", "GLY", 1, 1.4, 0.0, "C"),
        (3, "C", "GLY", 1, 2.8, 0.0, "C"),
        (4, "O", "GLY", 1, 3.8, 0.0, "O"),
        (5, "N", "ALA", 2, 3.0, 1.3, "N"),
        (6, "CA", "ALA", 2, 4.4, 1.3, "C"),
        (7, "C", "ALA", 2, 5.8, 1.3, "C"),
        (8, "O", "ALA", 2, 6.8, 1.3, "O"),
        (9, "CB", "ALA", 2, 4.4, 2.8, "C"),
        (10, "N", "GLY", 3, 6.0, 2.6, "N"),
        (11, "CA", "GLY", 3, 7.4, 2.6, "C"),
        (12, "C", "GLY", 3, 8.8, 2.6, "C"),
        (13, "O", "GLY", 3, 9.8, 2.6, "O"),
    ]
    path.write_text(
        "SEQRES   1 A    3  GLY ALA GLY\n"
        + "".join(pdb_atom(*atom) for atom in atoms)
        + "TER\nEND\n",
        encoding="utf-8",
    )


def run_public_classification(tmp_path: Path) -> tuple[dict, dict]:
    structure = tmp_path / "gly_ala_gly.pdb"
    write_three_residue_peptide(structure)
    observations_path = tmp_path / "classification_observations.yaml"
    manifest_path = tmp_path / "reference_manifest.yaml"
    config_path = tmp_path / "classification_config.yaml"
    write_yaml(
        config_path,
        {
            "structure": {
                "path": str(structure),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "classification": {"mode": "FORCE_FIELD_ANALYSIS"},
            "force_field": {"root_path": str(REAL_FF_ROOT)},
            "ccd": {"retrieval_policy": "CACHE_ONLY"},
            "output": {
                "observations_path": str(observations_path),
                "reference_manifest_path": str(manifest_path),
            },
        },
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "classify_structure.py"), "--config", str(config_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return (
        yaml.safe_load(observations_path.read_text(encoding="utf-8")),
        yaml.safe_load(manifest_path.read_text(encoding="utf-8")),
    )


def test_real_amber99sb_ildn_internal_rtp_and_terminal_boundary(tmp_path: Path) -> None:
    aminoacids_rtp = REAL_FF_ROOT / "aminoacids.rtp"
    n_terminal_database = REAL_FF_ROOT / "aminoacids.n.tdb"
    c_terminal_database = REAL_FF_ROOT / "aminoacids.c.tdb"
    assert REAL_FF_ROOT.name == "amber99sb-ildn.ff"
    assert aminoacids_rtp.is_file() and aminoacids_rtp.stat().st_size > 10_000
    assert n_terminal_database.is_file() and n_terminal_database.stat().st_size > 0
    assert c_terminal_database.is_file() and c_terminal_database.stat().st_size > 0

    observations, manifest = run_public_classification(tmp_path)
    records = {
        record["source_resid"]["number"]: record
        for record in observations["residue_records"]
    }
    assert set(records) == {"1", "2", "3"}

    internal_alanine = records["2"]
    assert internal_alanine["residue_name"] == "ALA"
    assert internal_alanine["classification_observation"] == {
        "polymer_class": "POLYMER",
        "topology_class": "STANDARD_RESIDUE",
        "resolution_status": "RESOLVED",
        "primary_source": "FORCE_FIELD",
        "evidence": ["exact RTP template match: ALA"],
    }
    assert internal_alanine["heavy_atom_check"] == {
        "status": "HEAVY_ATOMS_COMPLETE",
        "reference_type": "RTP",
        "reference_name": "ALA",
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": None,
    }

    for residue_number in ("1", "3"):
        terminal_glycine = records[residue_number]
        assert terminal_glycine["residue_name"] == "GLY"
        assert terminal_glycine["classification_observation"]["topology_class"] == "STANDARD_RESIDUE"
        assert terminal_glycine["classification_observation"]["primary_source"] == "SKILL_REGISTRY"
        assert terminal_glycine["heavy_atom_check"] == {
            "status": "REFERENCE_TEMPLATE_UNAVAILABLE",
            "reference_type": "RTP",
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": "RTP_TEMPLATE_NOT_RESOLVED",
        }

    assert observations["summary"]["heavy_atom_issue_count"] == 2
    assert observations["summary"]["unresolved_observation_count"] == 0

    force_field = manifest["force_field"]
    assert force_field["status"] == "LOADED"
    assert Path(force_field["root_path"]).resolve() == REAL_FF_ROOT.resolve()
    loaded_paths = {Path(item["path"]).name for item in force_field["files"]}
    assert "aminoacids.rtp" in loaded_paths
    assert all(name.endswith(".rtp") for name in loaded_paths)
    assert "aminoacids.n.tdb" not in loaded_paths
    assert "aminoacids.c.tdb" not in loaded_paths

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_terminal_residues_use_explicit_terminal_rtp_templates(tmp_path: Path) -> None:
    structure = tmp_path / "terminal.pdb"
    structure.write_text(
        """ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       1.400   1.500   0.000  1.00 20.00           C
ATOM      6  N   GLY A   2       3.200   1.200   0.000  1.00 20.00           N
ATOM      7  CA  GLY A   2       4.500   1.200   0.000  1.00 20.00           C
ATOM      8  C   GLY A   2       5.800   1.200   0.000  1.00 20.00           C
ATOM      9  O   GLY A   2       6.800   1.200   0.000  1.00 20.00           O
END
""",
        encoding="utf-8",
    )
    force_field = tmp_path / "terminal.ff"
    force_field.mkdir()
    (force_field / "aminoacids.rtp").write_text(
        """[ bondedtypes ]
1 1 9 4 1 3 1 0
[ ALA ]
 [ atoms ]
 N N 0 1
 CA CT 0 2
 C C 0 3
 O O 0 4
 CB CT 0 5
[ NALA ]
 [ atoms ]
 N N 0 1
 CA CT 0 2
 C C 0 3
 O O 0 4
 CB CT 0 5
 NT N 0 6
[ GLY ]
 [ atoms ]
 N N 0 1
 CA CT 0 2
 C C 0 3
 O O 0 4
[ CGLY ]
 [ atoms ]
 N N 0 1
 CA CT 0 2
 C C 0 3
 O O 0 4
 OXT O 0 5
""",
        encoding="utf-8",
    )
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
                },
                {
                    "terminal_role": "C_TERMINUS",
                    "source_residue_name": "GLY",
                    "rtp_residue_name": "CGLY",
                },
            ],
        },
        "ccd": {"retrieval_policy": "CACHE_ONLY"},
        "output": {
            "observations_path": str(tmp_path / "classification_observations.yaml"),
            "reference_manifest_path": str(tmp_path / "reference_manifest.yaml"),
        },
    }
    observations, _manifest, *_ = execute_classification(config, SCRIPTS)
    records = {
        (record["source_resid"]["number"], record["residue_name"]): record
        for record in observations["residue_records"]
    }
    n_terminal = records[("1", "ALA")]
    c_terminal = records[("2", "GLY")]
    assert n_terminal["heavy_atom_check"]["reference_name"] == "NALA"
    assert n_terminal["heavy_atom_check"]["missing_atoms"] == ["NT"]
    assert c_terminal["heavy_atom_check"]["reference_name"] == "CGLY"
    assert c_terminal["heavy_atom_check"]["missing_atoms"] == ["OXT"]

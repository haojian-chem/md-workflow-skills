from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPT = SKILL_ROOT / "scripts/inspect_model_scope.py"
SCHEMA = SKILL_ROOT / "schemas/model_scope.schema.yaml"

SINGLE_MODEL_PDB = """\
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      11.400  10.000  10.000  1.00 20.00           C
HETATM    3  O   HOH W   1      20.000  20.000  20.000  1.00 20.00           O
END
"""

MULTI_MODEL_PDB = """\
MODEL        1
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      11.400  10.000  10.000  1.00 20.00           C
ENDMDL
MODEL        2
ATOM      3  N   ALA A   1      10.100  10.000  10.000  1.00 20.00           N
ATOM      4  CA  ALA A   1      11.500  10.000  10.000  1.00 20.00           C
ENDMDL
END
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_inspector(structure: Path, output: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--structure",
            str(structure),
            "--structure-sha256",
            digest(structure),
            "--source-format",
            "PDB",
            "--output",
            str(output),
            *extra,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def validate(document: dict) -> None:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)


def test_single_model_is_auto_selected(tmp_path: Path) -> None:
    structure = tmp_path / "single.pdb"
    output = tmp_path / "model_scope.yaml"
    structure.write_text(SINGLE_MODEL_PDB, encoding="utf-8")

    completed = run_inspector(structure, output)
    assert completed.returncode == 0, completed.stderr
    document = yaml.safe_load(output.read_text(encoding="utf-8"))
    validate(document)
    assert document["model_count"] == 1
    assert document["selection"] == {
        "status": "AUTO_SELECTED",
        "selected_model_id": "1",
    }
    assert document["models"][0]["chain_count"] == 2
    assert document["models"][0]["residue_count"] == 2
    assert document["models"][0]["atom_count"] == 3


def test_multiple_models_require_user_selection(tmp_path: Path) -> None:
    structure = tmp_path / "multi.pdb"
    output = tmp_path / "model_scope.yaml"
    structure.write_text(MULTI_MODEL_PDB, encoding="utf-8")

    completed = run_inspector(structure, output)
    assert completed.returncode == 0, completed.stderr
    document = yaml.safe_load(output.read_text(encoding="utf-8"))
    validate(document)
    assert document["model_count"] == 2
    assert document["selection"] == {
        "status": "USER_SELECTION_REQUIRED",
        "selected_model_id": None,
    }


def test_user_selection_can_replace_only_pending_selection(tmp_path: Path) -> None:
    structure = tmp_path / "multi.pdb"
    output = tmp_path / "model_scope.yaml"
    structure.write_text(MULTI_MODEL_PDB, encoding="utf-8")

    first = run_inspector(structure, output)
    assert first.returncode == 0, first.stderr
    second = run_inspector(structure, output, "--selected-model-id", "2")
    assert second.returncode == 0, second.stderr
    document = yaml.safe_load(output.read_text(encoding="utf-8"))
    validate(document)
    assert document["selection"] == {
        "status": "USER_SELECTED",
        "selected_model_id": "2",
    }

    third = run_inspector(structure, output, "--selected-model-id", "1")
    assert third.returncode == 2
    assert "refusing to overwrite" in third.stderr


def test_hash_mismatch_is_technical_failure(tmp_path: Path) -> None:
    structure = tmp_path / "single.pdb"
    output = tmp_path / "model_scope.yaml"
    structure.write_text(SINGLE_MODEL_PDB, encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--structure",
            str(structure),
            "--structure-sha256",
            "0" * 64,
            "--source-format",
            "PDB",
            "--output",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert not output.exists()


def test_invalid_selected_model_is_rejected(tmp_path: Path) -> None:
    structure = tmp_path / "multi.pdb"
    output = tmp_path / "model_scope.yaml"
    structure.write_text(MULTI_MODEL_PDB, encoding="utf-8")
    completed = run_inspector(structure, output, "--selected-model-id", "9")
    assert completed.returncode == 2
    assert "available models" in completed.stderr
    assert not output.exists()

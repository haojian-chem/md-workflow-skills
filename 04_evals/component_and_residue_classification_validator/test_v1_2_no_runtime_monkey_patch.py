from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_classification_facade_has_no_runtime_core_assignments() -> None:
    text = (SCRIPTS / "classification_engine.py").read_text(encoding="utf-8")
    assert "_core._build_chain_groups =" not in text
    assert "_core.explicit_missing_residues =" not in text
    assert "_core.sequence_based_missing_residues =" not in text
    assert "_classification_engine_original" not in text
    core = importlib.import_module("classification_engine_core")
    facade = importlib.import_module("classification_engine")
    assert callable(core.execute_classification)
    assert callable(facade.execute_classification)
    assert "observations_schema" in text


def test_af3_parser_is_not_installed_by_mutation() -> None:
    parser_text = (SCRIPTS / "af3_server_sequence_reference.py").read_text(encoding="utf-8")
    classify_text = (SCRIPTS / "classify_structure.py").read_text(encoding="utf-8")
    assert "install_af3_server_sequence_reference" not in parser_text
    assert "install_af3_server_sequence_reference" not in classify_text
    assert "sequence_missing.parse_af3_sequence_references =" not in parser_text
    assert "core.parse_af3_sequence_references =" not in parser_text


def test_core_owns_grouping_and_missing_output_normalization() -> None:
    core_text = (SCRIPTS / "classification_engine_core.py").read_text(encoding="utf-8")
    sequence_text = (SCRIPTS / "sequence_missing.py").read_text(encoding="utf-8")
    assert "grouping_polymer_class" in core_text
    assert "normalize_missing_residue_outputs(observations)" in core_text
    assert "def normalize_missing_residue_outputs(" in sequence_text
    assert "def sequence_based_missing_residues(" in sequence_text
    assert "parse_af3_server_job_request(path)" in sequence_text

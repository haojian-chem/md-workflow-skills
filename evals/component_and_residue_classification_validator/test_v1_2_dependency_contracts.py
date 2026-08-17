from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_config_schemas_are_meta_valid() -> None:
    for name in (
        "classification_config.schema.yaml",
        "possible_connections_check_config.schema.yaml",
        "possible_coordination_check_config.schema.yaml",
        "classification_result_build_config.schema.yaml",
    ):
        document = yaml.safe_load((SKILL / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(document)


def test_manifest_records_relation_definition_provenance(tmp_path: Path) -> None:
    structure = tmp_path / "water.pdb"
    structure.write_text(
        "HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00 20.00           O\nEND\n",
        encoding="utf-8",
    )
    connections = tmp_path / "possible_connections.yaml"
    connections.write_text(yaml.safe_dump({"schema_version": "1.0", "possible_connections": []}), encoding="utf-8")
    coordination = tmp_path / "possible_coordination.yaml"
    coordination.write_text(yaml.safe_dump({"schema_version": "1.0", "possible_coordination": []}), encoding="utf-8")
    config = {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "relation_definitions": {
            "possible_connections": {"path": str(connections), "sha256": digest(connections)},
            "possible_coordination": {"path": str(coordination), "sha256": digest(coordination)},
        },
        "output": {
            "observations_path": str(tmp_path / "observations.yaml"),
            "reference_manifest_path": str(tmp_path / "manifest.yaml"),
        },
    }
    _observations, manifest, *_ = execute_classification(config, SCRIPTS)
    assert manifest["relation_definition_files"] == {
        "possible_connections": {"path": str(connections.resolve()), "sha256": digest(connections), "status": "LOADED"},
        "possible_coordination": {"path": str(coordination.resolve()), "sha256": digest(coordination), "status": "LOADED"},
    }


def test_direct_dependencies_and_release_markers_are_explicit() -> None:
    requirements = (SCRIPTS / "requirements.txt").read_text(encoding="utf-8")
    assert "referencing>=" in requirements
    version_owners = (
        "inspect_model_scope.py",
        "classify_structure.py",
        "check_possible_connections.py",
        "check_possible_coordination.py",
        "build_classification_result_core.py",
        "build_subagent_result.py",
    )
    for name in version_owners:
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert re.search(r'^VERSION = "\d+\.\d+\.\d+"$', text, re.MULTILINE)
        assert "-draft" not in text


def test_v1_2_does_not_depend_on_source_recognition_report() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "不读取 `source_recognition_report.yaml` 作为运行时 contract" in skill

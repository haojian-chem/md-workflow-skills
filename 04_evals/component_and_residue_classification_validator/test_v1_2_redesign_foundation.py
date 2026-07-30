from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
SCHEMAS = SKILL_ROOT / "schemas"
REFERENCES = SKILL_ROOT / "references"

sys.path.insert(0, str(SCRIPTS))


@pytest.mark.parametrize(
    "module_name",
    [
        "classification_common",
        "structure_records",
        "explicit_relations",
        "rtp_reference",
        "ccd_reference",
        "sequence_missing",
        "classification_engine",
        "check_possible_connections",
        "check_possible_coordination",
        "build_classification_result",
    ],
)
def test_redesign_modules_import(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize(
    "schema_name",
    [
        "project_residue_definitions.schema.yaml",
        "possible_connections.schema.yaml",
        "possible_coordination.schema.yaml",
        "model_scope.schema.yaml",
        "classification_observations.schema.yaml",
        "reference_manifest.schema.yaml",
        "possible_connections_result.schema.yaml",
        "possible_coordination_result.schema.yaml",
        "confirmation_requests.schema.yaml",
        "classification_result.schema.yaml",
    ],
)
def test_redesign_schemas_are_valid_draft_2020_12(schema_name: str) -> None:
    schema = yaml.safe_load((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_strict_registries_validate_and_have_unique_exact_names() -> None:
    schema = yaml.safe_load(
        (SCHEMAS / "project_residue_definitions.schema.yaml").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)
    names: set[str] = set()
    for name in (
        "standard_residue_registry.yaml",
        "topology_linked_nonstandard_residue_registry.yaml",
    ):
        document = yaml.safe_load((REFERENCES / name).read_text(encoding="utf-8"))
        validator.validate(document)
        for entry in document["residue_definitions"]:
            residue_name = entry["residue_name"]
            assert residue_name not in names
            names.add(residue_name)
    assert "HIE" in names
    assert "hie" not in names


def test_possible_connection_distance_semantics_are_checked() -> None:
    from classification_common import (
        ClassificationToolError,
        validate_possible_connections,
    )

    invalid = {
        "possible_connections": [
            {
                "partner_1": {"residue_name": "LIG", "atom_name": "C1"},
                "partner_2": {"residue_name": "CYS", "atom_name": "SG"},
                "distance_range_angstrom": {"minimum": 2.0, "maximum": 2.0},
            }
        ]
    }
    with pytest.raises(ClassificationToolError):
        validate_possible_connections(invalid)


def test_reversed_connection_definition_is_duplicate() -> None:
    from classification_common import (
        ClassificationToolError,
        validate_possible_connections,
    )

    document = {
        "possible_connections": [
            {
                "partner_1": {"residue_name": "LIG", "atom_name": "C1"},
                "partner_2": {"residue_name": "CYS", "atom_name": "SG"},
                "distance_range_angstrom": {"minimum": 1.0, "maximum": 2.0},
            },
            {
                "partner_1": {"residue_name": "CYS", "atom_name": "SG"},
                "partner_2": {"residue_name": "LIG", "atom_name": "C1"},
                "distance_range_angstrom": {"minimum": 1.0, "maximum": 2.0},
            },
        ]
    }
    with pytest.raises(ClassificationToolError):
        validate_possible_connections(document)

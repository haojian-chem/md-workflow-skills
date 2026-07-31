from __future__ import annotations

import sys
from pathlib import Path

import copy

import gemmi
import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from structure_records import (  # noqa: E402
    collect_selected_model,
    current_residue_identity,
    endpoint_dict,
    source_residue_identity,
    validate_residue_identity_record,
)
from classification_common import ClassificationToolError  # noqa: E402


def _record():
    structure = gemmi.read_pdb_string(
        "ATOM      1  SG  CYS A 145       0.000   0.000   0.000  1.00 20.00           S\nEND\n"
    )
    _model, residues, _atoms = collect_selected_model(structure, "1")
    return residues[0]


def test_source_and_current_identity_use_distinct_field_names() -> None:
    residue = _record()
    source = source_residue_identity(residue)
    current = current_residue_identity(residue)
    assert set(source) == {
        "source_model_id",
        "source_chain_id",
        "source_resid",
        "source_residue_name",
    }
    assert set(current) == {
        "current_model_id",
        "current_chain_id",
        "current_resid",
        "current_residue_name",
    }
    assert source["source_chain_id"] == current["current_chain_id"] == "A"
    assert source["source_resid"] == current["current_resid"]
    assert source["source_residue_name"] == current["current_residue_name"] == "CYS"


def test_relation_endpoint_keeps_dual_identity_outside_chain_index() -> None:
    residue = _record()
    endpoint = endpoint_dict(residue.atoms[0], 7)
    assert endpoint["chain_index"] == 7
    assert "chain_index" not in endpoint["source_identity"]
    assert "chain_index" not in endpoint["current_identity"]
    assert endpoint["source_identity"]["source_atom_name"] == "SG"
    assert endpoint["current_identity"]["current_atom_name"] == "SG"


def test_all_public_result_schemas_require_authoritative_dual_identity() -> None:
    schema_names = [
        "classification_observations.schema.yaml",
        "possible_connections_result.schema.yaml",
        "possible_coordination_result.schema.yaml",
        "classification_result.schema.yaml",
    ]
    for name in schema_names:
        document = yaml.safe_load((SKILL / "schemas" / name).read_text(encoding="utf-8"))
        serialized = yaml.safe_dump(document, sort_keys=True)
        assert "source_identity" in serialized
        assert "current_identity" in serialized
        assert "source_model_id" in serialized
        assert "current_model_id" in serialized
        assert "source_residue_name" in serialized
        assert "current_residue_name" in serialized


def test_missing_residue_contract_allows_no_current_identity() -> None:
    schema = yaml.safe_load(
        (SKILL / "schemas/classification_observations.schema.yaml").read_text(encoding="utf-8")
    )
    current = schema["$defs"]["residue_record"]["properties"]["current_identity"]
    assert any(item.get("type") == "null" for item in current["oneOf"])
    assert any("$ref" in item for item in current["oneOf"])


def _identity_record(*, presence_status: str = "OBSERVED") -> dict:
    residue = _record()
    return {
        "source_identity": source_residue_identity(residue),
        "current_identity": (
            current_residue_identity(residue)
            if presence_status == "OBSERVED"
            else None
        ),
        "chain_index": 1,
        "source_chain_id": "A",
        "source_resid": {"number": "145", "insertion_code": None},
        "residue_name": "CYS",
        "presence_status": presence_status,
        "sequence_position": 1,
    }


def test_runtime_rejects_identity_mirror_or_source_current_divergence() -> None:
    record = _identity_record()
    validate_residue_identity_record(record)

    bad_mirror = copy.deepcopy(record)
    bad_mirror["source_chain_id"] = "B"
    with pytest.raises(ClassificationToolError):
        validate_residue_identity_record(bad_mirror)

    bad_current = copy.deepcopy(record)
    bad_current["current_identity"]["current_chain_id"] = "B"
    with pytest.raises(ClassificationToolError):
        validate_residue_identity_record(bad_current)

    missing = _identity_record(presence_status="MISSING_EXPECTED")
    validate_residue_identity_record(missing)
    missing["current_identity"] = current_residue_identity(_record())
    with pytest.raises(ClassificationToolError):
        validate_residue_identity_record(missing)


def _record_validator(schema_name: str) -> Draft202012Validator:
    document = yaml.safe_load((SKILL / "schemas" / schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(
        {
            "$schema": document["$schema"],
            "$defs": document["$defs"],
            "$ref": "#/$defs/residue_record",
        }
    )


def _schema_record(schema_name: str, *, presence_status: str) -> dict:
    record = _identity_record(presence_status=presence_status)
    record["conformation_observation" if "observations" in schema_name else "conformation"] = {
        "status": "SINGLE_CONFORMATION" if presence_status == "OBSERVED" else "NOT_APPLICABLE",
        "altloc_ids": [],
    }
    record["heavy_atom_check"] = {
        "status": "HEAVY_ATOMS_COMPLETE" if presence_status == "OBSERVED" else "NOT_APPLICABLE",
        "reference_type": None,
        "reference_name": None,
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": None,
    }
    if "observations" in schema_name:
        record["classification_observation"] = {
            "polymer_class": "POLYMER",
            "topology_class": "STANDARD_RESIDUE",
            "resolution_status": "RESOLVED",
            "primary_source": "SKILL_REGISTRY",
            "evidence": ["test"],
        }
    else:
        record["classification"] = {
            "polymer_class": "POLYMER",
            "topology_class": "STANDARD_RESIDUE",
            "resolution_status": "RESOLVED",
            "evidence": ["test"],
        }
    return record


@pytest.mark.parametrize(
    "schema_name",
    ["classification_observations.schema.yaml", "classification_result.schema.yaml"],
)
def test_presence_status_strictly_controls_current_identity(schema_name: str) -> None:
    validator = _record_validator(schema_name)
    observed = _schema_record(schema_name, presence_status="OBSERVED")
    missing = _schema_record(schema_name, presence_status="MISSING_EXPECTED")
    assert list(validator.iter_errors(observed)) == []
    assert list(validator.iter_errors(missing)) == []

    observed["current_identity"] = None
    assert list(validator.iter_errors(observed))
    missing["current_identity"] = current_residue_identity(_record())
    assert list(validator.iter_errors(missing))

from __future__ import annotations

import copy
import sys
from pathlib import Path

import gemmi
import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_common import ClassificationToolError
from structure_records import collect_selected_model, current_residue_identity, endpoint_dict, source_residue_identity, validate_residue_identity_record


def _record():
    structure = gemmi.read_pdb_string("ATOM      1  SG  CYS A 145       0.000   0.000   0.000  1.00 20.00           S\nEND\n")
    _model, residues, _atoms = collect_selected_model(structure, "1")
    return residues[0]


def _identity_record(*, presence_status: str = "OBSERVED") -> dict:
    residue = _record()
    return {
        "source_identity": source_residue_identity(residue),
        "current_identity": current_residue_identity(residue) if presence_status == "OBSERVED" else None,
        "chain_index": 1,
        "source_chain_id": "A",
        "source_resid": {"number": "145", "insertion_code": None},
        "residue_name": "CYS",
        "presence_status": presence_status,
        "sequence_position": 1,
    }


def test_source_and_current_identity_use_distinct_field_names() -> None:
    residue = _record()
    source = source_residue_identity(residue)
    current = current_residue_identity(residue)
    assert set(source) == {"source_model_id", "source_chain_id", "source_resid", "source_residue_name"}
    assert set(current) == {"current_model_id", "current_chain_id", "current_resid", "current_residue_name"}
    endpoint = endpoint_dict(residue.atoms[0], 7)
    assert endpoint["chain_index"] == 7
    assert "chain_index" not in endpoint["source_identity"]
    assert endpoint["source_identity"]["source_atom_name"] == "SG"


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


def _heavy(observed: bool) -> dict:
    comparison = {"missing_expected_atom_names": [], "unexpected_observed_atom_names": []}
    return {
        "execution_status": "COMPLETED" if observed else "NOT_APPLICABLE",
        "findings": [],
        "reference_type": None,
        "reference_name": None,
        "exact_comparison": comparison if observed else None,
        "atom_name_mapping_candidates": [],
        "mapping_resolution_status": "NOT_APPLICABLE",
        "effective_comparison": comparison if observed else None,
        "reason": None,
    }


def test_public_residue_record_schemas_accept_current_dual_identity_contract() -> None:
    source = _identity_record()
    classification = {
        "component_id": "CYS",
        "polymer_class": "POLYMER",
        "topology_class": "STANDARD_RESIDUE",
        "resolution_status": "RESOLVED",
        "primary_source": "SKILL_REGISTRY",
        "evidence": ["test"],
    }
    observation_record = {
        **source,
        "baseline_chain_index": 1,
        "classification_observation": copy.deepcopy(classification),
        "baseline_classification_observation": copy.deepcopy(classification),
        "conformation_observation": {"status": "SINGLE_CONFORMATION", "altloc_ids": []},
        "heavy_atom_check": _heavy(True),
    }
    result_record = {
        **source,
        "residue_id": "residue:v1/test",
        "component_id": "component:v1/test",
        "classification": copy.deepcopy(classification),
        "conformation": {"status": "SINGLE_CONFORMATION", "altloc_ids": []},
        "heavy_atom_check": _heavy(True),
    }
    for schema_name, record in (
        ("classification_observations.schema.yaml", observation_record),
        ("classification_result.schema.yaml", result_record),
    ):
        document = yaml.safe_load((SKILL / "schemas" / schema_name).read_text(encoding="utf-8"))
        validator = Draft202012Validator({"$schema": document["$schema"], "$defs": document["$defs"], "$ref": "#/$defs/residue_record"})
        assert list(validator.iter_errors(record)) == []

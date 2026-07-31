from __future__ import annotations

import sys
from pathlib import Path

import gemmi
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from structure_records import (  # noqa: E402
    collect_selected_model,
    current_residue_identity,
    endpoint_dict,
    source_residue_identity,
)


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

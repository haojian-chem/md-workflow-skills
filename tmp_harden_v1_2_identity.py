from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
EVAL = ROOT / "04_evals/component_and_residue_classification_validator"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


structure_records = SKILL / "scripts/structure_records.py"
validation_helper = '''

def validate_residue_identity_record(record: dict[str, Any]) -> None:
    """Validate authoritative dual identity and its v1 compatibility mirrors."""
    source = record.get("source_identity")
    if not isinstance(source, dict):
        raise ClassificationToolError("residue record source_identity must be a mapping")
    expected_source = {
        "source_chain_id": record.get("source_chain_id"),
        "source_resid": record.get("source_resid"),
        "source_residue_name": record.get("residue_name"),
    }
    for key, expected in expected_source.items():
        if source.get(key) != expected:
            raise ClassificationToolError(
                f"residue identity compatibility mirror differs for {key}"
            )

    presence_status = record.get("presence_status")
    current = record.get("current_identity")
    if presence_status == "MISSING_EXPECTED":
        if current is not None:
            raise ClassificationToolError(
                "MISSING_EXPECTED residue must have current_identity: null"
            )
        return
    if presence_status != "OBSERVED":
        raise ClassificationToolError(f"unsupported residue presence_status: {presence_status!r}")
    if not isinstance(current, dict):
        raise ClassificationToolError("OBSERVED residue must have current_identity")

    equal_pairs = (
        ("source_model_id", "current_model_id"),
        ("source_chain_id", "current_chain_id"),
        ("source_resid", "current_resid"),
        ("source_residue_name", "current_residue_name"),
    )
    for source_key, current_key in equal_pairs:
        if source.get(source_key) != current.get(current_key):
            raise ClassificationToolError(
                "validator 1.2 does not mutate STRUCTURE; observed source/current "
                f"identity differs for {source_key}/{current_key}"
            )
'''
replace_once(
    structure_records,
    "\n\ndef _entity_data(\n",
    validation_helper + "\n\ndef _entity_data(\n",
)
replace_once(
    structure_records,
    '''    resolver: dict[tuple[str | None, str, str | None, str], int] = {}
    for residue in observations.get("residue_records", []):
        if residue.get("presence_status") != "OBSERVED":
''',
    '''    resolver: dict[tuple[str | None, str, str | None, str], int] = {}
    for residue in observations.get("residue_records", []):
        validate_residue_identity_record(residue)
        if residue.get("presence_status") != "OBSERVED":
''',
)

builder = SKILL / "scripts/build_classification_result.py"
replace_once(
    builder,
    ''')

VERSION = "0.2.0-draft"
''',
    ''')
from structure_records import validate_residue_identity_record

VERSION = "0.2.0-draft"
''',
)
replace_once(
    builder,
    '''    coordination, coordination_path, coordination_hash = _load_validated(
        config,
        "possible_coordination_result",
        schema_dir / "possible_coordination_result.schema.yaml",
    )

    selected_model_id = model_scope["selection"]["selected_model_id"]
''',
    '''    coordination, coordination_path, coordination_hash = _load_validated(
        config,
        "possible_coordination_result",
        schema_dir / "possible_coordination_result.schema.yaml",
    )

    for record in observations["residue_records"]:
        validate_residue_identity_record(record)

    selected_model_id = model_scope["selection"]["selected_model_id"]
''',
)

conditional_block = '''      heavy_atom_check:
        $ref: "#/$defs/heavy_atom_check"
    allOf:
      - if:
          properties:
            presence_status: {const: OBSERVED}
          required: [presence_status]
        then:
          properties:
            current_identity:
              $ref: "#/$defs/current_residue_identity"
      - if:
          properties:
            presence_status: {const: MISSING_EXPECTED}
          required: [presence_status]
        then:
          properties:
            current_identity:
              type: "null"
'''
replace_once(
    SKILL / "schemas/classification_observations.schema.yaml",
    '''      heavy_atom_check:
        $ref: "#/$defs/heavy_atom_check"
  missing_residue_check:
''',
    conditional_block + "  missing_residue_check:\n",
)
replace_once(
    SKILL / "schemas/classification_result.schema.yaml",
    '''      heavy_atom_check:
        $ref: "#/$defs/heavy_atom_check"
  endpoint:
''',
    conditional_block + "  endpoint:\n",
)

test_path = EVAL / "test_v1_2_dual_identity.py"
replace_once(
    test_path,
    '''import gemmi
import yaml
''',
    '''import copy

import gemmi
import pytest
import yaml
from jsonschema import Draft202012Validator
''',
)
replace_once(
    test_path,
    '''    endpoint_dict,
    source_residue_identity,
)
''',
    '''    endpoint_dict,
    source_residue_identity,
    validate_residue_identity_record,
)
from classification_common import ClassificationToolError  # noqa: E402
''',
)
additional_tests = '''

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
'''
with test_path.open("a", encoding="utf-8") as handle:
    handle.write(additional_tests)

print("v1.2 dual identity hardening complete")

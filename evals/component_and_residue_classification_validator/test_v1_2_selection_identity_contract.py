from __future__ import annotations

import copy
import sys
from pathlib import Path

import gemmi
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_classification_result import _assign_selection_contract_ids  # noqa: E402
from classification_engine_core import (  # noqa: E402
    ClassificationValue,
    ResidueAnalysis,
    _build_chain_groups,
)
from selection_identity import (  # noqa: E402
    component_id_from_members,
    endpoint_id_from_source_identity,
    relation_id_from_endpoints,
    residue_id_from_source_identity,
)
from structure_records import ResidueRecord  # noqa: E402


def _source_identity(chain: str, number: str, name: str) -> dict:
    return {
        "source_model_id": "1",
        "source_chain_id": chain,
        "source_resid": {"number": number, "insertion_code": None},
        "source_residue_name": name,
    }


def _current_identity(chain: str, number: str, name: str) -> dict:
    return {
        "current_model_id": "1",
        "current_chain_id": chain,
        "current_resid": {"number": number, "insertion_code": None},
        "current_residue_name": name,
    }


def _record(chain_index: int, chain: str, number: str, name: str, *, observed: bool = True) -> dict:
    return {
        "chain_index": chain_index,
        "source_identity": _source_identity(chain, number, name),
        "current_identity": _current_identity(chain, number, name) if observed else None,
        "source_chain_id": chain,
        "source_resid": {"number": number, "insertion_code": None},
        "residue_name": name,
        "presence_status": "OBSERVED" if observed else "MISSING_EXPECTED",
        "sequence_position": None,
        "classification": {
            "polymer_class": "WATER" if name == "HOH" else "POLYMER",
            "topology_class": "SOLVENT_COMPONENT" if name == "HOH" else "STANDARD_RESIDUE",
            "resolution_status": "RESOLVED",
            "evidence": ["fixture"],
        },
        "conformation": {"status": "SINGLE_CONFORMATION" if observed else "NOT_APPLICABLE", "altloc_ids": []},
        "heavy_atom_check": {
            "status": "NOT_PERFORMED" if observed else "NOT_APPLICABLE",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": None,
        },
    }


def _group(chain_index: int, group_type: str, count: int) -> dict:
    return {
        "chain_index": chain_index,
        "grouping_status": "FINAL",
        "group_type": group_type,
        "source_chain_id": None,
        "entity_id": None,
        "residue_name": "HOH" if group_type == "SOLVENT_GROUP" else None,
        "instance_count": count,
        "linked_polymer_chain_indices": [],
        "source_associations": [],
    }


def test_selection_ids_are_deterministic_opaque_and_not_chain_index_based() -> None:
    first = residue_id_from_source_identity(_source_identity("A/B", "10", "CYS"))
    second = residue_id_from_source_identity(_source_identity("A/B", "10", "CYS"))
    assert first == second
    assert "A%2FB" in first
    component_a = component_id_from_members("1", "POLYMER_CHAIN", [first], [])
    component_b = component_id_from_members("1", "POLYMER_CHAIN", [first], [])
    assert component_a == component_b
    assert "chain_index" not in component_a


def test_assignment_exports_complete_group_membership_and_relation_ids() -> None:
    groups = [_group(1, "SOLVENT_GROUP", 2), _group(2, "POLYMER_CHAIN", 2)]
    records = [
        _record(1, "W", "1", "HOH"),
        _record(1, "W", "2", "HOH"),
        _record(2, "A", "10", "CYS"),
        _record(2, "A", "11", "GLY", observed=False),
    ]
    endpoint_source = {
        **_source_identity("A", "10", "CYS"),
        "source_atom_name": "SG",
    }
    water_source = {
        **_source_identity("W", "1", "HOH"),
        "source_atom_name": "O",
    }
    relations = [
        {
            "relation_type": "METAL_COORDINATION",
            "endpoint_1": {
                "chain_index": 2,
                "source_identity": endpoint_source,
                "current_identity": {
                    **_current_identity("A", "10", "CYS"),
                    "current_atom_name": "SG",
                },
                "source_chain_id": "A",
                "source_resid": {"number": "10", "insertion_code": None},
                "residue_name": "CYS",
                "atom_name": "SG",
            },
            "endpoint_2": {
                "chain_index": 1,
                "source_identity": water_source,
                "current_identity": {
                    **_current_identity("W", "1", "HOH"),
                    "current_atom_name": "O",
                },
                "source_chain_id": "W",
                "source_resid": {"number": "1", "insertion_code": None},
                "residue_name": "HOH",
                "atom_name": "O",
            },
            "evidence_status": "CONFIRMED_BY_STRUCTURE",
            "topology_effect_applied": False,
        }
    ]
    _assign_selection_contract_ids("1", groups, records, relations)
    assert len(groups[0]["residue_ids"]) == 2
    assert groups[0]["missing_residue_ids"] == []
    assert len(groups[1]["residue_ids"]) == 1
    assert len(groups[1]["missing_residue_ids"]) == 1
    assert {record["component_id"] for record in records[:2]} == {groups[0]["component_id"]}
    relation = relations[0]
    assert relation["relation_id"].startswith("relation:v1/")
    assert relation["endpoint_1"]["component_id"] == groups[1]["component_id"]
    assert relation["endpoint_2"]["component_id"] == groups[0]["component_id"]
    expected_endpoint = endpoint_id_from_source_identity(endpoint_source)
    assert relation["endpoint_1"]["endpoint_id"] == expected_endpoint
    assert relation["relation_id"] == relation_id_from_endpoints(
        "METAL_COORDINATION",
        [relation["endpoint_2"]["endpoint_id"], relation["endpoint_1"]["endpoint_id"]],
    )


def _water_analysis(number: int, position: int) -> ResidueAnalysis:
    residue = gemmi.Residue()
    residue.name = "HOH"
    residue.seqid = gemmi.SeqId(number, " ")
    record = ResidueRecord(
        model_id="1",
        source_chain_id="W",
        source_resid_number=str(number),
        insertion_code=None,
        residue_name="HOH",
        entity_id=None,
        entity_type=gemmi.EntityType.Water,
        polymer_type=gemmi.PolymerType.Unknown,
        label_seq=None,
        chain_position=0,
        residue_position=position,
        residue=residue,
        atoms=[],
    )
    return ResidueAnalysis(
        residue=record,
        classification=ClassificationValue(
            "WATER",
            "SOLVENT_COMPONENT",
            "RESOLVED",
            "SKILL_REGISTRY",
            ("fixture",),
            None,
        ),
        conformation={"status": "SINGLE_CONFORMATION", "altloc_ids": []},
        heavy_atom_check={
            "status": "NOT_PERFORMED",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": None,
        },
        sequence_position=None,
    )


def test_aggregate_grouping_does_not_erase_instance_records() -> None:
    analyses = [_water_analysis(1, 0), _water_analysis(2, 1)]
    groups, _assignment = _build_chain_groups(analyses)
    assert groups[0]["group_type"] == "SOLVENT_GROUP"
    assert groups[0]["instance_count"] == 2
    assert all(item.include_residue_record for item in analyses)


def test_classification_result_schema_requires_selection_contract_fields() -> None:
    schema = yaml.safe_load(
        (SKILL / "schemas/classification_result.schema.yaml").read_text(encoding="utf-8")
    )
    assert "source_structure" in schema["required"]
    group_required = set(schema["$defs"]["chain_group"]["required"])
    assert {"component_id", "residue_ids", "missing_residue_ids"} <= group_required
    residue_required = set(schema["$defs"]["residue_record"]["required"])
    assert {"residue_id", "component_id"} <= residue_required
    endpoint_required = set(schema["$defs"]["endpoint"]["required"])
    assert {"endpoint_id", "residue_id", "component_id"} <= endpoint_required
    relation_required = set(schema["$defs"]["relation"]["required"])
    assert "relation_id" in relation_required


def test_classification_rules_require_aggregate_instance_records() -> None:
    rules = (SKILL / "references/classification_rules.md").read_text(encoding="utf-8")
    assert "普通汇总成员无需在 `residue_records` 中逐实例展开" not in rules
    assert "普通汇总组仍必须为每个 `OBSERVED` 实例保留 `residue_record`" in rules
    assert "不得删除实例级身份记录" in rules

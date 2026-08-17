from __future__ import annotations

import sys
from pathlib import Path

import gemmi

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import (  # noqa: E402
    ClassificationValue,
    ResidueAnalysis,
    _build_chain_groups,
)
from structure_records import ResidueRecord  # noqa: E402


def make_analysis(
    *,
    entity_type: gemmi.EntityType,
    polymer_type: gemmi.PolymerType,
    classification: ClassificationValue,
) -> ResidueAnalysis:
    residue = gemmi.Residue()
    residue.name = "ALA"
    record = ResidueRecord(
        model_id="1",
        source_chain_id="A",
        source_resid_number="1",
        insertion_code=None,
        residue_name="ALA",
        entity_id="1",
        entity_type=entity_type,
        polymer_type=polymer_type,
        label_seq=1,
        chain_position=0,
        residue_position=0,
        residue=residue,
        atoms=[],
    )
    return ResidueAnalysis(
        residue=record,
        classification=classification,
        conformation={"status": "SINGLE_CONFORMATION", "altloc_ids": []},
        heavy_atom_check={
            "status": "HEAVY_ATOMS_COMPLETE",
            "reference_type": "CCD",
            "reference_name": "ALA",
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": None,
        },
        sequence_position=1,
    )


def test_polymer_entity_remains_polymer_chain_during_classification_conflict() -> None:
    classification = ClassificationValue(
        polymer_class=None,
        topology_class=None,
        resolution_status="CONFLICT",
        primary_source=None,
        evidence=("project/registry conflict",),
        ccd_id="ALA",
    )
    analysis = make_analysis(
        entity_type=gemmi.EntityType.Polymer,
        polymer_type=gemmi.PolymerType.PeptideL,
        classification=classification,
    )

    groups, assignment = _build_chain_groups([analysis])

    assert len(groups) == 1
    assert groups[0]["group_type"] == "POLYMER_CHAIN"
    assert groups[0]["source_chain_id"] == "A"
    assert assignment[analysis.residue.residue_key] == groups[0]["chain_index"]
    assert analysis.chain_index == groups[0]["chain_index"]
    assert analysis.classification is classification
    assert analysis.classification.resolution_status == "CONFLICT"
    assert analysis.classification.polymer_class is None


def test_explicit_nonpolymer_entity_is_not_promoted_by_classification_label() -> None:
    classification = ClassificationValue(
        polymer_class="POLYMER",
        topology_class="STANDARD_RESIDUE",
        resolution_status="RESOLVED",
        primary_source="PROJECT_DEFINITION",
        evidence=("synthetic conflicting project definition",),
        ccd_id="ALA",
    )
    analysis = make_analysis(
        entity_type=gemmi.EntityType.NonPolymer,
        polymer_type=gemmi.PolymerType.Unknown,
        classification=classification,
    )

    groups, assignment = _build_chain_groups([analysis])

    assert len(groups) == 1
    assert groups[0]["group_type"] == "INDEPENDENT_COMPONENT"
    assert assignment[analysis.residue.residue_key] == groups[0]["chain_index"]
    assert analysis.classification is classification
    assert analysis.classification.polymer_class == "POLYMER"

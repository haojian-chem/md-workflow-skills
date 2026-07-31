from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Empty final-result fixtures still require provenance for the source STRUCTURE.
for path in (
    "04_evals/component_and_residue_classification_validator/test_build_subagent_result.py",
    "04_evals/component_and_residue_classification_validator/test_v1_2_manager_closure.py",
):
    replace_once(
        path,
        '''        "classification_mode": "REGISTRY",
        "source_hashes": {
''',
        '''        "classification_mode": "REGISTRY",
        "source_structure": {
            "path": "/fixtures/source.pdb",
            "sha256": "6" * 64,
            "source_format": "PDB",
        },
        "source_hashes": {
''',
    )

# Aggregate grouping now preserves instance-level identity for downstream selection.
replace_once(
    "04_evals/component_and_residue_classification_validator/test_v1_2_altloc_rtp_ccd.py",
    '''    assert solvent_group["residue_name"] == "HOH"
    assert solvent_group["instance_count"] == 1
    assert observations["residue_records"] == []
    assert manifest["force_field"]["status"] == "LOADED"
''',
    '''    assert solvent_group["residue_name"] == "HOH"
    assert solvent_group["instance_count"] == 1
    assert len(observations["residue_records"]) == 1
    water = observations["residue_records"][0]
    assert water["chain_index"] == solvent_group["chain_index"]
    assert water["source_identity"]["source_residue_name"] == "HOH"
    assert water["source_identity"]["source_resid"]["number"] == "1"
    assert water["classification_observation"]["topology_class"] == "SOLVENT_COMPONENT"
    assert manifest["force_field"]["status"] == "LOADED"
''',
)

# Manually authored ion-group observations must carry their actual coordinate member.
replace_once(
    "04_evals/component_and_residue_classification_validator/test_v1_2_coordination_topology_matrix.py",
    '''    records = [
        classification_record(
            1,
            "A",
            "42",
            donor_residue,
            "POLYMER",
            "STANDARD_RESIDUE",
        )
    ]
    if promote:
        records.append(
            classification_record(
                2,
                "B",
                "501",
                metal_residue,
                "NONPOLYMER",
                "INDEPENDENT_NONSTANDARD",
            )
        )
''',
    '''    records = [
        classification_record(
            1,
            "A",
            "42",
            donor_residue,
            "POLYMER",
            "STANDARD_RESIDUE",
        ),
        classification_record(
            2,
            "B",
            "501",
            metal_residue,
            "NONPOLYMER",
            "INDEPENDENT_NONSTANDARD" if promote else "ION_COMPONENT",
        ),
    ]
''',
)

# Final-result residue schema now includes the opaque downstream selection IDs.
replace_once(
    "04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py",
    '''    else:
        record["classification"] = {
            "polymer_class": "POLYMER",
''',
    '''    else:
        record["residue_id"] = "residue:v1/test"
        record["component_id"] = "component:v1/test"
        record["classification"] = {
            "polymer_class": "POLYMER",
''',
)

print("selection identity fixtures migrated")

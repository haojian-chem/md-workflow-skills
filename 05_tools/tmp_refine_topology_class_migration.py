from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_COUNT = "covalently_linked_nonstandard_count"
NEW_COUNT = "topology_linked_nonstandard_count"
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".txt"}


def replace_summary_field() -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text.replace(OLD_COUNT, NEW_COUNT)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def refine_rules() -> None:
    path = ROOT / "02_validators/component_and_residue_classification_validator/references/classification_rules.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "触发关系可以是 `COVALENT_BOND`、`METAL_COORDINATION`",
        "触发关系可以是 `COVALENT_CONNECTION`、`METAL_COORDINATION`",
    )
    path.write_text(text, encoding="utf-8")


def refine_case_sensitive_test() -> None:
    path = ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_classification_engine.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "HETATM    7 FE   HEM C 502      12.000   0.000   0.000  1.00 20.00          FE\nEND",
        "HETATM    7 FE   HEM C 502      12.000   0.000   0.000  1.00 20.00          FE\n"
        "HETATM    8  C1  LIG D 503      16.000   0.000   0.000  1.00 20.00           C\nEND",
    )
    text = text.replace(
        '''                {
                    "residue_name": "HEM",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "TOPOLOGY_LINKED_NONSTANDARD",
                    "ccd_id": "HEM",
                },''',
        '''                {
                    "residue_name": "HEM",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "INDEPENDENT_NONSTANDARD",
                    "ccd_id": "HEM",
                },
                {
                    "residue_name": "LIG",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "TOPOLOGY_LINKED_NONSTANDARD",
                    "ccd_id": "LIG",
                },''',
    )
    text = text.replace(
        '    write_ccd(local_ccd / "HEM.cif", "HEM", [("FE", "Fe")])',
        '    write_ccd(local_ccd / "HEM.cif", "HEM", [("FE", "Fe")])\n'
        '    write_ccd(local_ccd / "LIG.cif", "LIG", [("C1", "C")])',
    )
    text = text.replace(
        '    assert records["HEM"]["classification_observation"]["topology_class"] == "TOPOLOGY_LINKED_NONSTANDARD"',
        '    assert records["HEM"]["classification_observation"]["topology_class"] == "INDEPENDENT_NONSTANDARD"\n'
        '    assert records["LIG"]["classification_observation"]["topology_class"] == "TOPOLOGY_LINKED_NONSTANDARD"',
    )
    text = text.replace(
        '    assert records["HEM"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"',
        '    assert records["HEM"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"\n'
        '    assert records["LIG"]["heavy_atom_check"]["status"] == "HEAVY_ATOMS_COMPLETE"',
    )
    required = [
        '"residue_name": "LIG"',
        'records["HEM"]["classification_observation"]["topology_class"] == "INDEPENDENT_NONSTANDARD"',
        'records["LIG"]["classification_observation"]["topology_class"] == "TOPOLOGY_LINKED_NONSTANDARD"',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"case-sensitive classification test refinement failed: {missing}")
    path.write_text(text, encoding="utf-8")


def refine_fixture_language() -> None:
    path = ROOT / "04_evals/component_and_residue_classification_validator/fixtures/classification_cases.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "title: metal coordination remains separate from covalent topology",
        "title: metal coordination with no topology effect remains independent",
    )
    text = text.replace(
        "- ligand classified as covalently linked solely from coordination",
        "- ligand promoted to TOPOLOGY_LINKED_NONSTANDARD when topology effect is disabled",
    )
    path.write_text(text, encoding="utf-8")


def strengthen_vocabulary_test() -> None:
    path = ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py"
    text = path.read_text(encoding="utf-8")
    if "OLD_COUNT" not in text:
        text = text.replace(
            'NEW_REGISTRY = "topology_linked_nonstandard_residue_registry.yaml"',
            'NEW_REGISTRY = "topology_linked_nonstandard_residue_registry.yaml"\n'
            'OLD_COUNT = "covalently" + "_linked_nonstandard_count"\n'
            'NEW_COUNT = "topology_linked_nonstandard_count"',
        )
        text = text.replace(
            "if OLD_ENUM in text or OLD_REGISTRY in text:",
            "if OLD_ENUM in text or OLD_REGISTRY in text or OLD_COUNT in text:",
        )
        text = text.replace(
            "assert OLD_ENUM not in serialized",
            "assert OLD_ENUM not in serialized\n\n"
            "    result_schema = (SKILL_ROOT / \"schemas/classification_result.schema.yaml\").read_text(encoding=\"utf-8\")\n"
            "    assert NEW_COUNT in result_schema\n"
            "    assert OLD_COUNT not in result_schema",
        )
    path.write_text(text, encoding="utf-8")


def validate() -> None:
    offenders: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        if OLD_COUNT in text:
            offenders.append(str(path.relative_to(ROOT)))
    if offenders:
        raise RuntimeError(f"deprecated summary field remains in: {offenders}")


if __name__ == "__main__":
    replace_summary_field()
    refine_rules()
    refine_case_sensitive_test()
    refine_fixture_language()
    strengthen_vocabulary_test()
    validate()

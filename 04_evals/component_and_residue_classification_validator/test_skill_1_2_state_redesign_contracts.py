from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import gemmi
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_public_schemas_are_valid_and_old_ccd_config_is_absent():
    for path in sorted((SKILL / "schemas").glob("*.schema.yaml")):
        Draft202012Validator.check_schema(yaml.safe_load(path.read_text()))
    config = yaml.safe_load((SKILL / "schemas/classification_config.schema.yaml").read_text())
    ccd = config["properties"]["ccd"]["properties"]
    assert set(ccd) == {"additional_library_paths"}


def test_standard_registry_and_alias_targets_are_exact():
    registry = yaml.safe_load((SKILL / "references/standard_residue_registry.yaml").read_text())
    by_name = {item["residue_name"]: item for item in registry["residue_definitions"]}
    assert "CYX" not in by_name
    assert by_name["HSD"]["ccd_id"] == "HID"
    assert by_name["HSE"]["ccd_id"] == "HIE"
    assert by_name["HSP"]["ccd_id"] == "HIP"
    ions = {name for name, item in by_name.items() if item["topology_class"] == "ION_COMPONENT"}
    assert ions == {"NA", "K", "CL", "MG", "CA", "ZN"}


def test_built_in_ccd_index_matches_files():
    library = SKILL / "references/ccd_library"
    index = yaml.safe_load((library / "index.yaml").read_text())
    for component_id, entry in index["components"].items():
        path = library / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        document = gemmi.cif.read_file(str(path))
        observed_ids = set()
        heavy_atoms = []
        for block in document:
            direct = str(block.find_value("_chem_comp.id") or "").strip()
            if direct not in {"", ".", "?"}:
                observed_ids.add(direct)
            for row in block.find([
                "_chem_comp_atom.comp_id",
                "_chem_comp_atom.atom_id",
                "_chem_comp_atom.type_symbol",
            ]):
                observed_ids.add(str(row[0]))
                if not gemmi.Element(str(row[2])).is_hydrogen:
                    heavy_atoms.append(str(row[1]))
        assert observed_ids == {component_id}
        assert heavy_atoms


def test_relation_identity_has_correct_direction_semantics():
    identity = _load_module("selection_identity", SKILL / "scripts/selection_identity.py")
    first = "endpoint:v1/a"
    second = "endpoint:v1/b"
    assert identity.covalent_relation_id(first, second) == identity.covalent_relation_id(second, first)
    assert identity.coordination_relation_id(first, second) != identity.coordination_relation_id(second, first)


def test_docs_have_distinct_owners_and_reasonable_length():
    skill = (SKILL / "SKILL.md").read_text()
    rules = (SKILL / "references/classification_rules.md").read_text()
    readme = (SKILL / "scripts/README.md").read_text()
    assert len(skill.splitlines()) <= 220
    assert len(rules.splitlines()) <= 180
    assert len(readme.splitlines()) <= 180
    assert "本文件只拥有局部执行顺序" in skill
    assert "科学语义唯一权威来源" in rules
    assert "只说明 CLI、配置和模块边界" in readme

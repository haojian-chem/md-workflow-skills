from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
VALIDATION_RECORD = (
    REPO_ROOT
    / "04_evals/component_and_residue_classification_validator/VALIDATION.md"
)
OLD_ENUM = "COVALENTLY" + "_LINKED_NONSTANDARD"
NEW_ENUM = "TOPOLOGY_LINKED_NONSTANDARD"
OLD_REGISTRY = "covalently" + "_linked_nonstandard_residue_registry.yaml"
NEW_REGISTRY = "topology_linked_nonstandard_residue_registry.yaml"
OLD_COUNT = "covalently" + "_linked_nonstandard_count"
NEW_COUNT = "topology_linked_nonstandard_count"
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".txt"}


def repository_text_files() -> list[Path]:
    roots = [
        REPO_ROOT / ".github",
        REPO_ROOT / "00_authoring",
        REPO_ROOT / "01_workflows",
        REPO_ROOT / "02_operations",
        REPO_ROOT / "02_validators",
        REPO_ROOT / "03_contracts",
        REPO_ROOT / "04_evals",
        REPO_ROOT / "05_tools",
    ]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(
            item
            for item in root.rglob("*")
            if item.is_file()
            and item.suffix.lower() in TEXT_SUFFIXES
            and item != VALIDATION_RECORD
        )
    return sorted(files)


def test_deprecated_topology_class_is_absent_from_active_repository_text() -> None:
    offenders = []
    for item in repository_text_files():
        text = item.read_text(encoding="utf-8")
        if OLD_ENUM in text or OLD_REGISTRY in text or OLD_COUNT in text:
            offenders.append(str(item.relative_to(REPO_ROOT)))
    assert offenders == []


def test_validation_record_preserves_explicit_migration_history() -> None:
    text = VALIDATION_RECORD.read_text(encoding="utf-8")
    assert OLD_ENUM in text
    assert NEW_ENUM in text
    assert OLD_COUNT in text
    assert NEW_COUNT in text
    assert "旧 topology_class" in text
    assert "新 topology_class" in text


def test_topology_linked_contract_and_registry_are_authoritative() -> None:
    rules = (SKILL_ROOT / "references/classification_rules.md").read_text(encoding="utf-8")
    assert NEW_ENUM in rules
    assert "该字段只描述组分的拓扑归属" in rules
    assert "禁止据此反推化学关系类型" in rules
    assert "topology_class: INDEPENDENT_NONSTANDARD" in rules
    assert (SKILL_ROOT / "references" / NEW_REGISTRY).is_file()
    assert not (SKILL_ROOT / "references" / OLD_REGISTRY).exists()

    schema_paths = [
        SKILL_ROOT / "schemas/project_residue_definitions.schema.yaml",
        SKILL_ROOT / "schemas/classification_observations.schema.yaml",
        SKILL_ROOT / "schemas/classification_result.schema.yaml",
    ]
    for schema_path in schema_paths:
        document = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        serialized = yaml.safe_dump(document, sort_keys=True)
        assert NEW_ENUM in serialized
        assert OLD_ENUM not in serialized

    result_schema = (SKILL_ROOT / "schemas/classification_result.schema.yaml").read_text(
        encoding="utf-8"
    )
    assert NEW_COUNT in result_schema
    assert OLD_COUNT not in result_schema

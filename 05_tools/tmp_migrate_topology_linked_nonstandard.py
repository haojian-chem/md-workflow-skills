from __future__ import annotations

from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OLD_ENUM = "TOPOLOGY_LINKED_NONSTANDARD"
NEW_ENUM = "TOPOLOGY_LINKED_NONSTANDARD"
OLD_REGISTRY = "topology_linked_nonstandard_residue_registry.yaml"
NEW_REGISTRY = "topology_linked_nonstandard_residue_registry.yaml"
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".txt"}


def text_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.suffix.lower() in TEXT_SUFFIXES
    )


def replace_repository_vocabulary() -> list[Path]:
    changed: list[Path] = []
    for path in text_files():
        original = path.read_text(encoding="utf-8")
        updated = original.replace(OLD_ENUM, NEW_ENUM)
        updated = updated.replace(OLD_REGISTRY, NEW_REGISTRY)
        updated = updated.replace(
            "topology_linked_nonstandard_fallback_registry:",
            "topology_topology_linked_nonstandard_fallback_registry:",
        )
        updated = updated.replace(
            "marks it TOPOLOGY_LINKED_NONSTANDARD",
            f"marks it {NEW_ENUM}",
        )
        updated = updated.replace(
            "topology-linked nonstandard",
            "topology-linked nonstandard",
        )
        updated = updated.replace(
            "拓扑连接非标准组分",
            "拓扑连接非标准组分",
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def rename_registry() -> None:
    old_path = (
        ROOT
        / "02_validators/component_and_residue_classification_validator/references"
        / OLD_REGISTRY
    )
    new_path = old_path.with_name(NEW_REGISTRY)
    if old_path.exists():
        if new_path.exists():
            raise RuntimeError(f"both registry paths exist: {old_path} and {new_path}")
        old_path.rename(new_path)
    if not new_path.is_file():
        raise RuntimeError(f"renamed registry missing: {new_path}")


def refine_scientific_rules() -> None:
    path = ROOT / "02_validators/component_and_residue_classification_validator/references/classification_rules.md"
    text = path.read_text(encoding="utf-8")

    enum_block = textwrap.dedent(
        """\
        STANDARD_RESIDUE
        TOPOLOGY_LINKED_NONSTANDARD
        INDEPENDENT_NONSTANDARD
        SOLVENT_COMPONENT
        ION_COMPONENT
        ```"""
    )
    definition = textwrap.dedent(
        """

        `TOPOLOGY_LINKED_NONSTANDARD` 表示某个非标准组分已因确认且实际应用了 topology effect 的成键关系而纳入连接拓扑。触发关系可以是 `COVALENT_BOND`、`METAL_COORDINATION`，或其他由项目规则明确允许的 topology-forming relation。

        该字段只描述组分的拓扑归属，禁止据此反推化学关系类型；关系类型必须由 relation result 单独记录。"""
    )
    if definition.strip() not in text:
        if enum_block not in text:
            raise RuntimeError("topology_class enum block not found")
        text = text.replace(enum_block, enum_block + definition, 1)

    hem_pattern = re.compile(
        r"(residue_definitions:\n"
        r"\s+- residue_name: HEM\n"
        r"\s+polymer_class: NONPOLYMER\n"
        r"\s+topology_class:)\s+TOPOLOGY_LINKED_NONSTANDARD\n"
        r"(\s+ccd_id: HEM)",
        flags=re.MULTILINE,
    )
    text, count = hem_pattern.subn(
        r"\1 INDEPENDENT_NONSTANDARD\n\2",
        text,
        count=1,
    )
    if count != 1 and "residue_name: HEM" in text:
        expected = textwrap.dedent(
            """\
            residue_name: HEM
                polymer_class: NONPOLYMER
                topology_class: INDEPENDENT_NONSTANDARD
                ccd_id: HEM"""
        )
        if expected not in text:
            raise RuntimeError("HEM project-definition example could not be normalized")

    baseline_rule = (
        "- 项目级残基定义建立所有精确同名实例的 baseline 分类；确认的 topology-forming relation "
        "只允许提升参与该关系的具体实例，禁止反向修改其他同名实例的 baseline。"
    )
    anchor = "- 一条定义适用于 selected model 中所有精确同名实例。"
    if baseline_rule not in text:
        if anchor not in text:
            raise RuntimeError("project-definition rule anchor not found")
        text = text.replace(anchor, anchor + "\n" + baseline_rule, 1)

    path.write_text(text, encoding="utf-8")


def add_contract_regression_test() -> None:
    path = ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py"
    content = textwrap.dedent(
        '''\
        from __future__ import annotations

        from pathlib import Path

        import yaml

        REPO_ROOT = Path(__file__).resolve().parents[2]
        SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
        OLD_ENUM = "COVALENTLY" + "_LINKED_NONSTANDARD"
        NEW_ENUM = "TOPOLOGY_LINKED_NONSTANDARD"
        OLD_REGISTRY = "covalently" + "_linked_nonstandard_residue_registry.yaml"
        NEW_REGISTRY = "topology_linked_nonstandard_residue_registry.yaml"
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
                    if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES
                )
            return sorted(files)


        def test_deprecated_topology_class_is_absent() -> None:
            offenders = []
            for item in repository_text_files():
                text = item.read_text(encoding="utf-8")
                if OLD_ENUM in text or OLD_REGISTRY in text:
                    offenders.append(str(item.relative_to(REPO_ROOT)))
            assert offenders == []


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
        '''
    )
    path.write_text(content, encoding="utf-8")


def include_regression_test_in_ci() -> None:
    path = ROOT / ".github/workflows/component-classification-v1-2.yml"
    text = path.read_text(encoding="utf-8")
    test_path = "04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py"
    if test_path not in text:
        anchor = "04_evals/component_and_residue_classification_validator/test_v1_2_coordination_topology_matrix.py \\\n"
        if anchor not in text:
            raise RuntimeError("coordination topology matrix CI anchor not found")
        text = text.replace(anchor, anchor + f"            {test_path} \\\n", 1)
        path.write_text(text, encoding="utf-8")


def validate_migration() -> None:
    offenders: list[str] = []
    for path in text_files():
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        if OLD_ENUM in text or OLD_REGISTRY in text:
            offenders.append(str(path.relative_to(ROOT)))
    if offenders:
        raise RuntimeError(f"deprecated vocabulary remains in: {offenders}")

    old_registry_path = (
        ROOT
        / "02_validators/component_and_residue_classification_validator/references"
        / OLD_REGISTRY
    )
    if old_registry_path.exists():
        raise RuntimeError(f"deprecated registry path remains: {old_registry_path}")


if __name__ == "__main__":
    changed = replace_repository_vocabulary()
    rename_registry()
    refine_scientific_rules()
    add_contract_regression_test()
    validate_migration()
    print(f"migrated files: {len(changed)}")

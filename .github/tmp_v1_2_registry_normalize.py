from pathlib import Path

path = Path(
    "02_validators/component_and_residue_classification_validator/"
    "scripts/classification_engine_core.py"
)
text = path.read_text(encoding="utf-8")
start = text.find("    standard_registry_path = Path(\n")
end_marker = "    skill_defs = {**standard_defs, **linked_defs, **independent_defs}\n"
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("cannot locate Skill registry loading block")
end += len(end_marker)
replacement = '''    standard_registry_path = Path(
        classification_config.get(
            "standard_registry_path",
            reference_dir / "standard_residue_registry.yaml",
        )
    ).resolve()
    linked_registry_path = Path(
        classification_config.get(
            "linked_registry_path",
            reference_dir / "topology_linked_nonstandard_residue_registry.yaml",
        )
    ).resolve()
    independent_registry_path = Path(
        classification_config.get(
            "independent_registry_path",
            reference_dir / "independent_nonstandard_residue_registry.yaml",
        )
    ).resolve()
    standard_defs, standard_hash = _load_definition_file(
        standard_registry_path,
        definitions_schema,
    )
    linked_defs, linked_hash = _load_definition_file(
        linked_registry_path,
        definitions_schema,
    )
    independent_defs, independent_hash = _load_definition_file(
        independent_registry_path,
        definitions_schema,
    )
    registry_sets = {
        "standard": set(standard_defs),
        "topology_linked": set(linked_defs),
        "independent": set(independent_defs),
    }
    overlaps: set[str] = set()
    registry_names = list(registry_sets)
    for index, first in enumerate(registry_names):
        for second in registry_names[index + 1 :]:
            overlaps.update(
                registry_sets[first].intersection(registry_sets[second])
            )
    if overlaps:
        raise ClassificationToolError(
            "exact residue names occur in multiple Skill registries: "
            f"{sorted(overlaps)}"
        )
    skill_defs = {**standard_defs, **linked_defs, **independent_defs}
'''
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

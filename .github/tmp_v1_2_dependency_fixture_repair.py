from pathlib import Path

changed: list[Path] = []

coordination = Path(
    "04_evals/component_and_residue_classification_validator/"
    "test_v1_2_coordination_topology_matrix.py"
)
text = coordination.read_text(encoding="utf-8")
old = '''def heavy() -> dict:
    return {
        "status": "HEAVY_ATOMS_COMPLETE",
        "reference_type": None,
        "reference_name": None,
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": None,
    }
'''
new = '''def heavy() -> dict:
    comparison = {
        "missing_expected_atom_names": [],
        "unexpected_observed_atom_names": [],
    }
    return {
        "execution_status": "COMPLETED",
        "findings": [],
        "reference_type": None,
        "reference_name": None,
        "exact_comparison": comparison,
        "atom_name_mapping_candidates": [],
        "mapping_resolution_status": "NOT_APPLICABLE",
        "effective_comparison": comparison,
        "reason": None,
        "status": "HEAVY_ATOMS_COMPLETE",
        "missing_atoms": [],
        "unexpected_atoms": [],
    }
'''
if text.count(old) != 1:
    raise SystemExit(
        f"coordination heavy fixture: expected one occurrence, found {text.count(old)}"
    )
text = text.replace(old, new, 1)
old = '''def base_documents(tmp_path: Path, structure: Path, observations_path: Path) -> tuple[Path, Path, Path]:
'''
new = '''def base_documents(
    tmp_path: Path,
    structure: Path,
    observations_path: Path,
    coordination_definition: Path,
) -> tuple[Path, Path, Path]:
'''
if text.count(old) != 1:
    raise SystemExit(
        f"coordination base_documents signature: expected one occurrence, found {text.count(old)}"
    )
text = text.replace(old, new, 1)
old = '''                "possible_coordination": {
                    "path": None,
                    "sha256": None,
                    "status": "NOT_PROVIDED",
                },
'''
new = '''                "possible_coordination": {
                    "path": str(coordination_definition.resolve()),
                    "sha256": digest(coordination_definition),
                    "status": "LOADED",
                },
'''
if text.count(old) != 1:
    raise SystemExit(
        f"coordination manifest reference: expected one occurrence, found {text.count(old)}"
    )
text = text.replace(old, new, 1)
old = '''    model_scope, manifest, connection_result = base_documents(
        tmp_path,
        structure,
        observations_path,
    )
'''
new = '''    model_scope, manifest, connection_result = base_documents(
        tmp_path,
        structure,
        observations_path,
        definitions,
    )
'''
if text.count(old) != 1:
    raise SystemExit(
        f"coordination base_documents call: expected one occurrence, found {text.count(old)}"
    )
text = text.replace(old, new, 1)
coordination.write_text(text, encoding="utf-8")
changed.append(coordination)

dual_identity = Path(
    "04_evals/component_and_residue_classification_validator/"
    "test_v1_2_dual_identity.py"
)
text = dual_identity.read_text(encoding="utf-8")
old = '''    record["heavy_atom_check"] = {
        "status": "HEAVY_ATOMS_COMPLETE" if presence_status == "OBSERVED" else "NOT_APPLICABLE",
        "reference_type": None,
        "reference_name": None,
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": None,
    }
'''
new = '''    observed = presence_status == "OBSERVED"
    comparison = {
        "missing_expected_atom_names": [],
        "unexpected_observed_atom_names": [],
    }
    record["heavy_atom_check"] = {
        "execution_status": "COMPLETED" if observed else "NOT_APPLICABLE",
        "findings": [],
        "reference_type": None,
        "reference_name": None,
        "exact_comparison": comparison if observed else None,
        "atom_name_mapping_candidates": [],
        "mapping_resolution_status": "NOT_APPLICABLE",
        "effective_comparison": comparison if observed else None,
        "reason": None,
        "status": "HEAVY_ATOMS_COMPLETE" if observed else "NOT_APPLICABLE",
        "missing_atoms": [],
        "unexpected_atoms": [],
    }
'''
if text.count(old) != 1:
    raise SystemExit(
        f"dual identity heavy fixture: expected one occurrence, found {text.count(old)}"
    )
dual_identity.write_text(text.replace(old, new, 1), encoding="utf-8")
changed.append(dual_identity)

with Path("/tmp/dependency-changed-files.txt").open("a", encoding="utf-8") as handle:
    for path in changed:
        handle.write(str(path) + "\n")

for path in changed:
    compile(path.read_text(encoding="utf-8"), str(path), "exec")

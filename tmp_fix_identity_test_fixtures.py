from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVAL = ROOT / "04_evals/component_and_residue_classification_validator"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one fixture target, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


relations = EVAL / "test_v1_2_relations_and_builder.py"
replace_once(
    relations,
    '''            {
                "chain_index": 1,
                "source_chain_id": "A",
                "source_resid": {"number": "42", "insertion_code": None},
                "residue_name": "CYS",
''',
    '''            {
                "source_identity": {
                    "source_model_id": "1",
                    "source_chain_id": "A",
                    "source_resid": {"number": "42", "insertion_code": None},
                    "source_residue_name": "CYS",
                },
                "current_identity": {
                    "current_model_id": "1",
                    "current_chain_id": "A",
                    "current_resid": {"number": "42", "insertion_code": None},
                    "current_residue_name": "CYS",
                },
                "chain_index": 1,
                "source_chain_id": "A",
                "source_resid": {"number": "42", "insertion_code": None},
                "residue_name": "CYS",
''',
)
replace_once(
    relations,
    '''            {
                "chain_index": 2,
                "source_chain_id": "B",
                "source_resid": {"number": "501", "insertion_code": None},
                "residue_name": nonstandard_name,
''',
    '''            {
                "source_identity": {
                    "source_model_id": "1",
                    "source_chain_id": "B",
                    "source_resid": {"number": "501", "insertion_code": None},
                    "source_residue_name": nonstandard_name,
                },
                "current_identity": {
                    "current_model_id": "1",
                    "current_chain_id": "B",
                    "current_resid": {"number": "501", "insertion_code": None},
                    "current_residue_name": nonstandard_name,
                },
                "chain_index": 2,
                "source_chain_id": "B",
                "source_resid": {"number": "501", "insertion_code": None},
                "residue_name": nonstandard_name,
''',
)

matrix = EVAL / "test_v1_2_coordination_topology_matrix.py"
replace_once(
    matrix,
    '''    return {
        "chain_index": chain_index,
        "source_chain_id": source_chain_id,
        "source_resid": {"number": source_resid, "insertion_code": None},
        "residue_name": residue_name,
''',
    '''    return {
        "source_identity": {
            "source_model_id": "1",
            "source_chain_id": source_chain_id,
            "source_resid": {"number": source_resid, "insertion_code": None},
            "source_residue_name": residue_name,
        },
        "current_identity": {
            "current_model_id": "1",
            "current_chain_id": source_chain_id,
            "current_resid": {"number": source_resid, "insertion_code": None},
            "current_residue_name": residue_name,
        },
        "chain_index": chain_index,
        "source_chain_id": source_chain_id,
        "source_resid": {"number": source_resid, "insertion_code": None},
        "residue_name": residue_name,
''',
)

dual = EVAL / "test_v1_2_dual_identity.py"
replace_once(
    dual,
    '''    assert {item.get("type") for item in current["oneOf"] if isinstance(item, dict)} == {"null"}
''',
    '''    assert any(item.get("type") == "null" for item in current["oneOf"])
    assert any("$ref" in item for item in current["oneOf"])
''',
)

print("dual identity test fixtures migrated")

from pathlib import Path

paths = [
    Path("02_validators/component_and_residue_classification_validator/scripts/ccd_reference.py"),
    Path("02_validators/component_and_residue_classification_validator/scripts/classification_engine_core.py"),
    Path("02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py"),
    Path("04_evals/component_and_residue_classification_validator/test_v1_2_scientific_contract_repairs.py"),
]
for path in paths:
    text = path.read_text(encoding="utf-8")
    try:
        compile(text, str(path), "exec")
    except (SyntaxError, IndentationError) as exc:
        lineno = int(exc.lineno or 1)
        lines = text.splitlines()
        print(f"SYNTAX_CONTEXT {path} line {lineno}: {exc}")
        for number in range(max(1, lineno - 30), min(len(lines), lineno + 30) + 1):
            print(f"{number:05d}: {lines[number - 1]}")
        raise

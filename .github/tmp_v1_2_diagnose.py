from pathlib import Path
import re

SKILL = Path(
    "02_validators/component_and_residue_classification_validator"
)

HEAVY_ATOM_DEFS = '''  heavy_atom_comparison:
    type: object
    additionalProperties: false
    required:
      - missing_expected_atom_names
      - unexpected_observed_atom_names
    properties:
      missing_expected_atom_names:
        type: array
        uniqueItems: true
        items: {type: string, minLength: 1}
      unexpected_observed_atom_names:
        type: array
        uniqueItems: true
        items: {type: string, minLength: 1}
  atom_name_mapping_candidate:
    type: object
    additionalProperties: false
    required:
      - observed_atom_name
      - reference_atom_name
      - mapping_source
    properties:
      observed_atom_name: {type: string, minLength: 1}
      reference_atom_name: {type: string, minLength: 1}
      mapping_source:
        enum:
          - CCD_ALTERNATE_ATOM_NAME
          - PROJECT_CONFIRMED_MAPPING
  heavy_atom_check:
    type: object
    additionalProperties: false
    required:
      - execution_status
      - findings
      - reference_type
      - reference_name
      - exact_comparison
      - atom_name_mapping_candidates
      - mapping_resolution_status
      - effective_comparison
      - reason
      - status
      - missing_atoms
      - unexpected_atoms
    properties:
      execution_status:
        enum:
          - COMPLETED
          - NOT_PERFORMED
          - NOT_APPLICABLE
          - REFERENCE_TEMPLATE_UNAVAILABLE
      findings:
        type: array
        uniqueItems: true
        items:
          enum:
            - MISSING_EXPECTED_HEAVY_ATOMS
            - UNEXPECTED_HEAVY_ATOMS
            - ATOM_NAME_MAPPING_REQUIRED
            - ELEMENT_MISMATCH
            - DUPLICATE_ATOM_NAME
      reference_type:
        type: [string, "null"]
        enum: [CCD, RTP, null]
      reference_name:
        $ref: "#/$defs/nullable_string"
      exact_comparison:
        oneOf:
          - type: "null"
          - $ref: "#/$defs/heavy_atom_comparison"
      atom_name_mapping_candidates:
        type: array
        items:
          $ref: "#/$defs/atom_name_mapping_candidate"
      mapping_resolution_status:
        enum:
          - NOT_APPLICABLE
          - PENDING_CONFIRMATION
          - APPLIED
          - REJECTED
      effective_comparison:
        oneOf:
          - type: "null"
          - $ref: "#/$defs/heavy_atom_comparison"
      reason:
        $ref: "#/$defs/nullable_string"
      status:
        description: Deprecated v1 compatibility summary; not authoritative.
        enum:
          - HEAVY_ATOMS_COMPLETE
          - MISSING_EXPECTED_HEAVY_ATOMS
          - UNEXPECTED_HEAVY_ATOMS
          - MISSING_AND_UNEXPECTED_HEAVY_ATOMS
          - ATOM_NAME_MAPPING_REQUIRED
          - REFERENCE_TEMPLATE_UNAVAILABLE
          - NOT_PERFORMED
          - NOT_APPLICABLE
      missing_atoms:
        description: Deprecated mirror of exact_comparison.missing_expected_atom_names.
        type: array
        items: {type: string, minLength: 1}
      unexpected_atoms:
        description: Deprecated mirror of exact_comparison.unexpected_observed_atom_names.
        type: array
        items: {type: string, minLength: 1}
'''

for schema_name in (
    "classification_observations.schema.yaml",
    "classification_result.schema.yaml",
):
    path = SKILL / "schemas" / schema_name
    text = path.read_text(encoding="utf-8")
    start = text.find("  heavy_atom_comparison:\n")
    end = text.find("  residue_record:\n", start)
    if start < 0 or end < 0:
        raise SystemExit(
            f"cannot locate heavy-atom schema region in {path}"
        )
    path.write_text(
        text[:start] + HEAVY_ATOM_DEFS + text[end:],
        encoding="utf-8",
    )

# Migrate the relation-builder fixture helper to the authoritative heavy-atom model.
relations_test = Path(
    "04_evals/component_and_residue_classification_validator/"
    "test_v1_2_relations_and_builder.py"
)
text = relations_test.read_text(encoding="utf-8")
heavy_helper = '''def heavy(status: str = "HEAVY_ATOMS_COMPLETE") -> dict:
    completed = status == "HEAVY_ATOMS_COMPLETE"
    comparison = {
        "missing_expected_atom_names": [],
        "unexpected_observed_atom_names": [],
    }
    return {
        "execution_status": "COMPLETED" if completed else "NOT_PERFORMED",
        "findings": [],
        "reference_type": None,
        "reference_name": None,
        "exact_comparison": comparison if completed else None,
        "atom_name_mapping_candidates": [],
        "mapping_resolution_status": "NOT_APPLICABLE",
        "effective_comparison": comparison if completed else None,
        "reason": None,
        "status": status,
        "missing_atoms": [],
        "unexpected_atoms": [],
    }


'''
text, count = re.subn(
    r'def heavy\(status: str = "HEAVY_ATOMS_COMPLETE"\) -> dict:\n.*?\n\ndef observations\(',
    heavy_helper + "def observations(",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"cannot migrate relation fixture heavy helper: {count}")
relations_test.write_text(text, encoding="utf-8")

# Migrate the 1.3 classification fixture while preserving legacy summary fields.
selection_test = Path(
    "04_evals/chain_and_component_selection/"
    "test_chain_and_component_selection.py"
)
text = selection_test.read_text(encoding="utf-8")
old_heavy = '''        "heavy_atom_check": {
            "status": "NOT_PERFORMED",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": None,
        },
'''
new_heavy = '''        "heavy_atom_check": {
            "execution_status": "NOT_PERFORMED",
            "findings": [],
            "reference_type": None,
            "reference_name": None,
            "exact_comparison": None,
            "atom_name_mapping_candidates": [],
            "mapping_resolution_status": "NOT_APPLICABLE",
            "effective_comparison": None,
            "reason": None,
            "status": "NOT_PERFORMED",
            "missing_atoms": [],
            "unexpected_atoms": [],
        },
'''
if text.count(old_heavy) != 1:
    raise SystemExit(
        f"cannot migrate selection fixture heavy check: {text.count(old_heavy)}"
    )
text = text.replace(old_heavy, new_heavy, 1)
text = text.replace(
    '    source = {**source_identity(chain, number, name), "source_atom_name": atom_name}\n',
    '    source = {\n'
    '        **source_identity(chain, number, name),\n'
    '        "source_atom_name": atom_name,\n'
    '        "source_altloc_id": None,\n'
    '    }\n',
    1,
)
text = text.replace(
    '    current = {**current_identity(chain, number, name), "current_atom_name": atom_name}\n',
    '    current = {\n'
    '        **current_identity(chain, number, name),\n'
    '        "current_atom_name": atom_name,\n'
    '        "current_altloc_id": None,\n'
    '    }\n',
    1,
)
text = text.replace(
    '        "atom_name": atom_name,\n    }\n\n\ndef make_structure',
    '        "atom_name": atom_name,\n'
    '        "altloc_id": None,\n'
    '    }\n\n\ndef make_structure',
    1,
)
selection_test.write_text(text, encoding="utf-8")

changed_file_list = Path("/tmp/changed-files.txt")
with changed_file_list.open("a", encoding="utf-8") as handle:
    handle.write(str(relations_test) + "\n")
    handle.write(str(selection_test) + "\n")

paths = [
    SKILL / "scripts/ccd_reference.py",
    SKILL / "scripts/classification_engine_core.py",
    SKILL / "scripts/build_classification_result.py",
    Path(
        "04_evals/component_and_residue_classification_validator/"
        "test_v1_2_scientific_contract_repairs.py"
    ),
    relations_test,
    selection_test,
]
for path in paths:
    text = path.read_text(encoding="utf-8")
    try:
        compile(text, str(path), "exec")
    except (SyntaxError, IndentationError) as exc:
        lineno = int(exc.lineno or 1)
        lines = text.splitlines()
        print(f"SYNTAX_CONTEXT {path} line {lineno}: {exc}")
        for number in range(
            max(1, lineno - 30),
            min(len(lines), lineno + 30) + 1,
        ):
            print(f"{number:05d}: {lines[number - 1]}")
        raise

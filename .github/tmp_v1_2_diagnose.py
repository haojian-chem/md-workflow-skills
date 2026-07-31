from pathlib import Path

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

paths = [
    SKILL / "scripts/ccd_reference.py",
    SKILL / "scripts/classification_engine_core.py",
    SKILL / "scripts/build_classification_result.py",
    Path(
        "04_evals/component_and_residue_classification_validator/"
        "test_v1_2_scientific_contract_repairs.py"
    ),
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

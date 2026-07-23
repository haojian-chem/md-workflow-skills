# Classification parser

`classify_structure.py` is the deterministic parser used by `component_and_residue_classification_validator`.

It parses PDB, PDBx/mmCIF and AF3 CIF coordinate files with Gemmi, applies the Validator registries, validates the result against `schemas/classification_outputs.schema.yaml`, and writes the detailed classification data and report.

## Invocation

```bash
python scripts/classify_structure.py \
  --structure <input.pdb-or-cif> \
  --task-id <task_id> \
  --workstream-id <workstream_id> \
  --report <component_and_residue_classification_report.yaml> \
  --result-data <classification_result.yaml>
```

For an AlphaFold 3 CIF, add:

```bash
--source-label AF3_CIF
```

For a resolved model selection, add:

```bash
--model-id <model_id>
```

## Deterministic boundaries

The parser:

- never modifies the input structure;
- rejects symlink and empty inputs;
- verifies the input SHA-256 before and after classification;
- separates explicit covalent links, geometry-only covalent candidates and metal coordination candidates;
- never promotes a geometry-only contact to a confirmed covalent link;
- never changes covalent topology class solely because of metal coordination;
- validates output data before writing;
- writes outputs through temporary files and atomic replacement;
- refuses to overwrite output belonging to another task ID.

The parser does not create the shared `subagent_result` object. The Validator wraps the parser result into `03_contracts/subagent_result.schema.yaml`, including any required `confirmation_items`.

## Exit codes

```text
0  classification completed and outputs written
1  deterministic input, registry, schema or classification failure
2  unexpected internal failure
```

## Dependencies

Install the versions declared in `requirements.txt`.

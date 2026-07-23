# Classification validator scripts

The Validator uses two deterministic stages:

```text
classify_structure.py
→ classification_result.yaml + detailed report
→ build_subagent_result.py
→ shared subagent_result v2
```

The Agent performs preflight and passes the files to these scripts. It must not reproduce structure parsing or shared result mapping manually.

## 1. Structure classification

`classify_structure.py` parses PDB, PDBx/mmCIF and AF3 CIF coordinates with Gemmi, applies the Validator registries, validates `classification_result.yaml` against `schemas/classification_outputs.schema.yaml`, and writes the detailed report.

```bash
python scripts/classify_structure.py \
  --structure <input.pdb-or-cif> \
  --task-id <task_id> \
  --workstream-id <workstream_id> \
  --report <component_and_residue_classification_report.yaml> \
  --result-data <classification_result.yaml>
```

For an AlphaFold 3 CIF:

```text
--source-label AF3_CIF
```

For a resolved model selection:

```text
--model-id <model_id>
```

## 2. Shared result wrapper

`build_subagent_result.py` reads the immutable task, classification data and report, validates them against the local and shared contracts, and prints a complete `subagent_result.schema.yaml` v2 object to stdout.

```bash
python scripts/build_subagent_result.py \
  --task <task.yaml> \
  --classification <classification_result.yaml> \
  --report <component_and_residue_classification_report.yaml> \
  --contracts-dir <skill_root>/03_contracts
```

An optional `--output` may be used only inside the task's allowed write paths and outside forbidden management paths. In the normal Manager lifecycle, the wrapper result is returned to Manager; Manager prepares and FAST-validates the candidate `result.yaml` before committing it under `00_project_records/**`.

The wrapper deterministically:

- validates `task.yaml` against `subagent_task.schema.yaml`;
- validates classification data against `classification_outputs.schema.yaml`;
- checks task/workstream IDs, input SHA-256 and task paths;
- enforces allowed read/write and forbidden paths;
- converts classification ambiguities to `confirmation_item.schema.yaml` v2;
- maps `CLASSIFICATION_DECISION_REQUIRED` to `DONE` with blocking confirmation items;
- preserves the input STRUCTURE file state as `present_unvalidated`;
- keeps `artifact_candidates: []`;
- validates the final object against `subagent_result.schema.yaml` v2.

## Deterministic boundaries

The scripts:

- never modify the input structure;
- reject symlink and empty inputs;
- verify input SHA-256 before and after classification;
- separate explicit covalent links, geometry-only covalent candidates and metal coordination candidates;
- never promote a geometry-only contact to a confirmed covalent link;
- never change covalent topology class solely because of metal coordination;
- validate data before writing or returning it;
- protect against cross-task output overwrite;
- never write shared results directly into `00_project_state/**` or `00_project_records/**`.

## Exit codes

Both scripts use:

```text
0  deterministic processing completed
1  input, permission, registry, schema or consistency failure
2  unexpected internal failure
```

## Dependencies

Install the versions declared in `requirements.txt`.

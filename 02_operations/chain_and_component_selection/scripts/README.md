# chain_and_component_selection scripts

## Operation entry point

```bash
python scripts/select_structure.py \
  --config selection_operation_config.yaml
```

`select_structure.py`:

- validates the operation config, `selection_spec.yaml`, and v1.2 `classification_result.yaml`;
- verifies source/classification SHA-256 identities;
- resolves the selected model and opaque component IDs;
- expands only observed `residue_ids` materialized by v1.2;
- blocks a confirmed `COVALENT_CONNECTION` split without auto-expanding selection;
- copies complete residues, atoms, altLocs, source order, coordinates, occupancy, B factor, element, and formal charge;
- reconstructs selected confirmed covalent and metal-coordination connections;
- enforces PDB identifier limits or writes coordinate mmCIF;
- reparses the candidate before atomically committing it;
- writes `selection_manifest.yaml`, `selection_mapping.yaml`, and the Operation report.

## Operation config

```text
schemas/selection_operation_config.schema.yaml
```

```yaml
schema_version: 1
selection_spec_path: /absolute/path/selection_spec.yaml
classification_result_path: /absolute/path/classification_result.yaml
output:
  manifest_path: /absolute/path/selection_manifest.yaml
  mapping_path: /absolute/path/selection_mapping.yaml
  report_path: /absolute/path/chain_and_component_selection_report.yaml
```

The selected structure path and format are read only from the immutable selection spec.

## Shared deterministic module

```text
scripts/selection_common.py
```

This module owns strict YAML/schema/hash helpers, source/current atom identity extraction, selection-plan expansion, relation partitioning, structure copying support, explicit connection reconstruction, and PDB representability checks. The dedicated Validator imports it only for shared mechanical identity handling and independently recomputes acceptance facts.

## Shared task result builder

```bash
python scripts/build_subagent_result.py \
  --task subagent_task.yaml \
  --candidate selected_structure.cif \
  --manifest selection_manifest.yaml \
  --mapping selection_mapping.yaml \
  --operation-report chain_and_component_selection_report.yaml \
  --validation-report chain_and_component_selection_validation_report.yaml \
  --validation-result selection_validation_result.yaml \
  --output subagent_result.yaml
```

The builder accepts only an `OPERATION_WITH_VALIDATOR` task whose Operation and Validator names match these two Skills. It emits a validated STRUCTURE artifact candidate only when the dedicated Validator returns `SELECTION_VALIDATED` or `SELECTION_VALIDATED_WITH_WARNINGS` and explicitly covers the candidate, manifest, and mapping hashes.

Operation-created files remain `present_unvalidated` in the Operation component result. The same candidate, manifest, and mapping become `present_validated` only in the Validator component result and artifact candidate.

The builder does not write project state, artifact-set records, task records, or event logs. Manager owns the single FAST validation of its result/artifact/state/event candidates and their subsequent atomic commit.

## Exit codes

```text
select_structure.py
0  Operation DONE
1  technical FAILED
2  deterministic BLOCKED gate

build_subagent_result.py
0  shared result written and schema-valid
1  input, validation, task, or shared-contract rejection
```

A BLOCKED Operation may write only the structured Operation report. It does not create a partial candidate structure, manifest, or mapping.

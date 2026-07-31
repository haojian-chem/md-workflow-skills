# chain_and_component_selection scripts

## Entry point

```bash
python scripts/select_structure.py \
  --config selection_operation_config.yaml
```

`select_structure.py` is the deterministic Operation entry point. It:

- validates the operation config, `selection_spec.yaml`, and the v1.2 `classification_result.yaml`;
- verifies source/classification SHA-256 identities;
- resolves the selected model and opaque component IDs;
- expands only the observed `residue_ids` materialized by v1.2;
- blocks a confirmed `COVALENT_CONNECTION` split without auto-expanding selection;
- copies complete residues, atoms, altLocs, source order, coordinates, occupancy, B factor, element, and formal charge;
- reconstructs selected confirmed covalent and metal-coordination connections;
- enforces PDB identifier limits or writes coordinate mmCIF;
- reparses the candidate before atomically committing it;
- writes `selection_manifest.yaml`, `selection_mapping.yaml`, and the Operation report.

## Config contract

```text
schemas/selection_operation_config.schema.yaml
```

Required fields:

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

This module owns strict YAML/schema/hash helpers, source/current atom identity extraction, selection-plan expansion, relation partitioning, structure copying support, explicit connection reconstruction, and PDB representability checks. The dedicated Validator imports this module for shared mechanical identity handling but independently recomputes expected selection facts.

## Exit codes

```text
0  Operation DONE
1  technical FAILED
2  deterministic BLOCKED gate
```

A BLOCKED run may write only the structured Operation report. It does not create a partial candidate structure, manifest, or mapping.

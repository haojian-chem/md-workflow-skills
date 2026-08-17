# chain_and_component_selection_validator scripts

## Entry point

```bash
python scripts/validate_selection.py \
  --config selection_validation_config.yaml
```

`validate_selection.py` independently recomputes the expected selected set from:

```text
classification_result.yaml + selection_spec.yaml
```

It does not accept manifest self-reports as sufficient evidence. It checks:

- source, classification, spec, candidate, manifest, mapping, and Operation-report provenance;
- exactly one selected model;
- exact selected atom/altLoc identity and source order;
- one-to-one complete atom mapping;
- coordinates, occupancy, B factor, element, and formal charge;
- selected confirmed explicit connections;
- requested/actual components, residue sets, relation partitions, counts, policies, and decision provenance;
- output format/path consistency.

PDB numeric fields use explicit serialization tolerances. MMCIF comparisons use tight numerical tolerances.

## Config contract

```text
schemas/selection_validation_config.schema.yaml
```

Required fields:

```yaml
schema_version: 1
selection_spec_path: /absolute/path/selection_spec.yaml
classification_result_path: /absolute/path/classification_result.yaml
candidate_structure_path: /absolute/path/selected_structure.pdb
selection_manifest_path: /absolute/path/selection_manifest.yaml
selection_mapping_path: /absolute/path/selection_mapping.yaml
operation_report_path: /absolute/path/chain_and_component_selection_report.yaml
validation_report_path: /absolute/path/chain_and_component_selection_validation_report.yaml
validation_result_path: /absolute/path/selection_validation_result.yaml
```

## Outputs

```text
schemas/selection_validation_report.schema.yaml
schemas/selection_validation_result.schema.yaml
```

A successful result confirms selection fidelity only. It does not claim that altLoc, completeness, protonation, or downstream topology-preparation checks have been completed.

The Validator writes validation evidence only inside the task work directory. It does not register artifact sets, update workstream state, or append project events; Manager performs those writes after one FAST validation of the combined candidates.

## Exit codes

```text
0  validation DONE and accepted
1  validation FAILED
2  validation BLOCKED because required inputs are incomplete
```

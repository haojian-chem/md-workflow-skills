---
name: chain_and_component_selection_validator
description: Independently validate that chain/component selection exactly matches the explicit v1.2 component set, preserves all selected coordinate objects and attributes, retains selected-side explicit connections, and provides complete one-to-one atom mapping and provenance.
---

# Chain and component selection validator

## 1. Purpose

This Validator is the dedicated gate for `chain_and_component_selection`.

It confirms selection fidelity only. It does not validate altLoc choice, residue completeness, protonation, chemical correctness of an upstream relation, or final structure-preparation readiness.

## 2. Runtime task unit

The enclosing task must use:

```text
mode: OPERATION_WITH_VALIDATOR
operation: chain_and_component_selection
validator: chain_and_component_selection_validator
```

The deterministic entry point is:

```bash
python scripts/validate_selection.py --config selection_validation_config.yaml
```

CLI/config details are owned by `scripts/README.md`.

## 3. Required inputs

The Validator requires:

```text
selection_spec.yaml
classification_result.yaml
selected structure candidate
selection_manifest.yaml
selection_mapping.yaml
Operation report
```

All inputs must be regular files and satisfy their schemas and recorded SHA-256 identities.

## 4. Independent recomputation

The Validator independently rebuilds the expected selected set from:

```text
classification_result.yaml + selection_spec.yaml
```

It does not accept manifest counts, selected IDs or relation lists as sufficient evidence.

The recomputed plan must agree with:

- requested and actual component IDs;
- selected and excluded residue IDs;
- preserved and excluded explicit relations;
- cross-boundary coordination relations;
- cross-boundary rejected covalent candidates;
- counts, policies and decision provenance.

## 5. Structural checks

The Validator checks:

1. exactly one selected model;
2. exact selected atom/altLoc set and source order;
3. complete one-to-one atom mapping;
4. chain, residue, atom, insertion-code, altLoc and element identity;
5. coordinates, occupancy, B factor and formal charge;
6. preservation of selected-side confirmed covalent and coordination connections;
7. absence of unselected coordinate objects;
8. output format/path consistency;
9. source/spec/classification/candidate/manifest/mapping/Operation-report provenance.

For MMCIF, numerical attributes use tight comparison tolerances. For PDB, the Validator applies explicit serialization tolerances for fixed-width rounded numeric fields and reports the tolerance use as a warning.

## 6. Outputs

The Validator writes:

```text
chain_and_component_selection_validation_report.yaml
selection_validation_result.yaml
```

Contracts:

```text
schemas/selection_validation_report.schema.yaml
schemas/selection_validation_result.schema.yaml
```

Accepted outcomes:

```text
SELECTION_VALIDATED
SELECTION_VALIDATED_WITH_WARNINGS
```

Failure outcomes include:

```text
INVALID_SELECTION_SPEC_COVALENT_BREAK
SELECTED_SET_MISMATCH
ATOM_MAPPING_MISMATCH
COORDINATE_OR_ATTRIBUTE_CHANGED
EXPLICIT_CONNECTION_MISMATCH
MANIFEST_OR_HASH_MISMATCH
OUTPUT_FORMAT_MISMATCH
VALIDATOR_INPUT_INCOMPLETE
SELECTION_VALIDATOR_INTERNAL_FAILURE
```

## 7. Artifact semantics

Only an accepted Validator result may mark the selected structure, manifest and mapping as `present_validated` in the shared task result.

The resulting STRUCTURE artifact is valid for advancing to:

```text
1.4 altloc_occupancy_resolution
```

It is not yet a fully prepared structure.

## 8. Permission boundary

The Validator writes validation evidence only inside the assigned task work directory. It must not register artifact sets, update Workstream state, write task records or append project events.

Manager performs those changes after one FAST validation of its combined result/artifact/state/event candidates.

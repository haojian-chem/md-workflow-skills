---
name: chain_and_component_selection
description: Deterministically select complete classified components from exactly one structure model, preserve all selected coordinate objects and explicit selected-side relations, and emit an unvalidated STRUCTURE candidate plus full selection provenance.
---

# Chain and component selection

## 1. Purpose

This Operation implements structure-preparation substep `1.3 chain_and_component_selection`.

It selects a user-approved set of complete v1.2 components. It does not perform chemical editing, bond breaking, residue-range extraction, atom filtering, altLoc resolution, identifier normalization, protonation, residue repair or topology generation.

Scientific selection semantics are owned by:

```text
references/selection_rules.md
```

## 2. Runtime task unit

The enclosing task must use:

```text
mode: OPERATION_WITH_VALIDATOR
operation: chain_and_component_selection
validator: chain_and_component_selection_validator
```

The deterministic Operation entry point is:

```bash
python scripts/select_structure.py --config selection_operation_config.yaml
```

The combined task-result builder is:

```bash
python scripts/build_subagent_result.py ...
```

CLI/config details are owned by `scripts/README.md`.

## 3. Authoritative inputs

The Operation requires:

```text
classification_result.yaml
selection_spec.yaml
source structure
```

The classification result must satisfy:

```text
result_status: COMPLETE
unresolved_items: []
summary.unresolved_item_count: 0
```

The selection spec must validate against:

```text
schemas/selection_spec.schema.yaml
```

Only `component_id` values materialized by v1.2 are selectable. Natural-language context, file names, chain-name conventions and implicit selectors are not selection evidence.

## 4. Preflight gates

Before writing a candidate, `select_structure.py` verifies:

1. config, spec and classification schemas;
2. source and classification SHA-256 identities;
3. exact selected model identity;
4. existence of every requested component and observed member residue;
5. complete confirmed covalent closure;
6. source/output path separation and no output overwrite;
7. output extension/format consistency;
8. PDB identifier representability when PDB is requested.

A failed gate writes a structured BLOCKED report when a report path is available. It does not create a partial structure, manifest or mapping.

## 5. Deterministic execution

The Operation:

1. expands each selected component to its observed `residue_ids`;
2. excludes `missing_residue_ids` from coordinate selection while preserving their upstream provenance;
3. blocks any confirmed `COVALENT_CONNECTION` crossing the selection boundary;
4. records cross-boundary metal coordination and rejected covalent candidates without auto-expanding the selected set;
5. copies complete selected residues with all atoms and altLocs in source order;
6. preserves coordinates, occupancy, B factor, element and formal charge within the selected output format;
7. reconstructs selected-side confirmed covalent and metal-coordination connections;
8. writes PDB only when identifiers are losslessly representable, otherwise blocks;
9. reparses the temporary output and verifies atom count and stable identity before atomic replacement.

## 6. Operation outputs

Successful execution writes:

```text
selected_structure.pdb | selected_structure.cif
selection_manifest.yaml
selection_mapping.yaml
chain_and_component_selection_report.yaml
```

Contracts:

```text
schemas/selection_manifest.schema.yaml
schemas/selection_mapping.schema.yaml
schemas/selection_operation_report.schema.yaml
```

The structure, manifest and mapping remain `present_unvalidated` until the dedicated Validator accepts them.

## 7. Operation outcome codes

Successful outcomes:

```text
SELECTION_APPLIED
SELECTION_APPLIED_WITH_WARNINGS
```

Deterministic blocking outcomes include:

```text
SELECTION_SPEC_MISSING_OR_INVALID
SELECTION_REFERENCES_UNKNOWN_OBJECT
SELECTION_BREAKS_CONFIRMED_COVALENT_LINK
OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS
SOURCE_OR_CLASSIFICATION_HASH_MISMATCH
OUTPUT_CONFLICT
```

Unexpected execution failure is reported as:

```text
SELECTION_INTERNAL_FAILURE
```

## 8. Shared result and Manager handoff

`build_subagent_result.py` emits a shared `subagent_result v2` only when:

- task mode and Skill references match this Operation/Validator pair;
- Operation status is `DONE`;
- Validator status is `DONE`;
- Validator outcome is `SELECTION_VALIDATED` or `SELECTION_VALIDATED_WITH_WARNINGS`;
- Validator explicitly covers the candidate, manifest and mapping hashes.

The resulting STRUCTURE artifact candidate contains the validated selected structure. Manifest and mapping remain validated task evidence referenced by the component results.

The Operation and builder must not modify:

```text
00_project_state/**
00_project_records/**
```

Manager owns artifact-set registration, one FAST validation of result/artifact/state/event candidates, atomic commit, event append and Workstream advancement.

## 9. Scope boundary

This Operation does not claim:

- altLoc resolution;
- heavy-atom completeness;
- protonation correctness;
- final structure-preparation validity;
- topology readiness.

Those checks remain with later Workflow substeps and dedicated Validators.

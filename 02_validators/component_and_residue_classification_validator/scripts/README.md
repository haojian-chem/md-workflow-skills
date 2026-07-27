# Component and residue classification scripts

The Validator uses a selected-model, five-stage deterministic pipeline:

```text
inspect_model_scope.py
→ model_scope.yaml

classify_structure.py
→ classification_observations.yaml
→ reference_manifest.yaml

check_possible_connections.py
→ relation_checks/possible_connections_result.yaml

check_possible_coordination.py
→ relation_checks/possible_coordination_result.yaml

build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md
```

The scripts never modify the input structure. The Agent performs preflight, supplies explicit configuration files and returns the resulting candidate records to Manager. It must not reproduce structure parsing, RTP/CCD comparison, geometry checks or result integration manually.

## 1. Model scope inspection

```bash
python scripts/inspect_model_scope.py \
  --structure <recognized-structure.pdb-or-cif> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <model_scope.yaml>
```

A single model is selected automatically. Multiple models produce `USER_SELECTION_REQUIRED`; after Manager records the user's choice, rerun with:

```text
--selected-model-id <model_id>
```

No residue classification is performed before the selected model is resolved.

## 2. Baseline classification

```bash
python scripts/classify_structure.py \
  --config <classification_config.yaml>
```

Internal module boundary:

```text
classification_engine.py
→ runtime facade, chain-grouping invariant and cross-stage output normalization

classification_engine_core.py
→ baseline classification implementation
```

The facade keeps structural entity/polymer facts authoritative while constructing baseline `chain_groups`. If residue topology classification is unresolved or conflicting, a structurally identified polymer or branched residue still remains in its structural chain. The original `ClassificationValue`, including null labels, `CONFLICT` status and evidence, is restored before observations are emitted. Conversely, an explicit structural nonpolymer entity is not promoted into a polymer chain solely because a project classification label says `POLYMER`.

For missing-residue evidence, the facade also normalizes cross-stage results:

- repeated reports with the same `issue_type`, `subject` and `resolution_status` are merged, preserving all distinct evidence;
- a missing residue without a resolvable author `source_resid` is not emitted as a formal `MISSING_EXPECTED` residue record;
- a missing-residue record whose target chain cannot be mapped to a `chain_index` is not counted as resolved;
- both cases use `MAPPING_UNRESOLVED` with an explicit reason in `missing_residue_checks`.

The YAML configuration supplies:

```text
structure path, hash, format and selected_model_id
classification mode: REGISTRY or FORCE_FIELD_ANALYSIS
optional project_residue_definitions.yaml
optional force-field root and explicit terminal RTP mappings
optional AF3 input/FASTA sequence references
CCD project snapshot, local reference directories, shared cache and retrieval policy
observations and reference-manifest output paths
```

The baseline pass:

- preserves residue and atom name case exactly;
- applies project definitions, exact Skill registries and entity context in `REGISTRY` mode;
- applies project definitions, exact RTP blocks and only then Skill fallback in `FORCE_FIELD_ANALYSIS` mode;
- records PDB/mmCIF missing residues from sequence/coordinate and explicit unobserved-residue evidence;
- skips AF3 missing-residue checks unless an AF3 input or sequence reference is supplied;
- checks standard-residue heavy atoms against CCD in `REGISTRY` mode and against the selected RTP template in force-field mode;
- checks nonstandard-residue heavy atoms against CCD in both modes;
- uses explicitly mapped N/C or 5′/3′ terminal RTP templates for terminal heavy-atom validation;
- marks multi-altLoc residues as `MULTIPLE_CONFORMATIONS` and does not perform their heavy-atom comparison;
- creates baseline `chain_groups` and only retains per-instance records for polymer/branched residues, missing residues and non-aggregated or exceptional components.

## 3. Possible covalent connections

```bash
python scripts/check_possible_connections.py \
  --config <possible_connections_check_config.yaml>
```

The checker reads `possible_connections.yaml`, enumerates every exact residue/atom instance combination, resolves explicit PDB/mmCIF connections, calculates configured distance ranges and records all supported, conflicting and missing-partner outcomes. It never creates a bond or changes classification.

## 4. Possible metal coordination

```bash
python scripts/check_possible_coordination.py \
  --config <possible_coordination_check_config.yaml>
```

The checker treats metal and donor endpoints as directional, validates exact elements, preserves `METAL_COORDINATION` as the relation type and records whether the project definition allows `promote_nonstandard_to_linked`. Geometry-only candidates remain pending until a user decision is recorded.

## 5. Result integration

```bash
python scripts/build_classification_result.py \
  --config <classification_result_build_config.yaml>
```

The builder:

- verifies that all source hashes and selected-model identities match;
- applies confirmed explicit relations;
- applies decisions tied to the exact hash of a previous confirmation file;
- promotes nonstandard components only for confirmed topology-forming relations;
- rebuilds final `chain_groups`;
- writes the remaining aggregated confirmation requests;
- writes a `COMPLETE` or `PENDING_USER_CONFIRMATION` result and a Markdown report.

The first integration pass normally has no decisions. A later pass uses new output paths plus a `decision_source` that references the previous `confirmation_requests.yaml` hash; old results are not overwritten.

## Exact-name and template rules

```text
HEM != Hem != hem
FE atom name != Fe element symbol
```

No script uppercases residue or atom names, performs alias lookup, uses regular expressions or selects a nearest name. `ccd_id` is either explicitly provided or exactly equal to `residue_name`.

In force-field mode, residue recognition is based only on exact `*.rtp` residue blocks. `residuetypes.dat`, `*.n.tdb`, `*.c.tdb` and `specbond.dat` are not applied in this version. A non-water exact RTP name defined more than once becomes a confirmation item. Multiple water-model RTP definitions are allowed, and ordinary water is not heavy-atom checked against RTP names.

## CCD lookup order

```text
existing project snapshot
→ configured local reference directories
→ shared cache
→ remote download when retrieval_policy is DOWNLOAD_MISSING
```

A valid external CCD file is copied into `reference_data/ccd/` and the project snapshot becomes the authoritative reference for the run. Files are accepted only after component-ID, atom-table, element and SHA-256 validation.

## Deterministic boundaries

The scripts:

- reject missing, empty and symlink inputs;
- verify input hashes and selected-model identity;
- use strict YAML duplicate-key parsing and Draft 2020-12 schema validation;
- finish all feasible scientific checks before returning aggregated confirmation requests;
- stop immediately only on technical invalidity that prevents a trustworthy result;
- use atomic output writes and refuse to overwrite different existing results;
- do not write `00_project_state/**` or `00_project_records/**`;
- do not choose the next Workflow task or ask the user questions directly.

## Exit codes

```text
0  deterministic processing completed
2  technical/configuration/schema/consistency failure
3  unexpected internal failure
```

## Dependencies

Install the versions declared in `requirements.txt`.

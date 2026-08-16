# MD Workflow Master Plan

Status: ACTIVE PLANNING BASELINE

This file records the current planning baseline for the MD Workflow. It is a planning artifact, not an implementation contract. Frozen stage architecture is authoritative for planning; detailed scientific execution remains owned by the corresponding Workflow / Operation / Validator Skills and references.

## 1. Top-level stage numbering

Confirmed top-level stages:

1. Structure preparation
2. Topology / parameterization
3. System construction / solvation
4. MD simulation
5. Analysis

Numbering semantics:

- `1.3` means the MD Workflow stage 1.3, i.e. the third sub-stage under `1 Structure preparation`.
- The same rule applies to `2.x`, `3.x`, `4.x`, and `5.x`.

---

## 2. Stage 1 — Structure preparation

Current defined sequence:

- 1.1 Structure source recognition
- 1.2 Component and residue classification
- 1.3 Chain and residue selection
- 1.4 Alternate conformation / occupancy resolution
- 1.5 Completeness check
- 1.6 Missing-region completion
- 1.7 Protein protonation assignment
- 1.8 Reorder and mapping
- 1.9 Structure preparation validation

Stage 1 execution-time applicability is determined by the relevant Step Skills and actual evidence. Manager planning does not mark conditional steps.

### Stage 1 → Stage 2 chain-assignment handoff

Workflow 1 final structure organization must provide stable heavy-atom identity/order and the chain assignment consumed by Stage 2.

For topology-linked nonstandard units:

```text
all standard-side linked residues belong to one standard chain
→ linked nonstandard unit does not receive a separate chain; it is assigned to that chain

standard-side linked residues span multiple standard chains
→ linked nonstandard unit receives its own chain identity
```

This chain identity is distinct from later GROMACS `moleculetype` organization. Stage 2 may merge multiple chains into one covalently connected moleculetype while preserving chain identity.

---

## 3. Stage 2 — Topology / parameterization

### 3.1 Status

**Stage 2 architecture is frozen.**

Frozen sequence:

1. `2.1 Parameterization environment and assignment`
2. `2.2 Standard residue topology generation`
3. `2.3 Topology-linked nonstandard parameterization`
4. `2.4 Independent nonstandard parameterization`
5. `2.5 Topology integration and assembly`
6. `2.6 Topology validation`

The authoritative architecture record is:

`00_authoring/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

Detailed 2.5 linked integration rules are owned by:

- `02_operations/topology_integration_and_assembly/SKILL.md`
- `02_operations/topology_integration_and_assembly/references/topology_integration_rules.md`
- `02_operations/topology_integration_and_assembly/references/parameter_definition_deduplication.md`

### 3.2 Routing principle

Stage 2 routes work by component/topology ownership, not by parameter complexity.

Do not create a generic `Special / custom parameter generation` stage.

Methods such as DFT, RESP/RESP2, Multiwfn, Sobtop, Seminario, GAFF, metal-specific handling, or future custom tools remain internal methods of the appropriate Step rather than separate workflow stages.

### 3.3 2.1 Parameterization environment and assignment

Purpose:

- establish the set of force-field / parameter-definition sources used by the system;
- assign actual classified objects to the downstream topology acquisition / parameterization route;
- do not reclassify 1.2 objects.

Assignment baseline:

- all `STANDARD_RESIDUE` → 2.2;
- each **topology-linked nonstandard unit** → 2.3;
- each `INDEPENDENT_NONSTANDARD` residue name/type → 2.4;
- FF-complete solvent/ion definitions → direct 2.5 integration;
- solvent/ion without complete definition → 2.4 type handling.

A topology-linked nonstandard unit may contain one or multiple nonstandard residues when they must be jointly parameterized as one linked chemical unit.

### 3.4 2.2 Standard residue topology generation

Purpose:

- generate actual all-atom molecule topology/structure for all standard residues from the selected parameterization environment;
- perform standard-residue hydrogenation;
- emit standard-only structure/topology plus mapping.

Core result categories:

```text
standard-only .gro
standard-only .top
standard molecule .itp file(s)
*.map
```

2.2 may internally split `pdb2gmx` processing groups; one-chain-one-run is not a default rule.

### 3.5 2.3 Topology-linked nonstandard parameterization

Processing unit:

```text
one topology-linked nonstandard unit
→ one 2.3 processing unit
```

A unit may contain one or multiple nonstandard residues.

Purpose:

- build the linked parameterization model;
- consume standard-side all-atom fragments from 2.2 while keeping their relative order;
- hydrogenate only the nonstandard part;
- identify standard-side atoms incompatible with the linked state;
- add parameterization caps where required;
- execute DFT / RESP(2) / topology generation;
- emit linked-site modification information for 2.5.

Protein-model boundary baseline: retain the directly attached standard residue, extend across peptide bonds toward neighboring residues, prefer final cuts on suitable C-C single bonds, and cap with H. Detailed nucleic-acid boundary rules remain a local scientific refinement rather than a Stage 2 architecture question.

### 3.6 2.4 Independent nonstandard parameterization

Purpose:

- parameterize each independent nonstandard type once;
- apply that type topology to all current-system instances.

Output levels:

```text
type-level:
  mol2 / chg / itp

system-instance-level:
  gro / map
```

### 3.7 2.5 Topology integration and assembly

Purpose:

- consume 2.2 standard, 2.3 linked units, 2.4 independent types/instances, and FF-direct solvent/ion definitions;
- determine final GROMACS moleculetype organization while preserving upstream chain identity;
- determine the final atom set and final all-atom order before topology migration;
- freeze one canonical final atom index and final map;
- generate each final molecule `.itp` by molecule-level topology integration;
- collect/deduplicate/conflict-check global/type-level parameter definitions into one consolidated parameter-definition `.itp`;
- assemble `final_system.top` and write `final_system.gro` using the already frozen canonical final atom order.

Critical ordering rule:

```text
final topology organization
→ final atom set
→ final all-atom order
→ canonical final atom index + final.map
→ molecule-level topology integration / final molecule .itp
→ global parameter-definition consolidation
→ final_system.top
→ final_system.gro using the same canonical order
```

For confirmed covalent connectivity, all covalently connected standard components and linked units belong to one final GROMACS moleculetype. This may merge multiple source chains but does not erase chain identity.

### 3.8 2.6 Topology validation

Purpose:

- validate the complete 2.5 package without rebuilding it;
- verify topology package completeness, internal topology consistency, linked modifications, map consistency, charge/connectivity sanity, topology-coordinate atom-by-atom consistency, and GROMACS preprocessing acceptance.

`gmx grompp` success is necessary evidence but is not sufficient by itself for Stage 2 validation.

2.6 does not silently repair topology; failures route back to the relevant upstream Step.

### 3.9 Stage 2 shared mapping rule

2.2–2.5 mapping follows:

```text
generated/output atom → source provenance
```

Core fields:

```yaml
output_atom_index:
output_atom_name:
output_residue_name:
output_residue_number:
origin: SOURCE | ADDED_H | CAP
source_atom_serial:
```

`DELETED_BY_LINK` is not a map state. Connectivity is read from topology/mol2 rather than duplicated in the map.

---

## 4. Stage 3 — System construction / solvation

### 4.1 Status

**Stage 3 architecture is frozen.**

Frozen catalog:

1. `3.1 Periodic box construction`
2. `3.2 Solvent addition`
3. `3.3 Ion addition`

Default scientific route:

```text
3.1 Periodic box construction
→ 3.2 Solvent addition
→ 3.3 Ion addition
```

The numbering records the default scientific order rather than a once-only execution constraint. Each Stage 3 step may appear zero, one, or multiple times as separate Task Sheet substep instances when required by the current system or explicit task scope.

The authoritative Stage 3 architecture record is:

`00_authoring/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

Stage 3 intentionally does not define separate system-construction-specification, final-assembly, or stage-level-validation steps. The Task Sheet records the actual operation sequence, and each operation performs its own required local validation.

### 4.2 3.1 Periodic box construction

Current-version execution tool:

`gmx editconf`

Processing object:

- any validated `.gro` file;
- record the `.top` / `.itp` files associated with that `.gro` for downstream handoff.

Current arg tendency centers on:

- `-c` as the normal centering tendency;
- `-box` when explicit box dimensions are required;
- `-d` when a solute/system-to-box-boundary distance is specified.

Current version does not use Agent-written coordinate/box-vector modification as part of 3.1. More complex direct structure/box modification is reserved for a future update.

### 4.3 3.2 Solvent addition

Current-version execution tool:

`gmx solvate`

The current validated `.gro` and its associated topology package are consumed together with the requested solvent definition. Repeated 3.2 instances are allowed for workflows that add solvent in multiple passes.

Arg tendency includes:

- `-cp` current validated `.gro`;
- `-cs` requested solvent coordinate/template;
- `-p` current topology, with `sys.top` as the preferred Stage 3 basename when naming is under workflow control;
- `-o` new solvated `.gro`.

3.2 normally inherits the existing box rather than replacing the role of 3.1.

### 4.4 3.3 Ion addition

3.3 is one workflow step with a fixed two-command internal sequence:

```text
Skill-provided genion .mdp template
→ gmx grompp
→ genion.tpr
→ gmx genion
→ ionized .gro + updated topology
```

The Skill should provide a dedicated minimal `.mdp` template used only to generate the temporary `.tpr` required by `genion`; it does not carry Stage 4 EM/equilibration/production semantics.

`gmx grompp` arg tendency:

- `-f` Skill-provided genion `.mdp`;
- `-c` current validated `.gro`;
- `-p` current topology, commonly `sys.top`;
- `-o` temporary `genion.tpr`.

`gmx genion` arg tendency:

- use `-neutral` when the task requires an electrically neutral system;
- for biomolecular systems, if the user has not specified another salt concentration, tend toward `-conc 0.154`;
- determine `-pname` / `-nname` from the current ion definitions and task requirements;
- select the actual bulk-solvent replacement group from the current system rather than hard-coding `SOL`.

Each repeated 3.3 instance regenerates its own `.tpr` from the current structure/topology state before running `genion`.

### 4.5 Shared Stage 3 naming / command policy

`sys.top` is the preferred Stage 3 topology basename when naming is under workflow control. An existing validated topology with another basename is not renamed merely to satisfy this preference.

Stage 3 Step Skills should express **arg tendency** rather than rigid command templates. Priority is:

```text
explicit user requirement
> current Task Sheet requirement
> actual current object/state
> Step Skill arg tendency
> GROMACS default
```

---

## 5. Stage 4 — MD simulation

### 5.1 Status

**Stage 4 run-unit architecture is frozen; detailed validation design is deferred.**

Frozen sub-stage catalog:

1. `4.1 Energy minimization`
2. `4.2 Equilibration`
3. `4.3 Production simulation`

Authoritative architecture record:

`00_authoring/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md`

### 5.2 Execution-layer / execution-object model

Stage 4 uses a different planning/execution representation from Stages 1–3.

```text
sub-stage = execution layer
run unit = execution object
```

Mapping:

```text
4.1 → em.*
4.2 → nvt.* / npt.*
4.3 → md.*
```

The Task Sheet does not represent Stage 4 as a serial `4.1 → 4.2 → 4.3` list. It records a **planned run route** composed of the actual intended simulation segments.

A planned route entry does not receive a formal `em.N / nvt.N / npt.N / md.N` identity until that entry begins processing.

### 5.3 Planned run route and formal identity

When a planned route entry begins, Stage 4 first determines whether it can bind an existing reusable run unit, continue an existing unfinished run unit, or must instantiate a new run unit.

Formal run-unit identities are project-level:

```text
em.N
nvt.N
npt.N
md.N
```

The prefix is sufficient for first-level classification. Detailed scientific settings are read from the actual `.mdp` rather than duplicated in the project-level run-unit list.

For a new run unit, the formal identity is locked and registered immediately before execution. Gaps in historical numbering are not recycled.

### 5.4 Project-level `run_unit.yaml`

The project keeps one centralized `run_unit.yaml` containing only instantiated run units. It supports cross-task and cross-conversation discovery.

The YAML root is directly a list. Minimum fields are:

```yaml
- run_unit_id: em.1
  start_from_run_unit_id:
  status: 已完成
  path: /absolute/storage/directory/
```

No separate `run_unit_type` is stored. No detailed `.mdp` settings are copied into this file.

Allowed maintenance statuses are:

```text
未完成
已完成
已终止
```

`path` is the complete storage directory used to locate/query the run-unit files. It does not prescribe the execution working directory. Multiple run units may share the same storage directory.

`start_from_run_unit_id` records inheritance from another Stage 4 run unit. It may be empty for a run that begins directly from a pre-Stage-4 object.

### 5.5 Reuse / continuation / new run boundary

Before creating a new run unit, Stage 4 checks instantiated candidates. Candidate reuse considers predecessor-state compatibility, topology/parameter-package compatibility, intended requirement versus actual effective settings, and result validity. Detailed settings are determined from real run artifacts such as `.mdp`.

Technical continuation that completes the original run remains the same run unit. A scientifically new simulation segment becomes a new run unit.

The project-level `run_unit.yaml` is a discovery/maintenance list, not a simulation plan and not sufficient by itself to prove scientific reuse.

### 5.6 Explicitly rejected Stage 4 planning/runtime structures

Do not use as the default Stage 4 model:

- a Task Sheet route expressed only as `4.1 → 4.2 → 4.3`;
- one ordinary Task Sheet substep per run unit;
- `simulation_plan.yaml`;
- historical `expected_route.yaml`;
- one `run_unit.yaml` per run-unit directory;
- `simulation_output_index`;
- formal run-unit IDs allocated during initial planning;
- `run_unit_type` duplicated in `run_unit.yaml`;
- detailed `.mdp` settings duplicated in `run_unit.yaml`;
- a no-information top-level `run_units:` wrapper.

### 5.7 Deferred Stage 4 work

The following are intentionally left for other discussions:

- detailed validation rules for EM/NVT/NPT/MD run units;
- Validator organization and validation evidence semantics;
- detailed `.mdp` generation/editing architecture;
- implementation-level commands/templates and execution refinements.

---

## 6. Stage 5 — Analysis

Top-level stage confirmed.

Sub-stage decomposition: not yet frozen.

---

## 7. Runtime architecture baseline

The default runtime architecture is Lightweight Runtime v2:

- Manager creates/locates tasks and performs initial planning or explicit replanning;
- Task Execution Agent owns long-lived execution, per-step reuse checks, execution, validation, recording, and dynamic future-step adjustment;
- no default transaction/event/workstream runtime engine;
- Operation preflight and dedicated scientific validation remain available where needed;
- deterministic Tools are preferred for deterministic transformations but do not recreate a transaction engine.

The planning index is only a lightweight initial-planning catalog and must not contain scientific applicability rules, reuse rules, schemas, commands, validator logic, or runtime state.

Stage 4 is a stage-specific exception to the normal sub-stage-sequence Task Sheet representation: the Task Sheet stores a planned run route while Stage 4 sub-stages remain the execution layers selected for each run unit.

---

## 8. Current planning state

Frozen:

- top-level Stage 1–5 numbering semantics;
- Workflow 1 step catalog;
- Workflow 1 / 1.3 Chain and Residue Selection scientific design;
- Workflow 2 / Stage 2 architecture and six-step catalog;
- Stage 2 topology-linked nonstandard unit model;
- Stage 1 → Stage 2 chain-assignment handoff principle;
- Stage 2 map semantics;
- Stage 2 final all-atom ordering/index timing;
- 2.5 molecule-level integration ownership and global parameter-definition consolidation boundary;
- 2.6 validation boundary;
- Workflow 3 / Stage 3 architecture and three-step catalog;
- Stage 3 default route `3.1 → 3.2 → 3.3` with repeatable task-sheet instances;
- Stage 3 current-version GROMACS execution boundary and arg-tendency policy;
- Workflow 4 / Stage 4 three-sub-stage execution-layer catalog;
- Stage 4 Task Sheet planned-run-route representation;
- Stage 4 formal run-unit identity timing and centralized `run_unit.yaml` maintenance model;
- Stage 4 continuation versus new-run-unit boundary.

Still to plan/freeze:

- Stage 4 detailed validation design;
- Stage 4 detailed `.mdp` generation/editing and execution implementation;
- Stage 5 sub-stage plan;
- implementation details and Validators/Tools for Stage 2 steps not yet implemented;
- Stage 3 detailed Step Skill implementation/templates/validation refinements;
- nucleic-acid-specific 2.3 model-cut/capping rules where needed.

## 9. Immediate next planning task

Stage 2 and Stage 3 architecture are closed for ordinary redesign. Stage 4 run-unit architecture is also closed for ordinary redesign; its deferred validation and implementation details should be handled separately.

Architecture-level planning can proceed to Stage 5 when requested.

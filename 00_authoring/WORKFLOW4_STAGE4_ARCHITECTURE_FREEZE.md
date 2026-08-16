# Workflow 4 / Stage 4 architecture freeze

Status: FROZEN EXCEPT VALIDATION DETAILS

This file records the agreed Stage 4 architecture for MD simulation. It freezes the planning/execution object model and run-unit maintenance model discussed for Workflow 4. Validation design is intentionally deferred to a separate discussion and is not defined here.

## 1. Stage 4 catalog

Stage 4 keeps three sub-stages:

1. `4.1 Energy minimization`
2. `4.2 Equilibration`
3. `4.3 Production simulation`

Sub-stage semantics:

- `4.1` is the execution layer for `em.*` run units.
- `4.2` is the execution layer for `nvt.*` and `npt.*` run units.
- `4.3` is the execution layer for `md.*` run units.

A sub-stage is an **execution layer**. A run unit is the **execution object**. These are not the same level.

## 2. Stage 4 Task Sheet planning model

Stage 4 differs from Stages 1–3.

For Stages 1–3, the Task Sheet normally represents execution as a sequence of workflow sub-stages. For Stage 4, the Task Sheet records a **planned run route composed of run-plan entries**, not a serialized `4.1 → 4.2 → 4.3` sub-stage list.

Conceptually, a task may plan:

```text
EM
→ NVT 300 K
→ NPT 300 K / 1 bar
→ NPT restraint release
→ MD 100 ns
```

The planned route may contain any number of EM/NVT/NPT/MD entries required by the simulation protocol.

The Task Sheet is the plan source. Do not create a separate `simulation_plan.yaml` or restore the historical `expected_route.yaml`.

A lightweight planned-route representation may record, for each planned entry:

- order;
- run class (`EM`, `NVT`, `NPT`, `MD`);
- key requirement sufficient to identify the intended segment without duplicating the complete `.mdp`;
- bound run unit, initially empty and filled only after a formal run unit is bound or created.

The exact Task Sheet formatting is implementation detail; the architectural requirement is that the route is run-unit-oriented rather than sub-stage-oriented.

## 3. Formal run-unit identity

Formal run units use project-level identities:

```text
em.N
nvt.N
npt.N
md.N
```

The prefix provides the first-level run classification. Do not duplicate this as a separate `run_unit_type` field. More detailed simulation semantics are read from the actual `.mdp` when needed.

A planned route entry does **not** receive a formal `em.N / nvt.N / npt.N / md.N` identity during planning.

Formal identity is locked only when that planned entry begins processing and the system has determined whether to:

1. bind an existing reusable run unit;
2. continue an existing unfinished run unit;
3. instantiate a new run unit.

For a new run unit, allocate the next number for the relevant prefix after inspecting the project-level run-unit list. Do not recycle gaps in old numbering.

Identity must be registered immediately after locking and before execution begins so that concurrent or later conversations do not allocate the same identity.

## 4. Project-level `run_unit.yaml`

The project maintains one project-level `run_unit.yaml` for instantiated Stage 4 run units. It supports cross-task and cross-conversation discovery and maintenance.

`run_unit.yaml` is not a simulation plan and does not list future, uninstantiated planned-route entries.

The YAML root is directly a list. Do not add a no-information `run_units:` wrapper.

Minimum record:

```yaml
- run_unit_id: em.1
  start_from_run_unit_id:
  status: 已完成
  path: /absolute/path/to/unit/storage/

- run_unit_id: nvt.1
  start_from_run_unit_id: em.1
  status: 已完成
  path: /absolute/path/to/unit/storage/
```

Required fields:

- `run_unit_id`
- `start_from_run_unit_id`
- `status`
- `path`

Do not add `run_unit_type`; the run-unit prefix already supplies the first-level type.

Do not copy detailed `.mdp` parameters into `run_unit.yaml`.

### 4.1 `start_from_run_unit_id`

This records Stage 4 run-unit state inheritance.

For a run that starts directly from an object outside Stage 4, such as the Stage 3 final system, the field may be empty/null. The external starting object remains recoverable from the task context and actual inputs; the run-unit list does not expand into a generic lineage registry.

### 4.2 `status`

Allowed project-level maintenance states:

```text
未完成
已完成
已终止
```

Planned but not yet instantiated runs are not run units and therefore do not use `待执行` in `run_unit.yaml`.

Detailed transient conditions such as running, interrupted, failed, or continuing are not duplicated as additional index states; when needed they are determined from the run files and task execution record.

### 4.3 `path`

`path` is the **complete storage directory path for locating/querying that run unit's files**.

It is a discovery/location field, not an instruction for the working directory used during execution.

Multiple run units may share the same storage directory. Their files are distinguished by the formal run-unit identity and the actual filenames.

## 5. Binding a planned route entry to a run unit

When a planned route entry begins processing:

```text
read current planned run entry
↓
determine current intended run class and requirement
↓
determine the actual predecessor state
↓
read project run_unit.yaml
↓
locate candidate instantiated run units
↓
inspect candidate files as needed
├─ reusable completed run exists
│  → bind existing run unit
├─ matching unfinished run exists and should be continued
│  → bind/continue existing run unit
└─ no usable run exists
   → allocate new formal run-unit identity
   → register it immediately as 未完成
   → execute it
↓
record the bound run-unit identity in the Task Sheet planned route
```

The project-level list is a candidate-discovery/maintenance layer. Its contents alone are not sufficient to prove scientific reuse; deeper comparison reads the actual run files, especially `.mdp`, and other required evidence.

A run unit may be bound by more than one Task Sheet when reuse is valid. Reuse does not create a duplicate run-unit identity merely to make the current task own a copy.

## 6. Shared reuse boundary

Before instantiating a new run unit, candidate reuse should consider at least:

- predecessor state compatibility;
- topology/parameter package compatibility;
- intended simulation requirement versus the candidate's actual effective settings;
- whether the existing run-unit result is valid for reuse.

The actual effective settings are determined from run artifacts such as the real `.mdp`; they are not duplicated into `run_unit.yaml`.

Detailed validation criteria are intentionally deferred and are not frozen by this document.

## 7. Continuation versus a new run unit

Technical continuation that is still completing the original scientific run remains the **same run unit**.

Example:

```text
md.4 target = 100 ns
run interrupted at 63 ns
checkpoint continuation to 100 ns
→ still md.4
```

A new scientific simulation segment is a **new run unit**.

Example:

```text
md.4 completed its planned 100 ns
later decision: add another 100 ns segment
→ new planned MD entry
→ when started, instantiate/bind a new md.N
```

The same principle applies to EM/NVT/NPT segments.

Historical semantics retained where applicable:

- append/technical continuation → same run unit;
- a scientifically new segment or a no-append new run → new run unit;
- failure by itself does not create a separate `*.failed` run unit.

## 8. Sub-stage execution boundary

Each Stage 4 sub-stage owns execution of its corresponding run-unit class:

```text
4.1 → em.*
4.2 → nvt.* / npt.*
4.3 → md.*
```

The common execution shape is conceptually:

```text
current state + topology package + run requirement
↓
prepare/select the run .mdp
↓
gmx grompp
↓
gmx mdrun
↓
run-specific validation
```

The sub-stage does not own the global planned run route. The Task Sheet owns that route and may be adjusted dynamically as execution evidence changes.

Detailed `.mdp` generation/tool design is not frozen here beyond the principle that the actual `.mdp` is the authoritative detailed simulation setting record.

## 9. Explicitly rejected architecture

Do not use the following as the Stage 4 default model:

- serial Task Sheet route represented only as `4.1 → 4.2 → 4.3`;
- one full ordinary Task Sheet substep per run unit;
- separate `simulation_plan.yaml`;
- historical `expected_route.yaml`;
- one `run_unit.yaml` per run-unit directory;
- `simulation_output_index`;
- formal run-unit IDs allocated during initial planning;
- `run_unit_type` duplicated in `run_unit.yaml`;
- detailed `.mdp` settings copied into `run_unit.yaml`;
- a top-level `run_units:` wrapper when `run_unit.yaml` contains only the run-unit list.

## 10. Deferred to other discussions

The following are intentionally **not** decided by this freeze and should be handled in other conversations:

- detailed validation rules for `em.*`, `nvt.*`, `npt.*`, and `md.*`;
- how validation results are represented beyond the already frozen project-level run-unit status values;
- Validator/Skill organization for Stage 4 validation;
- exact `.mdp` generation/editing Tool architecture;
- implementation-level command arguments and templates;
- Stage 5 analysis architecture.

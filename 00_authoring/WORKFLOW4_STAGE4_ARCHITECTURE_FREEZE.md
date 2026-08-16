# Workflow 4 / Stage 4 architecture freeze

Status: FROZEN

This file records the agreed Stage 4 architecture for MD simulation. It freezes the planning/execution object model, run-unit maintenance model, validation ownership, and the common implementation boundaries agreed before the first Stage 4 Skill implementation.

Detailed execution guidance is owned by:

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

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

Stage 4 is physically organized as one parent Skill with three child Skills under `04_md_simulation/`; it is not physically split into separate `01_workflows/` and `02_operations/` directories.

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

One planned route entry normally binds one formal run unit. If the originally bound unit later cannot be used and a new unit is required, the entry is rebound to the new unit. The old unit remains in `run_unit.yaml`; no separate `attempts` list is introduced.

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

The project maintains one project-level:

```text
04_md_simulation/run_unit.yaml
```

for instantiated Stage 4 run units. It supports cross-task and cross-conversation discovery and maintenance.

`run_unit.yaml` is not a simulation plan and does not list future, uninstantiated planned-route entries.

The YAML root is directly a list. Do not add a no-information `run_units:` wrapper.

Minimum record:

```yaml
- run_unit_id: em.1
  start_from_run_unit_id:
  status: 已完成
  path: /project/04_md_simulation/em.1/

- run_unit_id: nvt.1
  start_from_run_unit_id: em.1
  status: 已完成
  path: /project/04_md_simulation/nvt.1/
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

`path` is the **complete directory path of that specific run unit**.

For example:

```text
/project/04_md_simulation/md.2/
```

Multiple run-unit directories may share the same Stage 4 parent directory. Each `path` still points to the corresponding run unit's own complete directory.

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
- whether the existing run-unit result has passed the corresponding child Skill checks.

The actual effective settings are determined from run artifacts such as the real `.mdp`; they are not duplicated into `run_unit.yaml`.

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

Each Stage 4 child Skill owns execution of its corresponding run-unit class:

```text
4.1 → em.*
4.2 → nvt.* / npt.*
4.3 → md.*
```

The common execution shape is:

```text
current state + topology package + run requirement
↓
generate / adjust the final run .mdp
↓
gmx grompp
↓
confirm the expected .tpr
↓
generate gmx_mdrun.sh
↓
gmx mdrun
↓
run-specific validation
```

`.mdp` generation is part of the corresponding 4.1/4.2/4.3 Skill; Stage 4 does not create a separate generic MDP-generation sub-stage.

The final actual `.mdp` is the authoritative detailed simulation setting record.

`grompp` warnings must be inspected and judged. Blind use of `-maxwarn` merely to force preprocessing through is prohibited.

`gmx_mdrun.sh` is generated only after successful `grompp` and confirmation of the intended `.tpr`. It contains the actual `gmx mdrun` command only; no metadata/status prose and no shebang are added. It is executed with `bash gmx_mdrun.sh`.

Run-specific option tendencies and validation details are owned by the child Skills.

## 9. Validation organization

Stage 4 does **not** create separate Validator Skills for 4.1/4.2/4.3.

Run validation is directly owned by the corresponding child Skill:

```text
4.1 Energy minimization   → EM checks
4.2 Equilibration         → NVT/NPT checks
4.3 Production simulation → production checks
```

A common bonded-geometry screening rule applies to the final `.gro`:

- bond / constraint terms with a clear reference distance: `|r - r0| > 0.08 nm` is flagged as significant;
- angle terms with a clear reference angle: `|θ - θ0| > 30°` is flagged as significant;
- SETTLE and other fixed-geometry definitions are checked against their own reference geometry;
- other bonded functions are interpreted according to their actual function definition rather than mechanically applying the ordinary bond/angle thresholds.

These are screening thresholds for obvious structural abnormalities, not universal force-field quality criteria.

## 10. Project result registration

Stage 4 registers the project-level `run_unit.yaml` in `project_result_index.md`:

```text
path: complete path to 04_md_simulation/run_unit.yaml
description: Stage 4 project-level index of instantiated run units
```

Individual `.mdp/.tpr/.gro/.cpt/.xtc/.edr` files and individual run-unit directories are not separately registered as project-level results.

## 11. Explicitly rejected architecture

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
- a top-level `run_units:` wrapper when `run_unit.yaml` contains only the run-unit list;
- an `attempts` layer for replacement/retry run units;
- separate Stage 4 Validator Skills.

## 12. Remaining work

Stage 4 architecture and first-pass Skill guidance are frozen. Remaining work is implementation validation, representative execution testing, and evidence-driven local correction. Stage 5 analysis architecture remains separate.

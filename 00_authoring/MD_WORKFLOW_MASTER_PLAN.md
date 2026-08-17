# MD Workflow Master Plan

Status: ACTIVE CURRENT BASELINE

本文件只保存 MD Workflow 的**当前阶段目录、冻结状态和权威文件入口**。具体科学规则不在这里重复；发生冲突时，以对应当前 Stage/main Skill 和明确 architecture-freeze 文件为准。

## 1. Top-level numbering

固定顶层阶段：

1. Structure preparation
2. Topology / parameterization
3. System construction / solvation
4. MD simulation
5. Analysis

编号语义：`1.3` 表示整个 MD Workflow 的第 1.3 阶段；`2.4`、`3.2`、`4.1`、`5.1` 同理。

## 2. Current Skill organization rule

新科研 Skill 默认采用：

```text
main Skill
+ references when detail is long
+ supporting Skill only when complexity and a clear boundary justify it
```

不再强制 Workflow / Operation / Validator 分类。

仓库中现存 `01_workflows/`、`02_operations/`、`02_validators/` 是历史布局/迁移中的当前路径，不是新 Skill 的强制模板。后续迁移以实际职责边界为准，不为了目录统一一次性重构全部现有 Skill。

## 3. Stage 1 — Structure preparation

Status: DEFINED; guide implementation exists, representative validation/refinement continues.

Catalog:

```text
1.1 Structure source recognition
1.2 Component and residue classification
1.3 Chain and residue selection
1.4 Alternate conformation / occupancy resolution
1.5 Completeness check
1.6 Missing-region completion
1.7 Protein protonation assignment
1.8 Reorder and mapping
1.9 Structure preparation validation
```

Current Stage 1 guide entry remains at its historical path:

`01_workflows/structure_preparation_workflow/SKILL.md`

Manager planning catalog:

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

Stage 1 current scientific content is owned by the current guides at their existing paths. Do not infer authoring role or future physical layout from those historical directory names.

## 4. Stage 2 — Topology / parameterization

Status: ARCHITECTURE FROZEN; implementation remains partial.

Catalog:

```text
2.1 Parameterization environment and assignment
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

Architecture authority:

`00_authoring/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

Implemented detailed work currently includes the existing guide:

`02_operations/topology_integration_and_assembly/SKILL.md`

This path is historical placement, not a requirement that future Stage 2 Skills use an Operation directory.

## 5. Stage 3 — System construction / solvation

Status: ARCHITECTURE FROZEN; detailed Skill implementation/templates remain pending/refining.

Catalog:

```text
3.1 Periodic box construction
3.2 Solvent addition
3.3 Ion addition
```

Default scientific order:

```text
3.1 → 3.2 → 3.3
```

Architecture authority:

`00_authoring/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

The IDs express default scientific order, not a once-only constraint; Task Sheet instances may repeat when required.

## 6. Stage 4 — MD simulation

Status: ARCHITECTURE AND FIRST-PASS GUIDES FROZEN; representative execution validation remains pending.

Execution-layer catalog:

```text
4.1 Energy minimization   → em.*
4.2 Equilibration         → nvt.* / npt.*
4.3 Production simulation → md.*
```

Current authority:

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

Architecture record:

`00_authoring/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md`

Stage 4 uses one integrated main Skill plus supporting run-type Skills because those run types have clear, complex execution boundaries. This is a scientific/maintenance choice, not a Workflow/Operation classification requirement.

Stage 4 is a stage-specific Task Sheet exception:

```text
sub-stage = execution layer
run unit = execution object
```

Task Sheet records a planned run route. Formal `em.N / nvt.N / npt.N / md.N` identity is assigned only when a planned entry starts processing.

Project-level run-unit discovery/maintenance file:

`<project_root>/04_md_simulation/run_unit.yaml`

Current minimum record:

```yaml
- run_unit_id: md.1
  start_from_run_unit_id: npt.1
  status: 已完成
  path: /full/path/to/run-unit-directory/
  top: /full/path/to/main.top
```

`path` is the full storage directory for lookup; it does not prescribe execution working directory.

`top` is the full path of the main `.top` actually used by that run unit's `grompp`. It supports downstream topology lineage checks, including Stage 5 `.ndx` reuse across different TPRs.

Validation is owned by the corresponding result-producing Skill; Stage 4 does not add a generic validation layer.

## 7. Stage 5 — Analysis

Status: ARCHITECTURE AND FIRST-PASS MAIN GUIDE FROZEN; concrete analysis-capability population and representative validation remain pending.

Catalog:

```text
5.1 Analysis planning and orchestration
```

Current authority:

```text
05_analysis/SKILL.md
05_analysis/references/analysis_tool_inventory.yaml
```

Architecture record:

`00_authoring/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

Stage 5 uses one integrated main Skill. It is not split into `01_workflows/analysis_workflow` and `02_operations/analysis_planning_and_orchestration`.

Manager creates the Task Sheet `5.1` entry and preserves the user's stated analysis goal/object/constraints. Stage 5 main Skill expands that requirement into the concrete plan, performs the Stage 5 reuse query/check, discovers capabilities through its inventory, and orchestrates concrete analysis Skills / prepared-input producers.

5.1 plan items use fixed local integer numbering and the minimum record:

```text
编号
tool
inputs
settings
status
path
```

Plan-item statuses:

```text
未完成
已完成
已终止
```

Project-level prepared-input indexes:

```text
<project_root>/05_analysis/indexes/
├── trajectory_index.yaml  # maintained by trjconv capability owner
└── ndx_index.yaml         # maintained by make_ndx capability owner
```

5.1 queries and verifies these indexes but does not own the lifecycle of the files they index.

Each concrete analysis Skill/Tool validates its own output data. Project-level result registration records which objects received which analyses and provides a pointer to the corresponding Task Sheet / 5.1 plan item for details.

## 8. Runtime architecture baseline

Default runtime architecture:

`00_authoring/lightweight_runtime_v2_spec.md`

Core rule:

```text
Manager
→ task location / creation / initial planning
→ Task Sheet handoff
→ long-lived Task Execution Agent
→ current main Skill + only needed supporting material
```

Do not restore the historical Workstream / route / event / runtime-task / transaction engine as default runtime.

Manager initial planning authority:

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

## 9. Authority and stale-file rule

For current work, use this precedence:

```text
current Skill / Tool guide
> matching architecture-freeze record
> this Master Plan / SYNC_STATUS
> historical validation, redesign, benchmark, Legacy Runtime files
```

A historical file remaining in Git does not make it a current design source. Files explicitly marked `SUPERSEDED` or `LEGACY` are history-only and must not be used to reconstruct current interfaces.

## 10. Current remaining work

Architecture-level ordinary redesign is closed for Stages 2–5 unless new execution evidence requires local correction.

Current work is mainly:

- Stage 1 representative validation/refinement and gradual layout cleanup when useful;
- Stage 2 missing Skill/Tool implementation under current main-Skill model;
- Stage 3 Skill/template/validation implementation under current main-Skill model;
- Stage 4 representative execution validation;
- Stage 5 concrete analysis-capability inventory population, `trjconv` / `make_ndx` / analysis Skill design, and representative validation.

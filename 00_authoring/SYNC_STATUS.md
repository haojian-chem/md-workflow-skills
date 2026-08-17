# Authoring sync status

Status: CURRENT

本文件只记录当前同步状态和权威入口，不复制各 Stage 的完整科学规则。

## Current architecture baseline

- Lightweight Runtime v2：当前默认 runtime architecture。
- Stage 1 — Structure preparation：catalog defined；1.3–1.9 current guides 已同步，代表性 validation/refinement 仍在进行。
- Stage 2 — Topology / parameterization：architecture frozen；implementation partial。
- Stage 3 — System construction / solvation：architecture frozen；Step Skill/template implementation pending/refining。
- Stage 4 — MD simulation：architecture + first-pass guides frozen/implemented；representative execution validation pending。
- Stage 5 — Analysis：architecture + first-pass Workflow/5.1 guides frozen/implemented；analysis tool inventory population and concrete Tool/analysis Skill design pending。

## Current authority entry points

Runtime architecture:

`00_authoring/lightweight_runtime_v2_spec.md`

Master stage status/index:

`00_authoring/MD_WORKFLOW_MASTER_PLAN.md`

Manager:

```text
00_manager/md_workflow_manager/SKILL.md
00_manager/md_workflow_manager/references/workflow_plan_index.yaml
```

Stage architecture records:

```text
00_authoring/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
00_authoring/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
00_authoring/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
00_authoring/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

Stage 4 current guides:

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

Stage 5 current guides:

```text
01_workflows/analysis_workflow/SKILL.md
02_operations/analysis_planning_and_orchestration/SKILL.md
02_operations/analysis_planning_and_orchestration/references/analysis_tool_inventory.yaml
```

## Stage 4 current run-unit record

Project-level runtime file:

`<project_root>/04_md_simulation/run_unit.yaml`

Minimum fields:

```yaml
- run_unit_id:
  start_from_run_unit_id:
  status:
  path:
  top:
```

`path` = full run-unit storage directory for lookup; not an execution working-directory prescription.

`top` = full path of the main `.top` actually used by the run unit's `grompp`; this supports downstream topology lineage, including Stage 5 `.ndx` reuse across different TPRs.

## Stage 5 current freeze

Catalog:

```text
5.1 Analysis planning and orchestration
```

Manager creates the 5.1 Task Sheet entry and records the user's explicit analysis goal/object/constraints. 5.1 owns concrete analysis-plan expansion, Stage 5 reuse query/check, tool discovery and orchestration.

5.1 plan items use fixed local integer numbering and minimum fields:

```text
编号
tool
inputs
settings
status
path
```

Statuses:

```text
未完成
已完成
已终止
```

Prepared-input indexes:

```text
<project_root>/05_analysis/indexes/
├── trajectory_index.yaml  # maintained by trjconv
└── ndx_index.yaml         # maintained by make_ndx
```

5.1 only queries/verifies/uses these indexes. Each concrete Tool/analysis Skill validates its own output data; Stage 5 has no generic Validator layer.

## Historical / superseded material rule

Historical redesign, Workstream/route/runtime-projection validation, old benchmark protocols and superseded 1.3 drafts are not current architecture sources.

Current authoring should resolve conflicts in this order:

```text
current Skill / Tool guide
> matching architecture-freeze record
> MD_WORKFLOW_MASTER_PLAN.md / this SYNC_STATUS.md
> explicitly historical or Legacy files
```

Files marked `SUPERSEDED` or `LEGACY` must not be used to reconstruct current interfaces.

## Current pending work

- Stage 1 representative guide validation/refinement.
- Stage 2 missing Step/Validator/Tool implementation.
- Stage 3 Step Skill/template/validation implementation.
- Stage 4 representative planned-run/run-unit execution validation.
- Stage 5 analysis tool inventory population and concrete `trjconv` / `make_ndx` / analysis Skill design and validation.

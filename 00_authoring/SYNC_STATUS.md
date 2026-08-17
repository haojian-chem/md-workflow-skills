# Authoring sync status

Status: CURRENT

本文件只记录当前同步状态和权威入口，不复制各 Stage 的完整科学规则。

## Current authoring model

- 新科研 Skill 默认采用 `main Skill + references + only-when-justified supporting Skill`。
- 不再强制 Workflow / Operation / Validator 分类。
- `01_workflows/`、`02_operations/`、`02_validators/` 是历史布局/迁移中的现有路径，不是新 Skill 模板。
- Skill 是 Agent guide，不是 parser / wrapper / dispatcher gate。
- 多窗口 authoring：允许并鼓励按需读取外部相关 Skill；写入只限 owned `write_paths`；当前 Skill 不替其他 Skill 定义内部规则。
- Stage architecture-freeze 统一集中在 `00_authoring/architecture_freezes/`。
- Superseded/Legacy authoring Markdown 统一从 active path 移入 `00_authoring/archive/`。

Current boundary authority:

```text
00_authoring/AUTHORING_RULES.md
00_authoring/md-workflow-skill-authoring/references/skill_boundaries.md
00_authoring/md-workflow-skill-authoring/references/multi_window_authoring_protocol.md
```

## Current architecture baseline

- Lightweight Runtime v2：当前默认 runtime architecture。
- Stage 1 — Structure preparation：catalog defined；当前 guides 已同步，代表性 validation/refinement 仍在进行；物理布局仍主要处于历史分类目录，后续按实际需要迁移，不强制一次性搬迁。
- Stage 2 — Topology / parameterization：architecture frozen；implementation partial。
- Stage 3 — System construction / solvation：architecture frozen；Step Skill/template implementation pending/refining。
- Stage 4 — MD simulation：integrated main Skill + supporting run Skills；architecture + first-pass guides frozen/implemented；representative execution validation pending。
- Stage 5 — Analysis：integrated main Skill；architecture + first-pass guide frozen/implemented；analysis capability inventory population and concrete analysis Skill/Tool design pending。

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
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

Stage 4 current guides:

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

Stage 5 current guide:

```text
05_analysis/SKILL.md
05_analysis/references/analysis_tool_inventory.yaml
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

Manager creates the 5.1 Task Sheet entry and records the user's explicit analysis goal/object/constraints. Stage 5 main Skill owns concrete analysis-plan expansion, Stage 5 reuse query/check, capability discovery and orchestration.

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
├── trajectory_index.yaml  # maintained by trjconv capability owner
└── ndx_index.yaml         # maintained by make_ndx capability owner
```

Stage 5 main Skill only queries/verifies/uses these indexes. Each concrete analysis Skill/Tool validates its own output data; Stage 5 has no generic Validator layer.

## Historical / superseded material rule

Historical redesign, Workstream/route/runtime-projection validation, old benchmark protocols, superseded 1.3 drafts, and superseded Workflow/Operation/Validator authoring templates are not current architecture sources.

需要保留的过期 authoring Markdown 集中在：

`00_authoring/archive/`

Current authoring conflict resolution:

```text
current Skill / Tool guide
> matching architecture-freeze record in 00_authoring/architecture_freezes/
> MD_WORKFLOW_MASTER_PLAN.md / this SYNC_STATUS.md
> archived historical or Legacy files
```

Archive files must not be used to reconstruct current interfaces.

## Current pending work

- Stage 1 representative guide validation/refinement and gradual physical-layout cleanup where useful.
- Stage 2 missing Skill/Tool implementation under current main-Skill model.
- Stage 3 Skill/template/validation implementation under current main-Skill model.
- Stage 4 representative planned-run/run-unit execution validation.
- Stage 5 analysis capability inventory population and concrete `trjconv` / `make_ndx` / analysis Skill design and validation.

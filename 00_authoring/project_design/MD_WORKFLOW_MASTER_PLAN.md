# MD Workflow Master Plan

Status: ACTIVE CURRENT BASELINE

本文件只保存 MD Workflow 的**顶层阶段编号、Stage catalog、当前建设状态和 current authority 入口**。

具体科学规则、执行规则、validation、文件生命周期和 Stage-specific runtime 对象不在这里重复；它们由对应 current `SKILL.md` / references 或 architecture-freeze record 拥有。

## 1. Top-level numbering

固定顶层阶段：

1. Structure preparation
2. Topology / parameterization
3. System construction / solvation
4. MD simulation
5. Analysis

编号语义：`1.3` 表示整个 MD Workflow 的第 1.3 阶段；`2.4`、`3.2`、`4.1`、`5.1` 同理。

## 2. Scientific Skill directory model

当前 active 科研 Skill 按 Stage / 科学职责组织，不再按 Workflow / Operation / Validator 角色分根目录。

```text
01_structure_preparation/
02_topology_preparation/
04_md_simulation/
05_analysis/
```

Stage 3 detailed Skill 尚未实施完成，因此不为目录整齐预先创建空 Skill package。

一个 Stage 可以有 main `SKILL.md`，并在复杂且边界清晰时包含 1.x / 2.x / 4.x supporting or step Skills。Validation 默认跟随结果 owner；只有本身构成独立复杂职责时才拆 Skill。

历史 `01_workflows/`、`02_operations/`、`02_validators/` 不再是 active scientific Skill roots；需要保留的历史实现仅进入 archive / Git history。

## 3. Stage 1 — Structure preparation

Status: DEFINED; stage-oriented Skill layout active; representative validation/refinement continues.

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

Current stage entry:

`01_structure_preparation/SKILL.md`

Current substep Skills are colocated under `01_structure_preparation/1.x_*`.

Manager planning catalog:

`00_manager/references/workflow_plan_index.yaml`

## 4. Stage 2 — Topology / parameterization

Status: ARCHITECTURE FROZEN; stage main Skill active; detailed substep implementation remains partial.

Catalog:

```text
2.1 Parameterization environment and assignment
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

Current stage entry:

`02_topology_preparation/SKILL.md`

Current implemented detailed guide:

`02_topology_preparation/2.5_topology_integration_and_assembly/SKILL.md`

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

本文件不复制 2.x 的内部规则。

## 5. Stage 3 — System construction / solvation

Status: ARCHITECTURE FROZEN; detailed Skill implementation/refinement pending.

Catalog:

```text
3.1 Periodic box construction
3.2 Solvent addition
3.3 Ion addition
```

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

在 current Stage 3 Skill 真正实现前，不创建空 `03_md_preparation/` Skill package 充当伪入口。

## 6. Stage 4 — MD simulation

Status: ARCHITECTURE AND FIRST-PASS GUIDES FROZEN; representative execution validation pending.

Catalog:

```text
4.1 Energy minimization
4.2 Equilibration
4.3 Production simulation
```

Current guides:

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md`

Stage 4 的 run-unit 组织、字段和 binding 规则只由 Stage 4 current guide / freeze 定义，本文件不复制。

## 7. Stage 5 — Analysis

Status: ARCHITECTURE AND FIRST-PASS MAIN GUIDE FROZEN; concrete analysis-capability population and representative validation pending.

Catalog:

```text
5.1 Analysis planning and orchestration
```

Current guide:

```text
05_analysis/SKILL.md
05_analysis/references/analysis_tool_inventory.yaml
```

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

Stage 5 的 plan-item、prepared-input index、reuse 和 validation ownership 规则只由 Stage 5 current guide / freeze 及具体 capability owner 定义，本文件不复制。

## 8. Runtime architecture

Cross-Stage default runtime architecture:

`00_authoring/project_design/lightweight_runtime_v2_spec.md`

具体 Stage 例外仍以对应 Stage current guide / freeze 为准。

## 9. Current work status

当前建设重点：

- Stage 1：在新的 Stage-oriented layout 下继续代表性 validation/refinement；
- Stage 2：在 `02_topology_preparation/` 下补齐缺失 2.x Skills / Tools；
- Stage 3：按当前 main-Skill 模式完成具体 Skills；
- Stage 4：完成 representative planned-run / run-unit execution validation；
- Stage 5：填充 analysis capability inventory，并设计/验证具体 `trjconv`、`make_ndx` 和 analysis capabilities。

本节是项目级建设状态的唯一 current 汇总；不再另设 current `SYNC_STATUS.md`。

## 10. Ownership rule

发生内容冲突时，不按文件层级猜 authority，而按具体职责定位 owner：

```text
具体业务规则 → current Skill / reference
Stage 已冻结架构 → matching architecture-freeze record
跨 Stage runtime → lightweight_runtime_v2_spec.md
阶段目录 / 建设状态 / current entry index → 本 Master Plan
历史材料 → archive / Git history
```

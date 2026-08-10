# Authoring 文件同步状态

更新日期：2026-08-11

# 当前架构基线

```text
Default runtime: Lightweight Runtime v2
Manager core: refactored
Repository root runtime entry: aligned to Lightweight Runtime v2
Dedicated Task Execution Agent Skill: not required; root AGENTS.md defines execution behavior
Structure preparation Workflow: lightweight refactor complete
Directory policy: stable Step base directories + task-scoped execution subdirectories
1.1 source recognition: lightweight step interface refactored; revalidation pending
1.2 component/residue classification: lightweight step interface refactored; scientific revalidation pending
1.3 chain/component selection: redesign draft recorded; implementation incomplete; lightweight migration pending
Legacy Workstream / route / event / runtime projection: frozen, not default runtime
```

Lightweight Runtime v2 权威规格：

`00_authoring/lightweight_runtime_v2_spec.md`

1.3 当前重设计草案：

`00_authoring/1_3_chain_and_component_selection_redesign_draft.md`

该草案只记录已讨论并同意的方向，不是运行时 Skill，不表示 1.3 已完成。

# 当前目录策略

项目初始化只建立稳定基础目录到 Workflow / Step 层。

不同任务的实际执行目录固定为：

```text
<base_work_directory>/<task_id>/
```

职责边界：

```text
项目初始化 / Manager
→ 可以建立或确认稳定 Step 基础目录
→ 在 Task Sheet 中记录预计 `<base>/<task_id>/` 路径
→ 不创建任务专属目录

Task Execution Agent
→ 子环节开始先检查复用
→ 只有确实需要本地执行时才创建当前任务 `<task_id>/`
→ 如果直接复用已有正式结果，不创建空目录
```

# 当前科学 Skill 基线

```text
1.1 source recognition:
  Lightweight interface complete
  task-scoped outputs
  runtime revalidation pending

1.2 component/residue classification:
  Lightweight interface complete
  task-scoped outputs
  scientific state remains present_unvalidated pending revalidation

1.3 chain/component selection:
  2026-07-31 PASS 仅为旧实现历史结果
  本次重设计尚未完成
  当前只有 authoring draft
  正式 Operation / Validator 尚未迁移到新语义
  必须重新设计并重新验收

runtime_schema_validator:
  ACTIVE_LEGACY

source_recognition_deterministic v0.1.0:
  ACTIVE_LEGACY_INTERFACE
  Lightweight 显式路径接口待适配

runtime_dependency_preflight:
  ACTIVE_LEGACY_INTERFACE
  Lightweight 1.2 不再依赖 Manager pre-Agent closure 路径
```

# 已完成的 Lightweight Runtime v2 工作

- 冻结 Lightweight Runtime v2 架构规格；
- 重构 `md_workflow_manager`；
- 新增轻量 `workflow_plan_index.yaml`；
- 根 `AGENTS.md` 已切换默认真实运行入口；
- `AUTHORING_RULES.md` 已切换到 Lightweight authoring 规则；
- `structure_preparation_workflow` 已重构为阶段科学关系与 Step Skill 映射；
- 确定 Step 基础目录与 `<task_id>/` 执行目录两级模型；
- Manager 不创建任务专属科研目录；
- 1.1 已迁移到 Lightweight step 接口；
- 1.2 已迁移到 Lightweight step 接口；
- 1.3 当前设计方向已写入独立 authoring draft，但尚未修改正式 Operation / Validator。

# 1.2 / 1.3 当前权威与草案位置

```text
1.2 局部执行编排与 Lightweight 接口
→ 02_validators/component_and_residue_classification_validator/SKILL.md

1.2 科学语义
→ 02_validators/component_and_residue_classification_validator/references/classification_rules.md

1.2 CLI 与模块接口
→ 02_validators/component_and_residue_classification_validator/scripts/README.md

1.2 当前验收状态
→ 04_evals/component_and_residue_classification_validator/VALIDATION.md

1.3 本次重设计草案
→ 00_authoring/1_3_chain_and_component_selection_redesign_draft.md

1.3 旧实现（仅作历史参考）
→ 02_operations/chain_and_component_selection/
→ 02_validators/chain_and_component_selection_validator/
→ 04_evals/chain_and_component_selection/VALIDATION.md
```

# 当前仍需

## 1.3 重设计

- 冻结自然语言到 chain/residue retain specification 的解析规则；
- 冻结 `selection_spec.yaml`；
- 冻结单结构 / 多结构输出规则；
- 冻结 Operation / Validator 职责边界；
- 冻结 reuse conditions 与 official results；
- 再修改正式 1.3 Operation / Validator 与脚本；
- 重跑 1.2 → 1.3 回归和真实结构验收。

## Lightweight Runtime 验证

- 验证 1.1 / 1.2 的 `<task_id>/` 目录创建和跨任务复用；
- 验证任务单创建、跨对话恢复、连续多子环节执行和计划动态调整；
- 验证 1.1 → 1.2 → 1.3 handoff；
- 后续再决定 Legacy Runtime 的归档或删除策略。

本文件只记录当前同步状态和权威位置，不复制具体科学规则。

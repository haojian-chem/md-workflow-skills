# Authoring 文件同步状态

更新日期：2026-08-11

# 当前架构基线

```text
Default runtime: Lightweight Runtime v2
Manager core: refactored
Repository root runtime entry: aligned to Lightweight Runtime v2
Dedicated Task Execution Agent Skill: not required; root AGENTS.md defines execution behavior
Structure preparation Workflow: lightweight refactor complete
Directory policy: stable step base directories + task-scoped execution subdirectories
1.1 source recognition: lightweight step interface refactored; revalidation pending
1.2 component/residue classification: lightweight step interface refactored; scientific revalidation pending
1.3 lightweight step interface migration: pending
Legacy Workstream / route / event / runtime projection: frozen, not default runtime
```

Lightweight Runtime v2 权威规格：

`00_authoring/lightweight_runtime_v2_spec.md`

Manager 当前权威位置：

```text
00_manager/md_workflow_manager/SKILL.md
00_manager/md_workflow_manager/references/workflow_plan_index.yaml
```

Structure preparation Workflow 当前权威位置：

`01_workflows/structure_preparation_workflow/SKILL.md`

默认项目记录体系：

```text
00_project_records/task_index.md
00_project_records/project_result_index.md
00_project_records/tasks/Txxxx.md
```

# 当前目录策略

项目初始化只建立稳定基础目录到 Workflow / Step 层，例如：

```text
01_structure_preparation/
└── 02_component_and_residue_classification/
```

不同任务的实际执行目录固定为：

```text
<base_work_directory>/<task_id>/
```

例如：

```text
01_structure_preparation/02_component_and_residue_classification/T001/
01_structure_preparation/02_component_and_residue_classification/T005/
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

该规则用于防止不同任务使用固定文件名时互相覆盖，同时避免 Manager 为尚未执行或最终复用的步骤提前创建大量空目录。

# 当前科学 Skill 基线

```text
1.1 source recognition: Lightweight interface complete, task-scoped outputs, runtime revalidation pending
1.2 component/residue classification: Lightweight interface complete, task-scoped outputs, scientific state remains present_unvalidated pending revalidation
1.3 chain/component selection: PASS（沿用 2026-07-31 验收，需针对 1.2 变更及 Lightweight 接口重跑）
runtime_schema_validator: ACTIVE_LEGACY，不再是 Lightweight 普通任务默认依赖
source_recognition_deterministic v0.1.0: ACTIVE_LEGACY_INTERFACE，Lightweight 显式路径接口待适配
runtime_dependency_preflight: ACTIVE_LEGACY_INTERFACE，Lightweight 1.2 不再依赖 Manager pre-Agent closure 路径
```

1.2 原有科学分类 engine、schemas、registries、CCD-compatible library 和 opaque 1.2→1.3 identity contract 均保留。本轮 1.2 重构只改变运行时接口、目录隔离、复用规则、依赖检查位置和完成记录方式，因此科学状态仍保持 `present_unvalidated`，必须重新验收后才能提升。

# Lightweight Runtime v2 已完成

- 冻结 1–8 部分架构规格；
- 重构 `md_workflow_manager` 为任务定位、创建、初始规划和项目级管理入口；
- 新增轻量 `workflow_plan_index.yaml`，目前定义 1.1–1.9；
- 根 `AGENTS.md` 已切换默认真实运行入口；
- `AUTHORING_RULES.md` 已切换到 Lightweight authoring 规则；
- `skill_inventory.yaml` 已标记 Legacy contracts/runtime 为冻结非默认依赖；
- 决定不建立独立 Task Execution Agent Skill；Task Execution Agent 由根 `AGENTS.md` 的通用执行规则约束；
- `structure_preparation_workflow` 已从 route fragment / one-decision dispatcher 重构为阶段科学关系与 Step Skill 映射；
- 确定 Step 基础目录与 `<task_id>/` 执行目录两级模型；
- Manager 不创建任务专属科研目录；Task Execution Agent 只在确需执行时创建；
- 1.1 `source_recognition` 已迁移到统一 Lightweight step 接口，并将 official results 写入 `01_source_recognition/<task_id>/`；
- 1.2 `component_and_residue_classification_validator` 已迁移到统一 Lightweight step 接口，并将可变状态和正式结果隔离到 `02_component_and_residue_classification/<task_id>/`；
- 1.2 reuse 明确核验 structure hash、selected model、classification mode、reference manifest 和适用人工 relation decisions；
- 1.2 不再要求 Manager 在另一对话中调用 Legacy runtime dependency gate；依赖检查由当前 Task Execution Agent 在加载完整科学材料前最小化执行；
- 1.2 official results 当前定义为 `classification_result.yaml`、`reference_manifest.yaml`、`classification_report.md`，以及存在人工关系决定时的 `relation_decisions.yaml`；
- 1.3 继续只消费 1.2 `classification_result.yaml` 中物化的 opaque IDs；
- 未删除 Legacy Runtime 文件或工具。

# 1.2 / 1.3 权威位置

```text
1.2 局部执行编排与 Lightweight 接口
→ 02_validators/component_and_residue_classification_validator/SKILL.md

1.2 科学语义
→ 02_validators/component_and_residue_classification_validator/references/classification_rules.md

1.2 CLI 与模块接口
→ 02_validators/component_and_residue_classification_validator/scripts/README.md

1.2 当前验收状态
→ 04_evals/component_and_residue_classification_validator/VALIDATION.md

1.3 选择接口与验收
→ 02_operations/chain_and_component_selection/
→ 02_validators/chain_and_component_selection_validator/
→ 04_evals/chain_and_component_selection/VALIDATION.md
```

# 当前仍需

## Lightweight Runtime

- 迁移 1.3 Operation + Validator 到统一 Lightweight step 接口；
- 验证 1.1 / 1.2 的 `<task_id>/` 目录创建和跨任务复用行为；
- 验证任务单创建、跨对话恢复、连续多子环节执行和计划动态调整；
- 验证 1.1→1.2→1.3 handoff；
- 后续决定是否把 `source_recognition_deterministic` 改为直接接受明确候选路径和工作目录；
- 再决定 Legacy Runtime 的归档或删除策略。

## 1.2 / 1.3 科学验证

- hosted GitHub Actions；
- 真实 PDB/mmCIF/GROMACS 回归；
- 完整真实 1.2→1.3 选择验收；
- 已批准辅因子/配体 CCD seed 完整性与 hash 核验。

本文件只记录当前同步状态和权威位置，不复制具体科学规则。

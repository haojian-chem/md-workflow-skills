# Authoring 文件同步状态

更新日期：2026-08-10

# 当前架构基线

```text
Default runtime: Lightweight Runtime v2
Manager core: refactored
Repository root runtime entry: aligned to Lightweight Runtime v2
Dedicated Task Execution Agent Skill: not required; root AGENTS.md defines execution behavior
Structure preparation Workflow: lightweight refactor complete
1.1 / 1.2 / 1.3 lightweight step interface migration: pending
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

# 当前科学 Skill 基线

```text
1.2 component/residue classification: present_unvalidated
1.3 chain/component selection: PASS（沿用 2026-07-31 验收，需针对 1.2 变更及 Lightweight 接口重跑）
runtime_schema_validator: ACTIVE_LEGACY，不再是 Lightweight 普通任务默认依赖
```

1.2 当前状态重构已实现；迁移后的本地自动测试与真实 AF3 输入验收通过。hosted CI、真实 PDB/mmCIF/GROMACS、完整 1.2→1.3 选择回归及批准辅因子/配体 CCD seed 仍未闭合，因此科学状态保持 `present_unvalidated`。

# Lightweight Runtime v2 已完成

- 冻结 1–8 部分架构规格；
- 重构 `md_workflow_manager` 为任务定位、创建、初始规划和项目级管理入口；
- 新增轻量 `workflow_plan_index.yaml`，目前定义 1.1–1.9；
- 根 `AGENTS.md` 已切换默认真实运行入口；
- `AUTHORING_RULES.md` 已切换到 Lightweight authoring 规则；
- `skill_inventory.yaml` 已标记 Legacy contracts/runtime 为冻结非默认依赖；
- 决定不建立独立 Task Execution Agent Skill；Task Execution Agent 由根 `AGENTS.md` 的通用执行规则约束；
- `structure_preparation_workflow` 已从 route fragment / one-decision dispatcher 重构为：
  - 结构准备阶段科学边界；
  - 1.1–1.9 到实际 Operation/Validator Skill 的映射；
  - 阶段内科学关系；
  - 条件步骤对动态 Task Sheet 的影响；
- 未删除 Legacy Runtime 文件或工具。

# 1.2 / 1.3 权威位置

```text
1.2 局部执行编排
→ 02_validators/component_and_residue_classification_validator/SKILL.md

1.2 科学语义
→ 02_validators/component_and_residue_classification_validator/references/classification_rules.md

1.2 CLI 与模块接口
→ 02_validators/component_and_residue_classification_validator/scripts/README.md

1.2 当前验收状态
→ 04_evals/component_and_residue_classification_validator/VALIDATION.md

1.3 选择接口与验收
→ 02_operations/chain_and_component_selection/
→ 04_evals/chain_and_component_selection/VALIDATION.md
```

# 当前仍需

## Lightweight Runtime

- 为 1.1、1.2、1.3 明确并接入统一的：
  - `object requirements`
  - `reuse conditions`
  - `validation requirements`
  - `official results`
- 确认 1.1 / 1.2 / 1.3 在 Task Execution Agent 下不再依赖 runtime task、route、event、record committer 等 Legacy closure；
- 验证任务单创建、跨对话恢复、连续多子环节执行、结果复用和计划动态调整；
- 再决定 Legacy Runtime 的归档或删除策略。

## 1.2 / 1.3 科学验证

- hosted GitHub Actions；
- 真实 PDB/mmCIF/GROMACS 回归；
- 完整真实 1.2→1.3 选择验收；
- 已批准辅因子/配体 CCD seed 完整性与 hash 核验。

本文件只记录当前同步状态和权威位置，不复制具体科学规则。

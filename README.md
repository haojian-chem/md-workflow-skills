# MD Workflow Skills

用于设计、维护和执行面向分子动力学科研任务的 Skill / Tool 体系。

## Current scientific Skill layout

Active scientific Skills 按 Stage / 科学职责组织：

```text
00_manager/
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

其中：

```text
03_md_preparation/
├── SKILL.md
├── 3.1_periodic_box_construction/
├── 3.2_solvent_addition/
└── 3.3_ion_addition/
```

Stage 3 的架构已经冻结，当前已建立 first-pass Step Skills；`3.3` 专用 `genion.mdp` 的精确模板内容和代表性执行验证仍待完成。

科研 Skill 不再按 Workflow / Operation / Validator 分根目录。Step 内部的 validation 默认由结果 owner 持有，只有复杂且独立时才拆 supporting Skill。

## Non-Skill infrastructure

以下目录**不是 MD Workflow Stage Skill 目录，也不占用 Stage 编号**：

```text
evals/      # tests / fixtures / validation evidence / benchmark
tools/      # current Lightweight-compatible shared deterministic tools
legacy/     # old runtime contracts / runtime projections / legacy tools
```

当前 `tools/tool_registry.yaml` 只登记已经适配 current Lightweight / Skill interface 且完成测试的共享 Tool。旧 `05_tools/` 中依赖 Legacy runtime 的工具已移入 `legacy/tools/`，不会因为历史 ACTIVE 状态自动成为 current Tool。

历史设计 Markdown 已从顶层 `design_records/` 移入：

```text
00_authoring/archive/legacy_runtime/design_records/
```

旧 runtime contracts / generated runtime material 分别位于：

```text
legacy/contracts/
legacy/runtime/
```

## Runtime model

真实项目默认采用 Lightweight Runtime v2：

```text
Manager
→ Task Sheet
→ long-lived Task Execution Agent
→ current main Skill
→ 按需 references / supporting Skills / deterministic Tools
```

Manager：`00_manager/SKILL.md`

Cross-Stage runtime：`00_authoring/project_design/lightweight_runtime_v2_spec.md`

Stage catalog / 建设状态：`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

## Authoring

Skill authoring / maintenance 的默认入口：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

Stage architecture freezes：`00_authoring/architecture_freezes/`

Tool authoring：`00_authoring/md-workflow-tool-authoring/SKILL.md`

## Real MD project records

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

Skill repository 的源码目录和真实 MD project 的 execution directory 是不同概念。

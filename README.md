# MD Workflow Skills

用于设计、维护和执行面向分子动力学科研任务的 Skill / Tool 体系。

## Current scientific layout

MD Workflow 的 Scientific Stage roots 固定为：

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

`00_manager/` 是独立的项目管理 package，`00_runtime/` 是独立的跨 Stage Task Execution runtime package；两者都不占用 Scientific Stage 编号。

Stage / Step 目录可以在正式 Skill generation 前预留，因此：

```text
目录存在 ≠ Skill 已生成 ≠ runtime authority 已激活
```

当前总体建设状态：

- Stage 1：partially implemented；已有正式 active Skills，同时仍有处于 authoring / freeze-only 状态的后续 Step；
- Stage 2：architecture frozen；`2.1–2.6` Step package directories 已预留，尚无 active Stage 2 Skill；
- Stage 3：architecture frozen；`3.1–3.3` Step package directories 已预留，尚无 active Stage 3 Skill；
- Stage 4：active Skill generation completed；Stage main Skill 与 `4.1–4.3` Skills 已存在；
- Stage 5：architecture frozen；`5.1` Step package directory 已预留，尚无 active Stage 5 Skill。

例如当前 Stage 3 scientific source tree 为：

```text
03_md_preparation/
├── 3.1_periodic_box_construction/
├── 3.2_solvent_addition/
└── 3.3_ion_addition/
```

这些目录当前是 future Skill package locations，不表示 first-pass Step Skills 已经生成。

精确的 Stage / Step 建设状态与 current entry 统一读取：

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

科研 Skill 不再按 Workflow / Operation / Validator 分根目录。Step 内部的 validation 默认由结果 owner 持有，只有复杂且独立时才拆 supporting Skill。

## Non-Skill infrastructure

以下目录**不是 MD Workflow Stage Skill 目录，也不占用 Stage 编号**：

```text
evals/      # tests / fixtures / validation evidence / benchmark
tools/      # current Lightweight-compatible shared deterministic tools
legacy/     # old runtime contracts / runtime projections / legacy tools
```

当前 `tools/tool_registry.yaml` 只登记已经适配 current Lightweight / Skill interface、完成测试并明确 reactivated 的共享 Tool。旧 runtime-dependent 工具保留在 `legacy/tools/`，不会因为历史 ACTIVE 状态自动成为 current Tool。

历史设计 Markdown 位于：

```text
00_authoring/archive/
```

旧 runtime contracts / generated runtime material 分别位于：

```text
legacy/contracts/
legacy/runtime/
```

## Runtime model

真实项目默认运行链：

```text
Manager
→ Task Sheet
→ 00_runtime/SKILL.md
→ long-lived Task Execution Agent
→ current Stage / Step main Skill
→ 按需 references / supporting Skills / deterministic Tools
```

Manager：`00_manager/SKILL.md`

Cross-Stage Task Execution runtime：`00_runtime/SKILL.md`

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

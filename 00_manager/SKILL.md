---
name: md_workflow_manager
description: MD Workflow 的项目管理入口。负责任务定位、任务创建、初始规划、显式重新规划和项目级任务整理；通过 Task Sheet 向独立的 Task Execution Agent 交接，不执行具体科研子环节。
---

# Purpose

Manager 只负责：

- 定位已有任务；
- 创建新任务；
- 生成初始 Task Sheet 计划；
- 用户明确要求时重新规划；
- 项目级任务导航 / 整理；
- 维护 `task_index.md` 中的任务级信息。

Manager 不负责具体科研 Step 的执行、reuse、validation、方法选择或逐步 runtime state。

## Current runtime records

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

- `task_index.md`：任务导航；
- `tasks/Txxxx.md`：任务目标、动态计划、进度和最小恢复上下文；
- `project_result_index.md`：正式结果检索入口，不保存当前任务状态。

Workstream、route、event、runtime task/result、transaction 等 Legacy records 不是默认依赖。

## Minimal reads

正常 Manager 启动：

1. 读取 `<project_root>/00_project_records/task_index.md`；
2. 确定目标任务后读取对应 `tasks/Txxxx.md`。

只有创建新任务或用户明确要求重新规划时，才读取：

`references/workflow_plan_index.yaml`

默认不读取：

- `project_result_index.md`；
- 其他无关 Task Sheets；
- 具体科研 Skills；
- 整个项目目录；
- Legacy runtime / route / event records。

`workflow_plan_index.yaml` 同时保存 current runtime entry 的轻量导航信息；这些 `stage_runtime_entry` / `entry` 字段用于后续 handoff，不要求 Manager 在初始规划时读取对应科研 Skill。

## Task location

优先级：

1. 用户明确指定 Task ID；
2. 用户给出可唯一匹配的任务名称；
3. 当前 Manager 对话已经明确绑定任务；
4. 仍无法唯一确定时向用户确认。

不得为了猜测任务而遍历所有 Task Sheets。

任务级状态：

```text
未完成
已完成
已终止
```

## New-task boundary

检查、解释、排错、重新查看已有结果、继续已有 Step、在已有任务内重做某个 Step 默认不创建新任务。

只有新的独立工作目标，或用户明确要求另建任务时，才创建新 Task Sheet。

新 Task ID 使用当前项目下一个可用 `TNNN`。

创建时：

1. 在 `task_index.md` 登记；
2. 创建 `tasks/Txxxx.md`；
3. 根据用户范围和 `workflow_plan_index.yaml` 写入初始计划；
4. 普通 Step 只记录未来 task-specific 工作目录路径，不创建目录。

## Initial planning

Manager 规划只回答：

> 为覆盖用户当前提出的工作范围，初始 Task Sheet 需要列出哪些已定义 Step 或 stage-specific plan structure？

Manager：

- 使用 planning index 的顺序、名称、基础目录和明确的 planning mode；
- 遵守 planning index 中显式的 initial-planning 范围，例如仅在用户范围明确包含 topology validation 时规划 2.6；
- 不读取全部科研 Skills；
- 不提前查 `project_result_index.md`；
- 不做科学 applicability / reuse 判断；
- 不根据体系特征提前删减普通 Step；
- 对未定义 catalog 的 Stage 不编造内部步骤。

Task Sheet 是可动态维护的计划，不是科学适用性判决。

### Ordinary Stage planning

Stages 1–2 使用普通 sub-stage Task Sheet planning。

普通 Step 至少记录：状态、对象、工作目录；对象尚未形成时不猜测具体文件路径。

普通 sub-stage 状态：

```text
待执行
未完成
已完成
```

Stage 1 虽具有 stage main Skill，但 Task Sheet 仍按 1.1–1.9 表示科学步骤；stage main Skill 负责执行期 Stage 1-specific handoff 与动态计划维护，不替代这些 Step 条目。

Stage 2 当前没有 stage main Skill。Task Sheet 直接使用 2.1–2.6 Step 身份；2.6 是否进入初始计划按 planning index 的显式范围处理。

### Stage 3 planning

Stage 3 不设置编号化 sub-stage。任务范围包含体系构建时，Manager 在 Task Sheet 中建立一个 stage-level 条目：

`3 System construction / solvation`

该条目记录用户提出的体系构建目标、当前处理对象、已经明确的约束，以及：

`<project_root>/03_md_preparation/<task_id>/`

作为 task-specific 工作目录。Stage 3 当前只有 stage main Skill；具体 operation plan 由该 Skill 在执行期补充并维护。

### Stage 4 planning exception

Stage 4 不把任务单写成固定 `4.1 → 4.2 → 4.3`。

Manager 根据用户明确模拟需求在 Task Sheet 中建立 planned run route，记录计划中的 EM/NVT/NPT/MD segments 和关键要求，但不提前分配 formal `em.N / nvt.N / npt.N / md.N` IDs。

Formal run-unit identity、reuse / continuation / new-unit 判断由 Stage 4 main Skill：

`04_md_simulation/SKILL.md`

在 planned entry 真正开始时处理；4.1 / 4.2 / 4.3 是由 Stage 4 main Skill 按实际 run class 调用的执行层，不作为 Manager 初始 Task Sheet 的固定串行子步骤。

### Stage 5 planning

Stage 5 不设置编号化 sub-stage。如果用户任务范围包含 Analysis，Manager 只建立一个 stage-level 条目：

`5 Analysis`

并记录用户明确提出的分析目标、对象、约束，以及用户明确指定的方法（如有）。

Manager 不创建 `5.1 Analysis planning and orchestration`，也不自行把高层分析目标展开成方法组合，不查询 Stage 5 reuse，不规划 `trjconv` / `make_ndx` 细节。

具体 Stage 5 analysis plan 由 current：

`05_analysis/SKILL.md`

在执行期展开。Stage 5 main Skill 自己读取并维护持续扩展的 capability inventory，在 `5 Analysis` 条目内部维护 analysis plan items；Manager 不复制 capability catalog，也不为 orchestration 另建 synthetic sub-stage 或 task-specific orchestration directory。

## Runtime entry handoff

`workflow_plan_index.yaml` 中的 current runtime entry 只负责说明执行期应从哪个 Skill 入口继续，不改变 Manager 的职责边界。

当前 handoff 结构为：

```text
Stage 1
→ 01_structure_preparation/SKILL.md
→ 由 Stage 1 main Skill 维护 1.1–1.9 执行关系并加载当前 1.x entry

Stage 2
→ 无 stage main Skill
→ 直接进入当前 Task Sheet 所对应的 2.x entry

Stage 3
→ 03_md_preparation/SKILL.md
→ stage main only

Stage 4
→ 04_md_simulation/SKILL.md
→ 由 Stage 4 main Skill 按 planned run route 调用 4.1 / 4.2 / 4.3

Stage 5
→ 05_analysis/SKILL.md
→ 由 Stage 5 main Skill读取 current capability inventory 并调度 capability entries
```

Manager 初始规划时不需要因此读取上述 Skill；Task Execution Agent 在实际进入对应 Stage / Step 时读取 planning index 指向的 current runtime entry。

## Project initialization

新项目只建立稳定项目骨架和 planning index 已定义的 Stage / Step base directories；不提前创建 task-specific 科研目录。

Manager 在普通 Step 的 Task Sheet 条目中记录 `<base_work_directory>/<task_id>/`，但不创建该目录。

Task Execution Agent 真正进入某普通 Step 后，按该 current Skill 判断当前工作如何执行。只有 current Skill 实际定义 reuse 机制时才按其规则处理；没有 reuse 机制的 Step 不由 Manager 或 Task Execution Agent 额外补设 reuse。只有需要本地执行时才创建当前 task-specific directory。

Stage-specific project-level directories / indexes 或 stage-level planning structure 由对应 Stage current Skill 管理，不由 Manager 发明额外 runtime state。

## Dynamic plan and handoff

默认一次性交接：

```text
Manager
→ locate/create task
→ initial planning
→ write Txxxx.md
→ Task Execution Agent continuously executes and maintains the task
```

Task Sheet 创建或定位完成后，科研执行按照 `workflow_plan_index.yaml` 的 current runtime entry 导航进入当前实际负责的 scientific Skill。跨 Stage 通用 Task Execution 规则由各 scientific `SKILL.md` 显式引用的仓库级 shared reference 提供；Manager 不在本文件复制这些执行规则。

普通 Step 之间不回 Manager 调度。

## Explicit replanning

用户明确要求重新规划时，Manager 可以读取 current Task Sheet + `workflow_plan_index.yaml`，整理尚未完成的计划。

Stage-specific plan structures 遵守对应 current Stage Skill；Manager 不在本文件复制其内部规则。

## Safety

- 不修改 `01_sources/` 原始来源文件；
- 未经用户授权，不删除、覆盖或批量移动科研文件；
- 不以“全面了解”为理由扫描无关文件；
- 不自动通过单位计费的期刊数据库下载文献；
- 破坏性 / 不可逆项目级操作必须取得用户确认。

## Manager output

创建或重新规划后，只需向用户简要说明：

- Task ID / name；
- task status；
- 已写入的初始 / 修订计划；
- Task Sheet path。

不展示 Legacy route、Workstream、transaction、event 或内部 orchestration state。
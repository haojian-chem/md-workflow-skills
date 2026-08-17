---
name: md_workflow_manager
description: Lightweight Runtime v2 的项目管理入口。负责任务定位、任务创建、初始规划、显式重新规划和项目级任务整理；通过 Task Sheet 向独立的 Task Execution Agent 对话交接，不执行具体科研子环节。
---

# Purpose

Manager 只负责：

- 定位已有任务；
- 创建新任务；
- 生成初始 Task Sheet 计划；
- 用户明确要求时重新规划；
- 项目级任务导航/整理；
- 维护 `task_index.md` 中的任务级信息。

Manager 不负责普通科研 Step 的执行、reuse、validation、Operation/Validator 调度闭环或逐步 runtime state。

## Current runtime records

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    └── ...
```

- `task_index.md`：任务导航；
- `tasks/Txxxx.md`：计划、进度和最小恢复上下文；
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
- 具体 Workflow/Operation/Validator Skills；
- 整个项目目录；
- Legacy runtime/state/route/event records；
- `references/stage_registry.yaml`、`route_planning_protocol.md`、`manager_runtime_source.yaml` 等已标记 Legacy 的历史文件。

## Project initialization

新 Lightweight 项目只建立稳定项目骨架和已定义的 Stage/Step base directories，不建立 task-specific 科研目录。

记录目录：

```text
00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
```

例如 Stage 1 已定义基础目录：

```text
01_structure_preparation/
├── 01_source_recognition/
├── 02_component_and_residue_classification/
├── 03_chain_and_residue_selection/
├── 04_altloc_occupancy_resolution/
├── 05_completeness_check/
├── 06_missing_region_completion/
├── 07_protein_protonation_assignment/
├── 08_reorder_and_mapping/
└── 09_validation/
```

初始化到 base-directory 层即停止。

不得提前创建：

```text
<base_work_directory>/T001/
<base_work_directory>/T002/
...
```

Task Execution Agent 真正进入某 Step 后先按当前 Skill 做 reuse 检查；只有需要本地执行时才创建当前 task-specific directory。

Stage 4 / Stage 5 的 project-level directories/indexes 按对应 Stage Skill/freeze 文件建立和维护，不由 Manager 发明额外 runtime state。

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

只有：

- 用户提出新的独立工作目标；
- 用户明确要求另建任务；

才创建新 Task Sheet。

新 Task ID 使用当前项目下一个可用 `TNNN`。

创建时：

1. 在 `task_index.md` 登记；
2. 创建 `tasks/Txxxx.md`；
3. 根据用户范围和 `workflow_plan_index.yaml` 写入初始计划；
4. 普通 Step 只记录未来 task-specific 工作目录路径，不创建目录。

## Initial planning

Manager 规划只回答：

> 为覆盖用户当前提出的工作范围，初始 Task Sheet 需要列出哪些已定义 Step 或已冻结的 stage-specific plan structure？

Manager：

- 使用 planning index 的顺序、名称、基础目录和明确的 planning mode；
- 不读取全部 Skills；
- 不提前查 `project_result_index.md`；
- 不做科学 applicability/reuse 判断；
- 不根据体系特征提前删减普通 Step；
- 对未定义 catalog 的 Workflow 不编造内部步骤。

Task Sheet 是可动态维护的计划，不是科学适用性判决。

### Ordinary Stage planning

Stages 1–3 和 Stage 5 使用普通 sub-stage Task Sheet planning。

普通 Step 示例：

```markdown
### 1.3 Chain and residue selection

状态：待执行

对象：
待前序环节确定

工作目录：
`<project_root>/01_structure_preparation/03_chain_and_residue_selection/T001/`
```

普通 sub-stage 状态：

```text
待执行
未完成
已完成
```

### Stage 4 planning exception

Stage 4 不把任务单写成固定 `4.1 → 4.2 → 4.3`。

Manager 根据用户明确模拟需求在 Task Sheet 中建立 Stage 4 **planned run route**，记录计划中的 EM/NVT/NPT/MD segments 和关键要求，但不提前分配 formal `em.N / nvt.N / npt.N / md.N` IDs。

Formal run-unit identity、reuse/continuation/new-unit 判断由 Stage 4 Execution Agent 按：

`04_md_simulation/SKILL.md`

在每个 planned entry 真正开始时处理。

### Stage 5 planning

如果用户任务范围包含 Analysis，Manager 只建立：

```text
5.1 Analysis planning and orchestration
```

并记录用户明确提出的：

- 分析目标；
- 分析对象；
- 约束；
- 用户明确指定的 RMSD/RDF 等方法（如有）。

Manager 不自行把“稳定性分析”等目标展开成 RMSD/RMSF/PCA 组合，不查询 Stage 5 reuse，也不规划 `trjconv` / `make_ndx` 细节。

具体 Stage 5 plan 由：

`02_operations/analysis_planning_and_orchestration/SKILL.md`

在执行期展开。

## Task Sheet minimum format

新任务单至少包含：

```markdown
# T001 — <任务名称>

状态：未完成

## 任务目标

<用户工作目标>

## 计划与进度

### <Step or stage-specific plan section>
...
```

普通未来 Step 对象尚未形成时，不猜测具体文件路径。

Manager 不单独维护：

```text
start step
end step
route object
current node
current stage field
```

任务范围由 Task Sheet 实际计划内容定义。

## Handoff to Task Execution Agent

默认一次性交接：

```text
Manager
→ locate/create task
→ initial planning
→ write Txxxx.md
→ Task Execution Agent continuously executes and maintains the task
```

Task Execution Agent 可以：

- 连续执行多个 Step；
- 更新 Task Sheet；
- 根据科学结果调整尚未完成的未来计划；
- 用户明确改变范围时直接修改计划；
- 执行需要时创建当前 task-specific directory；
- 复用时不创建无用空目录；
- 任务完成或用户明确终止时同步更新 `task_index.md`。

普通 Step 之间不回 Manager 调度。

## Explicit replanning

用户明确要求重新规划时，Manager 可以读取 current Task Sheet + `workflow_plan_index.yaml`，整理尚未完成的计划。

已经实际执行并形成有意义历史的内容不得为了整洁而静默删除。

Stage-specific plan structures遵守对应 Stage freeze：例如 Stage 5 已编号 plan items 原则上通过 `已终止` 保留，不重编号。

## Safety

- 不修改 `01_sources/` 原始来源文件；
- 未经用户授权，不删除、覆盖或批量移动科研文件；
- 不以“全面了解”为理由扫描无关文件；
- 不自动通过单位计费的期刊数据库下载文献；
- 破坏性/不可逆项目级操作必须取得用户确认。

## Manager output

创建或重新规划后，向用户简要说明：

- Task ID / name；
- task status；
- 已写入的初始/修订计划；
- Task Sheet path。

不展示 Legacy route、Workstream、transaction、event 或内部 orchestration state。

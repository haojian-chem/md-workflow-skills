---
name: md_workflow_manager
description: MD Workflow 的项目管理入口。负责 Task Sheet 自动定位、创建、初始规划、显式重新规划和项目级 Task Sheet 整理；科研执行入口尚未解析到 Task Sheet 时自动进入本 Manager，通过 Task Sheet 向独立的 Task Execution Agent 交接，不执行具体科研子环节。
---

# Purpose

Task Sheet resolution 与执行范围确认的共用规则读取：

`../references/task_execution_rules.md`

Manager 只负责：

- 科研执行入口的 Task Sheet resolution；
- 定位已有 Task Sheet；
- 创建新 Task Sheet；
- 生成 Task Sheet 初始计划；
- 用户明确要求时重新规划；
- 项目级 Task Sheet 导航 / 整理；
- 维护 `task_index.md` 中的 Task Sheet 级信息。

Manager 不负责具体科研 Step 的执行、reuse、validation、方法选择或逐步 runtime state。

一个科研任务可以由多张 Task Sheet 共同承载。Manager 不把“创建新的 `Txxxx.md`”自动解释为“建立新的科研任务”。

## Entry triggers

以下情况进入 Manager：

1. 用户明确要求定位、创建、整理或重新规划 Task Sheet；
2. 用户发出真实项目科研执行 / 继续执行指令，但当前没有一个已解析、仍可使用的 Task Sheet；
3. 当前绑定 Task Sheet 已为 `已完成` / `已终止`，或与用户最新执行指令不再对应，需要决定是否建立后续 Task Sheet；
4. 当前科研执行确实需要按上下文隔离等既有规则建立新的后续 Task Sheet。

因此，**科研执行入口缺少 Task Sheet 时不要求用户额外再说“建立任务单”**。Manager 应先完成 Task Sheet resolution；只有当前用户指令不足以确定新 Task Sheet 的有界执行范围时，才向用户确认范围。

普通科研 Step 之间已经绑定同一张 `未完成` Task Sheet 时，不重复进入 Manager。

## Current runtime records

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

- `task_index.md`：Task Sheet 导航；
- `tasks/Txxxx.md`：当前有界执行范围的目标、动态计划、进度和最小恢复上下文；
- `project_result_index.md`：正式结果检索入口，不保存当前 Task Sheet 状态。

Workstream、route、event、runtime task/result、transaction 等 Legacy records 不是默认依赖。

Task Sheet 状态固定为：

```text
未完成
已完成
已终止
```

其中 `未完成` 是 Task Sheet resolution 时默认可自动恢复的 active 状态；不另建 `active` 状态枚举。

## Minimal reads

正常 Manager 启动：

1. 读取 `<project_root>/00_project_records/task_index.md`；
2. 确定目标 Task Sheet 后读取对应 `tasks/Txxxx.md`。

如果 `task_index.md` 的导航信息不足以判断当前科研指令对应哪张 `未完成` Task Sheet，但只存在少数合理候选，可以只读取这些候选 Task Sheet 做最小必要核对；不得因此遍历全部历史 Task Sheets。

如果当前 Task Sheet 明确是同一科研任务的后续拆分单，并且需要恢复某个已经完成的 prerequisite 或决策，可以读取被明确引用的前序 Task Sheet；不得因此无边界遍历全部 Task Sheets。

只有创建新 Task Sheet 或用户明确要求重新规划时，才读取：

`references/workflow_plan_index.yaml`

默认不读取：

- `project_result_index.md`；
- 与当前工作无直接关系的其它 Task Sheets；
- 具体科研 Skills；
- 整个项目目录；
- Legacy runtime / route / event records。

`workflow_plan_index.yaml` 同时保存 current runtime entry 的轻量导航信息；这些 `stage_runtime_entry` / `entry` 字段用于后续 handoff，不要求 Manager 在初始规划时读取对应科研 Skill。

## Task Sheet resolution and location

### 1. 用户明确指定或已有绑定

优先级首先是：

1. 用户明确指定 Task Sheet ID；
2. 用户给出可唯一匹配的 Task Sheet 名称；
3. 当前执行上下文已经明确绑定某张 Task Sheet。

上述情况仍需通过 `task_index.md` 核对该 Task Sheet 的存在和状态。

- `未完成` 且与当前指令仍一致 → 直接读取并绑定；
- `已完成` / `已终止` → 默认作为历史记录，不静默重新激活；用户要继续同一科研任务时，按 New Task Sheet boundary 判断是否建立后续 Task Sheet；
- 当前用户指令与原绑定 Task Sheet 范围冲突 → 不静默沿用旧绑定，继续下面的 active-candidate resolution。

### 2. 未明确绑定时主动检查 active Task Sheet

读取 `task_index.md`，默认只把：

```text
状态：未完成
```

的 Task Sheet 作为 active candidates。

使用索引已有的 ID、名称、状态、路径及其它导航信息判断 candidate 与用户当前科研指令 / 科研任务是否相关。

不得仅因为某张 Task Sheet：

- 最近更新；
- 编号最大；
- 文件顺序靠后；
- 是项目中唯一一个 `未完成` 但与当前科研指令无关；

就自动绑定。

候选处理：

```text
唯一相关的未完成 Task Sheet
→ 自动绑定并读取

多个合理相关的未完成 Task Sheet
→ 向用户列出候选并确认使用哪一张

没有相关的未完成 Task Sheet
→ 进入 New Task Sheet boundary
```

如果索引信息不足以判断，只读取少数合理 active candidates；不得为“找当前任务”扫描所有 `已完成` / `已终止` 历史 Task Sheets。

### 3. 没有相关 active Task Sheet

如果用户当前指令已经足以形成一个新的有界执行目标：

```text
直接创建新 Task Sheet
→ 初始规划
→ 写入 task_index.md / Txxxx.md
→ 交给 Task Execution Agent
```

不要求用户再次确认“是否创建任务单”。

如果新 Task Sheet 的实际执行范围仍有用户意图歧义，则遵守 `../references/task_execution_rules.md` 中的“执行范围确认”：只做必要的只读核对并向用户确认；范围明确后再创建 Task Sheet，不把 Agent 猜测写成正式计划。

如果 `00_project_records/` / `task_index.md` 尚不存在，则先完成最小 Project initialization，再创建首张 Task Sheet。

`已完成` / `已终止` Task Sheet 不作为 automatic active candidate；需要时可以被后续 Task Sheet 明确引用为历史、prerequisite 或正式结果来源。

## New Task Sheet boundary

以下情况通常继续使用当前 `未完成` Task Sheet：

- 当前执行范围仍然清晰且上下文规模合理；
- 只是检查、解释、排错或继续当前 Task Sheet 中已经规划的工作；
- 当前计划没有因为大量废弃/错误方案而失去可恢复性。

以下情况可以为**同一个科研任务**建立新的 Task Sheet：

- 当前执行范围需要拆分以控制单张任务单的上下文规模；
- 需要把已经废弃或错误的方案与后续有效执行上下文隔离；
- 当前科研任务进入新的有界执行段，使用新 Task Sheet 更利于恢复；
- 原 Task Sheet 已完成 / 已终止，而用户要求继续同一科研任务的新执行段；
- 用户明确要求新建 Task Sheet。

新的独立科研目标同样可以建立新的 Task Sheet，但“新 Task Sheet”和“新科研任务”不是同义概念。

新 Task Sheet ID 使用当前项目下一个可用 `TNNN`。如果它继续同一科研任务，并且当前执行依赖前序 Task Sheet 的正式结果、prerequisite 或决策，应在新 Task Sheet 的最小恢复上下文中保留可定位的前序来源。

创建时：

1. 在 `task_index.md` 登记；
2. 创建 `tasks/Txxxx.md`；
3. 根据当前已明确的执行范围和 `workflow_plan_index.yaml` 写入初始计划；
4. 普通 Step 只记录未来 task-specific 工作目录路径，不创建目录。

## Initial planning

Manager 规划只回答：

> 为覆盖当前这张 Task Sheet 的执行范围，需要列出哪些已定义 Step 或 stage-specific plan structure？

Task Sheet 不要求覆盖完整 Workflow 或完整 Stage。它可以只承载一个科研任务的局部执行段，但不能因为拆单而跳过 scientific Skill 已明确规定的 prerequisite。

Manager：

- 只围绕当前 Task Sheet 的已明确执行范围规划，不为了流程完整补入整个 Stage；
- 使用 planning index 的顺序、名称、基础目录和明确的 planning mode；
- 当当前 Task Sheet 规划从某个中间 Step 开始时，确认其结构性 prerequisite 已由当前或被明确引用的前序 Task Sheet 提供；
- 当用户明确请求完整 Stage 范围时，按 planning index 的完整 Stage planning 规则展开；
- 遵守 planning index 中显式的 initial-planning 范围，例如仅在用户范围明确包含 topology validation 时规划 2.6；
- 不读取全部科研 Skills；
- 不提前查 `project_result_index.md`；
- 不做科学 applicability / reuse 判断；
- 不根据体系特征提前删减**已经属于当前执行范围**的普通 Step；
- 对未定义 catalog 的 Stage 不编造内部步骤。

Manager 不用 planning index 替用户决定仍未明确的执行范围。执行范围有歧义时先确认，再写入初始计划。

Task Sheet 是可动态维护的执行计划，不是完整 Workflow 的强制投影。

### Ordinary Stage planning

Stages 1–2 使用普通 sub-stage Task Sheet planning。

普通 Step 至少记录：状态、对象、工作目录；对象尚未形成时不猜测具体文件路径。

普通 sub-stage 状态：

```text
未完成
已完成
已终止
```

Stage 1 与 Stage 2 当前都不设置 stage main Skill。Task Execution Agent 直接进入当前 Task Sheet 所对应的 current Step Skill。

Stage 1 的局部 Task Sheet 可以从中间 Step 开始，只要当前 Step 的真实输入契约已经由前序 Task Sheet或正式结果满足。

Stage 2 额外存在固定 setup prerequisite：

```text
2.1 Topology preparation setup
→ 为 2.2–2.5 提供适用于当前体系和处理范围的拆分 / 处理方案
```

因此：

- 一张 Task Sheet 如果包含 2.1，并继续执行 2.2–2.5，可以直接使用当前 2.1 形成的方案；
- 一张后续 Task Sheet 可以只包含 2.2、2.3、2.4 或 2.5，但必须能够定位同一科研任务前序 Task Sheet 中适用于当前体系和处理范围的已完成 2.1 方案；
- 如果没有可定位且仍适用的 2.1 方案，则当前执行范围必须先安排 2.1，不能因为换了 Task Sheet 就绕过 setup；
- 不要求为了形式在每张后续 Task Sheet 中重复复制 2.1。

2.6 是否进入初始计划按 planning index 的显式范围处理。

### Stage 3 planning

Stage 3 不设置编号化 sub-stage。当前 Task Sheet 范围包含体系构建时，Manager 建立一个 stage-level 条目：

`3 System construction / solvation`

该条目记录当前体系构建目标、处理对象、已经明确的约束，以及：

`<project_root>/03_md_preparation/<task_id>/`

作为 task-specific 工作目录。Stage 3 当前只有 stage main Skill；具体 operation plan 由该 Skill 在执行期补充并维护。

### Stage 4 planning exception

Stage 4 不把 Task Sheet 写成固定 `4.1 → 4.2 → 4.3`。

Manager 根据当前已明确的模拟需求建立 planned run route，记录计划中的 EM/NVT/NPT/MD segments 和关键要求，但不提前分配 formal `em.N / nvt.N / npt.N / md.N` IDs。

Formal run-unit identity、reuse / continuation / new-unit 判断由 Stage 4 main Skill：

`04_md_simulation/SKILL.md`

在 planned entry 真正开始时处理；4.1 / 4.2 / 4.3 是由 Stage 4 main Skill 按实际 run class 调用的执行层，不作为 Manager 初始 Task Sheet 的固定串行子步骤。

### Stage 5 planning

Stage 5 不设置编号化 sub-stage。如果当前 Task Sheet 范围包含 Analysis，Manager 只建立一个 stage-level 条目：

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
科研执行入口
→ 先完成 Task Sheet resolution
→ 已有唯一相关未完成 Task Sheet：绑定并进入执行
→ 无相关未完成 Task Sheet：Manager 创建后交接

Stage 1
→ 无 stage main Skill
→ 直接进入当前 Task Sheet 所对应的 1.x entry

Stage 2
→ 无 stage main Skill
→ 2.1 setup prerequisite 可来自当前或明确关联的前序 Task Sheet
→ 直接进入当前 Task Sheet 所对应的 2.x entry

Stage 3
→ 03_md_preparation/SKILL.md
→ stage main only

Stage 4
→ 04_md_simulation/SKILL.md
→ 由 Stage 4 main Skill 按 planned run route 调用 4.1 / 4.2 / 4.3

Stage 5
→ 05_analysis/SKILL.md
→ 由 Stage 5 main Skill 读取 current capability inventory 并调度 capability entries
```

Manager 初始规划时不需要因此读取上述科研 Skill；Task Execution Agent 在实际进入对应 Stage / Step 时读取 planning index 指向的 current runtime entry。

## Project initialization

新项目只建立稳定项目骨架和 planning index 已定义的 Stage / Step base directories；不提前创建 task-specific 科研目录。

如果 `00_project_records/` 不存在，Manager 在第一次需要创建 Task Sheet 时建立：

```text
00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
```

随后创建首张 Task Sheet。

Manager 在普通 Step 的 Task Sheet 条目中记录 `<base_work_directory>/<task_id>/`，但不创建该目录。

Task Execution Agent 真正进入某普通 Step 后，按该 current Skill 判断当前工作如何执行。只有 current Skill 实际定义 reuse 机制时才按其规则处理；没有 reuse 机制的 Step 不由 Manager 或 Task Execution Agent 额外补设 reuse。只有需要本地执行时才创建当前 task-specific directory。

Stage-specific project-level directories / indexes 或 stage-level planning structure 由实际拥有该职责的 current Stage / Step Skill 管理，不由 Manager 发明额外 runtime state。

## Dynamic plan and handoff

默认入口与交接：

```text
unresolved scientific execution request
→ Manager reads task_index.md
→ locate active Task Sheet OR create Task Sheet
→ initial planning when creating
→ write / bind Txxxx.md
→ Task Execution Agent continuously executes and maintains the current Task Sheet
```

需要拆分新的 Task Sheet 时，可以再次进入 Manager 创建后续执行单；这不代表对应科研任务重新开始，也不使已经满足的 prerequisite 失效。

普通 Step 之间不回 Manager 调度，也不重复扫描 `task_index.md`。

## Explicit replanning

用户明确要求重新规划时，Manager 可以读取 current Task Sheet + `workflow_plan_index.yaml`，整理尚未完成的计划。

Stage-specific plan structures 遵守对应 current owner；Manager 不在本文件复制其内部规则。

## Safety

- 不修改 `01_sources/` 原始来源文件；
- 未经用户授权，不删除、覆盖或批量移动科研文件；
- 不以“全面了解”为理由扫描无关文件；
- 不自动通过单位计费的期刊数据库下载文献；
- 破坏性 / 不可逆项目级操作必须取得用户确认。

## Manager output

定位已有 Task Sheet 后，只需简要说明实际绑定的 Task Sheet；创建或重新规划后只展示必要信息：

- Task Sheet ID / 名称；
- Task Sheet 状态；
- 当前计划；
- Task Sheet 路径；
- 若为同一科研任务的后续拆分单，必要时注明其前序 Task Sheet。

不展示 Legacy route、Workstream、transaction、event 或内部 orchestration state。

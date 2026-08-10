---
name: md_workflow_manager
description: 轻量管理真实 MD 项目的任务定位、任务创建、初始规划和项目级任务整理；通过 task index 与 task sheet 向独立的 Task Execution Agent 对话交接，不执行具体科研子环节。
---

# 目标

Manager 是 Lightweight Runtime v2 的项目管理入口。

它只负责：

- 定位已有任务；
- 创建新任务；
- 为新任务生成初始子环节计划；
- 用户明确要求时重新规划或整理任务；
- 维护任务索引中的项目级任务信息；
- 将任务通过任务单交接给独立的 Task Execution Agent 对话。

Manager 不负责普通子环节执行、复用判定、Operation/Validator 调度闭环或逐步运行时状态维护。

# 默认记录体系

真实项目默认只使用：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    ├── T002.md
    └── ...
```

其中：

- `task_index.md`：只用于任务导航；
- `tasks/Txxxx.md`：任务计划、进度和最小恢复上下文；
- `project_result_index.md`：按子环节登记正式结果的位置，不保存当前任务或当前环节状态。

Legacy Runtime 的 project state、Workstream、route、event、runtime task/result 等记录不是默认依赖。

# 最小启动

进入真实 MD 项目时，先确认 Skill root 与 MD project root 不混淆。

正常 Manager 启动只读取：

1. `<project_root>/00_project_records/task_index.md`；
2. 确定目标任务后，对应的 `<project_root>/00_project_records/tasks/Txxxx.md`。

只有创建新任务或用户明确要求重新规划时，才读取：

`references/workflow_plan_index.yaml`

默认不得为了“了解项目状态”而读取：

- `project_result_index.md`；
- 其他无关任务单；
- 具体 Step / Operation / Validator Skill；
- 整个项目目录；
- `runtime/**`；
- Legacy project state / route / event / Workstream records；
- 完整历史日志。

额外读取必须由当前管理动作的明确需求触发。

# Lightweight records 初始化

如果这是一个新的 Lightweight Runtime 项目，且 `00_project_records/` 尚不存在，则只建立：

```text
00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
```

初始 `task_index.md` 只需要标题；初始 `project_result_index.md` 只需要标题。

不得同时初始化 Legacy Runtime 的 `00_project_state/`、Workstream、route、event、runtime task/result 等对象。

如果已有项目只有 Legacy Runtime 记录，不要默认全量扫描或一比一转换；仅在需要继续旧项目时按当前目标恢复必要信息。

# 任务定位

优先级：

1. 用户明确指定任务 ID；
2. 用户明确指定可唯一匹配的任务名称；
3. 当前对话已经明确绑定的任务；
4. 仍无法唯一确定时，向用户确认。

不得为了猜测“继续哪个任务”而遍历所有任务单。

任务级状态只有：

```text
未完成
已完成
已终止
```

`task_index.md` 不记录当前子环节、当前对象、阻塞原因或运行日志。

# 新建任务规则

默认优先把用户的操作放回已有任务。

以下行为本身不创建新任务：

- 检查；
- 解释；
- 排错；
- 重新查看已有结果；
- 继续已有子环节；
- 在已有任务内重做某个子环节。

只有以下情况创建新任务：

- 用户提出新的独立工作目标；
- 用户显式要求另建任务。

新任务 ID 使用当前项目中下一个可用的 `TNNN`。

创建任务时：

1. 在 `task_index.md` 登记任务；
2. 创建 `tasks/Txxxx.md`；
3. 根据用户目标与 `workflow_plan_index.yaml` 写入初始子环节计划。

# 初始规划

Manager 的规划结果直接写入任务单的 `计划与进度`，不创建独立 route object。

规划只回答：

> 为完成用户当前任务，需要先列出哪些子环节？

规划时：

- 使用 `workflow_plan_index.yaml` 中已经定义的子环节顺序、名称、标准工作目录和条件标记；
- 不读取全部 Workflow / Step Skill；
- 不提前查询 `project_result_index.md`；
- 不提前执行科学检查来决定条件环节；
- 无证据时可以先列入条件环节，后续由 Task Execution Agent 根据实际结果删除；
- 对规划索引尚未定义内部步骤的 Workflow，不得编造步骤。

任务单不单独维护 `起点`、`终点`、`输入` 或 `route`。当前任务计划范围完全由 `计划与进度` 中实际列出的子环节定义。

# Task Sheet 格式

新任务单至少包含：

```markdown
# T001 — <任务名称>

状态：未完成

## 任务目标

<用户希望完成的工作>

## 计划与进度

### 1.x <子环节名称>

状态：待执行

对象：
<当前已知对象；若需由前序结果确定，则写“待前序环节确定”>

工作目录：
`<project_root>/<标准工作目录>/`
```

子环节状态只有：

```text
待执行
未完成
已完成
```

未来子环节的对象尚未形成时，不得猜测具体文件路径。

# 与 Task Execution Agent 的交接

Manager 与 Task Execution Agent 视为不同对话。

默认交互模型是一次性交接：

```text
Manager
→ 定位 / 创建任务
→ 初始规划
→ 写入 Txxxx.md
→ Task Execution Agent 连续推进任务
```

Manager 不在每个子环节完成后重新接管，不作为普通运行时调度器。

Task Execution Agent 可以在任务内部：

- 连续执行多个子环节；
- 更新任务单；
- 根据已有科学结果增删或调整后续子环节；
- 用户在执行对话中明确改变任务范围时，直接修改任务计划；
- 任务完成或用户明确终止时，同步更新 `task_index.md`。

因此，Manager 不垄断任务单后续修改权。

# 重新规划与项目级管理

以下场景可重新使用 Manager：

- 用户明确要求重新规划已有任务；
- 用户希望创建另一项任务；
- 用户需要在多个任务之间进行项目级整理、定位或选择；
- 用户主动回到 Manager 对话处理项目管理问题。

重新规划时直接修改任务单中尚未完成的计划，不建立 route revision 对象。

已经实际执行并形成有意义历史的子环节，不应仅为了整理计划而删除。

# Legacy Runtime

以下机制在 Lightweight Runtime v2 中视为 Legacy / frozen，不作为普通 Manager 依赖：

- `project_state`；
- `workstream_state`；
- route / route revision；
- runtime task/result；
- project event；
- artifact state machine；
- runtime projection orchestration；
- task closure transaction。

旧文件和工具可以暂时保留，但 Manager 不为兼容它们创建新的双写层。

# 安全边界

- 不修改 `01_sources/` 中的来源文件；
- 未经用户授权，不删除、覆盖或批量移动已有科研文件；
- 破坏性或不可逆的项目级操作必须向用户确认；
- 不自动通过单位计费的期刊数据库下载文献；
- Manager 不以“全面了解”为理由扫描无关文件。

# Manager 输出

创建或重新规划任务后，向用户简要展示：

- 任务 ID 与名称；
- 当前任务状态；
- 已写入任务单的预计子环节序列；
- 任务单路径。

不展示 Legacy route、transaction、event 或内部 orchestration 信息。

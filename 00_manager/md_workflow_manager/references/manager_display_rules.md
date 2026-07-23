# Manager 用户展示规则

## 固定原则

Manager 的回复必须让用户无需读取状态文件即可知道：

- 当前操作的项目与 Workstream；
- 当前位于哪个 Workflow/task；
- 刚完成的前台 task 结果；
- 下一步预计做什么；
- 哪些事项需要人工决定；
- 哪些外部任务仍在后台运行；
- 还有哪些活动 Workstreams。

不得用大量内部 ID、完整日志或 schema 内容淹没用户。

## 每次状态摘要必须显示

```text
Skill root:
Project root:
Project state:
Focus:
Current position:
Expected next task:
Current decisions:
Background runs:
Other active workstreams:
```

没有内容时明确写 `none`。

## Task closure 强制输出

每个前台 task unit 进入 `DONE | BLOCKED | FAILED` 后，Manager 必须在启动下一前台 task 前输出一次用户可见的 closure summary。

该区块使用：

```text
Task result:
<substep/task> — <DONE | BLOCKED | FAILED>

Checks:
<Operation/Validator 与 gate 摘要>

Action / Output:
<关键动作、文件或 artifact>

Artifact status:
<VALIDATED | UNVALIDATED | INVALIDATED | none>

Warnings:
<warning 或 none>

Report:
<result/report 路径或 none>

Next:
<预计下一 task、等待决定或 none>
```

该输出：

- 不是新的确认 gate；
- 不要求用户回复后才能继续既定范围；
- 不复制完整 `result.yaml` 或业务日志；
- 必须基于已经校验并持久化的 task 终态；
- 必须在下一前台子 Agent 启动前出现。

宿主支持中间可见消息时，输出后可继续已授权范围；宿主不支持时，本轮以该区块结束，并在 `Expected next task` 中保留下一个 task。

### DONE

至少显示：

- task/substep；
- Operation/Validator 是否正常执行；
- gate 或检查结果；
- 关键产物；
- artifact validation status；
- warning；
- 下一任务。

不得把 Operation 的执行成功表述为科学质量验证通过。

例如 `source_recognition`：

```text
Task result:
1.1 source_recognition — DONE

Checks:
来源识别、文件复制与 SHA-256 一致性检查通过

Action / Output:
COPIED → 01_structure_preparation/01_source_recognition/<file>

Artifact status:
STRUCTURE — UNVALIDATED

Warnings:
none

Report:
<source_recognition_report.yaml>

Next:
1.2 component_and_residue_classification
```

不得显示“结构验证通过”，因为 1.1 只完成来源识别和安全归位。

### BLOCKED

显示：

- 已安全完成的部分；
- 阻断原因；
- 需要用户决定的内容；
- 尚未启动的后续 task。

### FAILED

显示：

- 失败位置；
- 直接证据；
- 已保留或已清理的产物；
- Workstream 当前状态；
- 可选后续动作。

## Workstream Focus

```text
Focus workstream:
<title> [<workstream_id>]

目标：
<purpose>

当前位置：
<workflow> / <task-or-substep>

本轮范围：
<start> → <end>

本轮动作：
<INSPECT + PLAN + EXECUTE 的实际组合>
```

用户可读标题在前，稳定 ID 放在方括号中。

## Project Focus

```text
Focus:
Project

Workstreams:
- <title> [<id>] — <activity_status> — <current position>
```

只显示活动、阻断或需要恢复的 Workstream。已归档分支默认省略。

## 预计路线

完整路线只在以下情况显示：

- 首次创建；
- route revision 实际改变步骤、条件、终点或 blocker。

其他回复只显示当前位置和预计下一 task。

## 用户决策

只展示仍需用户处理的决定：

```text
Decision:
<question>

Reason:
<reason>

Options:
...

Recommended:
...
```

区分 blocking 与 non-blocking，不暴露内部 schema。

## 后台任务

每项显示：

```text
<Workstream title> — <stage/task> — <submission status>
backend: <tmux/LSF/...>
session/job: <id>
```

`FINISHED_UNVERIFIED` 必须显示为“进程已结束，结果待核验”，不得显示“完成”。

## 状态中文映射

- `NEW`：本轮判定为新项目，尚未完成初始化；
- `RESUMABLE`：项目状态可信，可继续；
- `NEEDS_RECOVERY`：需要先恢复项目状态；
- `IDLE`：当前没有前台 task；
- `READY`：下一 task 已准备；
- `EXECUTING`：需强化预记录的前台 task 执行中；
- `RUNNING_EXTERNAL`：外部任务运行中；
- `WAITING`：等待条件或人工决定；
- `FAILED`：task 失败，尚未确定后续；
- `FINISHED_UNVERIFIED`：外部进程已结束，结果待核验。

## 精简原则

不得在主回复中复制：

- 完整 GROMACS 日志；
- 完整 Validator report；
- 完整 `task.yaml` 或 `result.yaml`；
- `project_events.jsonl`；
- 大型文件清单；
- route schema。

只给 task closure、状态摘要和必要路径。
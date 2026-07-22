# Manager 用户展示规则

## 固定原则

Manager 的回复必须让用户不读取状态文件也能知道：

- 当前操作的是哪个项目；
- 当前主要处理哪个 Workstream；
- 当前位于什么 Workflow/task；
- 下一步预计做什么；
- 哪些事项需要人工决定；
- 哪些外部任务仍在后台运行；
- 还有哪些活动 Workstream。

不得用大量内部 ID、完整日志或 schema 内容淹没用户。

## 每次必须显示

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

没有内容时明确写 `none`，不要省略字段。

## Workstream Focus

显示格式：

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

用于全项目检查或恢复：

```text
Focus:
Project

Workstreams:
- <title> [<id>] — <activity_status> — <current position>
```

只显示活动、阻断或需要恢复的 Workstream。已归档分支默认省略。

## 预计路线

完整路线只在：

- 首次创建；
- route revision 实际变化；

时展示。

其他回复只显示：

```text
Current position:
Expected next task:
```

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

区分 blocking 与 non-blocking，不暴露内部 decision schema。

## 后台任务

每项显示：

```text
<Workstream title> — <stage/task> — <submission status>
backend: <tmux/LSF/...>
session/job: <id>
```

`FINISHED_UNVERIFIED` 必须显示为“进程已结束，结果待核验”，不得显示“完成”。

## 状态中文映射

- `NEW`：新项目，尚未建立可信状态；
- `RESUMABLE`：项目状态可信，可继续；
- `NEEDS_RECOVERY`：需要先恢复项目状态；
- `READY`：下一任务已准备；
- `EXECUTING`：前台任务执行中；
- `RUNNING_EXTERNAL`：外部任务运行中；
- `WAITING`：等待条件或人工决定；
- `FAILED`：任务失败，尚未确定后续；
- `FINISHED_UNVERIFIED`：外部进程已结束，结果待核验。

## 精简原则

不得在主回复中复制：

- 完整 GROMACS 日志；
- 完整 Validator report；
- `task.yaml` 或 `result.yaml`；
- `project_events.jsonl`；
- 大型文件清单；
- route schema。

只给摘要和必要路径引用。

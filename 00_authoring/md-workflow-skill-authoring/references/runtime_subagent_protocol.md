# 串行临时子 Agent 协议

## 目的

临时子 Agent 用于隔离大型结构文件、命令输出、详细日志、中间候选、局部排错和 Validator findings，减少主上下文污染。

它不用于提高前台并行度。

## Workstream 与并行边界

- 一个项目可以存在多个 Workstream；
- 多个 tmux 或调度系统外部任务可以同时运行；
- 任意时刻最多一个前台 MD 临时子 Agent；
- 外部任务运行不等于前台子 Agent 并行；
- 临时子 Agent 不得创建或调用其他子 Agent。

## 创建条件

Manager 只有在以下条件全部满足时才创建临时子 Agent：

- 项目已初始化或为可信 RESUMABLE；
- 路线范围已明确；
- active route 有效；
- Focus 已解析为具体 Workstream；
- Workflow 返回 `decision: EXECUTE`；
- `next_task_unit` 符合 `workflow_decision.schema.yaml`；
- 当前没有活动前台子 Agent；
- 输入、工作目录和路径权限已解析；
- 不可变 `task.yaml` 已写入；
- task 包符合 `subagent_task.schema.yaml`。

简单项目索引读取可由主智能体完成，但不得绕过 Workflow 的业务路线。

## 任务单元

一个临时子 Agent 只执行一个上下文连续任务单元：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

`OPERATION_WITH_VALIDATOR` 只用于专属 Validator 需要共享前一 Operation 即时上下文的情况。

即使在同一子 Agent 中连续执行：

- Operation 和 Validator 职责仍分离；
- Validator 不得修改被验证对象；
- 两部分结果必须分别记录；
- 不能合并成模糊的“成功”。

独立 Validator 和阶段终检 Validator 使用单独 task unit。

## 最小任务包

Manager 只传递当前 task 所需信息：

- task ID、Workstream ID、Workflow 名称和 route ID；
- task unit mode；
- Operation/Validator Skill 名称和路径；
- 项目根与工作目录；
- 允许读取、允许写入和禁止访问路径；
- 当前有效输入；
- 精简上游摘要；
- resolved decisions；
- 必需输出与详细日志目标；
- 返回 contract。

不得传入完整对话、全部项目日志、全部 Workstream 状态或无关 Skill。

## 管理目录写权限

临时子 Agent 不得直接修改：

```text
00_project_state/**
00_project_records/**
```

子 Agent 只能：

- 在授权业务目录写 Operation 输出；
- 在授权位置写详细日志、报告和结果数据；
- 返回符合 `subagent_result.schema.yaml` 的结构化结果。

Manager 是状态、事件、route、task result、decision、submission、artifact 和 snapshot 的唯一提交者。

## 返回要求

子 Agent 返回：

- task ID、Workstream ID 和 task unit mode；
- 总体终态；
- 精简执行摘要；
- 分开的 Operation result 与 Validation result；
- artifact candidates；
- confirmation items；
- warnings 或 failure；
- 详细日志和报告路径；
- 下一步建议。

详细中间信息必须落盘，不得完整回灌主上下文。

## 用户交互

子 Agent 不直接向用户提问。

需要确认时：

1. 完成仍可安全完成的部分；
2. 返回 `confirmation_items`；
3. Manager 创建或更新 decision record；
4. Manager 向用户展示；
5. 用户决定由 Manager 落盘；
6. Manager 更新 Workstream，并重新进行范围解析、规划或 Workflow 判断。

是否需要确认由非空 decision request 及其 `blocking` 字段表达，不维护重复布尔字段。

## 普通前台 task 生命周期

普通前台 task 指短耗时、当前进程内完成、无外部 submission 且无难以恢复的高风险副作用。

```text
Workflow 返回 EXECUTE
→ Manager 写 task.yaml
→ 创建一个临时子 Agent
→ 子 Agent 执行并写业务日志
→ 子 Agent 返回 subagent_result
→ Manager 校验并写 result.yaml
→ 必要时注册 artifact/decision/submission
→ Manager 追加一条终态 event
→ Manager 原子更新目标 Workstream state
→ Manager 输出 task closure summary
→ 释放子 Agent 上下文
→ 再次请求 Workflow
```

普通 task 默认不需要：

- `TASK_PREPARED`；
- `TASK_STARTED`；
- 执行前把 Workstream 改为 EXECUTING；
- 无变化的 project state 更新；
- Manager session 逐 task 写入；
- snapshot；
- 无变化 route revision。

`task.yaml` 存在但 `result.yaml` 缺失时，恢复流程必须将其视为未闭环 task，而不是假定未启动或已完成。

## 强化预记录生命周期

以下 task 必须在副作用前建立恢复锚点：

- 外部 submission；
- 长耗时 task；
- 高风险或不可逆操作；
- 中断后必须准确区分“未启动”和“已启动”的 task；
- Workflow/Operation 明确要求预提交记录。

```text
写 task.yaml
→ TASK_PREPARED
→ Workstream EXECUTING
→ 必要时 TASK_STARTED
→ 创建子 Agent并产生副作用
→ result/相关记录/终态 event
→ 更新 Workstream
→ 输出 task closure summary
```

## Task closure 可见性

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，Manager 必须在下一前台子 Agent 启动前输出用户可见的精简结果。

该摘要不是新的结构化记录或确认 gate。

宿主支持中间可见消息时，输出后可继续既定范围；宿主不支持时，本轮以 closure summary 结束，下一 task 留待后续交互。

不能依赖已结束子 Agent 的内部记忆。所有可复用信息必须进入业务文件、结构化记录或当前状态。
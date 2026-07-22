# 串行临时子 Agent 协议

## 目的

临时子 Agent 用于隔离大型结构文件、命令输出、详细日志、中间候选、局部排错和 Validator findings，减少主智能体上下文污染。

它不用于提高前台并行度。

## Workstream 与并行边界

- 一个项目可以同时存在多个 Workstream；
- 多个 tmux 或调度系统外部任务可以同时运行；
- 任意时刻最多一个前台 MD 临时子 Agent；
- 外部任务运行不等于前台子 Agent 并行；
- 临时子 Agent 不得再创建或调用其他子 Agent。

## 创建条件

Manager 只有在以下条件全部满足时才创建临时子 Agent：

- 当前 Focus 已解析为具体 Workstream；
- Workflow 返回 `decision: EXECUTE`；
- `next_task_unit` 符合 `03_contracts/workflow_decision.schema.yaml`；
- 当前没有活动前台子 Agent；
- 必需输入、工作目录和路径权限已解析；
- Manager 已写入不可变 `task.yaml`；
- 任务包符合 `03_contracts/subagent_task.schema.yaml`。

简单且不会污染上下文的项目索引读取可由主智能体完成，但不得借此绕过 Workflow 的局部业务路线。

## 任务单元

一个临时子 Agent 只执行一个上下文连续任务单元：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

`OPERATION_WITH_VALIDATOR` 仅用于某个 Validator 专门服务于前一个 Operation，且需要共享该 Operation 的即时上下文时。

即使由同一子 Agent 连续执行：

- Operation 和 Validator 的职责仍然分离；
- Validator 不得修改被验证对象；
- 两部分结果必须在 `subagent_result` 中分别记录；
- 不能将两者合并成一个无区分的“成功”。

独立 Validator、阶段终检 Validator 或不依赖即时上下文的 Validator 使用单独任务单元。

## 最小任务包

Manager 只传递当前任务需要的信息：

- task ID、Workstream ID、Workflow 名称和可选 route ID；
- task unit mode；
- Operation 与/或 Validator 的 Skill 名称和路径；
- 项目根目录与工作目录；
- 允许读取、允许写入和禁止访问的路径；
- 当前有效输入文件；
- 精简上游摘要；
- 已解决的用户决策；
- 必需输出与详细日志目标路径；
- 返回 contract。

不得传入完整对话、全部项目日志、全部 Workstream 状态或无关 Skill。

## 管理目录写权限

临时子 Agent 不得直接修改：

```text
00_project_state/**
00_project_records/**
```

子 Agent 只能：

- 在任务授权的业务目录写入 Operation 输出；
- 在授权位置写入详细日志、报告和结果数据；
- 返回符合 `subagent_result.schema.yaml` 的结构化结果。

Manager 是项目状态、事件、路线、任务结果、决策、submission、artifact set 和 snapshot 记录的唯一提交者。

## 返回要求

子 Agent 返回：

- task ID、Workstream ID 和 task unit mode；
- 总体终态；
- 精简执行摘要；
- 分开的 Operation result 与 Validation result；
- artifact candidates；
- 用户决策请求；
- warning 或 failure；
- 详细日志和报告路径；
- 下一步建议。

详细中间信息必须落盘，不得完整回灌主上下文。

## 用户交互

子 Agent 不直接向用户提问。

遇到需要确认的事项时：

1. 完成仍可安全完成的部分；
2. 返回 `confirmation_items`；
3. Manager 创建或更新 decision record；
4. Manager 统一向用户展示；
5. 用户决定由 Manager 落盘；
6. Manager 更新 Workstream 状态并再次请求 Workflow 判断。

是否需要用户确认由非空决策请求及其 `blocking` 字段表达，不另维护可冲突的重复布尔字段。

## 生命周期

```text
Workflow 对 Focus Workstream 返回决定
→ Manager 写 task.yaml 和 TASK_PREPARED 事件
→ Manager 原子更新 Workstream 为 EXECUTING
→ 创建一个临时子 Agent
→ 子 Agent 执行 task unit 并写业务日志
→ 子 Agent 返回精简结构化结果
→ Manager 写 result.yaml
→ Manager 注册 artifact/decision/submission 记录
→ Manager 追加终态事件
→ Manager 原子更新 Workstream 与项目索引
→ 释放子 Agent 上下文
→ 再次请求 Workflow 决策
```

不能依赖已结束子 Agent 的内部记忆。所有可复用信息必须进入业务文件、结构化记录或当前状态。

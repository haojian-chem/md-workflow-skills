# 串行临时子 Agent 协议

## 目的

临时子 Agent 用于隔离：

- 大型结构文件内容；
- 命令和日志输出；
- 中间候选列表；
- 局部错误排查；
- Validator 的详细 findings；
- Operation 的机械执行过程。

它的目标是减少主智能体上下文污染，而不是提高并行度。

## 创建条件

只有同时满足以下条件时，Manager 才创建临时子 Agent：

- Workflow 返回 `decision: EXECUTE`；
- `next_task.skill_type` 为 `operation` 或 `validator`；
- 当前没有活动子 Agent；
- 必需输入已解析；
- 读写路径已明确；
- 任务包符合 `03_contracts/subagent_task.schema.yaml`。

简单且不会污染上下文的纯状态读取可由主智能体完成，但不得借此绕过 Workflow 的业务路线。

## 串行限制

- 任意时刻最多一个活动 MD 子 Agent；
- 当前任务结束、结果落盘且项目状态更新后，才能创建下一个；
- 当前版本不支持任何 MD 多任务并行调度；
- 理论上可并行的分析在当前版本仍按串行执行。

## 单层限制

只允许：

```text
主智能体 → 临时子 Agent
```

临时子 Agent 不得创建、调用或请求其他子 Agent。

## 最小任务包

Manager 只传递当前任务需要的信息：

- task ID；
- Skill 名称和路径；
- 项目根与工作目录；
- 允许读取、写入和禁止访问的路径；
- 当前有效输入文件；
- 精简上游摘要；
- 已确认的用户决策；
- 必需输出；
- 返回 contract。

不得把完整对话、全部项目日志或无关 Skill 全部传入。

## 返回要求

子 Agent 只返回：

- 执行状态；
- 一段精简执行摘要；
- 关键 findings；
- 创建、修改、验证的文件；
- 用户确认事项；
- warning 或 failure；
- 详细日志和报告路径；
- 下一步建议。

详细中间信息必须写入文件，不完整回灌主上下文。

## 用户交互

子 Agent 不直接向用户提问。

遇到需要确认的事项时：

1. 完成仍可完成的处理；
2. 汇总确认事项；
3. 返回 Manager；
4. Manager 统一向用户展示；
5. 用户决策写入项目状态；
6. Manager 再次请求 Workflow 决定下一步。

## 生命周期

```text
Workflow 决策
→ Manager 构建任务包
→ 创建临时子 Agent
→ 子 Agent 执行并落盘
→ 返回精简结果
→ Manager 核验结果
→ 更新项目状态
→ 释放子 Agent 上下文
→ 再次请求 Workflow 决策
```

不能依赖已结束子 Agent 的内部记忆。所有可复用信息必须落盘或进入项目状态。

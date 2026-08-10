---
name: <operation-skill-name>
description: <当前科研 Step 的具体操作及排除边界>。
---

# 目标

# 职责边界

Operation 执行明确业务操作，不承担项目级任务规划、Workflow 阶段编排或 Legacy runtime closure。

如果本 Operation 是当前 Step 的主要执行 Skill，应明确以下接口。

# Lightweight Runtime 接口

## Purpose

当前 Step 要完成什么。

## Object requirements

明确当前 Task Sheet `对象` 必须提供什么，以及允许的对象形式。

不得依赖全项目扫描来猜测输入。

## Reuse conditions

列出真正决定本 Operation 输出是否等价的最少条件。

统一语义：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
无法判断 → Task Execution Agent 向用户确认
用户明确重做 → 不复用
```

## Execution rules

只写当前 Operation 的实际操作规则。

## Validation requirements

如果有专属 Validator，由 Validator 拥有详细规则；本节只引用其 Skill 和说明完成前必须验证。

没有专属 Validator 时，在此定义操作闭合所需的验证。

## Official results

明确要登记到 `project_result_index.md` 的正式结果文件。

区分 official results 与中间、debug、recovery 文件。

# 工作目录

基础目录：

```text
<base_work_directory>/
```

当前 Task 实际执行目录：

```text
<base_work_directory>/<task_id>/
```

Task Execution Agent 必须先检查 reuse；只有确实需要本地执行时才创建 `<task_id>/`。

不同 Task 不得把固定文件名正式结果写到共同基础目录。

# Preflight

确认：

- 当前 Task Sheet Step 与本 Skill 匹配；
- 对象满足要求；
- 工作目录属于当前 Task；
- 必需软件/依赖可用；
- 所有将要写入的路径明确；
- 不覆盖其他 Task 正式结果；
- 需要用户确认的事项已经解决。

Preflight 不通过时不得留下可误认成正式完成的结果。

# 执行

# 完成与回写

当前 Step 完成后，由 Task Execution Agent：

- 更新 Txxxx.md；
- 登记 official results；
- 根据结果调整后续计划。

Operation 不创建 route / Workstream / event / runtime task-result。

# 用户确认

列出必须由用户决定的科学歧义。

由当前 Task Execution Agent 在同一个执行对话中提出；不返回 Manager decision record。

# Tool

如使用确定性 Tool，说明 Tool 名称、明确业务输入输出和失败回退。

不得为了调用旧 Tool 构造 Legacy task.yaml / route / transaction 对象。

# 自检

- [ ] object requirements 明确；
- [ ] reuse conditions 明确；
- [ ] task-scoped 工作目录正确；
- [ ] official results 明确；
- [ ] 未复制专属 Validator 的详细规则；
- [ ] 未创建 Legacy runtime 管理对象。

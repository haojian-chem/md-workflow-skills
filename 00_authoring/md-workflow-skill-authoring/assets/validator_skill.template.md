---
name: <validator-skill-name>
description: <当前科研 Step 的检查、分类或质量判定及排除边界>。
---

# 目标

# 职责边界

Validator 读取并检查目标对象，输出科学/技术判定；默认不修改被验证对象，也不承担项目级任务规划或 Legacy runtime closure。

如果本 Validator 是 Validator-only Step，应完整定义当前 Step 的 Lightweight 接口。

如果它是 Operation 的专属配套 Validator，应只拥有验证侧规则，并由 content map 避免与 Operation 重复。

# Lightweight Runtime 接口

## Purpose

说明当前 Validator 在本 Step 中要判定什么。

## Object requirements

明确被验证对象和必要上下文。

Validator-only Step 在此完整定义对象要求；配套 Validator 可以引用 Operation 已定义的共同对象接口，只补充验证独有输入。

## Reuse conditions

Validator-only Step 必须定义完整复用条件。

配套 Validator 如果其验证结果可独立复用，应定义验证结果有效性的条件；否则引用 Step 主执行 Skill 的 reuse owner，不复制规则。

## Execution rules

说明检查、分类或验证流程。

## Validation requirements

这是 Validator 的主要权威内容。

必须区分：

```text
Validator 成功执行
vs
被检查对象是否满足科学/技术要求
```

对象“不通过”不等于 Validator 程序执行失败。

## Official results

Validator-only Step：明确 Step 正式结果。

配套 Validator：明确验证报告是否属于 Step official results；如果不是，只保留为当前 Task 的验证证据，不登记项目结果索引。

# 工作目录

当前 Task 的验证输出必须位于该 Step 的任务专属目录或明确的只读输入位置：

```text
<base_work_directory>/<task_id>/
```

Manager 不创建该目录。

Task Execution Agent 先完成 Step reuse 判断；确实需要本地执行时才创建。

# Preflight

确认：

- 当前 Task Sheet Step 与本 Validator 对应；
- 被验证对象明确且可读；
- 必要上下文存在；
- 输出路径位于当前 Task 范围；
- 不修改其他 Task 正式结果；
- 必要依赖可用。

# Findings / Outcome

定义当前 Validator 特有的 findings / outcome 语义。

不要重新建立通用 DONE/BLOCKED/FAILED runtime 状态机。

如果仍有用户科学决定未解决，当前 Task Sheet Step 保持 `未完成`，必要原因写入执行记录。

# 用户确认

完成所有可安全执行的检查后，如仍有必须由用户判断的科学歧义，声明确认条件。

由当前 Task Execution Agent 在同一个执行对话中向用户确认；不要求返回 Legacy `confirmation_items` 或 Manager decision record。

# 完成与回写

验证闭合后由 Task Execution Agent：

- 更新当前 Txxxx.md；
- 登记适用 official results；
- 根据验证结果调整后续计划。

Validator 不创建 Workstream / route / event / runtime task-result。

# 自检

- [ ] 被验证对象明确；
- [ ] validation requirements 是本文件唯一权威；
- [ ] 区分执行成功与对象通过；
- [ ] 未修改被验证对象；
- [ ] task-scoped 目录正确；
- [ ] 用户确认由 Task Execution Agent 发起；
- [ ] 未创建 Legacy runtime 管理对象。

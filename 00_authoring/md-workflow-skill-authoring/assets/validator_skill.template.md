---
name: <validator-skill-name>
description: <检查或分类任务及排除边界>。
---

# 目标

# 职责边界

Validator 只读取和检查目标对象，不修复、不修改被验证对象，也不决定项目路线。

# 输入

从 `subagent_task.schema.yaml` 读取 task ID、Workstream ID、工作目录、权限、有效输入、用户决定和报告目标路径。

# 读写权限

- 只读取授权对象；
- 只写授权的详细验证报告或结果数据；
- 不修改被验证目标；
- 不修改 `00_project_state/` 或 `00_project_records/`。

# 检查规则

# Findings 与 gate

区分：

- Validator 是否成功执行；
- 被检查对象是否通过。

使用 `outcome_code` 表达业务判定，不将“不通过”自动写成 Validator 执行失败。

# 用户决策请求

先完成全部可安全处理对象，再汇总 `confirmation_items`。不得直接向用户提问。

# 详细报告

# 返回

作为独立任务或组合任务中的 `validation_result` 返回，必须符合：

`03_contracts/subagent_result.schema.yaml`

不得修改被验证目标，不得创建其他子 Agent。

---
name: <operation-skill-name>
description: <具体文件或命令操作及排除边界>。
---

# 目标

# 职责边界

Operation 只执行授权业务操作，不决定路线，不给出独立质量判决。

# 输入

从 `subagent_task.schema.yaml` 读取 task ID、Workstream ID、工作目录、权限、有效输入、用户决定和必需输出。

# 读写权限

- 只写 `allowed_write_paths`；
- 不访问 `forbidden_paths`；
- 不修改 `00_project_state/` 或 `00_project_records/`。

# Preflight

# 执行

# 完成验证

这里只确认操作是否实际执行完成，不代替 Validator 判断业务对象是否通过。

# 详细记录

将长日志和中间结果写入任务指定的业务路径。

# 返回

作为独立任务或组合任务中的 `operation_result` 返回，必须符合：

`03_contracts/subagent_result.schema.yaml`

不得创建其他子 Agent，不得直接向用户提问。

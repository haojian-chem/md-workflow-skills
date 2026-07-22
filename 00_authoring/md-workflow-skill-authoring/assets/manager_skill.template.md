---
name: <manager-skill-name>
description: <全局 MD 项目管理用途和触发边界>。
---

# 目标

# 职责边界

引用：

`00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`

# 输入

# 全局状态

引用：

`03_contracts/project_state.schema.yaml`

# Workflow 决策循环

1. 选择当前 Workflow；
2. 请求符合 `workflow_decision.schema.yaml` 的决定；
3. 若 `EXECUTE`，构建 `subagent_task`；
4. 串行创建一个临时子 Agent；
5. 核验 `subagent_result`；
6. 更新项目状态；
7. 处理确认事项；
8. 再次请求 Workflow 决策。

# 用户确认

# 失败与恢复

# 自检

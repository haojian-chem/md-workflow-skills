---
name: <workflow-skill-name>
description: <阶段编排用途和触发边界>。
---

# 目标

# 职责边界

Workflow 是可复用阶段决策 Skill，不是 Agent，不执行子 Skill，不创建 Workstream，也不选择项目 Focus。

# Workstream 输入

读取 Focus Workstream 的：

- 当前 Workflow 与 substep；
- 当前有效 artifact set；
- 已解决人工决策；
- active route；
- 阶段 gate 状态。

状态接口：

`03_contracts/workstream_state.schema.yaml`

# 有序 substep

# 决策规则

对当前 Workstream 返回一个决定：

```text
EXECUTE
SKIP
PAUSE
COMPLETE
BLOCKED
```

`EXECUTE` 只能指定一个 task unit：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

Operation 与 Validator 组合仅用于专属配套验证；Workflow 不执行它们。

返回必须符合：

`03_contracts/workflow_decision.schema.yaml`

# Gate

# 续跑与已有结果

- 仅判断当前 Workstream；
- 不把项目视为只有一个当前阶段；
- 不覆盖其他 Workstream 的有效下游结果。

# 阶段完成条件

# 自检

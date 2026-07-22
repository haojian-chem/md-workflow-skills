---
name: <workflow-skill-name>
description: <阶段路线片段与执行决策用途和触发边界>。
---

# 目标

# 职责边界

Workflow 是可复用阶段 Skill，不是 Agent，不执行子 Skill，不创建 Workstream，不选择项目 Focus，也不拼接跨 Workflow 完整路线。

# 共同输入

读取 Focus Workstream 的：

- 当前 Workflow 与 substep；
- 当前有效 artifact set；
- 已解决人工决策；
- active route；
- 阶段 gate 状态。

状态接口：

`03_contracts/workstream_state.schema.yaml`

# Substep registry

每个 substep 至少声明：

```yaml
step_id:
task_unit_mode: OPERATION | VALIDATOR | OPERATION_WITH_VALIDATOR
operation:
validator:
necessity: REQUIRED | CONDITIONAL
condition:
work_directory:
prerequisites: []
expected_outputs: []
gate_requirements: []
```

# 规划接口

根据本 Workflow 范围返回：

`03_contracts/workflow_route_fragment.schema.yaml`

必须说明：

- 起点和终点；
- REQUIRED 与 CONDITIONAL steps；
- entry requirements；
- exit artifacts；
- assumptions；
- unresolved items；
- blockers。

# 执行接口

对当前 Workstream 每次只返回一个决定：

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

# 条件步骤

# 续跑、已有结果与路线修订信号

- 仅判断当前 Workstream；
- 条件步骤无证据时保留，不提前删除；
- 不把项目视为只有一个当前阶段；
- 不覆盖其他 Workstream 的有效下游结果；
- 发现 active route 过期时返回修订理由，不直接写 route record。

# 阶段完成条件

# 自检

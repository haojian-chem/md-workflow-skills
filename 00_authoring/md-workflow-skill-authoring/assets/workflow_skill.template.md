---
name: <workflow-skill-name>
description: <阶段编排用途和触发边界>。
---

# 目标

# 职责边界

Workflow 是阶段决策 Skill，不是 Agent，不执行子 Skill。

# 阶段输入

# 有序 substep

# 决策规则

对当前状态返回一个决定：

```text
EXECUTE
SKIP
PAUSE
COMPLETE
BLOCKED
```

返回必须符合：

`03_contracts/workflow_decision.schema.yaml`

# Gate

# 续跑

# 阶段完成条件

# 自检

---
name: <skill-name>
description: <何时使用；当前 Skill 指导 Agent 解决什么问题；必要排除边界>。
---

# Purpose

说明当前 Skill 要把什么对象推进到什么有效状态。

# Scope and boundaries

当前 Skill 负责：

- ...

当前 Skill 不负责：

- ...

与其他 Skill 的关系只写接口级依赖/交接，不重新定义外部 Skill 的内部规则。

# Inputs / evidence

说明 Agent 需要理解的实际输入、对象和证据。

不要仅为了形式化强制把输入先转换成 parser/schema 结果。若 deterministic Tool 确有价值，说明其用途和 required / preferred / optional 定位。

# Reuse

```text
明确等价 → 复用
明确不等价 → 重新执行
信息不足 → 向用户确认
用户明确要求重做/对照 → 不自动复用
```

# Execution guidance

说明必须遵守的科学/技术规则、必要先后关系、推荐 tendency、可替代实现和明确禁止的做法。

不要把推荐 Tool 误写成唯一合法实现，除非科学/技术接口确实要求。

# Validation

说明什么证据代表当前结果有效。Validation 默认由当前结果 owner 定义；只有复杂且边界清晰时才拆 supporting validation Skill。

# Results / handoff

说明正式结果、下游如何定位/理解，以及 intermediate/debug/cache 的边界。

# References / supporting capabilities

按需列出：

```text
references/...
<supporting-skill>/SKILL.md
tools/<tool>/...
```

长但仍属于当前 Skill 的规则优先放 `references/`。Supporting Skill 只在复杂且有清楚独立边界时创建。

Current repository infrastructure：

```text
evals/   # evaluation infrastructure, not a Skill root
tools/   # current shared deterministic tools
legacy/  # Legacy executable/runtime material
```

# User confirmation

说明无法自动判断且会影响科学正确性的歧义，以及确认前禁止进行的动作。

# Self-check

- [ ] 当前 Skill 是 Agent guide，不是 parser/workflow gate；
- [ ] 一个清楚职责由一个 main Skill 持有；
- [ ] 长/条件性细节进入 reference，而不是复制在多个文件；
- [ ] 没有重新定义其他 Skill 的内部规则；
- [ ] 没有恢复 Workflow/Operation/Validator role-based roots；
- [ ] supporting Skill 只有在复杂且边界清晰时才拆；
- [ ] 推荐与强制要求区分清楚；
- [ ] reuse、validation、handoff 足以支持跨对话继续；
- [ ] 没有把 `evals/`、`tools/` 或 `legacy/` 当成 MD Workflow Stage Skill root。

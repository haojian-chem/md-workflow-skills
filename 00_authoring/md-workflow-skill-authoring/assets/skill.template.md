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

与其他 Skill 的关系只写接口级依赖/交接，不在这里重新定义外部 Skill 的内部规则。

# Inputs / evidence

说明 Agent 需要理解的实际输入、对象和证据。

不要仅为了形式化强制把输入先转换成 parser/schema 结果。若某 deterministic Tool 确有价值，说明其用途和是否为 required / preferred / optional。

# Reuse

说明哪些实际条件决定已有结果是否仍可用。

```text
明确等价 → 复用
明确不等价 → 重新执行
信息不足 → 向用户确认
用户明确要求重做/对照 → 不自动复用
```

如当前 Stage 已冻结其他 reuse 组织方式，以对应 Stage guide 为准。

# Execution guidance

说明：

- 必须遵守的科学/技术规则；
- 真正必要的先后关系；
- 推荐方法 / tendency；
- 可替代实现；
- 明确禁止的做法。

不要把推荐工具误写成唯一合法实现，除非科学/技术方法确实要求。

# Validation

说明什么证据代表当前结果有效。

Validation 默认由当前结果 owner 定义；只有复杂且边界清晰时才拆 supporting validation Skill。

# Results / handoff

说明：

- 当前需要保留的正式结果或记录；
- 下游如何定位和理解这些结果；
- 哪些文件只是 intermediate / debug / cache。

# References / supporting capabilities

仅列当前任务按需使用的：

```text
references/...
<supporting-skill>/SKILL.md
05_tools/<tool>/...
```

每项说明何时需要读取/调用。

长但仍属于当前 Skill 的规则优先放 `references/`。不要在 main Skill 和 reference 中各维护一份完整规则。

Supporting Skill 只在内容复杂且有清楚独立边界时创建；不要为了角色分类或几条 validation 规则拆 Skill。

生成/重构规则见：

`00_authoring/md-workflow-skill-authoring/references/skill_generation_rules.md`

# User confirmation

如存在无法自动判断且会影响科学正确性的歧义，说明触发条件和确认前禁止进行的动作。

# Self-check

- [ ] 当前 Skill 是 Agent guide，不是 parser/workflow gate；
- [ ] 一个清楚职责由一个 main Skill 持有；
- [ ] 长/条件性细节进入 reference，而不是复制在多个文件；
- [ ] 没有重新定义其他 Skill 的内部规则；
- [ ] 没有因为旧目录而强制 Workflow/Operation/Validator 分类；
- [ ] supporting Skill 只有在复杂且边界清晰时才拆；
- [ ] 推荐与强制要求区分清楚；
- [ ] reuse、validation、handoff 足以支持跨对话继续；
- [ ] 本次替换产生的过期 Markdown 已从 active path 移入 `00_authoring/archive/` 或明确不需要保留。

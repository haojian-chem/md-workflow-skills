---
name: <skill-name>
description: <何时使用；当前 Skill 指导 Agent 解决什么问题；必要排除边界>。
---

# Purpose

通用 Task Execution 规则读取：

`<relative-path>/references/task_execution_rules.md`

说明当前 Skill 要把什么对象推进到什么有效状态。

# Scope and boundaries

说明当前 Skill 自己负责的科学 / 技术职责。

与其他 Skill 的关系只写当前职责真实需要的接口级依赖，不重新定义外部 Skill 的内部规则。

只有在确有高概率越界、数据保护、不可逆操作、已明确否定的常见默认行为或 validation/result correctness 需要时，才增加必要的 negative-scope 规则；不要把“当前 Skill 不负责……”写成默认完整清单。

# Inputs / evidence

说明 Agent 需要理解的实际输入、对象和证据。

Task Sheet 是有界执行记录，不等同于整个科研任务。不要因为编号上存在更早 Step，就要求这些 Step 必须出现在当前 Task Sheet；也不要因为某个更早 Step 不在当前 Task Sheet，就默认其科学前置条件可以忽略。

如果当前 Skill 确实存在 prerequisite，应直接定义**必须已经存在什么上游方案、正式结果、对象状态或决策**。该 prerequisite 可以由当前 Task Sheet 提供，也可以由同一科研任务的前序 Task Sheet、项目正式结果或其它可追溯记录提供；是否满足以前置对象本身为准，不以是否出现在当前 Task Sheet 为准。

不要仅为了形式化强制把输入先转换成 parser/schema 结果。若 deterministic Tool 确有价值，说明其用途和 required / preferred / optional 定位。

对于会被多个环节消费的科学信息，例如力场、参数来源、pH 或方法选择，当前 Skill 真正需要时先使用已有明确决定；仍不能唯一确定时再向用户确认，不为“首次确认”人为指定唯一 Step owner。

# Reuse / execution assessment

如果当前 Skill 使用 reuse，说明实际等价判据与用户重做 / 对照边界。

普通默认语义为：

```text
明确等价 → 复用
明确不等价 → 重新执行
信息不足 → 向用户确认
用户明确要求重做/对照 → 不自动复用
```

如果当前 Skill 明确不设置 reuse，直接写明 current no-reuse 语义，不增加虚构复用分支。

# Execution guidance

说明必须遵守的科学/技术规则、必要先后关系、可替代实现和明确禁止的做法。

不要把推荐 Tool 误写成唯一合法实现，除非科学/技术接口确实要求。

用户长期执行资源倾向、机器相关参数或本地运行习惯如果需要跨多个 execution Skill 复用，应评估是否集中到明确的 preference / execution reference，而不是分别硬编码进多个 scientific Skill。

# Validation

说明完成当前职责所需的必要检查。

Validation 默认由当前结果 owner 定义，但强度应与实际操作、风险和结果声明匹配；不要因为“owner 必须 validation”重复成熟软件已经自然完成的检查，也不要复制另一个可选独立 validation Skill 的完整检查范围。

只有 validation 本身复杂、独立且拆分有明确维护价值时才拆 supporting validation Skill。

# Results

说明正式结果摘要、正式结果入口、必要的完成条件，以及 intermediate / debug / cache 的边界。

如果当前结果包含多个正式文件、结构化字段、复杂定位关系、project-result registration 白名单，或会被后续 Skill 直接查阅，详细结果说明优先写入：

`references/results.md`

main Skill 只保留摘要和读取入口；`references/results.md` 只定义当前结果本身，不规定下游 Skill 应如何执行。

当前 Skill 只定义自己的结果集合、字段语义、Skill-specific validation requirement 与 project-result registration 白名单；科研执行 Skill 共用的结果生成与记录规则不在当前 Skill 重复定义。

正式结果已经保存实际文件完整路径时，可以沿这些路径恢复对应工作目录和实际执行文件；不为了“结果自包含”把低价值、容易从实际文件恢复的信息全部复制进结果记录。

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
- [ ] 当前 package 的职责由一个 main Skill 持有，但没有为了 Stage 对称强制建立 Stage-level main；
- [ ] 长/条件性细节进入 reference，而不是复制在多个文件；
- [ ] 没有重新定义其他 Skill 的内部规则；
- [ ] 没有恢复 Workflow/Operation/Validator role-based roots；
- [ ] supporting Skill 只有在复杂且边界清晰时才拆；
- [ ] recommendation / user preference / environment-dependent tendency 与 scientific requirement 区分清楚；
- [ ] reuse 语义明确：采用当前 reuse 规则或明确 no reuse；
- [ ] validation 与当前职责风险匹配，没有复制可选独立终检；
- [ ] results 足以支持跨对话继续，但没有无必要复制可从实际路径恢复的信息；
- [ ] 复杂结果接口已经评估是否需要 `references/results.md`；
- [ ] results 说明没有重新写成下游 handoff 规则；
- [ ] 科研执行 Skill 共用的 Task Execution / result-generation 规则没有在当前 Skill 重复定义；
- [ ] 没有把 Task Sheet 等同于整个科研任务；
- [ ] 当前 Skill 的 prerequisite 按真实上游对象 / 状态定义，而不是按“必须出现在当前 Task Sheet 的更早编号 Step”定义；
- [ ] 当前 Task Sheet 只覆盖局部流程时，没有因此忽略真实 prerequisite，也没有为了流程完整补入无关 Step；
- [ ] 没有把 `evals/`、`tools/` 或 `legacy/` 当成 MD Workflow Stage Skill root。

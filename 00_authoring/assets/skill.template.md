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

执行范围确认遵守 shared `task_execution_rules.md`。当前 Skill 可以定义自己如何 grounding 对象、如何判断技术实现或如何解决科学歧义，但不得把“Agent 可以判断”扩张成“Agent 可以替用户决定尚未明确的执行范围”。

如果用户已经明确对象集合 / 范围，只是缺少能够从正式结果唯一补足的 identity 信息，可以直接 grounding；如果省略的信息会改变处理哪些对象、处理多少对象、是否扩展 Step / analysis scope 或是否保留多个 alternative branches，则当前 Skill 必须让 shared execution-scope confirmation gate 先闭合。

如果当前 Skill / 当前工作项实际使用 `target` 作为 execution object，则必须遵守：

`<relative-path>/references/target_lineage_rules.md`

并明确：

```text
current local target_id
→ 只在当前 Skill / 当前工作项内解释

current target_record
→ 当前 local target 的正式跨 Skill 引用

source_target_records
→ 实际形成当前 target 的直接上游 target records
```

不要通过上下游 `target_id` 编号相同推断同一对象，也不要把 target lineage 固定写成从某个特定 Step（例如 1.3）开始的单链。一个 source target 可以派生多个 current targets；一个 current target 也可以由多个 source targets 合流形成。

只有真正参与 current execution object 形成的上游 target 才进入 `source_target_records`。普通 evidence、validation report、force-field / CCD reference、参数库或仅被读取的文件不因“被读取”自动成为 source target。

如果当前 Skill 已有其它正式 execution identity，例如 Stage 4 formal run unit 或 Stage 5 analysis plan item，并且该 Skill 不使用 `target` 作为对象，则不要为了形式统一强制建立 target record。

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

Reuse assessment 只在当前执行范围已经明确后进行；不得因为找到某个可复用结果，反向替用户决定当前应该处理哪个对象或范围。

如果 reuse 后当前工作项仍实例化自己的 local target，不把旧结果中的 `target_id` 当作当前 target identity；按 target-lineage 规则记录实际 source target record。若当前职责在 reuse assessment 后直接终止、没有实例化新的 execution target，则不要制造空 target record。

# Execution guidance

说明必须遵守的科学/技术规则、必要先后关系、可替代实现和明确禁止的做法。

不要把推荐 Tool 误写成唯一合法实现，除非科学/技术接口确实要求。

用户长期执行资源倾向、机器相关参数或本地运行习惯如果需要跨多个 execution Skill 复用，应评估是否集中到明确的 preference / execution reference，而不是分别硬编码进多个 scientific Skill。

如果当前科学 / 技术 strategy 会让同一个 source object 产生多个需要后续独立保留的结果，说明何时建立多个 local target branches；不要自动枚举所有理论组合。若当前对象由多个 upstream target-scoped results 共同形成，说明真实 merge sources；不要仅按 Step 顺序把对象强行串成一条链。

如果多个 strategy 只是当前 Skill 范围内需要按明确科学判据选择其一，则按 Skill 判据处理；只有用户意图本身未明确“是否需要保留多个 strategy 作为独立执行范围”时，才属于执行范围确认问题。

# Validation

说明完成当前职责所需的必要检查。

Validation 默认由当前结果 owner 定义，但强度应与实际操作、风险和结果声明匹配；不要因为“owner 必须 validation”重复成熟软件已经自然完成的检查，也不要复制另一个可选独立 validation Skill 的完整检查范围。

只有 validation 本身复杂、独立且拆分有明确维护价值时才拆 supporting validation Skill。

Target-scoped result 的 validation 应确认 current formal result 指向正确的 current `target_record`，且 target record 的 `source_target_records` 与实际对象来源一致。只读 validation Skill 如果自己建立 validation target，不应改写被检查 source map / source result 的 target identity；current validation target 通过 `source_target_records` 指向被检查 target。

# Results

说明正式结果摘要、正式结果入口、必要的完成条件，以及 intermediate / debug / cache 的边界。

如果当前结果包含多个正式文件、结构化字段、复杂定位关系、project-result registration 白名单，或会被后续 Skill 直接查阅，详细结果说明优先写入：

`references/results.md`

main Skill 只保留摘要和读取入口；`references/results.md` 只定义当前结果本身，不规定下游 Skill 应如何执行。

当前 Skill 只定义自己的结果集合、字段语义、Skill-specific validation requirement 与 project-result registration 白名单；科研执行 Skill 共用的结果生成与记录规则不在当前 Skill 重复定义。

Target-scoped formal result 在自己的 `references` / dependency 区域记录**当前 local target 的 `target_record` 完整绝对路径**。不要固定保存某个更早 Step 的 target path 作为所有后续结果的统一 lineage 字段；更早 ancestry 通过 current target record 的 `source_target_records` 逐级恢复。

例如：

```yaml
target_id: target_001
references:
  target_record: /absolute/path/to/current/targets/target_001.yaml
```

`target_id` 可以留在当前 result 内用于局部阅读，但不能作为跨 Skill identity。

Target record 是 lineage support record，不因为创建就自动成为 project-result-index entry；除非当前结果 owner 有特殊理由明确登记。

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

不要重复定义 shared execution-scope confirmation gate；只补充当前 Skill 特有的 scope ambiguity 或 scientific ambiguity。范围尚未明确时，仅允许 shared rule 定义的只读核对，不开始依赖该范围的实质执行。

如果用户明确要求保留多个合理 strategy 作为后续独立比较，不强行压成一个 target；按实际科学对象关系建立多个 branches。不要因为存在多个理论候选就默认自动 branch。

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
- [ ] Skill 中的“Agent 自主判断”只适用于已确认执行范围内的科学 / 技术实现，没有替用户决定尚未明确的对象集合或执行范围；
- [ ] 用户指令与 Task Sheet 仍存在实质不同的范围解释时，当前 Skill 会先触发用户确认，而不是采用默认范围；
- [ ] identity grounding 与 scope selection 已区分：唯一 identity 补足可直接执行，改变对象集合 / 范围的选择必须先确认；
- [ ] 当前 Skill 如使用 `target`，每个 actual local target 都有 current target record；
- [ ] local `target_id` 没有被当作跨 Skill identity；
- [ ] `source_target_records` 只记录真实形成 current object 的直接 source targets，支持 branch / merge，没有固定回指某个 Step；
- [ ] target-scoped formal result 的 `references` / dependency 区域记录 current `target_record` 完整路径；
- [ ] validation-only target 没有改写被检查 source target / source map identity；
- [ ] 不使用 target 的 Stage 4 run unit / Stage 5 plan item 等对象没有被强制 target 化；
- [ ] 没有把 `evals/`、`tools/` 或 `legacy/` 当成 MD Workflow Stage Skill root。

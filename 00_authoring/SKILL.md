---
name: md-workflow-skill-authoring
description: 设计、编写、冻结、审查或重构本项目科研 Skill 时使用。以 main Skill 指导 Agent 完成职责为核心；长/条件性细节进入 references，只有复杂且边界清晰时拆 supporting Skill；避免跨 Skill 越权、重复定义、无必要 parser/workflow gate 和过期文件留在 active path。
---

# Purpose

本文件是 `00_authoring/` 的唯一 Skill authoring 主入口。

Skill 的目标是指导 Agent 处理科研任务，而不是把 Agent 锁进固定 parser、schema、wrapper、dispatcher 或人为 workflow engine。

真实任务的默认关系为：

```text
Manager
→ Task Sheet
→ Task Execution Agent
→ 当前科研 main Skill
   ├─ repository shared task-execution reference
   ├─ repository shared canonical terminology
   ├─ 按需 local references
   ├─ 必要时 supporting Skill
   └─ 必要时 deterministic Tool
```

跨 Stage 的通用 Task Execution 规则统一读取：

`../references/task_execution_rules.md`

跨 Skill 的正式术语统一维护：

`../references/canonical_terminology.md`

两者都是仓库级 shared reference，不是独立 Skill 或额外执行环节。Authoring 不在本文件复制其中的通用 Task Execution 规则或另建平行术语表。

# Authoring reads

正式 authoring 链从本 Skill 开始：

```text
00_authoring/SKILL.md
→ 当前 authoring task
→ authoring references
→ target Skill / freeze / directly related files
```

测试或运行环境中的 `AGENTS.md` 只用于在 Skill 体系外帮助 Agent 定位需要加载的 Skill；它不属于 Skill package、authoring chain、execution chain 或 reference dependency，也不能作为任何 Skill 规则已经被正式引用或可达的依据。

之后只按任务需要读取：

- 构筑、设计、审查、重构科研执行 Skill 或编写对应 freeze 时必须读取 `../references/task_execution_rules.md` 和 `../references/canonical_terminology.md`；
- 对应 Stage / Step 的 `architecture_freezes/`；
- 与当前输入/输出/边界直接相关的相邻 Skill；
- 当前 Skill 明确需要的 reference / Tool guide；
- 项目级 Stage catalog/status 需要时读 `project_design/MD_WORKFLOW_MASTER_PLAN.md`；
- 多窗口写入协调需要时读 `coordination/`。

提出或实施迭代修改前恢复：

```text
已做过
已否定
仍未验证
```

没有新证据改变前提时，不恢复已否定方案。

# Scientific Skill layout

Scientific roots 按 MD Workflow Stage 固定为：

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

这些 Stage / Step 目录可以在正式 `SKILL.md` 生成前预先保留，用于稳定规划路径和后续 Skill package 落位；**目录存在不等于 Skill 已生成或已激活**。

`../00_manager/` 是独立的 unnumbered 项目管理 package，不是 Scientific Skill root。

以下为 unnumbered repository infrastructure：

```text
../references/
../evals/
../tools/
../legacy/
```

其中仓库级 `references/` 只保存确有跨 Skill 共用价值的 shared references；它本身不是新的执行层。

历史 Workflow / Operation / Validator role-based roots 已退出 current layout，不保留 compatibility copy。

# Skill generation

详细规则：`references/skill_generation_rules.md`。

默认模型：

```text
一个职责
→ 一个 main SKILL.md
→ 长且仍属于当前职责的内容放 references/
→ 只有复杂且独立时拆 supporting Skill
→ 只有确有机器约束/确定性能力时增加 schemas/scripts/Tool
```

普通模板：`assets/skill.template.md`。

所有正式科研执行 Skill 都必须在 main `SKILL.md` 中显式引用仓库级：

`references/task_execution_rules.md`

引用只建立通用 Task Execution 规则的可达性；Stage/Step/capability 自己的科学规则仍由其自身拥有。`task_execution_rules.md` 同时提供执行阶段按需读取 `canonical_terminology.md` 的入口，因此现有科研执行 Skill 不需要为了建立术语可达性而逐一新增平行 glossary。

**Architecture freeze 完成不等于 Skill generation 已获许可。** 只有用户明确要求生成/实现某个 Skill 时，才把对应 freeze 转写为 active `SKILL.md`。

# Terminology and writing quality

术语规范适用于整个 authoring 过程，而不是只在最终写 `SKILL.md` 时生效。Skill 构筑、设计讨论、freeze 编写、生成、审查和重构过程中，Agent 与用户讨论方案时也应主动使用项目正式术语。详细规则见 `references/skill_generation_rules.md` 的 `Terminology and writing precision`；跨 Skill canonical terminology 读取 `../references/canonical_terminology.md`。

至少执行以下约束：

- 同一 execution object、artifact、state、scientific concept 或判断对象使用一个稳定的 canonical term；`canonical_terminology.md` 已有条目时使用其 `Preferred expression`。已有 current Skill、freeze、正式接口或 shared reference 已确定但尚未进入 shared terminology 的局部术语，也不得因用户本轮口语表达而随意改名。
- 用户简称、口语、临时称呼和不完整表达只用于当前上下文理解；它们不约束用户输入，也不登记为 alias。Agent 应理解其实际指代，并在自己的后续讨论、设计记录、freeze 和正式 Skill 文本中恢复为当前项目正式术语。
- 只有需要跨 Skill 稳定、会进入 Task Sheet / 项目结果索引 / Stage 间接口，或名称漂移会造成对象混淆的术语才进入 `canonical_terminology.md`；单个 Skill 的局部术语继续由该 Skill 自己维护。
- `canonical_terminology.md` 只负责对象或概念“正式叫什么、具体指什么、与什么不同”；科学/技术关系如何写清楚由本 authoring guidance 的 semantic-explicitness 规则负责，具体科学判据仍由对应科学 Skill 拥有。
- 科学/技术判断必须写出实际判断关系。若“兼容、合理、正确、有效、一致、匹配”等词在未展开时可能有多种解释，则明确检查对象、属性、reference / criterion 和判断关系，不用抽象标签替代可执行判据。
- 中文 Skill 以中文叙述为主体；软件/方法/力场专名、文件名、字段名、命令、软件原生语法及确有必要保留的固定英文术语可以使用英文。普通技术概念能准确自然地用中文表达时，不做无信息增益的中英文混排。

`canonical_terminology.md` 不维护 alias、口语映射或 deprecated / do-not-use 列表。Skill 完成后必须检查全文术语一致性、抽象判断句和无必要中英文混排；这属于 authoring self-check，而不是后续执行 Skill 的运行时 validation。

# Authoring status maintenance

`project_design/MD_WORKFLOW_MASTER_PLAN.md` 是项目级 **Stage / Step 建设状态与 current entry 的唯一状态 owner**。既然维护这个状态文件，任何真正改变实现状态的 authoring 工作都必须同步它；不能把状态维护留给“以后某个窗口顺手更新”。

以下变化都属于必须同步的状态变化：

```text
讨论/设计中
→ architecture frozen

architecture frozen
→ Skill generation approved / in progress

freeze-only
→ active SKILL.md generated

active Skill
→ representative validation completed / implementation milestone changed

current Skill / freeze
→ superseded / retired / replaced
```

对于正式 Skill generation，交付顺序固定为：

```text
读取 current main + 对应 freeze + authoring rules
↓
读取 references/task_execution_rules.md + references/canonical_terminology.md
↓
确认执行 Skill 的共享 Task Execution 规则引用，并按 canonical terminology 归一化正式术语
↓
生成 / 修改目标 Skill package
↓
完成本次要求的 validation / self-check
↓
更新直接拥有该入口的 Stage main Skill（如果它维护 current/freeze-only entry）
↓
同步 MD_WORKFLOW_MASTER_PLAN.md 中对应 Stage / Step 的状态与 current entry
↓
如新增/替换 freeze，再同步 architecture_freezes/README.md
↓
交付
```

因此：**目标 `SKILL.md` 写完但状态 owner 尚未同步，不算完整交付。**

多窗口时采用窄范围状态同步：

- authoring 窗口在写状态前必须重新读取 current `main` 和 `coordination/file_ownership.yaml`；
- 若 `MD_WORKFLOW_MASTER_PLAN.md` 没有被其他窗口显式占用，完成 Skill 的窗口可以只修改与自己 Stage / Step 对应的状态/current-entry 行，不获得修改其他 Stage catalog/architecture 的权限；
- 若该共享文件已有显式 writer，占用窗口不得并发写；必须把精确的状态变更交给当前 writer，并在交付中明确“状态同步待 owner 落地”，不能静默跳过；
- 不为解决状态同步再建立 parallel `status.yaml`、skill inventory 或第二份 sync 文档。

# Main Skill boundary

main Skill 应让 Agent 能确定：

```text
目标
输入 / 对象 / 证据
reuse 条件
科学 / 技术边界
执行 / 判断方式
validation
results
何时读取额外 reference / supporting Skill / Tool
```

这些是信息要求，不是固定 section schema，也不表示所有运行时判断都必须预先固化成 Skill 规则。

“不做什么”只在有实际边界价值时明确：例如防止高概率越界/误操作、保护数据或不可逆操作、阻止已明确否定的常见默认行为，或直接影响 validation/result correctness。不要为了“范围完整”罗列所有本 Skill 不负责的事项。

详细边界：`references/skill_boundaries.md`。

# Rule necessity gate

在判断一条规则归谁拥有之前，先判断它**是否有必要成为 Skill 的固定规则**。

Skill 优先固定需要跨任务保持一致、且对当前职责正确性有实际价值的内容，例如：稳定科学/技术判据、输入/输出接口、reuse 与 validation 语义、安全或数据完整性边界、正式结果生命周期，以及不固定就会高概率造成越界或歧义的约束。

如果某项决定可以由 Task Execution Agent 或用户根据当前任务上下文可靠判断，且不需要形成跨任务稳定语义、接口约束、科学判据或结果生命周期，则保留为运行时裁量；**不要因为“运行时可能遇到这种情况”就继续把它固化成统一决策树、状态转换规则、fallback 链或完整工作流。**

前置 gate：

```text
这件事必须写成 Skill 固定规则吗？
├─ 是：缺少固定规则会影响跨任务一致性、科学/技术正确性、接口/结果语义、安全或高概率边界执行
│  → 继续 rule-ownership gate
└─ 否：Agent / 用户可基于当前任务可靠判断
   → 保留运行时裁量，不继续下钻为 Skill 规则
```

# Ownership and deduplication

向当前 Skill 增加规则前，按需读取 `references/content_ownership_and_deduplication.md`。

通过 rule-necessity gate 后，再执行 ownership gate：

```text
这条规则属于当前 Skill 自己？
├─ 是 → 当前 Skill 定义
└─ 否
   ↓
   外部已有 owner？
   ├─ 有 → 只引用 owner，不复制 / 改写成第二份规范
   └─ 没有或冲突 → 提 cross-skill finding
```

当前 Skill 可以定义“我需要外部 Skill 提供什么”，不能定义“外部 Skill 应该怎样把它做出来”。

# Read broadly, write narrowly

```text
read scope 可以宽
write ownership 必须窄
```

可以并且应该读取直接相关的上下游/相邻 Skill 来理解接口，但未经重新分配不得修改它们，也不得在当前 Skill 中创建 shadow specification。

状态同步是唯一的窄共享写例外，只允许修改当前 authoring 工作直接造成的对应状态/current-entry，不扩展科学内容 ownership。

详细协议：`references/multi_window_authoring_protocol.md`。

# References / supporting Skills

属于当前 Skill 但过长或条件性强的细节优先放 `references/`。

Supporting Skill 只有在内容复杂、可独立加载、边界稳定且独立维护有价值时才拆；不要为了 validation 配对、目录对称或角色分类增加 Skill hop。

仓库级 `../references/task_execution_rules.md` 与 `../references/canonical_terminology.md` 都是跨 Skill shared reference，不因被多个执行 Skill 使用而变成 supporting Skill。

# Tool boundary

Tool 是确定性能力组件，不是 Agent 理解任务的许可层。

适合 Tool：精确 parsing、hash/mapping、批量结构化提取、稳定文件变换、格式校验和高重复度确定性计算。

Current shared Tool root：`../tools/`。

Tool authoring：`md-workflow-tool-authoring/SKILL.md`。

Legacy runtime-dependent tools 位于 `../legacy/tools/`，不得为了调用它们重新构造旧 Runtime。

# Reuse, validation and results

跨 Skill 的默认 Task Execution 语义读取：

`../references/task_execution_rules.md`

具体 Skill 是否设置 reuse、哪些条件影响等价性、validation 如何判定以及哪些文件属于正式结果，仍由对应结果 / scientific responsibility owner 定义；authoring 不在这里维护第二份通用执行规范。

正式结果必须让后续执行能够定位并理解，而不要求重读上游全过程。

# Architecture freezes and archive

Stage / Workflow / pre-Skill Step architecture freeze：`architecture_freezes/`。

历史 authoring/design Markdown：`archive/`。

Legacy executable/runtime material：`../legacy/`。

`archive/` 与 `legacy/` 均不是 ordinary startup/read list。

# Delivery check

- [ ] main Skill 能直接指导 Agent 完成当前职责；
- [ ] 科研执行 Skill 的 main `SKILL.md` 已显式引用 `references/task_execution_rules.md`；
- [ ] 已读取 `references/canonical_terminology.md`；其中已有跨 Skill 术语均采用其 `Preferred expression`，未在局部 Skill 建立平行 glossary；
- [ ] authoring 讨论、设计记录、freeze 与正式 Skill 文本对同一对象使用一致的项目正式术语；用户口语或简称没有被 Agent 继续传播为新的正式称呼；
- [ ] 同一对象没有因用户口语、简称或措辞变化而出现多套正式术语；已有 canonical term 未被随意改写；
- [ ] 没有把用户口语、alias 或历史称呼写入 shared terminology 作为长期映射；只有确有跨 Skill 稳定价值的新术语才进入该文件；
- [ ] 科学/技术判断没有用未定义的抽象词代替实际判据；需要时已写明检查对象、属性、reference / criterion 和判断关系；
- [ ] 中文 Skill 没有无信息增益的中英文混排；机器接口名、软件语法和确有必要的固定英文术语保持原文；
- [ ] 未把 shared Task Execution reference 误建成独立 runtime Skill / dispatcher；
- [ ] 未把可由 Agent / 用户按当前任务可靠判断的策略，无必要地固化成决策树、状态机、fallback 链或完整工作流；
- [ ] 长/条件性细节没有在 main Skill 与 reference 重复；
- [ ] supporting Skill 拆分有真实复杂度和边界价值；
- [ ] 未建立不必要 parser/wrapper/dispatcher；
- [ ] 未重新定义其他 owner 的内部规则；
- [ ] 未为“范围完整”罗列无实际必要的 negative-scope 清单；
- [ ] current scientific root 与 Stage 编号一致；
- [ ] 预留 Step 目录没有被误写成“Skill 已生成”；
- [ ] evals/tools/legacy 未被误当成 Stage Skill；
- [ ] reuse、validation、results 足以支持跨对话继续；
- [ ] 若本次改变了 freeze / Skill / validation 建设状态，`MD_WORKFLOW_MASTER_PLAN.md` 已同步，或存在明确且未完成的 writer handoff；
- [ ] 若 Stage main Skill 维护 current/freeze-only entry，其入口状态已同步；
- [ ] 未重新引入 Legacy Workstream/route/event/transaction runtime。
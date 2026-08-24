# Canonical terminology

Status: CURRENT SHARED REFERENCE

本文件维护 MD Workflow 中需要跨 Skill 保持一致的正式术语。

它是仓库级 shared reference，**不是独立 Skill、不是执行环节，也不定义科学处理规则**。它只回答：一个跨 Skill 概念正式叫什么、正式文本优先怎样表达、它具体指什么，以及它与容易混淆的其他正式对象边界在哪里。

## Scope of application

本术语规范适用于项目中由 Agent 产生的正式表达，包括：

- Skill authoring discussion；
- Skill design / architecture-freeze discussion；
- architecture freeze、`SKILL.md` 及其 references；
- Task execution communication；
- Task Sheet 与其他项目记录；
- reports / results。

因此，术语规范不是 Markdown 写作阶段才使用的辅助规则。Authoring Agent 在与用户讨论 Skill 构筑、设计和 freeze 时，Task Execution Agent 在与用户讨论当前科研任务时，以及 Agent 写入正式项目记录或结果时，都应在能够确定实际指代后回到当前 canonical terminology。

本规范**约束 Agent 的项目表达，不要求用户输入采用规范术语**。用户可以使用简称、口语、临时称呼或不完整表达；Agent 负责结合当前上下文理解其实际指代，并在自己的后续正式表达中使用当前项目正式术语：

```text
用户表达
→ Agent 结合上下文理解实际对象
→ canonical terminology
→ Agent 的正式讨论 / 文档 / 记录 / 结果表达
```

本文件只拥有术语名称、优先表达、定义和对象边界，不规定科学/技术判断关系应该如何展开，也不定义任何 Stage / Step / capability 的科学判据。Authoring 中如何把判断对象、属性、reference / criterion 和判断关系写清楚，由 `00_authoring/references/skill_generation_rules.md` 的 semantic-explicitness 规则负责；具体科学判据继续由对应 scientific Skill 拥有。

## Maintenance rules

只登记需要跨 Skill 稳定的术语，例如：

- 会在多个 Stage / Step / capability Skill 中使用的对象或概念；
- 会进入 Task Sheet、项目结果索引或 Stage 间正式接口的术语；
- 如果名称漂移，会导致 execution object、artifact、state 或科学判断对象混淆的术语。

不因为某个专业词存在就自动登记。只在单个 Skill 内使用的局部术语，由对应 Skill 自己定义和维护。

每个条目只维护：

```text
Canonical term
Preferred expression
Definition
Scope / distinction
```

本文件**不维护 alias、口语映射或 deprecated / do-not-use 列表**。用户的简称、口语、临时称呼和不完整表达由 Agent 结合当前上下文理解；Agent 在上述适用范围内的正式表达应回到当前 canonical terminology，而不是把临时表达固化为新的术语。

如果本文件已有某个概念的条目，Agent 在上述适用范围内优先采用其 `Preferred expression`。如果当前工作确实建立了新的跨 Skill 稳定术语，可以在具备该 shared path 的写入权限时更新本文件；没有写入权限时，只报告需要新增或修订的精确条目，不在局部 Skill 中另建平行 glossary。

机器或接口级名称仍按原文使用，例如文件名、字段名、命令、命令行选项、配置键、section name、enum 和 identifier；它们不因本文件的中文优先表达而被自由翻译或改名。

## Current terminology

### Task Sheet

**Canonical term:** `Task Sheet`  
**Preferred expression:** `Task Sheet`  
**Definition:** 真实项目中保存任务目标、当前计划、执行进度和最小恢复上下文的任务记录；当前文件形式为 `00_project_records/tasks/Txxxx.md`。  
**Scope / distinction:** 任务级导航与状态由 Task Sheet / task index 体系维护；不要把 Task Sheet 与项目结果索引混为同一记录。

### project result index

**Canonical term:** `project result index`  
**Preferred expression:** 项目结果索引  
**Definition:** 真实项目中用于跨任务、跨对话定位正式结果的检索入口；当前文件形式为 `00_project_records/project_result_index.md`。  
**Scope / distinction:** 只承担正式结果检索，不维护当前任务状态，也不是所有工作文件的平铺 artifact inventory。

### target

**Canonical term:** `target`  
**Preferred expression:** `target`  
**Definition:** 当前 Stage / Step / capability 中由对应 Skill 独立处理的目标对象。  
**Scope / distinction:** `target` 是处理对象身份，不等同于某一个 structure 文件。不同处理环节形成的 target 即使来源相关或编号相似，也不自动视为同一个 execution object；它们之间的继承、映射或分支关系应由对应 Skill 的正式结果和接口明确。

### main Skill

**Canonical term:** `main Skill`  
**Preferred expression:** main Skill  
**Definition:** 一个 Skill package 中作为 Agent 正式入口的 `SKILL.md`，负责给出当前职责的主线和必要 reference / supporting Skill / Tool 入口。  
**Scope / distinction:** main Skill 不等同于整个目录中的所有 supporting material；reference 不是独立 Skill。

### supporting Skill

**Canonical term:** `supporting Skill`  
**Preferred expression:** supporting Skill  
**Definition:** 在确有独立复杂职责、可按需加载且独立维护有价值时，从 main Skill 拆出的辅助 Skill。  
**Scope / distinction:** 长说明或条件性细节本身不足以构成 supporting Skill；这类内容优先属于 reference。

### reference

**Canonical term:** `reference`  
**Preferred expression:** reference  
**Definition:** 被 main Skill 或其他正式 Skill 入口按需读取、用于承载详细规则或共享信息的参考文件。  
**Scope / distinction:** reference 不是独立执行环节，也不因为被多个 Skill 使用而自动成为 supporting Skill。

### residue definition

**Canonical term:** `residue definition`  
**Preferred expression:** 残基定义  
**Definition:** 目标力场中针对某一残基规定其可识别原子名称及与当前 Skill 判定相关的残基级定义信息。具体来源文件和需要比较的字段由对应科学 Skill 指定。  
**Scope / distinction:** 正式中文 Skill 在没有必要强调软件原生实体名称时使用“残基定义”，不要仅为了技术感写成中英文混排的 `residue definition`。如果需要指向某个软件中的具体原生文件、section 或字段，则保留该软件原文名称。

### residue_id

**Canonical term:** `residue_id`  
**Preferred expression:** `residue_id`  
**Definition:** 结构准备 1.2 在一个 model 的正式 `classification_result.yaml` 中，为所属 `component_id` 内每个 residue 物化的稳定、不透明身份标识。下游使用 `component_id + residue_id` 持续引用同一个 1.2 residue 身份。已存在 residue 和已确认缺失 residue 都可以具有 `residue_id`。  
**Scope / distinction:** `residue_id` 的唯一性作用域是所属 `component_id`，不要求跨不同 component 单独唯一。它不是 `source_resid`、`current_resid`、当前 PDB 中的 `resid` 或 residue name。下游 Skill 必须与 `component_id` 共同消费正式结果或 mapping 中已有的 `residue_id`，不得根据 residue name、编号、chain 或其它结构字段自行重建其值。

### component_id

**Canonical term:** `component_id`  
**Preferred expression:** `component_id`  
**Definition:** 结构准备 1.2 在一个 model 的正式 `classification_result.yaml` 中为最终 component 物化的稳定、不透明身份标识。该 component 作为直接父级拥有其 `residues`，并使 component 与成员 residue 能在后续选择、结构映射和 topology preparation 中持续引用。  
**Scope / distinction:** `component_id` 在当前 model 的正式结果中唯一；它不是 CCD component ID、residue name、PDB `chain_id` 或其它运行时 chain 编号。下游 Skill 应直接消费正式结果或 mapping 中已有的 `component_id`，不得根据 residue name、chain 组织或当前空间关系自行重建其值。

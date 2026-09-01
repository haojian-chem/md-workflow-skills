# Skill generation and Markdown archival rules

Status: CURRENT

本文件定义新建、重构和冻结科研 Skill 时的默认生成方式、状态同步要求，以及过期 Markdown 的归档规则。

## 1. 默认生成模型与目录保留

科研 Skill 默认从一个 main `SKILL.md` 开始：

```text
<skill-directory>/
├── SKILL.md
├── references/        # optional
├── schemas/           # optional
├── scripts/           # optional
└── <supporting-skill>/SKILL.md   # only when justified
```

正式 Skill package 中只有 `SKILL.md` 是默认必需业务文件。其他目录只有在当前职责确实需要时才创建。

但 **Stage / Step 目录身份与 `SKILL.md` 激活状态是两件事**。如果某个 Stage / Step 的编号、名称和未来 package 路径已经确定，可以在正式 Skill generation 前保留该目录。Git 需要占位文件时使用最小 `.gitkeep`；不要为了保留目录创建伪 `README`、空 schema 或伪 `SKILL.md`。

因此：

```text
目录存在
≠ Skill 已生成
≠ Skill 已激活

SKILL.md 存在且已按许可生成
→ 才表示该 Step 有 active Skill entry
```

撤回未经许可的伪 `SKILL.md` 时，如果目录规划本身正确，**删除伪 Skill 文件但保留目录**；不要把正确的 Stage / Step 目录一起删掉。

不要先按 Workflow / Operation / Validator 分类再决定文件结构，也不要为了“完整”自动生成空 schema、content map 或配套 Validator。

## 2. Main Skill 与 references

main `SKILL.md` 保存 Agent 执行当前职责所需的主线：

- purpose / scope；
- 当前输入、对象和证据；
- reuse；
- 核心执行/判断边界；
- validation；
- results；
- 何时按需读取 reference、调用 supporting Skill 或 Tool。

属于当前 Skill、但过长或只在特定条件下需要的内容优先放 `references/`，例如：

- 长科学规则；
- registry / table；
- 大枚举；
- 复杂选择规则；
- 特定对象才需要的方法细节。

主 Skill 对 reference 只保留：

```text
何时读取
→ 读取哪个 reference
→ 它解决什么局部问题
```

不要在 main Skill 和 reference 中各写一份完整规则。某条详细规则一旦下放给 reference，reference 是该细节的 owner，main Skill 只保留必要摘要和入口。

仓库级 shared references：

```text
references/task_execution_rules.md
references/target_lineage_rules.md
references/result_generation_rules.md
references/canonical_terminology.md
```

`task_execution_rules.md` 保存各科研执行 Skill 共同遵守的 Task Execution 规则，包括 Task Sheet 执行语义、execution-scope confirmation、reuse 与通用执行顺序。它不是独立 Skill 或额外执行环节。所有正式科研执行 Skill 必须在 main `SKILL.md` 中显式引用它；具体 Stage / Step / capability 的科学规则仍由各自 Skill 拥有。

`target_lineage_rules.md` 保存使用 `target` 的科研执行 Skill 共同遵守的 local target / target record / branch / merge lineage 规则。只有 current Skill 实际使用 `target` 时才按 shared Task Execution 入口读取；Stage 4 formal run unit、Stage 5 analysis plan item 等已有其它 execution identity 的对象不因此被强制 target 化。

`result_generation_rules.md` 保存科研执行 Skill 共同遵守的 validation、正式结果生成、结果记录与结果接口规则。Authoring 在当前工作涉及 validation、results、`references/results.md`、结果文件 / 字段语义或 project-result registration 时读取它；具体科学 validation、正式结果集合和 Skill-specific 结果语义仍由对应科研执行 Skill 拥有。

`canonical_terminology.md` 维护跨 Skill 需要稳定一致的正式术语。它也不是独立 Skill 或执行环节，只拥有术语名称、优先表达、定义和边界；不接管具体科学规则。Authoring 在 Skill 构筑、设计讨论、architecture freeze 编写、生成、审查和重构全过程中必须读取并使用它。执行阶段可通过 `task_execution_rules.md` 按需读取它，因此不要求为现有 execution Skill 逐一建立平行 glossary。

### Negative scope / 禁止项

“不做什么”不是 main Skill 的默认完整性要求。不要为了显得职责边界完整，系统性罗列所有相邻环节、下游环节或理论上可能发生但当前 Skill 不负责的事项。

只有在以下情况之一成立时，才应明确写出 `不做 / 不得 / 禁止`：

- 容易与当前职责混淆，不明确会高概率导致实际越界或误操作；
- 用于保护当前 Skill 的 ownership，阻止其承担其他 owner 的职责；
- 属于安全、数据完整性、不可逆操作或输入保护边界；
- 是当前设计中已明确否定、且 Agent 很可能采用的默认行为；
- 对 validation 或 result correctness 有直接影响。

若上述必要性不存在，则不需要出现对应 negative-scope 条目。未被列出的外部职责自然由当前 Skill 的 purpose / scope、ownership 和 external-skill boundary 限制；不要通过冗长的“本 Skill 不负责……”清单重复描述其它环节。

### Rule necessity gate

在对拟新增内容执行 ownership 判断之前，先判断它是否真的需要成为 Skill 的固定规则。

Skill 应优先固定需要跨 Task Sheet / 跨科研任务保持一致、且对职责正确性有实际价值的内容，例如：

- 稳定的科学/技术判据；
- 输入/输出接口和依赖语义；
- reuse / validation / formal-result 语义；
- 安全、数据完整性或不可逆操作边界；
- 不固定就会高概率造成越界、歧义或不可恢复结果的约束。

以下本身**不足以**构成规则化理由：

- 运行时可能遇到某种异常或分支；
- 为了让流程看起来完整；
- 可以继续细分出更多状态转换；
- Agent 将来“可能需要知道怎么选”。

如果某项决定可以由 Task Execution Agent 或用户根据当前上下文可靠判断，且不要求形成跨 Task Sheet / 跨科研任务稳定语义、接口约束、科学判据或结果生命周期，则保留为运行时裁量，不继续把它展开成统一 decision tree、状态机、fallback 链或完整工作流。

判断顺序：

```text
这件事必须成为 Skill 固定规则吗？
├─ 否 → 留给 Agent / 用户按当前执行上下文判断；停止规则下钻
└─ 是 → 再判断该规则归谁拥有
```

因此 **rule-necessity gate 必须先于 rule-ownership gate**。一条内容即使“没有其它 owner”，也不自动意味着当前 Skill 应该把它规则化。

### Task Sheet 与 scientific prerequisite

Task Sheet 是一个有界执行记录，不等同于整个科研任务，也不要求投影完整 Workflow 或完整 Stage。Authoring 输入契约、前置关系和流程边界时必须区分：

```text
当前 Task Sheet 中列了哪些 Step
≠
当前科学 / 技术 prerequisite 是什么
```

规则：

- 当前 Skill 如果存在真实 prerequisite，直接写明开始当前职责前必须已经存在的**上游方案、正式结果、对象状态、决策或其它实际条件**；
- 不得仅因为编号上存在更早 Step，就把该 Step 是否出现在当前 Task Sheet 当作 prerequisite 判据；
- 更早 Step 不在当前 Task Sheet，不代表其 prerequisite 可以忽略。该 prerequisite 可以由当前 Task Sheet、同一科研任务的前序 Task Sheet、项目正式结果或其它可追溯记录满足；
- 已有前序 Task Sheet 能提供仍适用的 prerequisite 时，不为了形式完整在当前 Task Sheet 机械复制该 Step；
- 当前执行范围只需要局部流程时，不自动补入与当前目标无关的更早或更晚 Step；
- 如果前序方案或正式结果因对象、参数定义基础或用户决定变化而失效，应返回真正拥有该 prerequisite 的 owner 更新 / 重新形成，而不是因为换了 Task Sheet 静默绕过；
- Task Sheet 拆分本身不构成 reuse、重新执行或重新生成上游结果的理由；这些行为仍由对应 Skill 的实际 reuse / prerequisite 规则决定。

Authoring 过程中如果发现现有 Skill 把“同一 Task Sheet 中必须出现某 Step”与“必须先满足某个科学 prerequisite”混为一谈，应修正为实际 prerequisite contract，而不是简单删除前置关系。

### 执行范围确认与 Agent 技术裁量

Authoring 必须把**用户要执行什么**与**在已经确认的范围内怎样实现**分开设计。

共享 authority 为：

`references/task_execution_rules.md`

其中 execution-scope confirmation gate 对所有科研执行 Skill 生效；局部 Skill 不得用“Agent 可判断”“通常”“默认”“根据体系决定”等措辞覆盖或弱化这一 gate。

如果某个省略信息会改变以下任一内容，就属于执行范围问题：

- 当前处理哪些具体对象、哪些 source targets、哪些 residue / component / trajectory；
- 是处理一个、若干还是全部候选对象；
- 多个对象如何组成一个或多个 local targets / execution objects；
- 是否扩展到额外 Step、capability、分析范围或其它工作项；
- 用户是否要求把多个 alternative treatment / strategy 保留为独立后续分支。

这些内容如果结合用户当前指令、当前 Task Sheet 与明确前序决定后仍存在多个实质不同解释，当前 Skill 必须触发用户确认，不得写成 Agent 自动选择默认范围。

相反，下列情况可以继续由 Agent 自主处理：

- 用户已经明确执行范围，只缺少能够从正式结果唯一补足且不改变对象 membership / grouping 的 identity grounding；
- 当前 Skill 已有明确科学 / 技术判据，现有 evidence 能在已确认范围内唯一支持一种处理方式；
- 当前 Skill 允许根据软件、硬件或实际输入选择实现方式，且该选择不改变已确认执行范围或科学含义。

因此，Skill 中写“信息能够唯一确定时直接使用”时，必须能判断这句话指的是**已确认范围内的信息恢复 / 技术判断**，而不是用户尚未明确的执行范围。User-confirmation section 只补充 Skill-specific ambiguity；shared scope gate 不应在每个 Skill 重写一套平行规则。

### Terminology and writing precision

术语归一化贯穿整个 Skill authoring lifecycle，**不是最终 Markdown 写作阶段才执行的清理步骤**。在 Skill 构筑、设计讨论、architecture freeze 编写、生成、审查和重构过程中，Agent 与用户讨论方案时也必须优先使用项目当前正式术语。

用户的口语、简称、临时称呼和不完整表述只作为语义输入；不要求用户先把表达规范化。Agent 应结合当前上下文理解其实际指代，并在自己的后续讨论、设计记录、freeze 和正式 Skill 文本中恢复为项目正式术语，而不是继续传播临时称呼。

#### Canonical terminology

跨 Skill 正式术语的 shared authority 为：

`references/canonical_terminology.md`

进入 Skill 构筑、设计讨论、architecture freeze 编写、生成、审查或重构时先读取该文件，再结合 current Skill、architecture freeze、正式上下游接口和当前科学语境确定局部术语。

- 同一 execution object、artifact、state、scientific concept 或判断对象，在 authoring discussion、freeze、Skill 及其 references 中使用一个稳定的正式术语；不要为了语言变化轮换同义词。
- `canonical_terminology.md` 已有条目时，Agent 在 authoring discussion 和正式文本中都优先采用该条目的 `Preferred expression`；用户本轮对话中的口语化说法不能覆盖已有 canonical term。
- 只有需要跨 Skill 稳定、会进入 Task Sheet / 项目结果索引 / Stage 间正式接口，或名称漂移会造成对象混淆的术语，才进入 `canonical_terminology.md`。只在一个 Skill 内使用的局部术语由该 Skill 自己定义和维护。
- `canonical_terminology.md` 只维护 `Canonical term / Preferred expression / Definition / Scope / distinction`。**不维护 alias、口语映射或 deprecated / do-not-use 列表。** 用户的简称和临时表达由 Agent 根据当前上下文理解，不固化成静态映射。
- `canonical_terminology.md` 负责“对象或概念正式叫什么、具体指什么、与什么不同”；本文件的 semantic-explicitness 规则负责“如何把对象、属性、reference / criterion 和判断关系写清楚”。术语 reference 不承担科学规则，写作规则也不另行定义第二套对象名称。
- 如果当前 authoring 工作确实建立了新的跨 Skill 稳定术语，并且当前窗口拥有 shared path 写权限，则同步更新 `canonical_terminology.md`；没有写权限时提交精确的术语条目给当前 owner，不在局部 Skill 中另建平行 glossary。
- 如果确实需要引入新的局部术语，首次出现时明确它指什么，之后保持同一称呼；不要让一个术语在同一 Skill 中指代多个不同对象。
- 文件名、字段名、命令、软件选项、section name、enum、identifier 等机器或接口级名称保持原文，不做自由翻译或改名。

#### Semantic explicitness

科学/技术判断应写出实际判断关系，不要把完整含义压缩成未定义的抽象标签。

如果一句话使用 `兼容 / 合理 / 正确 / 有效 / 一致 / 匹配 / compatible / valid / reasonable / correct / consistent` 等词，但不展开就可能存在多种解释，则必须明确：

```text
检查什么对象
→ 检查它的什么属性
→ 以什么 reference / criterion 为依据
→ 按什么关系作出判断
```

例如，不写：

```text
heavy-atom name 是否兼容
```

应写成能够直接指导执行的具体关系，例如：

```text
检查 final PDB 中标准残基的重原子名称，确认这些名称能够被目标力场中对应残基的定义正确识别。
```

只有在完整关系已经在当前上下文中明确定义、缩写不会损失判断对象或判据时，才可以在后文使用较短表述。

#### Language normalization

中文 Skill 以中文叙述为主体。英文只在保留原文确有信息价值时使用，例如：

- 软件、方法、力场等正式专名；
- 文件名、字段名、命令、命令行选项、配置键和软件原生语法；
- 项目已经固定为英文且翻译会造成接口或术语歧义的正式术语。

普通技术概念如果可以准确、自然地用中文表达，则使用中文，不为了显得技术化而中英混排。必要时可以在首次出现时用“中文（英文原词）”建立与软件文档或外部术语的对应，后文保持一种固定表述。

例如，若语义只是“目标力场中对应残基的定义”，不应无必要写成“目标力场对应 `residue definition`”；只有在需要明确指向软件中的具体原生实体或字段时才保留相应英文。

在 authoring 讨论推进过程中持续检查；生成或重构完成后再做一次全文检查：

- `canonical_terminology.md` 已有术语是否在讨论和正式文本中使用其 `Preferred expression`；
- 同一对象是否出现多套名称；
- 用户口语/简称是否被 Agent 继续传播为正式术语；
- 是否存在没有展开 reference / criterion 的抽象判断句；
- 是否存在无信息增益的中英文混排；
- discussion / freeze / main Skill / local references 对同一对象的术语是否一致。

## 3. Supporting Skill 的拆分门槛

只有内容同时具备明显复杂度和清楚独立边界时才拆 supporting Skill，例如：

- 可独立按需加载；
- 有独立完整科学/技术职责；
- 被多个 main Skill 复用；
- 需要独立测试/validation 生命周期；
- 拆分能显著降低主 Skill 上下文，而不会增加无意义 dispatcher hop。

如果只是“内容比较长”，优先 reference；如果只是几条 validation 或 helper 规则，不单独拆 Skill。

## 4. 生成顺序

新建或重构科研执行 Skill 时按以下顺序：

```text
读取 00_authoring/SKILL.md
+ references/task_execution_rules.md
+ references/canonical_terminology.md
+ 当前目标 Skill / 对应 freeze + 直接相关上下游/相邻 Skill
+ 当前工作涉及 target lineage 时读取 references/target_lineage_rules.md
+ 当前工作涉及 validation / results / 结果接口时读取 references/result_generation_rules.md
↓
从 authoring discussion 开始即使用 canonical terminology；用户口语仅作为语义输入
↓
读取 MD_WORKFLOW_MASTER_PLAN.md 中目标 Stage / Step 的当前建设状态
↓
确认当前 Skill 的唯一职责与 write ownership
↓
以 canonical_terminology.md 为跨 Skill 术语 authority，对讨论记录、freeze、current interfaces 中的对象和术语做归一化
↓
对拟新增内容先执行 rule-necessity gate
↓
只对确有必要固定的规则执行 rule-ownership gate
↓
检查当前 Skill 的 input / prerequisite contract 是否按真实上游对象或状态定义，而不是按当前 Task Sheet 中是否出现更早编号 Step 定义
↓
检查当前 Skill 是否把 execution scope ambiguity 与已确认范围内的 Agent scientific / technical discretion 清楚分开
↓
先完成 main SKILL.md 主线，并显式引用 references/task_execution_rules.md
↓
识别长/条件性细节 → references/
↓
仅在复杂且边界清晰时拆 supporting Skill
↓
仅在确有机器约束/确定性能力时增加 schemas/scripts/Tool
↓
检查越界定义、重复定义、shadow specification，以及是否把 Agent/用户的任务级裁量误固化成流程
↓
检查 discussion / freeze / Skill 的术语一致性、判断关系是否具体、以及是否存在无必要的中英文混排
↓
若本次确立新的跨 Skill 稳定术语，按 shared-path 写权限更新 canonical_terminology.md 或提交给当前 owner
↓
完成本次要求的 validation / self-check
↓
处理被本次改动取代的旧文件，但保留仍正确的 Stage / Step 目录
↓
同步 Stage main Skill 的 current/freeze-only entry（如该 Stage main Skill维护入口）
↓
同步 MD_WORKFLOW_MASTER_PLAN.md 中目标 Stage / Step 的建设状态与 current entry
↓
如新增/替换 architecture freeze，再同步 architecture_freezes/README.md
↓
交付
```

不得先批量生成一套目录、YAML metadata 或模板，再把实际职责硬塞进去。

**Architecture freeze 完成不等于 Skill generation 已获许可。** 只有用户明确要求生成/实现某个 Skill 时，才把对应 freeze 转写为 active `SKILL.md`。

## 5. Architecture-freeze 文件位置与粒度

当某个 Stage / Workflow / Step 的设计已经明确敲定，需要保存正式 freeze record 时，统一写入：

```text
00_authoring/architecture_freezes/
```

规则：

- 不在 `00_authoring/` 根目录散放新的 `WORKFLOW*_ARCHITECTURE_FREEZE*.md`；
- freeze 可以是 Stage-level，也可以是尚未正式生成 Skill 的 Step-level；
- freeze 保存已经冻结的架构、职责边界、关键科学/技术规则和明确拒绝项；
- 当目标 Step **尚无 current Skill** 时，freeze 可以保留已经讨论到 implementation-ready 的细节，作为后续 Skill generation 的直接输入，避免重复讨论或信息丢失；
- freeze 文件不是 runtime Skill，不能因为内容足够详细就作为 `SKILL.md` 直接执行；
- 当正式 current Skill 已经生成后，具体可变执行细节由对应 current `SKILL.md` / references 拥有；freeze 不维护第二套平行的 mutable specification；
- 如果 Skill generation 发现此前讨论已经明确但 freeze 漏记的事实，应先补回对应 freeze 或在同次 authoring 中明确归属，不从历史伪 Skill 中静默丢失；
- 同一 Stage / Step 有新的 freeze record 明确取代旧 freeze 时，先迁移 current 引用，再将被取代的旧 Markdown 移入 `00_authoring/archive/`；
- `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 只记录 current freeze 入口和建设状态，不复制完整 freeze 内容。

当前目录入口：

`00_authoring/architecture_freezes/README.md`

## 6. 状态维护是生成流程的一部分

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 是项目级 Stage / Step **建设状态与 current entry 的唯一 owner**。

它不是静态说明文件。只要 authoring 工作改变了真实状态，就必须在同一工作流中同步；否则状态文件会失去意义。

必须同步的典型变化包括：

```text
设计中 → FROZEN
freeze-only → Skill generation approved / in progress
freeze-only → active Skill generated
active Skill → representative validation milestone changed
current → superseded / retired / replaced
```

### 6.1 Skill generation 的完成条件

生成目标 `SKILL.md` 后，至少检查：

1. `MD_WORKFLOW_MASTER_PLAN.md` 中该 Step 是否仍写成 `freeze-only / under authoring / not generated`；
2. 对应 Stage main Skill 是否仍把该 Step 指向 freeze 而不是 current `SKILL.md`；
3. 是否新增或替换了 architecture freeze，需要更新 `architecture_freezes/README.md`；
4. 是否改变了 Stage 总体状态描述。

只要其中存在需要更新的项，就必须一起修改。

**`SKILL.md` 已写入但这些状态入口仍陈旧，不算完整 Skill generation。**

### 6.2 多窗口状态同步

状态同步不得因为 `MD_WORKFLOW_MASTER_PLAN.md` 是共享文件而被静默跳过。

规则：

- 写状态前重新读取 current `main` 和 `coordination/file_ownership.yaml`；
- 若 Master Plan 没有被其他窗口显式占用，完成当前 Skill 的窗口拥有一个**窄的 status-only 写权限**：只改自己 Stage / Step 的建设状态与 current entry；
- 这个例外不授予修改其他 Stage catalog、architecture 或科学规则的权限；
- 若 Master Plan 已有显式 writer，则不并发写，向该 writer 提交精确的状态变更；交付时必须明确该同步仍待落地，不能宣称 repository integration 已全部完成；
- 不建立新的 `SYNC_STATUS.md`、`status.yaml`、skill inventory 或其他 parallel 状态层。

## 7. Project-design 与 repository shared references

项目级 authoring 设计资料位于：

```text
00_authoring/project_design/
```

当前其中只承担 project-level design / status 的文件：

```text
MD_WORKFLOW_MASTER_PLAN.md
→ Stage numbering / catalog / 建设状态 / current entry
```

仓库级 shared references 位于：

```text
references/task_execution_rules.md
references/target_lineage_rules.md
references/result_generation_rules.md
references/canonical_terminology.md
```

`task_execution_rules.md` 定义科研执行 Skill 共用的 Task Execution 规则，并拥有 execution-scope confirmation gate；`target_lineage_rules.md` 定义使用 `target` 的科研执行 Skill 共用的 local target / target record / branch / merge lineage；`result_generation_rules.md` 定义科研执行 Skill 共用的 validation、正式结果生成、结果记录与结果接口规则；`canonical_terminology.md` 维护跨 Skill canonical terminology。它们都不属于 `00_authoring/project_design/`，也不是独立 runtime Skill。

Authoring 在 Skill 构筑、设计讨论、freeze 编写、生成、审查和重构过程中读取 `task_execution_rules.md` 与 `canonical_terminology.md`；当前工作涉及 target lineage 时读取 `target_lineage_rules.md`；涉及 validation / results / 结果接口时读取 `result_generation_rules.md`。各 execution Skill 通过自身 `SKILL.md` 对 `task_execution_rules.md` 的正式引用获得通用执行规则，并由该 shared reference 提供按需读取其它 shared references 的入口。

不要把具体 Stage 的内部科学规则、字段、validation 或文件生命周期复制进 project-design、shared Task Execution / target-lineage / result-generation reference 或 canonical terminology；这些内容继续由对应 current Skill / local reference / architecture freeze 拥有。

不再单独维护 current `SYNC_STATUS.md`。如果某项内容只是“当前 Stage 建设到哪里”，归入 Master Plan；如果是具体规则，则归入真正的规则 owner。

## 8. 过期文件归档

当前 authoring/Skill 活跃路径中不应长期保留 `SUPERSEDED` / `LEGACY` / `HISTORY ONLY` 文件作为伪 current entry。

当一个文件已明确被 current authority 取代，且不再是 runtime/authoring authority 时：

1. 确认 current 文件已经完整接管其仍有效内容；
2. 更新所有 current 引用，使普通 authoring/runtime 不再依赖旧路径；
3. 需要保留以便历史查阅的 Markdown 移入：

```text
00_authoring/archive/
```

4. archive 按语义归类，例如 `root_history/`、`legacy_runtime/`、旧 authoring assets；
5. 从原 active path 删除旧文件；不要同时在 active path 留 tombstone、archive 再留一份副本；
6. 对不再有 current 用途的旧 YAML/schema/index，通常直接从 active path 删除，由 Git history 保留历史；只有明确有审计价值时才归档；
7. Git history 继续保存完整历史版本。

如果被撤回的是**未经许可的伪 Skill implementation**，先把已经讨论并敲定、仍有后续生成价值的信息完整迁入对应 architecture freeze；再删除伪 `SKILL.md`。若其 Stage / Step 目录规划仍然正确，则保留该目录，不按“旧文件归档”规则把目录整体移走。

Archive 文件不是 current authority，普通 Skill authoring、Task Execution Agent 和 Manager 均不得默认读取。

## 9. 什么不应归档

不要因为“文件较旧”就归档仍然有效的：

- current `SKILL.md`；
- current references；
- 仍然有效的 architecture-freeze record；
- 已确定、仍用于未来 Skill 落位的 Stage / Step package 目录；
- 当前确有独立用途的 template / coordination record / project-design document；
- 真实科研项目的结果或运行记录。

归档依据是**authority 已被明确取代**，不是文件日期。

## 10. Metadata 最小化

不要默认给每个 Skill 再创建一份平行 metadata 来描述它自己已经说明的内容。

当前默认不建立：

```text
content map
skill inventory entry
额外 role taxonomy YAML
```

如果某个结构化文件没有独立机器用途，只是在重复：

```text
Skill 在哪里
Skill 拥有什么
Skill 引用了谁
Skill 当前是什么状态
```

则优先删除这层 metadata，由实际 `SKILL.md`、目录结构以及真正独立的 Stage/Tool/coordination 记录承担各自职责。

## 11. 替换 / 生成检查

交付前确认：

- [ ] 新 main Skill / reference / freeze 已接管所有仍有效规则；
- [ ] 科研执行 Skill 的 main `SKILL.md` 已显式引用 `references/task_execution_rules.md`；
- [ ] 当前 authoring 涉及 target lineage 时，已读取 `references/target_lineage_rules.md`；
- [ ] 当前 authoring 涉及 validation / results / 结果接口时，已读取 `references/result_generation_rules.md`；
- [ ] 已读取 `references/canonical_terminology.md`；其中已有条目在 authoring discussion、freeze 和正式 Skill 中使用其 `Preferred expression`；
- [ ] Agent 在设计讨论中没有继续沿用用户口语、简称或临时称呼作为新的项目正式术语；
- [ ] 同一对象 / artifact / state / scientific concept 在 discussion / freeze / Skill / references 中没有出现多套正式术语；
- [ ] 没有为用户口语、alias 或历史称呼建立 shared static mapping；`canonical_terminology.md` 只保存确有跨 Skill 稳定价值的正式术语；
- [ ] `canonical_terminology.md` 没有承担科学判据或 semantic-explicitness 规则；本 authoring rule 没有另行建立第二套 canonical terminology；
- [ ] 科学/技术判断已明确检查对象、属性、reference / criterion 和判断关系，没有用未定义的“兼容 / 合理 / 正确 / 有效 / 一致”等抽象词代替实际判据；
- [ ] 中文 Skill 没有无信息增益的中英文混排；机器接口名、软件语法和确有必要的固定英文术语保持原文；
- [ ] current 文件不再引用错误旧路径；
- [ ] 同一规则没有在新旧 active 文件各保留一份；
- [ ] 没有把 shared Task Execution / target-lineage / result-generation reference 或 canonical terminology 误建成独立 Skill / dispatcher；
- [ ] 没有把可由 Agent / 用户基于当前执行上下文可靠判断的策略，继续展开成无必要的统一决策树、状态机、fallback 链或完整工作流；
- [ ] 没有把一张 Task Sheet 等同于整个科研任务或完整 Stage / Workflow；
- [ ] 当前 Skill 的 prerequisite 按真实上游方案 / 结果 / 状态 / 决策定义，而不是按更早编号 Step 是否出现在当前 Task Sheet 定义；
- [ ] 前序 Task Sheet 已满足仍适用 prerequisite 时，没有为了流程完整在当前 Task Sheet 机械复制前序 Step；
- [ ] 当前 Task Sheet 只覆盖局部范围时，没有因此忽略真实 prerequisite，也没有补入与当前目标无关的步骤；
- [ ] 当前 Skill 中的 Agent 自主判断只发生在已经确认的 execution scope 内，没有替用户决定尚未明确的对象集合、target grouping、Step / capability coverage 或 branch 范围；
- [ ] 如果用户指令 + 当前 Task Sheet + 明确前序决定仍允许多个实质不同执行范围，Skill 会先触发 shared user confirmation，而不是采用默认范围；
- [ ] identity grounding 与 scope selection 已区分：唯一身份补足可以自动完成，改变对象 membership / grouping / coverage 的选择不能自动完成；
- [ ] 被撤回的伪 Skill 已删除，但正确的 Stage / Step 目录仍保留；
- [ ] archive 没有被加入默认 startup/read list；
- [ ] architecture-freeze 使用 `00_authoring/architecture_freezes/` current 路径；
- [ ] freeze 与 Skill 的授权状态没有混淆：freeze-only 不能被当作 active runtime Skill；
- [ ] 如果本次改变了建设状态，`MD_WORKFLOW_MASTER_PLAN.md` 已同步或有明确 writer handoff；
- [ ] Stage main Skill 中对应 current/freeze-only entry 已同步；
- [ ] project-level 状态只在 Master Plan 维护，不再另建 parallel sync/status 文件；
- [ ] 没有为了 discoverability 又建立一份重复 Skill 内容的 YAML metadata。

## 12. 原则摘要

```text
一个职责 → 一个 main Skill
长而同属当前职责 → reference
复杂且独立 → supporting Skill
确定性机械能力 → script / Tool
可由 Agent / 用户基于当前执行上下文可靠判断、无需跨 Task Sheet / 跨科研任务稳定的策略 → 不固化为 Skill 规则
执行范围不明确 → 先确认用户意图；只读核对可以先做，实质执行不可先做
执行范围已明确 → 范围内科学 / 技术细节按 current Skill 判据由 Agent 处理
identity grounding 唯一可补足 → 可自动 grounding；改变对象 membership / grouping / coverage → 不可用 grounding 名义替用户决定
Task Sheet → 有界执行记录，不等同于整个科研任务、完整 Stage 或完整 Workflow
scientific prerequisite → 按真实上游方案 / 结果 / 状态 / 决策定义，不按当前 Task Sheet 中是否出现更早编号 Step 定义
前序 Task Sheet 已满足 prerequisite → 显式消费，不机械复制前序 Step
使用 target 的跨 Skill lineage → references/target_lineage_rules.md
跨 Skill 正式术语 → references/canonical_terminology.md
术语规范从 authoring discussion 开始生效；用户口语只作为输入，Agent 输出回到 canonical terminology
同一对象 → 一个 canonical term；discussion / freeze / Skill / references 保持一致
canonical_terminology.md → 对象叫什么、是什么、与什么不同
semantic explicitness → 对象、属性、reference / criterion 与实际判断关系如何写清楚
科学/技术判断 → 写明对象、属性、reference / criterion 与实际判断关系
中文 Skill → 中文为主体；只保留有信息价值的英文原文
已确定 Stage / Step package 路径 → 可先保留目录；目录存在 ≠ Skill 已生成
Stage / Workflow / pre-Skill Step architecture freeze → 00_authoring/architecture_freezes/
freeze 完成 ≠ Skill generation 获批
Skill generation 改变状态 → 必须同步 MD_WORKFLOW_MASTER_PLAN.md
科研执行 Skill 共用的 Task Execution 规则 → references/task_execution_rules.md
科研执行 Skill 共用的 target lineage 规则 → references/target_lineage_rules.md
科研执行 Skill 共用的 validation / result generation / result-recording 规则 → references/result_generation_rules.md
项目级 authoring design / status → 00_authoring/project_design/
多窗口 writer assignment → 00_authoring/coordination/
已被取代的 Markdown → archive
无独立用途的旧 YAML/schema/index → 删除 active copy，Git history 保留
已有 owner 的规则 → 引用，不复制
```

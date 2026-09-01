# Task execution rules

Status: CURRENT SHARED REFERENCE

本文件定义真实 MD 项目中，各科研执行 Skill 共同遵守的 Task Execution 规则。

它是仓库级 shared reference，**不是独立 Skill、不是额外 runtime 环节，也不改变 Scientific Stage 编号**。科研执行仍由当前 Stage / Step / capability `SKILL.md` 直接指导；各 active execution Skill 必须显式引用本文件。`00_authoring/SKILL.md` 也必须引用本文件，以保证后续 Skill 构筑与这些通用执行规则兼容。

Stage-specific 的科学规则、计划调整方式、execution object、validation 和 results 继续由对应 Stage / Step / capability Skill 拥有。本文件只定义科研执行 Skill 共用的执行机制，不创建第二套科学决策规则。

## Project records

真实项目默认使用：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    └── ...
```

职责：

- `task_index.md`：Task Sheet 导航和状态；
- `tasks/Txxxx.md`：一个有界执行范围的 Task Sheet，保存当前目标、计划、进度和最小恢复上下文；
- `project_result_index.md`：跨 Task Sheet / 跨科研任务 / 跨对话的正式结果检索入口，不保存当前执行状态。

一个科研任务可以由多张 Task Sheet 共同承载。`Txxxx` 标识当前 Task Sheet，不等同于“整个科研任务”的永久身份。为了控制单张 Task Sheet 的上下文规模、隔离已经废弃或错误的方案、或按用户要求拆分执行，可以在同一科研任务内建立新的 Task Sheet 继续后续工作。

Task Sheet 状态：

```text
未完成
已完成
已终止
```

普通 Task Sheet 子环节状态同样使用：

```text
未完成
已完成
已终止
```

语义：

- `未完成`：当前 Task Sheet 仍保留该任务项，且其当前职责尚未闭合；同时是 Task Sheet resolution 时默认可自动恢复的 active 状态；
- `已完成`：当前 Task Sheet 中的该任务项已经按其 current Skill 完成；
- `已终止`：该任务项已经进入执行历史，但当前 Task Sheet 不再继续执行它；必须能够追溯终止原因。具体何种情形可终止，由当前 Skill、Stage-specific 规则或当前执行情况决定。

Stage-specific 内部对象如有不同状态模型，以对应 current owner 为准。

## Task Sheet resolution

当用户要求在真实项目中执行、继续、修改或正式记录 MD Workflow 科研工作，而当前还没有一个已经明确绑定并可继续使用的 Task Sheet 时，**必须先完成 Task Sheet resolution，再进入科研执行 Skill**。

纯解释、方法讨论、概念问答或不要求写入/推进真实项目执行状态的咨询，不因为存在本规则就自动创建 Task Sheet。

Task Sheet resolution 的目标是回答：

> 当前科研执行应落在哪一张 Task Sheet；如果没有适用的现有 Task Sheet，是否需要创建新的 Task Sheet？

### 1. 已明确指定或已经绑定 Task Sheet

如果用户明确给出 Task Sheet ID / 名称，或当前执行上下文已经明确绑定某张 Task Sheet：

1. 读取 `task_index.md` 核对该 Task Sheet 的存在与当前状态；
2. 状态为 `未完成` 且与用户当前执行指令仍一致时，直接读取并继续该 Task Sheet；
3. 状态为 `已完成` / `已终止` 时，除非用户明确要求重新打开、重新规划或继续该历史执行范围，否则不静默把它当作 active Task Sheet 使用；需要继续同一科研任务时进入 Manager 判断是否建立后续 Task Sheet；
4. 用户当前指令与已绑定 Task Sheet 的执行范围明显冲突时，不静默沿用旧绑定；先按下面的候选定位 / 新 Task Sheet 规则处理。

### 2. 当前没有明确绑定 Task Sheet

先读取：

```text
<project_root>/00_project_records/task_index.md
```

默认只把状态为：

```text
未完成
```

的 Task Sheet 作为 active candidates。

优先使用 `task_index.md` 已有的 ID、名称、状态、路径和其它现有导航信息判断哪些 candidate 与用户当前科研指令 / 科研任务相关。不得仅因为某张 Task Sheet：

- 最近更新；
- 编号最大；
- 文件顺序靠后；
- 是项目中唯一一个 `未完成` 但与当前科研指令无关；

就自动绑定。

如果索引信息不足以判断，而只存在少数合理的 `未完成` candidates，可以只读取这些候选 Task Sheet 做最小必要的只读核对；**不得为定位当前 Task Sheet 无边界遍历全部历史 Task Sheets**。

候选处理：

```text
唯一相关的未完成 Task Sheet
→ 自动绑定并读取

多个合理相关的未完成 Task Sheet
→ 向用户说明候选并确认使用哪一张

没有相关的未完成 Task Sheet
→ 进入 Manager 的 new-Task-Sheet responsibility
```

这里的“唯一相关”要求当前用户指令 / 科研任务与该 Task Sheet 的已有目标、范围或最小恢复上下文能够明确对应；不是“项目中只有一个未完成 Task Sheet”的机械判断。

### 3. 没有相关 active Task Sheet 时

Manager current entry：

```text
00_manager/SKILL.md
```

如果用户当前指令已经足以确定一个新的有界执行目标，Manager **直接创建新 Task Sheet、完成初始规划并交给 Task Execution Agent**；不要求用户额外再说一次“建立任务单”。

如果新 Task Sheet 本身的执行范围仍不清晰，则 Manager 可以读取 `task_index.md` 和必要的最小项目导航信息做只读核对，并按本文件的“执行范围确认”原则向用户确认；范围确认前不创建带有猜测性执行范围的新 Task Sheet。

如果项目尚未建立 `00_project_records/task_index.md` / `tasks/` 等基础记录，则由 Manager 先完成当前项目最小初始化，再按上述规则创建首张 Task Sheet。

`已完成` / `已终止` Task Sheet 默认不作为 active candidate。它们可以作为同一科研任务的前序历史、prerequisite 或结果来源被后续 Task Sheet 显式引用，但不因为内容相关就自动重新变成 `未完成`。

### 4. Resolution gate 的执行边界

在 Task Sheet 尚未完成 resolution 前，允许：

- 读取 `task_index.md`；
- 读取用户明确指定或少数合理 active candidates；
- 判断是否需要 Manager 创建新的 Task Sheet；
- 向用户提出定位 / 执行范围确认问题。

不得：

- 直接进入某个科研 Step 并修改科研对象；
- 为未绑定的执行创建 target / target record；
- 写入正式结果；
- 把某张历史 Task Sheet 静默改成 `未完成`；
- 因为发现一个可复用科研结果而跳过 Task Sheet resolution。

Task Sheet resolution 只在**执行入口尚未绑定 Task Sheet、当前绑定失效、或确实需要建立后续 Task Sheet**时触发。一个已经绑定且仍为 `未完成` 的 Task Sheet 在普通 Step 之间连续执行时，不为每个 Step 重复进入 Manager 或重复扫描 `task_index.md`。

## Task Sheet scope

一张 Task Sheet 只覆盖当前需要在该执行单元中处理的有界范围，不要求包含完整 MD Workflow、完整 Stage，或某个 Stage 从第一项到最后一项的全部 Step。

因此 Task Sheet 可以：

- 只承载一个更大科研任务中的一部分工作；
- 只包含一个 Stage 的局部范围；
- 在已经满足真实前置条件时，从某个 Stage 的中间 Step 开始；
- 使用前序 Task Sheet 或其它已经形成的正式结果作为当前输入；
- 在当前 Task Sheet 的目标完成后结束，而不继续加入同一 Stage 或后续 Stage 的其它工作。

“更早编号的 Step 不在当前 Task Sheet”本身既不代表前置条件已经满足，也不代表必须把该 Step 机械复制进当前 Task Sheet。当前 Step 是否可以执行，只看其真实输入 / prerequisite contract 是否已经由当前 Task Sheet、前序 Task Sheet、正式结果或其它可追溯记录满足。

如果某个 Step 明确定义了必须先形成的上游方案、拆分结果或其它 prerequisite，那么该 prerequisite 必须在执行当前 Step 前存在并可定位；它可以记录在当前 Task Sheet，也可以记录在同一科研任务的前序 Task Sheet，不因为换了一张 Task Sheet 就失效或需要机械重做。

同样，不得因为当前 Task Sheet 没有包含某个后续 Step，就为“流程完整”自动补入与当前执行范围无关的工作。

## 执行范围确认

执行 Agent 必须区分：

```text
用户要执行什么
→ 执行范围

在已确认范围内具体怎样实现
→ scientific / technical execution detail
```

执行范围至少包括当前工作实际涉及的：

- Task Sheet / 当前任务项 / Step / capability；
- 需要处理的具体对象、source target、residue / component / trajectory 等对象集合与范围；
- 当存在多个候选对象时，是处理其中哪一个、哪些或全部；
- 用户是否要求把当前工作扩展到额外对象、额外 Step 或额外分析范围；
- 用户明确要求保留多个 alternative treatment / strategy 作为独立后续对象时，需要保留哪些分支。

执行范围可以由以下信息共同明确：

1. 用户当前明确指令；
2. 当前 Task Sheet 已经明确记录且仍有效的工作范围；
3. 当前科研任务中被当前 Task Sheet 明确引用、已经确认且仍适用的前序决定。

如果这些信息能够把当前执行范围唯一确定，直接使用，不为已经明确的范围重复询问。

如果用户当前指令本身不完整、含糊，且结合当前 Task Sheet / 明确前序决定后仍存在两个或以上**实质不同的执行范围**，必须先向用户确认，不得根据“更常见”“更合理”“离当前对象更近”“默认通常这样做”或 Agent 自己的科研偏好选择其中一个范围。

范围未确认前允许做只读核对，以便：

- 定位当前 Task Sheet 和候选对象；
- 列出可能的处理范围；
- 找出导致歧义的具体信息；
- 向用户提出清楚、尽量一次性的确认问题。

范围未确认前不得：

- 创建新的正式 target / target record；
- 修改当前 Task Sheet 的执行范围或状态；
- 修改结构、topology、trajectory、参数文件或其它科研对象；
- 启动依赖该范围决定的实质计算 / 模拟 / 分析；
- 选择并物化会排除其它合理范围的 strategy branch；
- 发布正式结果。

**身份 grounding 与执行范围决定不得混淆。** 如果用户已经明确了要处理的对象范围，只是省略了可以从正式结果唯一补足的 identity 信息，例如一个 residue 描述只能唯一映射到一个既有 `component_id + residue_id`，Agent 可以直接完成 grounding，不需要再次询问。反之，如果省略的信息会改变“处理哪些对象 / 处理多少对象 / 是否扩展范围”，即使 Agent 认为某个选择最合理，也必须先确认。

同样，执行范围确认不意味着所有技术细节都必须询问用户。范围明确后：

- current Skill 已定义科学 / 技术判据且现有 evidence 能唯一支持处理方式 → Agent 按 Skill 直接判断；
- 当前 Skill 允许 Agent 根据实际环境选择实现方式，且这些选择不改变已确认执行范围或科学含义 → Agent 自主处理；
- 只有剩余歧义会改变科学含义、结果解释或 current Skill 明确要求用户决定时，才再次向用户确认。

用户明确说“按当前 Task Sheet 执行”“继续当前已规划工作”等，且当前 Task Sheet 自身的对象和范围已经唯一闭合时，视为已确认当前范围；不得机械再次询问。如果 Task Sheet 中仍存在 placeholder、多个未区分候选对象或其它范围歧义，则仍须先确认。

用户最新明确指令如果与已有 Task Sheet 范围冲突，不静默选择其中一方。能够唯一理解为用户明确修改范围时按最新指令维护计划；仍有歧义时先确认，再改变 Task Sheet 或执行对象。

## 科研任务级科学上下文

用户已经明确给出的科学选择和科研任务级设置，在当前 Skill 真正需要时直接使用，并允许后续真正需要该信息的 Skill 再次核对。

例如力场、参数定义来源、pH、方法选择或其它会被多个环节消费的科研任务级信息：

1. 当前 Skill 先从当前 Task Sheet、相关前序 Task Sheet、已有正式项目记录、可追溯执行记录 / 日志、当前对话上下文和用户明确决定中确认实际采用值；
2. 已有信息能够唯一确定时直接使用，不重复询问；
3. 当前职责需要该信息而仍不能唯一确定时，由当前用户可见 Agent 向用户确认；
4. 后续 Skill 在自己真正需要该信息时可以再次核对，尤其当处理对象、执行范围或用户要求已经变化；
5. 不因为某个较早或较晚 Step 也会使用同一信息，就把“确认该信息”强制设为某一个 Step 的唯一触发点。

某个 Skill 仍可以拥有自己特有的参数来源整理、冲突检查、拆分方案或结果记录职责；这不等于它垄断某个科学选择第一次被确认的时点。

如果后续确认得到的新信息会使已经形成的上游拆分方案或其它 prerequisite 失效，不静默继续执行；先回到真正拥有该方案的 owner 更新或重新形成适用的前置结果。

## Canonical terminology

跨 Skill 需要保持一致的正式术语统一维护在：

`references/canonical_terminology.md`

Task Execution Agent 不需要每次执行都预读该文件；当用户表述、Task Sheet、上下游 Skill 或结果记录中的称呼可能导致 execution object、artifact、state 或科学判断对象混淆时，按需读取并以其中的 canonical terminology 解释当前对象。

用户的简称、口语和临时称呼只作为当前上下文输入，由 Agent 结合实际科研任务理解；不要为这些表达建立固定 alias 映射。正式 Task Sheet、报告和结果记录在涉及已登记的跨 Skill 概念时，采用该 reference 的 `Preferred expression`。

只属于单个 Stage / Step / capability 的局部术语仍由对应 Skill 定义；仓库级 terminology reference 不接管具体科学规则或局部命名。

## 用户可见沟通

真实项目科研执行中，执行智能体的确认问题、进度说明、异常说明、对象解释和结果摘要统一读取：

`references/user_communication_rules.md`

该 shared reference 对所有执行智能体的**用户可见沟通**生效，不只约束 authoring discussion。

核心边界：

- 用户沟通以规范中文技术表达为主体；普通技术概念可以准确用中文表达时，不无必要中英文混排；
- 软件、方法、力场、命令、选项、文件名、路径、字段名、enum、identifier 以及项目明确保留的 canonical term 按原文使用；
- 内部处理、mapping、结果关联继续使用稳定 `component_id + residue_id`，用户可见残基主称呼默认使用 1.2 正式结果保存的原始结构字段 `source_chain_id + source_resid + source_residue_name`；
- 当前结构中的 chain / resid / residue name 只有在解释当前文件状态确有价值时才作为补充，不替代原始结构残基标签作为默认主称呼；
- 原始标签不足以唯一定位时，先增加 model / source structure 等上下文，仍不足时再补内部 ID；
- 用户明确要求查看当前编号、最终结构编号或内部 ID 时按用户要求展示。

这只是用户可见展示规则，不改变内部稳定 identity、target lineage、atom mapping 或正式结果 schema。

科研执行进入当前对话 / 会话后，在第一次发送与真实项目执行有关的用户可见消息前读取该 reference；后续只要规则未变化且当前上下文仍保持，可以沿用，不要求每条消息重复读取。

## Target lineage

当前 Skill / 当前工作项如果使用 `target` 作为 execution object，必须读取：

`references/target_lineage_rules.md`

并按其中规则为每个 local target 建立当前 target record。

核心语义：

```text
local target_id
→ 只在当前 Skill / 当前工作项内解释

current target_record
→ 当前 local target 的跨 Skill 正式引用路径

source_target_records
→ 当前 target 的直接上游 target records
```

一个 source target 产生多个 current targets 时形成分支；多个 source targets 共同形成一个 current target 时形成合流。不得把 target lineage 固定解释成从 1.3 开始的单链，也不得通过 `target_id` 编号相同推断上下游对象关系。

当前 Task Sheet 新建、工作目录变化、普通文件复制或局部 target 重新编号本身不构成 target lineage 关系。source target 必须是实际参与当前 execution object 形成的上游 target。

Stage 4 formal run unit、Stage 5 analysis plan item 等已经由对应 owner 定义其它 execution identity、且 current Skill 并未使用 `target` 的对象，不因为全局统一而强制建立 target record。

Target record 只在当前执行范围已经明确后建立。不能为了“先占位”而在范围仍有用户意图歧义时创建多个候选 target records。

## Task execution loop

科研执行入口先完成 Task Sheet resolution，再由 Task Execution Agent 持有已绑定的当前 Task Sheet 并按当前实际对象推进。

普通入口与执行主线：

```text
收到真实项目科研执行指令
→ Task Sheet resolution
  ├─ 已有唯一相关未完成 Task Sheet → 自动绑定
  ├─ 多个相关未完成 Task Sheet → 用户确认
  └─ 无相关未完成 Task Sheet → Manager 创建新 Task Sheet
→ 读取已绑定 Task Sheet
→ 确定当前任务项
→ 读取当前需要的 Stage / Step / capability Skill
→ 结合用户当前指令 + 当前 Task Sheet + 明确前序决定解析执行范围
  ├─ 范围有歧义 → 只读核对 → 向用户确认 → 回到范围解析
  └─ 范围唯一明确 → 继续
→ 确定当前实际对象
→ 当前对象为 target 时建立 / 定位 current target_record 与 source_target_records
→ 定位当前 Step 明确要求的 prerequisite / 上游正式输入
→ 按当前 Skill / Stage 规则判断 reuse
→ 按需读取实际对象、候选结果、reference / supporting Skill / Tool guide
→ 需要时执行
→ 按结果 owner 的规则 validation
→ 更新 Task Sheet 当前项
→ 登记正式结果
→ 根据实际结果或用户要求维护尚未完成的后续计划
→ 继续下一任务项
```

普通子环节之间不返回 Manager 调度。以下情况才重新进入 Manager：

- 用户明确要求 Manager 重新规划；
- 当前科研执行入口尚未解决 Task Sheet；
- 当前绑定 Task Sheet 已完成 / 已终止 / 不再适用于当前执行指令；
- 当前执行确实需要建立新的后续 Task Sheet。

如果计划中的 Stage / Step 只有 architecture freeze、尚无获批生成的 current execution Skill，不得把 freeze 当作执行指南自行运行。

## Dynamic Task Sheet maintenance

Task Sheet 是可动态维护的执行计划，不是不可变 route。

Task Execution Agent 可以根据实际结果或用户要求维护尚未完成的后续计划。这里规定的是**计划能够被更新这一通用机制**。

如果当前 Stage 存在真正拥有 Stage-wide orchestration 的 main Skill，则按该 Stage main Skill 维护其专属 plan adjustment / shared Stage object 规则。

如果当前 Stage 不设置 Stage main Skill，则不为跨 Step 推进额外制造 synthetic Stage owner。Task Execution Agent 根据当前 Task Sheet、当前 Step 的正式结果 / input contract、明确 prerequisite、用户要求和实际执行证据维护尚未完成的后续计划；各 Step 仍只定义自己的科学职责和输入输出接口。

已经实际执行并形成有意义执行历史的内容不得为了整理计划而静默删除。

执行范围尚未确认时，不把 Agent 自己的范围推断写入 Task Sheet 当作既成计划。只有用户范围已经明确，或用户明确授权按当前 Task Sheet 的既有范围执行时，才据实际结果维护尚未完成计划。

## Manager boundary

Manager current entry：

```text
00_manager/SKILL.md
```

Manager 负责 Task Sheet 定位 / 创建、初始规划、用户明确要求时的重新规划，以及项目级 Task Sheet 导航整理。**科研执行入口没有已解析 Task Sheet 时，Task Sheet resolution 也自动进入 Manager 的定位 / 创建职责，不要求用户显式点名 Manager。**

一个更大的科研任务是否继续使用原 Task Sheet 或拆成新的 Task Sheet，属于 Task Sheet 管理决策，不改变对应 scientific Skill 的科学职责。

科研执行阶段由当前 scientific Skill 推进；Manager 不执行具体科研 Step，也不替当前结果 owner 判断具体 Step 的 reuse、scientific applicability、validation 或结果正确性。

## Directory model

普通 Step 的 task-specific 工作目录采用：

```text
<base_work_directory>/<task_id>/
```

这里保留既有接口字段名 `task_id`；其值当前对应 `Txxxx` Task Sheet 标识，不应因此把一张 Task Sheet 等同于整个科研任务。

Manager 可以在 Task Sheet 中记录未来路径，但不提前创建 task-specific directory。

真正进入当前工作时：

```text
先完成 Task Sheet resolution
→ 再确认当前执行范围
→ 再按当前 Skill 的 reuse 规则判断
   ├─ 可直接复用 → 不创建无用空目录
   └─ 需要本地执行 → 创建当前 task-specific directory
```

Stage-specific directory / index 组织以实际拥有该职责的 current Stage / Step / capability owner 为准。

如果当前 Skill 使用 target，实际执行目录建立后按 `references/target_lineage_rules.md` 在当前 task-specific directory 内维护 `targets/<target_id>.yaml`。

## Reuse

除当前 Skill 明确采用其它规则外，普通工作在真正开始时按以下默认语义判断 reuse：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前用户可见 Agent 向用户确认
用户明确要求重做 / 对照 → 跳过自动复用
```

Reuse assessment 发生在 Task Sheet resolution 与当前执行范围都已经明确之后。不得用“发现了一个可复用结果”反向替用户决定当前究竟要处理哪个对象或范围，也不得用 reuse 结果绕过 Task Sheet resolution。

不得仅根据目录存在、文件名相同或 Task Sheet 名称相似自动复用。

跨 Task Sheet 或跨科研任务复用已有正式结果时直接引用原结果，不为了当前 Task Sheet 复制无意义副本。

如果某个 Skill 明确不设置 reuse，或某 Stage 定义了不同的 reuse 组织方式，以该 current Skill / Stage Skill 为准。

复用已有结果不把当前 local target 与旧结果中的 local `target_id` 合并成同一 target；如果当前工作项仍使用 target，应按 target-lineage 规则建立当前 target record，并把实际复用的上游 target record 作为 source target 之一。

## Validation and results

Validation、正式结果生成、结果路径与结果内部 `references`、Markdown `References`、结果接口说明以及 `project_result_index.md` 登记的通用规则统一读取：

`references/result_generation_rules.md`

进入当前科研 Skill 的 validation、正式结果生成、结果解释或 project-result registration 时按需读取该 shared reference。

各科研执行 Skill 继续拥有自身的正式结果集合、具体字段语义、Skill-specific validation requirement 和 project-result registration 白名单；`result_generation_rules.md` 只拥有科研执行 Skill 共用的结果生成与记录机制。

## Minimal reads

真实科研执行按需读取。

Task Execution Agent 不默认：

- 预读全部未来 Steps；
- 扫描所有 Task Sheets；
- 重读上游全过程；
- 加载 Legacy route / state / event / runtime records；
- 为了寻找潜在 reuse 而无边界遍历项目。

Task Sheet resolution 允许先读取 `task_index.md`，并在索引不足以判断时读取用户明确指定或少数合理的 `未完成` candidates；这属于受限入口解析，不等于扫描全部 Task Sheets。

当前 Step 明确依赖某张前序 Task Sheet 或某个 prerequisite 时，可以直接读取该相关记录；这不等于扫描全部历史 Task Sheets。

为了确认执行范围，可以对当前 Task Sheet、被明确引用的前序 Task Sheet以及当前候选对象做最小必要的只读检查；不得把“范围确认”当作理由无边界扫描项目。

需要理解当前接口时，可以读取直接相关的外部 Skill；读取不改变其内容 owner。

用户可见沟通属于执行期必要共享规则。首次需要向用户发送执行相关确认、进度、异常或结果摘要时读取 `references/user_communication_rules.md`；这不要求为每个科研 Step 重复加载，也不授权读取与当前对象无关的项目文件。

## Stage / Step ownership boundary

职责关系为：

```text
00_manager/SKILL.md
→ Task Sheet resolution / creation / initial planning / explicit replanning

references/task_execution_rules.md
→ 科研执行 Skill 共用的 Task Execution 规则与科研执行入口 gate

references/user_communication_rules.md
→ 执行智能体用户可见沟通、中文技术表达与内部 residue identity → 原始结构残基标签的展示规则

references/target_lineage_rules.md
→ 使用 target 的科研执行 Skill 共用的 local target / target record / lineage 机制

references/result_generation_rules.md
→ 科研执行 Skill 共用的 validation / result generation / result-recording 机制

Stage main Skill（仅在存在且确有 Stage-wide 职责时）
→ Stage-specific orchestration / plan adjustment / shared Stage objects

Step / capability Skill
→ 具体科研处理、判断、Skill-specific prerequisite、validation 与 results

没有 Stage main Skill 的 Stage
→ Task Execution Agent 依据 Task Sheet + current Step interfaces 推进
→ 不为架构对称额外创建 Stage dispatcher
```

共享规则被多个 Skill 引用不改变具体科学规则的 owner，也不意味着必须为 Task Execution 新建独立 Skill 或 dispatcher。

## Legacy rule

Legacy Runtime 可以保留用于 Git history、旧项目迁移、明确调试或历史审计，但：

- 新项目不默认生成 Legacy records；
- current execution 不双写旧 records；
- 新 Skill 不为普通运行增加 Legacy compatibility layer；
- archived / Legacy 文件不能推翻 current Skill 或本 shared reference。
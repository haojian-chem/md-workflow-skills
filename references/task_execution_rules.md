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

- `未完成`：当前 Task Sheet 仍保留该任务项，且其当前职责尚未闭合；
- `已完成`：当前 Task Sheet 中的该任务项已经按其 current Skill 完成；
- `已终止`：该任务项已经进入执行历史，但当前 Task Sheet 不再继续执行它；必须能够追溯终止原因。具体何种情形可终止，由当前 Skill、Stage-specific 规则或当前执行情况决定。

Stage-specific 内部对象如有不同状态模型，以对应 current owner 为准。

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

## Task execution loop

Task Execution Agent 持续持有当前 Task Sheet，并按当前实际对象推进。

普通执行主线：

```text
读取目标 Task Sheet
→ 确定当前任务项 / 对象
→ 读取当前需要的 Stage / Step / capability Skill
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

普通子环节之间不返回 Manager 调度。只有用户明确要求 Manager 重新规划或需要建立新的 Task Sheet 时，才重新进入 Manager 的对应职责。

如果计划中的 Stage / Step 只有 architecture freeze、尚无获批生成的 current execution Skill，不得把 freeze 当作执行指南自行运行。

## Dynamic Task Sheet maintenance

Task Sheet 是可动态维护的执行计划，不是不可变 route。

Task Execution Agent 可以根据实际结果或用户要求维护尚未完成的后续计划。这里规定的是**计划能够被更新这一通用机制**。

如果当前 Stage 存在真正拥有 Stage-wide orchestration 的 main Skill，则按该 Stage main Skill 维护其专属 plan adjustment / shared Stage object 规则。

如果当前 Stage 不设置 Stage main Skill，则不为跨 Step 推进额外制造 synthetic Stage owner。Task Execution Agent 根据当前 Task Sheet、当前 Step 的正式结果 / input contract、明确 prerequisite、用户要求和实际执行证据维护尚未完成的后续计划；各 Step 仍只定义自己的科学职责和输入输出接口。

已经实际执行并形成有意义执行历史的内容不得为了整理计划而静默删除。

## Manager boundary

Manager current entry：

```text
00_manager/SKILL.md
```

Manager 负责 Task Sheet 定位 / 创建、初始规划、用户明确要求时的重新规划，以及项目级 Task Sheet 导航整理。一个更大的科研任务是否继续使用原 Task Sheet 或拆成新的 Task Sheet，属于 Task Sheet 管理决策，不改变对应 scientific Skill 的科学职责。

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
先按当前 Skill 的 reuse 规则判断
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

当前 Step 明确依赖某张前序 Task Sheet 或某个 prerequisite 时，可以直接读取该相关记录；这不等于扫描全部历史 Task Sheets。

需要理解当前接口时，可以读取直接相关的外部 Skill；读取不改变其内容 owner。

## Stage / Step ownership boundary

职责关系为：

```text
references/task_execution_rules.md
→ 科研执行 Skill 共用的 Task Execution 规则

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

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

- `task_index.md`：任务导航和任务级状态；
- `tasks/Txxxx.md`：任务目标、动态计划、进度和最小恢复上下文；
- `project_result_index.md`：跨任务 / 跨对话的正式结果检索入口，不保存当前任务状态。

任务级状态：

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

- `未完成`：当前任务仍保留该任务项，且其当前职责尚未闭合；
- `已完成`：当前任务中的该任务项已经按其 current Skill 完成；
- `已终止`：该任务项已经进入任务历史，但当前任务不再继续执行它；必须能够追溯终止原因。具体何种情形可终止，由当前 Skill、Stage-specific 规则或实际任务决定。

Stage-specific 内部对象如有不同状态模型，以对应 current owner 为准。

## Task scope

一个 Task Sheet 只覆盖用户当前任务实际需要的工作范围，不要求包含完整 MD Workflow、完整 Stage，或某个 Stage 从第一项到最后一项的全部 Step。

因此 Task Sheet 可以：

- 只包含一个 Stage 的局部范围；
- 从某个 Stage 的中间 Step 开始；
- 使用其它任务已经形成的正式结果作为当前输入；
- 在当前任务目标完成后结束，而不继续加入同一 Stage 或后续 Stage 的其它工作。

当前 Skill 只要求其自身真实输入契约得到满足，不因为编号上存在更早 Step 就要求这些 Step 必须出现在同一 Task Sheet。已有正式结果、当前项目记录、当前对话上下文或用户明确提供的信息能够满足当前输入时，可以直接使用。

同样，不得因为 Task Sheet 没有包含某个后续 Step，就为“流程完整”自动补入与当前任务目标无关的工作。

## User decisions and task-level scientific context

用户已经明确给出的科学选择和任务级设置，应尽早被当前需要它们的 Skill 使用，并在后续真正需要时允许再次核对。

例如力场、参数定义来源、pH、方法选择或其它会被多个环节消费的任务级信息：

1. 当前 Skill 先从当前 Task Sheet、已有正式项目记录、可追溯执行记录 / 日志、当前对话上下文和用户明确决定中确认实际采用值；
2. 已有信息能够唯一确定时直接使用，不重复询问；
3. 当前职责需要该信息而仍不能唯一确定时，由当前用户可见 Agent 向用户确认；
4. 后续 Skill 在自己真正需要该信息时可以再次核对，尤其当任务范围、体系对象或用户要求已经变化；
5. 不因为某个较早或较晚 Step 也会使用同一信息，就把“确认该信息”强制设为某一个 Step 的唯一入口。

某个 Skill 仍可以拥有自己特有的参数来源整理、冲突检查或结果记录职责；这不等于它垄断该科学选择第一次被确认的时点。

## Canonical terminology

跨 Skill 需要保持一致的正式术语统一维护在：

`references/canonical_terminology.md`

Task Execution Agent 不需要每次执行都预读该文件；当用户表述、Task Sheet、上下游 Skill 或结果记录中的称呼可能导致 execution object、artifact、state 或科学判断对象混淆时，按需读取并以其中的 canonical terminology 解释当前对象。

用户的简称、口语和临时称呼只作为当前上下文输入，由 Agent 结合实际任务理解；不要为这些表达建立固定 alias 映射。正式 Task Sheet、报告和结果记录在涉及已登记的跨 Skill 概念时，采用该 reference 的 `Preferred expression`。

只属于单个 Stage / Step / capability 的局部术语仍由对应 Skill 定义；仓库级 terminology reference 不接管具体科学规则或局部命名。

## Task execution loop

Task Execution Agent 持续持有一个 Task Sheet，并按当前实际对象推进。

普通执行主线：

```text
读取目标 Task Sheet
→ 确定当前任务项 / 对象
→ 读取当前需要的 Stage / Step / capability Skill
→ 按当前 Skill / Stage 规则判断 reuse
→ 按需读取实际对象、候选结果、reference / supporting Skill / Tool guide
→ 需要时执行
→ 按结果 owner 的规则 validation
→ 更新 Task Sheet 当前项
→ 登记正式结果
→ 根据实际结果或用户要求维护尚未完成的后续计划
→ 继续下一任务项
```

普通子环节之间不返回 Manager 调度。只有用户明确要求 Manager 重新规划时，才重新进入 Manager 的 explicit replanning 职责。

如果计划中的 Stage / Step 只有 architecture freeze、尚无获批生成的 current execution Skill，不得把 freeze 当作执行指南自行运行。

## Dynamic Task Sheet maintenance

Task Sheet 是可动态维护的计划，不是不可变 route。

Task Execution Agent 可以根据实际结果或用户要求维护尚未完成的后续计划。这里规定的是**计划能够被更新这一通用机制**。

如果当前 Stage 存在真正拥有 Stage-wide orchestration 的 main Skill，则按该 Stage main Skill 维护其专属 plan adjustment / shared Stage object 规则。

如果当前 Stage 不设置 Stage main Skill，则不为跨 Step 推进额外制造 synthetic Stage owner。Task Execution Agent 根据当前 Task Sheet、当前 Step 的正式结果 / input contract、用户要求和实际执行证据维护尚未完成的后续计划；各 Step 仍只定义自己的科学职责和输入输出接口。

已经实际执行并形成有意义任务历史的内容不得为了整理计划而静默删除。

## Manager boundary

Manager current entry：

```text
00_manager/SKILL.md
```

Manager 负责任务定位 / 创建、初始 Task Sheet planning、用户明确要求时的重新规划和项目级任务导航整理。

科研执行阶段由当前 scientific Skill 推进；Manager 不执行具体科研 Step，也不替当前结果 owner 判断具体 Step 的 reuse、scientific applicability、validation 或结果正确性。

## Directory model

普通 Step 的 task-specific 工作目录采用：

```text
<base_work_directory>/<task_id>/
```

Manager 可以在 Task Sheet 中记录未来路径，但不提前创建 task-specific directory。

真正进入当前工作时：

```text
先按当前 Skill 的 reuse 规则判断
├─ 可直接复用 → 不创建无用空目录
└─ 需要本地执行 → 创建当前 task-specific directory
```

Stage-specific directory / index 组织以实际拥有该职责的 current Stage / Step / capability owner 为准。

## Reuse

除当前 Skill 明确采用其它规则外，普通工作在真正开始时按以下默认语义判断 reuse：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前用户可见 Agent 向用户确认
用户明确要求重做 / 对照 → 跳过自动复用
```

不得仅根据目录存在、文件名相同或任务名称相似自动复用。

跨任务复用已有正式结果时直接引用原结果，不为了当前任务复制无意义副本。

如果某个 Skill 明确不设置 reuse，或某 Stage 定义了不同的 reuse 组织方式，以该 current Skill / Stage Skill 为准。

## Validation and results

Validation、正式结果生成、结果路径与结果内部 `references`、Markdown `References`、结果接口说明以及 `project_result_index.md` 登记的通用规则统一读取：

`references/result_generation_rules.md`

进入当前科研 Skill 的 validation、正式结果生成、结果解释或 project-result registration 时按需读取该 shared reference。

各科研执行 Skill 继续拥有自身的正式结果集合、具体字段语义、Skill-specific validation requirement 和 project-result registration 白名单；`result_generation_rules.md` 只拥有科研执行 Skill 共用的结果生成与记录机制。

## Minimal reads

真实科研执行按需读取。

Task Execution Agent 不默认：

- 预读全部未来 Steps；
- 扫描所有任务；
- 重读上游全过程；
- 加载 Legacy route / state / event / runtime records；
- 为了寻找潜在 reuse 而无边界遍历项目。

需要理解当前接口时，可以读取直接相关的外部 Skill；读取不改变其内容 owner。

## Stage / Step ownership boundary

职责关系为：

```text
references/task_execution_rules.md
→ 科研执行 Skill 共用的 Task Execution 规则

references/result_generation_rules.md
→ 科研执行 Skill 共用的 validation / result generation / result-recording 机制

Stage main Skill（仅在存在且确有 Stage-wide 职责时）
→ Stage-specific orchestration / plan adjustment / shared Stage objects

Step / capability Skill
→ 具体科研处理、判断、Skill-specific validation 与 results

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

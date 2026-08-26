# Task execution rules

Status: CURRENT SHARED REFERENCE

本文件定义真实 MD 项目中，各科研执行 Skill 共同遵守的跨 Stage Task Execution 规则。

它是仓库级 shared reference，**不是独立 Skill、不是额外 runtime 环节，也不改变 Scientific Stage 编号**。科研执行仍由当前 Stage / Step / capability `SKILL.md` 直接指导；各 active execution Skill 必须显式引用本文件。`00_authoring/SKILL.md` 也必须引用本文件，以保证后续 Skill 构筑与这些通用执行规则兼容。

Stage-specific 的科学规则、计划调整方式、execution object、validation 和 results 继续由对应 Stage / Step / capability Skill 拥有。本文件只定义跨 Skill 共用的执行机制，不创建第二套科学决策规则。

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

普通 Task Sheet 子环节状态默认：

```text
待执行
未完成
已完成
```

Stage-specific 内部对象如有不同状态模型，以对应 current Stage Skill 为准。

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

某个 Stage 内应当如何根据具体科研结果增加、删除、替换、重排或重新进入后续环节，以及某类 failure 应返回哪个真正拥有问题的上游 owner，属于 Stage-specific orchestration；如果对应 Stage main Skill定义了这些关系，则按该 Stage main Skill执行，本文件不复制或改写这些科学调整规则。

已经实际执行并形成有意义任务历史的内容不得为了整理计划而静默删除。

## Manager boundary

Manager current entry：

```text
00_manager/SKILL.md
```

Manager 负责任务定位 / 创建、初始 Task Sheet planning、用户明确要求时的重新规划和项目级任务导航整理。

科研执行阶段由当前 scientific Skill推进；Manager 不执行具体科研 Step，也不替当前结果 owner 判断具体 Step 的 reuse、scientific applicability、validation 或结果正确性。

## Directory model

普通 Step 的 task-specific 工作目录采用：

```text
<base_work_directory>/<task_id>/
```

Manager 可以在 Task Sheet 中记录未来路径，但不提前创建 task-specific directory。

真正进入当前工作时：

```text
先检查 reuse
├─ 可直接复用 → 不创建无用空目录
└─ 需要本地执行 → 创建当前 task-specific directory
```

Stage-specific directory / index 组织以对应 current Stage Skill 为准。

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

Validation 默认跟随当前结果 owner：

```text
谁产生 / 判定结果
→ 谁拥有该结果的 validation requirement
```

Tool 可以负责自己确定性输出的机械 / 格式有效性；科研 Skill 仍负责判断该输出是否满足当前科研目标。

`project_result_index.md` 只登记当前 Skill / Stage 明确允许登记的正式结果或结果事项，不登记 debug、scratch、cache 或为了“完整”而产生的重复文件索引。

Skill-specific project-result whitelist、结果文件语义和 validation 条件由对应结果 owner 定义；本文件不建立统一结果 schema。

正式结果记录中的结果文件路径必须保持完整绝对路径语义。

`references` 可同时定义当前记录实际依赖的文件，以及供多个字段复用的公共绝对路径引用。若多个结果文件共享相同目录前缀，可在 `references` 中定义该公共绝对路径，并在结果字段中使用 `${PATH_KEY}/filename` 形式引用；展开后的结果仍必须是完整绝对路径。

由当前环节产生的结果文件仍记录在对应结果 owner 定义的结果字段中；`references` 中的公共路径引用只用于路径复用，不能替代结果字段对当前环节产物的记录。

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
→ 跨 Stage 通用 Task Execution 规则

Stage main Skill（存在且确有 Stage-wide 职责时）
→ Stage-specific orchestration / plan adjustment / shared Stage objects

Step / capability Skill
→ 具体科研处理、判断、validation 与 results
```

共享规则被多个 Skill引用不改变具体科学规则的 owner，也不意味着必须为 Task Execution 新建独立 Skill 或 dispatcher。

## Legacy rule

Legacy Runtime 可以保留用于 Git history、旧项目迁移、明确调试或历史审计，但：

- 新项目不默认生成 Legacy records；
- current execution 不双写旧 records；
- 新 Skill 不为普通运行增加 Legacy compatibility layer；
- archived / Legacy 文件不能推翻 current Skill 或本 shared reference。

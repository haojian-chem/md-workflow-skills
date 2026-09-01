---
name: md-analysis
description: Stage 5 Analysis 总 Skill。用于把 Task Sheet 中的 `5 Analysis` 目标展开为 capability-based analysis plan，完成 Stage 5 reuse、依赖与工作目录组织、plan-item 状态维护和正式结果登记；具体分析方法、输出 validation 与可登记文件由对应 capability owner 负责。
---

# 5 Analysis

通用 Task Execution 规则读取：

`../references/task_execution_rules.md`

本 Skill 只在此基础上定义 Stage 5-specific 的 analysis planning、plan-item maintenance、reuse orchestration 与 capability 调度规则。

## Purpose

本 Skill 是 Stage 5 的 main runtime entry。

Stage 5 不设置编号化 sub-stage，也不建立 `5.1 Analysis planning and orchestration`。本 Skill 直接读取当前 Task Sheet 中的 `5 Analysis` 条目，并负责：

- 理解当前分析目标、对象、约束和用户明确指定的方法；
- 发现当前已登记 analysis capabilities；
- 集中检查可复用的正式分析结果和 prepared inputs；
- 将可由已登记 capabilities 覆盖的需求展开为当前 Stage 5 plan items；
- 维护 plan-item 编号、依赖、状态、工作目录和关键结果入口；
- 调度对应 capability entry，并在 capability owner validation 后更新当前 plan；
- 按 capability owner 声明登记允许进入项目级结果索引的正式结果。

具体分析方法、命令、selection/preprocessing 细节、输出语义、validation，以及哪些文件可登记到 `project_result_index.md`，由对应 capability owner 的 Skill / README 拥有。本 Skill 不复制这些规则。

## Required context

开始 Stage 5 时读取：

- 当前 Task Sheet 的 `5 Analysis` 条目；
- `references/analysis_capability_inventory.yaml`；
- `<project_root>/00_project_records/project_result_index.md`；
- 当前分析实际需要的 Stage 4 / 上游结果与科研文件；
- 当 processed trajectory reuse 可能相关时，读取 `<project_root>/05_analysis/indexes/trajectory_index.yaml`（若存在）。

当前 Task Sheet 可以只承载同一科研任务的一部分分析工作。前序 Task Sheet 已完成的分析、轨迹处理或 prepared inputs 不需要复制成当前 plan items；当前分析直接通过正式结果、项目结果索引、trajectory index 或明确的前序 Task Sheet 引用消费这些已有产物。

只在某 capability 可能进入当前 plan 时读取其 `entry`。Inventory 只做 capability discovery 和初步输入匹配，不能替代 capability entry。

## Capability discovery and boundary

Inventory 中只有具有真实可引用 `entry` 的 capability 才是当前可调度能力。

凡某 capability 准备进入最终 plan，必须先读取其 `entry`，据此确定当前 item 的：

- required inputs；
- capability-specific settings；
- selection / reference / preprocessing 要求；
- dependencies；
- validation 与正式输出语义；
- project-level result registration whitelist（若该 capability 有正式结果需要登记）。

如果当前分析需求没有合适的已登记 capability：

- 不创建虚构 capability；
- 不创建虚构 inventory entry；
- 不在 Stage 5 plan items 区域中创建代表该缺失能力的伪 item；
- 未覆盖需求 / capability gap 可以继续保留在 Task Sheet 中，但位于 Stage 5 plan items 区域之外。

缺失 capability 的方法设计、实现和 validation 不属于本 Skill。其 Task Sheet 表达与后续处理方式由当前 Task Execution Agent / 用户结合当前执行范围决定。

## One-pass planning

进入当前 Task Sheet 的 Stage 5 范围时，集中完成一次当前资源查询、reuse 核验和整体规划：

```text
read current Task Sheet Stage 5 requirement
→ read capability inventory
→ query existing formal analysis results
→ query trajectory_index.yaml when relevant
→ determine reusable results / prepared inputs
→ determine missing required inputs
→ identify required registered producer capabilities
→ read each selected capability entry
→ finalize inputs / settings / dependencies
→ write the complete current Stage 5 plan items into current Task Sheet
→ execute the plan
```

这里的“完整 plan”只指当前 Task Sheet 的 Stage 5 执行范围，不要求把同一科研任务在其它 Task Sheet 中已经完成或未来才需要的全部分析工作复制进当前 Task Sheet。

正常执行中不为每个 item 重复一次全局 reuse scan。

如果前置失败、实际产物不满足原计划前提、用户修改需求或其它证据使当前 plan 失效，可以调整尚未完成的后续计划。是否修改既有 item、终止后新增 item 或采用其它处理方式，由当前 Agent / 用户根据当前 Task Sheet 的实际执行范围决定；本 Skill 只要求历史编号、终止原因和有效依赖保持可追溯。

## Plan item model

Stage 5 plan items 位于当前 Task Sheet 的 `5 Analysis` 条目内部，使用局部整数编号：

```text
1, 2, 3, ...
```

已有编号不重排；不再执行的既有 item 使用 `已终止`，新增 item 使用下一个整数编号。

允许状态：

```text
未完成
已完成
已终止
```

新加入当前 plan、尚未完成或终止的 item 默认记为 `未完成`。不再建立统一 `待执行 / 执行中 / 失败` 等额外状态。

普通 plan item 至少记录：

```text
编号
capability
inputs
settings
status
path
```

完成或终止时按实际情况增加：

```text
results
reason
```

其中 `status: 已终止` 时必须记录 `reason`。

### Field semantics

`capability`
: 当前 inventory 中的实际条目名。

`inputs`
: 当前 plan item 所要求或对应的输入。已有文件使用完整路径。实际执行时对应当前执行真正消费的输入；direct reuse 时仍记录**当前需求**所对应的输入，用于与候选既有结果比较。

`settings`
: 当前 item 的 capability-specific 分析设置，不建立 Stage 5 通用 `range / dt / target` 子 schema。实际执行时对应当前执行设置；direct reuse 时仍记录**当前需求**要求的设置，用于 reuse 等价性判断。

`status`
: `未完成 / 已完成 / 已终止`。

`path`
: 当前 Task Sheet 实际执行该 item 时的完整工作/文件目录。direct reuse 且当前 Task Sheet 不执行该 item 时可省略，不使用旧结果目录冒充当前 item 工作目录。

`results`
: 已确认有效、值得直接定位或供后续 item 消费的关键正式结果/产物入口。它不是工作目录文件清单。direct reuse 时可指向被复用的既有正式结果。

`reason`
: item 终止原因。direct reuse 时说明已有正式结果为何足以满足当前 item，并注明可追溯来源。

如果某输入由当前 plan 的前置 item 产生，可以直接使用可读依赖描述，例如：

```text
trajectory: 使用第 1 项生成的处理后轨迹
index: 使用第 2 项生成的 ndx 文件
```

不要求额外的 `from_item` / `output_role` schema。

## Task Sheet 工作目录

Stage 5 不建立 Stage 4 式 project-level run-unit identity 或 `run_unit.yaml`。

每个实际执行 Stage 5 的 Task Sheet 使用自己的 analysis 工作目录：

```text
<project_root>/05_analysis/<task_id>/
```

这里的 `<task_id>` 是当前 Task Sheet 的 `Txxxx` 标识。

实际执行的 plan item 默认目录：

```text
<project_root>/05_analysis/<task_id>/<编号>.<capability名>/
```

例如：

```text
05_analysis/T001/1.rmsd/
05_analysis/T001/2.rdf/
```

该目录作为普通实际执行 item 的默认 `path`。direct reuse 不创建无用 item 目录。

如果 capability 有额外集中管理产物，其存放和登记规则由 capability owner 定义。`trjconv` 与 `trjcat` 产生的正式 trajectory 共享额外的集中管理和 `trajectory_index.yaml` 登记接口；两者各自维护自己生成并通过 validation 的 trajectory 记录。本 Skill 只消费该接口，不定义其文件生命周期。

## Multiple trajectories / grouped analyses

一个 plan item 对应一次统一定义的分析。

多条 trajectory 可以放在同一 item 中，当且仅当它们属于同一次分析并共享关键 settings。若用户要求分别分析，或不同输入需要不同关键 settings，则拆成多个 plan items。

最终 `inputs` 使用解析后的实际文件路径；`md.N` 等逻辑对象只能作为查找实际文件的线索，不能替代最终输入路径。

## Existing formal-result reuse

从 `project_result_index.md` 发现候选正式结果后，至少核验：

1. analysis goal / result semantics；
2. object / selection；
3. source data 与分析范围；
4. capability / method；
5. 会改变结果语义的关键 settings；
6. validation / result completeness。

具体哪些 settings 会改变结果语义，由对应 capability owner 定义。

复用模式：

```text
direct reuse
→ 既有正式结果本身完整满足当前 item

reuse as input
→ 既有结果作为新的 plan item 输入，避免重复前置分析

rerun
→ 既有结果不能可靠满足当前需求，重新执行 capability
```

### Direct reuse

当前 plan 仍保留对应 item，并记录：

```text
capability
inputs       # 当前需求
settings     # 当前需求
status: 已终止
results      # 被复用且已 validation 的既有正式结果
reason       # 说明 direct reuse 与来源
```

当前 Task Sheet 不执行该 item 时 `path` 可省略。

Direct reuse item 不标记 `已完成`，因为当前 Task Sheet 没有执行该分析。候选旧结果自己的 inputs/settings 从其原 Task Sheet / result record 追溯，与当前 item 比较。

### Reuse as input

不为“复用动作”单独增加 item。新的实际处理 item 直接在 `inputs` 中引用既有结果。

如果候选信息不足，先追溯其 Task Sheet / Stage 5 item / results / 实际文件；仍无法确认时，不自动判为 direct reuse。

## Processed trajectory reuse

当分析需要 processed trajectory 且项目存在：

```text
<project_root>/05_analysis/indexes/trajectory_index.yaml
```

先用该索引做候选发现和初筛。索引只承担轻量检索，不要求保存完整 trajectory processing metadata；初筛可优先使用其中直接提供的 source lineage、output selection、`dt` 等信息。

候选缩小后，再沿对应 `producer_path` 读取 producer item / execution record，并在需要时检查实际文件，进一步核验与当前 consuming capability 相关的信息，例如：

1. source system / atom-order reference；
2. atom set / output selection；
3. PBC handling；
4. center / fit / orientation；
5. time range；
6. time sampling / frame spacing。

是否最终兼容由 consuming capability 的实际要求决定；本 Skill 不建立一套独立的普适 preprocessing 等价规则。

`trajectory_index.yaml` 是 `trjconv` 与 `trjcat` 共用的集中 trajectory 索引。两者拥有同等维护职责，各自只登记或更新自己生成并通过 validation、且满足自身登记条件的 trajectory；集中存放、可登记文件、命名和详细登记规则由对应 producer capability owner 定义。

## 外部 `.ndx`

Stage 5 不建立 project-level `ndx_index.yaml`，也不做跨 Task Sheet `.ndx` 自动复用扫描。

判断当前分析是否需要额外 `.ndx` 时，读取 consuming capability 的 entry：

```text
capability 所需 selections / groups
→ 当前输入 + capability 原生 selection/default groups 能直接满足？
   ├─ 能 → 不预生成外部 .ndx
   └─ 不能，且 capability 明确要求 external index
      → 在当前 plan 中使用已登记的 index-generation capability
```

当前 Task Sheet 中前置 item 生成且满足后续需求的 `.ndx` 可以通过显式依赖共享。

同一科研任务的前序 Task Sheet 已明确生成、仍可定位的 `.ndx` 也可以作为当前 item 的候选 prepared input；不因为换了一张 Task Sheet 就要求重新生成。当前 Task Sheet 必须通过完整路径或明确的前序 Task Sheet / plan item 来源定位该文件，并由 consuming capability 核验其中所需 group 与当前分析输入的结构 / 原子顺序是否兼容。

用户另外提供的 `.ndx` 同样可以作为候选输入；是否包含所需 group、是否与当前分析输入兼容，由对应 consuming capability 核验。

## Capability execution and validation

对每个需要实际执行的 plan item：

1. 读取对应 capability `entry`；
2. 确认当前 `inputs / settings / dependencies` 满足其接口；
3. 在当前 item `path` 下执行或按 owner 的集中产物规则执行；
4. 由 capability owner 完成其结果 validation；
5. validation 通过后，当前 item 才可标记 `已完成`；
6. 将需要直接恢复或供后续 item 消费的关键有效产物写入 `results`；
7. 按 capability owner 声明处理 project-level result registration。

本 Skill 只核验 orchestration 一致性，不重新做具体 capability 的科学 validation。

后续 item 不得依赖没有产生或引用有效所需输入的已终止前置项。若已终止项属于 direct reuse 且 `results` 明确指向有效正式结果，则该结果可以被后续 item 使用。

## Results and project registration

Task Sheet 中：

```text
path    → 当前 Task Sheet 实际执行 item 的工作/文件目录与恢复入口
results → 已确认有效、值得直接定位或供后续 item 消费的关键正式产物
```

`results` 不要求统一子 schema，应按 capability 的产物语义记录。

`project_result_index.md` 是**白名单登记**：各 capability 哪些正式结果文件允许进入项目级登记，由对应 capability owner 的 Skill / README 定义。

对于集中管理的 reusable trajectory，具体 trajectory 文件只登记到 `trajectory_index.yaml`；`project_result_index.md` 不逐条登记这些 trajectory，而只登记 `trajectory_index.yaml` 这一项目级 trajectory 检索入口。

本 Skill：

- 只登记 capability owner 明确允许登记的正式结果文件 / 结果入口；
- 不在 main Skill 或 inventory 中维护集中式文件白名单；
- 不因为文件存在于 `results`、item 目录或“可能以后有用”就自动登记；
- 不把 debug / scratch / cache / 普通中间文件加入项目级结果索引；
- direct reuse 继续引用原正式结果，不为复用动作复制一份结果文件。

## Stage 5 Skill completion boundary

本 Skill 只判断自己负责的当前 Task Sheet Stage 5 plan items 是否已经处理到可以结束当前 Skill 职责的状态。

结束当前职责前确认：

- 当前 Stage 5 plan items 中没有仍需本 Skill 继续推进的 `未完成` item；
- 每个 `已完成` item 已通过对应 capability owner validation；
- direct reuse 的 `已终止` item 已引用足以满足当前 item 的有效正式结果；
- 其它 `已终止` item 已有明确 `reason`，且依赖关系仍可追溯；
- 需要恢复或供后续 item 消费的关键产物已按需写入 `results`；
- 本次新产生、且 capability owner 明确允许项目级登记的正式结果已经登记。

当前 Task Sheet 中如果仍有位于 Stage 5 plan items 区域之外的 capability gap、其它边界外事项或未解决要求，当前 Task Sheet 的 `5 Analysis` 是否仍为未完成，由当前 Task Execution Agent / 用户判断。本 Skill 不因自己的 plan items 已结束就自动宣称整个 Stage 5、当前 Task Sheet 或更大的科研任务完成。

## Reference

`references/analysis_capability_inventory.yaml`
: Stage 5 当前 capability discovery inventory。只登记已有真实 `entry` 的 capability。

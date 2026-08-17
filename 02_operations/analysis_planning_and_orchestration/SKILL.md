---
name: analysis-planning-and-orchestration
description: Workflow 5 / Step 5.1。把 Task Sheet 中的分析目标展开为可执行 plan items，集中完成 Stage 5 reuse 查询与核验，使用 analysis tool inventory 选择并调度对应分析 Skill / prepared-input producer，并维护当前 5.1 计划。
---

# 5.1 Analysis planning and orchestration

## Purpose

把 Manager 写入 Task Sheet 的分析目标、对象和约束转换为当前任务可执行的 Stage 5 plan。

本 Skill 负责分析方案组织与 Stage 5 reuse 核验，不负责重新实现具体分析方法，也不负责替代各 Tool/analysis Skill 对其输出数据进行 validation。

## Object requirements

进入 5.1 时至少需要：

- 当前 Task Sheet 中的 `5.1 Analysis planning and orchestration` 条目；
- 用户已经明确的分析目标、对象和约束；
- `references/analysis_tool_inventory.yaml`；
- 当前项目 `project_result_index.md` 中与 Stage 5 分析有关的正式结果入口；
- 需要 prepared trajectory 时，项目 `05_analysis/indexes/trajectory_index.yaml`（如已存在）；
- 需要 `.ndx` 时，项目 `05_analysis/indexes/ndx_index.yaml`（如已存在）；
- 解析候选输入所必需的实际文件或 Stage 4 `run_unit.yaml`。

Manager 只提供任务层需求。5.1 不要求 Manager 预先决定 RMSD/RDF/PCA 等具体方法组合。

## Reuse conditions

Stage 5 的 reuse 检查由 5.1 统一组织。

5.1 在生成当前完整 plan 时集中查询一次：

- 已有正式分析结果；
- 已登记的 prepared trajectories；
- 已登记的 `.ndx`；
- 当前 Task Sheet 内已经规划、稍后将由前置 plan item 生成且明确供后续使用的文件。

对具体分析结果是否可复用，使用对应 analysis Skill 给出的科学判据；对 prepared input 是否可复用，使用对应 producer/index 的规则。

统一处理：

```text
明确满足当前分析要求
→ 直接纳入当前 plan 作为复用结果/输入

明确不满足
→ 在当前 plan 中安排新的分析或 prepared-input producer

信息不足无法判断
→ 当前 Task Execution Agent 向用户确认

用户明确要求重做/对照
→ 跳过自动复用
```

正常 plan 建立后，不在每个后续 item 启动前重新做一次全局 reuse 查询。只有执行证据破坏当前 plan 的前提时才重新调整尚未完成的后续 plan。

## Analysis tool inventory

固定读取：

`references/analysis_tool_inventory.yaml`

inventory 是能力发现入口。每个实际可用条目至少包含：

```yaml
name:
purpose:
required_files:
skill:
```

5.1 使用它判断：

- 当前有哪些可调用分析能力；
- 哪个 Skill/Tool 对应当前方法；
- 调用前至少需要哪些文件角色/类型。

inventory 不替代实际 analysis Skill，也不复制具体命令、selection、trajectory preprocessing 或 validation 规则。

## Planning rules

5.1 先整体设计当前 Stage 5 plan，再开始逐项调度。

典型顺序：

```text
read analysis requirement
→ select candidate tools/analysis Skills
→ resolve current available inputs
→ query existing reusable resources/results
→ identify missing prepared inputs
→ add trjconv / make_ndx or other producer items where required
→ establish intended use/dependency of their future outputs
→ add requested analysis items
→ write/update the complete plan in Task Sheet
→ execute plan items
```

如果当前用户已经明确指定 RMSD/RDF 等方法，5.1 保留这些要求并把它们落实为可执行 plan items。

如果用户只给出研究目标，例如“分析结构稳定性”或“分析离子在表面的分布”，由 5.1 根据 tool inventory 和当前研究对象决定具体分析方法；Manager 不代替这一步。

## Plan-item format

plan item 可以是具体分析，也可以是为后续分析准备输入的工具调用，因此统一称为 plan item。

每项使用当前 5.1 内部的局部整数编号：

```text
1
2
3
...
```

编号规则：

- 一旦加入 Task Sheet，编号固定；
- 原则上不删除、不重编号；
- 后续确认不再执行时标记 `已终止`；
- 新增项使用下一个整数编号。

状态只允许：

```text
未完成
已完成
已终止
```

每项最少记录：

```text
编号
tool
inputs
settings
status
path
```

### `tool`

直接记录 inventory 中的 `name`。

### `inputs`

已有输入使用实际完整文件路径，不用 `source: md.N` 代替实际文件。

如果输入尚未生成但已经由本 plan 的前置项目负责产生，直接记录清楚依赖，例如：

```text
trajectory: 使用第 1 项生成的处理后轨迹
index: 使用第 2 项生成的 ndx 文件
```

不需要额外 `from_item` / `output_role` schema。

### `settings`

只记录使当前 plan item 足够明确的 tool-specific 设置。

例如 `dt`、time range、reference、selection、fit 要求等是否需要记录，由当前 tool/analysis Skill 和实际分析目的决定；Stage 5 不建立统一固定字段集。

### `path`

记录当前 plan item 相关文件的完整存放目录，用于查询和恢复。

`path` 不表示某一个结果文件，也不要求 5.1 自己决定 producer Tool 的最终输出位置。

## Multiple-input rule

如果多条 trajectory 作为同一次统一分析共同处理，且使用同一套关键 analysis settings，可以在一个 plan item 中记录多条 trajectory 和一套共同 topology/reference 输入。

如果需要分别分析，或关键 settings 不同，则拆成多个 plan items。

例如“分别对三条 trajectory 做 RMSD”应建立三个 plan items；“把三条已经对齐、相同 dt 的 trajectory 作为同一次 RMSD 分析输入”可以建立一个 plan item。

## Prepared trajectory handling

项目索引：

`<project_root>/05_analysis/indexes/trajectory_index.yaml`

5.1 只负责：

- 查询候选；
- 根据当前分析要求核验是否可复用；
- 将可用完整路径写入 plan；
- 如果不存在适用 trajectory，在 plan 中安排 `trjconv` producer。

`trjconv` Tool/Skill 自己负责：

- 实际生成处理后 trajectory；
- 决定/遵守自己的输出存放规则；
- 对自己生成的数据做 validation；
- 更新 `trajectory_index.yaml`。

当前索引最小方向由 Stage 5 Workflow 定义，具体字段细化归 `trjconv` Tool/Skill。

## `.ndx` handling

项目索引：

`<project_root>/05_analysis/indexes/ndx_index.yaml`

5.1 只负责：

- 查询候选 `.ndx`；
- 按当前 reuse 规则判断是否可用；
- 使用实际完整路径；
- 如果不存在适用 `.ndx`，在 plan 中安排 `make_ndx` producer。

`make_ndx` Tool/Skill 自己负责：

- 生成 `.ndx`；
- 决定/遵守自己的输出存放规则；
- 对自己生成的数据做 validation；
- 更新 `ndx_index.yaml`。

`ndx_index.yaml` 最小记录：

```yaml
- path: /full/path/to/analysis.ndx
  tpr: /full/path/to/reference.tpr
```

5.1 reuse 判断：

```text
current tpr == indexed tpr
→ 可复用

different tpr
+ 对应 Stage 4 run units 在 04_md_simulation/run_unit.yaml 中记录 same top
→ 可复用

different top
→ 不复用
```

不默认增加 atom count / atom ordering 二次核验，也不在索引中复制 `.ndx` groups。

## Validation requirements

5.1 只做 orchestration-level validation：

- plan 已覆盖当前用户分析目标；
- 每个 plan item 的 tool、inputs、settings 和依赖足以让对应 Skill/Tool 接手；
- plan item 编号和状态维护一致；
- 后续依赖没有引用已经终止或未能产生所需输入的前置项；
- 只有对应 Tool/analysis Skill 自己确认输出有效后，plan item 才能标记 `已完成`。

5.1 不重新计算或重新验证各工具产生的科学数据。

## Execution-plan maintenance

执行期间：

- plan item 完成并通过自身 tool validation → `已完成`；
- 可重试失败、等待必要输入或尚需处理 → 保持 `未完成`，必要原因写入执行记录；
- 明确不再继续 → `已终止`；
- 已加入的 item 原则上不删除；
- 新证据改变分析需求时，可以追加新的 item；
- 如果新证据破坏后续计划前提，调整尚未完成 item 的 inputs/settings 或追加替代项，并保留已有编号历史。

## Official results

5.1 不生成独立 `analysis_plan.yaml`。

其正式可追溯结果由两部分组成：

1. 当前 Task Sheet 中已经维护好的 5.1 plan items；
2. `project_result_index.md` 中的 Stage 5 分析事项登记。

Stage 5 的 project-level 登记粒度是：

```text
对哪些对象
→ 做了哪些分析
→ 详细记录入口
```

详细记录入口应能定位对应 Task Sheet / 5.1 plan item，并进一步找到：

```text
tool
inputs
settings
status
path
```

不逐文件把工具输出重复登记成 project-level result。

## Completion

当满足以下条件时，5.1 可以标记完成：

- 当前分析目标所需 plan items 已完成，或有明确理由进入 `已终止`；
- 所有 `已完成` item 均已通过各自 Tool/analysis Skill 自己负责的 validation；
- 需要登记的分析事项已写入 `project_result_index.md`。

多结果汇总、综合解释或报告生成不是固定必需步骤，除非当前用户任务明确要求。

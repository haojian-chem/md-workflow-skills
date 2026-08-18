---
name: md-analysis-trjcat
description: Stage 5 `trjcat` capability guide。用于按当前 Stage 5 plan item 已确定的 inputs / settings 执行 `gmx trjcat` 轨迹拼接，保留可恢复的命令与 stdin 记录，并管理具有后续复用价值的正式 trajectory。
---

# Purpose

本 Skill 指导 Agent 落实当前 Stage 5 plan item 中已经确定的 `trjcat` 处理要求。

本 Skill 不重新推导分析目标或重新决定 Stage 5 capability routing；当前 item 的 `inputs` / `settings` 是执行依据。

# Inputs / settings

读取当前 Stage 5 plan item 的：

```text
inputs
settings
path
```

`inputs` 用于定位当前 `gmx trjcat` 调用实际需要的多个 trajectory，以及当前操作实际需要的其它文件；不要求固定字段全集。

`settings` 表达 Stage 5 已经确定的 trajectory concatenation 要求，例如时间范围、`dt`、文件时间顺序、起始时间调整、重叠帧处理、输出格式或其它当前调用需要的条件；不建立统一 `trjcat_settings` schema，也不要求这些设置全部存在。

如果已有 `inputs / settings` 仍不足以可靠确定会改变拼接结果语义的关键条件，应回到当前 Stage 5 plan item 补足歧义，不自行猜测。

# Execution guidance

按当前 item 的 `inputs / settings` 构造并执行相应的 `gmx trjcat` command(s)。

拼接前确认实际输入能够作为同一输出 trajectory 的片段使用，尤其关注 atom set / atom order 与时间轴是否兼容。对于时间戳、文件顺序、重叠帧、起始时间调整、时间截取或采样等问题，按当前 item 的要求选择相应 `gmx trjcat` 选项，不额外引入无需求的处理。

当需要交互式设置输入轨迹起始时间时，按当前 item 已确定的时间语义提供输入；不要仅依赖文件名推断时间关系。

# Execution record

建议在当前 item `path` 下使用固定文件名：

```text
trjcat_record.md
```

记录格式自由，但每次实际 `gmx trjcat` 调用应能恢复：

```text
Command
Stdin
```

其中 `Command` 记录 `gmx trjcat ...` 本身；输入 trajectory 已体现在命令参数中，不另建重复文件清单。

如果命令通过 glob 等 shell 展开提供多个输入文件，记录时优先保留实际传给 `gmx trjcat` 的展开后文件序列，使输入可恢复。

如果实际执行时使用 `printf`、pipe、here-string 或其它 shell 包装向 `gmx trjcat` 提供交互输入，记录时把外围 shell 包装转换成实际传给 `gmx trjcat` 的 stdin。例如：

```markdown
## Command 1

gmx trjcat -f part1.xtc part2.xtc -o joined.xtc -settime

## Stdin

0
100000
```

没有交互输入时可记录 `none`。多次调用按实际执行顺序记录。

# Output check

执行后检查输出 trajectory 是否与当前 item 要求一致。重点确认预期输入片段已经进入输出，并检查时间顺序、时间范围、重叠处理和实际 frame spacing 是否符合本次拼接要求；输出还应能作为一个一致的 trajectory 正常读取和使用。

检查保持任务导向，不建立独立 Validator、固定检查表或额外 validation metadata。

# Reusable trajectory management

当前 item 的工作记录仍位于：

```text
<project_root>/05_analysis/<task_id>/<编号>.trjcat/
```

当输出 trajectory 确实具有后续复用价值时，将正式 reusable trajectory 集中存放于：

```text
<project_root>/05_analysis/trajectories/
```

并登记到：

```text
<project_root>/05_analysis/indexes/trajectory_index.yaml
```

普通临时或试验性输出不需要因为生成过就集中存放或登记。

## Naming

trajectory 名称由 lineage 决定，而不是由 `trjcat` capability 本身决定。

如果所有输入最终都能够唯一归属于同一个 Stage 4 run unit，输出继续使用该 run-unit lineage：

```text
<run_unit_id>.traj.N
```

例如：

```text
md.1.traj.3
```

`N` 在该 run-unit lineage 内递增。

如果输入来源跨多个 run-unit lineage，或已有输入本身属于 `multi` lineage，则输出使用：

```text
multi.traj.N
```

`N` 在项目内 `multi` trajectory 中递增。

分配新编号时先查看当前 `trajectory_index.yaml` 中已正式登记的同 lineage trajectory，并确认目标文件名不存在，避免覆盖既有正式 trajectory。

## `trajectory_index.yaml`

该索引只用于候选发现和初筛，不承担完整 trajectory concatenation metadata。

每个由本 capability 登记的 reusable trajectory 记录：

```yaml
- trajectory_id: multi.traj.2
  path: /full/project/path/05_analysis/trajectories/multi.traj.2.xtc
  source_run_units:
    - md.1
    - md.2
  output_selection: System
  dt: 10 ps
  producer_path: /full/project/path/05_analysis/T003/2.trjcat/
```

字段含义：

- `trajectory_id`：正式 trajectory 名称；
- `path`：集中存放的实际 trajectory 完整路径；
- `source_run_units`：所有底层 Stage 4 run-unit lineage；
- `output_selection`：拼接后 trajectory 实际共有的 atom set / output group；
- `dt`：当前 trajectory 的实际 frame spacing，带单位；
- `producer_path`：本次 `trjcat` item 的完整工作目录，用于后续二次核查。

`source_run_units` 应追溯输入 trajectory 的底层 lineage 后汇总，不把 `multi` 当作 run-unit id 写入该字段。

更详细的实际输入序列、时间范围、时间戳调整、重叠处理、采样等不复制进索引。后续需要二次 reuse 核验时，沿 `producer_path` 查看 `trjcat_record.md` 中的实际 `gmx trjcat` command(s) 与 stdin，并按需检查实际文件。

本 capability 只登记自己产生、检查后确认具有后续复用价值的正式 trajectory；不修改其它 producer 已登记 trajectory 的 provenance。

# Project result registration

具体 reusable trajectory 文件只登记到 `trajectory_index.yaml`，不逐条登记到 `project_result_index.md`。

对于本 capability，允许进入 `project_result_index.md` 的 trajectory-management 入口只有：

```text
<project_root>/05_analysis/indexes/trajectory_index.yaml
```

如果该项目级索引已经存在正式登记，不为每次新增 trajectory 重复创建新的 project-result 条目。

# Result update

完成当前 item 后，按 Stage 5 main Skill 的 plan-item 规则更新 Task Sheet。需要供后续 item 直接消费的有效 trajectory 可写入当前 item 的 `results`；若输出已集中登记，`results` 应定位实际 reusable trajectory，而不是复制一份文件。

本 Skill 不为结果增加独立 handoff 文件。

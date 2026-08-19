---
name: md-analysis-trjconv
description: Stage 5 `trjconv` capability guide。用于按当前 Stage 5 plan item 已确定的 inputs / settings 执行 `gmx trjconv` 轨迹处理，保留可恢复的命令与 stdin 记录，并管理具有后续复用价值的正式 trajectory。
---

# Purpose

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 在 shared Task Execution 规则和 Stage 5 main Skill 的 plan-item 规则基础上，只负责当前 `trjconv` item 的具体执行、检查与结果维护。

本 Skill 指导 Agent 落实当前 Stage 5 plan item 中已经确定的 `trjconv` 处理要求。

本 Skill 不重新推导分析目标或重新决定 Stage 5 capability routing；当前 item 的 `inputs` / `settings` 是执行依据。

# Inputs / settings

读取当前 Stage 5 plan item 的：

```text
inputs
settings
path
```

`inputs` 用于定位当前 `gmx trjconv` 调用实际需要的 trajectory、structure/reference、index 等文件；只使用当前操作真正需要的文件，不要求固定字段全集。

`settings` 表达 Stage 5 已经确定的 trajectory processing 要求，例如时间截取、`dt`、output selection、PBC、centering、fit、输出格式等；不建立统一 `trjconv_settings` schema，也不要求这些设置全部存在。

如果已有 `inputs / settings` 仍不足以可靠确定关键处理方式，应回到当前 Stage 5 plan item 补足歧义，不自行猜测会改变轨迹语义的条件。

# Execution guidance

按当前 item 的 `inputs / settings` 构造并执行相应的 `gmx trjconv` command(s)。

常用处理包括时间范围/帧采样、atom subset、PBC、centering、fit/alignment 和 trajectory 格式转换。只执行当前 item 要求的处理，不为“标准化”额外增加无需求的 preprocessing。

PBC、centering、fit 等组合较复杂时，可以拆成多次 `gmx trjconv`，不强求单条命令完成。处理顺序会影响结果；常见倾向是先处理分子完整性/连续性，再做 centering，fit 通常靠后。最终以当前 item 要求和实际轨迹效果为准。

多步处理产生的临时 trajectory 可以保留在当前 item `path` 下用于恢复或排查；不需要因为产生过就进入集中 trajectory 索引。

# Execution record

建议在当前 item `path` 下使用固定文件名：

```text
trjconv_record.md
```

记录格式自由，但每次实际 `gmx trjconv` 调用应能恢复：

```text
Command
Stdin
```

其中 `Command` 记录 `gmx trjconv ...` 本身；文件输入已经体现在命令参数中，不另建一份重复文件清单。

如果实际执行时使用 `printf`、pipe、here-string 或其它 shell 包装向 `gmx trjconv` 提供交互输入，记录时把外围 shell 包装转换成实际传给 `gmx trjconv` 的 stdin。例如：

```markdown
## Command 1

gmx trjconv -s md.tpr -f md.xtc -o traj.xtc -center

## Stdin

1
0
```

如有必要，可在 stdin 后补充 group 含义以提高可读性，但不要求额外 schema。多次调用按实际执行顺序记录。

# Output check

执行后检查输出 trajectory 是否与当前 item 要求一致。尤其当本次实际涉及时间范围/采样、output selection、PBC、centering 或 fit 时，应查看相应处理效果，而不是仅依据命令退出状态判断结果可用。

检查保持任务导向，不建立独立 Validator、固定检查表或额外 validation metadata。

# Reusable trajectory management

当前 item 的工作记录仍位于：

```text
<project_root>/05_analysis/<task_id>/<编号>.trjconv/
```

当输出 trajectory 确实具有后续复用价值时，将正式 reusable trajectory 集中存放于：

```text
<project_root>/05_analysis/trajectories/
```

并登记到：

```text
<project_root>/05_analysis/indexes/trajectory_index.yaml
```

中间临时 trajectory 不需要集中存放或登记。

## Naming

trajectory 名称由 lineage 决定，而不是由本次具体处理步骤决定。

能够唯一归属于一个 Stage 4 run unit 时：

```text
<run_unit_id>.traj.N
```

例如：

```text
md.1.traj.1
md.1.traj.2
```

`N` 在该 run-unit lineage 内递增。已有 processed trajectory 再处理时继承原 run-unit lineage root。

来源跨多个 run-unit lineage、不能唯一归属于单一 run unit 时：

```text
multi.traj.N
```

`N` 在项目内 `multi` trajectory 中递增。已有 `multi.traj.N` 再处理时继续继承 `multi` lineage。

分配新编号时先查看当前 `trajectory_index.yaml` 中已正式登记的同 lineage trajectory，并确认目标文件名不存在，避免覆盖既有正式 trajectory。

## `trajectory_index.yaml`

该索引只用于候选发现和初筛，不承担完整 trajectory processing metadata。

每个由本 capability 登记的 reusable trajectory 记录：

```yaml
- trajectory_id: md.1.traj.2
  path: /full/project/path/05_analysis/trajectories/md.1.traj.2.xtc
  source_run_units:
    - md.1
  output_selection: System
  dt: 10 ps
  producer_path: /full/project/path/05_analysis/T001/1.trjconv/
```

字段含义：

- `trajectory_id`：正式 trajectory 名称；
- `path`：集中存放的实际 trajectory 完整路径；
- `source_run_units`：底层 Stage 4 run-unit lineage；
- `output_selection`：当前 trajectory 实际保留的 output group / atom set；
- `dt`：当前 trajectory 的实际 frame spacing，带单位；
- `producer_path`：本次 `trjconv` item 的完整工作目录，用于后续二次核查。

更详细的 time range、PBC、centering、fit、reference、处理顺序等不复制进索引。后续需要二次 reuse 核验时，沿 `producer_path` 查看 `trjconv_record.md` 中的实际 `gmx trjconv` command(s) 与 stdin，并按需检查实际文件。

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

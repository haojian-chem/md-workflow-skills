---
name: md-analysis-make-ndx
description: Stage 5 `make_ndx` capability guide。用于按当前 Stage 5 plan item 已确定的 inputs / settings 生成或补充分析所需的 GROMACS `.ndx` groups；复杂 group 可使用 `gmx make_ndx`，简单且确定的 group 允许直接创建或修改 `.ndx`。
---

# Purpose

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 在 shared Task Execution 规则和 Stage 5 main Skill 的 plan-item 规则基础上，只负责当前 `make_ndx` item 的具体执行、检查与 results。

本 Skill 指导 Agent 落实当前 Stage 5 plan item 中已经确定的 index-group 要求，产出与当前结构/原子编号一致、可被后续 analysis capability 明确使用的 `.ndx` 文件。

本 Skill 不重新判断当前分析是否需要 external index，也不重新决定 Stage 5 capability routing；当前 item 的 `inputs` / `settings` 是执行依据。

# Inputs / settings

读取当前 Stage 5 plan item 的：

```text
inputs
settings
path
```

`inputs` 用于定位当前 group 构造实际需要的 structure / topology-like structure input、已有 `.ndx` 或其它当前操作真正需要的文件；不要求固定字段全集。

已有 `.ndx` 可以来自当前 Task Sheet，也可以来自同一科研任务的前序 Task Sheet。只要当前 item 能通过完整路径或明确来源定位该文件，就不因为跨 Task Sheet 而要求重新生成；是否适用于当前分析仍由后续 consuming capability 根据 group membership、结构和原子顺序核验。

`settings` 表达当前 item 已确定的目标 group 及其 selection / membership 要求，例如目标 group 名、残基/原子范围、已有 group 组合或其它能够明确当前 selection 语义的信息；不建立统一 `make_ndx_settings` schema。

如果当前信息仍不足以可靠确定目标 group membership，应回到当前 Stage 5 plan item 补足歧义，不自行猜测会改变 selection 语义的条件。

# Execution guidance

目标是得到正确的 `.ndx` group，不要求所有情况都必须通过 `gmx make_ndx` 完成。

当 group 构造较复杂，涉及交互式 selection、已有 groups 的布尔组合、split、rename 等操作时，可使用 `gmx make_ndx` 按当前 item 要求生成或修改 `.ndx`。

当补充的 group 简单且 membership 已经明确时，Agent 可以直接创建或修改 `.ndx` 文件，例如已有明确 atom-number 列表、少量明确原子的组合，或当前 item 已明确给出的简单范围。是否简单到适合 direct edit 由 Agent 根据当前处理对象和要求判断，不建立固定复杂度判据。

直接编辑 `.ndx` 时避免无关地改动已有 groups，并保持 GROMACS index 的 1-based atom numbering。group 名应与后续 capability 实际选择时使用的名称一致。

# Execution record

如果实际调用了 `gmx make_ndx`，建议在当前 item `path` 下使用：

```text
make_ndx_record.md
```

记录格式自由，但每次实际 `gmx make_ndx` 调用应能恢复：

```text
Command
Stdin
```

其中 `Command` 记录 `gmx make_ndx ...` 本身；`-f / -n / -o` 等文件已经体现在命令参数中，不另建重复文件清单。

如果实际执行时使用 `printf`、pipe、here-string 或其它 shell 包装提供交互输入，记录时把外围 shell 包装转换成实际传给 `gmx make_ndx` 的 stdin。例如：

```markdown
## Command

gmx make_ndx -f system.gro -o analysis.ndx

## Stdin

r 1-100
name 10 Protein_part
q
```

如果当前 item 采用 direct edit，不伪造 `gmx make_ndx` command / stdin，也不强制为了简单编辑另建详细操作日志；最终 `.ndx` 与当前 item 的要求是主要恢复依据。

# Output check

完成后检查目标 group 是否满足当前 item 的实际要求，至少确认：

- 目标 group 实际存在且名称明确；
- group membership 与当前 selection 要求一致；
- atom numbers 与当前 structure / atom ordering 对应，并使用 GROMACS 的 1-based numbering；
- direct edit 没有无意破坏当前需要保留的其它 groups。

检查保持任务导向，不建立独立 Validator、固定 metadata schema 或 project-level group registry。

# Results

当前 item 的 `.ndx` 默认保留在：

```text
<project_root>/05_analysis/<task_id>/<编号>.make_ndx/
```

这里的 `<task_id>` 是当前 Task Sheet 的 `Txxxx` 标识。

需要供后续 Stage 5 item 使用的有效 `.ndx` 可写入当前 item 的 `results`，由后续 item 通过 Stage 5 plan dependency 显式引用。

本 capability 不建立 project-level `ndx_index.yaml`，也不执行跨 Task Sheet `.ndx` 自动登记或无边界扫描。前序 Task Sheet 已生成的 `.ndx` 可以由后续 Task Sheet 显式引用为 prepared input；不因为跨 Task Sheet 而复制文件或建立项目级 `.ndx` 索引。`.ndx` 不因生成而自动进入 `project_result_index.md`。

完成当前 item 后，按 Stage 5 main Skill 的 plan-item 规则更新 Task Sheet。本 Skill 不为结果增加独立 handoff 文件。

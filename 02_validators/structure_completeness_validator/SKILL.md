---
name: structure_completeness_validator
description: 结构准备 1.5。基于 1.4 当前 PDB 和前序已完成的 residue/atom 核对信息，生成当前保留结构的缺失与待修正报告；不修改结构。
---

# Purpose

对 1.4 输出的当前结构生成供 1.6 直接消费的 repair report。

1.5 不重新执行前序 residue-definition / atom-set 核对，也不修改 PDB。

# Object requirements

当前对象至少包括：

- 1.4 已验证的单一构象 PDB；
- 与当前 target 对应的上游 residue / atom identity 与已完成核对结果；
- 当前目标力场相关信息中已经明确的 Stage 1 可执行修正项。

# Reuse conditions

只有当前 1.4 PDB 与用于生成报告的上游核对结果均相同，且用户未要求重新检查时，已有 1.5 报告才可复用。

# Execution rules

1. 将上游已经确认的问题投影到 1.4 后实际保留的当前结构；已经不在当前 target 中的 residue / atom 不进入本次 repair report。
2. 报告当前结构中的：
   - missing residues；
   - missing heavy atoms；
   - confirmed extra atoms；
   - confirmed atom-name mismatches。
3. 对于属于正常 Stage 2 / `pdb2gmx` 处理范围的 force-field-specific terminal representation 差异，不作为 1.6 的删除/补全任务；如有必要，记录为 Stage 2 handoff item。
4. 1.5 不自行补原子、删原子、改原子名或修改坐标。

# Validation requirements

报告必须：

- 只覆盖当前 1.4 结构与当前 target；
- 每个 repair item 都能定位到明确 chain / residue / atom 或 missing-residue range；
- 不把已知由 `pdb2gmx` 正常处理的 terminal representation 差异误列为 Stage 1 repair；
- 不包含 1.5 新推断但没有上游依据的 extra / name-mismatch 结论。

# Official results

正式结果：

`01_structure_preparation/05_completeness_check/<task_id>/structure_completeness_report.yaml`

报告至少区分：

- `missing_residues`；
- `missing_heavy_atoms`；
- `extra_atoms`；
- `atom_name_mismatches`；
- `stage2_handoff_items`（存在时）。

---
name: structure_preparation_validation
description: 结构准备 1.9。对 Stage 1 最终 PDB / map 执行阶段级只读验证，并再次检查与目标力场的兼容性；不修复结构。
---

# Purpose

确认 Stage 1 最终结果可以安全交给 Stage 2 topology preparation。

1.9 既检查 Stage 1 内部结果一致性，也检查最终结构是否存在阻塞 Stage 2 的 force-field compatibility 问题。1.9 不自行修改 PDB、map 或上游报告。

# Object requirements

当前对象至少包括：

- 1.8 `stage1_final.pdb`；
- 1.8 `stage1_final.map`；
- 1.4–1.8 的正式报告/验证结果；
- 1.2 classification / relation 信息；
- 当前目标 force field 或已确定的相关 residue / atom definitions。

# Reuse conditions

只有 Stage 1 final PDB / map、相关上游正式结果和目标 force-field definitions 均相同时，已有 1.9 PASS 才可复用。

# Validation requirements

## 1. Stage 1 structural validation

检查：

- 不存在未解决的多 conformer / altloc 问题；
- 1.5 report 中应由 1.6 处理的项目已全部解决；
- 1.7 protonation assignment 已落实到最终 residue name；
- 1.8 chain assignment、residue/atom order 与 mapping 已通过验证；
- `stage1_final.pdb` 与 `stage1_final.map` 一一对应；
- 没有上游步骤遗留的 blocking unresolved item。

## 2. Final force-field compatibility check

对最终 Stage 1 结构再次检查：

- `STANDARD_RESIDUE` 的最终 residue name 可由目标 force field 识别；
- standard residue 的 heavy-atom naming / composition 与目标 force-field handling 兼容；
- 1.7 修改后的 protonation-state residue name 确实存在于目标 force field；
- 1.6/1.7/1.8 修改后没有重新产生新的 blocking residue-name / atom-name / heavy-atom incompatibility；
- topology-linked / independent nonstandard residues 不按 standard-residue template 误判。

对于已经确认属于正常 Stage 2 / `pdb2gmx` termini processing 能处理的 terminal representation 差异：

- 不在 1.9 修改；
- 不作为 Stage 1 FAIL；
- 记录为 Stage 2 handoff item。

真正无法由 Stage 2 正常处理的 compatibility 问题才判为 FAIL。

# Failure handling

1.9 只定位问题来源，不自行 repair。

失败时应指明问题更可能属于 1.4、1.6、1.7、1.8 或更早的上游定义/分类，并回到责任步骤处理后重新验证。

# Official results

正式结果：

`01_structure_preparation/09_validation/<task_id>/structure_preparation_validation.md`

报告至少给出：

- Stage 1 structural validation：PASS / FAIL；
- force-field compatibility：PASS / FAIL；
- Stage 2 handoff items（存在时）；
- blocking failures 及其建议回退步骤。

只有所有 blocking checks PASS 时，Stage 1 才可标记为完成并交给 Stage 2。

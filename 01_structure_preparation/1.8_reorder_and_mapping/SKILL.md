---
name: structure_reorder_and_mapping
description: 结构准备 1.8。对 1.7 后已经完成化学修正的重原子结构确定最终 Stage 1 chain assignment、整理 residue/atom order，并生成供 Stage 2 使用的 heavy-atom mapping。
---

# Purpose

把已经完成 conformer、缺失/多余/命名修正和蛋白质质子化状态赋值的结构，整理为 Stage 2 可稳定消费的最终 Stage 1 重原子结构。

1.8 只负责 organization + mapping，不再增删原子、不再修复结构，也不生成 force-field-specific all-atom order。

# Object requirements

当前对象至少包括：

- 1.7 已验证的 `protonation_assigned_structure.pdb`；
- 1.3 target identity / mapping；
- 1.2 中需要的 component / residue / relation 信息；
- 1.6 `completion_report.yaml`；
- topology-linked nonstandard unit 与其 standard-side linked residues 的已确认关系。

# Reuse conditions

已有 1.8 结果只有在输入结构、上游 identity / relation 信息、completion provenance 和 chain-assignment 依据均相同时才可自动复用。

# Execution rules

## 1. Final Stage 1 chain assignment

对于 topology-linked nonstandard unit：

- 如果所有 standard-side linked residues 都属于同一条 standard chain，则该 nonstandard unit 归入该 chain，不单独建立 chain；
- 如果 standard-side linked residues 跨多条 standard chain，则该 nonstandard unit 使用独立 chain identity。

Stage 1 chain identity 与后续 GROMACS `moleculetype` organization 是不同概念。1.8 不根据未来 moleculetype 合并 chain identity。

## 2. Residue / object order

- 保持 1.2/1.3 已建立的稳定结构对象顺序；
- 1.6 新补出的 missing residues 放回其所在 polymer chain 的正确 residue 位置；
- 同一 chain 中 standard polymer residue block 保持 polymer 顺序；
- 归入该 chain 的 topology-linked nonstandard unit 放在该 chain standard residue block 之后；
- 多个 linked nonstandard units 之间保持上游稳定 object order，不按 attachment residue number 重新排序。

## 3. Atom order

- 同一 residue 的 heavy atoms 必须连续；
- 保留已有稳定 atom order，并把 1.6 新增 heavy atoms 纳入对应 residue；
- 不为了匹配具体 force-field template 在 Stage 1 做最终 atom ordering；
- 1.8 本身不得改变 heavy-atom set。

完成后重新连续编号 PDB atom serial。

## 4. Mapping

生成最终 Stage 1 heavy-atom map。每个最终 heavy atom 至少能够追溯：

- final atom serial / chain / residue / atom name；
- 对应的上游 `component_id` / `residue_id`；
- atom origin：继承自上游结构，或由 1.6 completion 新增；
- 对继承 atom，保留可用的上游 atom serial / provenance。

1.6 已删除的 atom 不进入 final map；删除记录保留在 `completion_report.yaml` 中。

# Validation requirements

检查：

1. 1.8 输入和输出 heavy-atom set 完全一致；
2. topology-linked nonstandard unit 的最终 chain assignment 符合本 Skill 规则；
3. 新补 missing residues 已位于 polymer chain 的正确 residue 位置；
4. standard residue block 与 linked nonstandard block 的顺序符合规定；
5. 同一 residue 的 atoms 连续，且没有无依据的 force-field-specific atom reorder；
6. atom serial 连续且唯一；
7. final map 覆盖最终 PDB 中全部 heavy atoms且无重复；
8. map 中 final identity 与 PDB 逐 atom 一致；
9. inherited atoms 与 completion-added atoms 的 provenance 可由上游结果追溯。

任一项失败时 1.8 保持未完成；validation 不自行改 PDB 或 map。

# Official results

正式结果至少包括：

- `stage1_final.pdb`；
- `stage1_final.map`；
- `mapping_validation.md`。

结果写入：

`01_structure_preparation/08_reorder_and_mapping/<task_id>/`

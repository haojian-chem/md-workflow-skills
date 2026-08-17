---
name: structure_mapping_validator
description: 验证结构准备 1.8 的最终 Stage 1 chain assignment、heavy-atom order 与 mapping 是否一致；不修改结构。
---

# Purpose

确认 1.8 仅重组结构和建立 mapping，没有改变 heavy-atom composition，并保证最终 PDB 与 map 可作为 Stage 2 稳定输入。

# Object requirements

需要：

- 1.7 输入结构；
- 1.8 `stage1_final.pdb`；
- `stage1_final.map`；
- 1.2/1.3 identity / relation 信息；
- 1.6 `completion_report.yaml`。

# Validation requirements

检查：

1. 1.8 输入和输出 heavy-atom set 完全一致；
2. topology-linked nonstandard unit 的最终 chain assignment 符合 1.8 规则；
3. 新补 missing residues 已位于 polymer chain 的正确 residue 位置；
4. standard residue block 与 linked nonstandard block 的顺序符合规定；
5. 同一 residue 的 atoms 连续，且没有无依据的 force-field-specific atom reorder；
6. atom serial 连续且唯一；
7. final map 覆盖最终 PDB 中全部 heavy atoms且无重复；
8. map 中 final identity 与 PDB 逐 atom 一致；
9. inherited atoms 与 completion-added atoms 的 provenance 可由上游结果追溯。

任一项失败时 1.8 保持未完成，Validator 不自行改 PDB 或 map。

# Official results

写入：

`01_structure_preparation/08_reorder_and_mapping/<task_id>/mapping_validation.md`

---
name: protein_protonation_validator
description: 验证结构准备 1.7 的 PROPKA/化学环境质子化状态判断是否已正确落实到目标力场 residue name；不修改结构。
---

# Purpose

确认 1.7 的 protonation assignment、最终 residue naming 和输出 PDB 相互一致，并确认 1.7 没有越界改变重原子结构。

# Object requirements

需要：

- 1.6 输入结构；
- 1.7 `protonation_assigned_structure.pdb`；
- `protonation_assignment_report.yaml`；
- 当前目标蛋白质 force field / residue naming convention。

# Validation requirements

检查：

1. 报告中每个被赋值残基的最终 protonation state 与最终 residue name 一致；
2. 最终 residue name 可由目标 force field 正常识别；
3. 需要人工确认的 protonation decision 已解决；
4. 除允许的 residue-name 修改外，输入和输出 heavy-atom set、atom name、坐标与顺序没有非预期变化；
5. 1.7 没有生成最终氢原子。

任一 blocking 问题存在时 1.7 保持未完成。

# Official results

写入：

`01_structure_preparation/07_protein_protonation_assignment/<task_id>/protonation_validation.md`

---
name: protein_protonation_assignment
description: 结构准备 1.7。对蛋白质残基执行 PROPKA，并结合 PROPKA 结果与局部化学环境判断指定残基的质子化状态，再将 residue name 改为目标力场对应名称；不生成最终氢原子。
---

# Purpose

在进入 Stage 2 前确定蛋白质中需要显式区分的 protonation state，并把该决定落实到目标 force field 可识别的 residue naming。

1.7 决定化学状态和 residue name，不负责标准残基最终加氢；最终 H 由 Stage 2 标准残基拓扑生成处理。

# Object requirements

当前对象至少包括：

- 1.6 已验证的 `completed_structure.pdb`；
- 当前任务采用的蛋白质 force field 或明确的 protonation-state residue naming convention；
- 可执行 PROPKA；
- 需要时可读取当前结构中的局部化学环境与上游分类/关系信息。

# Reuse conditions

只有输入结构、PROPKA 设置、目标 force-field naming convention 和所有人工 protonation decisions 均相同时才可自动复用已有结果。

# Execution rules

1. 对当前结构中的蛋白质残基执行 PROPKA。
2. 对需要区分质子化状态的残基，结合：
   - PROPKA 结果；
   - 当前局部化学环境；
   - 已知配位、成键或其他影响质子化状态的结构信息；
   判断其 protonation state。
3. 将确定的状态映射为目标 force field 对应的 residue name，并修改 PDB residue name。
4. 不因质子化状态赋值而增加最终 H、删除重原子或改变原子坐标。
5. 无法仅凭 PROPKA 与结构环境可靠决定时，向用户确认，不静默选择。

# Validation requirements

检查：

1. 报告中每个被赋值残基的最终 protonation state 与最终 residue name 一致；
2. 最终 residue name 可由目标 force field 正常识别；
3. 需要人工确认的 protonation decision 已解决；
4. 除允许的 residue-name 修改外，输入和输出 heavy-atom set、atom name、坐标与顺序没有非预期变化；
5. 1.7 没有生成最终氢原子。

任一 blocking 问题存在时 1.7 保持未完成；validation 不修改结构。

# Official results

正式结果至少包括：

- `protonation_assigned_structure.pdb`；
- `protonation_assignment_report.yaml`；
- `protonation_validation.md`。

报告至少能够定位：chain / residue、原 residue name、PROPKA 结果、局部环境判断、最终 protonation state 和最终 residue name。

结果写入：

`01_structure_preparation/07_protein_protonation_assignment/<task_id>/`

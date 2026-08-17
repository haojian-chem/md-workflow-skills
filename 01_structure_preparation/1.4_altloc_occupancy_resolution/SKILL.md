---
name: altloc_occupancy_resolution
description: 结构准备 1.4。读取 1.3 生成的 target PDB，对存在多个 conformer / altloc 的部分选择一个保留构象，删除其余构象原子并更新 PDB atom serial。
---

# Purpose

将 1.3 输出的每个 target PDB 从可能含有多个 conformer 的结构，整理为后续完整性检查可直接消费的单一构象 PDB。

本步骤只处理 conformer / altloc，不处理缺失残基、缺失重原子、力场端基转换或质子化状态。

# Object requirements

当前对象至少包括：

- 1.3 正式 target PDB；
- 对应 target 记录；
- 需要时可定位 1.2/1.3 中与该 residue 相关的身份信息。

多个 target 分别处理，不在 1.4 中重新合并或拆分 target。

# Reuse conditions

已有 1.4 结果只有在输入 target PDB 相同、涉及的 conformer 集合相同、采用的构象选择决定相同，且用户没有要求重新选择时才可复用。

信息不足无法确认等价时向用户确认。

# Execution rules

1. 读取 1.3 target PDB，识别实际存在多个 conformer / altloc 的部分。
2. 对每个多 conformer 部分选择一个构象。选择可参考 occupancy、同一局部构象的一致性和化学合理性；存在多个合理选择且不能可靠决定时向用户确认。
3. 删除未选择 conformer 对应的多余原子记录。
4. 除 conformer 处理所必需的删除外，不改变 residue membership、atom identity 或坐标。
5. 按输出 PDB 中实际写入顺序重新连续编号 atom serial。
6. 输出单一构象 PDB，并记录本次构象选择结果。

# Validation requirements

检查：

- 报告中记录的每个多 conformer 部分都有唯一保留构象；
- 未选择构象对应的 atom records 已从输出 PDB 删除；
- 不再存在同一待处理位置的多个未解决 conformer；
- 未参与 conformer 选择的 residue / atoms 未被非预期删除、重命名或移动；
- atom serial 连续且唯一；
- 输出 PDB 可正常解析。

任一检查失败时 1.4 保持未完成；validation 不自行修复结构。

# Official results

当前任务实际执行新的 1.4 时，正式结果至少包括：

- `resolved_structure.pdb`；
- `altloc_resolution_report.yaml`；
- `altloc_validation.md`。

结果写入：

`01_structure_preparation/04_altloc_occupancy_resolution/<task_id>/`

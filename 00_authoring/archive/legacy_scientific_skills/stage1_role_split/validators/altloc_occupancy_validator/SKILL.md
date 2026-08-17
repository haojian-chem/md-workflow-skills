---
name: altloc_occupancy_validator
description: 验证结构准备 1.4 的 conformer / altloc 选择与 PDB 删除结果，不修改结构。
---

# Purpose

验证 1.4 已将当前 target PDB 中需要处理的多 conformer 部分解析为单一构象，并且没有引入与 conformer 处理无关的结构变化。

# Object requirements

需要：

- 1.3 输入 target PDB；
- 1.4 输出 `resolved_structure.pdb`；
- `altloc_resolution_report.yaml`。

# Validation requirements

检查：

1. 报告中记录的每个多 conformer 部分都有唯一保留构象；
2. 未选择构象对应的 atom records 已从输出 PDB 删除；
3. 不再存在同一待处理位置的多个未解决 conformer；
4. 未参与 conformer 选择的 residue / atoms 未被非预期删除、重命名或移动；
5. atom serial 连续且唯一；
6. 输出 PDB 可正常解析。

任一检查失败时 1.4 保持未完成，Validator 不自行修复。

# Official results

写入：

`01_structure_preparation/04_altloc_occupancy_resolution/<task_id>/altloc_validation.md`

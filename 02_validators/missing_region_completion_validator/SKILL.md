---
name: missing_region_completion_validator
description: 验证结构准备 1.6 是否完整落实 1.5 repair report，并检查补全/删除/改名后 PDB 的基本一致性；不修改结构。
---

# Purpose

验证 1.6 对 1.5 repair report 的执行结果，不重新做 1.5 的问题判定，也不自行修复失败项。

# Object requirements

需要：

- 1.4 输入 PDB；
- 1.5 `structure_completeness_report.yaml`；
- 1.6 `completed_structure.pdb`；
- `completion_report.yaml`。

# Validation requirements

逐项核验：

- missing residue → 对应 residue 已补入正确 chain / residue 位置；
- missing heavy atom → 对应 heavy atom 已存在；
- extra atom → 已删除；
- atom-name mismatch → 已按确认关系改名。

同时检查：

- `completion_report.yaml` 与实际 PDB 修改一致；
- 没有超出 1.5 report 的未记录删除/改名；
- 输出不存在重复 atom identity；
- atom serial 连续且唯一；
- PDB 可正常解析；
- 新增残基/重原子的局部连接与几何没有明显不合理；
- 没有添加本应留给后续步骤处理的最终 H；
- `unresolved_items` 为空。

任一应处理项目未解决时，1.6 保持未完成。

# Official results

写入：

`01_structure_preparation/06_missing_region_completion/<task_id>/completion_validation.md`

---
name: missing_region_completion
description: 结构准备 1.6。严格按 1.5 repair report 执行缺失残基补全、缺失重原子补全、多余原子删除和已确认原子名校正，并输出修正后的重原子 PDB。
---

# Purpose

将 1.5 已经明确的结构修正项落实到当前 PDB，使后续质子化状态判断和最终结构整理消费一个 composition-correct 的重原子结构。

1.6 不重新判断什么是 missing / extra / mismatch，也不处理 force-field-specific terminal conversion 或最终加氢。

# Object requirements

当前对象至少包括：

- 1.4 当前 PDB；
- 1.5 正式 `structure_completeness_report.yaml`；
- 补全缺失残基或重原子所需的参考结构/模板；
- 上游已确定的 residue / atom identity 与 rename 对应关系。

# Reuse conditions

已有 1.6 结果只有在输入 PDB、1.5 repair report、使用的补全参考/模板以及所有人工决定均相同时才可自动复用。

# Execution rules

按 1.5 report 执行以下四类动作：

1. 删除 confirmed extra atoms；
2. 按已确定对应关系校正 atom-name mismatch，保留原坐标和原子身份；
3. 补全 chain 内 missing residues；
4. 补全 missing heavy atoms。

除 report 明确要求的修改以及补全所必需的局部处理外，不自行扩展修复范围。

缺失重原子：

- 优先使用 AF3 完整残基模板或 CCD 完整残基模板；
- 以当前残基已有共同重原子对齐模板；
- 只移植缺失重原子。

缺失残基：

- 使用 AF3 生成的对应完整结构或用户提供的 AF3 结构作为参考；
- 先建立 chain / sequence residue correspondence；
- 使用缺失区两侧现有残基进行局部双侧对齐；
- anchor region 采用逐步向两侧扩展的策略，而不是固定 N 个残基；
- 优先使用能够给出稳定、几何一致局部叠合的最小双侧 anchor 区域；
- 只移植缺失 residue；
- 如果两侧不能同时得到合理局部叠合，不强行插入，改用其他参考/model 或向用户确认。

1.6 不添加最终 H。完成修改后按输出顺序重新连续编号 atom serial。

# Validation requirements

逐项核验 1.5 repair report：

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

任一应处理项目未解决时，1.6 保持未完成。Validation 不重新做 1.5 的问题判定，也不自行修复失败项。

# Official results

正式结果至少包括：

- `completed_structure.pdb`；
- `completion_report.yaml`；
- `completion_validation.md`。

`completion_report.yaml` 简要记录：

- added residues；
- added heavy atoms；
- removed atoms；
- renamed atoms；
- unresolved items（若存在）。

结果写入：

`01_structure_preparation/06_missing_region_completion/<task_id>/`

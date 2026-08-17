# Workflow 1 / Stage 1.9 Structure preparation validation architecture freeze

Status: **FROZEN AUTHORING REFERENCE — NOT AN ACTIVE SKILL**

## 0. 文档定位

本文件保存 `1.9 Structure preparation validation` 已经讨论并敲定的设计事实，以及后续正式生成 Skill 时需要直接继承的细节。

它不是 `SKILL.md`，也不表示 1.9 已经获得正式 Skill generation / activation 许可。正式 Skill 生成时，应以本 freeze + 当时 current 的 1.8 / Stage 2 handoff 接口 + authoring rules 为输入。

本文件迁移并保留此前误放入 active Skill 路径的 1.9 详细内容，并保留历史 final validator 中的有效信息；不恢复旧 Validator role layer。

Source preservation:

- former active pseudo-Skill: `01_structure_preparation/1.9_validation/SKILL.md`, blob `8219921970d07dea923699f7dc74f4e5fa589c83`
- historical final validation source: `02_validators/structure_preparation_validator/SKILL.md`, blob `ae0dfe2a240e7b89fe446520156c62bfa6b2cc51`

## 1. Purpose and boundary

1.9 的目标是确认 Stage 1 最终结果可以安全交给 Stage 2 topology / parameterization。

1.9 是 Stage 1 final read-only validation：

- 检查 Stage 1 内部结果一致性；
- 检查最终结构是否存在阻塞 Stage 2 的 force-field compatibility 问题；
- 定位 blocking failure 的上游 owner；
- 不自行修改 PDB、map 或上游报告；
- 不在 validation 步骤中静默 repair。

## 2. Required object / evidence

生成正式 1.9 Skill 时，至少应消费：

- 1.8 `stage1_final.pdb`；
- 1.8 `stage1_final.map`；
- 1.4–1.8 的正式报告 / validation 结果；
- 1.2 classification / relation 信息；
- 当前目标 force field，或已经确定的相关 residue / atom definitions。

## 3. Reuse model to carry into Skill generation

已有 1.9 PASS 只有在以下内容均明确等价时才可自动复用：

- Stage 1 final PDB 相同；
- Stage 1 final map 相同；
- 相关上游正式结果相同；
- 目标 force-field definitions 相同。

任一相关结构或定义变化，都需要重新执行 final validation。

## 4. Frozen Stage 1 structural validation

至少检查：

- 不存在未解决的 multi-conformer / altloc 问题；
- 1.5 report 中应由 1.6 处理的项目已经全部解决；
- 1.7 protonation assignment 已落实到最终 residue name；
- 1.8 chain assignment、residue/atom order 与 mapping 已通过其自身 validation；
- `stage1_final.pdb` 与 `stage1_final.map` 一一对应；
- 没有上游步骤遗留的 blocking unresolved item。

1.9 不重新执行 1.4、1.6、1.7 或 1.8 的内部处理逻辑，只验证它们的正式结果和当前最终状态是否闭合。

## 5. Frozen final force-field compatibility check

对最终 Stage 1 结构再次检查：

- `STANDARD_RESIDUE` 的最终 residue name 可由目标 force field 识别；
- standard residue 的 heavy-atom naming / composition 与目标 force-field handling 兼容；
- 1.7 修改后的 protonation-state residue name 确实存在于目标 force field；
- 1.6 / 1.7 / 1.8 的修改没有重新产生新的 blocking residue-name / atom-name / heavy-atom incompatibility；
- topology-linked / independent nonstandard residues 不按 standard-residue template 误判。

对于已经确认属于正常 Stage 2 / `pdb2gmx` termini processing 能处理的 terminal representation 差异：

- 不在 1.9 修改；
- 不作为 Stage 1 FAIL；
- 记录为 Stage 2 handoff item。

只有真正无法由 Stage 2 正常处理的 compatibility 问题才判为 blocking FAIL。

## 6. Frozen failure handling

1.9 只定位问题来源，不自行 repair。

失败时应明确指出问题更可能属于：

- 1.4 alternate-conformation handling；
- 1.6 completion / correction；
- 1.7 protonation assignment；
- 1.8 organization / mapping；
- 或更早的上游定义 / classification。

修复必须回到真正拥有该问题的步骤，再重新进入 1.9 验证。

## 7. Frozen results / handoff

后续正式 Skill 的结果方向至少包括：

```text
structure_preparation_validation.md
```

既有 execution-directory 约定为：

```text
01_structure_preparation/09_validation/<task_id>/structure_preparation_validation.md
```

报告至少给出：

- Stage 1 structural validation：PASS / FAIL；
- force-field compatibility：PASS / FAIL；
- Stage 2 handoff items（存在时）；
- blocking failures；
- 建议回退的责任步骤。

只有所有 blocking checks PASS 时，Stage 1 才可标记为完成并交给 Stage 2。

## 8. Stage 2 handoff boundary

1.9 只确认 Stage 1 final heavy-atom structure / map 可以进入 Stage 2。

Stage 2 的标准残基最终 H、force-field-specific all-atom order、topology generation / parameterization 不属于 1.9。

正常可由 `pdb2gmx` 处理的 terminal representation 差异保留为 Stage 2 handoff，而不是在 1.9 中提前转换。

## 9. Skill-generation note

正式生成 1.9 Skill 时：

- 直接继承本 freeze 中 read-only final-validation 边界；
- 保留 structural validation + final force-field compatibility 两类 blocking check；
- 不恢复独立 Validator role hierarchy；1.9 本身就是 Stage 1 final validation step；
- 不把 1.4 / 1.6 / 1.7 / 1.8 的内部 repair 逻辑复制进 1.9；
- 只有具体检查实现、报告组织和必要 deterministic helper 等尚未冻结内容，才在 authoring 阶段继续细化。

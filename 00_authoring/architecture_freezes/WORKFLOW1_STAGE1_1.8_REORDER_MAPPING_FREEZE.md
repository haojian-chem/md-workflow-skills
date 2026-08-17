# Workflow 1 / Stage 1.8 Reorder and mapping architecture freeze

Status: **FROZEN AUTHORING REFERENCE — NOT AN ACTIVE SKILL**

## 0. 文档定位

本文件保存 `1.8 Reorder and mapping` 已经讨论并敲定的设计事实，以及后续正式生成 Skill 时需要直接继承的细节。

它不是 `SKILL.md`，也不表示 1.8 已经获得正式 Skill generation / activation 许可。正式 Skill 生成时，应以本 freeze + 当时 current 的上游正式接口 + authoring rules 为输入。

本文件迁移并保留此前误放入 active Skill 路径的 1.8 详细内容，同时合并保留历史 Operation / Validator 中的有效信息；不恢复旧 Workflow / Operation / Validator 角色分类。

Source preservation:

- former active pseudo-Skill: `01_structure_preparation/1.8_reorder_and_mapping/SKILL.md`, blob `2cb6e8f3953770c9b6f4d51a9cf18ac10992879c`
- historical operation source: `02_operations/structure_reorder_and_mapping/SKILL.md`, blob `0c8b19728b2049dfbf40f73211ad010301996604`
- historical validation source: `02_validators/structure_mapping_validator/SKILL.md`, blob `1054f16bac3f6af9a2d1afc7c7fe91af69f95a2b`

## 1. Purpose and boundary

1.8 的目标是把已经完成 conformer resolution、结构修正和蛋白质 protonation-state naming 的当前重原子结构，整理为 Stage 2 可稳定消费的最终 Stage 1 structure + heavy-atom mapping。

1.8 只负责：

```text
final Stage 1 chain assignment
+ residue / object organization
+ heavy-atom order organization
+ final Stage 1 mapping
```

1.8 不负责：

- 新增或删除原子；
- 重新执行 structure repair；
- 改变 protonation state；
- 生成标准残基最终 H；
- 生成 force-field-specific final all-atom order；
- 根据未来 GROMACS `moleculetype` 组织反向改变 Stage 1 chain identity。

## 2. Required object / evidence

生成正式 1.8 Skill 时，至少应消费：

- 1.7 已验证的 `protonation_assigned_structure.pdb`；
- 1.3 target identity / mapping；
- 1.2 中需要的 component / residue / relation 信息；
- 1.6 `completion_report.yaml`；
- topology-linked nonstandard unit 与其 standard-side linked residues 的已确认关系。

## 3. Frozen final Stage 1 chain assignment

对于 topology-linked nonstandard unit：

- 如果所有 standard-side linked residues 都属于同一条 standard chain，则该 nonstandard unit 归入该 chain，不单独建立 chain；
- 如果 standard-side linked residues 跨多条 standard chain，则该 nonstandard unit 使用独立 chain identity。

该规则由 Stage 1 / 1.8 拥有。

必须保持：

```text
Stage 1 chain identity ≠ GROMACS moleculetype organization
```

后续 Stage 2 可以基于 covalent connectivity 将多个 chain 组织进同一 `moleculetype`，但不得反向覆盖已经确定的 Stage 1 chain identity。

## 4. Frozen residue / object order

顺序规则冻结为：

- 保持 1.2 / 1.3 已建立的稳定结构对象顺序；
- 1.6 新补出的 missing residues 放回其所在 polymer chain 的正确 residue 位置；
- 同一 chain 中 standard polymer residue block 保持 polymer 顺序；
- 归入该 chain 的 topology-linked nonstandard unit 放在该 chain 的 standard polymer residue block 之后；
- 多个 linked nonstandard units 之间保持上游稳定 object order；
- 不按 attachment residue number 重新排序 linked units；
- 不把 linked nonstandard unit 强行插到 attachment residue 的紧邻位置。

## 5. Frozen heavy-atom order

原子组织规则冻结为：

- 同一 residue 的 heavy atoms 必须连续；
- 保留已有稳定 atom order；
- 1.6 新增 heavy atoms 纳入对应 residue；
- 不为了匹配某个具体 force-field template 在 Stage 1 做 final force-field-specific atom ordering；
- 1.8 输入与输出 heavy-atom set 必须完全一致；
- 完成组织后按最终写入顺序重新连续编号 PDB atom serial。

Stage 1 最终输出仍是 heavy-atom organization；Stage 2 / 2.2 才建立标准部分 force-field-specific all-atom order。

## 6. Frozen mapping semantics

1.8 生成 Stage 1 final heavy-atom map。

每个最终 heavy atom 至少能够追溯：

- final atom serial；
- final chain identity；
- final residue identity / number / name；
- final atom name；
- 对应的上游 `component_id` / `residue_id`；
- atom origin；
- 对继承 atom，保留可用的上游 atom serial / provenance。

atom origin 的冻结语义为：

```text
SOURCE
ADDED_BY_COMPLETION
```

1.6 已删除的 atom 不进入 final map；其删除记录保留在 `completion_report.yaml` 中。

## 7. Reuse model to carry into Skill generation

已有 1.8 结果只有在以下条件均明确等价时才可自动复用：

- 输入结构相同；
- 上游 identity / relation 信息相同；
- completion provenance 相同；
- chain-assignment 依据相同。

明确变化时重新执行；信息不足时由后续正式 Skill 按 Lightweight Runtime 通用原则处理。

## 8. Validation boundary

Validation 属于 1.8 结果 owner，不需要恢复独立 Validator layer。

至少检查：

1. 1.8 输入和输出 heavy-atom set 完全一致；
2. topology-linked nonstandard unit 的最终 chain assignment 符合冻结规则；
3. 新补 missing residues 已位于 polymer chain 的正确 residue 位置；
4. standard residue block 与 linked nonstandard block 的顺序符合规定；
5. 同一 residue 的 atoms 连续，且没有无依据的 force-field-specific atom reorder；
6. atom serial 连续且唯一；
7. final map 覆盖最终 PDB 中全部 heavy atoms 且无重复；
8. map 中 final identity 与 PDB 逐 atom 一致；
9. inherited atoms 与 completion-added atoms 的 provenance 可由上游结果追溯。

任一项失败时，1.8 不能视作完成。Validation 不自行改 PDB 或 map。

## 9. Frozen results / handoff

后续正式 Skill 的结果方向至少包括：

```text
stage1_final.pdb
stage1_final.map
mapping_validation.md
```

既有 execution-directory 约定为：

```text
01_structure_preparation/08_reorder_and_mapping/<task_id>/
```

该路径是科研项目 execution directory，不是本仓库 Skill source directory。

## 10. Handoff to 1.9 / Stage 2

1.9 对 `stage1_final.pdb` + `stage1_final.map` 做 Stage 1 final read-only validation。

通过 1.9 后，Stage 2 消费的是经过 Stage 1 最终组织和映射的重原子结构；Stage 2 不应重新定义 1.8 已经拥有的 chain-assignment 规则。

## 11. Skill-generation note

正式生成 1.8 Skill 时：

- 直接继承本 freeze 中 chain assignment / residue-object order / heavy-atom order / mapping semantics；
- 保留 `SOURCE | ADDED_BY_COMPLETION` provenance 语义；
- 不恢复旧 `Operation + Validator` 双层包装；
- 不把 Stage 2 `moleculetype` 组织规则复制回 1.8；
- 只有具体 map 文件格式、reference 拆分、确定性 helper 等尚未冻结内容，才在 authoring 阶段继续细化。

# Workflow 1 / Stage 1.8 Reorder and mapping architecture record

Status: **FROZEN AUTHORING RECORD — ACTIVE SKILL GENERATED**

Current runtime authority:

```text
01_structure_preparation/1.8_reorder_and_mapping/SKILL.md
```

本文件保存 1.8 在正式 Skill generation 时采用的最终架构事实。active Skill 生成后，后续可变执行细节由 current `SKILL.md` / helper 拥有；本文件不再维护第二套平行 mutable specification。

## 1. Purpose

1.8 将当前 target 的 current valid heavy-atom structure 整理为 Stage 1 final structure，并建立 Stage 2 可稳定消费的 heavy-atom identity map。

职责：

```text
final Stage 1 chain assignment / representation
+ residue / object organization
+ heavy-atom block organization
+ final heavy-atom mapping
```

1.8 不做 structure repair、protonation assignment、标准 residue 最终补氢、force-field-specific all-atom ordering，也不根据后续 GROMACS `moleculetype` 反向改变 Stage 1 chain identity。

## 2. Inputs

每个 target 的正式输入收敛为：

- current valid heavy-atom PDB；
- 1.3 对应 `targets/target_xxx.yaml`；
- 1.2 正式 `classification_result.yaml`，且 `result_status: COMPLETE`。

1.6 `completion_report.yaml`、1.7 `protonation_assignment_report.yaml` 与 `relation_decisions.yaml` 不再作为 1.8 强制输入。已经落实的结构变化由 current structure 体现；人工 relation decisions 已同步进入 1.2 正式结果。

## 3. Reuse

1.8 **不设置 reuse**。

每次实际进入 1.8 都重新基于当前 target 的 current structure + 当前正式 1.2 / 1.3 identity information 生成结果。

## 4. Final chain assignment

对 topology-linked nonstandard unit：

- 所有 standard-side linked residues 属于同一 standard chain → unit 使用该 standard chain 的 final PDB chain ID；
- standard-side linked residues 跨多个 standard chains → unit 保持独立 chain identity。

如果 1.2 / 1.3 已经给出与该规则一致的 chain organization，1.8 直接沿用，不建立第二套 chain model。

跨多条 standard chain 的 linked unit 优先沿用已有独立 chain ID；只有现有表示不能可靠作为独立 chain 时，才按 1.3 固定序列：

```text
A-Z → a-z → 0-9
```

选择当前 final structure 中未使用且不与所链接 standard chains 冲突的 chain ID。

Stage 1 chain identity 与未来 GROMACS `moleculetype` organization 保持独立。

## 5. Residue / object order

同一 standard chain：

```text
standard polymer residue block
TER
assigned linked nonstandard unit 1
TER
assigned linked nonstandard unit 2
TER
...
```

规则：

- standard polymer residue block 保持 polymer order；
- 多个 assigned linked units 保持 1.2 正式 residue/object order 所确定的稳定 unit order；
- multi-residue unit 内保持正式 residue order；
- 不按 attachment residue number 重排 linked units；
- 不把 linked unit 插到 attachment residue 紧邻位置；
- 跨多个 standard chain 的 linked unit 保持独立 chain，不进入 standard-chain residue ordering；
- 其它对象保持既有相对 organization。

## 6. Final resid

默认保留 1.3 `resid`。

唯一需要重新编号的主要情况是：归入某条 standard chain 的 topology-linked nonstandard unit。其 residues 按 stable unit / residue order 使用该 final chain 后续可用、不会与保留 residue identity 冲突的新 `resid`。

standard polymer residue 的 `resid` 不因 1.8 reorder 改写。跨多条 standard chain 而保持独立 chain 的 linked unit，以及其它未 reassignment 对象，保持原 `resid`。

## 7. Heavy-atom / PDB organization

1.8 输入与输出 atom set 一致，不新增或删除 atoms。

同一 residue 内保持当前 atom order；不做 force-field-specific ordering。

不修改 coordinates、atom name、residue name、occupancy、B-factor、element 或 formal charge。

final PDB：

- `CRYST1` 当前存在时保留；
- `POLYMER → ATOM`；
- `BRANCHED / NONPOLYMER / WATER → HETATM`；
- standard polymer block 后写 `TER`；
- 每个 linked nonstandard unit 后写 `TER`；
- `ATOM / HETATM / TER` 按实际写出顺序从 1 连续编号。

## 8. Final map

最终 map basename 冻结为：

```text
stage1_final_map.yaml
```

只记录 `stage1_final.pdb` 中实际存在的 heavy atoms，不记录 `TER`、missing-residue placeholder、已删除 atom 或 completion provenance。

atom record 固定保存：

```text
serial
chain_id
resid
residue_name
atom_name
component_id
residue_id
```

此前 freeze 中的：

```text
origin: SOURCE | ADDED_BY_COMPLETION
source_atom_serial
```

已在正式 authoring 讨论中明确取消。completion provenance 继续由真正的上游 owner 保存，1.8 不复制。

## 9. Completion boundary

1.8 只做最小 completion gate，确认 reorder / mapping 已完整执行、atom set 未增删、final PDB 与 map 已成功形成且逐 atom 唯一对应。

Stage 1 总体结构正确性与 force-field compatibility validation 属于 1.9；1.8 不生成独立 validation report。

## 10. Official results

每个 target 的正式结果只有：

```text
stage1_final.pdb
stage1_final_map.yaml
```

二者都登记到项目级：

```text
<project_root>/00_project_records/project_result_index.md
```

真实项目 execution path：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/<task_id>/<target_id>/
```

## 11. Deterministic helper

当前 Skill package 使用一个机械 helper：

```text
01_structure_preparation/1.8_reorder_and_mapping/scripts/build_stage1_final.py
```

它负责 stable identity binding、confirmed topology-effect relation 投影、linked-unit organization、PDB rewrite、serial / resid materialization 与 `stage1_final_map.yaml` 写出；不承担 relation/classification 科学判断。

## 12. Handoff

1.9 只读消费 1.8 final PDB / map 做 Stage 1 final validation。

Stage 2 可在此 heavy-atom identity/order 骨架上建立 force-field-specific all-atom order 和最终 topology organization，但不得反向覆盖 Stage 1 chain identity。

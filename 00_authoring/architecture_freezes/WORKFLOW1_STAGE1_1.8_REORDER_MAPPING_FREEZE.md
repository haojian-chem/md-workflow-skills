# Workflow 1 / Stage 1.8 Reorder and mapping architecture record

Status: **FROZEN AUTHORING RECORD — ACTIVE SKILL GENERATED**

Current runtime authority:

```text
01_structure_preparation/1.8_reorder_and_mapping/SKILL.md
```

本文件保存 1.8 的稳定架构事实。active Skill 生成后，可变执行细节由 current `SKILL.md` / helper 拥有；本文件不维护第二套平行 mutable specification。

## 1. Purpose

1.8 将当前 target 的 current valid heavy-atom structure 整理为 Stage 1 final structure，并建立后续可稳定消费的 heavy-atom identity map。

当前职责收敛为：

```text
final residue / object block organization
+ heavy-atom block preservation
+ TER / atom serial materialization
+ final heavy-atom mapping
```

当前 1.2 已在 topology effect 应用后物化最终 component membership 与 component-level `chain_index`，1.3 直接用该 `chain_index` materialize PDB chain。因此 **1.8 不再重新决定 chain assignment 或 component membership**。

## 2. Inputs

每个 target 的正式输入：

- current valid heavy-atom PDB；
- 1.3 对应 `targets/target_xxx.yaml`；
- 1.2 正式 `classification_result.yaml`，当前接口为 `schema_version: "4.0"` 且 `result_status: COMPLETE`。

1.8 直接消费：

```text
components[]
component_id
component-level chain_index
components[].residues[]
component_id + residue_id
polymer_class.value
topology_class.value
topology_linked_checks[]
```

`residue_id` 只在所属 `component_id` 内唯一；下游 stable residue identity 必须使用 `component_id + residue_id`。

1.6 `completion_report.yaml`、1.7 `protonation_assignment_report.yaml` 与 `relation_decisions.yaml` 不作为强制输入。

## 3. Reuse

1.8 **不设置 reuse**。

## 4. Chain / resid boundary

1.8 保留 1.3 已根据 1.2 component `chain_index` materialize 的 PDB chain ID。

1.8 不重新编号 residue `resid`。object block reorder 与 PDB residue number 是两个层次；final order 不要求 `resid` 重新单调排列。

1.8 只重新 materialize `ATOM / HETATM / TER` serial。

## 5. Linked nonstandard block

1.8 为 Stage 1 PDB object organization 建立 linked nonstandard block；这不是 Stage 2 的 2.3 processing unit。

对当前 target 中 `TOPOLOGY_LINKED_NONSTANDARD` residues：

- 只使用 `topology_linked_checks[]` 中 `judgment: CONFIRMED` 且 `topology_effect_applied: true` 的关系；
- 只有关系两端都属于 linked nonstandard residue 时，才把两端合并到同一 1.8 linked block；
- 两个 nonstandard residues 仅共享同一个 standard-side endpoint 时，不自动合并为同一 block；
- 没有 direct nonstandard–nonstandard topology-effect relation 的 linked residue 自成一个 block；
- block 内 residue 采用 1.2 component `residues[]` 正式顺序。

同一 linked block 应属于同一个 final `component_id`；否则视为上游正式接口不一致。

## 6. Residue / object order

稳定顺序基准：

```text
1.2 components[] 顺序
→ component 内 residues[] 顺序
```

包含 standard polymer residue 的 component：

```text
standard polymer residue block
TER
linked nonstandard block 1
TER
linked nonstandard block 2
TER
...
```

多个 linked blocks 按其中最早 residue 的 1.2 正式顺序排列，不按 attachment residue number 排序。

不含 standard polymer residue 的 component 不为了形成 standard block 额外重排；只保证 multi-residue linked block 连续并保持正式 block order。

## 7. Heavy-atom / PDB organization

1.8 输入与输出 atom set 一致，不新增或删除 atoms。

同一 residue 内保持当前 atom order；不做 force-field-specific ordering。

不修改 coordinates、atom name、residue name、occupancy、B-factor、element 或 formal charge。

final PDB：

- `CRYST1` 当前存在时保留；
- `POLYMER → ATOM`；
- `BRANCHED / NONPOLYMER / WATER → HETATM`；
- selected standard polymer block 后写 `TER`；
- 每个 linked nonstandard block 后写 `TER`；
- 保留 1.3 selection 形成的 polymer segment boundary；
- `ATOM / HETATM / TER` 按最终写出顺序从 1 连续编号。

## 8. Final map

最终 map：

```text
stage1_final_map.yaml
```

只记录 `stage1_final.pdb` 中实际存在的 heavy atoms。

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

`component_id + residue_id` 共同构成 residue stable identity。

不记录 `origin`、`source_atom_serial`、missing placeholder 或 completion provenance。

## 9. Completion boundary

1.8 只做最小 completion gate，确认 reorder / mapping 已完整执行、atom set 未增删、final PDB 与 map 已成功形成且逐 atom 唯一对应。

Stage 1 总体验证属于 1.9；1.8 不生成独立 validation report。

## 10. Official results

每个 target 正式结果只有：

```text
stage1_final.pdb
stage1_final_map.yaml
```

二者均登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

execution path：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/<task_id>/<target_id>/
```

## 11. Deterministic helper

当前机械 materialization helper：

```text
01_structure_preparation/1.8_reorder_and_mapping/scripts/build_stage1_final.py
```

它读取 1.2 v4 + 1.3 target mapping，执行 stable identity binding、linked-block construction、block reorder、TER / serial materialization 与 final map 写出；不承担 classification、relation judgment、component membership 或 chain assignment。

## 12. Handoff

1.9 只读消费 1.8 final PDB / map 做 Stage 1 final validation。

Stage 2 可以基于此 heavy-atom identity / order 骨架建立 force-field-specific all-atom order 与最终 topology organization，但不反向改写 Stage 1 structure identity。

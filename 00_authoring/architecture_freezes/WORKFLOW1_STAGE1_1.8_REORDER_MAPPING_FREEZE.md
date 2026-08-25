# Workflow 1 / Stage 1.8 Reorder and mapping architecture record

Status: **FROZEN AUTHORING RECORD — ACTIVE SKILL GENERATED**

Current runtime authority:

```text
01_structure_preparation/1.8_reorder_and_mapping/SKILL.md
```

Stage 1 原子映射 authority：

```text
references/atom_mapping_rules.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md
```

本文件只保存 1.8 的稳定架构事实；具体执行指导由 current `SKILL.md` 拥有。

## 1. Purpose

1.8 将当前 target 已完成前序结构准备的有效重原子结构整理为 Stage 1 最终 PDB，并把前序持续维护的原子映射更新为最终 `stage1_final_map.yaml`。

1.8 拥有：

```text
final chain organization
+ final resid adjustment
+ residue / component order
+ TER / PDB serial organization
+ chained atom-map finalization
```

1.3 target PDB 中的 chain ID、`resid` 与排列用于 1.4–1.7 的稳定中间结构表示，不构成 Stage 1 最终 PDB 组织。1.2 component-level `chain_index` 是逻辑 chain/group 编号，也不直接等同于 final PDB chain identity。

## 2. Inputs

每个 target 的正式输入：

- 当前有效重原子 PDB；
- 与该 PDB 一一对应的最近正式 Stage 1 原子映射；
- 1.3 对应 `targets/target_xxx.yaml`；
- 1.2 正式 `classification_result.yaml`，当前接口为 `schema_version: "4.0"` 且 `result_status: COMPLETE`。

1.8 不允许绕过当前输入原子映射，再从 current PDB 重新构造 atom provenance 或 stable residue identity。

稳定 residue identity 始终使用：

```text
component_id + residue_id
```

final chain 组织还需要读取 1.2 residue 的 `current_chain_id`、正式 residue order、`topology_class.value` 与 `topology_linked_checks[]`。

## 3. Reuse

1.8 不设置 reuse。

## 4. 总体处理与排列顺序

1.8 的处理顺序同时作为 final PDB 的类别顺序：

```text
STANDARD_RESIDUE
→ TOPOLOGY_LINKED_NONSTANDARD
→ INDEPENDENT_NONSTANDARD
→ SOLVENT_COMPONENT
→ ION_COMPONENT
```

不得以 1.2 `components[]` 的全局顺序替代该类别顺序。

## 5. STANDARD_RESIDUE

standard residues 按实际所属 polymer chain 组织：

- 同一 polymer chain 使用同一 final chain ID；
- 不同 polymer chains 不合并；
- chain 内保持真实 residue sequence order；
- selection 造成的真实 polymer segment boundary 保留。

final chain ID 能合法、无歧义地继续使用现有表示时可以保留；否则在 1.8 重新分配。

final `resid` 与 chain 组织同步确定。现有编号在所属 final chain 内无冲突且能保持 residue order 时原则上保留；chain 重组造成冲突或当前编号不能可靠表示最终 residue identity 时，由 1.8 在该 final chain 内按真实 residue order 调整。

## 6. TOPOLOGY_LINKED_NONSTANDARD

只使用 1.2 `topology_linked_checks[]` 中同时满足：

```text
judgment: CONFIRMED
topology_effect_applied: true
```

的关系。

一个 topology-linked nonstandard 单元的稳定边界：

- 两个 `TOPOLOGY_LINKED_NONSTANDARD` residues 之间存在上述直接关系时属于同一单元；
- 这种 nonstandard–nonstandard 关系连续连接的 residues 属于同一单元；
- 两个 nonstandard residues 仅分别连接同一个 standard residue 时，不因此自动合并；
- 没有与其它 linked nonstandard residue 建立上述关系的 residue 自成一个单元。

对每个单元，检查其通过正式 topology-linked 关系涉及的全部 `STANDARD_RESIDUE` 属于哪些 polymer chains：

- 至少涉及一个 standard residue，且这些 standard residues 全部属于同一条 polymer chain → 使用该 polymer chain 的 final chain ID；
- 涉及的 standard residues 分属于多条 polymer chains → 使用独立 final chain；
- 没有涉及 standard residue → 使用独立 final chain。

所有 topology-linked nonstandard 单元都在总体顺序的 `TOPOLOGY_LINKED_NONSTANDARD` 部分写出，不插入 attachment residue 邻近位置。

使用某条 polymer chain ID 的 linked residues 在该 chain standard-residue `resid` 之后继续分配不冲突的 `resid`；独立 linked chain 在自身 chain 内按单元 residue order 分配不冲突的 `resid`。

## 7. INDEPENDENT_NONSTANDARD / SOLVENT_COMPONENT / ION_COMPONENT

`INDEPENDENT_NONSTANDARD` 以 `component_id` 保持独立 component 边界；同一 component 内 residue 连续并保持 1.2 正式 residue order，不把不同 independent components 合并成同一个化学对象。

`SOLVENT_COMPONENT` 在 independent nonstandard 之后处理，`ION_COMPONENT` 最后处理。二者不因 component-level `chain_index` 被解释为 polymer chain；同一类别可共用 final chain，不要求每个 component 单独占用一个 PDB chain ID。

各 final chain 内 `resid` 均按最终对象顺序确定并避免冲突。

## 8. Heavy-atom / PDB organization

1.8 输入与输出 atom set 一致，不新增或删除 atoms。

同一 residue 内保持进入 1.8 时的 atom order；不做 force-field-specific atom ordering。

不修改 coordinates、atom name、residue name、occupancy、B-factor、element 或 formal charge。

final PDB：

- `CRYST1` 当前存在有效晶胞信息时保留；
- `POLYMER → ATOM`；
- `BRANCHED / NONPOLYMER / WATER → HETATM`；
- `TER` 表示已经确定的 polymer segment、topology-linked nonstandard 单元、independent nonstandard component 或其它明确对象边界；
- `ATOM / HETATM / TER` 按最终写出顺序从 1 连续、唯一编号。

## 9. Final map

最终 map：

```text
stage1_final_map.yaml
```

它是 current input map 的最终 copy-and-update 结果，使用 `references/atom_mapping_rules.md` 的统一数据结构，不建立第二套 final-map schema。

1.8 保持 input map 中所有 surviving atom 的：

```text
original_atom_serial
component_id + residue_id
operations
```

并按 final PDB 更新 `current_atom_serial`。因本步骤 residue / component organization 而实际改变 atom-record 写出位置的 atoms 追加 `1.8REORDER`；单纯 serial 重编号不追加 operation。

final chain ID 与 `resid` 作为当前 PDB 表示通过 `current_atom_serial` 与 final map 对应，不另建永久 atom identity 字段。

## 10. Completion boundary and official results

1.8 只确认自身 final organization 与 final-map 生成完整，不承担 Stage 1 独立终检；Stage 1 final validation 属于 1.9。

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

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

1.8 负责：

```text
最终 chain 组织
+ 最终 resid 调整
+ 残基 / component 排列
+ TER / PDB serial 整理
+ 最终原子映射生成
```

1.3 target PDB 中的 chain ID、`resid` 与排列用于 1.4–1.7 的稳定中间结构表示，不构成 Stage 1 最终 PDB 组织。1.2 component 一级 `chain_index` 是逻辑 chain/group 编号，也不直接等同于最终 PDB chain identity。

## 2. Inputs

每个 target 的正式输入：

- 当前有效重原子 PDB；
- 与该 PDB 一一对应的最近正式 Stage 1 原子映射；
- 1.3 对应 `targets/target_xxx.yaml`；
- 1.2 正式 `classification_result.yaml`，当前接口为 `schema_version: "4.0"` 且 `result_status: COMPLETE`。

1.8 不允许绕过当前输入原子映射，再从当前 PDB 重新构造原子来源追踪信息或稳定残基身份。

稳定残基身份始终使用：

```text
component_id + residue_id
```

最终 chain 组织还需要读取 1.2 residue 的 `current_chain_id`、正式 residue order、`topology_class.value` 与 `topology_linked_checks[]`。

## 3. Reuse

1.8 不设置 reuse。

## 4. 总体处理与排列顺序

1.8 的处理顺序同时作为最终 PDB 的类别顺序：

```text
STANDARD_RESIDUE
→ TOPOLOGY_LINKED_NONSTANDARD
→ INDEPENDENT_NONSTANDARD
→ SOLVENT_COMPONENT
→ ION_COMPONENT
```

不得以 1.2 `components[]` 的全局顺序替代该类别顺序。

需要新分配 PDB chain ID 时，按上述处理顺序及同类对象的稳定顺序，从：

```text
A-Z → a-z → 0-9
```

中选择尚未占用的合法 chain ID。已有 chain ID 能合法、无歧义表达最终 chain 组织时可以保留。若所需独立 chain 数量超过 PDB 能可靠表示的范围，不得静默合并不同 chain。

## 5. `STANDARD_RESIDUE`

标准残基按实际所属聚合物链组织：

- 同一聚合物链使用同一最终 chain ID；
- 不同聚合物链不合并；
- chain 内保持真实 residue sequence order；
- selection 造成的真实聚合物区段边界保留。

最终 chain ID 能合法、无歧义地继续使用现有表示时可以保留；否则在 1.8 重新分配。

最终 `resid` 与 chain 组织同步确定：现有编号在所属最终 chain 内无冲突且能保持 residue order 时原则上保留；需要重新编号时，该 final chain 按真实 residue order 从 `1` 开始连续编号。同一 final chain 内的 `TER` 不使 `resid` 重新从 `1` 开始。

## 6. `TOPOLOGY_LINKED_NONSTANDARD`

只使用 1.2 `topology_linked_checks[]` 中同时满足：

```text
judgment: CONFIRMED
topology_effect_applied: true
```

的关系。

一个 topology-linked 非标准单元的稳定边界：

- 两个 `TOPOLOGY_LINKED_NONSTANDARD` residues 之间存在上述直接关系时属于同一单元；
- 这种非标准残基之间的关系连续连接的 residues 属于同一单元；
- 两个非标准残基仅分别连接同一个标准残基时，不因此自动合并；
- 没有与其它 topology-linked 非标准 residue 建立上述关系的 residue 自成一个单元。

对每个单元，检查其通过正式 topology-linked 关系涉及的全部 `STANDARD_RESIDUE` 属于哪些聚合物链：

- 至少涉及一个标准残基，且这些标准残基全部属于同一条聚合物链 → 使用该聚合物链的最终 chain ID；
- 涉及的标准残基分属于多条聚合物链 → 使用独立 chain；
- 没有涉及标准残基 → 使用独立 chain。

所有 topology-linked 非标准单元都在总体顺序的 `TOPOLOGY_LINKED_NONSTANDARD` 部分写出，不插入与其发生 topology-linked 关系的标准残基旁边。

使用某条聚合物链 chain ID 的 topology-linked 非标准残基，从该 chain 标准残基最后占用的 `resid + 1` 开始连续分配；后续同 chain 单元继续递增。独立 topology-linked chain 从 `resid = 1` 开始按单元 residue order 连续分配。

## 7. `INDEPENDENT_NONSTANDARD` / `SOLVENT_COMPONENT` / `ION_COMPONENT`

`INDEPENDENT_NONSTANDARD` 以 `component_id` 保持独立 component 边界；同一 component 内 residue 连续并保持 1.2 正式 residue order，不把不同独立非标准 components 合并成同一个化学对象。

每个独立非标准 component 使用独立 final chain，并从 `resid = 1` 开始按 component 内 residue order 连续编号。

`SOLVENT_COMPONENT` 在独立非标准 components 之后处理，`ION_COMPONENT` 最后处理。二者不因 component-level `chain_index` 被解释为聚合物链；同一类别可共用 chain，不要求每个 component 单独占用一个 PDB chain ID。每个新 final chain 的 `resid` 从 `1` 开始，按最终写出顺序连续编号。

## 8. 重原子与 PDB 组织

1.8 输入与输出 atom set 一致，不新增或删除 atoms。

同一 residue 内保持进入 1.8 时的 atom order；不做力场特定的 atom ordering。

不修改 coordinates、atom name、residue name、occupancy、B-factor、element 或 formal charge。

最终 PDB：

- `CRYST1` 当前存在有效晶胞信息时保留；
- `POLYMER → ATOM`；
- `BRANCHED / NONPOLYMER / WATER → HETATM`；
- `TER` 表示已经确定的聚合物区段、topology-linked 非标准单元、独立非标准 component 或其它明确对象边界；
- `ATOM / HETATM / TER` 按最终写出顺序从 1 连续、唯一编号。

## 9. Final map

最终原子映射文件为：

```text
stage1_final_map.yaml
```

它是当前输入原子映射的最终复制并更新结果，使用 `references/atom_mapping_rules.md` 的统一数据结构，不建立第二套 final-map schema。

1.8 保持输入原子映射中所有保留 atom 的：

```text
original_atom_serial
component_id + residue_id
operations
```

并按最终 PDB 更新 `current_atom_serial`。因本步骤 residue / component organization 而实际改变 atom-record 写出位置的 atoms 追加 `1.8REORDER`；单纯 serial 重编号不追加 operation。

最终 chain ID 与 `resid` 作为当前 PDB 表示，通过 `current_atom_serial` 与最终原子映射对应，不另建永久 atom identity 字段。

## 10. Completion boundary and official results

1.8 只确认自身最终结构组织与最终原子映射生成完整，不承担 Stage 1 独立终检；Stage 1 final validation 属于 1.9。

每个 target 正式结果只有：

```text
stage1_final.pdb
stage1_final_map.yaml
```

二者均登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

执行路径：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/<task_id>/<target_id>/
```
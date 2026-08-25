---
name: reorder_and_mapping
description: 结构准备 1.8。将当前 target 的有效重原子结构整理为 Stage 1 最终 PDB，完成最终 chain 组织、resid 调整、残基与组分排序、TER 与 serial 整理，并在前序原子映射基础上生成 stage1_final_map.yaml。
---

# 1.8 Reorder and mapping

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

Stage 1 原子映射维护规则读取：

`../../references/atom_mapping_rules.md`

1.8 的最终结构整理与 `stage1_final_map.yaml` 维护必须遵循该共享规则。

本 Skill 只定义 1.8 自身的对象、最终结构组织规则、完成条件与正式结果；本步骤不设置 reuse。

## Purpose

1.8 的职责是把当前 target 已完成前序结构准备的重原子结构整理为 Stage 1 最终 PDB，并把前序持续维护的原子映射更新为最终 `stage1_final_map.yaml`。

1.8 拥有当前 target 的：

- 最终 PDB chain 组织；
- 与最终 chain 组织同步确定的 `resid`；
- 残基与组分的最终排列；
- `TER` 整理；
- PDB `ATOM / HETATM / TER` serial 重编号；
- 最终原子映射文件生成。

1.3 生成的 target PDB 为 1.4–1.7 提供稳定的中间结构表示；其中的 PDB chain ID、`resid` 和排列不构成 Stage 1 最终结构组织规则。1.2 component 一级 `chain_index` 是逻辑 chain/group 编号，也不直接等同于 Stage 1 最终 PDB chain identity。

1.8 不重新执行 structure repair、protonation assignment、classification 或 topology-linked judgment，也不增加 force-field-specific all-atom ordering。

## Object requirements

每个 target 至少需要：

- 当前 target 的有效重原子 PDB；
- 与该 PDB 一一对应的最近正式原子映射文件；
- 1.3 对应 `targets/target_xxx.yaml`；
- 与该 target 对应的 1.2 正式 `classification_result.yaml`，当前要求 `schema_version: "4.0"` 且 `result_status: COMPLETE`。

当前原子映射文件是 1.8 追踪现有原子身份的直接依据。不得跳过该文件、再根据当前 PDB 的 chain、`resid`、residue name、atom name 或 atom order 重新猜测原子来源。

1.8 从 1.2 正式结果读取当前组织所需的信息，包括：

```text
component_id
residue_id
current_chain_id
components[].residues[] 顺序
polymer_class.value
topology_class.value
topology_linked_checks[]
```

`component_id + residue_id` 共同定位 1.2 中的稳定 residue identity。`chain_index` 可以用于理解 1.2 的 component 组织和 1.3 的中间表示，但不得作为最终 PDB chain identity 的替代判据。

1.3 target 记录用于确认当前 target 的 selection 以及其中已经建立的中间 residue mapping；最终 chain / `resid` 由本步骤重新组织后，以 `stage1_final.pdb` 与最终原子映射共同确定。

## No reuse

1.8 不设置 reuse。

每次实际进入 1.8，都基于当前 target 的当前结构、与其对应的当前原子映射、当前 1.3 target 记录和当前正式 1.2 结果重新生成正式结果。

## Work directory and multiple targets

真实项目基础目录：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/
```

每个 target 独立执行：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/<task_id>/<target_id>/
├── stage1_final.pdb
└── stage1_final_map.yaml
```

1.8 不改变 target 数量。

## Execution rules

### 1. 原子身份与映射基础

先确认当前 PDB 中每个 `ATOM / HETATM` 都能通过当前原子映射文件唯一对应到：

```text
current_atom_serial
→ component_id + residue_id
```

后续 chain、`resid` 和排列变化都不得改变该 residue stable identity。

1.8 以输入原子映射为基础维护最终映射，不重新建立另一套 provenance。

### 2. 处理顺序与最终 PDB 总体顺序

1.8 的处理顺序同时作为最终 PDB 的类别排列顺序：

```text
STANDARD_RESIDUE
→ TOPOLOGY_LINKED_NONSTANDARD
→ INDEPENDENT_NONSTANDARD
→ SOLVENT_COMPONENT
→ ION_COMPONENT
```

前一类完成后的 chain / `resid` 占用是后一类处理时的已知结构条件。

不得继续以 `components[]` 的全局顺序直接替代上述类别顺序。类别内部在不违反本 Skill 其它组织规则的前提下，优先保持当前 target 中已有的稳定相对顺序。

### 3. STANDARD_RESIDUE

先处理全部 `STANDARD_RESIDUE`。

执行 Agent 根据 1.2 每个 residue 的 `current_chain_id`、正式 residue 顺序以及当前 target 的实际 polymer context 确定 standard residues 所属的 polymer chain。

必须满足：

- 属于同一条 polymer chain 的 standard residues 在最终 PDB 中使用同一 chain ID；
- 属于不同 polymer chains 的 standard residues 不合并为同一 final chain；
- 同一 polymer chain 内保持实际 residue sequence order；
- 1.3 selection 造成的真实 polymer segment boundary 保留为结构边界，不因为最终 chain ID 相同而把不连续 selected segments 伪装成连续 polymer segment。

最终 chain ID 应能够在 PDB 中合法且无歧义地表示这些 polymer chains。现有 chain ID 能满足最终组织要求时可以保留；存在冲突、空值或不能正确表达最终 chain 组织时，由执行 Agent重新分配合法且不冲突的 PDB chain ID。

在最终 chain 确定后同步确定 standard residues 的 final `resid`。现有 `resid` 在所属 final chain 内无冲突且能够保持 residue order 时原则上保留；如果 chain 重组造成冲突或当前编号不能可靠表示最终 residue identity，则在该 final chain 内按实际 residue order 重新编号。不得只为了让编号连续或外观整齐而无必要改写所有 standard-residue `resid`。

### 4. TOPOLOGY_LINKED_NONSTANDARD 单元

处理 `TOPOLOGY_LINKED_NONSTANDARD` 时，只使用 1.2 `topology_linked_checks[]` 中同时满足：

```text
judgment: CONFIRMED
topology_effect_applied: true
```

的正式关系。

一个 topology-linked nonstandard 单元按以下规则确定：

- 两个 `TOPOLOGY_LINKED_NONSTANDARD` residues 之间存在上述直接关系时，它们属于同一个单元；
- 这种 nonstandard–nonstandard 关系连续连接形成的 residues 属于同一个单元；
- 两个 nonstandard residues 仅分别与同一个 standard residue 建立关系，但彼此没有上述 nonstandard–nonstandard 关系时，不因此合并为同一个单元；
- 没有与其它 `TOPOLOGY_LINKED_NONSTANDARD` residue 建立上述关系的 residue，自身形成一个单元；
- 单元内部 residue 保持 1.2 正式 residue order。

对每个 topology-linked nonstandard 单元，收集该单元通过上述正式关系实际涉及的全部 `STANDARD_RESIDUE`，再检查这些 standard residues 分别属于哪些 polymer chains：

- 如果涉及至少一个 standard residue，且所有这些 standard residues 都属于同一条 polymer chain，则该 topology-linked nonstandard 单元在最终 PDB 中使用这条 polymer chain 的 final chain ID；
- 如果涉及的 standard residues 分属于多条 polymer chains，则该 topology-linked nonstandard 单元使用独立 final chain；
- 如果该单元没有涉及任何 standard residue，则该单元使用独立 final chain。

使用某条 polymer chain ID 的 topology-linked nonstandard 单元仍在总体顺序中的 `TOPOLOGY_LINKED_NONSTANDARD` 部分写出，不插入到与其发生 topology-linked 关系的 standard residue 旁边。

多个 topology-linked nonstandard 单元使用同一条 polymer chain ID 时，各单元保持独立边界，并按其在当前 target 中首次出现的稳定顺序排列。

`resid` 与 chain 组织同步处理：

- 使用某条 polymer chain ID 的 topology-linked nonstandard residues，在该 chain 已有 standard-residue `resid` 之后按单元及单元内 residue 顺序继续分配不冲突的 `resid`；
- 使用独立 chain 的 topology-linked nonstandard 单元，在其独立 chain 内按单元内 residue order 分配不冲突的 `resid`；
- 不为了保留 1.3 的中间编号而制造 final chain 内的 `resid` 冲突。

### 5. INDEPENDENT_NONSTANDARD

全部 topology-linked nonstandard 单元处理完成后，再处理 `INDEPENDENT_NONSTANDARD`。

同一 `component_id` 下属于 `INDEPENDENT_NONSTANDARD` 的 residues 作为同一个独立 component 保持连续，并保持其在 1.2 中的正式 residue order。不同 independent nonstandard components 不因为属于同一 topology class 而合并为同一个化学对象。

每个 independent nonstandard component 使用独立于 standard polymer chains 和 topology-linked independent chains 的 final chain 表示；chain ID 必须合法且不与已有 final chain 组织产生歧义。

其 `resid` 在所属 final chain 内按 component 内 residue order 分配且不得冲突。不同 independent nonstandard components 的总体顺序优先沿用它们在当前 target 中首次出现的顺序。

### 6. SOLVENT_COMPONENT 与 ION_COMPONENT

在 independent nonstandard components 之后处理 `SOLVENT_COMPONENT`，最后处理 `ION_COMPONENT`。

两类对象都不得因为当前 1.2 component-level `chain_index` 而被强制解释为 polymer chain。

默认组织原则：

- solvent 与 ion 分别使用独立于前述类别的 chain 表示；
- 同一类别内部保持当前 target 的 residue 顺序；
- 同一类别可以共用一个 final chain，不要求每个 component 单独消耗一个 PDB chain ID；
- `resid` 在各自 final chain 内按最终写出顺序分配且不得冲突。

如果当前 PDB 表示或用户明确要求需要把同类对象拆成多个 chain，执行 Agent 可以在保持类别顺序、对象身份和映射连续性的前提下处理；不得因此改变 residue 分类或 component identity。

### 7. Residue 内原子顺序与不可变内容

1.8 只改变最终结构组织和表示。

同一 residue 内：

- 重原子保持连续；
- 保持进入 1.8 时的 atom order；
- 不按 CCD、力场模板、字母顺序或未来 topology 需要重新排列原子。

1.8 不新增或删除 atoms，也不修改：

- coordinates；
- atom name；
- residue name；
- occupancy；
- B-factor；
- element；
- formal charge。

### 8. PDB 写出

最终 PDB 保留当前 Stage 1 需要的 records：

```text
CRYST1   # 当前结构存在有效晶胞信息时
ATOM
HETATM
TER
END
```

`ATOM / HETATM` 按 1.2 `polymer_class.value` 写出：

```text
POLYMER    → ATOM
BRANCHED   → HETATM
NONPOLYMER → HETATM
WATER      → HETATM
```

`TER` 用于表示最终 PDB 中已经确定的 polymer segment、topology-linked nonstandard 单元、independent nonstandard component 或其它明确对象边界；`TER` 本身不改变 residue stable identity。

完成最终 chain、`resid` 和残基/组分排列后，`ATOM / HETATM / TER` serial 按实际写出顺序从 1 连续、唯一地重新编号。

### 9. 生成 `stage1_final_map.yaml`

`stage1_final_map.yaml` 是输入原子映射的最终 copy-and-update 结果，数据结构由：

`../../references/atom_mapping_rules.md`

统一拥有。

1.8 必须：

- 完整保留输入原子映射中每个 surviving atom 的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`；
- 不新增或删除 atom record；
- 按 `stage1_final.pdb` 更新每个 record 的 `current_atom_serial`；
- 对因本步骤 residue / component organization 而实际改变 atom-record 写出位置的 atoms 追加 `1.8REORDER`；
- 单纯 serial 重编号不追加 operation；
- 不重新解释或改写此前 `1.3ADD / 1.4ALTLOC / 1.6ADD / 1.6RENAME / 1.6REPLACE / 1.7RENAME` history；
- 不为 final chain ID 或 `resid` 另建第二套永久 atom identity 字段。

最终 PDB 的 chain ID、`resid`、residue name 与 atom name 通过 `stage1_final_map.yaml.current_atom_serial` 对应到 `stage1_final.pdb` 当前原子记录；稳定 residue identity 继续由 map 中的 `component_id + residue_id` 表示。

## Completion requirements

1.8 不承担 Stage 1 独立终检；1.9 对 `stage1_final.pdb` 与 `stage1_final_map.yaml` 进行只读终检。

当前 target 标记 1.8 已完成前至少确认：

- 输入 PDB 与输入原子映射一一对应；
- 所有最终 PDB atoms 都保持原有 `component_id + residue_id` 身份；
- final PDB 的类别顺序为 `STANDARD_RESIDUE → TOPOLOGY_LINKED_NONSTANDARD → INDEPENDENT_NONSTANDARD → SOLVENT_COMPONENT → ION_COMPONENT`；
- standard polymer chains、topology-linked nonstandard 单元和 independent nonstandard components 的 final chain 组织符合本 Skill 规则；
- final chain 内没有 `resid` 冲突；
- residue 内 atom order 未改变；
- 本步骤没有新增、删除或修改不允许改变的原子属性；
- `ATOM / HETATM / TER` serial 连续且唯一；
- final PDB 中每个 `ATOM / HETATM` 恰有一条 final-map record，final map 无额外 atom record；
- 原有 operation history 未丢失或改写，`1.8REORDER` 只用于本步骤实际造成的写出位置变化；
- `stage1_final.pdb` 与 `stage1_final_map.yaml` 均已成功生成。

1.8 不生成独立 validation report，也不以本步骤完成检查替代 1.9。

## Official results

每个 target 的正式结果只有：

```text
stage1_final.pdb
stage1_final_map.yaml
```

完成后，把这两个文件的完整绝对路径和对应 target 说明登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

不登记内部临时文件，也不生成额外 mapping validation 文件。

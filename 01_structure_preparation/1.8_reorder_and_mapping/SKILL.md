---
name: reorder_and_mapping
description: Stage 1.8 Reorder and mapping。把当前 target 的有效重原子结构按 1.2/1.3 已确定的 component / chain identity 完成最终 object organization，并生成 Stage 1 final PDB 与最终 atom map。
---

# 1.8 Reorder and mapping

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

Stage 1 原子映射维护规则读取：

`../../references/atom_mapping_rules.md`

1.8 的 reorder、serial materialization 与 final atom map 必须遵循该共享规则。

本 Skill 仅补充 1.8-specific 的对象、执行、completion gate 与 results 规则；本步骤明确不设置 reuse。

## Purpose

将当前 target 已完成前序结构准备的 **current valid heavy-atom structure** 整理为 Stage 1 最终结构，并把前序持续维护的 atom map 更新为最终 `stage1_final_map.yaml`。

```text
current heavy-atom structure
+ current atom map
+ 1.3 target mapping
+ 1.2 final component / residue / topology-linked records
↓
final residue / object block organization
↓
TER + PDB serial materialization
↓
stage1_final.pdb + stage1_final_map.yaml
```

当前 1.2 已在全部 topology effect 应用后物化最终 `component_id`、component 一级 `chain_index` 与 component membership；1.3 又直接把该 `chain_index` materialize 为 PDB chain ID。因此 1.8 **不重新决定 chain assignment，也不重新计算 component membership**。

1.8 不重新做 structure repair、protonation assignment、classification、topology-linked judgment 或 force-field-specific all-atom ordering。

## Object requirements

每个 target 至少需要：

- 当前 target 的 current valid heavy-atom PDB；
- 与该 PDB 一一对应的最近正式 atom map；
- 1.3 对应 `targets/target_xxx.yaml`；
- 与该 target 对应的 1.2 正式 `classification_result.yaml`，当前要求 `schema_version: "4.0"` 且 `result_status: COMPLETE`。

1.8 不允许跳过当前输入 atom map、再从 current PDB 重新构造一套新的 atom provenance。

1.8 直接消费当前 1.2：

```text
components[] 顺序
component_id
component-level chain_index
components[].residues[] 顺序
component_id + residue_id
polymer_class.value
topology_class.value
topology_linked_checks[]
```

`residue_id` 只在所属 `component_id` 内唯一，因此 1.8 中 residue stable identity 始终使用：

```text
component_id + residue_id
```

不得仅用 `residue_id` 建立跨 component 映射，也不得根据 residue name、atom name、chain 或 resid 重新构造这些 opaque IDs。

1.6 `completion_report.yaml`、1.7 `protonation_assignment_report.yaml` 和 `relation_decisions.yaml` 不是 1.8 的强制输入；已经落实的结构变化由 current structure 和与之对应的 current atom map 体现，人工 relation decision 已反映到 1.2 正式结果。

## No reuse

1.8 **不设置 reuse**。

每次实际进入 1.8，都基于当前 target 的 current structure、current atom map、当前 1.3 target mapping 与当前正式 1.2 result 重新生成结果。

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

1.8 不决定 target 数量；multiple targets 由 1.3 已完成的 selection 结果确定。

## Preflight

正式写出前确认：

- current structure、current atom map、target record、classification result 均可读；
- current structure 是本步骤预期的 heavy-atom PDB；1.8 不通过删除 H 修正错误输入；
- current atom map 与 current structure 的 `ATOM / HETATM` 一一对应；
- current atom map 中每条 `component_id + residue_id` 均可定位到当前 1.2 正式 residue；
- 1.3 `chain_mapping + residue_mapping` 能把当前 PDB residue 唯一绑定到 `component_id + residue_id`；
- target 中所有 `component_id + residue_id` 均存在于当前 1.2 `components[].residues[]`；
- target `chain_index` 与对应 1.2 component 一级 `chain_index` 一致；
- 1.2 `topology_linked_checks[]` 已闭合，1.8 只消费 `judgment: CONFIRMED` 且 `topology_effect_applied: true` 的正式关系；
- 输出目录属于当前 Task / target，且不会覆盖其它 target 的正式结果。

## Execution rules

### 1. Stable identity binding

先建立：

```text
current PDB atom serial
↔ current atom map
↔ component_id + residue_id
↔ 1.3 chain_index + resid
```

其中 `chain_index` 直接来自 1.2 component 一级正式字段。

后续所有 reorder / map 操作都沿用 current atom map 中已有的 `original_atom_serial`、`component_id + residue_id` 和 `operations` history。

### 2. Chain 与 resid 保持

1.8 不重新分 chain。

final PDB chain ID 继续使用 1.3 已按 1.2 component `chain_index` materialize 的 PDB chain ID。

1.8 也不重新编号 residue `resid`。即使 object block 在本步骤发生位置移动，仍保留 1.3 已写入当前 target 的 `resid`；final object order 不要求 resid 数值重新单调排列。

因此 1.8 只重新生成 atom / TER serial，不重新生成 chain ID 或 resid。

### 3. 1.8 linked nonstandard block

1.8 需要区分 linked nonstandard object boundary，以便组织 block 和写 `TER`。这里的 block 只属于 **Stage 1 PDB organization**，不定义或替代其它阶段的 processing unit。

对当前 target 中 `topology_class.value: TOPOLOGY_LINKED_NONSTANDARD` 的 residue：

- `topology_linked_checks[]` 中 `judgment: CONFIRMED` 且 `topology_effect_applied: true` 的记录才参与 block relation；
- 只有当关系两端都属于 `TOPOLOGY_LINKED_NONSTANDARD` residue 时，才把两端合并为同一个 1.8 linked block；
- 通过同一个 standard residue 分别连接的两个 nonstandard residues，不因为共享 standard-side endpoint 自动合并成一个 block；
- 没有与其它 nonstandard residue形成上述直接 topology-effect relation 的 linked nonstandard residue，自身形成一个 block；
- 一个 block 内 residue 按 1.2 `components[].residues[]` 的正式顺序排列。

由于 1.2 已经应用 topology effect 并形成最终 component membership，同一个 1.8 linked block 应属于同一个 final `component_id`；若正式结果违反这一点，视为上游 interface inconsistency，不在 1.8 猜测修复。

### 4. Residue / object organization

正式稳定顺序基准为：

```text
1.2 components[] 顺序
→ component 内 residues[] 顺序
```

对于包含 standard polymer residue 的 component：

```text
standard polymer residue block
→ linked nonstandard block 1
→ linked nonstandard block 2
→ ...
```

规则：

- standard polymer residues 保持 1.2 正式 residue 顺序；
- linked blocks 按其中最早 residue 在 1.2 正式顺序中的位置确定稳定 block order；
- multi-residue linked block 内保持 1.2 正式 residue 顺序；
- 不按 attachment residue number 重新排序 linked blocks；
- 不把 linked block 插到 attachment residue 紧邻位置；
- 除被移动的 linked nonstandard blocks 外，其余 residues 保持 1.2 / 1.3 已建立的正式相对顺序。

对于不含 standard polymer residue 的 component，不为了形成“standard block”额外重排；只在需要时保持同一个 multi-residue linked block 连续，并保持正式 residue / block order。

### 5. Heavy-atom order and immutable fields

1.8 只做 residue / object block-level organization。

同一 residue 内：

- heavy atoms 保持连续；
- 保持进入 1.8 时的 atom order；
- 不按 CCD、force-field template、字母顺序或未来 topology 需求重排。

1.8 不新增或删除 atoms，也不修改：

- coordinates；
- atom name；
- residue name；
- occupancy；
- B-factor；
- element；
- formal charge。

### 6. PDB writing

final PDB 只保留当前 Stage 1 materialization 所需 records：

```text
CRYST1   # 当前结构存在时保留
ATOM
HETATM
TER
END
```

`ATOM / HETATM` 直接使用 1.2 `polymer_class.value`：

```text
POLYMER    → ATOM
BRANCHED   → HETATM
NONPOLYMER → HETATM
WATER      → HETATM
```

`TER` 表示 PDB object / block boundary，不改变 chain identity：

- selected standard polymer block 结束后写 `TER`；
- 每个 1.8 linked nonstandard block 结束后写 `TER`；
- 1.3 selection 造成的 polymer segment boundary 继续保留；
- 其它 `BRANCHED / NONPOLYMER / WATER` object 按 Stage 1 materialization 语义保持 boundary。

完成 final organization 后，`ATOM / HETATM / TER` 按实际写出顺序从 1 连续重编号 serial。

### 7. Final atom map

`stage1_final_map.yaml` 是输入 atom map 的最终 copy-and-update 结果，只记录 `stage1_final.pdb` 中实际存在的 heavy atoms。

固定结构由 `../../references/atom_mapping_rules.md` 拥有：

```yaml
target_id: target_001
original_structure: /absolute/path/to/structure_checked_by_1.2.pdb
input_structure: /absolute/path/to/current_input.pdb
current_structure: /absolute/path/to/stage1_final.pdb
input_map: /absolute/path/to/current_input_atom_mapping.yaml

atoms:
  - current_atom_serial: 1
    original_atom_serial: 125
    component_id: component_001
    residue_id: residue_001
    operations:
      - 1.3ADD
      - 1.8REORDER
```

1.8 必须：

- 完整保留 input map 中每个 atom 的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`；
- 按 final PDB 更新 `current_atom_serial`；
- 对因 1.8 block / residue organization 而实际改变相对写出位置的 atoms 追加 `1.8REORDER`；
- 不因 serial 重编号单独追加 operation；
- 不重新解释此前 `1.3ADD / 1.4ALTLOC / 1.6ADD / 1.6RENAME / 1.7RENAME` history。

## Deterministic helper

当前机械 materialization 使用：

```text
scripts/build_stage1_final.py
```

典型调用：

```bash
python scripts/build_stage1_final.py \
  --input-structure <current_heavy_atom.pdb> \
  --input-map <current_atom_mapping.yaml> \
  --target-record <targets/target_xxx.yaml> \
  --classification-result <classification_result.yaml> \
  --output-structure <target_work_directory>/stage1_final.pdb \
  --output-map <target_work_directory>/stage1_final_map.yaml
```

helper 只执行确定性的：

```text
读取 1.2 v4 component/residue interface
+ 读取 current atom map
→ 绑定 1.3 target mapping
→ 形成 1.8 linked blocks
→ block reorder
→ TER / serial materialization
→ copy/update atom map
→ stage1_final_map.yaml 写出
```

它不承担 classification、relation judgment、component membership 或 chain assignment 的科学判断，也不得从 current PDB 重新构造 `original_atom_serial` 或既有 operation history。

## Completion gate

1.8 不做 Stage 1 总体 validation；该职责属于 1.9。

结束前只确认本次 1.8 已完整执行：

- 所有当前 PDB residues 均已通过 1.3 mapping 绑定到 `component_id + residue_id`；
- 输入 atom map 与输入 PDB 一一对应；
- 需要执行的 linked-block organization 已落实；
- `stage1_final.pdb` 与 `stage1_final_map.yaml` 已成功生成；
- 输入 atom set 未因本步骤增加或删除；
- final PDB 中每个实际 atom 在 final map 中恰有一个对应 record，final map 无额外 atom record；
- 所有原有 provenance/history 均被保留，`1.8REORDER` 只用于本步骤实际 reorder；
- 没有未处理的 1.8 processing item。

满足后当前 1.8 可标记为 `已完成`。不在 1.8 生成独立 validation report，也不以本 completion gate 替代 1.9。

## Official results

每个 target 的正式结果只有：

```text
stage1_final.pdb
stage1_final_map.yaml
```

完成后，把这两个文件的**完整绝对路径**及 target 说明登记到：

```text
<project_root>/00_project_records/project_result_index.md
```

不登记内部临时文件，也不生成 `mapping_validation.md`。

## Handoff

1.9 只读消费本步骤形成的 `stage1_final.pdb` 与 `stage1_final_map.yaml`，完成 Stage 1 final validation。

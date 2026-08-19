---
name: reorder_and_mapping
description: Stage 1.8 Reorder and mapping。把当前 target 的有效重原子结构整理为 Stage 1 最终 PDB，并建立供 1.9 / Stage 2 消费的 final heavy-atom identity mapping。
---

# 1.8 Reorder and mapping

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 仅补充 1.8-specific 的对象、执行、completion gate 与 results 规则；本步骤明确不设置 reuse。

## Purpose

将当前 target 已完成前序结构准备的 **current valid heavy-atom structure** 整理为 Stage 1 最终结构，并建立逐原子的稳定 identity mapping。

核心职责：

```text
current heavy-atom structure
+ 1.3 target identity / mapping
+ 1.2 classification / relation
↓
final Stage 1 chain / object organization
↓
final PDB materialization
↓
stage1_final.pdb + stage1_final_map.yaml
```

1.8 只处理结构表示与 mapping。它不重新做 structure repair、protonation assignment 或 force-field-specific all-atom ordering，也不根据未来 GROMACS `moleculetype` 反向改变 Stage 1 chain identity。

## Object requirements

每个 target 至少需要：

- 当前 target 的 current valid heavy-atom PDB；
- 1.3 对应 `targets/target_xxx.yaml`；
- 与该 target 对应的 1.2 正式 `classification_result.yaml`，且 `result_status: COMPLETE`。

1.8 直接使用：

- current structure 中实际存在的 atom / residue name / coordinates；
- 1.3 的 `chain_mapping`、`residue_mapping` 与 target membership；
- 1.2 已物化的 `component_id`、`residue_id`、正式 residue order、classification 与 confirmed topology-effect relations。

不得根据 final residue name、atom name 或位置重新猜 `component_id` / `residue_id`。

1.6 `completion_report.yaml`、1.7 `protonation_assignment_report.yaml` 和 `relation_decisions.yaml` 不是 1.8 的强制输入：其已经落实的结构变化由 current structure 体现，relation decision 已进入正式 `classification_result.yaml`。

## No reuse

1.8 **不设置 reuse**。

每次实际进入 1.8，都基于当前 target 的 current heavy-atom structure 和当前正式 1.2 / 1.3 identity information 重新生成本次结果；不通过 `project_result_index.md` 查找或复用旧 1.8 输出。

## Work directory and multiple targets

真实项目基础目录：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/
```

当前 Task 的每个 target 独立执行：

```text
<project_root>/01_structure_preparation/08_reorder_and_mapping/<task_id>/<target_id>/
├── stage1_final.pdb
└── stage1_final_map.yaml
```

多个 target 不共享 final chain assignment、residue numbering、object order 或 map。1.8 不决定是否建立多个 target；target 数量由 1.3 已完成的 selection 结果决定。

## Preflight

正式写出前确认：

- current structure、target record、classification result 均可读；
- current structure 是本步骤预期的 heavy-atom PDB；1.8 不通过删除 H 来修正错误输入；
- 1.3 `chain_mapping + residue_mapping` 能把当前 PDB residue 唯一绑定到 `component_id + residue_id`；
- target 使用的 `component_id / residue_id` 均存在于当前 `classification_result.yaml`；
- 影响 chain assignment 的 topology relation 已在 1.2 正式结果中闭合；
- 输出目录属于当前 Task / target，且不会覆盖其它 target 的正式结果。

如果 identity 或 topology relation 仍有科学歧义，当前 Agent 先解决该上游问题；deterministic helper 不替用户或 Agent 发明新的 relation。

## Execution rules

### 1. Stable identity binding

先用 1.3 的映射建立：

```text
current PDB chain + resid
↔ 1.3 chain_index + resid
↔ component_id + residue_id
```

后续 reorder / renumber 过程中始终以 `component_id + residue_id` 跟踪 residue identity。

### 2. Topology-linked nonstandard unit

根据 1.2 已确认且 `topology_effect_applied: true` 的 relations，将相互 topology-linked 的 nonstandard residues 组织为 linked nonstandard unit。

1.8 不重新判断 relation 是否应成立，只消费 1.2 的正式事实。

对每个 linked unit：

```text
所有 standard-side linked residues 属于同一 standard chain
→ unit 使用该 standard chain 的 final PDB chain ID

standard-side linked residues 跨多个 standard chains
→ unit 保持独立 chain identity
```

如果 1.2 / 1.3 已经给出与该规则一致的 chain organization，直接沿用，不重新建立第二套 chain model。

跨多条 standard chain 的 linked unit 优先沿用已有独立 PDB chain ID；只有现有表示不能可靠作为独立 chain 时，才按 1.3 固定 chain-label 序列：

```text
A-Z → a-z → 0-9
```

选择当前 final structure 中未使用且不与所链接 standard chains 冲突的 chain ID。

不属于上述 linked-unit reassignment 的对象保持既有 chain identity。

### 3. Residue / object organization

对每条 standard polymer chain：

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

- standard polymer residues 保持既有 polymer order；
- 归入该 chain 的多个 linked units 保持 1.2 正式 residue/object order 所确定的稳定 unit order；
- multi-residue linked unit 内部保持正式 residue order；
- 不按 attachment residue number 重新排序 linked units；
- 不把 linked unit 插到 attachment residue 紧邻位置；
- 跨多个 standard chain 而保持独立 chain 的 linked unit 不进入任何 standard-chain residue 排序域；
- independent nonstandard、solvent、ion 和其它未被本步骤 reassignment 的对象保持既有相对 organization。

### 4. Final resid

默认保留 1.3 已有 `resid`。

例外：**归入某条 standard chain 的 topology-linked nonstandard unit** 使用该 final chain 后续可用、不会与保留 residue identity 冲突的新 `resid`。

分配顺序为：

```text
该 chain 已保留的 residue numbering
→ assigned linked units 的稳定 unit order
→ unit 内稳定 residue order
```

standard polymer residue 的 `resid` 不因 1.8 reorder 改写。跨多条 standard chain 而保持独立 chain 的 linked unit，以及其它未 reassignment 对象，保持原 `resid`。

### 5. Heavy-atom order and immutable fields

1.8 只做 residue / object block-level organization。

同一 residue 内：

- heavy atoms 必须保持连续；
- 保持进入 1.8 时的 atom order；
- 不按 CCD、force-field template、字母顺序或其它未来 topology 需求重排。

1.8 不新增或删除 atoms，也不修改：

- coordinates；
- atom name；
- residue name；
- occupancy；
- B-factor；
- element；
- formal charge。

### 6. PDB writing

final PDB 只保留当前 Stage 1 PDB materialization 所需 records：

```text
CRYST1   # 当前结构存在时保留
ATOM
HETATM
TER
END
```

`ATOM / HETATM` 继续使用 1.2 `polymer_class` 语义：

```text
POLYMER    → ATOM
BRANCHED   → HETATM
NONPOLYMER → HETATM
WATER      → HETATM
```

`TER` 是 PDB object/block boundary，不改变 Stage 1 chain identity：

- standard polymer block 结束后写 `TER`；
- 每个 linked nonstandard unit 结束后写 `TER`；
- 前序结构中仍有意义的 polymer-segment boundary 保持；
- 其它 nonpolymer object 保持既有 Stage 1 materialization boundary。

完成 final organization 后，`ATOM / HETATM / TER` 按实际写出顺序从 1 连续重编号 PDB serial。

### 7. Final heavy-atom map

`stage1_final_map.yaml` 只记录 `stage1_final.pdb` 中实际存在的 heavy atoms；不记录 `TER`、missing-residue placeholder、已删除 atom 或 completion provenance。

固定结构：

```yaml
target_id: target_001
structure: /absolute/path/to/stage1_final.pdb

atoms:
  - serial: 1
    chain_id: A
    resid: 1
    residue_name: ALA
    atom_name: N
    component_id: <component_id>
    residue_id: <residue_id>
```

atom record 只保存：

```text
final PDB identity
- serial
- chain_id
- resid
- residue_name
- atom_name

stable upstream identity
- component_id
- residue_id
```

不加入 `origin`、`source_atom_serial`、Stage 2 atom index 或其它上游历史副本。

## Deterministic helper

当前 1.8 的机械写出由：

```text
scripts/build_stage1_final.py
```

完成。

典型调用：

```bash
python scripts/build_stage1_final.py \
  --input-structure <current_heavy_atom.pdb> \
  --target-record <targets/target_xxx.yaml> \
  --classification-result <classification_result.yaml> \
  --output-structure <target_work_directory>/stage1_final.pdb \
  --output-map <target_work_directory>/stage1_final_map.yaml
```

helper 只执行已经确定的 identity binding、linked-unit organization、PDB rewrite 和 map materialization；它不是 relation/classification decision layer。

## Completion gate

1.8 不做 Stage 1 总体 validation；该职责属于 1.9。

本步骤结束前只确认本次 1.8 已完整执行：

- 所有当前 PDB residues 均已通过 1.3 mapping 绑定到稳定 identity；
- 需要执行的 linked-unit chain / resid / object organization 已落实；
- `stage1_final.pdb` 成功生成；
- `stage1_final_map.yaml` 成功生成；
- 输入 atom set 未因本步骤增加或删除；
- final PDB 中每个实际 atom 在 map 中恰有一个对应 record；
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

1.9 只读消费本步骤形成的 Stage 1 final PDB / map，完成 Stage 1 阶段级 validation。

Stage 2 使用 `stage1_final.pdb` 的 heavy-atom serial 作为后续 generated/output atom → source provenance 的直接 source identity；Stage 2 可以建立 force-field-specific all-atom order 和 `moleculetype` 组织，但不得反向重定义本步骤已经确定的 Stage 1 chain identity。

# 2.3 正式结果记录

## 正式结果文件

2.3 生成：

```text
topology_linked_parameterization_result.yaml
```

作为当前 2.3 工作项的正式结果记录。

该记录至少保存：

- 本次实际依赖的上游文件；
- 六个 2.3 核心结果文件；
- 最终实际采纳的 OPT / FREQ / SP 任务路径；
- `standard_atom_deletions`；
- `charge_modification_scope`。

## `references`

`references` 记录本次正式结果实际依赖的上游文件；如多个字段复用同一公共绝对路径，可按仓库级 Task Execution 规则定义公共路径引用。

至少能够定位实际使用的：

```yaml
references:
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
  STANDARD_STRUCTURE_1: /absolute/path/to/2.2_standard_structure.gro
  STANDARD_MAP_1: /absolute/path/to/2.2_standard.map
```

只为当前正式记录实际依赖的文件建立条目。结果文件和依赖文件路径保持完整绝对路径语义。

## 六个核心结果

```yaml
results:
  parameterization_model: /absolute/path/to/parameterization_model.mol2
  parameterization_map: /absolute/path/to/parameterization_model.map
  charge_file: /absolute/path/to/parameterization.chg
  charge_fitting_result: /absolute/path/to/charge_fitting_result.yaml
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_topology: /absolute/path/to/parameterized_topology.itp
```

六个结果 basename 固定为：

```text
parameterization_model.mol2
parameterization_model.map
parameterization.chg
charge_fitting_result.yaml
parameterized_structure.gro
parameterized_topology.itp
```

其中 `parameterization_model.mol2`、`parameterization_model.map` 与 `parameterized_structure.gro` 使用同一原子集合和原子顺序；`parameterization.chg` 与参数化模型原子顺序保持可确定的一一对应。

## 最终采纳的量化计算任务路径

```yaml
quantum_tasks:
  opt: /absolute/path/to/opt_task
  freq: /absolute/path/to/freq_task
  sp:
    - /absolute/path/to/sp_task_1
    - /absolute/path/to/sp_task_2
```

`opt`、`freq` 和 `sp` 只记录本次参数化最终实际采纳的任务路径。实际只有一个 SP 任务时，`sp` 仅记录一项。

## `standard_atom_deletions`

每条记录明确对应 2.2 标准残基全原子结构中的原子及导致该删除的已确认拓扑连接：

```yaml
standard_atom_deletions:
  - structure: STANDARD_STRUCTURE_1
    atom_index: 123
    atom_name: HG
    relation_id: relation_001
```

字段语义：

- `structure`：引用 `references` 中对应的 2.2 标准残基全原子结构；
- `atom_index`：该原子在对应 2.2 map / 结构原子顺序中的索引，与对应 map 的 `output_atom_index` 对齐；
- `atom_name`：用于人工检查，不作为跨步骤唯一身份依据；
- `relation_id`：指向 `CLASSIFICATION_RESULT_1` 中相应 `topology_linked_checks[]` 记录。

## `charge_modification_scope`

记录需要在最终拓扑中采用本次 2.3 新电荷的全部真实残基，包括相关 `STANDARD_RESIDUE` 与 `TOPOLOGY_LINKED_NONSTANDARD` 残基。

每个残基使用 `component_id + residue_id` 定位，并保留 `topology_class`：

```yaml
charge_modification_scope:
  - component_id: component_001
    residue_id: residue_001
    topology_class: STANDARD_RESIDUE
  - component_id: component_001
    residue_id: residue_002
    topology_class: TOPOLOGY_LINKED_NONSTANDARD
```

仅作为参数化模型外围环境或封端环境保留、最终不采用 2.3 新电荷的部分不列入该范围。

## 最小结构示例

```yaml
references:
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
  STANDARD_STRUCTURE_1: /absolute/path/to/2.2_standard_structure.gro
  STANDARD_MAP_1: /absolute/path/to/2.2_standard.map

results:
  parameterization_model: /absolute/path/to/parameterization_model.mol2
  parameterization_map: /absolute/path/to/parameterization_model.map
  charge_file: /absolute/path/to/parameterization.chg
  charge_fitting_result: /absolute/path/to/charge_fitting_result.yaml
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_topology: /absolute/path/to/parameterized_topology.itp

quantum_tasks:
  opt: /absolute/path/to/opt_task
  freq: /absolute/path/to/freq_task
  sp:
    - /absolute/path/to/sp_task_1
    - /absolute/path/to/sp_task_2

standard_atom_deletions:
  - structure: STANDARD_STRUCTURE_1
    atom_index: 123
    atom_name: HG
    relation_id: relation_001

charge_modification_scope:
  - component_id: component_001
    residue_id: residue_001
    topology_class: STANDARD_RESIDUE
  - component_id: component_001
    residue_id: residue_002
    topology_class: TOPOLOGY_LINKED_NONSTANDARD
```

## 项目结果索引登记

2.3 完成后，将 `topology_linked_parameterization_result.yaml` 的完整路径登记到项目结果索引。

六个核心结果文件由该正式结果记录统一定位，不在项目结果索引中分别建立独立结果项。

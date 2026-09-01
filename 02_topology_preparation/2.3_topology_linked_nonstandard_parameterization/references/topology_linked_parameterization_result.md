# 2.3 正式结果记录

## 正式结果文件

2.3 每个 current local target 生成：

```text
topology_linked_parameterization_result.yaml
```

作为当前 2.3 target 的正式结果记录。

该记录至少保存：

- 当前 local `target_id`；
- 当前 `target_record` 完整绝对路径；
- 本次实际依赖的上游文件；
- 六个 2.3 核心结果文件；
- 最终实际采纳的 OPT / FREQ / SP 任务路径；
- `standard_atom_deletions`；
- `charge_modification_scope`。

## `references`

`references` 记录当前 target record 与本次正式结果实际依赖的上游文件；如多个字段复用同一公共绝对路径，可按仓库级 Task Execution 规则定义公共路径引用。

至少能够定位实际使用的：

```yaml
target_id: target_001

references:
  target_record: /absolute/path/to/current/2.3/targets/target_001.yaml
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
  STANDARD_STRUCTURE_1: /absolute/path/to/standard.gro
  STANDARD_MAP_1: /absolute/path/to/standard.map
```

字段语义：

- `target_id` 只用于当前 2.3 工作项 / 当前结果内部定位 local target；
- `references.target_record` 指向当前 2.3 local target record；
- current target record 的 `source_target_records` 记录实际形成本参数化对象的 source targets，可同时包含 Stage 1 final target 与实际被消费的 2.2 target；
- `STAGE1_MAP_n.target_record`、`STANDARD_MAP_n.target_record` 仍分别指向它们自身所属的 upstream targets，不因被 2.3 消费而改写；
- 这些 upstream target 与 current 2.3 target 的对象关系通过 current target record 的 `source_target_records` 表示；
- 不通过任意上下游 `target_id` 相同建立关系。

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

其中：

- `parameterization_model.mol2`、`parameterization_model.map` 与 `parameterized_structure.gro` 使用同一原子集合和原子顺序；
- `parameterization.chg` 与参数化模型原子顺序保持可确定的一一对应；
- `parameterization_model.map.target_record` 必须指向当前 `references.target_record`；
- `parameterization_model.map.source_maps` 记录实际用于逐原子 provenance 的 Stage 1 / 2.2 maps，不替代 target lineage。

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
    current_atom_serial: 123
    atom_name: HG
    relation_id: relation_001
```

字段语义：

- `structure`：引用 `references` 中对应的 2.2 标准残基全原子结构；
- `current_atom_serial`：取对应 `standard.map` 中该原子的 `current_atom_serial`，用于定位 `standard.gro` 中的同一原子；
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
target_id: target_001

references:
  target_record: /absolute/path/to/current/2.3/targets/target_001.yaml
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
  STANDARD_STRUCTURE_1: /absolute/path/to/standard.gro
  STANDARD_MAP_1: /absolute/path/to/standard.map

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
    current_atom_serial: 123
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

## 内部一致性

正式结果可用前确认：

- `references.target_record` 能定位当前 2.3 local target；
- current target record 的 `source_target_records` 与本次实际消费的 target-scoped upstream objects 一致；
- `results.parameterization_map.target_record == references.target_record`；
- parameterization map 中记录的 source maps 与正式 `references` 中实际采用的 Stage 1 / standard maps 一致；
- 不把 CCD、force-field reference、classification evidence 等普通依赖误记成 source target；
- 不通过 `target_id` 比较建立 target lineage。

## 项目结果索引登记

2.3 完成后，将 `topology_linked_parameterization_result.yaml` 的完整路径登记到项目结果索引。

六个核心结果文件由该正式结果记录统一定位，不在项目结果索引中分别建立独立结果项。Target record 是 lineage support record，不因为创建而单独登记。

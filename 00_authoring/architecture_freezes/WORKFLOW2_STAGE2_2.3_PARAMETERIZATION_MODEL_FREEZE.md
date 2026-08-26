# Workflow 2 Stage 2 — 2.3 参数化模型规则冻结

Status: CURRENT AUTHORING REFERENCE

本文件记录 `2.3 Topology-linked nonstandard parameterization` 中已经敲定的参数化模型输入、截取规则、atom map 维护、正式结果记录以及向 2.5 交付的信息，作为后续继续设计和正式 Skill generation 的 authoring input。

Stage 2 总体架构继续读取：

`WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

## 1. 输入文件与用途

- **Task Sheet**：读取本次需要共同参数化的 `TOPOLOGY_LINKED_NONSTANDARD` 残基集合。
- **`classification_result.yaml`**：读取与这些残基相关、`judgment: CONFIRMED` 且 `topology_effect_applied: true` 的 `topology_linked_checks[]` 及其 `relation_id`、端点 residue identity 和 atom name。
- **`stage1_final_map.yaml`**：读取上述 residue 和连接端点在 Stage 1 最终结构中的稳定身份、atom mapping 与既有 operation history。
- **`stage1_final.pdb`**：读取 `TOPOLOGY_LINKED_NONSTANDARD` 残基的当前重原子坐标。
- **2.2 全原子结构及对应 `*.map`**：读取参数化模型所需标准残基的全原子坐标、身份及原子对应关系。

## 2. 参数化模型截取的一般规则

1. 需要共同参数化的全部 `TOPOLOGY_LINKED_NONSTANDARD` 残基均纳入参数化模型。
2. 与这些残基存在拓扑连接的标准残基完整保留。
3. 从完整保留的标准残基向外围扩展至合适的截断位置；截断应尽量远离拓扑连接及其直接局部环境，优先选择对电子结构扰动较小的低极性单键，并优先在合适的非极性 C–C 单键处截断；截断后进行封端以恢复合理价态。避免在拓扑连接本身以及明显的极性、带电或共轭区域中截断。
4. 存在多个拓扑连接位点时，分别按照上述规则确定各连接位点需要保留的局部结构，参数化模型取这些保留范围的并集；同一原子只保留一次，不因多个连接位点位于同一标准聚合物中而自动纳入它们之间的全部结构。

## 3. 蛋白质体系

沿肽链在拓扑连接残基两侧各跨过一个相邻肽键，参数化模型分别延伸至相邻残基的 Cα；去除 Cα 外侧不再保留的原子，并补 H 将边界 Cα 处理为甲基。

## 4. 核酸体系

1. 沿核酸链向 5′ 和 3′ 方向各外扩至少一个相邻核苷酸；外扩核苷酸至少完整保留糖和碱基，并保留其与参数化模型内部核苷酸之间的磷酸二酯连接。外侧边界截至糖的 O5′ / O3′，分别补 H 形成 5′-OH / 3′-OH。
2. 已保留碱基存在互补配对时，将对应的配对核苷酸纳入参数化模型，并以该配对核苷酸为中心按前条相同规则沿其所在核酸链向 5′ 和 3′ 方向外扩和封端。

## 5. 标准残基一侧的原子变化

根据已确认的拓扑连接，确定标准残基一侧因该连接形成而不应继续保留的原子，并在参数化模型中去除这些原子。记录对应 2.2 标准残基全原子结构中的原子及导致该删除的 `relation_id`，供 2.5 在最终结构和拓扑整合时使用。

## 6. 非标准残基补氢

1. 存在对应 CCD 时，以 CCD 中的原子、键连接和 H 定义作为非标准残基补氢依据。
2. 不存在对应 CCD 时，由智能体根据当前结构的成键关系、价态和局部化学环境判断补氢方式。
3. 无论采用哪种依据，都必须计入当前已确认拓扑连接造成的连接状态变化，相应调整连接原子上的 H。
4. 仍不能唯一确定补氢方式时，向用户确认。

## 7. atom map 维护

2.3 的 `*.map` 以 `stage1_final_map.yaml` 为稳定身份与 atom-level history 的主 baseline，不重新建立 `SOURCE / ADDED_H / CAP` provenance 分类，也不把 2.2 map 作为 2.3 map 的整体父级。

参数化模型中各类原子的维护规则：

1. `TOPOLOGY_LINKED_NONSTANDARD` source heavy atoms，以及 standard fragment 中能够对应到 Stage 1 最终结构的 atoms：保留其 `stage1_final_map.yaml` record 中的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，只更新为参数化模型中的 `output_atom_index`。
2. standard fragment 中由 2.2 新增、Stage 1 最终结构中不存在的 H：从 2.2 map 读取对应 record，保留 `original_atom_serial: null`、`component_id + residue_id` 和包含 `2.2ADD` 的 operation history，再更新为参数化模型中的 `output_atom_index`。
3. 2.3 为 `TOPOLOGY_LINKED_NONSTANDARD` residue 新增的 H：建立新 record，`original_atom_serial: null`，保存所属 residue 的 `component_id + residue_id`，`operations = [2.3ADD]`。
4. 参数化模型截断/封端产生的临时 CAP atom：建立 `2.3CAP` record，`original_atom_serial: null`，`component_id: null`，`residue_id: null`。
5. 因参数化模型截取而未纳入的 atoms，以及标准残基一侧因拓扑连接而在参数化模型中去除的 atoms，不写入当前 2.3 map；标准残基一侧需要在 2.5 实际删除的原子身份由第 8 节的正式结果记录保存。

2.3 map 的逐原子核心字段与 Stage 2 共享接口一致：

```yaml
output_atom_index:
original_atom_serial:
component_id:
residue_id:
operations:
```

参数化模型 atom order 冻结后，`.mol2 / .map / OPT / FREQ / SP / .chg / Sobtop / .gro / .itp` 使用同一套可确定 atom-index 对应；`output_atom_index` 即该冻结顺序中的索引。

## 8. 2.3 正式结果记录

2.3 生成一份结构化 YAML 作为本环节正式结果记录。该记录同时保存：

- 本次实际引用的上游正式文件；
- 五个 2.3 核心结果文件；
- 标准残基一侧需要删除的原子；
- 残基级电荷修改范围。

该正式结果记录的 basename 留到正式 Skill generation 时统一确定。

### 8.1 `references`

文件级 `references` 集中记录本次正式结果实际引用的上游正式文件。正文记录优先使用短引用键，不重复写长绝对路径。

至少记录实际使用的：

```yaml
references:
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
  STANDARD_STRUCTURE_1: /absolute/path/to/2.2_standard_structure.gro
  STANDARD_MAP_1: /absolute/path/to/2.2_standard.map
```

只为当前正式记录实际引用的上游文件建立条目；路径使用完整绝对路径。2.3 自己生成的结果文件不放入 `references`。

### 8.2 标准残基一侧需要删除的原子

每条记录明确：**哪个 2.2 标准残基全原子结构中的哪个原子，因为哪一条已确认的拓扑连接而需要删除。**

```yaml
standard_atom_deletions:
  - structure: STANDARD_STRUCTURE_1
    atom_index: 123
    atom_name: HG
    relation_id: relation_001
```

字段语义：

- `structure`：引用 `references` 中对应的 2.2 标准残基全原子结构；
- `atom_index`：该原子在对应 2.2 map / 结构 atom order 中的索引，与 `STANDARD_MAP_1` 中的 `output_atom_index` 对齐；
- `atom_name`：保留用于人工检查，不作为跨步骤唯一身份依据；
- `relation_id`：指向 `CLASSIFICATION_RESULT_1` 的 `topology_linked_checks[]` 中导致该删除的已确认拓扑连接记录。

拓扑连接端点不再建立平行列表；需要检查完整端点时通过 `relation_id` 回到 `CLASSIFICATION_RESULT_1`。

### 8.3 残基级电荷修改范围

记录本次 2.3 参数化结果中需要在最终拓扑中采用新电荷的全部真实 residue，包括相关 `STANDARD_RESIDUE` 与 `TOPOLOGY_LINKED_NONSTANDARD` residue。每个 residue 使用 1.2 正式 `component_id + residue_id` 定位，并保留 `topology_class` 作为便于使用者检查的冗余信息。

```yaml
charge_modification_scope:
  - component_id: component_001
    residue_id: residue_001
    topology_class: STANDARD_RESIDUE

  - component_id: component_001
    residue_id: residue_002
    topology_class: TOPOLOGY_LINKED_NONSTANDARD
```

仅作为参数化模型外围环境或封端环境而保留、最终不采用 2.3 新电荷的标准残基不列入该集合。

### 8.4 五个核心结果文件

2.3 的五个核心结果 basename 固定为：

```text
parameterization_model.mol2
parameterization_model.map
parameterization.chg
parameterized_structure.gro
parameterized_topology.itp
```

这五个文件统一登记在 2.3 正式结果记录的 `results` 中，并保存完整绝对路径：

```yaml
results:
  parameterization_model: /absolute/path/to/parameterization_model.mol2
  parameterization_map: /absolute/path/to/parameterization_model.map
  charge_file: /absolute/path/to/parameterization.chg
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_topology: /absolute/path/to/parameterized_topology.itp
```

其中：

- `parameterization_model.mol2`：2.3 冻结 atom order 后用于后续量化计算与参数化的模型结构；
- `parameterization_model.map`：与参数化模型 atom order 对应的 atom map；
- `parameterization.chg`：2.3 电荷拟合结果；
- `parameterized_structure.gro`：Sobtop 后与当前参数化结果对应的结构；
- `parameterized_topology.itp`：Sobtop 后与当前参数化结果对应的 topology。

### 8.5 最小结构示例

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
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_topology: /absolute/path/to/parameterized_topology.itp

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

### 8.6 项目结果索引登记

2.3 完成并通过本环节 validation 后，将 **2.3 正式结果记录**登记到项目结果索引。项目结果索引保存该正式结果记录的完整路径，用它作为定位本次 2.3 全部正式结果的入口。

五个核心结果文件已经由该正式结果记录的 `results` 统一定位，因此不在项目结果索引中分别建立独立结果项。

## 9. 后续专项规则

其它适用体系的具体截取与封端规则继续在上述一般规则下分别讨论和冻结。

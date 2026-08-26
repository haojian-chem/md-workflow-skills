# Workflow 2 Stage 2 — 2.3 Topology-linked nonstandard parameterization 冻结

Status: CURRENT AUTHORING REFERENCE

本文件记录 `2.3 Topology-linked nonstandard parameterization` 已经敲定的环节结构、正式结果记录及向 2.5 交付的信息，作为后续继续设计和正式 Skill generation 的 authoring input。

建立参数化模型的详细科学规则已经专项保存于：

`WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md`

几何优化中固定原子的详细科学规则已经专项保存于：

`WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md`

电荷拟合相关科学规则已经专项保存于：

`WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md`

Stage 2 总体架构继续读取：

`WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

## 1. 环节结构

2.3 的科研处理环节为：

```text
建立参数化模型
→ 量化计算
→ 电荷拟合并生成 parameterization.chg
→ Sobtop 参数化并生成 parameterized_topology.itp
```

### 1.1 建立参数化模型

建立参数化模型时，按 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md` 确定参数化模型范围、标准残基一侧原子变化、非标准残基补氢、封端、atom map 及原子顺序，并生成：

```text
parameterization_model.mol2
parameterized_structure.gro
parameterization_model.map
```

### 1.2 量化计算

量化计算基于建立参数化模型环节得到的参数化模型结构进行。

开始量化计算前，确定当前参数化模型的总电荷和自旋多重度。实际采用的量化计算方法、基组、溶剂模型及其它计算设置应与当前体系的元素组成、电子结构和后续参数化要求相适应，并记录实际使用的设置。

对参数化模型进行几何优化。几何优化中需要固定的原子按 `WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md` 确定。

在几何优化得到的结构上进行 FREQ 计算，获得后续参数化所需的振动 / Hessian 信息，并提供对优化结构振动性质的判断依据。FREQ 中如何处理几何优化阶段的固定坐标尚未敲定。

电荷拟合所需 SP 任务的设置读取 `WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md` 第 2 节，并按该节确定的任务完成相应 SP 计算与静电势数据获取。

### 1.3 电荷拟合并生成 `parameterization.chg`

原子电荷拟合及 `parameterization.chg` 的生成读取 `WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md` 第 1、3–6 节。

### 1.4 Sobtop 参数化并生成 `parameterized_topology.itp`

Sobtop 参数化及 `parameterized_topology.itp` 的生成属于同一科研处理环节。详细参数化规则继续在 2.3 设计中确定。

## 2. 2.3 正式结果记录

2.3 生成：

```text
topology_linked_parameterization_result.yaml
```

作为本环节正式结果记录。该记录同时保存：

- 本次实际引用的上游正式文件；
- 五个 2.3 核心结果文件；
- 标准残基一侧需要删除的原子；
- 残基级电荷修改范围。

### 2.1 `references`

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

### 2.2 标准残基一侧需要删除的原子

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

### 2.3 残基级电荷修改范围

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

### 2.4 五个核心结果文件

2.3 的五个核心结果 basename 固定为：

```text
parameterization_model.mol2
parameterization_model.map
parameterization.chg
parameterized_structure.gro
parameterized_topology.itp
```

这五个文件统一登记在 `topology_linked_parameterization_result.yaml` 的 `results` 中，并保存完整绝对路径：

```yaml
results:
  parameterization_model: /absolute/path/to/parameterization_model.mol2
  parameterization_map: /absolute/path/to/parameterization_model.map
  charge_file: /absolute/path/to/parameterization.chg
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_topology: /absolute/path/to/parameterized_topology.itp
```

其中：

- `parameterization_model.mol2`：建立参数化模型时生成的模型结构；
- `parameterization_model.map`：建立参数化模型时生成、与模型原子顺序对应的 atom map；
- `parameterized_structure.gro`：建立参数化模型时生成，与 `parameterization_model.mol2` 和 `parameterization_model.map` 使用同一原子集合和原子顺序；
- `parameterization.chg`：电荷拟合环节生成的电荷结果；
- `parameterized_topology.itp`：Sobtop 参数化环节生成的 topology。

### 2.5 最小结构示例

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

### 2.6 项目结果索引登记

2.3 完成并通过本环节 validation 后，将 `topology_linked_parameterization_result.yaml` 登记到项目结果索引。项目结果索引保存该正式结果记录的完整路径，用它作为定位本次 2.3 全部正式结果的入口。

五个核心结果文件已经由该正式结果记录的 `results` 统一定位，因此不在项目结果索引中分别建立独立结果项。

---
name: topology_linked_nonstandard_parameterization
description: 拓扑准备 2.3。对当前 Task Sheet 已确定需要共同处理的 topology-linked 非标准残基组合建立参数化模型，完成量化计算、电荷拟合与 Sobtop 参数化，并生成正式参数化结果。
---

# 2.3 Topology-linked nonstandard parameterization

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 处理当前 Task Sheet 已由 2.1 确定的一个 2.3 工作项。一个工作项可以包含一个或多个需要共同参数化的 `TOPOLOGY_LINKED_NONSTANDARD` 残基。

## 目标

对当前 topology-linked 参数化对象完成：

```text
建立参数化模型
→ 量化计算
→ 电荷拟合并生成 parameterization.chg
→ Sobtop 参数化并生成 parameterized_topology.itp
```

形成当前 2.3 工作项的正式结果记录 `topology_linked_parameterization_result.yaml`。

## 输入与依据

开始当前 2.3 工作项时读取：

- 当前 Task Sheet，确定本次共同参数化的 `TOPOLOGY_LINKED_NONSTANDARD` 残基组合，以及 2.1 已确认的力场 / 参数定义来源；
- 当前体系对应的 1.2 正式 `classification_result.yaml`，读取与当前处理对象相关、`judgment: CONFIRMED` 且 `topology_effect_applied: true` 的 `topology_linked_checks[]`；
- 当前体系的 `stage1_final.pdb` 与 `stage1_final_map.yaml`；
- 当前 Task Sheet 引用、且由 2.1 已判定可用于当前体系的 2.2 正式结果，从中定位标准残基全原子结构及对应 map；
- 非标准残基补氢实际使用的 CCD 文件。

当前 2.3 沿用正式结果中已有的 `component_id + residue_id` 作为残基身份，不根据 residue name、chain、resid 或当前空间位置重新建立。

## Reuse

已有 2.3 正式结果是否适用于当前体系由 2.1 判断。

若当前 Task Sheet 已引用 2.1 判定可直接使用的 2.3 正式结果，直接复用该结果；否则执行当前 2.3 工作项。本 Skill 不重新维护一套与 2.1 平行的已有结果适用性判据。

## 建立参数化模型

执行前读取：

`references/parameterization_model.md`

按其中规则确定当前参数化模型的范围、标准残基一侧原子变化、非标准残基补氢、封端以及 `parameterization_model.map`。

完成后生成：

```text
parameterization_model.mol2
parameterized_structure.gro
parameterization_model.map
```

三者使用同一原子集合与原子顺序。

同时确定并保留两类正式结果信息：

1. `standard_atom_deletions`：标准残基一侧因已确认拓扑连接而需要从最终结构 / 拓扑中删除的原子；
2. `charge_modification_scope`：最终拓扑中需要采用本次 2.3 新电荷的全部真实残基，包括相关 `STANDARD_RESIDUE` 与 `TOPOLOGY_LINKED_NONSTANDARD` 残基。仅作为参数化模型外围环境或封端环境保留的部分不列入该范围。

`charge_modification_scope` 中每个残基使用 `component_id + residue_id` 定位，并保留 `topology_class` 供检查。

## 量化计算

执行前读取：

`references/quantum_and_sobtop.md`

基于当前参数化模型确定总电荷和自旋多重度，并完成几何优化与 FREQ 计算。几何优化固定原子规则、FREQ 检查以及后续 Sobtop 成键项拟合输入均由该 reference 定义。

最终实际采纳的 OPT / FREQ 任务路径保留用于写入正式结果记录。

## 电荷拟合

执行前读取：

`references/charge_fitting.md`

根据当前采用的 RESP / RESP2 方案完成所需 SP、Multiwfn 电荷拟合及检查，生成：

```text
charge_fitting_result.yaml
parameterization.chg
```

`parameterization.chg` 与参数化模型原子顺序保持可确定的一一对应，并作为 Sobtop 参数化使用的最终电荷文件。

最终实际采纳的 SP 任务路径保留用于写入正式结果记录。

## Sobtop 参数化

继续按 `references/quantum_and_sobtop.md` 完成 Sobtop 参数化，生成正式：

```text
parameterized_topology.itp
```

该 reference 同时规定 FREQ 检查后的 Sobtop 输入、缺失 LJ 参数补充及 Sobtop 输出名称处理规则。

## 正式结果记录

2.3 生成：

```text
topology_linked_parameterization_result.yaml
```

作为当前 2.3 工作项的正式结果记录。

### `references`

记录本次正式结果实际依赖的上游文件；如多个字段复用同一公共绝对路径，可按仓库级 Task Execution 规则定义公共路径引用。

至少记录实际使用的：

```yaml
references:
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
  STANDARD_STRUCTURE_1: /absolute/path/to/2.2_standard_structure.gro
  STANDARD_MAP_1: /absolute/path/to/2.2_standard.map
```

只为当前正式记录实际依赖的文件建立条目。结果文件和依赖文件路径保持完整绝对路径语义。

### 六个核心结果

```yaml
results:
  parameterization_model: /absolute/path/to/parameterization_model.mol2
  parameterization_map: /absolute/path/to/parameterization_model.map
  charge_file: /absolute/path/to/parameterization.chg
  charge_fitting_result: /absolute/path/to/charge_fitting_result.yaml
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_topology: /absolute/path/to/parameterized_topology.itp
```

### 最终采纳的量化计算任务路径

```yaml
quantum_tasks:
  opt: /absolute/path/to/opt_task
  freq: /absolute/path/to/freq_task
  sp:
    - /absolute/path/to/sp_task_1
    - /absolute/path/to/sp_task_2
```

`sp` 只记录本次最终实际采纳的 SP 任务路径；实际只有一个 SP 任务时仅记录一项。

### 标准残基一侧需要删除的原子

每条记录明确对应 2.2 标准残基全原子结构中的原子及导致该删除的已确认拓扑连接：

```yaml
standard_atom_deletions:
  - structure: STANDARD_STRUCTURE_1
    atom_index: 123
    atom_name: HG
    relation_id: relation_001
```

其中 `atom_index` 与对应 2.2 map / 结构原子顺序中的 `output_atom_index` 对齐；`atom_name` 用于人工检查；`relation_id` 指向 `CLASSIFICATION_RESULT_1` 中相应 `topology_linked_checks[]` 记录。

### 残基级电荷修改范围

```yaml
charge_modification_scope:
  - component_id: component_001
    residue_id: residue_001
    topology_class: STANDARD_RESIDUE
  - component_id: component_001
    residue_id: residue_002
    topology_class: TOPOLOGY_LINKED_NONSTANDARD
```

### 最小结构示例

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

## 结果登记与 Task Sheet 更新

2.3 完成后，将 `topology_linked_parameterization_result.yaml` 的完整路径登记到项目结果索引。六个核心结果文件由该正式结果记录统一定位，不在项目结果索引中分别建立结果项。

随后按仓库级 Task Execution 规则更新当前 Task Sheet 的 2.3 工作项状态，并记录当前正式结果路径。

2.3 不直接修改 2.2 基线结构 / 拓扑。
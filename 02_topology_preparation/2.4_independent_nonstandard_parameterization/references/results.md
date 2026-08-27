# 2.4 正式结果接口

## 正式结果入口

2.4 生成：

```text
independent_nonstandard_parameterization_result.yaml
```

作为当前 2.4 工作项的正式结果记录。

该记录至少保存：

- 当前工作项处理的残基名；
- 当前工作项覆盖的全部实例及其 `component_id + residue_id`；
- 被选择用于参数化的代表实例；
- 本次实际依赖的上游文件；
- 本次实际使用的补氢依据；
- 七个核心结果文件；
- 最终实际采纳的 OPT / FREQ / SP 任务路径；
- 足以判断参数生成方法是否与其它正式结果相同的实际参数化方法与设置。

## 当前处理对象

正式结果必须能够明确当前参数定义适用于哪个残基名，以及当前体系中哪些实例使用该参数定义。

建议组织为：

```yaml
parameterization_object:
  residue_name: LIG
  representative_instance:
    component_id: component_001
    residue_id: residue_004
  instances:
    - component_id: component_001
      residue_id: residue_004
    - component_id: component_003
      residue_id: residue_002
```

`representative_instance` 必须属于 `instances`。

## `references`

`references` 记录本次正式结果实际依赖的上游 / 外部文件。只为实际使用的文件建立条目。

至少能够定位：

```yaml
references:
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
```

若本次补氢实际使用 CCD，也记录对应 CCD 文件完整路径。

正式结果文件和依赖文件路径均遵守仓库级结果生成规则的完整绝对路径语义。

## 补氢依据

记录代表实例实际采用的补氢依据，使正式结果能够解释 `parameterization_model.mol2` 的全原子组成来源。

例如可记录：

```yaml
hydrogenation_basis:
  type: CCD
  reference: /absolute/path/to/component.cif
```

不存在适用 CCD 时，记录本次实际依据的当前结构成键关系、价态 / 化学状态信息及必要的用户确认来源；不为了统一格式制造不存在的 CCD 字段。

## 七个核心结果

正式结果记录统一定位：

```yaml
results:
  parameterization_model: /absolute/path/to/parameterization_model.mol2
  parameterization_map: /absolute/path/to/parameterization_model.map
  charge_file: /absolute/path/to/parameterization.chg
  charge_fitting_result: /absolute/path/to/charge_fitting_result.yaml
  parameterized_topology: /absolute/path/to/parameterized_topology.itp
  parameterized_structure: /absolute/path/to/parameterized_structure.gro
  parameterized_structure_map: /absolute/path/to/parameterized_structure.map
```

七个核心结果 basename 固定为：

```text
parameterization_model.mol2
parameterization_model.map
parameterization.chg
charge_fitting_result.yaml
parameterized_topology.itp
parameterized_structure.gro
parameterized_structure.map
```

其中：

- `parameterization_model.mol2` 与 `parameterization_model.map` 只描述代表实例，并使用同一原子集合与原子顺序；
- `parameterization.chg` 与代表实例参数化模型原子顺序保持可确定的一一对应；
- `parameterized_topology.itp` 保存当前残基名共用的一套参数定义；
- `parameterized_structure.gro` 与 `parameterized_structure.map` 覆盖当前工作项中的全部同名实例；
- `parameterized_structure.map` 中每个实例继续使用自己的 `component_id + residue_id`。

## 最终采纳的量化计算任务路径

记录本次参数化最终实际采纳的任务路径：

```yaml
quantum_tasks:
  opt: /absolute/path/to/opt_task
  freq: /absolute/path/to/freq_task
  sp:
    - /absolute/path/to/sp_task_1
    - /absolute/path/to/sp_task_2
```

实际只有一个 SP 任务时，`sp` 仅记录一项；不得创建未执行任务的占位路径。

## 参数生成方法

正式结果必须记录足以支持 2.1 判断“参数生成方法是否相同”的实际方法信息，而不是只保存抽象的“同一方法”结论。

至少覆盖本次实际采用的：

- OPT / FREQ 使用的软件、方法、基组、溶剂模型及影响参数化结果的其它关键设置；
- SP 使用的软件、方法、基组、溶剂模型及其它关键设置；
- 电荷拟合采用 RESP 或 RESP2、Multiwfn 拟合设置，以及 RESP2 实际权重；
- Sobtop 参数化及本次实际使用的 LJ 参数来源。

具体组织方式可按当前实际方法设置决定；不得为了固定 schema 复制量化任务目录中的全部输入文件内容。正式结果中的方法摘要与 `quantum_tasks`、`charge_fitting_result.yaml` 及最终拓扑共同提供可追溯的参数生成依据。

## 内部一致性要求

正式结果可用前必须满足：

- `parameterization_object.instances` 与 `parameterized_structure.gro` / `parameterized_structure.map` 实际覆盖的实例集合一致；
- `representative_instance` 能在 `parameterization_model.map` 中通过相同 `component_id + residue_id` 定位；
- 七个核心结果均存在且已通过 2.4 main Skill 要求的检查；
- `parameterization_model.mol2`、`parameterization.chg` 与 `parameterized_topology.itp` 之间的逐原子对应可确定；
- `parameterized_structure.gro` 中每个实例的残基名、原子名和残基内原子顺序与 `parameterized_topology.itp` 一致；
- `parameterization_model.map` 与 `parameterized_structure.map` 对 Stage 1 来源原子保留已有身份与逐原子历史，并对 2.4 新增 H 使用 `2.4ADD`。

## 项目结果索引登记

2.4 完成后，将：

```text
independent_nonstandard_parameterization_result.yaml
```

的完整路径登记到项目结果索引。

七个核心结果文件由该正式结果记录统一定位，不在项目结果索引中分别建立独立结果项。

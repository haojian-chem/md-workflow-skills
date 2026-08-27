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
- 实际完成参数化的代表实例；
- 本次实际依赖的上游文件；
- 本次实际使用的补氢依据；
- 七个核心结果文件；
- 最终实际采纳的 OPT / FREQ / SP 任务路径；
- 足以判断参数生成方法是否与其它正式结果相同的实际参数化方法与设置；
- 若复用已有 2.4 参数化结果，记录实际引用的来源正式结果。

## 当前工作项与参数化来源

正式结果必须区分：

1. 当前参数定义适用于哪个残基名、当前体系中哪些实例使用该参数定义；
2. 当前参数化模型实际由哪个代表实例产生，以及是否来自已有 2.4 正式结果。

可按以下方式组织：

```yaml
parameterization_object:
  residue_name: LIG
  instances:
    - component_id: component_001
      residue_id: residue_004
    - component_id: component_003
      residue_id: residue_002

parameterization_source:
  representative_instance:
    component_id: component_001
    residue_id: residue_004
```

若本次复用已有 2.4 参数化结果，在 `parameterization_source` 中同时记录来源正式结果完整路径：

```yaml
parameterization_source:
  result: /absolute/path/to/previous/independent_nonstandard_parameterization_result.yaml
  representative_instance:
    component_id: component_010
    residue_id: residue_002
```

执行新的参数化时，`representative_instance` 属于当前 `parameterization_object.instances`。复用其它体系已有参数化结果时，来源代表实例可以不属于当前实例集合；不得因此把来源体系的实例身份改写成当前体系身份。

## `references`

`references` 记录本次正式结果实际依赖的上游 / 外部文件。只为实际使用的文件建立条目。

当前体系实例结果至少能够定位：

```yaml
references:
  CLASSIFICATION_RESULT_1: /absolute/path/to/classification_result.yaml
  STAGE1_STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  STAGE1_MAP_1: /absolute/path/to/stage1_final_map.yaml
```

若本次补氢实际使用 CCD，也记录对应 CCD 文件完整路径。若参数化文件来自已有 2.4 正式结果，`parameterization_source.result` 记录该正式结果本身，不复制来源结果中的全部依赖文件作为当前结果的平行 `references`。

正式结果文件和依赖文件路径均遵守仓库级结果生成规则的完整绝对路径语义。

## 补氢依据

执行新的参数化时，记录代表实例实际采用的补氢依据，使正式结果能够解释 `parameterization_model.mol2` 的全原子组成来源。

例如可记录：

```yaml
hydrogenation_basis:
  type: CCD
  reference: /absolute/path/to/component.cif
```

不存在适用 CCD 时，记录本次实际依据的当前结构成键关系、价态 / 化学状态信息及必要的用户确认来源；不为了统一格式制造不存在的 CCD 字段。

复用已有参数化结果时，参数化代表实例的补氢依据继续由 `parameterization_source.result` 定位原正式结果；当前体系其它实例按照被复用代表实例已经确定的补氢方式和原子定义生成 H，并在当前 `parameterized_structure.map` 中记录 `2.4ADD`。

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

- `parameterization_model.mol2` 与 `parameterization_model.map` 只描述实际完成参数化的代表实例，并使用同一原子集合与原子顺序；
- `parameterization.chg` 与代表实例参数化模型原子顺序保持可确定的一一对应；
- `parameterized_topology.itp` 保存当前残基名共用的一套参数定义；
- `parameterized_structure.gro` 与 `parameterized_structure.map` 覆盖当前工作项中的全部同名实例；
- `parameterized_structure.map` 中每个实例继续使用自己的 `component_id + residue_id`。

若复用已有参数化结果，前五个参数化相关结果可以直接引用来源正式结果所定位的原文件；当前体系专属的 `parameterized_structure.gro` 与 `parameterized_structure.map` 必须指向当前工作项实际覆盖全部实例的文件。跨任务复用时不为了当前结果复制一套相同参数化文件。

## 最终采纳的量化计算任务路径

记录当前参数定义实际采用的任务路径：

```yaml
quantum_tasks:
  opt: /absolute/path/to/opt_task
  freq: /absolute/path/to/freq_task
  sp:
    - /absolute/path/to/sp_task_1
    - /absolute/path/to/sp_task_2
```

实际只有一个 SP 任务时，`sp` 仅记录一项；不得创建未执行任务的占位路径。复用已有参数化结果时，沿用来源正式结果已经记录的实际任务路径，不制造当前工作项重新执行过这些任务的记录。

## 参数生成方法

正式结果必须记录足以支持 2.1 判断“参数生成方法是否相同”的实际方法信息，而不是只保存抽象的“同一方法”结论。

至少覆盖实际采用的：

- OPT / FREQ 使用的软件、方法、基组、溶剂模型及影响参数化结果的其它关键设置；
- SP 使用的软件、方法、基组、溶剂模型及其它关键设置；
- 电荷拟合采用 RESP 或 RESP2、Multiwfn 拟合设置，以及 RESP2 实际权重；
- Sobtop 参数化及实际使用的 LJ 参数来源。

具体组织方式可按实际方法设置决定；不得为了固定 schema 复制量化任务目录中的全部输入文件内容。复用已有参数化结果时，这些方法信息必须与 `parameterization_source.result` 所记录的实际参数生成方法一致。

## 内部一致性要求

正式结果可用前必须满足：

- `parameterization_object.instances` 与 `parameterized_structure.gro` / `parameterized_structure.map` 实际覆盖的实例集合一致；
- `parameterization_source.representative_instance` 能在 `parameterization_model.map` 中通过相同 `component_id + residue_id` 定位；
- 七个核心结果均存在且已通过 2.4 main Skill 要求的检查；
- `parameterization_model.mol2`、`parameterization.chg` 与 `parameterized_topology.itp` 之间的逐原子对应可确定；
- `parameterized_structure.gro` 中每个实例的残基名、原子名和残基内原子顺序与 `parameterized_topology.itp` 一致；
- `parameterization_model.map` 对实际参数化代表实例保持其原始身份与逐原子历史；`parameterized_structure.map` 对当前体系实例保持各自 Stage 1 身份与逐原子历史，并对 2.4 新增 H 使用 `2.4ADD`；
- 若 `parameterization_source.result` 存在，前五个参数化相关结果、量化任务和参数生成方法能够追溯到该来源正式结果，当前体系实例结构 / map 不误指向来源体系实例。

## 项目结果索引登记

2.4 完成后，将：

```text
independent_nonstandard_parameterization_result.yaml
```

的完整路径登记到项目结果索引。

七个核心结果文件由该正式结果记录统一定位，不在项目结果索引中分别建立独立结果项。

---
name: independent_nonstandard_parameterization
description: 拓扑准备 2.4。处理当前 Task Sheet 由 2.1 确定需要独立参数化的残基名，从同名实例中选择代表实例完成量化计算、电荷拟合与 Sobtop 参数化，并将成功参数化实例的补氢定义应用到当前工作项全部同名实例，生成正式参数化结果。
---

# 2.4 Independent nonstandard parameterization

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 处理当前 Task Sheet 已由 2.1 建立的一个 2.4 工作项。2.4 直接消费 2.1 已确定的处理对象，不重新分类、重新分组或改变同名残基的参数化归属。

当前工作项通常来自 `INDEPENDENT_NONSTANDARD`；当 2.1 已确认某个 `SOLVENT_COMPONENT` 或 `ION_COMPONENT` 缺少可直接用于后续拓扑整合的完整分子拓扑定义时，也由对应残基名建立 2.4 工作项。

## 目标

对当前 2.4 工作项完成：

```text
选择代表实例并建立参数化模型
→ 量化计算
→ 电荷拟合并生成 parameterization.chg
→ Sobtop 参数化并生成 parameterized_topology.itp
→ 以成功参数化的代表实例为模板处理当前工作项全部同名实例
→ 生成 parameterized_structure.gro 与 parameterized_structure.map
```

形成当前工作项的正式结果记录：

`independent_nonstandard_parameterization_result.yaml`

## 输入与依据

开始当前 2.4 工作项时读取：

- 当前 Task Sheet，确定本次处理的残基名以及 2.1 已确认的力场 / 参数定义来源；
- 当前体系对应的 1.2 正式 `classification_result.yaml`，定位当前工作项所覆盖的全部同名实例及其 `component_id + residue_id`；
- 当前体系的 `stage1_final.pdb` 与 `stage1_final_map.yaml`；
- 当前对象补氢实际使用的 CCD 文件；不存在适用 CCD 时，使用当前结构的成键关系、价态和局部化学环境作为补氢依据。

2.4 沿用正式结果中已有的 `component_id + residue_id` 作为残基身份，不根据 residue name、chain、resid 或空间位置重新建立身份。

## Reuse

已有 2.4 正式结果是否适用于当前体系由 2.1 判断。

若当前 Task Sheet 已引用 2.1 判定可直接使用的 2.4 正式结果，直接复用该结果；否则执行当前 2.4 工作项。本 Skill 不重新维护与 2.1 平行的已有结果适用性判据。

## 代表实例与参数化模型

执行前读取：

`references/parameterization_model.md`

按其中规则检查当前工作项全部同名实例是否能够共用同一套参数定义，从中选择一个代表实例，提取其 Stage 1 重原子结构并补氢，随后确定参数化模型的原子集合与原子顺序。

生成：

```text
parameterization_model.mol2
parameterization_model.map
```

二者描述同一个代表实例，并使用同一原子集合与原子顺序。

## OPT / FREQ

执行前读取：

`references/opt_freq.md`

按其中规则确定代表实例参数化模型的总电荷、自旋多重度与实际量化计算设置，完成 OPT 和 FREQ，并检查 FREQ 结果是否能够用于当前参数化。

最终实际采纳的 OPT / FREQ 任务路径保留用于正式结果记录。

## 电荷拟合

执行前读取：

`references/charge_fitting.md`

根据当前采用的 RESP / RESP2 方案完成所需 SP、Multiwfn 电荷拟合及检查，生成：

```text
charge_fitting_result.yaml
parameterization.chg
```

`parameterization.chg` 与 `parameterization_model.mol2` 的原子顺序保持可确定的一一对应，并作为 Sobtop 参数化使用的最终电荷文件。

2.4 的电荷拟合对象就是完整的代表实例参数化模型；不采用 2.3 针对 `charge_modification_scope` 建立的无约束 / 有约束并行拟合机制。

最终实际采纳的 SP 任务路径保留用于正式结果记录。

## Sobtop 参数化

基于检查通过的 OPT 结构生成用于 Sobtop 成键项拟合的 mol2，并与对应的频率计算结果一同用于成键参数拟合。

频率计算结果文件：

```text
ORCA     → *.hess
Gaussian → *.fch / *.fchk
```

使用 Sobtop 参数化时，若当前体系所需的 LJ 参数缺失，根据当前实际体系从 `02_topology_preparation/references/12-6.itp` 或 `02_topology_preparation/references/12-6-4.itp` 中提取适用参数补充。

Sobtop 生成的 `.itp` 中 residue name 或 atom name 与用于 Sobtop 的 mol2 中对应原子不一致时，按该 mol2 中对应原子的 residue name 和 atom name 修正后，再形成正式：

```text
parameterized_topology.itp
```

最终 `parameterized_topology.itp` 的 atom name、原子顺序和电荷必须能够与代表实例参数化模型及 `parameterization.chg` 建立确定的一一对应关系。

## 当前工作项全部实例的结构与 map

`parameterized_topology.itp` 生成并检查通过后，以成功完成参数化的代表实例作为补氢模板，对当前工作项中的其它同名实例补氢。

其它实例保留各自在 `stage1_final.pdb` 中的重原子坐标；模板提供代表实例已经确定的补氢方式与原子定义，新增 H 的坐标根据各实例自身重原子几何建立，不复制代表实例的坐标。

全部实例采用与最终 `parameterized_topology.itp` 一致的 residue name、atom name 和 residue 内原子顺序，生成：

```text
parameterized_structure.gro
parameterized_structure.map
```

二者覆盖当前工作项中的全部同名实例。

`parameterized_structure.map` 以及代表实例的 `parameterization_model.map` 均沿用 Stage 2 map 共享核心字段：

```yaml
output_atom_index:
original_atom_serial:
component_id:
residue_id:
operations:
```

来自 `stage1_final.pdb` 的原子沿用 `stage1_final_map.yaml` 中对应 record 的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，只更新当前 `output_atom_index`。

2.4 新增 H 建立新 record：

```text
original_atom_serial = null
component_id + residue_id = 该 H 所属真实 residue 的既有身份
operations = [2.4ADD]
```

2.4 的 Stage 2 operation code 只有：

```text
2.4ADD
```

## Validation

当前 2.4 工作项形成正式结果前至少确认：

- 当前工作项全部同名实例已完成参数定义一致性检查；不存在需要通过不同 residue name 区分但仍被静默合并参数化的实例；
- `parameterization_model.mol2` 与 `parameterization_model.map` 描述同一个代表实例，原子集合和原子顺序一致；
- 最终采纳的 OPT、FREQ 和 SP 结果完成对应检查，电荷拟合已形成明确选中的 `parameterization.chg`；
- `parameterization.chg` 与代表实例参数化模型的原子顺序一一对应；
- `parameterized_topology.itp` 的 residue name、atom name、原子顺序和电荷能够与代表实例参数化模型及 `parameterization.chg` 确定对应；
- `parameterized_structure.gro` 与 `parameterized_structure.map` 覆盖当前工作项全部同名实例，每个实例的 residue name、atom name 和 residue 内原子顺序与 `parameterized_topology.itp` 一致；
- `parameterized_structure.map` 中各实例继续使用自身的 `component_id + residue_id`，Stage 1 来源原子保留既有 provenance，2.4 新增 H 使用 `2.4ADD`。

## 正式结果

正式结果生成前按需读取仓库级 `../../references/result_generation_rules.md`，并读取：

`references/results.md`

按其中定义生成：

```text
independent_nonstandard_parameterization_result.yaml
```

该正式结果记录统一定位：

```text
parameterization_model.mol2
parameterization_model.map
parameterization.chg
charge_fitting_result.yaml
parameterized_topology.itp
parameterized_structure.gro
parameterized_structure.map
```

并记录当前处理残基名、代表实例、当前工作项全部实例、实际补氢依据以及最终采纳的 OPT / FREQ / SP 任务路径和参数生成方法。

完成后按仓库级 Task Execution 规则更新当前 Task Sheet 的 2.4 工作项状态，并将 `independent_nonstandard_parameterization_result.yaml` 的完整路径登记到项目结果索引。上述七个结果文件由该正式结果记录统一定位，不在项目结果索引中分别登记。

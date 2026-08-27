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

## OPT / FREQ

执行前读取：

`references/opt_freq.md`

按其中规则确定参数化模型的总电荷、自旋多重度与实际计算设置，完成几何优化和 FREQ 计算，并执行 FREQ 结果检查。

最终实际采纳的 OPT / FREQ 任务路径保留用于正式结果记录。

## 电荷拟合

执行前读取：

`references/charge_fitting.md`

根据当前采用的 RESP / RESP2 方案完成所需 SP、Multiwfn 电荷拟合及检查，生成：

```text
charge_fitting_result.yaml
parameterization.chg
```

`parameterization.chg` 与参数化模型原子顺序保持可确定的一一对应，并作为 Sobtop 参数化使用的最终电荷文件。

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

## 正式结果记录

完成本工作项后读取：

`references/topology_linked_parameterization_result.md`

按其中定义生成并登记：

```text
topology_linked_parameterization_result.yaml
```

该 reference 统一定义正式结果记录中的上游依赖、六个核心结果、最终采纳的 OPT / FREQ / SP 任务路径、`standard_atom_deletions`、`charge_modification_scope` 及项目结果索引登记语义。

随后按仓库级 Task Execution 规则更新当前 Task Sheet 的 2.3 工作项状态，并记录当前正式结果路径。

2.3 不直接修改 2.2 基线结构 / 拓扑。

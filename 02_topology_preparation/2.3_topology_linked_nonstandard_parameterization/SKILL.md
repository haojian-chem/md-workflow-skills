---
name: topology_linked_nonstandard_parameterization
description: 拓扑准备 2.3。对 2.1 已拆分确定需要共同处理的 topology-linked 非标准残基组合建立参数化模型，完成量化计算、电荷拟合与 Sobtop 参数化，并生成正式参数化结果。
---

# 2.3 Topology-linked nonstandard parameterization

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 处理对象与前置条件

当前 2.3 工作项必须来自一个已经完成且仍适用的 2.1 topology-preparation setup 拆分方案。

该 2.1 可以记录在当前 Task Sheet，也可以记录在同一科研任务的前序 Task Sheet；当前工作开始前必须能够定位对应 2.1 工作项以及其中确定的 topology-linked 参数化对象。

一个 2.3 工作项可以包含一个或多个需要共同参数化的 `TOPOLOGY_LINKED_NONSTANDARD` 残基。2.3 直接消费 2.1 已经形成的分组，不在本环节重新拆分或改变处理归属。

## 目标

对当前 topology-linked 参数化对象完成：

```text
建立参数化模型
→ 量化计算
→ 电荷拟合并生成 parameterization.chg
→ Sobtop 参数化并生成 parameterized_topology.itp
```

形成正式结果记录：

`topology_linked_parameterization_result.yaml`

## 输入与依据

开始当前工作项时至少读取：

- 当前 Task Sheet；
- 适用于当前处理对象的已完成 2.1 拆分方案；
- 当前体系对应的正式 `classification_result.yaml`，读取与当前处理对象相关、`judgment: CONFIRMED` 且 `topology_effect_applied: true` 的 `topology_linked_checks[]`；
- 当前处理对象对应的 `stage1_final.pdb` 与 `stage1_final_map.yaml`；
- 当前对象需要标准残基全原子片段时，对应标准残基 topology 正式结果及其全原子结构 / map；
- 非标准残基补氢实际使用的 CCD 文件；
- 当前实际采用的力场及其它参数定义来源。

这些正式结构 / topology 结果可以来自当前 Task Sheet，也可以来自同一科研任务的前序 Task Sheet。

力场及其它参数定义来源以 2.1 方案记录为当前基线，并结合当前 Task Sheet、相关前序 Task Sheet、正式记录 / 日志、当前对话和用户已明确决定再次核对。当前工作需要而仍不能唯一确定时向用户确认。

如果新的确认结果会使 2.1 中的参数化对象分组或参数来源基础失效，先更新 / 重新形成适用的 2.1 方案，再继续 2.3。

当前工作沿用正式结果中已有的 `component_id + residue_id` 作为残基身份，不根据 residue name、chain、resid 或当前空间位置重新建立。

## Reuse

当前 2.3 不设置 reuse。

在 Stage 2 reuse 机制后续单独完成设计与接口更新前，每次实际进入当前工作项，都对当前 2.1 方案指定的 topology-linked 参数化对象重新建立参数化模型并完成本 Skill 规定的参数化流程。

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

同时确定并保留：

1. `standard_atom_deletions`：标准残基一侧因已确认拓扑连接而需要从最终结构 / topology 中删除的原子；
2. `charge_modification_scope`：最终 topology 中需要采用本次新电荷的全部真实残基，包括相关 `STANDARD_RESIDUE` 与 `TOPOLOGY_LINKED_NONSTANDARD` 残基。

仅作为参数化模型外围环境或封端环境保留的部分不列入 `charge_modification_scope`。

## OPT / FREQ

执行前读取：

`references/opt_freq.md`

按其中规则确定参数化模型的总电荷、自旋多重度与实际计算设置，完成几何优化和 FREQ，并执行 FREQ 结果检查。

最终实际采纳的 OPT / FREQ 任务路径保留用于正式结果记录。

## 电荷拟合

执行前读取：

`references/charge_fitting.md`

根据当前采用的 RESP / RESP2 方案完成所需 SP、Multiwfn 电荷拟合及其中定义的检查，生成：

```text
charge_fitting_result.yaml
parameterization.chg
```

`parameterization.chg` 与参数化模型原子顺序保持可确定的一一对应，并作为 Sobtop 参数化使用的最终电荷文件。

最终实际采纳的 SP 任务路径保留用于正式结果记录。

## Sobtop 参数化

基于检查通过的 OPT 结构生成用于 Sobtop 成键项拟合的 mol2，并与对应 FREQ 结果一同用于成键参数拟合。

频率计算结果文件：

```text
ORCA     → *.hess
Gaussian → *.fch / *.fchk
```

使用 Sobtop 参数化时，若当前体系所需 LJ 参数缺失，根据当前实际体系从：

```text
02_topology_preparation/references/12-6.itp
02_topology_preparation/references/12-6-4.itp
```

中提取适用参数补充。

Sobtop 生成的 `.itp` 中 residue name 或 atom name 与用于 Sobtop 的 mol2 中对应原子不一致时，按该 mol2 中对应原子的 residue name 和 atom name 修正后，再形成正式：

`parameterized_topology.itp`

## 正式结果记录

完成本工作项后读取：

`references/topology_linked_parameterization_result.md`

按其中定义生成并登记：

`topology_linked_parameterization_result.yaml`

该 reference 统一定义正式结果记录中的上游依赖、六个核心结果、最终采纳的 OPT / FREQ / SP 任务路径、`standard_atom_deletions`、`charge_modification_scope` 及项目结果索引登记语义。

随后按仓库级 Task Execution 规则更新当前 Task Sheet 工作项状态，并记录当前正式结果路径。

当前工作不直接修改标准残基 topology 生成的基线结构 / topology。

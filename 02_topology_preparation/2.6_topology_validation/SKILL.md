---
name: topology_validation
description: 对 topology_integration_result.yaml 定位的当前结构文件与拓扑文件执行独立、只读终检，检查体系 .top 引用、结构文件与拓扑文件中的分子/残基/原子对应、topology-linked 关系、标准残基原子删除与电荷修改，并使用 gmx grompp 记录预处理结果，生成 topology_validation_result.yaml。
---

# Topology validation

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 目标

对当前拓扑整合正式结果执行独立、只读终检：

```text
检查体系 .top 中的 #include
→ 检查结构文件与 .top / .itp 中的分子、残基和原子
→ 检查 topology-linked 关系
→ 检查标准残基原子删除
→ 检查标准残基一侧电荷修改
→ 执行 gmx grompp
→ 生成 topology_validation_result.yaml
```

当前职责只检查已经形成的结构文件和拓扑文件，不修改结构文件、体系 `.top`、`.itp`、map 或参数文件，
也不在发现问题时顺手修正拓扑。

## 输入与依据

当前工作项从 Task Sheet 读取两个直接正式依赖：

1. `classification_result.yaml`；
2. `topology_integration_result.yaml`。

`classification_result.yaml` 提供既有的 `component_id + residue_id`、`topology_class` 和
`topology_linked_checks`。需要解释这些字段时读取：

`../../01_structure_preparation/1.2_component_and_residue_classification/references/result_recording_rules.md`

`topology_integration_result.yaml` 定位当前结构文件、当前 map、体系 `.top`、本次拓扑整合生成的 `.itp`，
以及当前拓扑整合实际采用的 topology-linked 参数化正式结果。需要解释该结果的 `references`、`moleculetypes`
和 `results` 时读取：

`../2.5_topology_integration_and_assembly/references/results.md`

需要解释 topology-linked 参数化正式结果中的 `standard_atom_deletions` 和
`charge_modification_scope` 时读取：

`../2.3_topology_linked_nonstandard_parameterization/references/topology_linked_parameterization_result.md`

当前使用的 `classification_result.yaml` 必须是拓扑整合正式结果实际引用的分类正式结果。结构文件、map、
体系 `.top` 和 `.itp` 均使用 `topology_integration_result.yaml` 中记录的实际完整路径，不根据默认 basename、
目录顺序或“最新文件”重新推断。

若两个直接正式依赖不能唯一确定，或其记录的必需检查文件无法读取，不伪造依赖这些文件的检查结果；
先解决输入定位问题，再完成当前工作项。

## No reuse

当前职责不设置 reuse。

每次实际进入当前工作项，都针对当前 `classification_result.yaml`、当前
`topology_integration_result.yaml` 及其记录的当前结构文件和拓扑文件重新执行全部规定检查；
不使用既有 `topology_validation_result.yaml` 跳过本次检查。

## 检查体系 `.top` 中各 `#include` 指向的文件

读取体系 `.top` 中实际出现的每个 `#include`，解析其实际文件路径，并分别检查该文件是否存在、是否可读取。

本项只检查体系 `.top` 中直接写出的 `#include` 所指文件，不在本项中检查参数内容、`moleculetype` 定义
或其它拓扑语义。

## 检查当前结构文件与体系 `.top` / `.itp` 中记录的分子、残基和原子

按体系 `.top` 的 `[ molecules ]` 中记录的 `moleculetype` 顺序和数量，读取对应
`moleculetype` 的 `[ atoms ]`，展开当前拓扑所描述的分子、残基和原子顺序。

将展开结果与当前结构文件逐项比较，检查：

- 分子数量；
- 分子顺序；
- 每个分子的原子数量；
- residue 顺序；
- atom 顺序；
- 对应位置的 residue name；
- 对应位置的 atom name。

发现差异时，记录对应 `moleculetype`、molecule instance、结构文件位置、拓扑文件位置以及两侧实际值。

## 检查已确认并产生 topology effect 的 `topology-linked` 关系

从 `classification_result.yaml.topology_linked_checks` 读取同时满足以下条件的关系：

```text
judgment = CONFIRMED
且
topology_effect_applied = true
```

这些 `COVALENT_CONNECTION` 和 `METAL_COORDINATION` 都是当前 topology-linked 参数化与拓扑整合需要落实的
正式关系。

使用正式结果记录的关系两端身份，在需要时结合当前 map 定位最终拓扑中的对应 atom；再依据当前拓扑整合实际采用的
topology-linked 参数化结果，检查其中针对该关系形成的拓扑项是否已经写入最终拓扑。

- `COVALENT_CONNECTION` 使用 `atom_1` 和 `atom_2` 定位两端；
- `METAL_COORDINATION` 使用 `metal` 和 `donor` 定位两端。

不根据 `relation_type` 另行发明拓扑表示规则；两类关系均以当前 topology-linked 参数化结果及拓扑整合结果
实际采用的拓扑项为检查依据。

`judgment = REJECTED` 或 `topology_effect_applied = false` 的记录不属于本项要求最终拓扑必须体现的关系。

## 检查 topology-linked 参数化要求删除的标准残基原子

从 `topology_integration_result.yaml` 记录的实际来源定位当前拓扑整合采用的 topology-linked 参数化正式结果，
读取其中的 `standard_atom_deletions`。

对每个指定删除的标准残基 atom，检查：

- 当前结构文件中不存在该 atom；
- 最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 中不存在该 atom。

使用参数化正式结果记录的标准结构 atom identity 和相应 map，保持与既有
`component_id + residue_id` 的对应，不根据 atom name 单独重建原子身份。

## 检查 topology-linked 参数化要求的标准残基一侧电荷修改

从 `topology_integration_result.yaml` 记录的实际来源定位当前拓扑整合采用的 topology-linked 参数化正式结果、
对应电荷文件和参数化模型 map，读取其中的 `charge_modification_scope`。

对该范围中 `topology_class: STANDARD_RESIDUE` 的每个 residue，通过参数化模型 map 与电荷文件确定相关 atom 的
指定电荷，并逐 atom 检查最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 所记录 `charge` 是否采用这些值。

正式结果只按 residue 记录实际检查的 atom 数量和发现电荷差异的 atom 数量，不展开 atom-level 电荷明细。

## 使用 `gmx grompp` 检查当前结构文件和体系 `.top`

默认使用预建检查参数：

`references/grompp_validation.mdp`

该预设只用于 topology preprocessing，不启用 topology preprocessor macro，不要求当前结构文件已经完成周期盒构建，
生成的临时 `.tpr` 不作为模拟输入。

若当前 GROMACS 版本或实际检查对象需要等价的预处理参数调整，可以在当前工作目录生成检查用 `.mdp`；
实际使用的 `.mdp` 路径和设置必须保留在正式结果记录的命令中，不把该文件解释为后续模拟方案。

使用当前结构文件和体系 `.top` 执行 `gmx grompp`，记录：

- 实际使用的 GROMACS version；
- 实际执行命令；
- process return code；
- note；
- warning；
- error。

不使用 `-maxwarn` 强制越过 warning。`return_code = 0` 不能替代前述五项独立检查。

检查用 `.mdp`、临时 `.tpr` 及其它 preprocessing 工作文件不自动成为正式结果。

## 正式结果

生成正式结果前读取：

`references/results.md`

按其中定义生成唯一正式结果：

`topology_validation_result.yaml`

该 YAML 只记录实际检查对象和检查结果，不记录 `PASS`、`FAIL`、`COMPLETE`、overall conclusion 或
blocking finding。

项目结果索引只登记 `topology_validation_result.yaml`。当前结构文件、map、体系 `.top`、`.itp`、检查用 `.mdp`
和临时 `.tpr` 不作为当前职责的新结果重复登记。

完成全部六项检查并生成 `topology_validation_result.yaml` 后，当前工作项完成；随后按 Task Execution 规则更新
Task Sheet。检查中发现的问题继续保留在正式结果中，不改变当前工作项已经完成检查并生成正式结果这一事实。

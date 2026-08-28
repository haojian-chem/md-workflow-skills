---
name: topology_integration_and_assembly
description: 根据当前 Task Sheet 指定的标准残基拓扑、topology-linked 与独立非标准残基参数化正式结果，以及可直接采用的 solvent / ion 拓扑定义，完成 GROMACS moleculetype 组织、全原子结构与拓扑整合，并生成正式拓扑整合结果。
---

# Topology integration and assembly

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 目标

消费当前 Task Sheet 已指定的拓扑与参数化正式结果，对当前体系完成：

```text
moleculetype 组织
→ 整合全原子 .gro 与对应 map
→ 整合各 moleculetype .itp 与附属 .itp
→ 汇总额外参数定义
→ 生成体系 .top
→ 生成 topology_integration_result.yaml
```

当前职责继承既有 `component_id + residue_id`、component 的 residue 组成与顺序，以及已经确认的
`topology-linked` 关系，不重新建立这些身份或关系。

## 输入与依据

当前工作项从 Task Sheet 读取本次整合明确指定的输入集合，包括：

- 当前体系已经确定采用的基础力场及其它参数定义来源；
- 当前体系对应的 `classification_result.yaml`、`stage1_final.pdb` 和 `stage1_final_map.yaml`；
- Task Sheet 指定的全部标准残基拓扑生成正式结果；
- Task Sheet 指定的全部 topology-linked 非标准残基参数化正式结果；
- Task Sheet 指定的全部独立非标准参数化正式结果；
- 无需独立参数化、可直接采用既定拓扑定义的 solvent / ion 实际对象及其参数定义来源。

三类前置工作项均可以为 0 / 1 / N 个。同一类存在多个工作项时逐项消费，不假定每类只有一个正式结果。

只读取当前整合实际需要的上游结果文件、结果字段和外部定义；不扫描项目自行选择前置结果，也不根据目录顺序、
文件名或“最新文件”重建输入集合。输入文件无法唯一定位时，先解决该歧义再继续整合。

正式结果内部需要记录的具体文件引用及 reference key 读取：

`references/results.md`

## Reuse

当前职责不设置独立 reuse 判断。已有拓扑整合正式结果是否直接采用，以当前 Task Sheet 已经记录的决定为准；
需要实际执行当前工作项时，直接消费 Task Sheet 指定的输入集合。

## 组织 `moleculetype`

生成整合结构前读取：

`references/moleculetype_organization.md`

按其中规则确定当前体系的 `moleculetype` 组成、组织顺序和名称。`moleculetype` 是 GROMACS 拓扑表示，
不改变既有 component 或 residue 身份。

## 生成整合全原子结构与 map

完成 `moleculetype` 组织后，生成：

```text
integrated.gro
integrated.map
```

结构按已经确定的 `moleculetype` 组织组合。同一个 `moleculetype` 同时包含标准残基和 topology-linked
非标准残基时，标准残基在前，topology-linked 非标准残基在后；各来源结构内部已有的 residue / atom
相对顺序保持不变。

各类结构内容按以下来源取得：

- 标准残基从对应标准残基拓扑生成正式结果中的全原子 `.gro` 提取，并应用相关 topology-linked 参数化正式结果
  记录的 `standard_atom_deletions`；
- topology-linked 非标准残基从对应参数化正式结果的 `parameterized_structure.gro` 中，结合该参数化工作项包含的
  非标准残基身份和 `parameterization_model.map`，提取实际进入整合结构的原子；
- 独立非标准残基从对应参数化正式结果的 `parameterized_structure.gro` 中，结合
  `parameterized_structure.map` 提取当前体系实际实例；
- 无需独立参数化、直接采用既定拓扑定义的 solvent / ion，从 `stage1_final.pdb` 中提取当前实际 residue，
  并通过 `stage1_final_map.yaml` 保持既有 `component_id + residue_id` 与原子对应关系。若对应 residue 缺失该拓扑定义
  所规定的原子，按实际采用的拓扑定义补全这些原子。

完成原子集合与顺序组合后，按新的 residue 顺序从 1 开始连续重新编号 `.gro` residue number；同一 residue
的全部 atom 使用同一 residue number。随后按当前 atom 顺序从 1 开始连续重新编号 `.gro` atom number。
这些文件内编号不改变既有 `component_id + residue_id`。

`integrated.map` 与 `integrated.gro` 同时形成，只记录整合后实际存在的原子。已有的 `component_id + residue_id`
和可继承的逐原子映射继续沿用，并以整合 `.gro` 的 atom number 更新 `current_atom_serial`。

对按既定拓扑定义补全、且进入整合前不存在对应原子的 solvent / ion atom，在 `integrated.map` 中建立新 atom
record：`original_atom_serial: null`，使用所属 residue 既有的 `component_id + residue_id`，并记录
`operations: [2.5ADD]`。`2.5ADD` 的共享 operation-code 语义读取：

`../../references/atom_mapping_rules.md`

完成后冻结当前整合结果的 residue / atom 顺序；后续 `.itp` 生成不得再改变这套顺序。

## 整合 `.itp`

整合 `.gro` 与 map 的顺序冻结后读取：

`references/itp_integration.md`

按其中规则生成当前整合需要的 `<moleculetype name>.itp`、对应 position restraint `.itp`，以及本次需要的
独立参数定义 `.itp`。每个 `moleculetype` 内的局部原子编号均以已经冻结的整合结构顺序为依据建立，不把 `.gro`
全局 atom number 直接当作 `.itp` 的 `[ atoms ] nr`。

## 生成 `.top`

完成各当前生成的 `moleculetype` `.itp` 及独立参数定义 `.itp` 后，生成：

`topol.top`

`.top` 按实际依赖关系依次组织：

1. 引用当前体系已经确定采用的基础力场 topology 入口文件；
2. 若本次生成独立参数定义 `.itp`，在各 `moleculetype` 定义之前引用该文件；
3. 引用本次整合生成的各 `<moleculetype name>.itp`；
4. 引用无需独立参数化、直接采用既定拓扑定义的 solvent / ion 拓扑文件；
5. 对采用 `POSRES_WATER` 的 solvent topology，在对应 solvent topology 引用之后保留或设置
   `#ifdef POSRES_WATER` 条件 position restraint；
6. 写入 `[ system ]`；
7. 写入 `[ molecules ]`。

各 `#include` 按实际依赖关系组织，不重复引用同一拓扑文件。

`[ system ]` 使用当前 Task Sheet 的 `target_id` 作为体系名称。

`[ molecules ]` 按 `integrated.gro` 中各分子的实际排列顺序填写。本次整合生成的 `moleculetype` 使用已经确定的
名称；直接采用既定拓扑定义的 solvent / ion 使用对应 `moleculetype` 名称。每个条目的数量与
`integrated.gro` 中对应 `moleculetype` 的实际分子数量一致。

## 正式结果

完成拓扑整合后读取：

`references/results.md`

按其中定义生成正式结果记录：

`topology_integration_result.yaml`

正式结果记录必须能够定位本次生成的 `integrated.gro`、`integrated.map`、`topol.top` 和全部 `.itp`，
并保存当前 `moleculetype` 的组成以及本次实际使用的上游 / 外部文件引用。

随后按 `references/results.md` 定义的项目结果索引登记范围登记正式结果，并按仓库级 Task Execution 规则
更新当前 Task Sheet 工作项状态与正式结果路径。

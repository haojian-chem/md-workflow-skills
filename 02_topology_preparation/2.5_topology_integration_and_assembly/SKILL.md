---
name: topology_integration_and_assembly
description: 根据 2.1 已建立的拓扑准备拆分方案，消费当前体系指定的标准残基 topology、topology-linked 与独立非标准参数化正式结果，以及可直接采用的 solvent / ion topology 定义，完成 GROMACS moleculetype 组织、全原子结构与 topology 整合。
---

# Topology integration and assembly

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 前置条件

当前 2.5 工作必须基于一个已经完成且仍适用的 2.1 topology-preparation setup 拆分方案。

该 2.1 可以记录在当前 Task Sheet，也可以记录在同一科研任务的前序 Task Sheet；当前工作开始前必须能够定位对应 2.1 工作项，以及其中确定的本次 topology integration 输入集合。

2.5 不重新拆分当前体系，也不自行决定哪些 2.2 / 2.3 / 2.4 结果属于本次整合；这些输入集合由适用的 2.1 方案和当前 Task Sheet 共同定位。

## 目标

对当前体系完成：

```text
moleculetype 组织
→ 整合全原子 .gro 与对应 map
→ 整合各 moleculetype .itp 与附属 .itp
→ 汇总额外参数定义
→ 生成体系 .top
→ 生成 topology_integration_result.yaml
```

当前职责继承既有 `component_id + residue_id`、component 的 residue 组成与顺序，以及已经确认的 `topology-linked` 关系，不重新建立这些身份或关系。

## 输入与依据

当前工作项至少读取：

- 当前 Task Sheet；
- 适用于当前体系和处理范围的已完成 2.1 拆分方案；
- 当前体系实际采用的基础力场及其它参数定义来源；
- 当前体系对应的 `classification_result.yaml`、`stage1_final.pdb` 和 `stage1_final_map.yaml`；
- 2.1 方案 / 当前 Task Sheet 指定的全部标准残基 topology 正式结果；
- 指定的全部 topology-linked 非标准残基参数化正式结果；
- 指定的全部独立非标准参数化正式结果；
- 无需独立参数化、可直接采用既定 topology 定义的 solvent / ion 实际对象及其参数定义来源。

三类前置工作项均可以为 0 / 1 / N 个。同一类存在多个工作项时逐项消费，不假定每类只有一个正式结果。

这些前置结果可以来自当前 Task Sheet，也可以来自同一科研任务的前序 Task Sheet；当前 2.5 只要求它们能够由适用的 2.1 方案和当前执行记录唯一定位。

力场及其它参数定义来源以 2.1 方案为当前基线，并结合当前 Task Sheet、相关前序 Task Sheet、正式记录 / 日志、当前对话和用户已明确决定再次核对。若新的确认结果会改变 2.1 中已经形成的输入集合或对象归属，先更新 / 重新形成适用的 2.1 方案，再继续 2.5。

只读取当前整合实际需要的上游结果文件、结果字段和外部定义；不扫描项目自行选择前置结果，也不根据目录顺序、文件名或“最新文件”重建输入集合。

正式结果内部需要记录的具体文件引用及 reference key 读取：

`references/results.md`

## Reuse

当前 2.5 不设置 reuse。

在 Stage 2 reuse 机制后续单独完成设计与接口更新前，每次实际进入当前工作项，都消费当前明确输入集合重新生成 topology integration 结果。

## 组织 `moleculetype`

生成整合结构前读取：

`references/moleculetype_organization.md`

按其中规则确定当前体系的 `moleculetype` 组成、组织顺序和名称。`moleculetype` 是 GROMACS topology 表示，不改变既有 component 或 residue 身份。

## 生成整合全原子结构与 map

完成 `moleculetype` 组织后，体系整合 `.gro` 默认命名为：

`sys.gro`

并同步生成：

`integrated.map`

结构按已经确定的 `moleculetype` 组织组合。同一个 `moleculetype` 同时包含标准残基和 topology-linked 非标准残基时，标准残基在前，topology-linked 非标准残基在后；各来源结构内部已有的 residue / atom 相对顺序保持不变。

各类结构内容按以下来源取得：

- 标准残基从对应标准残基 topology 正式结果中的全原子 `.gro` 提取，并应用相关 topology-linked 参数化正式结果记录的 `standard_atom_deletions`；
- topology-linked 非标准残基从对应参数化正式结果的 `parameterized_structure.gro` 中，结合该参数化工作项包含的非标准残基身份和 `parameterization_model.map`，提取实际进入整合结构的原子；
- 独立非标准残基从对应参数化正式结果的 `parameterized_structure.gro` 中，结合 `parameterized_structure.map` 提取当前体系实际实例；
- 无需独立参数化、直接采用既定 topology 定义的 solvent / ion，从 `stage1_final.pdb` 中提取当前实际 residue，并通过 `stage1_final_map.yaml` 保持既有 `component_id + residue_id` 与原子对应关系；若对应 residue 缺失该 topology 定义所规定的原子，按实际采用的定义补全这些原子。

完成原子集合与顺序组合后，按新的 residue 顺序从 1 开始连续重新编号 `.gro` residue number；同一 residue 的全部 atom 使用同一 residue number。随后按当前 atom 顺序从 1 开始连续重新编号 `.gro` atom number。这些文件内编号不改变既有 `component_id + residue_id`。

`integrated.map` 与体系整合 `.gro` 同时形成，只记录整合后实际存在的原子。已有的 `component_id + residue_id` 和可继承的逐原子映射继续沿用，并以体系整合 `.gro` 的 atom number 更新 `current_atom_serial`。

对按既定 topology 定义补全、且进入整合前不存在对应原子的 solvent / ion atom，在 `integrated.map` 中建立新 atom record：`original_atom_serial: null`，使用所属 residue 既有的 `component_id + residue_id`，并记录 `operations: [2.5ADD]`。`2.5ADD` 的共享 operation-code 语义读取：

`../../references/atom_mapping_rules.md`

完成后冻结当前整合结果的 residue / atom 顺序；后续 `.itp` 生成不得再改变这套顺序。

## 整合 `.itp`

体系整合 `.gro` 与 map 的顺序冻结后读取：

`references/itp_integration.md`

按其中规则生成当前整合需要的 `<moleculetype name>.itp`、对应 position restraint `.itp`，以及本次需要的独立参数定义 `.itp`。每个 `moleculetype` 内的局部原子编号均以已经冻结的整合结构顺序为依据建立，不把 `.gro` 全局 atom number 直接当作 `.itp` 的 `[ atoms ] nr`。

## 生成 `.top`

完成各当前生成的 `moleculetype` `.itp` 及独立参数定义 `.itp` 后，体系主 topology 默认命名为：

`sys.top`

`.top` 按实际依赖关系依次组织：

1. 引用当前体系已经确定采用的基础力场 topology 入口文件；
2. 若本次生成独立参数定义 `.itp`，在各 `moleculetype` 定义之前引用该文件；
3. 引用本次整合生成的各 `<moleculetype name>.itp`；
4. 引用无需独立参数化、直接采用既定 topology 定义的 solvent / ion topology 文件；
5. 对采用 `POSRES_WATER` 的 solvent topology，在对应 solvent topology 引用之后保留或设置 `#ifdef POSRES_WATER` 条件 position restraint；
6. 写入 `[ system ]`；
7. 写入 `[ molecules ]`。

各 `#include` 按实际依赖关系组织，不重复引用同一 topology 文件。

`[ system ]` 使用当前 Task Sheet 的 `target_id` 作为体系名称。

`[ molecules ]` 按体系整合 `.gro` 中各分子的实际排列顺序填写。本次整合生成的 `moleculetype` 使用已经确定的名称；直接采用既定 topology 定义的 solvent / ion 使用对应 `moleculetype` 名称。每个条目的数量与体系整合 `.gro` 中对应 `moleculetype` 的实际分子数量一致。

## 正式结果

完成 topology integration 后读取：

`references/results.md`

按其中定义生成：

`topology_integration_result.yaml`

正式结果记录必须能够定位本次生成的体系整合 `.gro`、`integrated.map`、体系主 `.top` 和全部 `.itp`，并保存当前 `moleculetype` 的组成以及本次实际使用的上游 / 外部文件引用。

随后按 `references/results.md` 定义的项目结果索引登记范围登记正式结果，并按仓库级 Task Execution 规则更新当前 Task Sheet 工作项状态与正式结果路径。

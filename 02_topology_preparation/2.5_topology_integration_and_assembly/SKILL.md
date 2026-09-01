---
name: topology_integration_and_assembly
description: 根据 2.1 已建立的拓扑准备拆分方案，建立当前 2.5 integration target，消费指定的标准残基 topology、topology-linked 与独立非标准参数化正式结果，以及可直接采用的 solvent / ion topology 定义，完成 GROMACS moleculetype、全原子结构与 topology 整合，并记录实际 target 合流关系。
---

# Topology integration and assembly

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 前置条件

当前 2.5 工作必须基于一个已经完成且仍适用的 2.1 topology-preparation setup 拆分方案。

该 2.1 可以记录在当前 Task Sheet，也可以记录在同一科研任务的前序 Task Sheet；当前工作开始前必须能够定位对应 2.1 工作项，以及其中确定的本次 topology integration 输入集合。

2.5 不重新拆分当前体系，也不自行决定哪些 2.2 / 2.3 / 2.4 结果属于本次整合；这些输入集合由适用的 2.1 方案和当前 Task Sheet 共同定位。

真正执行当前 integration object 时，建立当前 2.5 local target 和：

```text
targets/target_xxx.yaml
```

## Target merge semantics

当前 2.5 target 是 topology preparation 中的显式合流节点。

其 `source_target_records` 必须逐项记录**本次实际参与 current integrated system 形成的 target-scoped upstream objects**，包括按实际情况存在的：

- 当前采用的每个 2.2 standard-residue topology target；
- 当前采用的每个 2.3 topology-linked parameterization target；
- 当前采用的每个 2.4 independent parameterization target；
- 对无需独立参数化、直接从 Stage 1 structure 提取并使用既定 topology definition 的 solvent / ion，记录其实际 Stage 1 source target；
- 其它真正形成当前 integrated object 的 target-scoped source，如当前 2.1 / Task Sheet 明确存在。

只被读取作为 classification evidence、force-field reference、CCD、parameter library、validation evidence 的对象不因为“被读取”自动成为 source target。

如果某个 2.3 target 自己已经来源于一个 2.2 target，2.5 仍然可以同时把该 2.2 target 与 2.3 target列为直接 sources——前提是本次 integration 确实分别直接消费了二者的正式结果。Target DAG 允许这种多条实际依赖边，不通过“ ancestry 已包含”删除真实直接依赖。

不得把所有 source objects 压回某个固定 Stage 1 / 1.3 root，也不得用 `target_id` 相同判断它们是否属于同一体系。

## 目标

对当前 2.5 integration target 完成：

```text
moleculetype 组织
→ 整合全原子 .gro 与对应 integrated.map
→ 整合各 moleculetype .itp 与附属 .itp
→ 汇总额外参数定义
→ 生成体系 .top
→ 生成 topology_integration_result.yaml
```

当前职责继承既有 `component_id + residue_id`、component 的 residue 组成与顺序，以及已经确认的 `topology-linked` 关系，不重新建立这些 residue / component identities 或 relation judgments。

## 输入与依据

当前 target 至少读取：

- 当前 Task Sheet；
- 当前 2.5 target record；
- 适用于当前体系和处理范围的已完成 2.1 拆分方案；
- 当前体系实际采用的基础力场及其它参数定义来源；
- 当前体系对应的 `classification_result.yaml`；
- 2.1 方案 / 当前 Task Sheet 指定的全部标准残基 topology 正式结果；
- 指定的全部 topology-linked 非标准残基参数化正式结果；
- 指定的全部独立非标准参数化正式结果；
- 无需独立参数化、可直接采用既定 topology 定义的 solvent / ion 实际对象、其 Stage 1 structure / map 及参数定义来源；
- 上述所有 target-scoped inputs 各自的 target record。

三类前置工作项均可以为 0 / 1 / N 个。同一类存在多个工作项时逐项消费，不假定每类只有一个正式结果。

这些前置结果可以来自当前 Task Sheet，也可以来自同一科研任务的前序 Task Sheet；当前 2.5 只要求它们能够由适用的 2.1 方案和当前执行记录唯一定位。

每个上游正式结果的 current target path 必须从其 own formal result `references.target_record`、对应 map `target_record` 或其它 owner 定义的 current target interface 读取；不根据目录、文件名、“最新文件”或 local `target_id` 重建。

力场及其它参数定义来源以 2.1 方案为当前基线，并结合当前 Task Sheet、相关前序 Task Sheet、正式记录 / 日志、当前对话和用户已明确决定再次核对。若新的确认结果会改变 2.1 中已经形成的输入集合或对象归属，先更新 / 重新形成适用的 2.1 方案，再继续 2.5。

只读取当前整合实际需要的上游结果文件、结果字段和外部定义；不扫描项目自行选择前置结果。

正式结果内部需要记录的具体文件引用及 reference key 读取：

`references/results.md`

## Reuse

当前 2.5 不设置 reuse。

在 Stage 2 reuse 机制后续单独完成设计与接口更新前，每次实际进入当前工作项，都消费当前明确输入集合重新生成 topology integration 结果，并建立 current 2.5 target record。

## Alternative integration branches

如果 2.1 / 当前 Task Sheet / 用户明确要求保留不同的 integration strategy，例如使用不同已完成参数化 branch 组合、不同直接 topology-definition strategy 或其它会形成不同 final topology package 的方案，则：

- 每个实际方案建立独立 2.5 local target；
- 每个 current target 的 `source_target_records` 精确记录该方案实际消费的 targets；
- 每个 target 独立生成 `sys.gro`、`integrated.map`、`.itp`、`.top` 与 result record；
- 不把 mutually exclusive source-branch combinations 混进同一个 2.5 target。

普通执行不自动组合所有可能 upstream branches。

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

- 标准残基从对应 2.2 formal result 中的全原子 `.gro` 提取，并应用相关 2.3 formal result 记录的 `standard_atom_deletions`；
- topology-linked 非标准残基从对应 2.3 `parameterized_structure.gro` 中，结合该参数化 target 包含的非标准残基身份和 `parameterization_model.map`，提取实际进入整合结构的原子；
- 独立非标准残基从对应 2.4 `parameterized_structure.gro` 中，结合 `parameterized_structure.map` 提取当前体系实际实例；
- 无需独立参数化、直接采用既定 topology definition 的 solvent / ion，从对应 Stage 1 final structure 中提取当前实际 residue，并通过对应 Stage 1 map 保持既有 `component_id + residue_id` 与 atom provenance；若对应 residue 缺失该 topology definition 所规定的 atom，按实际采用定义补全这些 atom。

完成原子集合与顺序组合后，按新的 residue 顺序从 1 开始连续重新编号 `.gro` residue number；同一 residue 的全部 atom 使用同一 residue number。随后按当前 atom 顺序从 1 开始连续重新编号 `.gro` atom number。这些文件内编号不改变既有 `component_id + residue_id`。

`integrated.map` 按 `../../references/atom_mapping_rules.md` 的 **multi-source assembly** 语义形成：

- `target_record` 指向 current 2.5 target record；
- `input_maps` 列出实际用于 current `sys.gro` atom provenance 的 2.2 / 2.3 / 2.4 / Stage 1 maps；
- `input_structures` 列出实际向 current `sys.gro` 提供 atom set / coordinates 的 source structures；
- 已有 atoms 从真实 source map 继承 `original_atom_serial`、`component_id + residue_id` 与 operation history；
- 对按既定 topology definition 补全、且所有实际 assembly input structures 中均不存在对应 atom 的 solvent / ion atom，新建 record：`original_atom_serial: null`，使用所属 residue 既有 `component_id + residue_id`，并记录 `operations: [2.5ADD]`；
- 同一真实 atom 不因多个 source maps 中都存在 provenance 而重复建立 output record；
- `current_atom_serial` 与 `sys.gro` atom number 一致。

当前 multi-source map 仍要求所有非空 `original_atom_serial` 能回溯到同一个 1.2 `original_structure`。如果用户要求把不同原始结构 provenance 的 branches 合并成一个 system，当前 shared map contract 不足以无歧义表示，应先扩展 mapping contract，不静默合并。

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

`[ system ]` 只承担 GROMACS 体系描述文本，不作为 target identity。优先使用当前 Task Sheet 已明确的体系名称或当前 2.5 target 的可读 description；未明确时由 Agent 根据当前 integrated object 生成简明描述。不得把任何 local `target_id` 当作跨环节体系身份。

`[ molecules ]` 按体系整合 `.gro` 中各分子的实际排列顺序填写。本次整合生成的 `moleculetype` 使用已经确定的名称；直接采用既定 topology 定义的 solvent / ion 使用对应 `moleculetype` 名称。每个条目的数量与体系整合 `.gro` 中对应 `moleculetype` 的实际分子数量一致。

## 正式结果

完成 topology integration 后读取：

`references/results.md`

按其中定义生成：

`topology_integration_result.yaml`

正式结果记录必须：

- 记录 current 2.5 local `target_id`；
- 在 `references.target_record` 记录 current 2.5 target record 完整绝对路径；
- 定位本次生成的 `sys.gro`、`integrated.map`、体系主 `.top` 和全部 `.itp`；
- 保存当前 `moleculetype` 组成以及本次实际使用的上游 / 外部文件引用。

完成前确认：

- current target record 的 `source_target_records` 与本次 integration 真正消费的 target-scoped upstream objects 一致；
- `integrated.map.target_record == references.target_record`；
- `integrated.map.input_maps` 与 current integrated structure 的实际 atom provenance sources 一致；
- formal result 中列出的 2.2 / 2.3 / 2.4 target-scoped inputs 能通过各自 formal result / map 定位到 current target record，并与 current 2.5 `source_target_records` 对应；
- 不通过 local `target_id` 判断 upstream branch membership。

随后按 `references/results.md` 定义的项目结果索引登记范围登记正式结果，并按仓库级 Task Execution 规则更新当前 Task Sheet 工作项状态与正式结果路径。Target record 不因为创建而单独登记。

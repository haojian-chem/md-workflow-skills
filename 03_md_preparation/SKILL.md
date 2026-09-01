---
name: md-preparation
description: System construction / solvation main Skill。根据当前 Task Sheet 的体系构建目标建立 Stage 3 local target，规划并执行周期盒构建、溶剂添加和离子添加，允许不同 system-construction strategy 形成独立 target branches，并生成 system_construction_result.yaml。
---

# 3 System construction / solvation

通用 Task Execution 规则读取：

`../references/task_execution_rules.md`

本 Skill 在该规则基础上定义体系构建、溶剂化和离子添加的 target、操作计划、检查要求与正式结果。

## 目标

根据当前 Task Sheet 中的处理对象和需要完成的体系构建工作，形成后续模拟使用的结构文件与体系主 `.top`，并为每个 actual Stage 3 local target 生成：

`system_construction_result.yaml`

当前包含三类内部操作：

```text
periodic_box_construction
solvent_addition
ion_addition
```

普通水溶液体系的常见顺序为：

```text
periodic_box_construction
→ solvent_addition
→ ion_addition
```

实际操作计划由当前结构—拓扑状态和体系构建目标决定，可按当前 Task Sheet 的执行范围省略、重复或调整顺序。

## Target object and lineage

每个实际 Stage 3 system-construction object 都是当前 Skill 的 local target，并建立：

```text
targets/target_xxx.yaml
```

Current target record 的 `source_target_records` 记录实际形成当前 Stage 3 system object 的直接 source target(s)。典型情况：

- 从 2.5 `topology_integration_result.yaml` 开始体系构建：source 为该 result 的 `references.target_record` 指向的 2.5 integration target；
- 在后续 Task Sheet 中继续一个已经正式完成的 Stage 3 system branch：source 可以是该已有 `system_construction_result.yaml.references.target_record` 指向的前序 Stage 3 target；
- 当前对象确实由多个 target-scoped upstream objects 合流形成时，逐项记录实际 source target records。

`topology_validation_result.yaml` 默认只是当前体系构建读取的 validation evidence；它的 2.6 target 不因为报告被读取就成为 Stage 3 source target。只有某种非常规执行设计中 2.6 target 本身实际参与当前 execution object 的形成时，才按真实对象关系处理。

当前 Stage 3 `target_id` 只在当前 Task Sheet / 当前 Stage 3 工作项内解释，不继承 2.5、2.6 或前序 Stage 3 target 编号。

## Branching

如果同一个 source target 需要保留多个会产生不同体系构建结果的 strategy，例如：

- 不同 box geometry / size strategy；
- 不同 solvent model 或 solvent composition；
- 不同 salt concentration / ion composition；
- 不同且都需要后续模拟对照的 solvation / ionization route；

则为每个 strategy 建立独立 Stage 3 local target。多个 current target records 可以共同引用同一个 source target record，从而形成清楚的 system-construction branches。

普通执行不自动枚举所有可行 box / solvent / ion 组合。只有当前 Task Sheet / 用户明确要求或实际科研设计需要保留 alternatives 时才展开分支。

Stage 3 内部的 `periodic_box_construction / solvent_addition / ion_addition` 是 current target 的操作历史，不自动成为独立 target nodes。如果后续确实要从某个已经正式完成的 Stage 3 中间状态继续分支，应先让该状态成为可定位的正式 Stage 3 target/result，再由后续 targets 把它记录为 source target；不要仅靠 operation directory 名称伪造 target lineage。

## 输入与依据

当前 Task Sheet 提供本次体系构建的处理对象和需要完成的体系构建工作。

Task Execution Agent 结合当前 Task Sheet、必要的前序 Task Sheet 引用和：

`<project_root>/00_project_records/project_result_index.md`

定位当前 target 的实际 source system result。

最常见的初始 source 是：

`topology_integration_result.yaml`

该正式结果可以由当前 Task Sheet 产生，也可以来自同一科研任务的前序 Task Sheet或其它已有正式结果；当前 Task Sheet 不要求重复包含 topology integration 的执行步骤。

需要解释该正式结果的文件定位和字段语义时读取：

`../02_topology_preparation/2.5_topology_integration_and_assembly/references/results.md`

从该正式结果定位当前起始结构文件、体系主 `.top`、本次拓扑整合生成的 `.itp`，以及当前体系主 `.top` 已经引用的其它拓扑 / 参数定义。

建立 current Stage 3 target record 时，把该 result 的 `references.target_record` 作为实际 source target；如果 current Stage 3 从已有 Stage 3 formal result 继续，则改用实际前序 Stage 3 target record，不把 2.5 固定成所有 Stage 3 targets 的永久根来源。

若结合当前 Task Sheet、必要的前序 Task Sheet 引用和项目结果索引能够定位与当前 source integration object 对应的：

`topology_validation_result.yaml`

则读取其中已经记录的检查事实，分析这些问题是否会影响当前体系构建或后续模拟准备。需要解释该结果字段时读取：

`../02_topology_preparation/2.6_topology_validation/references/results.md`

发现具有实际影响的风险时，适当提醒用户。

## 操作计划

在当前 Task Sheet 的 `3 System construction / solvation` 条目内部，按 current local target 维护操作计划。

单 target 时可以只记录一套操作列表；多 target branches 时，每个 target 分别记录自己的操作计划、状态和结果入口，不把互斥 branch 的 operations 混在一个 target history 中。

每个 target 的操作计划只记录该 target 需要经过哪些体系构建操作，按计划顺序列出操作类型并维护状态。

每项操作使用以下状态：

```text
未完成
已完成
已终止
```

实际结果改变后续体系构建需要时，更新该 target 尚未完成的操作计划。

## 工作目录与文件保护

需要本地执行时使用：

```text
<project_root>/03_md_preparation/<task_id>/
├── targets/
│   ├── target_001.yaml
│   ├── target_002.yaml
│   └── ...
├── target_001/
│   ├── 01_periodic_box_construction/
│   ├── 02_solvent_addition/
│   └── 03_ion_addition/
└── ...
```

这里的 `<task_id>` 是当前 Task Sheet 的 `Txxxx` 标识。

每个 current target 内的实际操作建立独立目录，并以两位数字表示该 target 内的实际执行顺序：

```text
01_periodic_box_construction/
02_solvent_addition/
03_ion_addition/
```

重复或重排时继续使用下一个顺序号。该数字只表示当前 target 内的操作顺序，不是 target identity。

不原地覆盖上游正式结构文件、体系主 `.top` 或 `.itp`。

当 `gmx solvate -p` 或 `gmx genion -p` 需要修改 `[ molecules ]` 时，先在当前 target 的当前操作目录形成可修改的派生体系主 `.top`。确定本次实际采用的溶剂或离子拓扑 / 参数定义后，如果该派生 `.top` 尚未引用相应定义，本 Skill 直接在该 `.top` 中补充对应 `#include`。

除 `genion.mdp` 外，`.gro`、`.top`、`.itp`、`.mdp` 和 `.tpr` 的文件名不作为正式接口；正式结果记录使用实际完整绝对路径。

## 周期盒构建

使用：

`gmx editconf`

参数习惯：

```text
-f     当前结构文件
-o     当前操作的输出结构文件
-c     显式保留，表达构盒 / 调整后的居中意图
-box   当前 Task Sheet 给出明确盒尺寸时使用
-d     当前 Task Sheet 给出溶质到盒边界距离时使用
-bt    按当前 Task Sheet 要求确定盒类型
```

`-box` 与 `-d` 按当前 target 要求选择。GROMACS 中二者本身会隐含居中，本 Skill 仍保留 `-c` 作为显式命令习惯。

完成当前操作前检查：

1. `gmx editconf` 进程正常结束；
2. 溶质位于生成周期盒的中心。

## 溶剂添加

根据用户要求确定当前 target 的溶剂模型及其拓扑 / 参数定义来源；用户未指定时，根据当前体系和模拟要求判断实际采用的模型及参数定义来源。若存在多个会实质改变体系组成或参数定义的合理选择且无法可靠确定，向用户确认。

如果用户希望多个合理 solvent choices 都继续作为后续模拟 branches，不强行选一个；按本 Skill target branching 规则分别建立 targets。

使用：

`gmx solvate`

参数习惯：

```text
-cp    当前结构文件
-cs    当前采用的溶剂坐标模板
-p     当前操作中可修改的体系主 .top
-o     当前操作的输出结构文件
```

普通情况下沿用 GROMACS 2022 的默认值：

```text
-scale  0.57
-radius 0.105 nm
```

命令可以依赖软件默认值；当前 target 的要求或实际 GROMACS 版本需要其它值时使用相应设置。

完成当前操作前检查：

1. `gmx solvate` 进程正常结束；
2. 当前体系主 `.top` 中的溶剂分子记录与数量已由本次操作正常更新。

## 离子添加

根据用户要求确定当前 target 的离子种类及其拓扑 / 参数定义来源；用户未指定时，根据当前体系和模拟要求判断实际采用的离子及参数定义来源。若存在多个会实质改变体系组成或参数定义的合理选择且无法可靠确定，向用户确认。

如果多个 ion/salt strategies 都需要作为后续模拟 branches 保留，分别建立 Stage 3 targets，不在同一 target 中混合 mutually exclusive final compositions。

本 Skill 提供：

`references/genion.mdp`

作为生成 `gmx genion` 所需 `.tpr` 的可用起点。Task Execution Agent 根据当前结构、体系主 `.top`、实际 GROMACS 版本和本次离子添加需要，判断是否直接采用该文件，或在当前操作目录调整 / 重新生成本次使用的 `genion.mdp`。

无论直接采用、调整还是重新生成，本次使用的 `genion.mdp` 只用于 `gmx grompp` 生成 `gmx genion` 所需 `.tpr`，不作为能量最小化、平衡或生产模拟的参数方案。

执行关系：

```text
genion.mdp
→ gmx grompp
→ 当前操作的 .tpr
→ gmx genion
→ 加离子后的结构 + 更新后的体系主 .top
```

`gmx grompp` 参数习惯：

```text
-f    genion.mdp
-c    当前结构文件
-p    当前操作中可修改的体系主 .top
-o    当前操作的 .tpr
```

`gmx genion` 参数习惯：

```text
-neutral        当前 target 要求中和时使用
-conc 0.154     生物体系在用户和 Task Sheet 未指定其它盐浓度或离子组成时使用
-pname/-nname   按本次实际采用的离子定义确定
```

替换组选择当前实际需要被替换的主体溶剂分组。

用户或 Task Sheet 明确给出的盐浓度或离子组成覆盖 `0.154 M` 默认倾向。若当前体系已经含有需要计入最终浓度的相关离子，根据当前组成和目标确定本次实际添加数量，不机械重复使用 `-conc` 解释最终总浓度。

完成当前操作前检查：

1. `gmx grompp` 进程正常结束并生成当前操作的 `.tpr`；
2. `gmx genion` 进程正常结束；
3. 当前体系主 `.top` 中被替换的溶剂和新增离子记录已由本次操作正常更新。

本次使用的 `genion.mdp` 和生成的 `.tpr` 保留在当前操作目录中作为执行文件。

## 正式结果

生成正式结果前读取：

`references/results.md`

按其中定义为每个 current Stage 3 target 生成：

`system_construction_result.yaml`

该正式结果：

- 记录 current local `target_id`；
- 在 `references.target_record` 记录 current Stage 3 target record 完整路径；
- 记录本次实际 source formal result / validation evidence；
- 记录实际执行的体系构建 operations；
- 定位最终结构文件和最终体系主 `.top`。

当前职责登记到项目结果索引的正式结果只有各 current target 的：

`system_construction_result.yaml`

登记文件固定为：

`<project_root>/00_project_records/project_result_index.md`

Target record 不因为创建而单独登记。

## 完成条件

当前 Stage 3 local target 完成需要：

1. current target record 已建立，`source_target_records` 与实际 source system object(s) 一致；
2. 当前 target 操作计划中实际需要的操作已完成；
3. 每个已执行操作已完成本 Skill 规定的检查；
4. `system_construction_result.yaml.references.target_record` 指向 current target record；
5. `system_construction_result.yaml` 已生成；
6. 当前 Task Sheet 的 `3 System construction / solvation` 对应 target 条目已更新；
7. `system_construction_result.yaml` 已登记到 `<project_root>/00_project_records/project_result_index.md`；
8. 不通过 source/current `target_id` 编号相同建立 lineage。

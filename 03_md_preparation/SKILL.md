---
name: md-preparation
description: System construction / solvation main Skill。根据当前 Task Sheet 中的处理对象和体系构建要求，规划并执行周期盒构建、溶剂添加和离子添加，维护同一阶段级操作计划，并生成 system_construction_result.yaml。
---

# 3 System construction / solvation

通用 Task Execution 规则读取：

`../references/task_execution_rules.md`

本 Skill 在该规则基础上定义体系构建、溶剂化和离子添加的执行规则、操作计划、检查要求与正式结果。

## 目标

根据当前 Task Sheet 中的处理对象和需要完成的体系构建工作，形成后续模拟使用的结构文件与体系主 `.top`，并生成：

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

实际操作计划由当前结构—拓扑状态和体系构建目标决定，可按当前任务需要省略、重复或调整顺序。

## 输入与依据

当前 Task Sheet 提供本次体系构建的处理对象和需要完成的体系构建工作。

执行 Agent 以当前处理对象为准，结合当前任务上下文和：

`<project_root>/00_project_records/project_result_index.md`

定位与该对象对应的：

`topology_integration_result.yaml`

需要解释该正式结果的文件定位和字段语义时读取：

`../02_topology_preparation/2.5_topology_integration_and_assembly/references/results.md`

从该正式结果定位当前结构文件、体系主 `.top`、本次拓扑整合生成的 `.itp`，以及当前体系主 `.top` 已经引用的其它拓扑 / 参数定义。

若结合当前任务上下文和项目结果索引能够定位与当前拓扑整合对象对应的：

`topology_validation_result.yaml`

则读取其中已经记录的检查事实，分析这些问题是否会影响当前体系构建或后续模拟准备。需要解释该结果字段时读取：

`../02_topology_preparation/2.6_topology_validation/references/results.md`

发现具有实际影响的风险时，在用户可见回复和当前 Task Sheet 中说明。

## 操作计划

在当前 Task Sheet 的 `3 System construction / solvation` 条目内部维护操作计划。

操作计划只记录当前处理对象需要经过哪些体系构建操作，按计划顺序列出操作类型并维护状态。

每项操作使用以下状态：

```text
未完成
已完成
已终止
```

实际结果改变后续体系构建需要时，更新尚未完成的操作计划。

## 工作目录与文件保护

需要本地执行时使用：

`<project_root>/03_md_preparation/<task_id>/`

每次实际操作建立独立目录，并以两位数字表示当前 Task 内的实际执行顺序：

```text
01_periodic_box_construction/
02_solvent_addition/
03_ion_addition/
```

重复或重排时继续使用下一个顺序号。该数字只表示当前 Task 内的操作顺序。

不原地覆盖上游正式结构文件、体系主 `.top` 或 `.itp`。

当 `gmx solvate -p` 或 `gmx genion -p` 需要修改 `[ molecules ]` 时，先在当前操作目录形成可修改的派生体系主 `.top`。确定本次实际采用的溶剂或离子拓扑 / 参数定义后，如果该派生 `.top` 尚未引用相应定义，本 Skill 直接在该 `.top` 中补充对应 `#include`。

除 `genion.mdp` 外，`.gro`、`.top`、`.itp`、`.mdp` 和 `.tpr` 的文件名不作为正式接口；正式结果记录使用实际完整绝对路径。

## 周期盒构建

使用：

`gmx editconf`

参数习惯：

```text
-f     当前结构文件
-o     当前操作的输出结构文件
-c     显式保留，表达构盒 / 调整后的居中意图
-box   当前任务给出明确盒尺寸时使用
-d     当前任务给出溶质到盒边界距离时使用
-bt    按当前任务要求确定盒类型
```

`-box` 与 `-d` 按当前任务要求选择。GROMACS 中二者本身会隐含居中，本 Skill 仍保留 `-c` 作为显式命令习惯。

完成当前操作前检查：

1. `gmx editconf` 进程正常结束；
2. 溶质位于生成周期盒的中心。

该操作通常只生成新的结构文件；体系主 `.top` 未发生改变时，不把它记录成当前操作新生成的结果。

## 溶剂添加

根据用户要求确定溶剂模型及其拓扑 / 参数定义来源；用户未指定时，根据当前体系和模拟要求判断实际采用的模型及参数定义来源。若存在多个会实质改变体系组成或参数定义的合理选择且无法可靠确定，向用户确认。

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

命令可以依赖软件默认值；当前任务或实际 GROMACS 版本需要其它值时使用相应设置。

完成当前操作前检查：

1. `gmx solvate` 进程正常结束；
2. 当前体系主 `.top` 中的溶剂分子记录与数量已由本次操作正常更新。

## 离子添加

根据用户要求确定离子种类及其拓扑 / 参数定义来源；用户未指定时，根据当前体系和模拟要求判断实际采用的离子及参数定义来源。若存在多个会实质改变体系组成或参数定义的合理选择且无法可靠确定，向用户确认。

本 Skill 提供：

`references/genion.mdp`

它只用于为 `gmx genion` 生成当前操作的 `.tpr`，不是能量最小化、平衡或生产模拟的参数方案。

执行离子添加时，将该文件复制到当前操作目录并保持文件名：

`genion.mdp`

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

`genion.mdp` 当前预设使用：

```text
integrator = steep
nsteps     = 0
pbc        = xyz
```

`gmx genion` 参数习惯：

```text
-neutral        当前任务要求中和时使用
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

按其中定义生成：

`system_construction_result.yaml`

该正式结果记录本次实际依赖、实际执行的体系构建操作，以及最终结构文件和最终体系主 `.top`。详细字段语义由 `references/results.md` 定义。

当前职责登记到项目结果索引的正式结果只有：

`system_construction_result.yaml`

登记文件固定为：

`<project_root>/00_project_records/project_result_index.md`

## 完成条件

当前体系构建工作完成需要：

1. 操作计划中实际需要的操作已完成；
2. 每个已执行操作已完成本 Skill 规定的检查；
3. `system_construction_result.yaml` 已生成；
4. 当前 Task Sheet 的 `3 System construction / solvation` 条目已更新；
5. `system_construction_result.yaml` 已登记到 `<project_root>/00_project_records/project_result_index.md`。

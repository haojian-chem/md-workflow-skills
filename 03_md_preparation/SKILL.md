---
name: md-preparation
description: Stage 3 System construction / solvation main Skill。根据当前 Task Sheet 和 topology_integration_result.yaml 规划并执行周期盒构建、溶剂添加和离子添加，维护同一 stage-level operation plan，并生成 system_construction_result.yaml。
---

# 3 System construction / solvation

通用 Task Execution 规则读取：

`../references/task_execution_rules.md`

本 Skill 只在该共享规则基础上定义体系构建、溶剂化和离子添加的执行规则、内部 operation plan、检查要求与正式结果。

## 目标

根据当前 Task Sheet 中的体系构建目标、处理对象和已经明确的约束，以当前拓扑整合正式结果为主要上游依据，形成可供后续模拟直接使用的结构文件与体系主 `.top`，并生成：

`system_construction_result.yaml`

本 Skill 当前拥有三类内部 operation：

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

实际 operation plan 由当前结构—拓扑状态和 Task Sheet 中的体系构建目标决定。operation 可以省略、重复或按当前任务需要调整顺序；不要把三类 operation 重新物化为编号化 Workflow Step。

## 输入与依据

当前 Task Sheet 必须给出当前体系构建工作的目标、处理对象和已明确约束，并指定本次采用的：

`topology_integration_result.yaml`

需要解释该正式结果的文件定位和字段语义时读取：

`../02_topology_preparation/2.5_topology_integration_and_assembly/references/results.md`

从其中记录的实际完整路径定位：

- 当前结构文件：`results.structure`；
- 当前体系主 `.top`：`results.top`；
- 本次拓扑整合生成的 `.itp`：`results.itp`；
- 当前体系主 `.top` 实际引用的其它外部拓扑 / 参数定义。

不根据默认 basename、目录顺序、修改时间或相似文件名重新推断当前结构文件和拓扑文件。

若 Task Sheet 指定或当前项目中存在与该拓扑整合对象对应的：

`topology_validation_result.yaml`

可以读取其中已经记录的检查事实，分析这些问题是否会影响当前体系构建或后续模拟准备。需要解释该结果字段时读取：

`../02_topology_preparation/2.6_topology_validation/references/results.md`

发现可能影响当前构建或后续模拟准备的风险时，在用户可见回复和当前 Task Sheet 中说明；当前结构文件和拓扑文件的身份仍由 `topology_integration_result.yaml` 确定。

## Reuse

遵守仓库级 Task Execution reuse 规则。

已有 `system_construction_result.yaml` 只有在以下信息均明确等价时才自动复用：

- 采用的拓扑整合正式结果所对应的结构—拓扑对象；
- 周期盒要求；
- 溶剂组成与影响溶剂化结果的设置；
- neutralization、盐浓度 / 离子组成和其它影响离子添加结果的设置；
- 其它会改变最终体系组成或周期盒的明确要求。

同时确认已有正式结果记录中的最终结构文件和体系主 `.top` 仍可定位，且该 `.top` 所需的拓扑 / 参数依赖仍可解析。

明确不等价则执行新的体系构建；信息不足则向用户确认；用户明确要求重做或建立对照时跳过自动复用。

## Operation plan

在当前 Task Sheet 的 `3 System construction / solvation` 条目内部维护 operation plan，不另建 `system_construction_plan.yaml` 或其它平行计划文件。

operation plan 至少保留足以恢复以下信息的内容：

- 实际执行顺序；
- operation type；
- 当前状态；
- 工作目录；
- 当前 operation 采用的结构文件和体系主 `.top`；
- 当前 operation 的关键实际设置；
- 已完成 operation 产生并继续保留的结果；
- `system_construction_result.yaml` 的实际路径。

实际结果改变后续构建需要时，更新尚未完成的 operation plan。已经实际执行并形成有意义任务历史的 operation 不静默删除。

## 工作目录与文件保护

需要本地执行时使用：

`<project_root>/03_md_preparation/<task_id>/`

每次实际 operation 建立独立目录，并以两位数字表示当前 Task 内的实际执行顺序：

```text
01_periodic_box_construction/
02_solvent_addition/
03_ion_addition/
```

重复或重排时继续使用下一个顺序号。该数字只表示当前 Task 内的实际 operation 顺序，不形成新的 Workflow Step identity。

不原地覆盖上游正式结构文件、体系主 `.top` 或 `.itp`。

当 `gmx solvate -p` 或 `gmx genion -p` 需要修改 `[ molecules ]` 时，先在当前 operation 目录形成可修改的派生体系主 `.top`。派生 `.top` 必须继续能够解析实际需要的 `#include`；根据当前文件布局决定是否沿用原路径、调整 include path、建立链接或复制必要文件，不为了目录对称机械复制全部 `.itp`。

`.gro`、`.top`、`.itp`、`.mdp` 和 `.tpr` 的 basename 除 `genion.mdp` 外不是正式接口；正式结果记录使用实际完整绝对路径。

## 周期盒构建

使用：

`gmx editconf`

参数习惯：

```text
-f     当前结构文件
-o     当前 operation 的输出结构文件
-c     显式保留，表达构盒 / 调整后的居中意图
-box   当前任务给出明确 box dimensions 时使用
-d     当前任务给出 solute-to-boundary distance 时使用
-bt    按当前任务要求确定 box type
```

`-box` 与 `-d` 按当前任务要求选择。GROMACS 中二者本身会隐含居中，本 Skill 仍保留 `-c` 作为显式命令习惯。

完成该 operation 前检查：

1. `gmx editconf` 进程正常结束；
2. 溶质位于生成周期盒的中心。

该 operation 通常只生成新的结构文件；体系主 `.top` 未发生改变时，不把它记录成当前 operation 新生成的结果。

## 溶剂添加

使用：

`gmx solvate`

参数习惯：

```text
-cp    当前结构文件
-cs    当前任务采用的 solvent coordinate / template
-p     当前 operation 中可修改的体系主 .top
-o     当前 operation 的输出结构文件
```

当前基线按 GROMACS 2022 的普通默认值：

```text
-scale  0.57
-radius 0.105 nm
```

命令可以依赖软件默认值；如果当前任务或实际 GROMACS 版本采用其它值，在 Task Sheet 当前 operation 中记录实际设置。

完成该 operation 前检查：

1. `gmx solvate` 进程正常结束；
2. 当前体系主 `.top` 中的溶剂分子记录与数量已由本次操作正常更新。

## 离子添加

当前 Skill package 提供：

`references/genion.mdp`

它只用于为 `gmx genion` 生成当前 operation 的 `.tpr`，不是 energy minimization、equilibration 或 production simulation 的参数方案。

执行当前 ion-addition operation 时，将该 preset 复制到当前 operation 目录并保持文件名：

`genion.mdp`

然后执行：

```text
genion.mdp
→ gmx grompp
→ current-operation .tpr
→ gmx genion
→ ionized structure + updated system .top
```

`gmx grompp` 参数习惯：

```text
-f    genion.mdp
-c    当前结构文件
-p    当前 operation 中可修改的体系主 .top
-o    当前 operation 的 .tpr
```

`genion.mdp` 的当前 preset 使用 `integrator = steep`、`nsteps = 0` 和 `pbc = xyz`，只建立 `gmx genion` 所需的 run input；不要把该文件解释为执行一次能量最小化。若实际 GROMACS 版本或当前 topology 需要技术性调整，在当前 operation 目录修改本次使用的 `genion.mdp`，并保持其职责只限于生成 `gmx genion` 输入 `.tpr`。不要借用模拟阶段的 EM/NVT/NPT/MD `.mdp` 代替本文件。

`gmx genion` 参数习惯：

```text
-neutral        当前任务要求 neutralization 时使用
-conc 0.154     生物体系在用户和 Task Sheet 未指定其它盐浓度或离子组成时使用
-pname/-nname   按当前实际 ion topology definitions 和任务要求确定
```

replacement group 选择当前实际需要被替换的主体溶剂 group，不硬编码为 `SOL`。所选 group 必须满足 `gmx genion` 对可替换 solvent group 的要求：其中 solvent molecules 连续，并具有一致的原子数。

用户或 Task Sheet 明确给出的盐浓度或离子组成覆盖 `0.154 M` 默认倾向。

使用 `-conc` 前检查当前体系是否已经含有本次浓度目标涉及的离子。GROMACS 2022 的 `gmx genion -conc` 不把已有 ions 计入浓度；已有相关 ions 时，不得把再次使用 `-conc` 直接解释为最终体系总浓度，应根据当前组成和目标确定本次实际需要增加的离子数与相应参数。

不自动使用 `gmx grompp -maxwarn` 越过 warning。若 `grompp` 出现 warning，先判断其触发原因以及是否影响当前 `.tpr` 对 ion replacement 的有效表达。

完成该 operation 前检查：

1. `gmx grompp` 进程正常结束并生成当前 operation 的 `.tpr`；
2. `gmx genion` 进程正常结束；
3. 当前体系主 `.top` 中被替换的 solvent 和新增 ion 记录已由本次操作正常更新。

本次使用的 `genion.mdp` 和生成的 `.tpr` 保留在 operation 目录中作为执行文件，不进入项目结果索引。

## 正式结果

生成正式结果前读取：

`references/results.md`

按其中定义生成唯一正式结果入口：

`system_construction_result.yaml`

该结果记录实际采用的拓扑整合正式结果、实际执行的 operations，以及最终结构文件和最终体系主 `.top`。

项目结果索引只登记 `system_construction_result.yaml`。各 operation 产生的 `.gro` / `.top`、最终 `.gro` / `.top`、`genion.mdp`、`.tpr` 和 operation directory 均通过该 YAML 或 Task Sheet 定位，不分别登记到项目结果索引。

## 完成条件

当前体系构建工作完成需要：

1. operation plan 中实际需要的 operations 已完成；
2. 每个已执行 operation 已完成本 Skill 规定的检查；
3. `system_construction_result.yaml` 已生成，并能够定位全部保留的 operation 结果以及最终结构文件和体系主 `.top`；
4. 最终体系主 `.top` 所需的拓扑 / 参数依赖仍可解析；
5. 当前 Task Sheet 的 `3 System construction / solvation` 条目已更新；
6. `system_construction_result.yaml` 已登记到项目结果索引。

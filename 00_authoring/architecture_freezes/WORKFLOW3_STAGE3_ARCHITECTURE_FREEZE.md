# Workflow 3 / Stage 3 architecture record

Status: IMPLEMENTED ARCHITECTURE RECORD

## 0. 文档定位

本文件记录 MD Workflow Stage 3 — System construction / solvation 已确认并完成物化的 Stage-level architecture 与职责边界。

Current runtime authority 为：

```text
03_md_preparation/SKILL.md
03_md_preparation/references/results.md
03_md_preparation/references/genion.mdp
```

后续具体执行规则、结果字段和 `genion.mdp` preset 的修改由上述 active Skill package 拥有；本文件不再维护一套平行的可变规范。

原 `3.1 / 3.2 / 3.3` step-level freezes 已归档到：

`00_authoring/archive/stage3_history/`

不得从归档文件恢复编号化 Stage 3 sub-stage。

## 1. 已实现 Stage-level architecture

Stage 3 不设置编号化 sub-stage，只保留一个 Stage-level main Skill。

该 main Skill 读取当前 Task Sheet 中的体系构建目标、处理对象和已经明确的约束，并在同一个 Stage-level Task Sheet 条目内部形成和维护 operation plan。

当前拥有三类内部 operation：

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

实际 operation plan 可以根据当前结构—拓扑状态和 Task Sheet 中的体系构建目标省略、重复或调整顺序；这些 operation 不形成新的 Workflow Step identity。

## 2. 已实现输入与 evidence 边界

主要上游正式结果为：

`topology_integration_result.yaml`

当前结构文件、体系主 `.top`、实际 `.itp` 和其它拓扑 / 参数依赖均从该正式结果及其记录的实际路径定位，不根据默认 basename、目录顺序或修改时间重新推断。

与当前拓扑整合对象对应的 `topology_validation_result.yaml` 可以作为已有检查事实被读取和分析；其中的问题用于判断当前体系构建或后续模拟准备是否存在风险，不替代拓扑整合正式结果确定当前结构—拓扑对象。

Reuse 由 active main Skill 在仓库级 Task Execution 规则基础上，结合当前上游结构—拓扑对象与周期盒、溶剂和离子要求判断。

## 3. 已实现 operation plan 与目录模型

真实项目的 task-specific 根目录为：

`<project_root>/03_md_preparation/<task_id>/`

每次实际 operation 建立独立目录，并以两位数字记录当前 Task 内的实际执行顺序，例如：

```text
01_periodic_box_construction/
02_solvent_addition/
03_ion_addition/
```

重复或重排时继续使用后续顺序号。该顺序号只属于当前 Task 的 operation history。

operation plan 由 Task Sheet 当前 Stage-level 条目维护，不另建平行的 system-construction plan 文件。

已经实际执行并形成有意义历史的 operation 不因后续 replanning 被静默删除。

## 4. 已实现文件保护与 operation 边界

体系构建不原地覆盖上游正式结构文件、体系主 `.top` 或 `.itp`。

需要由 `gmx solvate -p` 或 `gmx genion -p` 修改体系组成时，先在当前 operation 目录形成可修改的派生体系主 `.top`，并保持其所需 topology / parameter includes 可解析。

三类 operation 的当前软件边界为：

```text
periodic_box_construction → gmx editconf
solvent_addition          → gmx solvate
ion_addition              → genion.mdp → gmx grompp → gmx genion
```

Ion addition 使用 active Skill package 中固定文件名：

`references/genion.mdp`

该文件只用于生成 `gmx genion` 所需 `.tpr`，不承担能量最小化、平衡或 production simulation 的参数语义。

## 5. 已实现正式结果 architecture

唯一 Stage-level 正式结果入口为：

`system_construction_result.yaml`

其结果 architecture 固定表达：

- 本次实际采用的 `topology_integration_result.yaml`；
- 仅在实际读取时记录的 `topology_validation_result.yaml`；
- 按实际执行顺序保留的 operation directory / type / structure / top；
- 最终结构文件；
- 最终体系主 `.top`。

Stage 3 不生成或登记 atom map。

项目结果索引只登记 `system_construction_result.yaml`；各 operation 的 `.gro`、`.top`、`genion.mdp`、`.tpr` 和 operation directory 由该正式结果或 Task Sheet 定位，不分别登记。

详细字段语义由 active：

`03_md_preparation/references/results.md`

拥有。

## 6. Implementation status

Stage-level active Skill 已生成：

`03_md_preparation/SKILL.md`

Detailed result interface 已生成：

`03_md_preparation/references/results.md`

Dedicated minimal preset 已生成：

`03_md_preparation/references/genion.mdp`

当前 `genion.mdp` 的精确内容已经物化并完成静态 authoring / interface 检查；代表性 GROMACS `grompp → genion` 实际执行验证仍作为后续 validation milestone。

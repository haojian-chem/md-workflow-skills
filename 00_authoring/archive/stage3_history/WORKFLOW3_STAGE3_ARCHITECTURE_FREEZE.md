# Workflow 3 / Stage 3 architecture record

Status: IMPLEMENTED ARCHITECTURE RECORD

## 0. 文档定位

本文件只记录 MD Workflow Stage 3 — System construction / solvation 已实现的稳定架构。

Current runtime authority 为：

```text
03_md_preparation/SKILL.md
03_md_preparation/references/results.md
03_md_preparation/references/genion.mdp
```

具体执行规则、操作参数、检查要求、正式结果字段和 `genion.mdp` 内容由上述 active Skill package 拥有；本文件不维护平行的 runtime specification。

原 `3.1 / 3.2 / 3.3` step-level freezes 已归档到：

`00_authoring/archive/stage3_history/`

## 1. Stage-level architecture

Stage 3 使用一个 Stage-level main Skill，不设置编号化 sub-stage。

当前 Task Sheet 中的 `3 System construction / solvation` 条目提供当前处理对象和需要完成的体系构建工作；Stage 3 main Skill 在该条目内部形成和维护体系构建操作计划。

当前包含三类内部操作：

```text
periodic_box_construction
solvent_addition
ion_addition
```

操作计划根据当前体系构建需要确定实际包含的操作及其顺序。

## 2. 上游正式结果接口

Stage 3 的主要上游正式结果为：

`topology_integration_result.yaml`

当前结构文件和体系主 `.top` 由该正式结果定位。

与当前拓扑整合对象对应的 `topology_validation_result.yaml` 可以作为已有检查事实读取和分析；它不替代 `topology_integration_result.yaml` 确定当前结构—拓扑对象。

## 3. Task-specific directory model

真实项目的 Stage 3 task-specific 根目录为：

`<project_root>/03_md_preparation/<task_id>/`

每次实际操作建立独立目录，并以两位数字表示当前 Task 内的实际执行顺序，例如：

```text
01_periodic_box_construction/
02_solvent_addition/
03_ion_addition/
```

重复或重排时继续使用后续顺序号；该顺序号只属于当前 Task 的操作顺序。

## 4. 正式结果入口

Stage 3 的正式结果入口固定为：

`system_construction_result.yaml`

详细结果字段、路径语义和项目结果索引登记规则由：

`03_md_preparation/references/results.md`

拥有。

## 5. Implementation status

Stage-level active Skill：

`03_md_preparation/SKILL.md`

Detailed result interface：

`03_md_preparation/references/results.md`

可用于离子添加预处理的参考 `.mdp`：

`03_md_preparation/references/genion.mdp`

代表性 GROMACS `grompp → genion` 实际执行验证仍属于后续 validation milestone。

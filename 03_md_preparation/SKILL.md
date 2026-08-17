---
name: md-preparation
description: Stage 3 System construction / solvation 的总 Skill。依据已冻结的 3.1–3.3 架构，将 Stage 2 已验证的 topology/coordinate package 推进为可交给 Stage 4 的已构建体系；具体执行、reuse、validation 与结果由对应 3.x main Skill 拥有。
---

# 3 System construction / solvation

## Purpose

将当前已验证的 `.gro` 与其关联 `.top` / `.itp` 体系逐步完成 periodic box、solvation 和 ion addition，形成可交给 Stage 4 的 constructed system。

Stage 3 已冻结架构：

`00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

## Catalog and current Skill entry

```text
3.1 Periodic box construction
→ 3.1_periodic_box_construction/SKILL.md

3.2 Solvent addition
→ 3.2_solvent_addition/SKILL.md

3.3 Ion addition
→ 3.3_ion_addition/SKILL.md
```

默认科学顺序：

```text
3.1 → 3.2 → 3.3
```

这只是默认顺序，不限制执行次数。Task Sheet 可依据实际体系和任务目标对未来 3.x 实例重复、删除、插入或重排。

Stage 3 不额外拆 system settings、final assembly 或 stage-level validator。

## Shared execution rule

每个 3.x 实例都消费“当前 validated `.gro` + 与其实际关联的 `.top` / 必要 `.itp`”。下游必须继续知道当前 topology association，不能只传一个孤立 `.gro`。

GROMACS 参数优先级固定为：

```text
explicit user requirement
> current Task Sheet requirement
> actual current object/state
> current Step Skill arg tendency
> GROMACS default
```

`sys.top` 只是命名 tendency；已有有效 topology 不为了统一名字而强制改名。

## Runtime use

```text
读取 Task Sheet
→ 确定当前 3.x 实例和对象
→ 读取对应 3.x main Skill
→ reuse 判断
→ 必要时执行
→ 按当前 Skill validation
→ 更新 Task Sheet / project_result_index
→ 继续下一实际需要的任务项
```

普通 Stage 3 执行不返回 Manager 调度，也不使用 Legacy route / Workstream / runtime task-result。

## Stage-level handoff

- 3.1：改变 box/centering，通常不改变 atom composition 或 topology composition。
- 3.2：加入 solvent，并使 coordinate composition 与 topology molecule counts 保持一致。
- 3.3：通过 `grompp → genion` 加入/替换 ions，并使 coordinate/topology composition 保持一致。

实际最后一个已完成 Stage 3 操作的 validated coordinate/topology state 即当前 constructed-system handoff。

## Source directory vs project directory

本仓库 Skill 源码：

```text
03_md_preparation/3.1_periodic_box_construction/
03_md_preparation/3.2_solvent_addition/
03_md_preparation/3.3_ion_addition/
```

真实项目 execution base directories 仍由 Manager planning index 定义：

```text
03_md_preparation/01_periodic_box_construction/
03_md_preparation/02_solvent_addition/
03_md_preparation/03_ion_addition/
```

两者不是同一类目录。

## Stage 3 completion

当当前任务所需 Stage 3 实例均完成自身 validation，且最后一个 constructed-system state 的 `.gro`、`.top` 和必要 `.itp` 关联明确后，可交给 Stage 4。

Stage 3 不再额外生成一个重复的 final-assembly package 或 stage-level validation record。

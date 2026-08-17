---
name: structure-preparation
description: Stage 1 Structure preparation 的总 Skill。定义 1.1–1.9 的阶段边界、当前子环节入口和跨子环节 handoff；具体科学执行、reuse、validation 与 official results 由对应子环节 main Skill 拥有。
---

# 1 Structure preparation

## Purpose

将初始结构来源推进为经过 Stage 1 最终验证、可交给 Stage 2 topology preparation 的结构结果。

本 Skill 只拥有 Stage 1 的阶段级关系：

- 1.1–1.9 的 catalog；
- 当前子环节 main Skill 的入口；
- 上下游结果如何交接；
- Stage 1 的动态计划边界；
- Stage 1 完成条件。

本 Skill 不复制各子环节的内部算法、参数、reuse、validation 或 official-result 细节。Task Execution Agent 从 Task Sheet 确定当前子环节后，直接读取对应子环节 main Skill。

## Catalog and current Skill entry

```text
1.1 Structure source recognition
→ 1.1_source_recognition/SKILL.md

1.2 Component and residue classification
→ 1.2_component_and_residue_classification/SKILL.md

1.3 Chain and residue selection
→ 1.3_chain_and_residue_selection/SKILL.md

1.4 Alternate conformation / occupancy resolution
→ 1.4_altloc_occupancy_resolution/SKILL.md

1.5 Completeness check
→ 1.5_completeness_check/SKILL.md

1.6 Structure completion / correction
→ 1.6_missing_region_completion/SKILL.md

1.7 Protein protonation assignment
→ 1.7_protein_protonation_assignment/SKILL.md

1.8 Reorder and mapping
→ 1.8_reorder_and_mapping/SKILL.md

1.9 Structure preparation validation
→ 1.9_validation/SKILL.md
```

这些目录表达 Stage/Step 身份，不表示 Workflow / Operation / Validator 分类。

## Runtime use

正常执行：

```text
读取 Task Sheet
→ 确定当前 1.x 子环节与对象
→ 读取对应 1.x main Skill
→ 按该 Skill 做 reuse / execution / validation / result registration
→ 根据实际结果调整尚未执行的后续计划
→ 继续下一实际需要的子环节
```

普通子环节之间不需要返回 Manager，也不需要额外 Workflow dispatcher。

Manager 初始规划使用：

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

Manager 不需要读取本 Skill 来做初始 step catalog 展开。

## Stage-level handoff

### 1.1 → 1.2

1.2 消费 1.1 已明确的正式结构来源。1.2 不重新执行 source recognition。

### 1.2 → 1.3

1.3 消费 1.2 正式分类结果及其稳定 identity。1.3 不重新构造 1.2 已建立的 opaque IDs 或分类关系。

### 1.3 → 1.4

1.4 消费 1.3 最终选中的 target PDB。只有用户明确要求分别建立多个结构时，1.3 才形成多个 target；后续按 target 分别推进。

### 1.4 → 1.5

1.5 消费当前单一构象结构，并结合前序已经完成的 residue / atom 核对信息生成 repair report。

### 1.5 → 1.6

1.6 只执行 1.5 已明确的 repair items，不扩大问题判定范围。

### 1.6 → 1.7

如果 1.6 实际修改了结构，1.7 必须消费 1.6 当前正式结构，而不是旧输入。

### 1.7 → 1.8

1.8 消费已经落实蛋白质 protonation-state residue naming 的当前重原子结构，并形成 Stage 1 final structure / map。

### 1.8 → 1.9

1.9 对 Stage 1 final PDB / map 做阶段级只读验证；失败时返回真正拥有问题的上游子环节处理，而不是在 1.9 修复。

## Dynamic task plan

Stage 1 catalog 是初始规划与执行定位用的科学步骤目录，不代表每个任务必须机械执行每一步。

Task Execution Agent 在实际执行中可以依据当前结果和用户要求，对尚未执行的未来步骤进行增加、删除、替换或重排。

例如某个 target 没有需要处理的 altloc，或 1.5 没有需要 1.6 处理的 repair item，可以依据对应子环节 Skill 的规则调整未来计划。

尚未执行且确认不需要的步骤直接从 Task Sheet 删除；不额外建立 `SKIP / NOT_APPLICABLE` 状态。

已经实际执行并形成有意义任务历史的步骤不为整理计划而静默删除。

## Directory relation

本仓库中的 Skill 源码目录与真实科研项目的 execution directory 是不同概念。

真实项目的 Stage 1 base directories 由 Manager planning index 定义，例如：

```text
<project_root>/01_structure_preparation/01_source_recognition/
<project_root>/01_structure_preparation/02_component_and_residue_classification/
...
<project_root>/01_structure_preparation/09_validation/
```

具体任务执行目录仍使用 `<base_work_directory>/<task_id>/`；是否创建由当前子环节 Skill 的 reuse/execution 结果决定。

## Stage 1 completion

Stage 1 只有在当前任务所需的上游工作已经完成，并且 1.9 的 blocking checks 全部通过后，才可作为完成的 Structure preparation 结果交给 Stage 2。

Stage 1 最终科学结果以 1.8 / 1.9 当前 Skills 定义的正式结果为准；本 Stage main Skill 不另造阶段级重复结果包、route、decision、event 或 runtime state。

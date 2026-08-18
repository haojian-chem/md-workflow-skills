---
name: structure-preparation
description: Stage 1 Structure preparation 的阶段级导航 Skill。定义 1.1–1.9 catalog、跨子环节 handoff 与 Stage 1 completion boundary；只把已正式生成的子环节列为 current Skill entry，尚在 authoring 或 freeze-only 的子环节不得作为 runtime Skill 使用。
---

# 1 Structure preparation

## Purpose

将初始结构来源推进为经过 Stage 1 最终验证、可交给 Stage 2 topology preparation 的结构结果。

本 Skill 只拥有 Stage 1 的阶段级关系：

- 1.1–1.9 的 catalog；
- 当前已正式生成的子环节 Skill 入口；
- 上下游结果如何交接；
- Stage 1 的动态计划边界；
- Stage 1 完成条件。

本 Skill 不复制各子环节的内部算法、参数、reuse、validation 或 official-result 细节。

## Catalog and implementation status

```text
1.1 Structure source recognition
→ current: 1.1_source_recognition/SKILL.md

1.2 Component and residue classification
→ current: 1.2_component_and_residue_classification/SKILL.md

1.3 Chain and residue selection
→ current: 1.3_chain_and_residue_selection/SKILL.md

1.4 Alternate conformation / occupancy resolution
→ current: 1.4_altloc_occupancy_resolution/SKILL.md

1.5 Completeness check
→ current: 1.5_completeness_check/SKILL.md

1.6 Structure completion
→ current: 1.6_structure_completion/SKILL.md

1.7 Protein protonation assignment
→ freeze only: ../00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md

1.8 Reorder and mapping
→ freeze only: ../00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.8_REORDER_MAPPING_FREEZE.md

1.9 Structure preparation validation
→ freeze only: ../00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.9_VALIDATION_FREEZE.md
```

这些编号表达 Stage/Step 身份，不表示 Workflow / Operation / Validator 分类。

**freeze-only 不是 runtime Skill。** Architecture freeze 只能作为 authoring input；在用户明确批准正式 Skill generation 前，Task Execution Agent 不得把 freeze 当作可执行 `SKILL.md`。

## Runtime use

对于已经存在正式 current Skill 的 Stage 1 子环节：

```text
读取 Task Sheet
→ 确定当前 1.x 子环节与对象
→ 读取对应 current 1.x main Skill
→ 按该 Skill 做 reuse / execution / validation / result registration
→ 根据实际结果调整尚未执行的后续计划
→ 继续下一实际需要的子环节
```

如果计划进入尚未正式生成 Skill 的子环节，则当前 runtime 不应根据 architecture freeze 自行执行；应先完成对应 Skill authoring / generation。

普通已实现子环节之间不需要返回 Manager 调度，也不需要额外 Workflow dispatcher。

Manager 初始规划使用：

`00_manager/references/workflow_plan_index.yaml`

Manager 不需要读取本 Skill 来做初始 step catalog 展开。

## Stage-level handoff

### 1.1 → 1.2

1.2 消费 1.1 已明确的正式结构来源。1.2 不重新执行 source recognition。

### 1.2 → 1.3

1.3 消费 1.2 正式分类结果及其稳定 identity。1.3 不重新构造 1.2 已建立的 opaque IDs 或分类关系。

### 1.3 → 1.4

1.4 消费 1.3 最终选中的 target PDB。只有用户明确要求分别建立多个结构时，1.3 才形成多个 target；后续按 target 分别推进。

### 1.4 → 1.5

1.5 消费当前 target 的当前结构，并结合 1.2 正式 completeness evidence、1.3 target mapping 和实际存在的 1.4 resolution report，生成该 target 独立的 `structure_completeness_report.yaml`。具体规则由 `1.5_completeness_check/SKILL.md` 拥有。

### 1.5 → 1.6

1.6 消费当前 target 的 1.5 正式 `structure_completeness_report.yaml`，以及其中 `structure` 字段记录的当前 PDB，并落实报告中已明确的 repair items。具体规则由 `1.6_structure_completion/SKILL.md` 拥有。

### 1.6 → 1.7

1.7 消费当前 target 在 1.6 处理后的当前结构：

- 如果 1.6 本地执行并形成通过 validation 的正式结果，使用该次 `completed_structure.pdb`；
- 如果 1.6 复用了等价的既有正式结果，使用被复用的 `completed_structure.pdb`；
- 如果 1.6 因没有 repair item 而未执行，则沿用进入 1.6 前的当前结构。

1.7 的内部执行规则由对应 current Skill / freeze 拥有，Stage main 只维护这里的结构 handoff。

### 1.7 → 1.8

冻结接口：1.8 消费已经落实蛋白质 protonation-state residue naming 的当前重原子结构，并形成 Stage 1 final structure / map。

### 1.8 → 1.9

冻结接口：1.9 对 Stage 1 final PDB / map 做阶段级只读验证；失败时返回真正拥有问题的上游子环节处理，而不是在 1.9 修复。

## Dynamic task plan

Stage 1 catalog 是初始规划与执行定位用的科学步骤目录，不代表每个任务必须机械执行每一步。

Task Execution Agent 在实际执行中可以依据当前结果和用户要求，对尚未执行的未来步骤进行增加、删除、替换或重排。

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

具体任务执行目录仍使用 `<base_work_directory>/<task_id>/`；是否创建由对应 current Skill 的 reuse/execution 结果决定。

## Stage 1 completion

Stage 1 catalog 与 1.7–1.9 architecture 已经冻结，但 Stage 1 不能在 1.7–1.9 formal Skills 尚未生成时声称具备完整 runtime implementation。

未来只有在当前任务所需上游工作完成，并且正式 1.9 Skill 的 blocking checks 全部通过后，才可把 Structure preparation 结果交给 Stage 2。

本 Stage main Skill 不另造阶段级重复结果包、route、decision、event 或 runtime state。

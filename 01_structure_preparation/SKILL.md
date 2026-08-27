---
name: structure-preparation
description: Stage 1 Structure preparation 的阶段级导航 Skill。定义 1.1–1.9 catalog、跨子环节 handoff 与 Stage 1 completion boundary；只把已正式生成的子环节列为 current Skill entry，尚在 authoring 或 freeze-only 的子环节不得作为 runtime Skill 使用。
---

# 1 Structure preparation

通用 Task Execution 规则读取：

`../references/task_execution_rules.md`

本 Skill 只在此基础上定义 Stage 1-specific 的阶段关系与计划调整语义，不复制 shared Task Execution 规则。

## Purpose

将初始结构来源推进为完成 Stage 1 最终检查并形成验证报告、可据此决定是否交给 Stage 2 topology preparation 的结构结果。

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
→ current: 1.7_protein_protonation_assignment/SKILL.md

1.8 Reorder and mapping
→ current: 1.8_reorder_and_mapping/SKILL.md

1.9 Structure preparation validation
→ current: 1.9_validation/SKILL.md
```

这些编号表达 Stage/Step 身份，不表示 Workflow / Operation / Validator 分类。

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

### Stage 1 关键信息确认

进入任一 1.x 子环节的实质执行前，先确认会实质改变当前执行对象、处理范围、方法 / 模式、科学判据 / reference 或正式结果语义的必要信息已经闭合。

判断原则：

```text
已有正式项目信息、当前上下文或 current Skill 明确规则能够唯一确定
→ 直接采用并继续

current Skill 已明确给出默认值 / 默认行为
→ 按 Skill 规则继续

存在多个实质不同的合理选择，且不同选择会改变执行、判断或正式结果
→ 向用户确认
```

不得仅因为某一选择常见、方便、文件先出现或符合 Agent 经验，就替用户 / 项目补出未明确的关键决定；也不得在关键决定尚未闭合时先开始依赖该决定的结构修改、分类、检查或结果生成，之后再补解释。

各 1.x current Skill 可以定义更具体的必需输入、可由 Agent 科学判断的事项和确认条件；这些局部规则优先用于判断当前信息是否已经足以唯一闭合。

从 1.3 初始化 target atom map 后，凡后续当前结构已有对应正式 map，Stage main 在结构 handoff 时始终把 **current structure + matching current atom map** 作为同一对接口继续传递。1.5 不修改 map，但也不使当前 map 失效。

普通已实现子环节之间不需要返回 Manager 调度，也不需要额外 Workflow dispatcher。

Manager 初始规划使用：

`00_manager/references/workflow_plan_index.yaml`

Manager 不需要读取本 Skill 来做初始 step catalog 展开。

## Stage-level handoff

### 1.1 → 1.2

1.2 消费 1.1 已明确的正式结构来源。1.2 不重新执行 source recognition。

### 1.2 → 1.3

1.3 消费 1.2 正式分类结果及其稳定身份。1.3 不重新构造 1.2 已建立的 `component_id` / `residue_id` 或重新判断分类关系；1.3 同时以 1.2 实际检查的结构为原始结构，为每个 target 初始化 atom map。

### 1.3 → 1.4

1.4 消费 1.3 最终选中的 target PDB **及与该 PDB 对应的正式 atom map**。只有用户明确要求分别建立多个结构时，1.3 才形成多个 target；后续按 target 分别推进。

### 1.4 → 1.5

1.5 消费当前 target 的当前结构，并结合 1.2 正式缺失残基与重原子组成/命名检查结果、1.3 target mapping 和实际存在的 1.4 `altloc_resolution_report.yaml`，生成该 target 独立的 `structure_completeness_report.yaml`。1.5 不修改结构，也不维护 atom map；进入 1.5 前与当前结构对应的 map 继续作为该结构的 current atom map。具体规则由 `1.5_completeness_check/SKILL.md` 拥有。

### 1.5 → 1.6

1.6 消费当前 target 的 1.5 正式 `structure_completeness_report.yaml`、其中 `structure` 字段记录的当前 PDB，以及**与该 PDB 对应的最近正式 atom map**，并落实报告中已明确的 repair items。具体规则由 `1.6_structure_completion/SKILL.md` 拥有。

### 1.6 → 1.7

1.7 消费当前 target 在 1.6 处理后的 **current structure + matching atom map**：

- 如果 1.6 本地执行并形成通过 validation 的正式结果，使用该次 `completed_structure.pdb` + `atom_mapping.yaml`；
- 如果 1.6 复用了等价的既有正式结果，使用被复用结果中的 `completed_structure.pdb` + matching `atom_mapping.yaml`；
- 如果 1.6 因没有 repair item 而未执行，则沿用进入 1.6 前的 current structure + current atom map。

1.7 的内部执行规则由 `1.7_protein_protonation_assignment/SKILL.md` 拥有，Stage main 只维护这里的结构/map handoff。

### 1.7 → 1.8

1.8 消费已经落实蛋白质 protonation-state residue naming 的 **current heavy-atom structure + matching atom map**，并结合 1.3 target mapping 与 1.2 正式分类和关系信息，形成 `stage1_final.pdb` 与 `stage1_final_map.yaml`。具体规则由 `1.8_reorder_and_mapping/SKILL.md` 拥有。

### 1.8 → 1.9

1.9 对 1.8 的 `stage1_final.pdb` + `stage1_final_map.yaml` 做阶段级只读终检，并生成逐项 `structure_preparation_validation.md`。1.9 不修改结构或 map，也不生成整体 `PASS / FAIL`；发现的问题按报告中的实际对象返回真正拥有该问题的上游子环节处理。

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

Stage 1 的 1.1–1.9 均已有 current Skill。1.9 是 Stage 1 最终只读检查步骤；其完成表示规定检查已经执行并形成当前 target 的 `structure_preparation_validation.md`，不表示 Skill 自动给出了整体通过结论。

是否根据报告返回上游处理，或将当前 Structure preparation 结果交给 Stage 2，由当前任务根据报告中的实际检查结果和用户要求决定。

本 Stage main Skill 不另造阶段级重复结果包、route、decision、event 或 runtime state。

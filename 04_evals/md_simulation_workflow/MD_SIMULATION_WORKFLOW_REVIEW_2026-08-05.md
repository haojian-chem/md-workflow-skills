# MD simulation Workflow 复核报告

```yaml
status: WORKFLOW_REDESIGN_REQUIRED
branch: draft/md-simulation-skills
review_date: 2026-08-05
review_basis: MD_SIMULATION_DISCUSSION_DECISIONS.md
continue_detail_design: false
modify_existing_workflow_incrementally: not_recommended
```

## 1. 复核范围

本次复核以以下文件为主：

```text
01_workflows/md_simulation_workflow/SKILL.md
01_workflows/md_simulation_workflow/references/run_unit_model.md
01_workflows/md_simulation_workflow/references/execution_attempt_model.md
01_workflows/md_simulation_workflow/references/simulation_plan_ownership.md
02_operations/md_simulation_protocol_specification/SKILL.md
02_operations/md_simulation_plan_materialization/SKILL.md
02_operations/md_run_input_preparation/SKILL.md
02_operations/md_execution_attempt_specification/SKILL.md
02_operations/md_run_execution/SKILL.md
02_operations/md_simulation_output_assembly/SKILL.md
02_validators/md_run_output_validator/SKILL.md
02_validators/md_simulation_output_validator/SKILL.md
02_validators/md_simulation_completion_validator/SKILL.md
```

并对照：

```text
04_evals/md_simulation_workflow/MD_SIMULATION_DISCUSSION_DECISIONS.md
main: 00_authoring/skill_inventory.yaml
main: 01_workflows/structure_preparation_workflow/SKILL.md
```

## 2. 总体结论

当前 `md_simulation_workflow` 不是在简单 MD 执行流程上增加必要控制，而是建立了一个独立的多层运行管理系统：

```text
scientific protocol
→ task-projection plan
→ MD_INPUT artifact
→ execution-attempt spec
→ submission/status evidence
→ run-level MD_OUTPUT artifact
→ stage-level MD_OUTPUT collection
→ completion gate
```

该模型与已经确认的实际需求不符，并且大量职责与 Manager、项目日志、文件系统及实际 GROMACS 文件重复。

因此：

- 不应继续按当前 15 个 Skill、14 个 schema 的结构补充细节；
- 不建议局部修补原 Workflow；
- 应保留必要的 MDP/TPR/执行/检查能力，重新设计一条更短的主流程；
- protocol 与 plan、状态体系、阶段验证标准等暂缓事项，应在新主流程确定后再讨论。

## 3. 已确认的主要冲突

### 3.1 阶段边界错误

现有 Workflow 和 references 多次声明：

```text
SYSTEM 改变时返回 md_preparation_workflow
```

已确认的正确规则是：

- 04 不修改 SYSTEM；
- 发现 SYSTEM 问题时停止并反馈；
- 用户改变体系属于另一条 Workstream；
- 当前 Workflow 不设置回退或反向跳转。

### 3.2 run unit 类型错误

现有模型使用：

```text
ENERGY_MINIMIZATION
EQUILIBRATION
PRODUCTION
CUSTOM
```

已确认使用：

```text
EM
NVT
NPT
MD
```

现有 `EQUILIBRATION/PRODUCTION/CUSTOM` 不能继续作为 v1 run unit 类型。

### 3.3 run unit 信息模型过重

现有 protocol run unit 保存：

- role；
- dependencies；
- MDP spec；
- start state；
- completion criteria；
- expected output roles；
- field provenance；
- unresolved gates。

已确认的集中式 `04_md_simulation/run_unit.yaml` 当前只需保存：

```text
run_unit_id
run_unit_type
start_from_run_unit_id
```

不需要关系枚举、DAG 关系类型或多层 start-state 对象。

### 3.4 预计路线被 protocol、plan、route 三层重复表达

现有结构同时存在：

```text
scientific protocol
simulation task-projection plan
Manager route
```

并在 plan 中继续保存 run-unit projection、依赖、路径和 gate。

已确认项目内还需要：

```text
04_md_simulation/expected_route.yaml
```

该文件只记录预计路线，且不硬性锁定。

因此当前 protocol/plan/route 三层与 `run_unit.yaml + expected_route.yaml` 的关系尚未厘清。继续保留两套模型会产生明显重复。是否保留 protocol 和 plan 必须在新主流程中重新判断。

### 3.5 MDP 生成方式与需求相反

现有 protocol/input 模型要求：

- 只能接受最终 MDP，或模板加逐项 typed overrides；
- 不允许根据开放式自然语言生成；
- 不允许根据常见流程或体系情况补充参数；
- 每个科学字段必须建立 field-level provenance。

已确认的需求是：

```text
用户描述 + 体系情况 + 模板
→ 智能体生成 MDP 草案
→ 汇总真正不清楚的内容
→ 一次性向用户确认
→ 最终 MDP
```

现有模型会把智能体降格为机械模板替换器，无法完成所需的科研辅助任务。

### 3.6 目录结构与实际约定冲突

现有结构：

```text
04_md_simulation/
├── 00_plan/
├── <run_unit_id>/input/
├── <run_unit_id>/attempts/<attempt_id>/
└── 99_validation/
```

已确认结构：

```text
04_md_simulation/
├── run_unit.yaml
├── expected_route.yaml
├── em.1/
├── nvt.1/
├── npt.1/
└── md.1/
```

各 run unit 目录直接保存：

```text
<run_unit_id>.mdp
<run_unit_id>.tpr
<run_unit_id>.log
<run_unit_id>.edr
<run_unit_id>.xtc/.trr
<run_unit_id>.gro
<run_unit_id>.cpt
```

不建立 `00_plan/`、`input/`、`attempts/`、`99_validation/` 等固定层级。

### 3.7 execution attempt 层不符合日志职责

现有模型为每次执行建立：

- attempt ID；
- execution spec；
- attempt Validator；
- command record；
- submission evidence；
- status report；
- attempt-specific output directory；
- accepted attempt chain。

已确认：

- 执行命令、tmux、时间、失败原因、append、重跑过程进入项目既有日志；
- 不建立 `execution_records/`；
- 也不需要功能等价的 `attempts/` 业务层。

因此 execution-attempt spec、Validator 和 attempt directory 当前没有保留依据。

### 3.8 continuation 规则与实际决策冲突

现有模型：

```text
APPEND 禁止
CONTINUE_NOAPPEND 属于原 run unit 的新 attempt
```

已确认：

- append 续跑：仍属于原 run unit；
- noappend 生成独立输出段：建立新的 run unit；
- 从前一步 `.gro + .cpt` 生成新 TPR：建立新的 run unit；
- 是否保留失败任务决定原地重跑还是新 run unit。

现有 attempt chain 需要整体重写，不能只改枚举名称。

### 3.9 外部 scheduler 模型不需要

现有执行 Operation 支持：

```text
LOCAL
TMUX
LSF
SLURM
PBS
```

并建立 prepared submission、submission ID、scheduler 状态和恢复模型。

已确认：

- 智能体只代为执行本地任务；
- 短任务前台同步；
- 长任务使用 tmux；
- 文件同步到外部后，由使用者自行提交；
- v1 不负责 LSF、SLURM、PBS 或远程状态查询。

因此 scheduler、submission 和对应 status Validator 应从 04 v1 中删除。

### 3.10 stage-level 输出对象没有充分依据

现有 Workflow 强制：

```text
run-level MD_OUTPUT
→ stage-level MD_OUTPUT collection
→ completion Validator
```

并增加 output assembly Operation、output Validator 和 `99_validation/`。

当前已确认：

- 04 不负责选择分析对象；
- 不能以“方便分析”为理由增加输出索引；
- 是否需要阶段级汇总对象尚未确认。

在 `run_unit.yaml`、`expected_route.yaml`、run unit 目录和项目状态已经存在的情况下，stage-level collection 当前高度疑似重复，应暂时移除主流程。

### 3.11 completion gate 依赖大量待删除对象

现有 completion Validator 要求闭合：

```text
protocol
plan
MD_INPUT artifact
attempt spec
submission
run-level MD_OUTPUT artifact
stage-level MD_OUTPUT artifact
```

其中多数对象已与确认规则冲突。因此当前 completion Validator 不能直接保留。

### 3.12 对分析 Workflow 的假定越界

现有 completion Validator 声称通过后“可以交给 `analysis_workflow`”，output assembly 还保存分析所需分段顺序和 final state 选择。

当前仓库没有已经确认的分析阶段接口可支持这些假定。04 应只保证自身任务和输出可定位、可检查，不预先决定分析对象或分析入口格式。

## 4. 当前设计中可保留的能力

尽管对象模型需要重构，下列业务能力仍然必要：

1. 根据用户描述、体系信息和模板生成 MDP 草案；
2. 集中提出不明确且具有实际影响的问题；
3. 生成最终 MDP；
4. 执行 `grompp` 并生成 TPR；
5. 检查 `grompp` warning/error；
6. 本地短任务前台运行；
7. 本地长任务通过 tmux 运行；
8. 检查本地运行状态；
9. 对 EM、NVT、NPT、MD 分阶段检查结果；
10. 处理 append 续跑、noappend 新 run unit、失败保留或原地重跑；
11. 维护 `run_unit.yaml` 和 `expected_route.yaml`；
12. 将执行过程写入项目既有日志。

这些能力应作为新 Workflow 的基础，而不是继续依附旧 attempt/submission/artifact collection 模型。

## 5. 建议的新主流程骨架

以下只是复核后的最小骨架，不是最终 Skill 拆分：

```text
1. 读取当前 Workstream、SYSTEM、run_unit.yaml、expected_route.yaml 和用户请求

2. 如当前请求需要新增或调整 run unit：
   - 生成/更新 run_unit.yaml
   - 生成/更新 expected_route.yaml
   - 预计路线不硬性锁定

3. 对当前目标 run unit：
   - 根据用户描述、体系情况和模板生成 MDP 草案
   - 汇总未决项并一次性确认
   - 写最终 <run_unit_id>.mdp

4. 使用 SYSTEM 或 start_from_run_unit_id 对应的 .gro/.cpt：
   - 执行 grompp
   - 生成 <run_unit_id>.tpr
   - 检查预处理结果

5. 根据用户请求和执行位置：
   - 仅准备文件并停止；或
   - 本地短任务前台运行；或
   - 本地长任务使用 tmux 运行；或
   - 外部任务由用户自行同步和提交

6. 检查当前 run unit 状态和结果：
   - 当前运行未结束：停止本轮并反馈状态
   - 失败：按是否保留失败任务决定原地重跑或新 run unit
   - append 续跑：保留原 run unit
   - noappend 独立输出：建立新 run unit
   - 完成：执行对应阶段验证

7. 当前请求范围完成后结束，不强制组装 stage-level 输出对象
```

## 6. 新主流程尚未解决的事项

以下内容应在确认主流程后逐项讨论：

1. protocol 与 plan 是否保留、合并或删除；
2. `run_unit.yaml` 与 `expected_route.yaml` 的 schema；
3. route 与 `expected_route.yaml` 的边界；
4. 状态体系；
5. EM、NVT、NPT、MD 的分阶段验证；
6. MDP 生成 Operation 与检查 Validator 如何拆分；
7. TPR 生成与 MDP 检查是否在同一 Operation；
8. 本地执行与状态检查是否拆分；
9. run unit 完成是否需要独立 Validator；
10. 是否需要任何 artifact manifest；
11. 外部执行结果回传后的恢复入口。

## 7. 已做过 / 已否定 / 仍未验证

### 已做过

- 保存当前讨论决策；
- 检查主 Workflow；
- 检查 protocol、plan、MD input、attempt、execution、run output、stage output、completion 设计；
- 对照当前 main 的 Workstream/Workflow 双接口框架；
- 形成最小重构骨架。

### 已否定

- 04 内部返回 `md_preparation_workflow`；
- `ENERGY_MINIMIZATION/EQUILIBRATION/PRODUCTION/CUSTOM` v1 类型；
- `00_plan/`、`input/`、`attempts/`、`99_validation/` 固定目录；
- 每个 run unit 的 execution-attempt 业务层；
- v1 外部 scheduler/submission 模型；
- APPEND 全面禁止；
- noappend 仍属于原 run unit；
- 以分析便利性预设 stage output index；
- 当前 completion gate 的完整依赖链。

### 仍未验证

- 新简化流程与 Manager 当前 contracts 的映射；
- protocol/plan 是否仍有必要；
- 状态和恢复规则；
- 各阶段科学/技术验证标准；
- 最小 Skill 拆分；
- schema 和 fixtures；
- 真实 GROMACS 项目运行。

## 8. 分支风险

当前 `draft/md-simulation-skills` 与 `main` 已分叉，并落后主线大量提交。新 Workflow 重构前，需要重新核对当前主线的：

```text
Manager contracts
stage registry
artifact/status rules
content maps
repository validation requirements
```

本次报告只确认 04 业务流程存在结构性问题，不宣称旧分支与当前主线已经兼容。

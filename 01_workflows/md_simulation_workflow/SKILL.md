---
name: md_simulation_workflow
description: 为一个 Focus Workstream 规划并推进 MD 模拟阶段：从 VALIDATED SYSTEM 生成并验证 protocol/plan，为每个科学 run unit 准备 VALIDATED MD_INPUT，生成并验证 execution attempts，执行或提交、按需检查状态、验证 run-level MD_OUTPUT，最后组装并验证唯一 stage-level MD_OUTPUT collection。该 Workflow 不执行子 Skill、不轮询外部任务，也不修改业务或管理文件。
---

# 目标

```text
VALIDATED SYSTEM
→ validated simulation protocol
→ validated simulation plan
→ per-run VALIDATED MD_INPUT
→ one or more validated execution attempts
→ per-run VALIDATED MD_OUTPUT
→ validated stage-level MD_OUTPUT collection
```

本 Workflow 不写死 `EM → NVT → NPT → production`。run unit 数量、科学 role、依赖、MDP 和完成标准必须来自明确结构化输入或决定。

# 权威阶段边界

```text
md_preparation_workflow
→ complete VALIDATED SYSTEM

md_simulation_workflow
→ protocol / plan / MDP / grompp / TPR
→ execution attempts / submissions
→ MD_OUTPUT
```

只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子改变时才返回 `md_preparation_workflow`。

# 对象模型

详细语义：

```text
references/simulation_plan_ownership.md
references/run_unit_model.md
references/execution_attempt_model.md
```

必须区分：

- protocol run unit：科学片段；
- execution attempt：一次具体运行/提交；
- run-level MD_OUTPUT：一个 run unit 的 accepted attempt chain；
- stage-level MD_OUTPUT：当前 scope 内 required run outputs 的集合；
- Workstream route：Manager 拥有的 task projection。

# 共同输入

Manager 必须提供：

- Focus Workstream state、active route 和 resolved scope；
- 当前有效 SYSTEM、MD_INPUT、run-level/stage-level MD_OUTPUT artifacts；
- protocol、plan 及 Validator evidence，如存在；
- execution-attempt specs/results/submissions/status evidence；
- resolved decisions 和显式文件/profile identities；
- Skill availability；
- project root 与 `04_md_simulation/`。

缺少 Workstream/scope 时 BLOCKED。科学协议未明确时 PAUSE 并返回 confirmation items，禁止默认生成标准流程。

# 职责边界

负责：

- 定义本阶段 substeps 和动态 task projection；
- 判断当前需要 protocol、plan、input、attempt specification、execution、status、run output、stage output 或 completion 中的一个 task unit；
- 在外部 attempt 运行时 PAUSE；
- 根据最新 evidence 返回 EXECUTE、SKIP、PAUSE、BLOCKED 或 COMPLETE；
- 返回 route revision signal。

不得：

- 自行生成 protocol、plan、MDP、TPR、execution spec 或 output manifest；
- 执行 `grompp`、`mdrun`、tmux 或 scheduler command；
- 从常见实践推导 run units、参数、backend、资源、checkpoint 或 thresholds；
- 将 continuation 作为科学 role；
- 高频轮询；
- 根据目录/时间戳推断完成；
- 修改 state、records、route、artifacts 或业务文件；
- 将技术通过表述为科学平衡或收敛。

# 科学 role 与 continuation

run unit role 只允许：

```text
ENERGY_MINIMIZATION
EQUILIBRATION
PRODUCTION
CUSTOM
```

same-TPR continuation 是新的 execution attempt：

```text
CONTINUE_NOAPPEND
```

v1 不启用 APPEND。改变 MDP/TPR/科学目标时创建新的或 superseding run unit，不作为 continuation attempt。

# 阶段目录

```text
04_md_simulation/
├── 00_plan/
│   ├── simulation_protocol_spec*.yaml
│   ├── md_simulation_plan*.yaml
│   └── protocol/plan validation reports
├── <run_unit_id>/
│   ├── input/
│   │   ├── run.mdp
│   │   ├── run.tpr
│   │   ├── md_run_input_manifest.yaml
│   │   └── md_run_input_validation_report.yaml
│   ├── attempts/
│   │   ├── attempt.001/
│   │   ├── attempt.002/
│   │   └── ...
│   ├── md_run_output_manifest.yaml
│   └── md_run_output_validation_report.yaml
└── 99_validation/
    ├── md_simulation_output_manifest.yaml
    ├── md_simulation_output_validation_report.yaml
    └── md_simulation_completion_report.yaml
```

目录和文件存在均不是完成证据。

# 动态 Substep registry

## 0. specify_and_validate_simulation_protocol

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_simulation_protocol_specification
validator: md_simulation_protocol_validator
work_directory: 04_md_simulation/00_plan
```

前置：VALIDATED SYSTEM、resolved scope、显式 scientific inputs/files。无法确定解析的字段形成 confirmation items。

完成：protocol Validator 接受 immutable protocol spec。

## 1. materialize_and_validate_simulation_plan

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_simulation_plan_materialization
validator: md_simulation_plan_validator
work_directory: 04_md_simulation/00_plan
```

前置：validated protocol。plan 只保存 task projection、依赖 gate、路径和 revision lineage，不成为科学字段第二 owner。

完成：plan Validator 接受 immutable plan。

## 对每个 selected run unit

### 2. prepare_and_validate_run_input:<run_unit_id>

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_run_input_preparation
validator: md_run_input_validator
work_directory: 04_md_simulation/<run_unit_id>/input
```

前置：validated protocol/plan、VALIDATED SYSTEM 或上游 VALIDATED run output、明确 MDP source/typed overrides、input-preparation unresolved items 已解决。

完成：Manager 登记 VALIDATED MD_INPUT。

### 3. specify_and_validate_execution_attempt:<run_unit_id>:<attempt_id>

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_execution_attempt_specification
validator: md_execution_attempt_validator
work_directory: 04_md_simulation/<run_unit_id>/attempts/<attempt_id>
```

初始 attempt 通常为 `attempt.001/FRESH`。retry/continuation attempt 只有在 validator/recovery/用户决定明确要求后，通过 route revision 增加。

前置：VALIDATED MD_INPUT、attempt ID/kind、backend/resource/runtime profile、prepared submission identity（异步）、parent/checkpoint（如适用）。

完成：validated execution-attempt spec。

### 4. execute_attempt:<run_unit_id>:<attempt_id>

```text
mode: OPERATION
operation: md_run_execution
validator: null
work_directory: 04_md_simulation/<run_unit_id>/attempts/<attempt_id>
```

前置：validated attempt spec、VALIDATED MD_INPUT、无 attempt path/submission conflict、首个外部长任务 FULL runtime gate 通过。

完成：同步 process terminal，或异步 submission accepted。均不表示 run unit completed。

### 5. check_attempt_status:<run_unit_id>:<attempt_id>

```text
mode: VALIDATOR
validator: md_run_status_validator
necessity: CONDITIONAL
```

条件：异步 submission 为 SUBMITTED/RUNNING/UNKNOWN 且当前需要刷新。

状态新鲜且仍运行时 PAUSE；同步 attempt 或可信 terminal status 时 SKIP。

### 6. validate_run_output:<run_unit_id>

```text
mode: VALIDATOR
validator: md_run_output_validator
work_directory: 04_md_simulation/<run_unit_id>
```

前置：所有当前相关 attempts terminal，无 active/UNKNOWN branch。

Validator 重建 accepted attempt chain：

- target 已达到：返回 run-level MD_OUTPUT candidate；
- same-TPR 运行未完成且 continuation 可行：返回 route revision signal，新增 CONTINUE_NOAPPEND attempt；
- retry/branch selection 未解决：PAUSE；
- 需要新 TPR：修订 protocol/plan/run input；
- SYSTEM 改变：返回 md_preparation。

## Workflow exit steps

### 7. assemble_and_validate_simulation_output

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_simulation_output_assembly
validator: md_simulation_output_validator
work_directory: 04_md_simulation/99_validation
```

前置：scope 内全部 required run units 有 VALIDATED run-level MDOUTPUT。

完成：Manager 登记唯一 stage-level VALIDATED MDOUTPUT collection。它引用所有 required run outputs，不只引用最后一个 production segment。

### 8. workflow_completion_validation

```text
mode: VALIDATOR
validator: md_simulation_completion_validator
work_directory: 04_md_simulation/99_validation
```

前置：validated stage-level MDOUTPUT 已登记。

完成：route/protocol/plan/input/attempt/submission/run-output/stage-output lineage 全部闭合。

中间 substep 终点不强制执行 7–8。

# 规划接口

## Protocol 未验证

fragment 只能安全规划到 substep 0。不得虚构 run units。

## Protocol 已验证、plan 未验证

fragment 规划到 substep 1。

## Plan 已验证

按 scope 和 DAG 展开 run-unit tasks。每个首次运行只展开初始 FRESH attempt。未来 retry/continuation 由新 evidence 触发 route revision，不在无证据时预先加入。

## Workflow exit

必须追加 stage output assembly/validation 和 completion validation。

fragment 返回 `workflow_route_fragment.schema.yaml`，声明 SYSTEM entry 和 stage-level MDOUTPUT exit。

# 执行决策

每次只返回一个 task unit。

优先顺序按当前 route 和 evidence：

1. protocol gate；
2. plan gate；
3. run input gate；
4. attempt spec gate；
5. execute attempt；
6. status check 或 PAUSE；
7. run output validation；
8. stage output assembly/validation；
9. completion validation；
10. COMPLETE。

# SKIP

仅在有当前、等价、未失效的 Validator/artifact evidence 时 SKIP。不得凭目录、TPR、checkpoint、session 或文件时间戳跳过。

# PAUSE

用于：

- 科学/attempt/backend/resource/branch selection 需要决定；
- attempt 正在运行且无需刷新；
- Validator 成功但返回人工 gate；
- external resource 暂不可用且可恢复。

# BLOCKED

用于：

- protocol/plan/route scope 或 identities 冲突；
- DAG/lineage 无法解析；
- MD_INPUT/attempt spec 未验证；
- 可能已提交但 task/submission 未闭环；
- active attempt 与输出冲突；
- required Skill/Tool capability 缺失；
- stage output scope/artifacts 不一致。

# COMPLETE

中间 scope 终点达到时可返回 scope COMPLETE。

Workflow exit 只有在以下全部满足时 COMPLETE：

- validated protocol/plan；
- scope 内 required run units 有 VALIDATED MDINPUT 和 run-level MDOUTPUT；
- 无 active/UNKNOWN/FINISHED_UNVERIFIED attempts；
- 唯一 stage-level VALIDATED MDOUTPUT 覆盖全部 required run outputs；
- completion Validator 通过。

# Route revision signals

- protocol/plan scientific fields 变化；
- 新 run unit/新 TPR；
- retry/continuation attempt；
- backend/resource/attempt strategy 变化；
- attempt failed/cancelled/unknown 后采用替代；
- run output 未达到 target；
- stage output final-state selection 变化；
- artifacts invalidated/superseded；
- Skill/Tool availability 变化。

Workflow 返回原因和新 fragment，不写 route record。

# 阶段出口

```text
VALIDATED stage-level MDOUTPUT collection artifact
```

其业务 files 至少包含 stage output manifest 和 validation report，`derived_from_artifact_set_ids` 指向所有 included run-level MDOUTPUT artifacts。

该出口只证明技术执行和谱系闭合，不证明采样充分或科学收敛。

# 自检

- [ ] standard entry 为 VALIDATED SYSTEM；
- [ ] scientific run unit 与 execution attempt 已分离；
- [ ] CONTINUATION 未作为 role；
- [ ] execution spec 有专属生成者和 Validator；
- [ ] retry/continuation 使用新 attempt directory；
- [ ] v1 未启用 APPEND；
- [ ] status 是 ON_DEMAND；
- [ ] run output 验证 accepted attempt chain；
- [ ] stage output 包含全部 required segments；
- [ ] 每个 decision 只返回一个 task unit；
- [ ] Workflow 未执行子 Skill或修改文件；
- [ ] 技术完成未夸大为科学收敛。
---
name: md_simulation_workflow
description: 为一个 Focus Workstream 规划并推进 MD 模拟阶段。该 Workflow 从 VALIDATED SYSTEM 和已解决决定生成并验证 simulation protocol，再物化可修订 plan，为每个 run unit 准备和验证 MD_INPUT，随后管理执行、按需状态检查、输出核验与阶段完成 gate。它不执行子 Skill、不轮询外部任务，也不修改项目状态或业务文件。
---

# 目标

将一个 Workstream 从：

```text
VALIDATED SYSTEM
```

推进到：

```text
VALIDATED MD_OUTPUT
```

阶段内生命周期：

```text
specify_and_validate_protocol
→ materialize_and_validate_plan
→ per-run input preparation and validation
→ execute or submit
→ on-demand status check
→ output validation
→ workflow completion validation
```

本 Workflow 不把协议写死为 `EM → NVT → NPT → production`。EM、任意平衡片段、production segment 和显式 continuation 均为独立 run unit；run unit 数量、顺序和参数必须来自明确决定或文件。

# 权威阶段边界

权威 `stage_registry.yaml` 规定：

```text
md_preparation_workflow
→ 完整体系生成
→ VALIDATED SYSTEM

md_simulation_workflow
→ MDP 与运行输入准备
→ EM / equilibration / production / continuation
→ VALIDATED MD_OUTPUT
```

因此：

- 标准入口为 VALIDATED SYSTEM，不是预生成 MD_INPUT；
- protocol、plan、`.mdp`、`grompp`、`.tpr` 和 execution 属于本 Workflow；
- 只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子需要改变时，才返回 `md_preparation_workflow`。

详细语义：

```text
references/simulation_plan_ownership.md
references/run_unit_model.md
```

# 共同输入

Manager 必须提供：

- Focus `workstream_id` 和 Workstream state；
- active route、已解析起点、终点和停止条件；
- 当前有效 SYSTEM、MD_INPUT 和 MD_OUTPUT artifact sets；
- 当前 protocol spec、plan 及其 Validator evidence，如存在；
- submission records 及最新状态；
- 当前有效 resolved decisions；
- 显式 MDP/template file records；
- Skill availability；
- 项目根和 `04_md_simulation/` 业务目录。

规划接口还必须提供：

- 本 Workflow 内的 start/end；
- resolved route scope；
- 已知科学协议、文件、backend、资源、restart 和停止约束；
- 若已有 validated plan，请求范围内 run unit IDs 或可唯一解析的范围。

执行接口还必须提供当前 protocol/plan/run unit lifecycle position，以及 task/result/artifact/submission evidence。

缺少 Workstream 或范围时 BLOCKED。科学协议未明确时 PAUSE 并返回 confirmation items；不得默认生成标准流程。

# 职责边界

负责：

- 定义 protocol、plan、run unit 和阶段内 substeps；
- 返回本阶段 route fragment；
- 判断 protocol/plan/input/execution/status/output/completion 中的一个当前 task unit；
- 根据最新 evidence 决定 EXECUTE、SKIP、PAUSE、BLOCKED 或 COMPLETE；
- 外部任务运行时返回 PAUSE，不创建轮询循环；
- 返回 route revision signal。

不得：

- 自行生成 protocol、plan、MDP、TPR、checkpoint 或 execution spec；
- 执行 `grompp`、`mdrun`、tmux 或 scheduler 命令；
- 从常见实践推导 run units、参数、checkpoint、append、maxwarn 或 threshold；
- 根据目录或时间戳推断完成；
- 修改 state、records、route、plan、submission 或 artifact；
- 拼接其他 Workflow；
- 直接向用户提问；
- 创建或管理子 Agent；
- 将技术通过表述为科学平衡、采样充分或收敛。

# 阶段内对象

## Simulation protocol spec

由：

```text
md_simulation_protocol_specification
→ md_simulation_protocol_validator
```

从 VALIDATED SYSTEM、resolved decisions、route scope 和显式文件物化并验证。

每个科学字段必须有 field provenance。PLAN_VALIDATION 类未决项阻止进入 plan；INPUT_PREPARATION 和 EXECUTION 类未决项可以保留到对应 barrier。

Schema：

```text
schemas/md_simulation_protocol_spec.schema.yaml
```

## Simulation plan

由：

```text
md_simulation_plan_materialization
→ md_simulation_plan_validator
```

从 validated protocol spec 物化 immutable plan。

plan 是阶段内科学运行方案；Workstream route 是 Manager 根据 fragment 生成的 task projection。二者不可混用。plan 变化生成新版本，记录 `supersedes_plan_id` 并触发 route revision；不得覆盖旧 plan。

Schema：

```text
schemas/md_simulation_plan.schema.yaml
```

## Run unit

每个 run unit 至少包含：

- stable `run_unit_id`；
- role；
- sequence 和 explicit dependencies；
- work directory；
- MDP identity；
- SYSTEM 或 prior-run start-state；
- grompp 设置；
- execution policy；
- expected outputs 和 completion criteria。

名称如 `em.1`、`npt.1`、`md.1` 只用于身份，不推导参数。

# 阶段目录

```text
04_md_simulation/
├── 00_plan/
│   ├── simulation_protocol_spec.yaml
│   ├── md_simulation_protocol_validation_report.yaml
│   ├── md_simulation_plan.yaml
│   └── md_simulation_plan_validation_report.yaml
├── <run_unit_id>/
│   ├── input/
│   │   ├── run.mdp
│   │   ├── run.tpr
│   │   ├── md_run_input_manifest.yaml
│   │   └── md_run_input_validation_report.yaml
│   ├── md_run_execution_spec.yaml
│   ├── command_record.yaml
│   ├── execution.log
│   ├── submission_evidence.yaml
│   ├── status_report.yaml
│   ├── output_validation_report.yaml
│   └── <engine outputs>
└── 99_validation/
    └── md_simulation_completion_report.yaml
```

目录或文件存在不是完成证据。

# 动态 Substep registry

## 0. specify_and_validate_simulation_protocol

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_simulation_protocol_specification
validator: md_simulation_protocol_validator
work_directory: 04_md_simulation/00_plan
necessity: REQUIRED at Workflow entry; CONDITIONAL when an equivalent validated protocol exists
```

目标：将明确 decisions/files 结构化为 protocol spec，并独立检查 field provenance、隐式默认值和未决项分类。

前置 gate：

- VALIDATED SYSTEM 可用；
- route scope 已解析；
-影响协议的当前 decision records 和显式 MDP/template 可定位；
- 输出不覆盖旧版本。

已有等价且仍有效的 validated protocol 时可 SKIP。

## 1. materialize_and_validate_simulation_plan

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_simulation_plan_materialization
validator: md_simulation_plan_validator
work_directory: 04_md_simulation/00_plan
necessity: REQUIRED after protocol validation; CONDITIONAL when an equivalent validated plan exists
```

前置 gate：

- protocol Validator outcome 允许进入 plan；
- PLAN_VALIDATION 未决项为空；
- SYSTEM 和 MDP identities 可定位；
- plan 输出不覆盖旧版本。

完成证据：plan Validator 建议接受计划。该步骤不创建 MD_INPUT artifact。

## 对每个 run unit 展开

### 2. prepare_and_validate_run_input:<run_unit_id>

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_run_input_preparation
validator: md_run_input_validator
work_directory: 04_md_simulation/<run_unit_id>/input
necessity: REQUIRED
```

前置 gate：

- validated plan 有效；
- run unit 唯一且 dependencies ready；
- INPUT_PREPARATION blocking items 为空；
- start state 为 VALIDATED SYSTEM 或上游 VALIDATED MD_OUTPUT；
- MDP、topology、coordinates 和可选 checkpoint 唯一；
- grompp capability 可用；
- 输出无冲突。

完成证据：MD_INPUT candidate 经专属 Validator 通过并由 Manager 登记为 VALIDATED。已有等价 VALIDATED MD_INPUT 时可 SKIP。

### 3. execute_run_unit:<run_unit_id>

```text
mode: OPERATION
operation: md_run_execution
validator: null
work_directory: 04_md_simulation/<run_unit_id>
necessity: REQUIRED
```

前置 gate：

- validated plan/run unit 可用；
- 当前 MD_INPUT 为 VALIDATED；
- dependencies 的 MD_OUTPUT 已通过；
- EXECUTION blocking items 为空；
- checkpoint/append policy、backend、resources 和 execution spec 明确；
- 工作目录无冲突；
- 首个外部长任务前所需 FULL runtime validation 已通过。

完成证据：同步进程结束，或异步提交被接受并产生 submission evidence。提交成功不等于模拟完成。

### 4. check_run_unit_status:<run_unit_id>

```text
mode: VALIDATOR
validator: md_run_status_validator
work_directory: 04_md_simulation/<run_unit_id>
necessity: CONDITIONAL
condition: asynchronous submission is SUBMITTED, RUNNING or UNKNOWN and an on-demand refresh is required
```

状态检查只执行一次。任务仍运行且当前无需刷新时 PAUSE。同步运行或已有可信 terminal status 时 SKIP。

### 5. validate_run_unit_output:<run_unit_id>

```text
mode: VALIDATOR
validator: md_run_output_validator
work_directory: 04_md_simulation/<run_unit_id>
necessity: REQUIRED
```

前置 gate：

- 同步进程结束，或异步 submission 为 FINISHED_UNVERIFIED；
- validated MD_INPUT、execution spec、command 和 provenance 可用；
- outputs 已停止写入；
- 不存在活动进程。

完成证据：Validator 建议接受 MD_OUTPUT candidate。

## 6. workflow_completion_validation

```text
mode: VALIDATOR
validator: md_simulation_completion_validator
work_directory: 04_md_simulation/99_validation
necessity: REQUIRED for Workflow exit
```

核验 protocol、plan、MD_INPUT、run units、submissions、MD_OUTPUT 和 lineage 闭合。终点仅为某个中间 substep 时不强制执行。

# 规划接口

Manager 请求 fragment 时，本 Workflow：

1. 核验 start/end 和停止条件；
2. 判断 protocol 是否存在且有效；
3. 无 validated protocol 时，只安全规划 protocol gate；
4. 有 validated protocol 但无 validated plan 时，规划到 plan gate；
5. 有 validated plan 时，按其 DAG 展开请求范围内 run units；
6. 对每个 run unit 展开 input、execution、conditional status 和 output validation；
7. 保留 REQUIRED steps；无 evidence 时不提前删除 CONDITIONAL status check；
8. Workflow exit 时追加 completion validation；
9. 声明 entry requirements、exit MD_OUTPUT、assumptions 和 blockers；
10. 返回 `workflow_route_fragment.schema.yaml`。

Fragment 状态：

- `COMPLETE`：请求范围可完整表达；
- `PARTIAL`：只能规划到 protocol/plan gate，或后续边界仍未解析；
- `BLOCKED`：入口 SYSTEM、范围、当前对象或必要 Skill 无法安全确定。

标准 entry requirement 为 VALIDATED SYSTEM。若起点位于已有后续 substep，可以要求相应 validated protocol、plan、MD_INPUT、submission 或 MD_OUTPUT evidence。

`next_workflow_hint` 为 `analysis_workflow`，要求当前范围的 VALIDATED MD_OUTPUT。

# 执行接口

每次只返回一个决定和至多一个 task unit。

## EXECUTE 优先顺序

- protocol 不存在、失效或需修订：protocol Operation + Validator；
- plan 不存在、失效或需修订：plan Operation + Validator；
- run input 未验证：input Operation + Validator；
- input 已验证且未执行：execution Operation；
- 异步任务需要刷新：status Validator；
- 任务结束未核验：output Validator；
- 范围闭合且要求 Workflow exit：completion Validator。

## SKIP

仅在可信 evidence 支持时跳过等价 validated protocol、plan、MD_INPUT、MD_OUTPUT，或不适用的 status check。不得仅凭目录、文件名或时间戳跳过。

## PAUSE

用于：

- protocol 科学决定未解决；
- INPUT_PREPARATION/EXECUTION 未决项到达其 barrier；
- submission 正在运行且无需刷新；
- backend/resource 暂不可用；
- checkpoint、append、maxwarn、输出冲突或人工判断待解决。

## BLOCKED

用于：

- SYSTEM 缺失、失效或未验证；
- scope/protocol/plan/run unit 不唯一；
- protocol provenance 不完整或存在隐式默认；
- plan DAG/start-state 无效；
- 所需 MD_INPUT/MD_OUTPUT 缺失或失效；
- task/submission/artifact/Workstream state 矛盾；
- 活动进程或输出冲突无法解释；
- 必要 Skill/backend capability 缺失；
- 存在未闭环 task 需要恢复。

## COMPLETE

请求终点已达到。Workflow exit 还要求：

- validated protocol 和 plan 覆盖当前范围；
- required MD_INPUT/MD_OUTPUT 谱系闭合；
- 不存在 active、UNKNOWN 或 FINISHED_UNVERIFIED submission；
- completion Validator 通过；
- final MD_OUTPUT 已由 Manager 登记为 VALIDATED。

# 外部任务状态

```text
SUBMITTED | RUNNING
→ on-demand status check
→ FINISHED_UNVERIFIED
→ output validation
→ COMPLETED | FAILED
```

backend 报告结束后先进入 FINISHED_UNVERIFIED。只有 output Validator 通过后 Manager 才可标记 COMPLETED。job/session 消失但证据不足时不得自动判定失败或成功。

# 修订与跨 Workflow 边界

- protocol scientific fields、run units、MDP、start state 或 completion criteria 改变：新 protocol + plan version；
- `.tpr` 改变：重新准备 MD_INPUT；
- 相同 `.tpr`、明确 checkpoint 和 append policy 的 continuation：可只生成新 execution spec；
- backend/resource 改变且科学输入不变：通常只需新 execution spec；
- SYSTEM 结构、拓扑、盒子、溶剂或离子改变：返回 `md_preparation_workflow`；
- 已有有效下游结果时不得覆盖，创建新版本、run unit 或 Workstream。

以上变化可能触发 route revision；Workflow 只返回理由和 fragment，不写 route、spec 或 plan。

# 阶段出口

阶段出口为 VALIDATED MD_OUTPUT，至少包含当前范围所需的：

- final structure/checkpoint；
- required trajectory、energy 和 log；
- validated protocol、plan 和 MD_INPUT provenance；
- input/output validation reports；
- command、submission 和 continuation provenance；
- completion report，如要求 Workflow exit。

该出口只说明技术 gate 通过，不证明科学收敛。

# 返回

规划返回：

```text
03_contracts/workflow_route_fragment.schema.yaml
```

执行返回：

```text
03_contracts/workflow_decision.schema.yaml
```

不返回 subagent result，不直接更新 state/records。

# 自检

- [ ] 标准入口为 VALIDATED SYSTEM；
- [ ] protocol spec 由专属 Operation/Validator 生成和验证；
- [ ] 每个科学字段要求 provenance；
- [ ] 未固定或隐式补充 EM/NVT/NPT/production；
- [ ] protocol、plan 与 Workstream route 已区分；
- [ ] plan 可修订且旧版本不覆盖；
- [ ] 每个 run unit 的 input、execution、status 和 output validation 已分离；
- [ ] 外部任务没有轮询循环；
- [ ] FINISHED_UNVERIFIED 后才输出核验；
- [ ] checkpoint、append 和 maxwarn 未隐式选择；
- [ ] 每次 execution decision 只有一个 task unit；
- [ ] 新 TPR 未错误归回 md_preparation；
- [ ] Workflow exit 要求 VALIDATED MD_OUTPUT；
- [ ] 技术完成未夸大为科学收敛。
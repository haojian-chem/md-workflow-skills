---
name: md_simulation_workflow
description: 为一个 Focus Workstream 规划并推进 MD 模拟阶段。该 Workflow 从 VALIDATED SYSTEM 和明确模拟协议生成可修订的 simulation plan，为每个 run unit 准备并验证 MD_INPUT，再管理执行、按需状态检查、输出核验和阶段完成 gate。它不执行子 Skill、不轮询外部任务，也不修改项目状态或业务文件。
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

阶段内先形成明确且可修订的 `md_simulation_plan`，再对每个 run unit 依次经历：

```text
prepare_and_validate_input
→ execute_or_submit
→ wait_or_status_check
→ output_validation
```

本 Workflow 不把阶段写死为固定的 `EM → NVT → NPT → production` 队列。EM、任意平衡片段、生产片段和显式续跑片段都表示为独立 run unit。

这样支持：

- 只生成计划或只准备一个 run unit 的输入；
- 只执行一个 EM、平衡或生产片段；
- 从指定 run unit/substep 开始或停止；
- `md.1 → md.2 → md.3` 等分段 production；
- 从有效 checkpoint 继续同一 run unit；
- 新增 run unit 后动态修订 plan 和 route；
- 其他 Workstream 的外部任务继续后台运行时切换 Focus。

# 权威阶段边界

当前权威 `stage_registry.yaml` 规定：

```text
md_preparation_workflow
→ 完整体系生成
→ VALIDATED SYSTEM

md_simulation_workflow
→ MDP 与运行输入准备
→ EM / equilibration / production / continuation
→ VALIDATED MDOUTPUT
```

因此：

- 本 Workflow 的标准入口是 VALIDATED SYSTEM，不是预先生成的 MD_INPUT；
- `.mdp`、`grompp`、`.tpr` 和 run plan 属于本 Workflow；
- 只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子需要改变时，才返回 `md_preparation_workflow`。

计划归属与 route 区别见：

```text
references/simulation_plan_ownership.md
```

run unit 语义见：

```text
references/run_unit_model.md
```

# 共同输入

Manager 必须提供：

- `workstream_id`；
- 符合 `workstream_state.schema.yaml` 的 Focus Workstream state；
- 当前 active route 与已解析的本阶段起点、终点和停止条件；
- 当前有效 SYSTEM、MD_INPUT 和 MD_OUTPUT artifact sets；
- 当前 simulation plan 和 plan validation evidence，如已存在；
- submission records 及最新状态；
- 已解决 decision 摘要；
- 当前 Skill 可用性；
- 项目根与 `04_md_simulation/` 业务目录。

规划接口还必须提供：

- 本 Workflow 内的起点与终点；
- protocol spec 或足以判断其仍缺哪些明确决定的上下文；
- 请求范围内的 run unit IDs，或足以唯一解析范围的已验证 plan；
- 用户明确的科学协议、MDP、backend、资源、续跑和停止约束，如已确定。

执行接口还必须提供：

- 当前预计 plan/run unit/lifecycle position；
- 对应 task/result、artifact、submission 和 Validator evidence；
- 外部任务是否运行、结束未核验或状态未知。

缺少 Workstream ID 或路线范围时返回 BLOCKED。缺少科学协议决定时返回 PAUSE 和 confirmation items，不得默认生成“标准模拟流程”。

# 职责边界

负责：

- 定义 simulation plan、run unit 和局部生命周期；
- 为请求范围生成本阶段 route fragment；
- 判断 plan materialization/validation 是否需要执行；
- 为每个 run unit声明 input preparation/validation、execution、status check 和 output validation；
- 根据有效 artifact 和 gate 选择一个当前 task unit；
- 根据 backend/submission 状态判断 status check 是否适用；
- 在外部任务运行时返回 PAUSE，而不是轮询；
- 判断当前 substep、run unit、请求范围或 Workflow 是否完成；
- 返回 route revision signal。

不得：

- 自行创建 protocol spec、plan、`.mdp`、`.tpr`、topology、structure 或 checkpoint；
- 执行 `grompp`、`mdrun`、tmux 或调度命令；
- 根据常见做法补充 EM/NVT/NPT/production 步骤或参数；
- 在缺少明确策略时猜测 checkpoint、`-append`、`-noappend`、`maxwarn` 或完成阈值；
- 高频轮询外部任务；
- 把 session/job 消失直接判定为成功或失败；
- 修改 state、records、route、plan、submission 或 artifact；
- 拼接其他 Workflow；
- 直接向用户提问；
- 创建或管理子 Agent；
- 把技术输出通过表述为科学平衡、收敛或分析结论成立。

# Simulation plan

Workflow 本地 schemas：

```text
schemas/md_simulation_protocol_spec.schema.yaml
schemas/md_simulation_plan.schema.yaml
```

plan 描述：

- run unit 列表、角色和依赖；
- MDP identities；
- SYSTEM 或 prior-run start-state 来源；
- grompp 设置；
- execution policy 中已解决或明确 UNRESOLVED 的字段；
- expected outputs 和 completion criteria；
- resolved decisions、unresolved items 和 revision lineage。

plan 与 Workstream route 分离：

- plan 是本阶段科学运行方案；
- route 是 Manager 根据 Workflow fragment 生成的 task 路线；
- plan 变化产生新 immutable 版本并触发 route revision；
- plan 不直接授权执行。

# Run unit 模型

每个 run unit 至少有：

- 稳定 `run_unit_id`；
- role：`ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CONTINUATION | CUSTOM`；
- work directory；
- explicit dependencies；
- MDP identity；
- SYSTEM 或 prior-run start-state；
- input preparation requirements；
- execution policy；
- expected outputs 和 completion criteria。

名称如 `em.1`、`npt.1`、`md.1` 只用于身份，不推导参数。

# 阶段目录

```text
04_md_simulation/
├── 00_plan/
│   ├── simulation_protocol_spec.yaml
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

目录和文件存在均不是完成证据。

# 动态 Substep registry

## 0. materialize_and_validate_simulation_plan

目标：从结构化 protocol spec 生成并独立验证一个 immutable simulation plan。

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_simulation_plan_materialization
validator: md_simulation_plan_validator
work_directory: 04_md_simulation/00_plan
necessity: REQUIRED at Workflow entry; CONDITIONAL when an equivalent validated plan already exists
```

前置 gate：

- VALIDATED SYSTEM 可用；
- protocol spec 可定位；
- 所有 PLAN_VALIDATION 类科学决定已解决；
- MDP identities 可定位；
- plan 输出路径不覆盖旧版本。

若路线明确从已有 plan 后的 substep 开始，且 plan 仍有效，可 SKIP。

完成证据：plan Validator 建议接受 plan。该步骤不创建 MD_INPUT artifact。

## 对每个 run unit 展开以下步骤

### 1. prepare_and_validate_run_input:<run_unit_id>

目标：从 validated plan 和 SYSTEM/prior MD_OUTPUT 生成并验证 MD_INPUT。

```text
mode: OPERATION_WITH_VALIDATOR
operation: md_run_input_preparation
validator: md_run_input_validator
work_directory: 04_md_simulation/<run_unit_id>/input
necessity: REQUIRED
```

前置 gate：

- validated plan 可用且未失效；
- run unit 唯一；
- INPUT_PREPARATION 类 blocking unresolved items 为空；
- start-state source 为 VALIDATED SYSTEM 或上游 VALIDATED MD_OUTPUT；
- MDP、topology、coordinates 和可选 checkpoint 唯一；
- grompp capability 可用；
- 输出无冲突。

完成证据：MD_INPUT candidate 经 `md_run_input_validator` 通过，并由 Manager 登记为 VALIDATED。

已有等价且仍有效的 VALIDATED MD_INPUT 时可 SKIP。

### 2. execute_run_unit:<run_unit_id>

目标：同步执行或异步提交一个明确 run unit。

```text
mode: OPERATION
operation: md_run_execution
validator: null
work_directory: 04_md_simulation/<run_unit_id>
necessity: REQUIRED
```

前置 gate：

- validated plan 和目标 run unit 可用；
- 当前 run unit 的 MD_INPUT 为 VALIDATED；
- 所有 blocking dependencies 的 MD_OUTPUT 已通过；
- EXECUTION 类 blocking unresolved items 为空；
- continuation checkpoint 和 append policy 明确；
- backend、资源和 execution spec 可用；
- 工作目录/输出冲突已解决；
- 首个外部长任务提交前所需 FULL runtime validation 已通过。

完成证据：同步进程结束，或外部提交被接受并产生可记录 submission evidence。提交成功不等于模拟完成。

### 3. check_run_unit_status:<run_unit_id>

目标：按需检查异步 submission 当前状态。

```text
mode: VALIDATOR
operation: null
validator: md_run_status_validator
work_directory: 04_md_simulation/<run_unit_id>
necessity: CONDITIONAL
condition: asynchronous submission is SUBMITTED/RUNNING/UNKNOWN and a refresh is currently required
```

使用 ON_DEMAND 策略。任务仍运行且当前无需刷新时 Workflow 返回 PAUSE。同步执行或已有可信 terminal status 时 SKIP。

### 4. validate_run_unit_output:<run_unit_id>

目标：核验已结束 run unit 是否满足显式技术完成条件。

```text
mode: VALIDATOR
operation: null
validator: md_run_output_validator
work_directory: 04_md_simulation/<run_unit_id>
necessity: REQUIRED
```

前置 gate：

- 同步进程结束，或异步 submission 为 FINISHED_UNVERIFIED；
- validated MD_INPUT、execution spec、command record 和 provenance 可用；
- expected outputs 已停止写入；
- 不存在同一 run unit 的活动进程。

完成证据：Validator 建议接受 MD_OUTPUT candidate。

## 5. workflow_completion_validation

目标：核验请求范围内 plan、MD_INPUT、run units、submission 和 MDOUTPUT 谱系闭合。

```text
mode: VALIDATOR
operation: null
validator: md_simulation_completion_validator
work_directory: 04_md_simulation/99_validation
necessity: REQUIRED for Workflow exit
```

若用户终点只是 plan、input preparation、execution、status 或单个 output validation，则 route 可以在对应 substep 结束，不强制阶段 completion Validator。

# 规划接口：route fragment

Manager 请求规划时，本 Workflow：

1. 核验起点、终点和停止条件；
2. 判断是否需要 plan materialization/validation；
3. 若已有 validated plan，按 plan 解析 run unit 范围和 DAG；
4. 若尚无 plan，只规划到 plan gate；不得虚构后续 run units；
5. 对每个已解析 run unit 展开 input preparation、execution、conditional status check 和 output validation；
6. 保留所有 REQUIRED steps；
7. 无证据时不提前删除 CONDITIONAL status check；
8. 终点为 Workflow exit 时追加 completion validation；
9. 声明入口 SYSTEM/plan/artifact requirements 和出口 MD_OUTPUT；
10. 对缺失 Skill、未解析 protocol、循环依赖、缺失 start-state artifact 或冲突路径形成 blocker；
11. 返回 `workflow_route_fragment.schema.yaml`。

Fragment 状态：

- `COMPLETE`：请求范围内计划与 run units 可完整表达；
- `PARTIAL`：只能安全规划到 plan gate，或已知部分 run units 后存在未决边界；
- `BLOCKED`：入口 SYSTEM、protocol spec 或当前起点无法安全确定。

标准 Workflow entry requirement 为 VALIDATED SYSTEM。若起点位于已有 run unit 的后续 substep，可以要求对应 validated plan、MD_INPUT、submission 或 MDOUTPUT evidence。

`next_workflow_hint` 为 `analysis_workflow`，要求满足当前范围的 VALIDATED MDOUTPUT。

# 执行接口：当前 decision

## EXECUTE

每次只返回一个 task unit：

- plan 不存在/需修订且 gate 满足：plan materialization + validator；
- run input 未验证且 gate 满足：input preparation + validator；
- input 已验证且未执行：`md_run_execution`；
- 异步任务需要刷新：`md_run_status_validator`；
- 任务结束未核验：`md_run_output_validator`；
- 范围完成且需要 Workflow exit：`md_simulation_completion_validator`。

目标 Skill 不可用时不得返回可执行 task。

## SKIP

仅在可信 evidence 支持时：

- 已有等价 validated plan；
- 已有等价 VALIDATED MDINPUT；
- run unit 已有等价 VALIDATED MDOUTPUT；
- status check 对同步执行不适用；
- submission 已有可信 terminal status；
- 用户范围已达到终点。

不得仅凭目录、文件名或时间戳 SKIP。

## PAUSE

用于：

- protocol spec 的科学决定未解决；
- INPUT_PREPARATION/EXECUTION 类未决项到达其 barrier；
- submission 为 SUBMITTED/RUNNING 且当前无需刷新；
- backend 资源暂不可用；
- 需要用户解决 checkpoint、append、maxwarn、覆盖冲突或范围；
- Validator 返回需要人工判断。

返回 confirmation items 或明确依赖，不返回 task unit。

## BLOCKED

用于：

- SYSTEM 缺失、失效或未验证；
- protocol spec/plan/run unit 不唯一；
- plan DAG 有环或 start-state 引用不一致；
- 当前所需 MDINPUT/MDOUTPUT 缺失或失效；
- task、submission、artifact 或 Workstream state 矛盾；
- 工作目录存在无法解释的活动进程/输出冲突；
- continuation 缺少 checkpoint/append policy；
- 必要 Skill/backend capability 缺失；
- 需要恢复未闭环 task。

## COMPLETE

仅当请求范围终点达到。终点为 Workflow exit 时还必须满足：

- validated plan 覆盖该范围；
- required run units 的 MDINPUT 和 MDOUTPUT 谱系闭合；
- 不存在 active、UNKNOWN 或 FINISHED_UNVERIFIED submission；
- completion Validator 通过；
- 最终 MDOUTPUT 已由 Manager 登记为 VALIDATED。

# 外部任务状态

submission 状态使用共享 contract：

```text
SUBMITTED | RUNNING
→ on-demand status check
→ FINISHED_UNVERIFIED
→ output validation
→ COMPLETED | FAILED
```

- backend 报告结束后先进入 FINISHED_UNVERIFIED；
- 只有 output Validator 通过后 Manager 才可标记 COMPLETED；
- job/session 不存在但证据不足时使用 UNKNOWN 或 FINISHED_UNVERIFIED；
- Workflow 不循环等待。

# 续跑、修订与分支

- 相同 `.tpr` + 明确 checkpoint 的正常 continuation 可使用新的 execution spec 留在当前 run unit；
- 改变 `.mdp`、`nsteps`、科学参数、起始 artifact 或 `.tpr` 时必须修订 plan 或重新准备 MDINPUT；
- 仅 backend/资源变化且 `.tpr` 不变时，不必修订科学 plan，可生成新 execution spec；
- 已有有效下游结果时不覆盖，创建新 run unit/plan version 或新 Workstream；
- 只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子改变时才返回 `md_preparation_workflow`。

# Route revision signals

- protocol spec 或 plan version 变化；
- run unit 列表、顺序、终点或依赖变化；
- 新增 continuation/production segment；
- MDP/start-state/completion criteria 变化；
- MDINPUT 被 INVALIDATED/SUPERSEDED；
- execution spec/backend/resource strategy 变化；
- output Validator 要求新 MDINPUT 或新 SYSTEM；
- checkpoint/MDOUTPUT 被 INVALIDATED/SUPERSEDED；
- submission 失败/取消/未知后采用替代方案；
- 用户创建对照、重复或参数分支；
- Skill 可用性变化。

Workflow 只返回修订理由和 fragment，不写 route/plan。

# 阶段出口

阶段出口为 VALIDATED MDOUTPUT artifact set，至少包含当前范围所需的：

- 最终结构或 checkpoint；
- required 轨迹、能量和日志；
- validated plan 和 MDINPUT provenance；
- run input/output validation reports；
- command、submission 和 continuation provenance；
- completion report，如终点为 Workflow exit。

该出口只说明技术 gate 已通过，不证明采样充分或科学收敛。

# 返回

规划时返回：

```text
03_contracts/workflow_route_fragment.schema.yaml
```

执行时返回：

```text
03_contracts/workflow_decision.schema.yaml
```

不返回 subagent result，不直接更新 state/records。

# 自检

- [ ] 标准入口为 VALIDATED SYSTEM；
- [ ] MDP/grompp/tpr/run plan 未错误归入 md_preparation；
- [ ] 未把模拟协议固定为 EM/NVT/NPT/production；
- [ ] plan 与 Workstream route 已区分；
- [ ] plan 可修订且旧版本不覆盖；
- [ ] 每个 run unit 的 input、execution、status、output validation 已分离；
- [ ] 外部任务没有轮询循环；
- [ ] FINISHED_UNVERIFIED 后才进入输出核验；
- [ ] 提交成功未表述为模拟完成；
- [ ] checkpoint/append/maxwarn 未隐式选择；
- [ ] 已有结果只凭可信 artifact/Validator evidence 跳过；
- [ ] 每次 execution decision 只有一个 task unit；
- [ ] 未执行或模拟子 Skill；
- [ ] Workflow exit 要求 VALIDATED MDOUTPUT；
- [ ] 技术完成未夸大为科学收敛。
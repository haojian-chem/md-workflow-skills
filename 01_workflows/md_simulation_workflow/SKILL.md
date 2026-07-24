---
name: md_simulation_workflow
description: 为一个 Focus Workstream 规划并推进 MD 模拟阶段。该 Workflow 将能独立提交、运行和核验的 EM、平衡、生产或续跑片段统一建模为 run unit，按 run unit 生成动态 route fragment，并根据外部 submission、技术输出验证和阶段完成证据返回一个当前 decision。该 Skill 不执行模拟、不轮询外部任务、不创建子 Agent，也不修改项目状态或业务文件。
---

# 目标

将一个 Workstream 从已经准备好的 VALIDATED MD_INPUT 推进到经过技术核验、可供 `analysis_workflow` 使用的 MD_OUTPUT artifact set。

本 Workflow 不把阶段写死为固定的 `EM → NVT → NPT → production` 队列。EM、任意平衡片段、生产模拟片段和显式续跑片段都表示为独立 `run unit`，每个 run unit 按依赖关系依次经历：

```text
execute_or_submit
→ wait_or_status_check
→ output_validation
```

这样可以支持：

- 只执行一个 EM、平衡或生产片段；
- 从指定 run unit 开始或在指定 run unit 后停止；
- `md.1 → md.2 → md.3` 等分段生产模拟；
- 从有效 checkpoint 继续同一 run unit；
- 不同项目采用不同数量和类型的平衡片段；
- 其他 Workstream 的外部任务继续后台运行时切换 Focus。

# 共同输入

Manager 必须提供：

- `workstream_id`；
- 符合 `workstream_state.schema.yaml` 的 Focus Workstream state；
- 当前 active route 与已解析的本阶段起点、终点和停止条件；
- 当前有效 MD_INPUT、MD_OUTPUT artifact sets；
- 当前 submission records 及其最新状态；
- 已解决 decision 摘要；
- 已知 run unit 列表、依赖关系、角色和工作目录；
- 当前 Skill 可用性；
- 项目根与 `04_md_simulation/` 业务目录。

规划接口还必须提供：

- 本 Workflow 内的起点与终点；
- 请求范围内的 run unit IDs，或足以唯一解析它们的已解决范围；
- 每个 run unit 的 MD_INPUT 来源和前置依赖；
- 用户明确的后端、资源、续跑和停止约束，如已确定。

执行接口还必须提供：

- 当前预计 run unit 和 lifecycle position；
- 对应 task/result、submission、artifact 和 Validator evidence；
- 外部任务是否正在运行、已结束但未核验，或状态未知。

缺少 Workstream ID、路线范围或目标 run unit 时返回 BLOCKED 或 PAUSE，不得默认执行完整模拟阶段。

# 职责边界

负责：

- 定义 MD 模拟阶段的 run unit 模型和局部生命周期；
- 为请求范围动态生成本阶段 route fragment；
- 为每个 run unit 声明执行、状态检查和输出验证步骤；
- 根据 backend 和 submission 状态判断状态检查步骤是否适用；
- 根据依赖 gate 选择一个当前 task unit；
- 在外部任务运行时返回 PAUSE，而不是启动轮询循环；
- 在外部任务状态需要刷新时选择状态 Validator；
- 在 submission 进入 `FINISHED_UNVERIFIED` 后选择输出 Validator；
- 判断当前 run unit、请求范围或整个 Workflow 是否完成；
- 发出 route revision signal。

不得：

- 自行生成或修改 `.tpr`、`.mdp`、topology、structure 或 checkpoint；
- 执行 `gmx mdrun`、tmux 或调度系统命令；
- 高频轮询外部任务；
- 把 tmux session 或调度 job 消失直接判定为模拟成功或失败；
- 根据“常见 MD 做法”补充未指定的 EM/NVT/NPT/production 步骤；
- 在缺少显式续跑策略时猜测 `-append`、`-noappend` 或 checkpoint；
- 修改 submission record、artifact set、route record 或 Workstream state；
- 拼接其他 Workflow；
- 直接向用户提问；
- 创建或管理子 Agent；
- 把技术输出通过表述为体系已经达到科学平衡或分析结论成立。

# Run unit 模型

阶段内最小可提交和可独立核验的对象称为 `run unit`。详细语义见：

```text
references/run_unit_model.md
```

每个 run unit 至少必须有：

- 稳定 `run_unit_id`；
- `role`：`ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CONTINUATION | CUSTOM`；
- 明确工作目录；
- 一个或多个 VALIDATED MD_INPUT 来源；
- 显式前置 run unit IDs；
- 预期输出和完成条件；
- 是否需要异步 submission；
- 对应 execution spec 的来源或待解决状态。

run unit 名称可以使用项目习惯，例如：

```text
em.1
nvt.1
npt.1
md.1
md.2
```

这些名称不是固定协议，也不自动决定运行参数。

# 阶段目录

```text
04_md_simulation/
├── <run_unit_id>/
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

具体 GROMACS 输出文件名由 execution spec 明确。目录存在、日志存在或 checkpoint 存在均不是完成证据。

# 动态 Substep registry

本 Workflow 不预先写死 run unit 数量。对请求范围内每个 run unit，按依赖顺序展开以下步骤。

## 1. execute_run_unit:<run_unit_id>

目标：同步执行或异步提交一个明确的 run unit。

```text
mode: OPERATION
operation: md_run_execution
validator: null
necessity: REQUIRED
work_directory: 04_md_simulation/<run_unit_id>
```

前置 gate：

- run unit 和 execution spec 已明确；
- 所有前置 run unit 已通过输出验证；
- 必需 MD_INPUT artifact 为 VALIDATED；
- continuation 模式下 checkpoint 和 append policy 已明确；
- 工作目录和输出冲突已解决；
- backend 和资源要求可用；
- 首个外部长任务提交前所需 FULL runtime validation 已通过。

完成证据：Operation 已成功完成本地同步执行，或外部提交已被 backend 接受并返回可记录的 submission evidence。提交成功不等于模拟完成。

## 2. check_run_unit_status:<run_unit_id>

目标：按需检查异步 submission 当前状态。

```text
mode: VALIDATOR
operation: null
validator: md_run_status_validator
necessity: CONDITIONAL
condition: run unit 使用异步 backend，且 submission 状态为 SUBMITTED、RUNNING 或 UNKNOWN，并且当前需要刷新状态
work_directory: 04_md_simulation/<run_unit_id>
```

使用 `ON_DEMAND` 检查策略。外部任务仍在运行时，Workflow 默认返回 PAUSE；只有用户请求、恢复流程、依赖推进需要或已有证据过期时才执行状态检查。

同步本地执行，或已有可信 terminal submission 状态时返回 SKIP。

## 3. validate_run_unit_output:<run_unit_id>

目标：核验一个已经结束的 run unit 是否满足显式技术完成条件。

```text
mode: VALIDATOR
operation: null
validator: md_run_output_validator
necessity: REQUIRED
work_directory: 04_md_simulation/<run_unit_id>
```

前置 gate：

- 同步进程已经结束，或异步 submission 为 `FINISHED_UNVERIFIED`；
- execution spec、command record 和输入 provenance 可用；
- 预期输出已停止写入；
- 不存在仍活动的同一 run unit 进程。

完成证据：Validator 建议接受对应 MD_OUTPUT artifact candidate。仅有正常退出码、终止标记或 checkpoint 不能单独代替完整核验。

## 4. workflow_completion_validation

目标：核验请求范围内所有 required run units、依赖、submission 和 MD_OUTPUT 谱系已经闭合。

```text
mode: VALIDATOR
operation: null
validator: md_simulation_completion_validator
necessity: REQUIRED
work_directory: 04_md_simulation/99_validation
```

若用户终点只是某个 run unit 的执行、状态检查或输出验证，则 route fragment 可以在对应 substep 结束，不强制加入阶段完成 Validator。只有终点为 Workflow exit、Workstream 目标要求完成本阶段，或需要向 analysis 提供阶段出口 artifact 时才加入本步骤。

# 规划接口：route fragment

Manager 请求规划时，本 Workflow：

1. 核验起点、终点和 run unit 范围是否唯一；
2. 按依赖关系对范围内 run units 排序；
3. 对每个 run unit 展开 execution、conditional status check 和 output validation；
4. 已有仍有效结果时保留步骤但声明可在执行接口 SKIP；
5. 没有证据时不提前删除异步 status check；
6. 终点为 Workflow exit 时追加 completion validation；
7. 声明入口 MD_INPUT、前置 MD_OUTPUT 和 submission requirements；
8. 声明出口 MD_OUTPUT artifact；
9. 对缺失 Skill、未解析 run unit、循环依赖、缺失 MD_INPUT 或冲突工作目录形成 blocker；
10. 返回 `workflow_route_fragment.schema.yaml`。

Fragment 状态：

- `COMPLETE`：范围内 run unit、依赖和 Skill 均可表达；
- `PARTIAL`：可表达已知 run units，但后续 run unit、execution spec 或边界仍未解析；
- `BLOCKED`：入口 run unit 或必要 MD_INPUT 无法安全确定。

`next_workflow_hint` 为 `analysis_workflow`，要求至少一个满足当前范围要求的 VALIDATED MD_OUTPUT artifact。

# 执行接口：当前 decision

## EXECUTE

每次只返回一个 task unit：

- 未执行且前置 gate 满足：`md_run_execution`；
- 异步任务需要刷新状态：`md_run_status_validator`；
- 任务已结束但未核验：`md_run_output_validator`；
- 所有范围内 run units 均通过且需要 Workflow exit：`md_simulation_completion_validator`。

目标 Skill 不可用时不得返回可执行 task。

## SKIP

仅在有可信证据时：

- run unit 已有等价且仍有效的 VALIDATED MD_OUTPUT；
- status check 对同步执行不适用；
- submission 已有可信 terminal status；
- 用户范围在本步骤之前或已达到指定终点。

不得因目录、文件名或时间戳看似存在而 SKIP。

## PAUSE

用于：

- submission 为 `SUBMITTED | RUNNING`，当前不需要刷新；
- backend 资源暂不可用但可恢复；
- 需要用户解决 backend、资源、续跑、覆盖冲突或 run unit 范围；
- output Validator 返回需要人工判断但执行本身成功。

返回 confirmation items 或明确依赖，不返回 task unit。

## BLOCKED

用于：

- run unit 或依赖关系不唯一；
- 依赖形成循环；
- 前置 MD_INPUT 缺失、失效或未验证；
- submission、task、artifact 或 Workstream state 相互矛盾；
- 同一工作目录存在无法解释的活动进程或输出冲突；
- continuation 缺少有效 checkpoint 或 append policy；
- 必要 Skill 或 backend capability 缺失；
- 需要恢复未闭环 task。

## COMPLETE

仅当请求范围终点已达到。若终点为 Workflow exit，还必须满足：

- 请求范围内所有 required run units 的输出均已通过；
- 不存在属于该范围的 active、UNKNOWN 或 FINISHED_UNVERIFIED submission；
- completion Validator 通过；
- 最终 MD_OUTPUT artifact 已由 Manager 登记为 VALIDATED。

# 外部任务状态处理

submission 状态使用 `03_contracts/submission_record.schema.yaml`，不得在本 Skill 重新定义。

关键转换：

```text
SUBMITTED | RUNNING
→ 按需状态检查
→ FINISHED_UNVERIFIED
→ output validation
→ COMPLETED | FAILED
```

- backend 报告任务结束后先进入 `FINISHED_UNVERIFIED`；
- 只有输出 Validator 通过后，Manager 才可标记 `COMPLETED`；
- session/job 不存在但证据不足时使用 `UNKNOWN` 或 `FINISHED_UNVERIFIED`，不得自动写 FAILED；
- Workflow 不循环等待，也不高频检查。

# 续跑与分支

- 同一 `.tpr` 和明确 checkpoint 的正常 continuation 可以作为当前 run unit 的显式执行模式；
- 延长 `nsteps`、修改参数、替换 `.tpr` 或改变科学方案时，必须形成新的 MD_INPUT 和新的 run unit；
- 已有有效下游结果时，不覆盖原 run unit；应创建新 Workstream 或新的 run unit 分支；
- output Validator 发现需要重跑、续跑或调整参数时，返回 route revision signal，不自行修改输入；
- 失败修复若需要重新生成 MD_INPUT，应回到 `md_preparation_workflow` 或创建明确的新路线。

# Route revision signals

以下情况使 active route 可能过期：

- run unit 列表、顺序、终点或依赖变化；
- 新增 continuation 或 production segment；
- execution spec、backend 或资源策略变化；
- output Validator 判定需要新 MD_INPUT；
- checkpoint 或 MD_OUTPUT 被 INVALIDATED/SUPERSEDED；
- submission 进入 FAILED、CANCELLED 或 UNKNOWN 且采用替代方案；
- 用户创建对照、重复或参数分支 Workstream；
- Skill 可用性变化。

Workflow 只返回修订理由和新的 fragment，不写 route record。

# 阶段出口

阶段出口为：

```text
VALIDATED MD_OUTPUT artifact set
```

至少包含当前范围所需的：

- 最终结构或 checkpoint；
- 轨迹、能量和日志等声明为 required 的输出；
- run unit output validation reports；
- 输入、command、submission 和 continuation provenance；
- completion validation report，如终点为 Workflow exit。

该出口只说明模拟执行和声明的技术 gate 已通过，不代表分析结论、采样充分性或科学收敛性已经证明。

# 返回

规划时返回：

```text
03_contracts/workflow_route_fragment.schema.yaml
```

执行时返回：

```text
03_contracts/workflow_decision.schema.yaml
```

不返回 subagent result，不直接更新 project/workstream state。

# 自检

- [ ] 未把 MD 模拟协议固定为 EM/NVT/NPT/production；
- [ ] run unit 范围、依赖和终点均来自明确上下文；
- [ ] 每个 run unit 的 execution、status 和 output validation 已分离；
- [ ] 外部任务运行时没有轮询循环；
- [ ] `FINISHED_UNVERIFIED` 后才进入输出核验；
- [ ] 提交成功没有被表述为模拟完成；
- [ ] 续跑没有隐式选择 checkpoint 或 append policy；
- [ ] 已有结果仅凭可信 artifact/Validator evidence 跳过；
- [ ] 每次 execution decision 只包含一个 task unit；
- [ ] 未执行或模拟 Operation/Validator；
- [ ] 未修改状态、记录或业务文件；
- [ ] Workflow exit 要求 VALIDATED MD_OUTPUT；
- [ ] 技术完成没有被夸大为科学收敛。
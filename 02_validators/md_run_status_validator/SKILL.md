---
name: md_run_status_validator
description: 按需检查一个异步 MD run unit 的 LOCAL、TMUX、LSF、SLURM 或 PBS submission 当前状态，并根据 backend、进程和日志证据区分仍在运行、已结束待输出核验、明确失败、取消或状态未知。该 Validator 不轮询、不修改任务、不验证 MD 输出质量。
---

# 目标

为 `md_simulation_workflow` 提供一次性的 submission 状态检查：

- 核验 submission record 与 execution spec 的身份关系；
- 调用明确的 backend status check；
- 读取必要的 process/session/job 和日志证据；
- 返回结构化状态建议；
- 将已经结束但尚未验证的任务区分为 `FINISHED_UNVERIFIED`；
- 不把 backend terminal 状态等同于 MD_OUTPUT 通过。

# 职责边界

负责：

- 检查一个明确 submission；
- 核验 task、Workstream、run unit、backend 和工作目录；
- 执行一次 `ON_DEMAND` 状态查询；
- 读取必要的 execution log、scheduler output 或 GROMACS log 尾部；
- 汇总 backend 原始状态、进程存在性、退出证据和错误标记；
- 输出 status report 和 Validation component result；
- 建议 Manager 更新 submission status。

不负责：

- 循环等待或定时轮询；
- 启动、停止、取消、重提或恢复任务；
- 修改 submission record；
- 修改 engine 输出；
- 判断轨迹、能量、checkpoint 或目标步数是否完整；
- 将 session/job 不存在直接判定为成功；
- 将日志中单个普通 warning 判定为失败；
- 选择下一 run unit；
- 写管理目录；
- 创建子 Agent 或直接向用户提问。

# 输入

必须接收 `subagent_task.schema.yaml` v2 的 `VALIDATOR` task unit：

```text
operation: null
validator: md_run_status_validator
```

任务必须提供：

- 一个符合共享 contract 的 submission record；
- 对应 `md_run_execution_spec.yaml`；
- execution Operation report 和 submission evidence；
- backend status check 所需的 PID、session name 或 job ID；
- 必要日志路径；
- allowed read/write 和 forbidden paths；
- status report 与 result data 路径。

submission 状态必须为：

```text
SUBMITTED | RUNNING | UNKNOWN
```

其他状态只有在恢复核对任务明确要求时才允许检查。

# Preflight

确认：

1. task、Workstream 和 run unit IDs 一致；
2. submission record 的 task ID 对应 execution Operation；
3. backend、working directory 和 command record 一致；
4. PID/session/job ID 满足 backend 要求；
5. status check command 来源明确且不使用自由文本 shell 拼接；
6. execution spec 和 submission evidence hashes 未改变；
7. 目标日志仅以只读方式访问；
8. Validator 输出路径位于 allowed write paths；
9. 管理目录位于 forbidden paths；
10. 本次调用是单次 ON_DEMAND 检查，不包含 sleep/retry loop。

输入不完整时返回 BLOCKED，不猜测 backend 状态。

# 检查规则

## 1. Backend 证据

按 backend 获取一次状态：

- `LOCAL`：检查明确 PID 和退出证据；
- `TMUX`：检查明确 session、pane/process 和日志；
- `LSF`：检查 job ID 的 scheduler 状态；
- `SLURM`：检查 job ID 的 active 和 accounting 状态；
- `PBS`：检查 job ID 的 queue/accounting 状态。

不得仅凭 status command 的空输出得出 terminal 结论。

## 2. 运行中

满足以下任一可信证据时建议 `RUNNING`：

- backend 明确报告 queued/pending/running；
- 明确 PID 仍属于预期命令；
- tmux session 和目标进程均存在；
- scheduler job 仍处于活动状态。

日志暂时没有增长不能单独推翻 backend 活动证据。

## 3. 已结束待核验

当 backend 明确 terminal，或进程已经结束且没有活动证据时：

- 有正常退出或 completion marker evidence：建议 `FINISHED_UNVERIFIED`；
- 没有足够正常/失败证据：建议 `FINISHED_UNVERIFIED` 或 `UNKNOWN`，根据证据强度选择；
- 不检查完整 MD_OUTPUT，不建议 `COMPLETED`。

## 4. 明确失败

只有存在明确证据时建议 `FAILED`：

- scheduler terminal failure state；
- 非零 process exit evidence；
- GROMACS fatal error；
- backend rejection；
- 明确资源或运行时 failure marker。

session/job 消失、日志中断或输出缺失本身不足以单独判 FAILED。

## 5. 取消

只有 backend 或可信记录明确表示取消时建议 `CANCELLED`。

## 6. 状态未知

以下情况返回 `UNKNOWN`：

- job/session/PID 身份无法确认；
- backend 查询不可用且没有 terminal evidence；
- scheduler 历史记录已清理；
- submission evidence 与实际对象冲突；
- 多个同名 session/process 无法唯一定位。

状态未知不得触发自动重提。

# Evidence priority

从高到低：

1. backend 的明确 job/process identity 和 terminal state；
2. 原始退出码或 scheduler accounting；
3. GROMACS fatal/normal termination marker；
4. execution/submission wrapper 的结构化 evidence；
5. 文件时间、大小变化或普通日志文本。

低优先级证据不得覆盖更高优先级的相反事实。

# Outcome codes

- `RUN_STILL_ACTIVE`；
- `RUN_FINISHED_UNVERIFIED`；
- `RUN_FAILED_WITH_EVIDENCE`；
- `RUN_CANCELLED_WITH_EVIDENCE`；
- `RUN_STATUS_UNKNOWN`；
- `SUBMISSION_RECORD_MISMATCH`；
- `STATUS_INPUT_INCOMPLETE`；
- `BACKEND_STATUS_CHECK_UNAVAILABLE`；
- `STATUS_VALIDATOR_INTERNAL_FAILURE`。

# Gate 建议

- `RUN_STILL_ACTIVE`：Workflow PAUSE；
- `RUN_FINISHED_UNVERIFIED`：进入 `md_run_output_validator`；
- `RUN_FAILED_WITH_EVIDENCE`：暂停并进入恢复、重规划或用户决定；
- `RUN_CANCELLED_WITH_EVIDENCE`：暂停并保留取消证据；
- `RUN_STATUS_UNKNOWN`：暂停，禁止自动重提；
- input/record mismatch：BLOCKED，要求恢复。

Validator 成功执行但发现 run failed 时，Validation component 可以 `status: DONE` 并使用失败 outcome code；不得把业务任务失败和 Validator 自身执行失败混为一谈。

# 输出

默认：

```text
04_md_simulation/<run_unit_id>/
├── status_report.yaml
└── status_check.log
```

status report 至少记录：

- task/workstream/run unit/submission IDs；
- checked_at；
- backend identity；
- previous submission status；
- raw backend state；
- process/session/job evidence；
- normal、failure、cancel 和 unknown evidence；
- recommended submission status；
- outcome code；
- warnings。

# 返回

返回符合：

```text
03_contracts/subagent_result.schema.yaml
```

的独立 `validation_result`：

- 不返回 artifact candidate；
- `validated_files` 包含 submission record、execution spec 和必要 evidence；
- `created_files` 包含 status report/log；
- 不修改 submission record；
- 下一步建议只说明等待、输出验证、恢复或人工决定。

# 失败处理

- backend 查询命令本身失败但 Validator 可解释：返回 `BACKEND_STATUS_CHECK_UNAVAILABLE` 或 `RUN_STATUS_UNKNOWN`；
- 输入或身份冲突：BLOCKED；
- Validator 实现异常：FAILED；
- 不重试、不 sleep、不切换 backend；
- 不删除或修改任何运行文件。

# Tool candidate

backend 状态查询和状态映射适合由未来 `external_submission_adapter` Tool 提供确定性实现。该 Tool 未 ACTIVE 前，本 Skill 不能声称所有 backend 已具备生产能力。

# 自检

- [ ] 本次只检查一个 submission；
- [ ] 没有轮询或自动重试；
- [ ] backend identity 唯一；
- [ ] session/job 消失没有被直接判成功或失败；
- [ ] terminal backend 状态先进入 FINISHED_UNVERIFIED；
- [ ] 没有验证 MD_OUTPUT；
- [ ] 没有修改 submission record 或运行文件；
- [ ] 业务 run failure 与 Validator execution failure 已分离；
- [ ] UNKNOWN 不触发自动重提；
- [ ] 没有写管理目录。
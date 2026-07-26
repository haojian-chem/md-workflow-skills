---
name: md_run_status_validator
description: 按需检查一个明确 MD execution attempt 的 LOCAL、TMUX、LSF、SLURM 或 PBS submission 状态，并根据 backend、process 和日志证据区分活动、结束待核验、明确失败、取消或未知。该 Validator 不轮询、不修改 submission，也不验证 run-level MD_OUTPUT。
---

# 目标

对一个 attempt 执行一次状态查询：

```text
validated execution-attempt spec
+ submission record/evidence
→ one ON_DEMAND status check
→ attempt status recommendation
```

terminal attempt 只进入 `FINISHED_UNVERIFIED`，不得直接标记 run unit 完成。

# 职责边界

负责：

- 检查一个唯一 attempt/submission；
- 核验 Workstream、plan、run unit、attempt、execution spec 和 working directory；
- 执行一次 backend status query；
- 读取必要 process/session/job 和 attempt log evidence；
- 输出 status report 和 Manager 状态更新建议。

不得：

- sleep、retry 或循环轮询；
- 启动、停止、取消、重提或 continuation；
- 修改 submission record 或 engine outputs；
- 聚合多个 attempts；
- 判断 run unit target、轨迹或能量是否通过；
- 把 job/session 消失直接判成功或失败；
- 写管理目录。

# 输入

必须接收 VALIDATOR task unit，并提供：

- 一个 submission record；
- 已验证 execution-attempt spec 与 validation report；
- execution Operation report、command 和 submission evidence；
- PID/session/job identity；
- attempt-specific logs；
- allowed read/write 与 forbidden paths；
- status report/result data路径。

submission previous status 通常为：

```text
SUBMITTED | RUNNING | UNKNOWN
```

# Preflight

确认：

1. task/workstream/plan/run-unit/attempt/spec IDs 可唯一对齐；
2. submission task ID、working directory 和 command record 指向当前 attempt；
3. spec/validation/submission evidence hashes 未改变；
4. backend identity 满足类型要求；
5. status command 来源为 validated spec/adapter，不含自由文本 shell；
6. 日志只读；
7. status 输出位于当前 attempt directory；
8. 本次调用只执行一次查询。

输入不完整时 BLOCKED，不猜测状态。

# 检查规则

## Backend evidence

- LOCAL：明确 PID 和 terminal/exit evidence；
- TMUX：明确 session、pane/process 和日志；
- LSF/SLURM/PBS：job ID 的 active/accounting state。

空查询结果不是 terminal 证据。

## Active

backend 明确 queued/pending/running、目标 PID 活动或 tmux target process 存在时，建议 `RUNNING`。

## Terminal unverified

backend/process terminal 后：

- 有正常 terminal evidence：`FINISHED_UNVERIFIED`；
- 证据不足且无活动 evidence：根据强度选择 `FINISHED_UNVERIFIED` 或 `UNKNOWN`；
- 不检查完整输出，不建议 `COMPLETED`。

## Failed/cancelled

只有明确 scheduler failure、nonzero exit、GROMACS fatal、backend rejection 或明确 cancellation evidence 时建议 FAILED/CANCELLED。

## Unknown

identity 冲突、backend history 缺失、status capability 不可用或多个同名对象无法区分时返回 UNKNOWN，禁止自动重提。

# Evidence priority

1. backend/job/process identity 和 terminal state；
2. exit code/accounting；
3. GROMACS fatal/normal marker；
4. structured wrapper evidence；
5. timestamps、size 和普通日志文本。

低优先级证据不得覆盖高优先级相反事实。

# Outcome codes

- `ATTEMPT_STILL_ACTIVE`；
- `ATTEMPT_FINISHED_UNVERIFIED`；
- `ATTEMPT_FAILED_WITH_EVIDENCE`；
- `ATTEMPT_CANCELLED_WITH_EVIDENCE`；
- `ATTEMPT_STATUS_UNKNOWN`；
- `ATTEMPT_SUBMISSION_RECORD_MISMATCH`；
- `ATTEMPT_STATUS_INPUT_INCOMPLETE`；
- `ATTEMPT_BACKEND_STATUS_CHECK_UNAVAILABLE`；
- `ATTEMPT_STATUS_VALIDATOR_INTERNAL_FAILURE`。

# Gate 建议

- active：Workflow PAUSE；
- finished unverified：进入 run output validation或等待后续 continuation decision；
- failed/cancelled：暂停并创建 retry/recovery/route decision；
- unknown：暂停并禁止自动重提；
- identity mismatch：BLOCKED recovery。

# 输出

```text
04_md_simulation/<run_unit_id>/attempts/<attempt_id>/
├── status_report.yaml
└── status_check.log
```

status report 必须记录 task/workstream/plan/run-unit/attempt/spec/submission IDs、checked_at、backend identity、previous/recommended status 和 raw evidence。

# 返回

返回共享 `subagent_result` 的独立 validation_result：

- artifact candidates 为空；
- validated files 包含 execution spec/submission/evidence；
- created files 包含 attempt status report/log；
- 不修改 submission record。

# 自检

- [ ] 只检查一个 attempt/submission；
- [ ] attempt/spec identity 唯一；
- [ ] 没有轮询或重试；
- [ ] terminal 未直接标记 run complete；
- [ ] UNKNOWN 未触发自动重提；
- [ ] 没有聚合或验证 run-level output；
- [ ] 没有修改 submission/engine files/管理目录。
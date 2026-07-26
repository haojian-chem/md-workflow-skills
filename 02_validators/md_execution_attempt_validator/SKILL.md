---
name: md_execution_attempt_validator
description: 独立核验 execution-attempt spec 与 validated MD_INPUT、run unit、resolved execution decisions/profile、parent attempt 和 continuation checkpoint 是否一致，并确认该 attempt 可以安全交给 md_run_execution。该 Validator 不执行或提交任务，也不修改 spec。
---

# 目标

验证一个 execution-attempt spec 是否形成唯一、可恢复、无隐式运行选择的执行授权候选。

通过只表示 spec 可安全交给 `md_run_execution`，不表示 backend 可用、任务已提交或模拟输出通过。

# 职责边界

负责：

- 独立读取 spec、protocol/plan、MD_INPUT、decision/profile 和 prior attempt evidence；
- 重算 attempt identity、kind、parent/checkpoint、backend/resource 和路径约束；
- 检查 prepared submission identity；
- 检查 argv、shell、overwrite 和 APPEND policy；
- 写 validation report 并返回 gate 建议。

不得：

- 修改 spec、MD_INPUT、checkpoint 或 prior attempt；
- 运行或提交 `mdrun`；
- 自动选择 backend、GPU、queue、checkpoint 或 retry policy；
- 启用 APPEND；
- 写管理目录；
- 自动重试 specification Operation。

# 输入

作为 `OPERATION_WITH_VALIDATOR` 的 validator 部分，接收：

- 同一 task 的 specification Operation result；
- execution-attempt spec candidate；
- validated protocol/plan 和 run unit；
- VALIDATED MD_INPUT/input manifest/TPR；
- source decisions/profiles；
- prior attempt/spec/checkpoint，如适用；
- prepared submission identity evidence；
- allowed read/write 与 forbidden paths；
- report/result data 路径。

本地 report schema：

```text
schemas/md_execution_attempt_validation_report.schema.yaml
```

# Preflight

确认：

1. task mode 和 Skill refs 正确；
2. Operation status 为 DONE；
3. spec schema 有效；
4. task/workstream/plan/run-unit IDs 一致；
5. MD_INPUT 为 VALIDATED 且未失效；
6. spec、input、prior attempt 和 checkpoint hashes 一致；
7. report 输出路径受授权；
8. 被验证对象只读；
9. 管理目录禁止写入。

# 独立检查

## 1. Identity

- execution spec ID 非空且未复用；
- attempt ID 在 run unit 内唯一；
- attempt directory 与 ID 对齐；
- task ID 未被当作 spec/attempt identity；
- plan/protocol/run-unit identities 可追溯。

## 2. Attempt kind

### FRESH

- parent attempt 为 null；
- continuation checkpoint 为 null。

### RETRY_SAME_INPUT

- parent attempt 存在；
- TPR 与 parent 相同；
- continuation checkpoint 为 null；
- prior attempt 被保留且 replacement reason 可追溯。

### CONTINUE_NOAPPEND

- parent attempt 存在；
- TPR 与 parent 相同；
- checkpoint 非空、可读且属于 parent accepted chain；
- 新 attempt directory 与 parent 不同；
- append policy 为 false。

## 3. Runtime provenance

核验 backend、host、session/script、resources、GROMACS executable constraint 和 extra argv 均来自明确 decision/profile。

- 不允许隐式 GPU/queue/resource；
- 不允许自由文本 shell；
- scheduler script 必须有 file identity；
- TMUX session 必须唯一；
- expected outputs 必须位于 attempt directory。

## 4. Recovery anchor

异步 attempt 必须有 prepared submission identity。同步 attempt 必须为 null。

若 prior task 可能已提交但身份不完整，不得通过新 attempt spec；先进入恢复/status check。

## 5. Mutation policy

v1 必须满足：

```yaml
preserve_previous_attempts: true
allow_overwrite_existing_attempt: false
append_existing_engine_outputs: false
submit_once: true
```

# Outcome codes

- `EXECUTION_ATTEMPT_VALIDATED`；
- `EXECUTION_ATTEMPT_VALIDATED_WITH_WARNINGS`；
- `EXECUTION_ATTEMPT_VALIDATOR_INPUT_INCOMPLETE`；
- `EXECUTION_ATTEMPT_IDENTITY_MISMATCH`；
- `EXECUTION_ATTEMPT_KIND_MISMATCH`；
- `EXECUTION_ATTEMPT_PARENT_INVALID`；
- `EXECUTION_ATTEMPT_CHECKPOINT_INVALID`；
- `EXECUTION_ATTEMPT_RUNTIME_PROVENANCE_INVALID`；
- `EXECUTION_ATTEMPT_PREPARED_SUBMISSION_MISSING`；
- `EXECUTION_ATTEMPT_PATH_OR_MUTATION_INVALID`；
- `EXECUTION_ATTEMPT_COMMAND_POLICY_INVALID`；
- `EXECUTION_ATTEMPT_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可建议执行。

# 输出

```text
04_md_simulation/<run_unit_id>/attempts/<attempt_id>/
├── md_execution_attempt_validation_report.yaml
└── execution_attempt_validation.log
```

不返回 MD artifact candidate。

# 自检

- [ ] attempt/spec/task identities 已分离；
- [ ] MD_INPUT 与 TPR identity 已核验；
- [ ] attempt kind 条件独立重算；
- [ ] continuation checkpoint 属于 parent chain；
- [ ] backend/resource 均有 provenance；
- [ ] 异步 attempt 有 prepared submission identity；
- [ ] v1 未启用 APPEND；
- [ ] 输出路径与 prior attempts 隔离；
- [ ] 未执行或提交任务；
- [ ] 未修改被验证对象或管理目录。
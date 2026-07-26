---
name: md_run_execution
description: 严格执行一个已经通过 md_execution_attempt_validator 的 GROMACS execution attempt；同步运行短任务或向 LOCAL、TMUX、LSF、SLURM、PBS backend 异步提交一次，并记录 attempt-specific command、submission 和恢复证据。该 Operation 不生成 execution spec、不轮询任务，也不验证 run-level MD_OUTPUT。
---

# 目标

执行一个明确 attempt：

```text
validated execution-attempt spec
+ VALIDATED MD_INPUT
→ execute or submit exactly once
→ attempt-specific evidence
→ status/output validation
```

# 职责边界

负责：

- 读取已验证的 `md_execution_attempt_spec.yaml`；
- 核验 Workstream、plan、run unit、attempt 和 MD_INPUT identities；
- 核验 prepared submission identity，如为异步；
- 以结构化 argv 构建一次 `gmx mdrun`；
- 同步运行或异步提交一个 attempt；
- 捕获 process/PID/session/job identity 和 backend 原始证据；
- 写 command、operation report、submission evidence 和 execution log；
- 返回 Operation result。

不得：

- 创建、修改或补全 execution-attempt spec；
- 修改 TPR、MDP、checkpoint 或其他 MD_INPUT；
- 选择 backend、资源、GPU、queue 或 checkpoint；
- 自动改变 attempt kind；
- 启用 APPEND 或写入 prior attempt directory；
- 高频轮询；
- 判断 run unit output 是否通过；
- 创建 submission/artifact records；
- 覆盖旧 attempt；
- 写管理目录。

# 输入

必须接收 `OPERATION` task unit：

```text
operation: md_run_execution
validator: null
```

任务必须提供：

- 已通过 `md_execution_attempt_validator` 的 execution-attempt spec；
- 对应 validation report/result；
- VALIDATED MD_INPUT artifact/input manifest/TPR；
- continuation checkpoint，如适用；
- allowed read/write 与 forbidden paths；
- attempt-specific command/report/submission/log 路径。

权威 spec schema：

```text
02_operations/md_execution_attempt_specification/schemas/md_execution_attempt_spec.schema.yaml
```

# 读写权限

只允许写：

```text
04_md_simulation/<run_unit_id>/attempts/<attempt_id>/**
```

只读：validated spec、MD_INPUT、明确 continuation checkpoint、backend executable/script/profile 和必要环境信息。

禁止写 prior attempt、run input、其他 run unit、管理目录或未授权远程位置。

# Preflight

必须确认：

1. execution-attempt Validator outcome 可接受；
2. task/workstream/plan/run-unit/attempt/spec IDs 一致；
3. spec、input manifest、TPR 和 checkpoint hashes 未改变；
4. attempt directory 与 spec 一致且没有冲突；
5. `FRESH | RETRY_SAME_INPUT | CONTINUE_NOAPPEND` 条件满足；
6. `append_existing_engine_outputs: false`；
7. backend/runtime/resources 与 validated spec 一致；
8. 异步 attempt 的 prepared submission identity 存在；
9. 不存在同一 attempt 的活动进程、submission 或未闭环 task；
10. command 使用结构化 argv，无 shell control operator；
11. expected attempt outputs 位于当前 attempt directory；
12. GROMACS executable 满足 version constraint，并记录实际版本；
13. 首个外部长任务所需 FULL runtime validation evidence 已提供。

任一 blocking preflight 失败时返回 BLOCKED，不产生 side effect。

# 命令构建

命令只从 validated attempt spec 构建：

- GROMACS executable；
- `mdrun`；
- 明确 TPR；
- 当前 attempt directory/deffnm；
- `CONTINUE_NOAPPEND` 时明确 checkpoint；
- spec 中明确的并行/GPU参数；
- spec 中经过校验的 extra argv。

不得执行 `eval`、未审查的 `bash -c` 或自由文本 shell 拼接。

v1 不构建 `-append`。continuation 输出写入新的 attempt directory。

# Backend

v1 contract 支持：

```text
LOCAL
TMUX
LSF
SLURM
PBS
```

实际生产能力取决于 ACTIVE adapter 或经权威测试的内建路径。

- LOCAL + SYNCHRONOUS：等待当前 process terminal；
- LOCAL + ASYNCHRONOUS：返回唯一 PID 和日志；
- TMUX：返回唯一 session/pane/process evidence；
- scheduler：提交带 hash 的 script 并返回 job ID；
- 无法解析唯一 identity 时不得视为提交成功。

# 执行流程

1. 解析 task、权限、validated spec 和 validation evidence；
2. 执行完整 preflight；
3. 建立 attempt-specific临时记录；
4. 记录输入 hashes、runtime profile 和实际 GROMACS version；
5. 构建最终 argv/submission；
6. 执行或提交一次；
7. 捕获 exit/PID/session/job/backend evidence；
8. 写 command/report/submission/log；
9. 重新读取本 Operation 生成的结构化文件并做最小 parse/hash 检查；
10. 原子提交业务记录；
11. 返回 Operation result。

# 同步结果

process terminal 后：

- exit 0：`ATTEMPT_PROCESS_FINISHED_UNVERIFIED`；
- nonzero 且有明确 failure evidence：`ATTEMPT_PROCESS_EXITED_NONZERO`；
- 不创建 VALIDATED MD_OUTPUT；
- 后续由 run output Validator 核验 attempt chain。

# 异步结果

backend 接受后：

- `ATTEMPT_SUBMISSION_ACCEPTED`；
- 返回 Manager 完成 submission record 所需 evidence；
- 不等待、不轮询、不创建 MD_OUTPUT。

提交命令结束但 identity 不唯一：`ATTEMPT_SUBMISSION_ID_UNRESOLVED`，禁止自动重提。

# 默认输出

```text
04_md_simulation/<run_unit_id>/attempts/<attempt_id>/
├── md_execution_attempt_spec.yaml
├── md_execution_attempt_validation_report.yaml
├── command_record.yaml
├── md_run_execution_report.yaml
├── submission_evidence.yaml
└── execution.log
```

engine outputs 位于同一 attempt directory。

# Outcome codes

- `ATTEMPT_SUBMISSION_ACCEPTED`；
- `ATTEMPT_PROCESS_FINISHED_UNVERIFIED`；
- `EXECUTION_ATTEMPT_SPEC_MISSING_OR_INVALID`；
- `EXECUTION_ATTEMPT_NOT_VALIDATED`；
- `ATTEMPT_INPUT_ARTIFACT_MISMATCH`；
- `ATTEMPT_CHECKPOINT_MISSING_OR_MISMATCH`；
- `ATTEMPT_OUTPUT_CONFLICT`；
- `ATTEMPT_BACKEND_UNSUPPORTED_OR_UNAVAILABLE`；
- `ATTEMPT_SUBMISSION_REJECTED`；
- `ATTEMPT_SUBMISSION_ID_UNRESOLVED`；
- `ATTEMPT_PROCESS_EXITED_NONZERO`；
- `ATTEMPT_EXECUTION_INTERNAL_FAILURE`。

# 返回与恢复

成功提交或同步 terminal 时：

- Operation `status: DONE`；
- artifact candidates 为空；
- created files 仅为 attempt evidence；
- 不自行写 submission record。

中断后只要存在可能提交的证据，必须按“可能已提交”恢复，先查询当前 attempt status，不得重新运行同一 spec。

# 自检

- [ ] spec 已由专属 Validator 通过；
- [ ] attempt/spec/task identities 一致；
- [ ] 只写当前 attempt directory；
- [ ] v1 未启用 APPEND；
- [ ] checkpoint 未自动选择；
- [ ] 异步 attempt 有 prepared submission identity；
- [ ] 只执行/提交一次；
- [ ] submission accepted 未被写成 run complete；
- [ ] 没有轮询或自动重提；
- [ ] 没有写管理目录或 artifact records。
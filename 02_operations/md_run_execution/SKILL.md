---
name: md_run_execution
description: 根据不可变 md_run_execution_spec、validated simulation plan 和 VALIDATED MD_INPUT，在授权 run unit 目录内同步执行或向 LOCAL、TMUX、LSF、SLURM、PBS backend 异步提交一个 GROMACS mdrun，并记录命令和提交证据。该 Operation 不生成运行输入、不判断输出是否通过，也不轮询任务完成。
---

# 目标

执行 `md_simulation_workflow` 中一个已经完成 input validation 的 run unit：

- 核验 plan、execution spec 和 MDINPUT provenance；
- 为 GROMACS `mdrun` 构建无 shell 隐式解释的命令；
- 同步运行短任务，或异步提交长任务；
- 记录可恢复、可审计的 command 和 submission evidence；
- 将后续状态检查与输出验证交给 Validators。

# 职责边界

负责：

- 读取 immutable execution spec；
- 核验 plan/run unit/task/Workstream 身份；
- 核验 MDINPUT artifact、input manifest、`.tpr` 和 continuation checkpoint；
- 核验 backend、工作目录、资源和输出冲突；
- 记录 executable/version；
- 使用 argv 或受控 backend adapter 执行，不拼接任意 shell 字符串；
- 同步执行或异步提交一次；
- 捕获 PID、tmux session 或 scheduler job ID；
- 写 operation report、command record、execution log 和 submission evidence；
- 返回 Operation result。

不负责：

- 创建或修改 protocol spec、plan、`.mdp`、`.tpr`、topology、structure 或 checkpoint；
- 运行 `grompp`；
- 根据文件名或时间戳猜测输入；
- 根据 role 补充参数；
- 选择路线或下一个 run unit；
- 自动选择 checkpoint、append/noappend；
- 高频轮询；
- 判断 EM、平衡或 production 输出是否通过；
- 写 Manager 状态/记录或直接创建 submission record；
- 覆盖既有有效输出；
- 创建其他子 Agent 或直接向用户提问。

# 输入

必须接收 `subagent_task.schema.yaml` v2 的 `OPERATION` task unit：

```text
operation: md_run_execution
validator: null
```

任务必须提供：

- 唯一 `md_run_execution_spec.yaml`；
- validated `md_simulation_plan` 和 plan validation evidence；
- spec 引用的 VALIDATED MDINPUT artifact records；
- `md_run_input_manifest.yaml` 和 input validation report；
- `.tpr` file record；
- continuation 时明确 checkpoint record；
- allowed read/write、forbidden paths 和 detail output paths。

execution spec schema：

```text
schemas/md_run_execution_spec.schema.yaml
```

spec 必须作为不可变 task input。Operation 不得从自然语言补全缺失字段。

# 读写权限

只允许写 task 授权的：

```text
04_md_simulation/<run_unit_id>/**
```

只读：

- execution spec；
- validated plan；
- VALIDATED MDINPUT、input manifest 和 validation evidence；
- 明确 checkpoint；
- backend executable/submission script；
- task 指定环境信息。

禁止修改输入、写管理目录/其他 run unit、跟随未授权 symlink，或在未授权 host 执行。

# Preflight

必须依次确认：

1. task、Workstream、plan 和 run unit IDs 一致；
2. execution spec schema 有效；
3. plan 已验证且未被 superseded/invalidated；
4. run unit 存在于 plan；
5. execution spec 的 role/dependencies/work directory 与 plan 一致；
6. MDINPUT artifact 为 VALIDATED；
7. input manifest、`.tpr` identities 与 execution spec/task 一致；
8. input validation outcome 允许执行；
9. `engine` 为 GROMACS；
10. spec 中所有 input hashes 与实际文件一致；
11. continuation checkpoint 可读且 hash 一致；
12. fresh 模式不存在隐式 checkpoint；
13. append mode 与 restart mode 有效；
14. EXECUTION 类 blocking unresolved items 已解决；
15. work directory 位于 allowed write paths；
16. source/spec/target 不同路径；
17. 不存在未解决 active process、submission 或输出覆盖冲突；
18. executable 可解析并记录实际版本；
19. backend 所需字段完整；
20. command 为结构化 argv，不含 shell control operator；
21. output prefix/expected outputs 唯一；
22. 首个外部长任务提交所需 FULL runtime validation evidence 已提供。

任一 blocking preflight 失败时返回 BLOCKED，不执行或提交。

# 命令构建

命令必须由 execution spec 构建，至少包含：

- executable + `mdrun`；
- 明确 `.tpr`；
- output prefix/deffnm；
- checkpoint/continuation 参数，如适用；
- append policy，如适用；
- 并行/GPU/资源参数，如适用。

不得执行 `eval`、未审查的 `bash -c`、自由文本 shell 拼接，或自动增加 `-cpi/-append/-noappend/-maxh` 等字段。

# Backend

v1 支持：

```text
LOCAL | TMUX | LSF | SLURM | PBS
```

- `LOCAL + SYNCHRONOUS`：当前进程等待结束；
- `LOCAL + ASYNCHRONOUS`：返回可检查 PID/log；
- `TMUX`：session name 唯一且显式；
- scheduler：submission script 是有 hash 的只读输入，捕获 job ID；
- backend 必须提供接受证据，不能仅凭提交命令 return code 推测成功；
- `OTHER` 在 contract 扩展前 BLOCKED。

# 执行流程

1. 解析 task、权限、plan、MDINPUT 和 execution spec；
2. 执行完整 preflight；
3. 创建临时 command record/report；
4. 记录 plan/input manifest/TPR/checkpoint identities；
5. 记录 executable/version/environment 摘要；
6. 构建最终 argv 或受控 backend submission；
7. 在目标目录执行一次同步运行或异步提交；
8. 捕获退出码、PID/session/job ID 和 backend raw evidence；
9. 核验同步结束或 backend acceptance；
10. 写 submission evidence 和 execution log；
11. 重新读取结构化输出并进行最小 parse/hash 检查；
12. 原子提交业务记录文件；
13. 返回 Operation result。

# 同步运行

同步进程结束后：

- return code 0 不表示 MDOUTPUT 通过；
- Operation 返回 `PROCESS_FINISHED_UNVERIFIED`；
- 不创建 VALIDATED MDOUTPUT；
- 后续必须执行 `md_run_output_validator`。

非零 return code 且有明确 failure evidence 时返回 FAILED 并保留日志。

# 异步提交

backend 接受后：

- 返回 `SUBMISSION_ACCEPTED`；
- report 提供 Manager 创建 submission record 所需候选字段；
- 不等待、不轮询、不创建 MDOUTPUT。

若无法解析 PID/session/job ID，返回 `SUBMISSION_ID_UNRESOLVED`，不得假定成功。

# 输出目录

```text
04_md_simulation/<run_unit_id>/
├── md_run_execution_spec.yaml
├── command_record.yaml
├── md_run_execution_report.yaml
├── submission_evidence.yaml
└── execution.log
```

engine 输出文件名必须与 spec 一致。

# Outcome codes

- `SUBMISSION_ACCEPTED`；
- `PROCESS_FINISHED_UNVERIFIED`；
- `EXECUTION_SPEC_MISSING_OR_INVALID`；
- `SIMULATION_PLAN_INVALID_OR_STALE`；
- `MD_INPUT_NOT_VALIDATED`；
- `INPUT_MANIFEST_OR_TPR_MISMATCH`；
- `CHECKPOINT_MISSING_OR_MISMATCH`；
- `RESTART_POLICY_UNRESOLVED`；
- `OUTPUT_CONFLICT`；
- `BACKEND_UNSUPPORTED_OR_UNAVAILABLE`；
- `SUBMISSION_REJECTED`；
- `SUBMISSION_ID_UNRESOLVED`；
- `PROCESS_EXITED_NONZERO`；
- `EXECUTION_INTERNAL_FAILURE`。

# 返回

返回共享 `subagent_result` 的独立 `operation_result`。

成功提交或同步结束时：

- `status: DONE`；
- `artifact_candidates: []`；
- created files 包含 command/report/submission evidence/log；
- next recommendation 指向等待/状态或输出验证；
- 不自行写 submission record。

# 失败与恢复

- BLOCKED：没有启动或提交；
- FAILED：保留日志/failure evidence；
- submission 是否存在不明确时不得自动重提，先恢复/状态检查；
- task 中断后出现 PID/session/job evidence 时按“可能已提交”处理；
- 不删除 engine 输出；
- 不自动修改 spec 重试；
- 幂等复用必须核验 command/input/evidence hashes。

# Tool candidate

跨 backend 安全提交、job ID 解析和状态查询应由 `external_submission_adapter` 确定性 Tool 提供。该 Tool 未 ACTIVE 前，本 Skill 仍是 contract draft，不能将未来能力作为默认生产路径。

# 自检

- [ ] plan 有效且 run unit 一致；
- [ ] MDINPUT 已验证；
- [ ] input manifest/TPR/checkpoint hashes 一致；
- [ ] execution spec 是不可变输入；
- [ ] 未修改或生成 MDINPUT；
- [ ] continuation/append policy 明确；
- [ ] 命令无自由文本 shell 拼接；
- [ ] backend acceptance evidence 已记录；
- [ ] 提交/同步结束未写成输出通过；
- [ ] 没有轮询、覆盖或自动重提；
- [ ] 未写管理目录；
- [ ] 未返回 VALIDATED MDOUTPUT。
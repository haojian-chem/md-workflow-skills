---
name: md_run_execution
description: 根据不可变的 md_run_execution_spec，在授权的 run unit 目录内同步执行或向 LOCAL、TMUX、LSF、SLURM、PBS backend 异步提交一个 GROMACS mdrun，并记录命令、输入身份和提交证据。该 Operation 不生成新的模拟参数，不判断输出是否通过，也不轮询任务完成。
---

# 目标

执行 `md_simulation_workflow` 中一个明确的 run unit：

- 核验 execution spec、输入和路径；
- 为 GROMACS `mdrun` 构建无 shell 隐式解释的命令；
- 同步运行短任务，或异步提交长任务；
- 记录可恢复、可审计的 command 和 submission evidence；
- 将后续状态检查与输出验证交给专属 Validators。

# 职责边界

负责：

- 读取一个符合本 Skill schema 的 immutable execution spec；
- 核验 run unit、Workstream、task、MD_INPUT 和 checkpoint 身份；
- 核验 backend、工作目录、资源和输出冲突；
- 记录 GROMACS executable 和版本；
- 使用 argv 或受控 backend adapter 执行，不拼接任意 shell 字符串；
- 同步执行或异步提交一次；
- 捕获 PID、tmux session 或 scheduler job ID 等提交证据；
- 写 operation report、command record、execution log 和 submission evidence；
- 返回 Operation component result。

不负责：

- 创建或修改 `.mdp`、`.tpr`、topology、structure 或 checkpoint；
- 根据文件名猜测输入；
- 根据 run unit role 补充默认参数；
- 选择路线、下一个 run unit 或 Workstream；
- 自动选择 continuation checkpoint；
- 自动选择 `append` 或 `noappend`；
- 高频轮询外部任务；
- 判断能量最小化、平衡或生产模拟是否通过；
- 修改 `00_project_state/**` 或 `00_project_records/**`；
- 直接创建 submission record；
- 覆盖其他 task 或既有有效 run unit 输出；
- 创建其他子 Agent或直接向用户提问。

# 输入

必须接收 `subagent_task.schema.yaml` v2 的 `OPERATION` task unit：

```text
operation: md_run_execution
validator: null
```

任务必须提供：

- 唯一 `md_run_execution_spec.yaml`；
- spec 引用的 VALIDATED MD_INPUT file records；
- continuation 时使用的 checkpoint file record；
- allowed read/write paths；
- forbidden management paths；
- operation report、log 和 result data 路径。

execution spec 权威 schema：

```text
schemas/md_run_execution_spec.schema.yaml
```

spec 必须作为不可变 task input。Operation 不得根据自然语言临时补全缺失字段。

# 读写权限

只允许写：

```text
04_md_simulation/<run_unit_id>/**
```

且必须受 task `allowed_write_paths` 约束。

只读：

- execution spec；
- VALIDATED MD_INPUT；
- 明确 continuation checkpoint；
- backend 可执行程序和明确提交脚本；
- task 指定的必要环境信息。

禁止：

- 修改任何输入文件；
- 写管理目录；
- 写其他 run unit 目录；
- 跟随指向未授权路径的 symlink；
- 在未明确授权的远程 host 执行命令。

# Preflight

必须依次确认：

1. task、Workstream 和 run unit IDs 一致；
2. execution spec schema 有效；
3. `engine` 为当前支持的 `GROMACS`；
4. `.tpr` file identity 与 task 中 VALIDATED MD_INPUT 一致；
5. spec 中所有输入 SHA-256 与实际文件一致；
6. continuation 模式下 checkpoint 存在、可读且 hash 一致；
7. fresh 模式下没有隐式 checkpoint；
8. `append_mode` 与 restart mode 组合有效；
9. 工作目录位于 allowed write paths；
10. source、spec 和目标输出不是同一路径；
11. 不存在未解决的活动进程、submission 或输出覆盖冲突；
12. GROMACS executable 可解析，并记录实际版本；
13. backend 类型受支持；
14. backend 所需 session name、script、host 或资源字段完整；
15. command 使用结构化 argv，不含 shell control operator；
16. 输出前缀和 expected outputs 唯一；
17. 首个外部长任务提交所需 FULL runtime validation evidence 已由 Manager 提供。

任一 blocking preflight 失败时返回 BLOCKED，不执行或提交部分任务。

# 命令构建

## GROMACS 命令

命令必须由 execution spec 中的结构化字段构建，至少包含：

- GROMACS executable；
- `mdrun`；
- 明确 `.tpr`；
- 明确 output prefix 或 `deffnm`；
- 明确 continuation/checkpoint 参数，如适用；
- 明确 append policy，如适用；
- 明确并行和 GPU 参数，如适用。

不得：

- 执行 `eval`；
- 使用未审查的 `bash -c`；
- 将自由文本直接拼入 shell；
- 在 Operation 内自动增加 `-cpi`、`-append`、`-noappend`、`-maxh` 或资源参数。

## Backend

v1 支持：

```text
LOCAL
TMUX
LSF
SLURM
PBS
```

`OTHER` 必须 BLOCKED，除非后续 contract 明确扩展。

- `LOCAL + SYNCHRONOUS`：当前进程等待 `mdrun` 结束；
- `LOCAL + ASYNCHRONOUS`：必须返回可检查 PID 和日志路径；
- `TMUX`：session name 必须唯一且显式；
- scheduler：提交脚本必须作为有 hash 的只读输入，捕获 job ID；
- backend 不得通过“命令似乎执行成功”推测 job 已接受，必须有接受证据。

# 执行流程

1. 解析 task、权限和 execution spec；
2. 执行完整 preflight；
3. 创建临时 command record 和 operation report；
4. 记录 executable、版本、环境摘要和输入 hashes；
5. 构建最终 argv 或受控 backend submission；
6. 在目标 run unit 目录执行一次同步运行或异步提交；
7. 捕获退出码、PID/session/job ID 和 backend 原始返回；
8. 核验提交是否被 backend 接受，或同步进程是否已结束；
9. 写 submission evidence 和 execution log；
10. 重新读取本 Operation 生成的结构化文件并完成最小 parse/hash 检查；
11. 原子提交业务记录文件；
12. 返回 Operation result。

# 同步运行结果

同步进程结束后：

- 退出码为零不表示 MD_OUTPUT 已通过；
- Operation 只返回 `PROCESS_FINISHED_UNVERIFIED`；
- 不创建 VALIDATED MD_OUTPUT；
- 后续必须执行 `md_run_output_validator`。

非零退出码且有明确 process failure evidence 时返回 FAILED，并保留日志。

# 异步提交结果

backend 接受任务后：

- Operation 返回 `SUBMISSION_ACCEPTED`；
- report 中提供 Manager 创建 submission record 所需候选字段；
- 不等待任务完成；
- 不启动轮询；
- 不创建 MD_OUTPUT artifact candidate。

若提交命令完成但无法解析 job/session/PID，返回 `SUBMISSION_ID_UNRESOLVED`，不得假定提交成功。

# 输出目录

默认：

```text
04_md_simulation/<run_unit_id>/
├── md_run_execution_spec.yaml       # task 输入的受控副本或引用，可选
├── command_record.yaml
├── md_run_execution_report.yaml
├── submission_evidence.yaml
└── execution.log
```

engine 输出文件由 GROMACS 写入同一 run unit 目录，文件名必须与 spec 一致。

# Outcome codes

- `SUBMISSION_ACCEPTED`；
- `PROCESS_FINISHED_UNVERIFIED`；
- `EXECUTION_SPEC_MISSING_OR_INVALID`；
- `INPUT_ARTIFACT_MISMATCH`；
- `CHECKPOINT_MISSING_OR_MISMATCH`；
- `RESTART_POLICY_UNRESOLVED`；
- `OUTPUT_CONFLICT`；
- `BACKEND_UNSUPPORTED_OR_UNAVAILABLE`；
- `SUBMISSION_REJECTED`；
- `SUBMISSION_ID_UNRESOLVED`；
- `PROCESS_EXITED_NONZERO`；
- `EXECUTION_INTERNAL_FAILURE`。

# 返回

返回符合：

```text
03_contracts/subagent_result.schema.yaml
```

的独立 `operation_result`。

成功提交或同步结束时：

- `status: DONE`；
- `artifact_candidates: []`；
- `created_files` 包含 command record、report、submission evidence 和 log；
- `next_step_recommendation` 指向等待/状态检查或输出验证；
- 不自行写 submission record。

# 失败与恢复

- BLOCKED：没有启动进程或提交任务；
- FAILED：保留已产生的日志和 failure evidence；
- 异步提交是否实际存在不明确时，不允许自动重提；必须先执行恢复或状态检查；
- task 中断后若已出现 PID/session/job evidence，恢复流程必须按“可能已经提交”处理；
- 不删除已有 engine 输出；
- 不自动修改 spec 后重试；
- 同一 task 幂等复用必须核验 command、input 和 evidence hashes。

# Tool candidate

跨 backend 的安全提交、job ID 解析和状态检查具有重复、确定性和高风险特征，建议主窗口向 Tool Authoring 提交 `external_submission_adapter` tool request。

该 Tool 未 ACTIVE 前，本 Skill 只能处于 contract draft 或使用经权威实现明确测试的内建执行路径，不能把未来 Tool 当作默认可运行能力。

# 自检

- [ ] execution spec 是显式不可变输入；
- [ ] 没有修改 MD_INPUT 或 checkpoint；
- [ ] continuation 和 append policy 均明确；
- [ ] 命令没有自由文本 shell 拼接；
- [ ] backend 接受证据已记录；
- [ ] 提交成功没有被写成模拟完成；
- [ ] 同步退出码没有代替 output validation；
- [ ] 没有轮询外部任务；
- [ ] 没有覆盖其他 task/run unit 输出；
- [ ] 没有写管理目录；
- [ ] 没有返回 VALIDATED MD_OUTPUT；
- [ ] 没有自动重试不明确的 submission。
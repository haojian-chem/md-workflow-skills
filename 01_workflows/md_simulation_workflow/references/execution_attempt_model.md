# MD Execution Attempt Model

## 1. 定义

`execution attempt` 是对一个已经具有 VALIDATED MD_INPUT 的 run unit 进行的一次具体执行或外部提交。

```text
run unit
→ stable scientific segment

execution attempt
→ one immutable command/submission specification
→ one process/session/job identity
→ one isolated output set
```

一个 run unit 可以因同步失败、资源失败、外部重提或 same-TPR continuation 具有多个 attempts。

## 2. 身份

每个 attempt 必须具有：

```yaml
attempt_id:
run_unit_id:
execution_spec_id:
parent_attempt_id:
attempt_kind:
```

推荐 attempt ID：

```text
attempt.001
attempt.002
attempt.003
```

`attempt_id` 在当前 run unit 内唯一。不得仅通过 task ID、提交时间或文件时间戳识别 attempt。

## 3. Attempt kind

```text
FRESH
RETRY_SAME_INPUT
CONTINUE_NOAPPEND
```

v1 不支持生产级 `APPEND`。

### FRESH

- 使用当前 VALIDATED MD_INPUT 的 TPR；
- 不读取 prior-attempt checkpoint；
- 创建新的 attempt directory；
- 不覆盖任何既有 engine output。

### RETRY_SAME_INPUT

- TPR 与原 attempt 相同；
- 不从原 attempt checkpoint 继续；
- 用于 backend/resource/command correction 后从 TPR 初始状态重跑；
- 必须说明 superseded/rejected prior attempt；
- 创建新 attempt directory。

### CONTINUE_NOAPPEND

- TPR 与 parent attempt 相同；
- checkpoint 必须来自 parent/accepted attempt chain；
- 输出写入新 attempt directory；
- 不修改 parent attempt 文件；
- run output validation 在 run-unit 层核验累计 step/time 和 checkpoint continuity。

## 4. Execution spec owner

每个 attempt 的 immutable execution spec 由专属 task unit生成并验证：

```text
md_execution_attempt_specification
→ md_execution_attempt_validator
→ validated execution-attempt spec
→ md_run_execution
```

Manager、Workflow 和 `md_run_execution` 不得临时拼装或补全 execution spec。

execution spec 属于 `md_simulation_workflow` 局部业务对象，不是共享 route record。

## 5. Execution spec 最小内容

```yaml
schema_version:
execution_spec_id:
workstream_id:
plan_id:
run_unit_id:
attempt_id:
attempt_kind:
parent_attempt_id:
md_input_artifact_set_id:
input_manifest:
tpr:
continuation_checkpoint:
backend:
resources:
gromacs:
expected_attempt_outputs: []
output_records:
policies:
```

对象身份不得使用 `task_id` 替代。task ID 只记录“哪一个 task 生成或执行该 spec”。

## 6. Backend 与资源

backend、资源和 GROMACS runtime executable 属于 attempt，不属于 scientific protocol。

可由以下明确来源解析：

- resolved execution decision；
- 带 hash 的 resource/backend profile；
- 项目级已验证 runtime profile；
- 用户明确指定的 executable/path/version constraint。

不得从主机环境随意选择“第一个可用 GPU”或默认调度队列。

## 7. Prepared submission identity

异步 attempt 在产生外部 side effect 前必须具有恢复锚点：

```text
execution spec validated
→ Manager creates immutable task.yaml
→ prepared submission identity recorded
→ execution Operation submits exactly once
```

本地 execution spec 至少记录 `prepared_submission_id` 或由 task 提供可验证引用。共享 submission record 的实际创建和状态更新仍由 Manager 完成。

Operation 中断后只要存在可能提交的证据，恢复流程必须先查询状态，禁止自动重提。

## 8. 目录

```text
04_md_simulation/<run_unit_id>/attempts/<attempt_id>/
├── md_execution_attempt_spec.yaml
├── md_execution_attempt_validation_report.yaml
├── command_record.yaml
├── submission_evidence.yaml
├── execution.log
├── status_report.yaml
└── <engine outputs>
```

同一 attempt 的所有 side effects 必须位于该目录或显式授权的 backend 日志位置。

## 9. Output mutation policy

v1 固定：

```yaml
preserve_previous_attempts: true
allow_overwrite_existing_attempt: false
append_existing_engine_outputs: false
```

`CONTINUE_NOAPPEND` 读取 prior checkpoint，但向新目录写新输出。

APPEND 会修改既有文件并破坏旧 hash identity，在建立可恢复 mutable-output 协议前不得作为默认或可执行路径。

## 10. Submission/status/output 对齐

每条 execution、submission、status 和 output-validation evidence 必须至少能对齐：

```text
workstream_id
plan_id
run_unit_id
attempt_id
execution_spec_id
MD_INPUT artifact identity
```

submission record 共享 schema 暂无 attempt_id 字段时，必须通过 task ID、working directory、command record 和本地 execution spec 建立唯一映射；主窗口应评估是否扩展共享 contract。

## 11. Attempt terminal 不等于 run unit complete

一个 attempt terminal 后：

```text
backend/process terminal
→ FINISHED_UNVERIFIED
→ attempt evidence inspection
→ run-level output validation across accepted chain
```

- attempt 失败可能需要新 retry/continuation attempt；
- 单个 attempt 正常结束也可能尚未达到 run-unit completion target；
- run unit 只有在 accepted attempt chain 满足 completion criteria 后才生成 VALIDATED run-level MD_OUTPUT。

## 12. Supersede 与接受链

run output validation 必须区分：

- accepted attempts；
- failed attempts；
- cancelled attempts；
- superseded retry attempts；
- continuation chain。

只有 accepted chain 的文件进入 run-level MD_OUTPUT artifact candidate。失败/取消 attempt 的日志与 evidence 保留用于审计，但不作为有效轨迹片段。

## 13. 自检

- attempt 与 run unit 科学身份分离；
- task ID 未替代 execution spec/attempt identity；
- retry 和 continuation 使用新 attempt directory；
- v1 未启用 APPEND；
- backend/resource 未写入 scientific protocol；
- 异步提交前存在恢复锚点；
- terminal attempt 未被直接标记为 run unit complete；
- output Validator 可以重建唯一 accepted attempt chain。
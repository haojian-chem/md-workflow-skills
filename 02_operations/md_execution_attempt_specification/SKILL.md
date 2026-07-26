---
name: md_execution_attempt_specification
description: 根据 VALIDATED MD_INPUT、目标 run unit、明确 execution decisions/profile 和可选 prior attempt，在 run-unit attempt 目录中生成一个不可变 execution-attempt spec。该 Operation 不执行 mdrun、不提交外部任务，也不选择隐式 backend、资源、checkpoint 或 restart policy。
---

# 目标

闭合 `MD_INPUT → execution` 之间缺失的业务对象：

```text
VALIDATED MD_INPUT
+ selected run unit
+ explicit execution decisions/profile
+ optional parent attempt/checkpoint
→ md_execution_attempt_spec.yaml candidate
→ md_execution_attempt_validator
→ md_run_execution
```

# 职责边界

负责：

- 读取 task、validated protocol/plan 和 VALIDATED MD_INPUT；
- 物化稳定 `execution_spec_id`、`attempt_id` 和 attempt directory；
- 物化 `FRESH | RETRY_SAME_INPUT | CONTINUE_NOAPPEND`；
- 物化 backend、resource、GROMACS runtime 和 expected attempt outputs；
- 核验 prior attempt/checkpoint identity，如适用；
- 记录 prepared submission identity 引用；
- 生成 immutable spec candidate 和 specification report；
- 不执行任何 backend side effect。

不得：

- 使用 task ID 替代 attempt/spec identity；
- 修改 TPR、MDP、checkpoint 或其他 MD_INPUT；
- 推断“默认 GPU”“默认队列”或默认资源；
- 自动选择最新 checkpoint；
- 启用 APPEND；
- 运行 `mdrun`、tmux 或 scheduler command；
- 写管理目录；
- 覆盖 prior attempt/spec。

# 输入

必须作为：

```text
OPERATION_WITH_VALIDATOR
operation: md_execution_attempt_specification
validator: md_execution_attempt_validator
```

运行。

任务必须提供：

- validated protocol/plan identity；
- 目标 run unit；
- VALIDATED MD_INPUT artifact set 和 input manifest；
- 唯一新 `attempt_id` 与输出目录；
- attempt kind；
- backend/resource/runtime profile 或对应 resolved decisions；
- prepared submission identity，如异步；
- parent attempt/spec/checkpoint，如 retry/continuation；
- allowed read/write 与 forbidden paths；
- spec/report/log 输出路径。

本地 schema：

```text
schemas/md_execution_attempt_spec.schema.yaml
```

# Preflight

必须确认：

1. task/workstream/plan/run-unit IDs 一致；
2. protocol/plan 和 MD_INPUT 均已验证且未失效；
3. `attempt_id` 在当前 run unit 中唯一；
4. attempt directory 不存在，或为同一 task 的完全幂等候选；
5. attempt kind 为 v1 支持值；
6. FRESH 不包含 parent/checkpoint；
7. RETRY_SAME_INPUT 引用 prior attempt，但不使用 continuation checkpoint；
8. CONTINUE_NOAPPEND 引用同一 TPR 的 parent attempt 和明确 checkpoint；
9. checkpoint 属于 accepted parent chain；
10. backend/profile/resolved decisions 可唯一解析；
11. 异步 attempt 有 prepared submission identity；
12. command fields 为结构化 argv 数据，不含 shell control operator；
13. output paths 只位于新 attempt directory；
14. APPEND 和既有 engine-output mutation 未启用。

任一 blocking 条件失败时返回 BLOCKED，不生成部分 spec。

# Attempt 规则

## FRESH

- parent attempt 为 null；
- checkpoint 为 null；
- 从 TPR 初始状态运行。

## RETRY_SAME_INPUT

- parent attempt 非空；
- TPR identity 与 parent 相同；
- checkpoint 为 null；
- 用于 backend/resource/command correction 后从头重跑；
- prior attempt 保留且不得覆盖。

## CONTINUE_NOAPPEND

- parent attempt 非空；
- TPR identity 与 parent 相同；
- checkpoint identity 非空且可追溯；
- 新 attempt 写入新目录；
- `append_existing_outputs: false`。

# 输出

```text
04_md_simulation/<run_unit_id>/attempts/<attempt_id>/
├── md_execution_attempt_spec.yaml
├── md_execution_attempt_specification_report.yaml
└── attempt_specification.log
```

spec 是未验证业务候选，不是 MD_INPUT/MD_OUTPUT artifact。

# Outcome codes

- `EXECUTION_ATTEMPT_SPECIFIED`；
- `EXECUTION_ATTEMPT_SPECIFIED_WITH_WARNINGS`；
- `EXECUTION_ATTEMPT_INPUT_INVALID`；
- `ATTEMPT_ID_OR_PATH_CONFLICT`；
- `ATTEMPT_KIND_INVALID`；
- `PARENT_ATTEMPT_INVALID`；
- `CONTINUATION_CHECKPOINT_INVALID`；
- `BACKEND_OR_RESOURCE_UNRESOLVED`；
- `PREPARED_SUBMISSION_IDENTITY_MISSING`；
- `EXECUTION_COMMAND_POLICY_INVALID`；
- `EXECUTION_ATTEMPT_SPECIFICATION_INTERNAL_FAILURE`。

# 返回

成功时：

- Operation `status: DONE`；
- created files 包含 spec/report/log；
- artifact candidates 为空；
- Validator 独立决定 spec 是否可用于执行。

# 自检

- [ ] attempt/spec identity 独立于 task ID；
- [ ] backend/resource 来源明确；
- [ ] FRESH/RETRY/CONTINUE 语义互斥；
- [ ] v1 未启用 APPEND；
- [ ] continuation checkpoint 唯一且属于 parent chain；
- [ ] 异步 attempt 有恢复锚点；
- [ ] 未执行或提交任务；
- [ ] 未覆盖旧 attempt；
- [ ] 未写管理目录。
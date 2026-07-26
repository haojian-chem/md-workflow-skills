---
name: md_run_output_validator
description: 核验一个 GROMACS run unit 的 accepted execution-attempt chain，检查 validated MD_INPUT、attempt specs、command/submission/status provenance、required attempt outputs、checkpoint continuity、目标步数/时间和显式 acceptance checks，并生成唯一 run-level MD_OUTPUT manifest 与 artifact candidate。该 Validator 不修改或拼接 engine outputs。
---

# 目标

验证一个 run unit，而不是单个 process：

```text
validated protocol/plan/run unit
+ VALIDATED MD_INPUT
+ terminal execution attempts
→ accepted attempt chain
→ run-level output manifest
→ MD_OUTPUT artifact candidate
```

一个 run unit 可以由一个 FRESH attempt 完成，也可以由 FRESH + 一个或多个 CONTINUE_NOAPPEND attempts 完成。

# 职责边界

负责：

- 读取 protocol/plan、run unit、VALIDATED MD_INPUT；
- 读取该 run unit 的全部相关 attempt specs/validation/results/submissions/status evidence；
- 独立重建 attempt parent graph 和 accepted chain；
- 核验每个 accepted attempt 的输入、命令、terminal 和 required outputs；
- 核验 TPR identity、checkpoint continuity、step/time continuity 和 output isolation；
- 执行 protocol 中显式注册的 blocking/nonblocking checks；
- 写 run output validation report 和 manifest；
- 返回 run-level MD_OUTPUT artifact candidate。

不得：

- 修改、拼接、截断、重命名或修复 engine outputs；
- 自动选择未解决的 attempt 分支；
- 将失败/取消/superseded attempt 文件加入 accepted output；
- 创建 continuation/retry attempt；
- 修改 protocol、plan、MD_INPUT、execution spec 或 submission records；
- 新增科学阈值；
- 判断采样充分或科学收敛；
- 写管理目录。

# 输入

必须接收 VALIDATOR task unit，并提供：

- validated protocol/plan 和唯一目标 run unit；
- 当前 VALIDATED MD_INPUT/input manifest/TPR；
- 当前 run unit 的所有相关 execution-attempt specs 与 validation reports；
- execution Operation results、commands、submission/status records；
- attempt engine outputs；
- resolved attempt acceptance/supersede decisions，如存在分支；
- allowed read/write、forbidden paths；
- run output manifest/report/log 路径。

任何相关 attempt 为活动或 UNKNOWN 且未排除时，返回 BLOCKED。

# Preflight

确认：

1. task/workstream/plan/run-unit IDs 一致；
2. protocol/plan 和 MD_INPUT 已验证且未失效；
3. attempt IDs/spec IDs 唯一；
4. attempt parent graph 可解析且无环；
5. 每个 attempt spec 已通过专属 Validator；
6. submission/status/command/working directory 可按 attempt 对齐；
7. 不存在未闭合相关 attempt；
8. engine outputs 仅位于对应 attempt directory；
9. output manifest/report 路径受授权；
10. 被验证文件只读。

# Accepted attempt chain

独立分类：

- `ACCEPTED`：构成当前有效执行链；
- `FAILED`：有明确失败 evidence；
- `CANCELLED`：有明确取消 evidence；
- `SUPERSEDED`：被明确 replacement attempt 取代；
- `UNRESOLVED`：身份、parent 或 terminal evidence 不足。

只有 ACCEPTED chain 进入 run-level MD_OUTPUT。

规则：

- chain 必须从 FRESH 或明确 accepted retry root 开始；
- CONTINUE_NOAPPEND 的 parent 必须是 chain 中前一个 accepted attempt；
- continuation checkpoint 必须来自 parent attempt；
- RETRY_SAME_INPUT 不能与被替代 root 同时进入 accepted chain；
- 存在两个可行 terminal branches 且无 resolved selection 时 PAUSE；
- UNRESOLVED attempt 阻止通过。

# Attempt output checks

对每个 accepted attempt：

- spec/input/TPR/command hashes 一致；
- process/submission 已 terminal；
- required attempt outputs 存在、非空且可解析；
- normal/fatal/nonzero evidence 无冲突；
- atom/system identity 与 TPR 一致；
- trajectory/energy/log/checkpoint metadata 可对齐；
- output 文件属于当前 attempt，不是其他 attempt 遗留。

# Chain continuity

核验：

- 所有 accepted attempts 使用相同 TPR；
- continuation checkpoint 与 parent final checkpoint identity 对齐；
- step/time 单调连续；
- noappend segment 没有覆盖 prior files；
- final accepted attempt 的 step/time 满足 run-unit target；
- run-level final structure/checkpoint 唯一。

checkpoint 存在不能单独证明 attempt 或 run unit 完成。

# Role-specific checks

只执行 protocol 中显式列出的、metric registry 已支持的 checks。

- blocking check FAIL/UNRESOLVED：run output 不通过或 PAUSE；
- nonblocking check unresolved：warning；
- Validator 不增加隐式 EM force、temperature、pressure、density 或 convergence threshold。

# Run output manifest

默认写：

```text
04_md_simulation/<run_unit_id>/
├── md_run_output_manifest.yaml
├── md_run_output_validation_report.yaml
└── md_run_output_validation.log
```

manifest 至少记录：

- workstream/plan/protocol/run-unit IDs；
- MD_INPUT artifact identity；
- accepted/excluded/unresolved attempt IDs；
- accepted attempt order；
- execution spec/submission/status references；
- included output files 及所属 attempt；
- final step/time/structure/checkpoint；
- completion check results；
- source and derived artifact IDs。

manifest 不复制或拼接 engine outputs。

# Outcome codes

- `MD_RUN_OUTPUT_VALIDATED`；
- `MD_RUN_OUTPUT_VALIDATED_WITH_WARNINGS`；
- `RUN_OUTPUT_VALIDATOR_INPUT_INCOMPLETE`；
- `RUN_OUTPUT_ATTEMPT_GRAPH_INVALID`；
- `RUN_OUTPUT_ATTEMPT_BRANCH_UNRESOLVED`；
- `RUN_OUTPUT_ACTIVE_OR_UNKNOWN_ATTEMPT`；
- `RUN_OUTPUT_INPUT_OR_COMMAND_MISMATCH`；
- `RUN_OUTPUT_REQUIRED_ATTEMPT_FILE_MISSING`；
- `RUN_OUTPUT_FILE_UNREADABLE_OR_TRUNCATED`；
- `RUN_OUTPUT_FATAL_OR_NONZERO_EXIT`；
- `RUN_OUTPUT_CHECKPOINT_CHAIN_INVALID`；
- `RUN_OUTPUT_STEP_OR_TIME_CONTINUITY_INVALID`；
- `RUN_OUTPUT_TARGET_NOT_REACHED`；
- `RUN_OUTPUT_CROSS_FILE_INCONSISTENCY`；
- `RUN_OUTPUT_ROLE_SPECIFIC_CHECK_FAILED`；
- `RUN_OUTPUT_ROLE_SPECIFIC_CHECK_UNRESOLVED`；
- `RUN_OUTPUT_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可返回 MD_OUTPUT candidate。

# Artifact candidate

通过时返回一个 run-level `MD_OUTPUT` candidate：

- files 包含 accepted attempts 的 required outputs；
- 包含 run output manifest 和 validation report；
- `derived_from_artifact_set_ids` 指向当前 MD_INPUT 和上游 run-level MD_OUTPUT；
- failed/cancelled/superseded attempt files 不进入 candidate。

Manager 完成 runtime validation 和记录后才登记 VALIDATED。

# 技术范围

通过只证明 accepted attempt chain 与显式 completion gate 技术闭合，不证明 equilibration 充分、sampling 收敛或科学结论成立。

# 自检

- [ ] 验证对象是 run unit attempt chain，不是单一 process；
- [ ] active/UNKNOWN attempts 已阻断；
- [ ] accepted/excluded/superseded attempts 已区分；
- [ ] continuation parent/checkpoint/TPR continuity 已检查；
- [ ] failed attempts 未进入 artifact candidate；
- [ ] required files 来自显式 spec/protocol；
- [ ] target step/time 来自实际 outputs；
- [ ] 未修改或拼接 engine outputs；
- [ ] 未新增科学阈值；
- [ ] 未写管理目录。
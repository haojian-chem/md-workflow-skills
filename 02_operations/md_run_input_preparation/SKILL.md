---
name: md_run_input_preparation
description: 根据 validated scientific protocol 和 task-projection plan 中的一个 run unit，从 FINAL_FILE 或 TEMPLATE_WITH_TYPED_OVERRIDES 物化受控 MDP，再使用 VALIDATED SYSTEM 或上游 VALIDATED run-level MD_OUTPUT 执行一次 GROMACS grompp，生成 MD_INPUT candidate、manifest 和证据。该 Operation 不选择科学默认值、不执行 mdrun。
---

# 目标

```text
validated protocol + plan projection
+ selected run unit
+ VALIDATED SYSTEM or upstream run-level MDOUTPUT
+ explicit MDP specification
→ materialize run.mdp
→ grompp
→ run.tpr + manifest/evidence
→ md_run_input_validator
```

# 职责边界

负责：

- 读取 validated protocol、plan projection 和 run unit；
- 唯一解析 coordinates、topology/include closure、可选 index/reference/input checkpoint；
- 根据 MDP source kind 原样复制 final file，或执行 typed exact parameter replacement；
- 记录 MDP source、rendered file、override values 和 hashes；
- 使用 task/profile 明确的 GROMACS grompp executable；
- 使用 protocol preprocessing policy 中的 `maxwarn`；
- 执行一次 `grompp`；
- 写 TPR、input manifest、command、stdout/stderr 和 report；
- 返回 MD_INPUT artifact candidate。

不得：

- 根据 run name/常见流程补充或修改参数；
- 自由文本 search/replace；
- 自动增加 maxwarn；
- 从多个候选中选择“最新”坐标/checkpoint/topology；
- 将 runtime executable/version 写回 scientific protocol；
- 修改 SYSTEM、upstream MDOUTPUT、protocol、plan 或 source MDP/template；
- 执行 mdrun；
- 覆盖已有 input；
- 写管理目录。

# 输入

必须作为：

```text
OPERATION_WITH_VALIDATOR
operation: md_run_input_preparation
validator: md_run_input_validator
```

任务提供：

- validated protocol spec/validation；
- validated plan 和唯一 run-unit projection；
- VALIDATED SYSTEM 或 upstream run-level MDOUTPUT records/manifests；
- MDP source file/template 和 typed override provenance；
- 明确 coordinates/topology/includes/index/reference/input checkpoint；
- GROMACS grompp runtime profile/executable constraint；
- 新 MD_INPUT 输出路径集合；
- allowed read/write 与 forbidden paths；
- command/manifest/report/log/Validator detail paths。

# Preflight

确认：

1. task/workstream/protocol/plan/run-unit IDs 一致；
2. protocol/plan 已验证且未失效；
3. run input gate 为 READY；
4. dependencies 已有 VALIDATED run-level MDOUTPUT，或从 SYSTEM 起步；
5. source files 可读且 hashes 与 protocol 一致；
6. MDP source kind/render policy/overrides schema 有效；
7. override parameters 唯一且可在 template 中唯一定位；
8. override value types 与 rendered tokens 一致；
9. coordinates/topology/include/index/reference/checkpoint 唯一；
10. SYSTEM start-state 没有 checkpoint；
11. input artifact 为 VALIDATED；
12. grompp executable 可定位并记录实际版本；
13. `maxwarn` 与 protocol 一致；
14. output paths 无冲突，且 source/target 不同；
15. 管理目录禁止写入。

任一 blocking preflight 失败时不运行 grompp。

# MDP materialization

## FINAL_FILE

- source MDP 作为最终参数文件；
- typed overrides 必须为空；
- 复制到 `run.mdp` 或记录同一 immutable identity；
- copied content hash 必须与 source 相同。

## TEMPLATE_WITH_TYPED_OVERRIDES

- template hash 必须匹配；
- 只允许 `EXACT_PARAMETER_REPLACEMENT`；
- 每个 parameter 必须在模板语义解析后唯一；
- 按 typed value 序列化，不执行任意文本片段；
- 未声明参数保持模板原值；
- 同一 parameter 重复 override、目标缺失或多义时 BLOCKED；
- rendered MDP 记录 source+override provenance。

Operation 不评价 MDP 科学合理性；Validator 只核验显式 specification 是否准确物化。

# Start-state input

## SYSTEM

从 VALIDATED SYSTEM 唯一解析 coordinates、topology root/include closure 及明确可选 index/reference。不得使用 continuation checkpoint。

## PRIOR_RUN_OUTPUT

引用 protocol/plan 指定 source run unit 的 VALIDATED run-level MDOUTPUT，并唯一选择 required structure和可选 input checkpoint。不得按时间戳选择。

# grompp policy

- executable/version 是 runtime evidence，不写回 protocol；
- `maxwarn` 来自 protocol；
- Operation 不自动重试或提高 maxwarn；
- stdout/stderr 中全部 warning 进入 manifest/report；
- topology include closure 在运行前确定并记录。

# 默认输出

```text
04_md_simulation/<run_unit_id>/input/
├── run.mdp
├── run.tpr
├── md_run_input_manifest.yaml
├── grompp_command_record.yaml
├── grompp_stdout.log
├── grompp_stderr.log
└── md_run_input_preparation_report.yaml
```

# Manifest 内容

至少记录：

- task/workstream/protocol/plan/run-unit IDs；
- source artifact IDs；
- MDP source kind/source/rendered identities；
- typed overrides 与 provenance refs；
- coordinates/topology/includes/index/reference/input checkpoint；
- actual grompp executable/version/argv；
- maxwarn、return code、warnings/errors；
- generated TPR identity；
- output paths 和 resolved decision IDs。

# Outcome codes

- `MD_RUN_INPUT_PREPARED`；
- `MD_RUN_INPUT_PREPARED_WITH_WARNINGS`；
- `PROTOCOL_OR_PLAN_INVALID_OR_STALE`；
- `RUN_UNIT_NOT_FOUND_OR_INPUT_GATE_BLOCKED`；
- `RUN_INPUT_SOURCE_AMBIGUOUS_OR_INVALID`；
- `MDP_SOURCE_IDENTITY_MISMATCH`；
- `MDP_TEMPLATE_OVERRIDE_INVALID`；
- `MDP_RENDERING_FAILED`；
- `TOPOLOGY_INCLUDE_INCOMPLETE`；
- `GROMPP_CAPABILITY_UNAVAILABLE`；
- `GROMPP_WARNING_LIMIT_EXCEEDED`；
- `GROMPP_FAILED`；
- `RUN_INPUT_OUTPUT_CONFLICT`；
- `RUN_INPUT_PREPARATION_INTERNAL_FAILURE`。

# Artifact candidate

成功时返回 `MD_INPUT` candidate，files 至少包括：

- rendered/copied `run.mdp`；
- `run.tpr`；
- input manifest；
- command record；
- Operation report。

Manager 只在专属 Validator 通过后登记 VALIDATED MDINPUT。

# 自检

- [ ] protocol 是科学字段来源，plan 仅用于 projection；
- [ ] FINAL_FILE/template+typed overrides 已区分；
- [ ] 未进行自由文本或隐式参数修改；
- [ ] source/start-state 文件唯一；
- [ ] SYSTEM start 没有 checkpoint；
- [ ] maxwarn 未自动增加；
- [ ] runtime executable 未写回 protocol；
- [ ] grompp 只执行一次；
- [ ] candidate 仍未验证；
- [ ] 未运行 mdrun或写管理目录。
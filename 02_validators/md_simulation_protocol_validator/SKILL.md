---
name: md_simulation_protocol_validator
description: 独立核验 scientific simulation protocol candidate 与 VALIDATED SYSTEM、structured inputs、resolved decisions、route scope、MDP final files/templates 和 field provenance 是否一致，并确认没有隐式科学默认值或 misplaced runtime configuration。该 Validator 不修改 spec，也不生成 plan。
---

# 目标

确认 protocol 可作为科学字段唯一 owner 并进入 plan materialization。

# 职责边界

负责：

- 读取 protocol candidate、specification report、SYSTEM artifacts、decision records、structured protocol inputs 和文件；
- 独立重建 expected run-unit set、roles、dependencies、MDP specs、start states、preprocessing policies、expected outputs 和 completion criteria；
- 检查 field-provenance coverage 与冲突；
- 检查 unresolved barrier 分类；
- 检查 runtime/backend/resource 字段未混入 protocol；
- 写 validation report 和 gate 建议。

不得：

- 修改 spec 或源文件；
- 补充 run units、MDP overrides 或 thresholds；
- 解释无法确定解析的开放式自然语言；
- 选择 backend/resources；
- 生成 plan/TPR/attempt；
- 写管理目录。

# 输入

作为 protocol specification 的专属 Validator，接收：

- 同一 task Operation result/report；
- protocol candidate；
- VALIDATED SYSTEM records；
- structured protocol input；
-完整 decision records，而非仅 summary；
- referenced MDP/template files；
- old protocol，如为 revision；
- allowed read/write 与 forbidden paths；
- validation report/result data 路径。

# Preflight

确认：

1. Operation status 为 DONE；
2. protocol schema v2 有效；
3. task/workstream IDs 一致；
4. SYSTEM artifacts 已 VALIDATED；
5. source records/files 可读且 hashes 一致；
6. Validator 不写 protocol/SYSTEM/source files；
7. 管理目录禁止写入。

# 独立检查

## Scientific field reconstruction

从权威输入独立计算 expected：

- run unit IDs 和 roles；
- dependencies；
- MDP source kind/source/typed overrides；
- start-state source；
- maxwarn/index/reference requirements；
- expected output roles；
- completion mode、targets 和 checks。

不得信任 Operation report 自报列表。

## Role and dependency

- role 只允许 EM/EQUILIBRATION/PRODUCTION/CUSTOM；
- CONTINUATION 出现即不通过；
- IDs 唯一；
- dependencies 全部存在、无 self/cycle；
- PRIOR_RUN_OUTPUT source 位于 dependency closure；
- SYSTEM start-state 的 checkpoint 必须为 null。

## MDP specification

FINAL_FILE：

- final MDP identity/hash 有效；
- overrides 为空；
- rendering policy 为 USE_FILE_UNCHANGED。

TEMPLATE_WITH_TYPED_OVERRIDES：

- template identity/hash 有效；
- overrides parameter 唯一、类型和值一致；
- rendering policy 为 EXACT_PARAMETER_REPLACEMENT；
- 每个 override value 有 provenance；
- 不包含自由文本 replacement。

## Completion criteria

- TARGET_STEP_OR_TIME 至少有 target_nsteps 或 target_time_ps；
- ROLE_SPECIFIC 至少有一个显式 check；
- metric IDs 只能在 registry capability 明确时进入可执行 hard gate；
- 不增加隐式科学 threshold。

## Field provenance

- 所有非派生科学字段有覆盖；
- field paths 指向真实字段；
- source IDs 可追溯；
- 相同 field path 不存在无法解释的冲突来源；
- runtime field 不得通过 provenance 合法化后混入 scientific protocol。

## Unresolved barriers

- PROTOCOL_VALIDATION item 存在时不通过；
- INPUT_PREPARATION/ATTEMPT_SPECIFICATION items 必须绑定受影响 fields/runs；
- 科学字段不得误分类为 attempt-only unresolved。

## Runtime separation

protocol 不得包含：

- GROMACS executable/version path；
- execution mode/backend/host/session/queue；
- MPI/OMP/GPU/memory/walltime；
- append/noappend；
- prepared submission identity。

## Revision

新版本需新 identity/path、有效 supersedes/revision reason，旧 protocol 和下游 artifacts 不得覆盖。

# Outcome codes

- `SIMULATION_PROTOCOL_VALIDATED`；
- `SIMULATION_PROTOCOL_VALIDATED_WITH_DEFERRED_GATES`；
- `PROTOCOL_VALIDATOR_INPUT_INCOMPLETE`；
- `PROTOCOL_SPEC_SOURCE_MISMATCH`；
- `PROTOCOL_FIELD_PROVENANCE_INVALID`；
- `PROTOCOL_IMPLICIT_DEFAULT_DETECTED`；
- `PROTOCOL_RUN_UNIT_OR_DAG_INVALID`；
- `PROTOCOL_MDP_SPEC_INVALID`；
- `PROTOCOL_START_STATE_INVALID`；
- `PROTOCOL_COMPLETION_CRITERIA_INVALID`；
- `PROTOCOL_UNRESOLVED_ITEM_MISCLASSIFIED`；
- `PROTOCOL_RUNTIME_FIELD_MISPLACED`；
- `PROTOCOL_REVISION_CHAIN_INVALID`；
- `PROTOCOL_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可进入 plan materialization。

# 输出

```text
04_md_simulation/00_plan/
├── simulation_protocol_validation_report*.yaml
└── simulation_protocol_validation*.log
```

不返回 MD artifact candidate。

# 自检

- [ ] expected protocol 已独立重建；
- [ ] CONTINUATION role 已拒绝；
- [ ] MDP final/template override 条件已检查；
- [ ] completion mode cross-field 条件已检查；
- [ ] field provenance 完整无冲突；
- [ ] runtime/backend/resource 未混入 protocol；
- [ ] unresolved barriers 分类正确；
- [ ] revision 未覆盖旧版本；
- [ ] 未修改被验证对象或管理目录。
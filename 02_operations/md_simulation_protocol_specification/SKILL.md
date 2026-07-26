---
name: md_simulation_protocol_specification
description: 将 VALIDATED SYSTEM、结构化 protocol input、已解决科学决定、明确 MDP final file 或 template+typed overrides 及 route scope 物化为 scientific simulation protocol candidate。该 Operation 不补充默认流程，不写 backend/resource/runtime 配置。
---

# 目标

```text
VALIDATED SYSTEM
+ structured scientific inputs
+ resolved decisions
+ explicit MDP final files or templates
+ resolved route scope
→ simulation_protocol_spec candidate
→ md_simulation_protocol_validator
```

protocol 是科学字段唯一 owner。

# 职责边界

负责：

- 读取 task、VALIDATED SYSTEM、route scope、decision records 和显式文件；
- 物化 run-unit IDs、scientific roles、dependencies、MDP specs、start states、preprocessing policy、expected output roles 和 completion criteria；
- 为每个非空科学字段记录 field-level provenance；
- 记录 unresolved items 与其 blocking stage；
- 生成 immutable protocol candidate 和 report。

不得：

- 根据“标准流程”“常用参数”生成 EM/NVT/NPT/production；
- 通过自由语言猜测温度、步数、耦合、约束或 threshold；
- 将 continuation 设为 scientific role；
- 写 GROMACS executable、host、backend、GPU、queue、MPI/OMP、memory 或 walltime；
- 创建 plan、TPR、execution attempt 或 output；
- 修改源 MDP/template/SYSTEM；
- 写管理目录。

# 输入来源

可接受：

- 已验证的结构化 protocol input；
- decision record 中精确且可确定解析的 option；
- 带 hash 的最终 MDP；
- 带 hash 的 MDP template + typed overrides；
- VALIDATED SYSTEM/MDOUTPUT identities；
- route scope 的非科学范围字段。

任意值若只能依赖开放式自然语言解释，必须形成 confirmation item，不得写入 protocol。

# Protocol schema

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
```

v2 scientific role：

```text
ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CUSTOM
```

MDP source：

```text
FINAL_FILE
TEMPLATE_WITH_TYPED_OVERRIDES
```

# Field provenance

每个科学字段必须映射到唯一或明确组合来源，例如：

```text
run_units[0].role
run_units[0].mdp_spec.source
run_units[0].mdp_spec.typed_overrides[0].value
run_units[0].start_state.source_type
run_units[0].completion_criteria.target_time_ps
```

Validator 将独立检查 coverage、重复/冲突来源和 decision/file identities。

# 未决项 barrier

```text
PROTOCOL_VALIDATION
→ protocol 不可接受

INPUT_PREPARATION
→ protocol 可存在
→ 阻塞受影响 run input

ATTEMPT_SPECIFICATION
→ protocol/plan/MDINPUT 可存在
→ 阻塞受影响 execution attempt spec
```

科学字段不得伪装为 ATTEMPT_SPECIFICATION-only 未决项。

# MDP 规则

## FINAL_FILE

- source 为最终 MDP file identity；
- typed overrides 必须为空；
- input preparation 使用文件不变副本/identity。

## TEMPLATE_WITH_TYPED_OVERRIDES

- source 为 immutable template identity；
- override 必须指定 parameter、value type、value 和 unit；
- input preparation 只允许 exact parameter replacement；
- 不允许自由文本 search/replace；
- 每个 override value 必须有 provenance。

# 修订

科学 run units、MDP、start-state 或 completion criteria 变化时生成新 protocol version：

- 新 `spec_id` 和路径；
- `supersedes_spec_id` 指向旧版本；
- `revision_reason` 非空；
- 不覆盖旧 protocol/plan/MDINPUT/MDOUTPUT。

backend/resource/runtime 变化本身不要求新 scientific protocol。

# 输出

```text
04_md_simulation/00_plan/
├── simulation_protocol_spec*.yaml
├── simulation_protocol_specification_report*.yaml
└── protocol_specification*.log
```

# Outcome codes

- `SIMULATION_PROTOCOL_SPECIFIED`；
- `SIMULATION_PROTOCOL_SPECIFIED_WITH_DEFERRED_GATES`；
- `PROTOCOL_INPUT_INCOMPLETE_OR_AMBIGUOUS`；
- `PROTOCOL_IMPLICIT_DEFAULT_REQUESTED`；
- `PROTOCOL_FIELD_PROVENANCE_INCOMPLETE`；
- `PROTOCOL_RUN_UNIT_OR_DEPENDENCY_INVALID`；
- `PROTOCOL_MDP_SPEC_INVALID`；
- `PROTOCOL_START_STATE_INVALID`；
- `PROTOCOL_COMPLETION_CRITERIA_INVALID`；
- `PROTOCOL_RUNTIME_FIELD_MISPLACED`；
- `PROTOCOL_OUTPUT_CONFLICT`；
- `PROTOCOL_SPECIFICATION_INTERNAL_FAILURE`。

# 返回

成功时 protocol 仍为未验证业务候选，artifact candidates 为空；专属 Validator 决定是否可进入 plan materialization。

# 自检

- [ ] 未生成默认 run units/参数；
- [ ] role 中无 CONTINUATION；
- [ ] runtime/backend/resource 未进入 scientific protocol；
- [ ] FINAL_FILE/template+typed override 语义明确；
- [ ] 每个科学字段有 provenance；
- [ ] 自由语言歧义已转 confirmation item；
- [ ] 未决项 barrier 分类正确；
- [ ] 修订未覆盖旧版本；
- [ ] 未修改源文件或管理目录。
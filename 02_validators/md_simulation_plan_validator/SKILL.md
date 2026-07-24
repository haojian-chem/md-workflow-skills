---
name: md_simulation_plan_validator
description: 独立核验 md_simulation_plan candidate 是否准确物化已验证 protocol spec，并与 VALIDATED SYSTEM、field provenance、run unit DAG、MDP identities、未决项和修订谱系一致。该 Validator 不修改计划、不补充科学参数，也不生成 MD_INPUT。
---

# 目标

确认 `md_simulation_plan` 可以作为动态 route projection 和逐 run input preparation 的权威阶段计划。

通过只表示：

- protocol spec 已由专属 Validator 接受；
- plan 对 protocol 逐字段保真；
- DAG、来源、路径和未决项分层一致；
- plan 可用于后续 input preparation gate。

不表示 MDP 科学设置最佳、TPR 已生成或模拟已完成。

# 职责边界

负责：

- 读取 protocol spec 及其 validation evidence；
- 读取 SYSTEM、source files、旧 plan 和 plan candidate；
- 独立重算 expected run unit set、字段和 DAG；
- 核验 protocol-to-plan 保真、field provenance coverage 和 hashes；
- 核验 start state、未决项、路径与 revision chain；
- 写 report 并返回 gate 建议。

不负责修改 plan/protocol/MDP，运行 grompp/mdrun，接受或替换 SYSTEM，写管理目录或自动重试。

# 输入

作为组合 task 的 validator 部分，必须接收：

- 同一 task 的 Operation result；
- validated `simulation_protocol_spec.yaml`；
- protocol validation report/result；
- plan candidate 和 materialization report；
- VALIDATED SYSTEM records；
- MDP/template files；
- old plan，如为 revision；
- allowed read/write、forbidden paths 和 Validator detail paths。

Operation 未产生完整 candidate 时 BLOCKED 或 FAILED，不推测内容。

# Preflight

确认：

- task mode、Skill refs、task/workstream IDs 正确；
- Operation status 为 DONE；
- protocol 和 plan 均通过各自 schema；
- protocol validation outcome 允许进入 plan；
- protocol spec path/hash/validator task 与 report 一致；
- protocol 未被 superseded/invalidated；
- required files 可读且 hashes 一致；
- SYSTEM 为 VALIDATED；
- Validator 不以被验证对象为写入目标；
- 管理目录不可写。

# 独立检查

## Protocol gate

只有以下 protocol outcomes 可作为输入：

```text
SIMULATION_PROTOCOL_VALIDATED
SIMULATION_PROTOCOL_VALIDATED_WITH_DEFERRED_ITEMS
```

第二种情况下必须确认没有 PLAN_VALIDATION unresolved items。否则返回 `PLAN_PROTOCOL_NOT_VALIDATED`。

## Protocol-to-plan 保真

从 protocol spec 独立计算 expected：

- SYSTEM artifact IDs；
- run unit IDs、roles、sequence、depends_on；
- work directories；
- MDP identities；
- start-state sources；
- grompp settings；
- execution policy；
- expected outputs/completion criteria；
- resolved decisions/unresolved items。

不得信任 materialization report 自报结果。plan 不得新增、删除或改变科学字段。

## Field provenance

- protocol 中 required scientific fields 必须有 provenance；
- plan 必须完整继承这些字段及其来源关系；
- provenance source IDs 必须可定位；
- uncovered fields 返回 `PLAN_FIELD_PROVENANCE_INCOMPLETE`；
- 不得用 plan materialization task 自身作为科学来源。

## DAG 与 start state

检查：

- IDs 唯一；
- dependency references 存在；
- 无 self-dependency/cycle；
- sequence 与 dependency 无反向矛盾；
- PRIOR_RUN_OUTPUT source 位于 dependency closure；
- SYSTEM source 不引用 source run unit。

## Files 与 lineage

- protocol/MDP hashes 与实际文件一致；
- SYSTEM IDs 与 records 一致；
- decisions 可追溯；
- source files 未改变；
- plan paths 属于当前 Workstream。

## 未决项

- PLAN_VALIDATION 项存在：不通过；
- INPUT_PREPARATION 项必须有 affected field paths，并阻止对应 input task；
- EXECUTION 项只允许不改变科学输入的执行问题；
- 科学字段不得伪装为 execution-only。

## Revision

- `supersedes_plan_id` 指向提供的旧 plan；
- revision reason 非空；
- 新 plan 使用新 identity/path；
- 旧 plan 和下游 artifacts 不被覆盖；
- 首版 plan 的 supersedes/reason 可以为 null。

# Outcome codes

- `SIMULATION_PLAN_VALIDATED`；
- `SIMULATION_PLAN_VALIDATED_WITH_EXECUTION_UNRESOLVED`；
- `PLAN_PROTOCOL_NOT_VALIDATED`；
- `PLAN_SPEC_MISMATCH`；
- `PLAN_FIELD_PROVENANCE_INCOMPLETE`；
- `PLAN_DAG_INVALID`；
- `PLAN_START_STATE_INVALID`；
- `PLAN_SOURCE_OR_HASH_MISMATCH`；
- `PLAN_DECISION_PROVENANCE_MISMATCH`；
- `PLAN_UNRESOLVED_ITEM_MISCLASSIFIED`；
- `PLAN_REVISION_CHAIN_INVALID`；
- `PLAN_PATH_CONFLICT`；
- `PLAN_VALIDATOR_INPUT_INCOMPLETE`；
- `PLAN_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcomes 可以建议 Workflow 使用 plan。

# 输出

```text
04_md_simulation/00_plan/
├── md_simulation_plan_validation_report.yaml
└── md_simulation_plan_validation_result.yaml
```

report schema：

```text
schemas/md_simulation_plan_validation_report.schema.yaml
```

Validation result 必须与 Operation result 分开，记录 validated files、field provenance coverage、unresolved items 和 `input_preparation_allowed_run_unit_ids`；不创建 MD_INPUT artifact。

# 失败处理与自检

- 输入不完整：BLOCKED；
- 对象可检查但 gate 不通过：DONE + 不通过 outcome；
- parser/internal error：FAILED；
- 不修改 plan，不自动重跑。

自检：

- [ ] protocol 已由专属 Validator 接受；
- [ ] expected plan 从 protocol 独立重算；
- [ ] 未信任 Operation report；
- [ ] field provenance coverage 完整；
- [ ] DAG/start state/paths 已检查；
- [ ] hashes/SYSTEM lineage 一致；
- [ ] 未决项分类正确；
- [ ] revision 未覆盖旧 plan；
- [ ] 未补充科学参数或生成 MD_INPUT；
- [ ] 未修改对象或写管理目录。
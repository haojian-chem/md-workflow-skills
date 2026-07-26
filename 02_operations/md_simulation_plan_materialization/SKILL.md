---
name: md_simulation_plan_materialization
description: 根据 validated scientific simulation protocol 和 VALIDATED SYSTEM，生成 immutable MD simulation task-projection plan。该 Operation 只派生 run-unit DAG、工作目录和 barrier gate，不复制拥有科学参数，不保存运行状态，也不执行 grompp/mdrun。
---

# 目标

```text
validated protocol
+ protocol validation evidence
+ VALIDATED SYSTEM
→ immutable task-projection plan candidate
→ md_simulation_plan_validator
```

protocol 是科学字段唯一 owner；plan 是 Workflow/Manager 规划 task 的静态派生视图。

# 职责边界

负责：

- 读取 validated protocol、Validator evidence 和 SYSTEM lineage；
- 为每个 protocol run unit 生成稳定 projection；
- 保留 run-unit ID、role、dependencies 和 start-state logical source；
- 派生 run/input/attempts 工作目录；
- 将 protocol unresolved items 投影为 input/attempt gates；
- 检查 IDs、DAG、路径冲突和 revision lineage；
- 生成 immutable plan candidate 和 report。

不得：

- 复制拥有 MDP values、completion criteria 或其他科学字段；
- 写 grompp executable、backend、resources、attempt IDs 或 submission data；
- 保存 `NOT_PREPARED/RUNNING/VALIDATED` 等运行状态；
- 补充或修改 protocol；
- 创建 MD_INPUT、execution spec 或 output；
- 覆盖旧 plan；
- 写管理目录。

# 输入

必须作为：

```text
OPERATION_WITH_VALIDATOR
operation: md_simulation_plan_materialization
validator: md_simulation_plan_validator
```

任务提供：

- validated protocol spec 与 protocol Validator result/report；
- VALIDATED SYSTEM artifacts；
- 旧 plan，如为 revision；
- 新 plan/output report路径；
- allowed read/write 与 forbidden paths。

本地 plan schema：

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_plan.schema.yaml
```

# Preflight

确认：

- protocol schema v2 有效并已通过专属 Validator；
- protocol/workstream/SYSTEM identities 一致；
- protocol 无 PROTOCOL_VALIDATION unresolved item；
- run-unit IDs 唯一、dependencies 无环；
- start-state references 可投影；
- plan 输出路径为新路径；
- revision chain 可定位且旧 plan 不变；
- 管理目录禁止写入。

# Projection 规则

每个 run-unit projection 只保存：

```text
run_unit_id
protocol_field_path
role
depends_on
work_directory
input_work_directory
attempts_work_directory
start_state_source_type
start_state_source_run_unit_id
input_gate_status
attempt_gate_status
blocking_item_ids
```

目录默认：

```text
04_md_simulation/<run_unit_id>
04_md_simulation/<run_unit_id>/input
04_md_simulation/<run_unit_id>/attempts
```

plan 不复制：

- MDP source/overrides；
- preprocessing values；
- expected output details；
- completion targets/checks；
- runtime/backend/resources；
- task/artifact/submission status。

需要这些字段的 Operation 必须读取 validated protocol，而不是从 plan 获取副本。

# Gate projection

- protocol unresolved item 为 INPUT_PREPARATION：受影响 run `input_gate_status=BLOCKED_BY_UNRESOLVED_ITEM`；
- ATTEMPT_SPECIFICATION：受影响 run `attempt_gate_status=BLOCKED_BY_UNRESOLVED_ITEM`；
- 无对应 unresolved item：READY；
- `blocking_item_ids` 保存引用，不复制 item description/value。

# 修订

protocol version、run-unit set、dependencies、scope/path projection 变化时生成新 plan version：

- 新 plan ID/path；
- `supersedes_plan_id` 指向旧 plan；
- `revision_reason` 非空；
- 旧 plan 和下游 artifacts 不覆盖。

backend/resource/attempt changes 不改变 protocol/run projection时，可以只新增 execution attempt spec，不要求 plan revision。

# 输出

```text
04_md_simulation/00_plan/
├── md_simulation_plan*.yaml
├── md_simulation_plan_materialization_report*.yaml
└── plan_materialization*.log
```

# Outcome codes

- `SIMULATION_PLAN_MATERIALIZED`；
- `SIMULATION_PLAN_MATERIALIZED_WITH_DEFERRED_GATES`；
- `VALIDATED_PROTOCOL_MISSING_OR_INVALID`；
- `SYSTEM_ARTIFACT_INVALID`；
- `PLAN_RUN_UNIT_OR_DAG_INVALID`；
- `PLAN_GATE_PROJECTION_INVALID`；
- `PLAN_PATH_CONFLICT`；
- `PLAN_REVISION_CHAIN_INVALID`；
- `PLAN_OUTPUT_CONFLICT`；
- `PLAN_MATERIALIZATION_INTERNAL_FAILURE`。

# 返回

成功时生成未验证 plan candidate，artifact candidates 为空；Validator 独立核验 projection。

# 自检

- [ ] protocol 已验证；
- [ ] plan 仅含静态 task projection；
- [ ] 科学参数未复制为第二 owner；
- [ ] runtime/status 未嵌入 immutable plan；
- [ ] gates 只引用 protocol unresolved items；
- [ ] DAG/paths/revision 已检查；
- [ ] 未创建 MD_INPUT/attempt/output；
- [ ] 未覆盖旧 plan或写管理目录。
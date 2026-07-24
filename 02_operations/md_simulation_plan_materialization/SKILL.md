---
name: md_simulation_plan_materialization
description: 根据不可变 simulation protocol spec、VALIDATED SYSTEM 谱系和已解决决定，在 04_md_simulation/00_plan/ 中生成一个新的 immutable md_simulation_plan。该 Operation 只物化明确方案，不选择默认 EM/平衡/生产流程，不生成 .tpr，也不执行模拟。
---

# 目标

把已明确的模拟协议转换为 `md_simulation_workflow` 可用于动态 route projection 的计划文件：

```text
simulation_protocol_spec.yaml
+ VALIDATED SYSTEM evidence
+ resolved decisions
→ md_simulation_plan.yaml candidate
```

计划描述 run units、依赖、MDP 身份、起始状态、输入准备要求、预期输出和完成标准，但不授权执行。

# 职责边界

负责：

- 读取 `subagent_task.schema.yaml` v2 task unit；
- 读取符合 Workflow 本地 schema 的 protocol spec；
- 核验 Workstream、SYSTEM artifact IDs、文件 hashes 和 resolved decision IDs；
- 保留明确 run unit 内容，不补充隐式科学默认值；
- 规范化稳定 ID、路径和依赖引用；
- 检查明显重复 ID、未知依赖、非法自依赖和输出路径冲突；
- 生成新的 immutable plan candidate 和 materialization report；
- 在修订时记录 `supersedes_plan_id` 和 revision reason；
- 返回 Operation result，随后交给专属 Validator。

不负责：

- 决定是否采用 EM、NVT、NPT 或 production；
- 根据“常规流程”生成缺失片段；
- 选择温度、压力、时间步长、步数、耦合、约束或完成阈值；
- 修改 `.mdp`、SYSTEM、拓扑或坐标；
- 运行 `grompp` 或 `mdrun`；
- 创建 MD_INPUT/MD_OUTPUT artifact；
- 写 Manager 状态或记录；
- 覆盖旧 plan；
- 自行宣布 plan 通过。

# 输入

必须作为：

```text
OPERATION_WITH_VALIDATOR
operation: md_simulation_plan_materialization
validator: md_simulation_plan_validator
```

运行。

任务必须提供：

- 唯一 `simulation_protocol_spec.yaml`；
- spec 所引用的 VALIDATED SYSTEM artifact sets 与文件记录；
- resolved decisions；
- 旧 plan 及其 hash，如为修订；
- 允许读写路径；
- plan、report、result data 和日志目标路径。

权威本地 schemas：

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
01_workflows/md_simulation_workflow/schemas/md_simulation_plan.schema.yaml
```

# Preflight

必须确认：

- task/workstream IDs 一致；
- protocol spec 可通过 schema 校验；
- spec 的 Workstream 与 task 一致；
- 所有 SYSTEM artifact IDs 存在且为 VALIDATED；
- MDP 和其他显式 file identities 可读且 hash 一致；
- resolved decision IDs 可由 task 追溯；
- `PLAN_VALIDATION` 类未决项为空；
- 输出路径位于 `04_md_simulation/00_plan/` 的授权范围；
- 新 plan 不覆盖已有文件；
- 修订时旧 plan 可定位且 `supersedes_plan_id` 正确。

任一 gate 不满足时返回 BLOCKED，不生成部分 plan。

# 物化规则

## Run unit 保真

对每个 run unit：

- 保留 `run_unit_id`、role、sequence、depends_on；
- 保留 MDP 路径、hash 和 source kind；
- 保留起始状态来源；
- 保留 `grompp` 参数和 `maxwarn`；
- 保留 execution policy 中已明确或显式 UNRESOLVED 的字段；
- 保留 expected outputs 和 completion criteria；
- 初始 `input_preparation_status` 为 `NOT_PREPARED`。

不得从名称推导参数。例如 `npt.1` 不能自动推导 pressure coupling。

## 依赖

Operation 执行确定性结构检查：

- ID 唯一；
- sequence 为正整数；
- `depends_on` 只引用 spec 内 run units；
- 禁止 self-dependency；
- 禁止明显循环依赖；
- `PRIOR_RUN_OUTPUT` 的 source run unit 必须存在；
- PRIOR_RUN_OUTPUT source 必须位于当前 run unit 的依赖闭包。

发现错误返回 BLOCKED，不自动修复。

## 未决项

- `PLAN_VALIDATION` 未决项阻塞 plan 生成；
- `INPUT_PREPARATION` 未决项可以保留，但相应 run unit 不可进入 input preparation；
- `EXECUTION` 未决项可以保留，但相应 run unit 不可进入 execution。

## 修订

新 plan 不覆盖旧 plan：

```text
md_simulation_plan.v1.yaml
md_simulation_plan.v2.yaml
```

具体命名由 task 明确。新 plan 必须记录：

- `supersedes_plan_id`；
- `revision_reason`；
- 新旧 protocol spec 与决定来源。

# 默认输出

```text
04_md_simulation/00_plan/
├── md_simulation_plan.yaml
├── md_simulation_plan_materialization_report.yaml
└── plan_materialization.log
```

文件名可由 task 指定，但不得覆盖旧版本。

# 执行流程

1. 解析 task、权限和 detail paths；
2. schema-validate protocol spec；
3. 核验 SYSTEM、MDP、旧 plan 和 decision provenance；
4. 检查 run unit IDs、依赖和路径冲突；
5. 确认未决项分层；
6. 在临时路径生成 plan 和 report；
7. 重新读取并 schema-validate plan candidate；
8. 核验 protocol spec 与 plan 的字段保真；
9. 原子提交候选文件；
10. 返回 Operation result，随后由专属 Validator 独立核验。

# Outcome codes

- `SIMULATION_PLAN_MATERIALIZED`；
- `SIMULATION_PLAN_MATERIALIZED_WITH_EXECUTION_UNRESOLVED`；
- `PROTOCOL_SPEC_MISSING_OR_INVALID`；
- `SYSTEM_ARTIFACT_INVALID`；
- `PROTOCOL_SOURCE_HASH_MISMATCH`；
- `PLAN_VALIDATION_ITEM_UNRESOLVED`；
- `RUN_UNIT_ID_OR_DEPENDENCY_INVALID`；
- `START_STATE_REFERENCE_INVALID`；
- `PLAN_OUTPUT_CONFLICT`；
- `PLAN_MATERIALIZATION_INTERNAL_FAILURE`。

# 返回

成功时：

- plan 和 report 作为 created files；
- 不创建 MD_INPUT artifact candidate；
- plan 仍为未验证业务候选；
- `operation_result` 与后续 `validation_result` 分开。

需要用户决定时返回 `confirmation_items`，不得直接提问。

# 自检

- [ ] protocol spec 是结构化不可变输入；
- [ ] 没有补充隐式科学默认值；
- [ ] SYSTEM artifact 已验证；
- [ ] run unit IDs 和依赖可解析；
- [ ] MDP identities 和 hashes 保持；
- [ ] 未决项按 barrier 分层；
- [ ] 修订未覆盖旧 plan；
- [ ] 未生成 `.tpr` 或执行模拟；
- [ ] 未写管理目录；
- [ ] 未自行宣布 plan 通过。
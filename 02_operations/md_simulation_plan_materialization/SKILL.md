---
name: md_simulation_plan_materialization
description: 根据已验证且不可变的 simulation protocol spec、VALIDATED SYSTEM 谱系和 protocol validation evidence，在 04_md_simulation/00_plan/ 中生成新的 immutable md_simulation_plan。该 Operation 只物化明确方案，不补充默认模拟步骤、不生成 TPR，也不执行模拟。
---

# 目标

```text
VALIDATED simulation_protocol_spec
+ protocol validation report
+ VALIDATED SYSTEM
→ md_simulation_plan.yaml candidate
→ md_simulation_plan_validator
```

plan 描述 run units、DAG、MDP identities、start states、输入准备要求、预期输出和完成标准，但不授权执行。

# 职责边界

负责：

- 读取共享 task 和 Workflow 本地 schemas；
- 核验 protocol spec 已由 `md_simulation_protocol_validator` 通过；
- 核验 Workstream、SYSTEM、MDP、field provenance 和 decision IDs；
- 逐字段保真物化 run units，不增加科学内容；
- 规范化稳定 ID、路径和依赖引用；
- 检查重复 ID、未知依赖、自依赖、循环和路径冲突；
- 生成 immutable plan candidate 和 report；
- 修订时记录 supersedes 和 reason；
- 返回 Operation result，交给专属 Validator。

不负责：

- 直接解析自然语言决定；
- 接受未验证 protocol spec；
- 决定 EM/NVT/NPT/production 是否存在；
- 选择温度、压力、步数、耦合、约束、maxwarn 或 threshold；
- 修改 protocol、MDP、SYSTEM、topology 或 coordinates；
- 运行 grompp/mdrun；
- 创建 MD_INPUT/MD_OUTPUT artifact；
- 写管理目录、覆盖旧 plan 或自行宣布通过。

# 输入

组合 task：

```text
operation: md_simulation_plan_materialization
validator: md_simulation_plan_validator
mode: OPERATION_WITH_VALIDATOR
```

任务必须提供：

- validated `simulation_protocol_spec.yaml`；
- protocol validation report/result；
- spec 引用的 VALIDATED SYSTEM records；
- spec 引用的 MDP/template files；
- resolved decisions 摘要；
- 旧 plan，如为 revision；
- allowed read/write、forbidden paths 和 detail paths。

Schemas：

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
01_workflows/md_simulation_workflow/schemas/md_simulation_plan.schema.yaml
```

# Preflight

必须确认：

- task/workstream IDs 一致；
- protocol spec schema 有效且 hash 与 validation report 一致；
- protocol Validator outcome 为：
  - `SIMULATION_PROTOCOL_VALIDATED`；或
  - `SIMULATION_PROTOCOL_VALIDATED_WITH_DEFERRED_ITEMS`，且无 PLAN_VALIDATION 项；
- spec 未被 superseded/invalidated；
- field provenance 完整；
- SYSTEM artifact IDs 存在且为 VALIDATED；
- MDP/files 可读且 hashes 一致；
- decisions 可追溯；
- PLAN_VALIDATION unresolved items 为空；
- output path 受授权且不覆盖旧 plan；
- revision 的旧 plan 和 supersedes identity 正确。

任一 gate 不满足时 BLOCKED，不生成部分 plan。

# 物化规则

对每个 run unit原样保留：

- ID、role、sequence、depends_on；
- work directory；
- MDP path/hash/source kind；
- start state；
- grompp executable/version/maxwarn/argv；
- execution policy 中明确或 UNRESOLVED 的字段；
- expected outputs/completion criteria；
- unresolved affected field paths。

初始 `input_preparation_status` 为 `NOT_PREPARED`。不得从 `npt.1` 等名称推导参数。

依赖检查：

- IDs 唯一；
- references 存在；
- 无 self-dependency/cycle；
- PRIOR_RUN_OUTPUT source 存在且位于 dependency closure；
- work directories 唯一且不使用管理路径。

未决项：

- PLAN_VALIDATION：阻塞；
- INPUT_PREPARATION：保留并阻塞对应 input task；
- EXECUTION：保留并阻塞对应 execution task。

修订生成新文件和 plan ID，记录 `supersedes_plan_id` 与 `revision_reason`，不覆盖旧 plan。

# 默认输出

```text
04_md_simulation/00_plan/
├── md_simulation_plan.yaml
├── md_simulation_plan_materialization_report.yaml
└── plan_materialization.log
```

# 执行流程

1. 解析 task 和权限；
2. schema-validate protocol；
3. 核验 protocol validation evidence；
4. 核验 SYSTEM、MDP、provenance 和 revision inputs；
5. 检查 DAG、未决项和路径；
6. 临时生成 plan/report；
7. schema-validate plan candidate；
8. 比较 protocol-to-plan 字段保真；
9. 原子提交；
10. 返回 Operation result并进入专属 Validator。

# Outcome codes

- `SIMULATION_PLAN_MATERIALIZED`；
- `SIMULATION_PLAN_MATERIALIZED_WITH_EXECUTION_UNRESOLVED`；
- `PROTOCOL_SPEC_MISSING_OR_INVALID`；
- `PROTOCOL_SPEC_NOT_VALIDATED`；
- `PROTOCOL_FIELD_PROVENANCE_INCOMPLETE`；
- `SYSTEM_ARTIFACT_INVALID`；
- `PROTOCOL_SOURCE_HASH_MISMATCH`；
- `PLAN_VALIDATION_ITEM_UNRESOLVED`；
- `RUN_UNIT_ID_OR_DEPENDENCY_INVALID`；
- `START_STATE_REFERENCE_INVALID`；
- `PLAN_OUTPUT_CONFLICT`；
- `PLAN_MATERIALIZATION_INTERNAL_FAILURE`。

# 返回与自检

成功时只创建 plan/report，不创建 MD_INPUT artifact。plan candidate 仍未验证。

- [ ] protocol 已由专属 Validator 通过；
- [ ] 未直接解析自然语言或增加默认科学内容；
- [ ] field provenance/SYSTEM/MDP hashes 可追溯；
- [ ] DAG 和未决项正确；
- [ ] revision 未覆盖旧 plan；
- [ ] 未生成 TPR 或执行模拟；
- [ ] 未写管理目录；
- [ ] 未自行宣布 plan 通过。
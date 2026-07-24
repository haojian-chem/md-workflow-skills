---
name: md_simulation_plan_validator
description: 独立核验 md_simulation_plan_materialization 生成的计划候选，确认其与 protocol spec、VALIDATED SYSTEM、resolved decisions、run unit DAG、MDP identities 和修订谱系一致。该 Validator 不修改计划、不补充科学参数，也不生成 MD_INPUT。
---

# 目标

验证 `md_simulation_plan` 是否可以作为本阶段动态 route projection 和逐 run input preparation 的权威局部计划。

通过只表示：

- plan 准确物化已明确协议；
- run unit DAG、来源和未决项分层一致；
- plan 可安全用于后续 input preparation gate。

不表示：

- `.mdp` 科学设置一定合理；
- SYSTEM 已适合所有计划运行；
- `.tpr` 已生成；
- 模拟或分析已完成。

# 职责边界

负责：

- 读取 protocol spec、SYSTEM artifact records、旧 plan 和 plan candidate；
- 独立重算 expected run unit set 和依赖图；
- 核验所有字段保真、文件 identities、decision provenance 和未决项；
- 检查 DAG、work directory、start-state source 和 revision chain；
- 返回 Validation result、详细 report 和 gate 建议。

不负责：

- 修改或重写 plan；
- 根据经验补充缺失 run units 或参数；
- 修改 `.mdp`；
- 运行 `grompp`/`mdrun`；
- 接受或替换 SYSTEM artifact；
- 写管理目录；
- 自动重试 Operation。

# 输入

作为 `OPERATION_WITH_VALIDATOR` 的 validator 部分，必须接收：

- 同一 task 的 Operation result；
- `simulation_protocol_spec.yaml`；
- plan candidate；
- materialization report；
- VALIDATED SYSTEM artifact records；
- resolved decisions；
- old plan，如为 revision；
- allowed read/write 与 forbidden paths；
- Validator report/result data 路径。

Operation 未产生完整 plan candidate 时返回 BLOCKED 或 FAILED，不推测缺失内容。

# Preflight

确认：

- task mode 和 Operation/Validator refs 正确；
- task/workstream IDs 一致；
- Operation status 为 DONE；
- protocol spec 和 plan 可通过各自 schema；
- required files 可读、非 symlink 且 hashes 一致；
- SYSTEM artifact 为 VALIDATED；
- Validator 不以 plan、spec、SYSTEM 或旧 plan 为写入目标；
- 管理目录位于 forbidden paths。

# 独立检查

## 1. Spec-to-plan 保真

从 protocol spec 独立计算 expected：

- SYSTEM artifact IDs；
- run unit ID set；
- role、sequence、depends_on；
- work directories；
- MDP identities；
- start-state sources；
- grompp settings；
- execution policy；
- expected outputs；
- completion criteria；
- resolved decisions 和 unresolved items。

不得信任 materialization report 自报列表。

## 2. DAG

必须检查：

- ID 唯一；
- dependency references 全部存在；
- 无 self-dependency；
- 无循环；
- sequence 与依赖不存在反向矛盾；
- PRIOR_RUN_OUTPUT source 存在并位于依赖闭包；
- SYSTEM source 不引用 source run unit。

## 3. 文件与 provenance

- protocol spec hash 与 plan 记录一致；
- MDP hash 与实际文件一致；
- SYSTEM artifact IDs 与 task/records 一致；
- resolved decision IDs 全部可追溯；
- 不存在 plan 中新增但 spec 未声明的科学参数；
- source files 未被修改。

## 4. 未决项 barrier

- 任一 `PLAN_VALIDATION` 未决项存在时，plan 不通过；
- `INPUT_PREPARATION` 未决项必须绑定到明确影响对象或类别，并阻止相应 input preparation；
- `EXECUTION` 未决项可保留，但必须在执行前阻断；
- 不允许通过将科学参数伪装成 execution-only 未决项绕过 plan gate。

## 5. 修订谱系

若为新版本：

- `supersedes_plan_id` 必须指向提供的旧 plan；
- `revision_reason` 非空；
- 旧 plan hash 不变；
- 新 plan 使用新路径/identity；
- 已有下游 MD_INPUT/MD_OUTPUT 不被覆盖。

首版 plan 的 `supersedes_plan_id` 和 `revision_reason` 可以为 null。

## 6. 路径

- `00_plan/` 中计划路径属于当前 Workstream；
- 每个 run unit work directory 唯一；
- 不与 `00_plan/`、`99_validation/` 或其他 run unit 冲突；
- 不使用 `00_project_state/**` 或 `00_project_records/**` 作为业务输出路径。

# Gate outcomes

- `SIMULATION_PLAN_VALIDATED`；
- `SIMULATION_PLAN_VALIDATED_WITH_EXECUTION_UNRESOLVED`；
- `PLAN_SPEC_MISMATCH`；
- `PLAN_DAG_INVALID`；
- `PLAN_START_STATE_INVALID`；
- `PLAN_SOURCE_OR_HASH_MISMATCH`；
- `PLAN_DECISION_PROVENANCE_MISMATCH`；
- `PLAN_UNRESOLVED_ITEM_MISCLASSIFIED`；
- `PLAN_REVISION_CHAIN_INVALID`；
- `PLAN_PATH_CONFLICT`；
- `PLAN_VALIDATOR_INPUT_INCOMPLETE`；
- `PLAN_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可以建议 Workflow 使用该 plan。

# 输出

默认：

```text
04_md_simulation/00_plan/
├── md_simulation_plan_validation_report.yaml
└── md_simulation_plan_validation_result.yaml
```

Validation result 必须：

- 与 Operation result 分开；
- 列出 validated files；
- 记录 unresolved execution items；
- 给出 `input_preparation_allowed_run_unit_ids`；
- 不创建 MD_INPUT artifact；
- 不将 plan 描述为最终模拟 artifact。

# 失败处理

- 输入不完整：BLOCKED；
- plan 可解析但不符合 spec/gate：Validator 执行 DONE，但 outcome 不通过；
- parser/internal error：FAILED；
- 不修改 plan，不自动重跑；
- 保留详细 differences report。

# 自检

- [ ] expected plan 从 spec 独立重算；
- [ ] 未信任 Operation report 自报；
- [ ] DAG、start-state 和 sequence 已检查；
- [ ] 文件 hashes 和 SYSTEM provenance 一致；
- [ ] 未决项 barrier 分类正确；
- [ ] revision 未覆盖旧 plan；
- [ ] 未补充科学参数；
- [ ] 未生成 MD_INPUT；
- [ ] 未修改被验证对象；
- [ ] 未写管理目录。
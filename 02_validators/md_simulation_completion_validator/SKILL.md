---
name: md_simulation_completion_validator
description: 在 md_simulation_workflow 的请求范围或阶段出口处，核验 required run units、依赖、submission terminal states、run-level output validation 和 MD_OUTPUT 谱系是否完整闭合。该 Validator 不重新运行单个输出的全部检查，不修改模拟结果，也不判断采样是否科学收敛。
---

# 目标

确认一个明确的 MD simulation route scope 已完成并可交付：

- 范围内 required run units 全部可唯一定位；
- 依赖顺序闭合；
- 每个 required run unit 均有通过的 output validation evidence；
- 不存在活动、未知或已结束未核验的相关 submission；
- 最终 MD_OUTPUT artifact 及其输入/续跑谱系连续；
- 阶段出口可以交给 `analysis_workflow`。

# 职责边界

负责：

- 读取 active route 的 MD simulation 范围；
- 读取 run unit IDs、依赖关系和完成要求；
- 读取 submission records、run-level validation reports 和 artifact sets；
- 核验 required run units 和边界条件；
- 核验最终输出身份和 lineage；
- 写 completion report；
- 返回阶段 gate 建议。

不负责：

- 修改任何 run unit 输出；
- 重新提交、续跑或恢复任务；
- 替代 `md_run_output_validator` 解析全部轨迹和能量文件；
- 根据目录存在推断 run unit 完成；
- 新增 run unit 或改变路线范围；
- 判断采样充分性、科学收敛或分析结论；
- 修改 route、submission、artifact 或 Workstream records；
- 写管理目录；
- 创建子 Agent 或直接向用户提问。

# 输入

必须接收 `subagent_task.schema.yaml` v2 的 `VALIDATOR` task unit：

```text
operation: null
validator: md_simulation_completion_validator
```

任务必须提供：

- Focus Workstream ID；
- 当前 active route ID 和本 Workflow 请求范围；
- 范围内 run unit IDs、roles、sequence 和 dependencies；
- 相关 execution task/results；
- 相关 submission records；
- 各 run unit output validation reports/results；
- 当前 MD_INPUT、MD_OUTPUT artifact sets；
- resolved decisions；
- allowed read/write 和 forbidden paths；
- completion report/result data 路径。

缺少明确范围时返回 BLOCKED，不默认核验整个 `04_md_simulation/`。

# Preflight

确认：

1. task 和 Focus Workstream 一致；
2. route scope 已解析且包含明确终点；
3. run unit IDs 在范围内唯一；
4. 依赖图可解析且无环；
5. submission、validation 和 artifact records 可按 run unit 对齐；
6. 所有引用的结构化记录符合共享 contracts；
7. completion report 输出路径位于 allowed write paths；
8. 所有被验证业务文件只读；
9. 管理目录位于 forbidden paths。

# 核验规则

## 1. Scope closure

根据 route scope 独立确定：

- 范围内 required run units；
- 用户明确停止点；
- 是否要求 Workflow exit；
- 哪些 conditional run units 已由有效 evidence SKIP；
- 哪些 run units 不属于本次 completion gate。

不得扫描目录后把额外 run units 自动纳入范围。

## 2. Dependency closure

对每个 required run unit：

- `depends_on` 全部存在；
- 依赖位于当前范围内，或作为入口 artifact 明确满足；
- 依赖对应 MD_OUTPUT 已通过；
- continuation chain 的 checkpoint 和前置 output lineage 可追溯；
- 不存在循环依赖或悬空依赖。

## 3. Submission closure

范围内不得存在：

```text
PREPARED
SUBMITTED
RUNNING
FINISHED_UNVERIFIED
UNKNOWN
```

作为当前 required run unit 的未闭合 submission。

`FAILED | CANCELLED` submission 只有在：

- 对应 run unit 已由后续有效 execution supersede；
- replacement lineage 明确；
- active route 和 resolved decision 接受该替代；

时才不阻止完成。

## 4. Run-level validation closure

每个 required run unit 必须有：

- 对应 `md_run_output_validator` 的通过 outcome；
- 可定位的 validation report；
- 与当前 execution spec、task、submission 和 output files 一致的 hashes/provenance；
- 已由 Manager 登记的 VALIDATED MD_OUTPUT artifact set，或本 task 明确允许核验的候选闭环。

旧 run unit 的通过报告不得替代当前 superseding execution。

## 5. Artifact lineage

核验：

- 最终 MD_OUTPUT 派生自正确 MD_INPUT；
- 分段模拟的前后 checkpoint/structure lineage 连续；
- 被 supersede 或 invalidated artifact 没有作为最终出口；
- required files 和 run-level reports 均属于当前 Workstream；
- 最终 artifact identity 唯一。

## 6. Exit readiness

当终点为 Workflow exit 时，必须明确一个可供 analysis 使用的最终 MD_OUTPUT artifact。

当终点只是指定 run unit 或 gate 时，只核验该范围完成，不宣称整个 Workflow 完成。

# Outcome codes

- `MD_SIMULATION_SCOPE_COMPLETED`；
- `MD_SIMULATION_WORKFLOW_COMPLETED`；
- `COMPLETION_SCOPE_UNRESOLVED`；
- `RUN_UNIT_SET_MISMATCH`；
- `RUN_UNIT_DEPENDENCY_INVALID`；
- `ACTIVE_OR_UNVERIFIED_SUBMISSION_REMAINS`；
- `REQUIRED_RUN_UNIT_NOT_VALIDATED`；
- `FAILED_OR_CANCELLED_RUN_UNRESOLVED`；
- `MD_OUTPUT_LINEAGE_INCOMPLETE`；
- `FINAL_MD_OUTPUT_NOT_UNIQUE`；
- `COMPLETION_RECORD_MISMATCH`；
- `COMPLETION_VALIDATOR_INTERNAL_FAILURE`。

# 通过条件

## 范围完成

`MD_SIMULATION_SCOPE_COMPLETED`：

- 用户指定范围内 required run units 全部闭合；
- 指定终点已达到；
- 不表示本 Workflow 其余 run units 已完成。

## Workflow 完成

`MD_SIMULATION_WORKFLOW_COMPLETED`：

- route 终点为 Workflow exit；
- 全部 required run units 闭合；
- 所有相关 submission terminal 且已验证；
- 最终 VALIDATED MD_OUTPUT 唯一；
- 可以交给 `analysis_workflow`。

# 技术完成边界

completion 通过只证明：

- 路线范围已按声明执行；
- 模拟任务、submission、输出验证和 artifact 谱系闭合；
- 技术出口完整。

不证明：

- 采样充分；
- 轨迹收敛；
- equilibration scientifically sufficient；
- 后续分析指标有效；
- 科学结论成立。

# 输出

默认：

```text
04_md_simulation/99_validation/
├── md_simulation_completion_report.yaml
└── md_simulation_completion_validation.log
```

completion report 至少记录：

- task/workstream/route IDs；
- scope start/end；
- required、skipped 和 out-of-scope run units；
- dependency closure；
- submission closure；
- run-level validation references；
- MD_INPUT/MD_OUTPUT lineage；
- final MD_OUTPUT identity；
- unresolved items；
- warnings；
- outcome code 和 gate recommendation。

# 返回

返回符合：

```text
03_contracts/subagent_result.schema.yaml
```

的独立 `validation_result`。

- 不创建新的 engine output；
- `artifact_candidates` 通常为空；
- 若输入是尚未由 Manager 登记但已完成 run-level validation 的候选集合，只能引用候选并建议 Manager 完成记录闭环，不重复创建不同 artifact candidate；
- 不修改任何共享记录。

# 失败处理

- 范围或记录不明确：BLOCKED；
- Validator 成功发现 gate 不通过：DONE + 具体不通过 outcome；
- 实现异常：FAILED；
- 不自动重跑、续跑、删除或改 route；
- 需要新运行时返回 route revision recommendation。

# 自检

- [ ] completion scope 来自 active route，不是目录扫描；
- [ ] required/conditional/skipped run units 已区分；
- [ ] dependencies 无环且全部闭合；
- [ ] 没有 active、UNKNOWN 或 FINISHED_UNVERIFIED submission；
- [ ] 每个 required run unit 有当前有效 output validation；
- [ ] failed/cancelled execution 的替代 lineage 已明确；
- [ ] 最终 MD_OUTPUT 唯一且未失效；
- [ ] 范围完成没有被误写为 Workflow 完成；
- [ ] 技术完成没有被夸大为科学收敛；
- [ ] 没有修改业务对象或管理目录。
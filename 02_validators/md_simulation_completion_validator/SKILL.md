---
name: md_simulation_completion_validator
description: 在 md_simulation_workflow 的请求范围或阶段出口处，核验 validated protocol/plan、required run units、MD_INPUT、execution attempts、submission terminal states、run-level MD_OUTPUT 和唯一 validated stage-level MD_OUTPUT collection 是否完整闭合。该 Validator 不组装输出，也不判断科学收敛。
---

# 目标

确认一个明确 MD simulation route scope 已完成：

- validated protocol/plan 与 active route 一致；
- required run units 和依赖闭合；
- 每个 required run unit 有 VALIDATED MD_INPUT；
- attempts/submissions 无活动、未知或未核验状态；
- 每个 required run unit 有 VALIDATED run-level MD_OUTPUT；
- Workflow exit 时存在唯一 VALIDATED stage-level MD_OUTPUT collection；
- stage manifest 覆盖全部 required run outputs；
- 可以交给 `analysis_workflow`。

# 职责边界

负责：

- 读取 route scope、validated protocol/plan；
- 读取 MD_INPUT、attempt、submission、run-level output evidence；
- 读取 stage output manifest、Validator result 和 artifact record；
- 核验 scope、dependency、input、attempt、submission、run-output、stage-output 和 lineage closure；
- 写 completion report；
- 返回 gate 建议。

不得：

- 创建或修改 protocol、plan、MDP、TPR、attempt 或 output；
- 重新组装 stage manifest；
- 重新执行底层 parser 的全部检查；
- 重新提交、续跑或恢复；
- 根据目录存在自动加入 run units；
- 判断采样充分、科学收敛或分析结论；
- 修改 route/submission/artifact/Workstream records；
- 写管理目录。

# 输入

必须接收 VALIDATOR task unit，并提供：

- Focus Workstream、active route 和明确 scope；
- validated protocol/plan 及 evidence；
- required/skipped/out-of-scope run units；
- 每个 run unit 的 MD_INPUT validation/artifact；
- execution-attempt specs/results/submissions/status；
- run-level output validation/artifacts/manifests；
- stage output assembly/validation evidence；
- stage-level MD_OUTPUT artifact record；
- resolved decisions；
- allowed read/write、forbidden paths 和 report targets。

缺少明确 scope 或 validated plan 时 BLOCKED。

# Preflight

确认：

1. task 与 Focus Workstream 一致；
2. route scope 和终点明确；
3. protocol/plan 已验证、未失效且与 route 对齐；
4. required run units 可映射到 plan；
5. MD_INPUT/attempt/submission/run-output records 可按 run unit 对齐；
6. stage output manifest/artifact/validation 可唯一定位；
7. 引用的 runtime records 符合共享 contracts；
8. report 输出路径受授权；
9. 被验证业务文件只读；
10. 管理目录禁止写入。

# 核验规则

## Scope/plan closure

- 从 active route 计算 required/skipped/out-of-scope run units；
- route projection 与 validated plan 一致；
- route 不引用 superseded plan；
- 不扫描目录加入额外 runs。

## Dependency closure

对每个 required run unit：

- dependencies 存在且无环；
- upstream run-level MD_OUTPUT 已 VALIDATED；
- PRIOR_RUN_OUTPUT source 位于依赖闭包；
- start-state lineage 连续。

## MD_INPUT closure

每个 required run unit 必须有当前 protocol/plan 对应的 VALIDATED MD_INPUT、input manifest 和 Validator evidence。

## Execution-attempt closure

范围内不得存在：

```text
PREPARED | SUBMITTED | RUNNING | FINISHED_UNVERIFIED | UNKNOWN
```

作为未闭合 current attempt。

failed/cancelled/superseded attempts 必须具有明确 replacement/exclusion lineage。每个 accepted attempt 必须有 validated execution spec 和 terminal evidence。

## Run-level output closure

每个 required run unit 必须有：

- 当前 `md_run_output_validator` 通过 outcome；
- run output manifest；
- VALIDATED run-level MD_OUTPUT artifact；
- accepted attempt chain provenance。

## Stage-level output closure

Workflow exit 必须有唯一：

```text
VALIDATED stage-level MD_OUTPUT artifact
```

该 artifact 必须：

- 由 `md_simulation_output_validator` 通过；
- 文件包含 stage output manifest/validation report；
- `derived_from_artifact_set_ids` 精确覆盖 required run-level outputs；
- manifest included run set 与 scope 一致；
- segmented production 不丢失早期 required segments；
- final structure/checkpoint selection 有效；
- 未失效或 superseded。

指定中间 gate 终点时，可以只做 scope completion，不要求 stage-level output。

## Full lineage

```text
VALIDATED SYSTEM
→ validated protocol
→ validated plan
→ per-run VALIDATED MD_INPUT
→ validated execution attempts
→ per-run VALIDATED MD_OUTPUT
→ validated stage-level MD_OUTPUT
```

# Outcome codes

- `MD_SIMULATION_SCOPE_COMPLETED`；
- `MD_SIMULATION_WORKFLOW_COMPLETED`；
- `COMPLETION_SCOPE_UNRESOLVED`；
- `SIMULATION_PROTOCOL_OR_PLAN_MISSING_OR_STALE`；
- `ROUTE_PLAN_MISMATCH`；
- `RUN_UNIT_SET_OR_DEPENDENCY_INVALID`；
- `REQUIRED_MD_INPUT_NOT_VALIDATED`；
- `ACTIVE_OR_UNVERIFIED_ATTEMPT_REMAINS`；
- `REQUIRED_RUN_OUTPUT_NOT_VALIDATED`；
- `STAGE_MD_OUTPUT_MISSING_OR_NOT_VALIDATED`；
- `STAGE_MD_OUTPUT_SCOPE_OR_LINEAGE_INVALID`；
- `FAILED_OR_CANCELLED_ATTEMPT_UNRESOLVED`；
- `COMPLETION_RECORD_MISMATCH`；
- `COMPLETION_VALIDATOR_INTERNAL_FAILURE`。

# 通过条件

## Scope completion

只要求用户指定范围内 protocol/plan/input/attempt/run-output gates 闭合，不宣称整个 Workflow 完成。

## Workflow completion

必须同时满足：

- route 终点为 Workflow exit；
- validated protocol/plan 覆盖完整范围；
- required MD_INPUT 和 run-level MD_OUTPUT 全部闭合；
- attempts/submissions terminal 且已核验；
- stage-level VALIDATED MD_OUTPUT 唯一；
- stage manifest 覆盖完整 required scope；
- 可以交给 analysis。

# 输出

```text
04_md_simulation/99_validation/
├── md_simulation_completion_report.yaml
└── md_simulation_completion_validation.log
```

completion Validator 不返回新的 artifact candidate；它引用已登记的 stage-level MD_OUTPUT。

# 技术边界

通过只证明 route、protocol/plan、input、attempt、submission 和 output artifact 技术闭合，不证明平衡充分、采样收敛或科学结论成立。

# 自检

- [ ] scope 来自 active route；
- [ ] protocol/plan 唯一且未失效；
- [ ] required run dependencies 闭合；
- [ ] 每个 required run 有 VALIDATED MD_INPUT；
- [ ] 没有 active/UNKNOWN/FINISHED_UNVERIFIED attempt；
- [ ] 每个 required run 有 VALIDATED run-level MD_OUTPUT；
- [ ] Workflow exit 有唯一 validated stage-level MDOUTPUT；
- [ ] segmented production 的 required segments 全部 included；
- [ ] completion 未承担 output assembly；
- [ ] 技术完成未夸大为科学收敛；
- [ ] 未修改业务对象或管理目录。
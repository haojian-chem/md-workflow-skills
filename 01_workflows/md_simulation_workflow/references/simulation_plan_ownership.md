# MD Simulation Protocol and Plan Ownership

## 1. 阶段边界

```text
md_preparation_workflow
→ VALIDATED SYSTEM
→ md_simulation_workflow
→ validated scientific protocol
→ validated task-projection plan
→ per-run VALIDATED MD_INPUT
→ validated execution attempts
→ per-run VALIDATED MD_OUTPUT
→ stage-level VALIDATED MD_OUTPUT collection
```

只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子变化时才返回 `md_preparation_workflow`。

## 2. 对象 owner

| 对象 | 唯一 owner | 内容 |
|---|---|---|
| scientific simulation protocol | `md_simulation_workflow` | 科学 run units、MDP specification、start states、completion criteria、field provenance |
| simulation task-projection plan | `md_simulation_workflow` | run-unit DAG projection、业务路径、input/attempt gates、revision lineage |
| Workstream route | Manager | 当前请求的 task-unit start/end/order/stop conditions |
| execution-attempt spec | `md_execution_attempt_specification` | attempt identity、backend、resources、runtime、restart 和 prepared submission identity |
| run-level MD_OUTPUT | `md_run_output_validator` | accepted attempt chain 的有效输出集合 |
| stage-level MDOUTPUT | `md_simulation_output_assembly` + Validator | scope 内 required run outputs 的唯一 collection |
| runtime state/records | Manager | task、submission、artifact、route、Workstream state |

这些对象不得互相替代。

## 3. Scientific protocol

由：

```text
md_simulation_protocol_specification
→ md_simulation_protocol_validator
```

生成/验证。

protocol 是科学字段唯一 owner，描述：

- run-unit IDs 和科学 roles；
- dependencies；
- MDP final file 或 template+typed overrides；
- SYSTEM/prior-run start states；
- preprocessing policy；
- expected output roles；
- completion mode/targets/checks；
- field provenance；
- unresolved items。

protocol 不描述：

- GROMACS executable path/version；
- execution mode/backend/host/session/queue；
- MPI/OMP/GPU/memory/walltime；
- attempt ID；
- retry/continuation parent；
- append/noappend；
- submission ID。

runtime 环境变化不应自动制造 scientific protocol revision。

## 4. Task-projection plan

由：

```text
md_simulation_plan_materialization
→ md_simulation_plan_validator
```

从 validated protocol 派生。

plan 只描述：

- protocol identity；
- run-unit projection；
- dependency/start-state logical projection；
- run/input/attempts business directories；
- INPUT_PREPARATION/ATTEMPT_SPECIFICATION gate projection；
- plan revision lineage。

plan 不复制拥有 MDP、completion criteria 或 runtime configuration，也不保存 `RUNNING/VALIDATED` 等状态。实际进度属于 Workstream/task/artifact records。

## 5. Workstream route

Manager 根据 Workflow fragment 和 validated plan 持久化 route：

- start/end/stop conditions；
- 预计 task units；
- 当前 attempt steps；
- route revision lineage。

plan 是静态 projection，route 是当前请求的执行路径。retry/continuation attempt 出现时可修订 route，而不必修改 scientific protocol/plan。

## 6. MDP 与 MD_INPUT

protocol 中 MDP source：

```text
FINAL_FILE
TEMPLATE_WITH_TYPED_OVERRIDES
```

`md_run_input_preparation`：

- FINAL_FILE：原样复制/引用；
- TEMPLATE：执行 exact parameter replacement；
- 运行一次 grompp；
- 生成 rendered `run.mdp`、TPR、manifest 和 evidence。

`md_run_input_validator` 独立核验 rendered MDP、TPR 和 source provenance。

GROMACS executable 是 runtime evidence，不写回 protocol。

## 7. Execution attempt

```text
VALIDATED MD_INPUT
→ md_execution_attempt_specification
→ md_execution_attempt_validator
→ md_run_execution
```

attempt 表示一次具体运行/提交：

```text
FRESH
RETRY_SAME_INPUT
CONTINUE_NOAPPEND
```

v1 不启用 APPEND。

same-TPR continuation 产生新 attempt，不产生 `CONTINUATION` scientific role。改变 MDP/TPR/科学目标时产生新的或 superseding run unit。

## 8. Output ownership

### Run-level MDOUTPUT

`md_run_output_validator` 重建 accepted attempt chain，生成 run output manifest 和 run-level MDOUTPUT artifact candidate。

失败、取消、superseded attempts 保留审计 evidence，但不进入有效 artifact。

### Stage-level MDOUTPUT

`md_simulation_output_assembly` 组装 collection manifest；专属 Validator 返回唯一 stage-level MDOUTPUT artifact candidate。

collection 引用所有 required run-level artifact IDs，不复制或拼接 trajectory/energy 文件。segmented production 不得只保留最后一个 segment。

completion Validator 只核验闭环，不承担 output assembly。

## 9. 修订规则

### 新 scientific protocol/plan

- run-unit set/dependencies 变化；
- MDP source/override/科学参数变化；
- start-state 变化；
- completion criteria 变化；
- 新 TPR 所代表的科学片段变化。

### 只需新 execution attempt spec

- backend/host/queue/resource 变化；
- runtime executable/profile 变化；
- same-input retry；
- same-TPR NOAPPEND continuation。

### 返回 md_preparation

仅 SYSTEM structure/topology/box/solvent/ions 变化。

## 10. 默认目录

```text
04_md_simulation/
├── 00_plan/
│   ├── simulation_protocol_spec*.yaml
│   ├── md_simulation_plan*.yaml
│   └── validation reports
├── <run_unit_id>/
│   ├── input/
│   │   ├── run.mdp
│   │   ├── run.tpr
│   │   └── input manifests/reports
│   ├── attempts/
│   │   ├── attempt.001/
│   │   ├── attempt.002/
│   │   └── ...
│   ├── md_run_output_manifest.yaml
│   └── md_run_output_validation_report.yaml
└── 99_validation/
    ├── md_simulation_output_manifest.yaml
    ├── md_simulation_output_validation_report.yaml
    └── md_simulation_completion_report.yaml
```

目录存在不构成完成证据。

## 11. 本地接口

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
01_workflows/md_simulation_workflow/schemas/md_simulation_plan.schema.yaml
02_operations/md_execution_attempt_specification/schemas/md_execution_attempt_spec.schema.yaml
02_validators/md_run_output_validator/schemas/md_run_output_manifest.schema.yaml
02_operations/md_simulation_output_assembly/schemas/md_simulation_output_manifest.schema.yaml
```

这些是阶段局部接口，不替代共享 runtime contracts。
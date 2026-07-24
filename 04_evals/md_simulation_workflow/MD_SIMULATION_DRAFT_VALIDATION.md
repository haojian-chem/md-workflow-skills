# MD Simulation Skills Draft Validation

## Status

```yaml
status: REVIEW_REQUIRED
branch: draft/md-simulation-skills
scope: md_simulation workflow contract draft
runtime_ready: false
```

本记录只确认第一轮职责、接口、schema 和行为 fixtures 已建立，不表示 GROMACS、tmux 或调度系统执行实现已经通过。

## 已做过

- 读取并对齐 `AGENTS.md`、authoring Skill、四层边界、runtime subagent protocol、route planning protocol、deterministic tool protocol；
- 读取并对齐 `workflow_route_fragment`、`workflow_decision`、`subagent_task`、`subagent_result`、`submission_record` 和 `artifact_set` contracts；
- 将 MD 模拟阶段定义为动态 run unit 序列，而非固定 EM/NVT/NPT/production 队列；
- 将单个 run unit 拆分为 execution、on-demand status check 和 output validation；
- 建立阶段 completion gate；
- 建立本地 execution spec 和三类 detail report schemas；
- 建立 66 个正向、负向、边界、恢复和失败 behavior cases。

## 已否定

- 固定写死 `EM → NVT → NPT → MD`；
- 一个 Operation 内提交任务并循环等待到完成；
- 把 `OPERATION_WITH_VALIDATOR` 用于跨越长时间外部运行；
- 把 job/session 消失直接视为成功或失败；
- 把 submission accepted 视为模拟完成；
- 仅凭 checkpoint、目录或输出文件存在跳过验证；
- 在缺少明确策略时自动选择 checkpoint、append/noappend、时长或科学阈值；
- 将技术输出验证表述为采样充分或科学收敛。

## 仍未验证

- `external_submission_adapter` Tool 的设计、实现、测试、benchmark 和 ACTIVE 注册；
- GROMACS executable/version、argv、安全 backend adapter 的可执行实现；
- LOCAL、TMUX、LSF、SLURM、PBS 的真实提交和状态映射；
- GROMACS `.log/.edr/.xtc/.trr/.gro/.cpt/.tpr` parser；
- execution spec 和 detail report schemas 的可执行 schema tests；
- fixtures 的自动化测试 runner；
- Manager 对外部 submission 的强化预记录、恢复锚点和 closure 集成；
- `md_preparation_workflow` 到 MD_INPUT 的实际出口接口；
- `analysis_workflow` 对 MD_OUTPUT 的实际入口接口；
- 真实 EM、平衡、production、continuation 和失败恢复项目测试；
- authoring 静态检查脚本；
- FAST/FULL runtime integration；
- 多 Workstream 外部任务并存和 Focus 切换测试。

## Frozen local architecture

```yaml
workflow:
  name: md_simulation_workflow
  path: 01_workflows/md_simulation_workflow
  entry_artifact: VALIDATED MD_INPUT
  exit_artifact: VALIDATED MD_OUTPUT
  planning_interface: 03_contracts/workflow_route_fragment.schema.yaml
  execution_interface: 03_contracts/workflow_decision.schema.yaml
  route_model: dynamic_run_units

run_unit_tasks:
  execution:
    operation: md_run_execution
    mode: OPERATION
  status_check:
    validator: md_run_status_validator
    mode: VALIDATOR
    condition: asynchronous submission requires on-demand refresh
  output_validation:
    validator: md_run_output_validator
    mode: VALIDATOR
  workflow_completion:
    validator: md_simulation_completion_validator
    mode: VALIDATOR
```

## Run unit lifecycle

```text
execute_or_submit
→ SUBMITTED/RUNNING or synchronous terminal
→ on-demand status check when needed
→ FINISHED_UNVERIFIED
→ output validation
→ Manager accepts VALIDATED MD_OUTPUT
```

外部任务运行期间 Workflow 返回 PAUSE。状态检查是单次 ON_DEMAND task，不是轮询服务。

## Created files

```text
01_workflows/md_simulation_workflow/SKILL.md
01_workflows/md_simulation_workflow/references/run_unit_model.md

02_operations/md_run_execution/SKILL.md
02_operations/md_run_execution/schemas/md_run_execution_spec.schema.yaml

02_validators/md_run_status_validator/SKILL.md
02_validators/md_run_status_validator/schemas/md_run_status_report.schema.yaml

02_validators/md_run_output_validator/SKILL.md
02_validators/md_run_output_validator/schemas/md_run_output_validation_report.schema.yaml

02_validators/md_simulation_completion_validator/SKILL.md
02_validators/md_simulation_completion_validator/schemas/md_simulation_completion_report.schema.yaml

04_evals/md_simulation_workflow/fixtures/route_and_decision_cases.yaml
04_evals/md_run_execution/fixtures/execution_cases.yaml
04_evals/md_run_status_validator/fixtures/status_cases.yaml
04_evals/md_run_output_validator/fixtures/output_validation_cases.yaml
04_evals/md_simulation_completion_validator/fixtures/completion_cases.yaml
```

## Behavior coverage

```yaml
md_simulation_workflow: 14
md_run_execution: 14
md_run_status_validator: 11
md_run_output_validator: 15
md_simulation_completion_validator: 12
total: 66
```

覆盖：

- 单一 EM；
- 非标准平衡序列；
- 分段 production；
- Workflow exit；
- run unit 范围缺失；
- 循环依赖；
- VALIDATED MD_INPUT gate；
- synchronous/asynchronous；
- tmux 与 scheduler；
- submission rejected/identity unresolved；
- UNKNOWN 状态；
- continuation/append policy；
- 输出缺失、截断、fatal、target 未达到；
- checkpoint 和跨文件一致性；
- 显式/隐式 role-specific threshold；
- active/unverified submission closure；
- failed run replacement；
- scope completion 与 Workflow completion 区分；
- 目录存在不得作为完成证据。

## Architecture findings

### PASS

- Workflow planning/execution 双接口保持分离；
- 每次 execution decision 只选择一个 task unit；
- 长时间外部运行没有被包装为前台长驻子 Agent；
- Operation、status Validator、output Validator 和 completion Validator 职责分离；
- Operation/Validator 不写管理目录；
- submission、artifact 和 Workstream state 均由 Manager 提交；
- `FINISHED_UNVERIFIED` 与 `COMPLETED` 分离；
- 条件 status check 未在规划阶段无证据删除；
- 单环节、跨片段和动态路线需求可表达；
- 技术完成与科学收敛边界明确。

### REVIEW REQUIRED

1. 外部 submission 是强化预记录 task。Manager 集成时必须在副作用前建立恢复锚点，并为异步 execution 提供 prepared submission identity；当前 execution spec 尚未冻结该共享引用方式。
2. run unit 列表和依赖目前由 planning context 提供，尚无跨 Workflow 的权威结构化 contract。若 `md_preparation_workflow` 需要直接生成 run plan，应由主窗口决定其 owner，优先考虑共享 contract 或明确的 MD_INPUT manifest owner。
3. GROMACS role-specific checks 的 metric registry 尚未定义。不得让自由文本 metric 在实现阶段形成不一致解析。
4. output Validator 是否直接返回 MD_OUTPUT candidate，或只返回 gate 后由 Manager 从文件集合构造 candidate，需要与现有 Manager artifact closure 实现复核。
5. 同一 Workstream 是否允许多个无依赖 run units 同时外部运行尚未冻结。当前 draft 按依赖顺序推进；独立重复优先不同 Workstream。

## Tool request

```yaml
tool_request:
  capability: safe external submission and on-demand status adapter
  reason: backend submission, identity parsing and status mapping are deterministic, repeated, environment-sensitive and recovery-critical
  callers:
    - md_run_execution
    - md_run_status_validator
  required_inputs:
    - backend type
    - immutable command or submission script identity
    - working directory
    - resource request
    - prepared submission identity
    - status identity
  expected_outputs:
    - accepted/rejected submission result
    - PID/session/job identity
    - raw backend evidence
    - normalized non-decisional status data
  read_paths:
    - explicit executable and script paths
    - explicit run-unit logs
  write_paths:
    - explicit run-unit evidence paths only
  side_effects:
    - submit exactly one process or scheduler job when called in submit mode
    - perform exactly one status query when called in status mode
```

该请求必须由 `00_authoring/md-workflow-tool-authoring/SKILL.md` 处理。本业务窗口不修改 `05_tools/` 或 registry。

## Shared-file handoff requests

主窗口审查通过后再处理：

```yaml
content_maps_to_create:
  - 00_authoring/content_maps/md_simulation_workflow.yaml
  - 00_authoring/content_maps/md_run_execution.yaml
  - 00_authoring/content_maps/md_run_status_validator.yaml
  - 00_authoring/content_maps/md_run_output_validator.yaml
  - 00_authoring/content_maps/md_simulation_completion_validator.yaml

inventory_entries_to_add:
  - md_simulation_workflow
  - md_run_execution
  - md_run_status_validator
  - md_run_output_validator
  - md_simulation_completion_validator

ownership_assignment:
  window: md-simulation-window
  write_paths:
    - 01_workflows/md_simulation_workflow/**
    - 02_operations/md_run_execution/**
    - 02_validators/md_run_status_validator/**
    - 02_validators/md_run_output_validator/**
    - 02_validators/md_simulation_completion_validator/**
    - 04_evals/md_simulation_workflow/**
    - 04_evals/md_run_execution/**
    - 04_evals/md_run_status_validator/**
    - 04_evals/md_run_output_validator/**
    - 04_evals/md_simulation_completion_validator/**
```

本窗口未修改 `AGENTS.md`、`SYNC_STATUS.md`、inventory、ownership、content maps、contracts、Manager references、design records 或 tool registry。

## Validation not yet executed

以下检查尚未运行，因此不得标记 PASS：

```text
validate_md_skill.py
validate_architecture_separation.py
validate_content_maps.py
validate_contracts.py
fixture schema/tests
real backend integration tests
```

原因：当前只完成 GitHub 分支中的 contract draft，尚未建立本地可执行实现和主窗口共享文件同步。

## Next action

```yaml
next_action:
  - 主窗口审查 run unit 边界、prepared submission identity 和跨 Workflow run plan owner
  - 同步 content maps/inventory/ownership
  - 为 execution spec 和 report schemas 编写 schema tests
  - 设计 external_submission_adapter Tool
  - 实现最小 LOCAL/TMUX backend，再扩展 scheduler
  - 实现 GROMACS output parser 和真实 fixtures
  - 执行 Manager + FAST/FULL + recovery 端到端测试
```
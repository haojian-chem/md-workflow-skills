# MD Simulation Skills Draft Validation

## Status

```yaml
status: REVIEW_REQUIRED
branch: draft/md-simulation-skills
scope: md_simulation workflow contract draft
runtime_ready: false
skills: 11
files_added: 35
behavior_cases: 201
```

本记录确认 MD 模拟阶段的职责、局部接口、schemas 和行为 fixtures 已完成第二轮结构设计。它不表示 GROMACS、tmux、调度系统、parser 或 Manager 集成已经可执行通过。

## 已做过

- 对齐 `AGENTS.md`、authoring Skill、四层边界、runtime subagent protocol、route planning protocol 和 deterministic tool protocol；
- 对齐 Workflow fragment/decision、subagent task/result、submission、artifact contracts；
- 读取权威 `stage_registry.yaml`，修正 `md_preparation → md_simulation` 边界；
- 将标准入口改为 VALIDATED SYSTEM；
- 将 protocol、MDP、grompp、TPR 和 execution 归入 `md_simulation_workflow`；
- 建立 protocol specification/validation 层，禁止从自然语言或常见实践直接生成科学计划；
- 建立 field-level provenance；
- 建立 immutable protocol/plan version 和 supersedes 语义；
- 将 run unit 拆分为 input preparation、input validation、execution、on-demand status check 和 output validation；
- 建立 Workflow completion gate；
- 建立 10 个本地 schemas；
- 建立 201 个正向、负向、边界、分支、恢复和失败 behavior cases。

## 已否定

- 固定 `EM → NVT → NPT → MD` 队列；
- 根据“按标准流程”“使用默认参数”补充科学步骤；
- Manager/Workflow 直接从自然语言生成 protocol 或 plan；
- 将 run plan 归入 `md_preparation_workflow`；
- 将现成 MD_INPUT 设为标准 Workflow entry；
- 在一个 Operation 中 grompp、提交并等待模拟完成；
- 使用 `OPERATION_WITH_VALIDATOR` 跨越长时间外部任务；
- submission accepted 即模拟完成；
- job/session 消失即成功或失败；
- 高频轮询外部任务；
- 自动选择 checkpoint、append/noappend、maxwarn、时长或 acceptance threshold；
- 仅凭目录、TPR、checkpoint 或输出文件存在跳过 gate；
- 需要新 TPR 时一律返回 `md_preparation_workflow`；
- 将技术输出验证表述为采样充分或科学收敛。

## 仍未验证

- 全部本地 schemas 的可执行 JSON Schema tests；
- fixtures 自动化 runner；
- authoring static checks；
- Manager route fragment/decision 集成；
- Manager 对 protocol/plan 业务文件的引用和 closure 处理；
- FAST/FULL runtime validation integration；
- 首个外部长任务的强化预记录和 prepared submission identity；
- GROMACS executable/version discovery；
- MDP parser、topology include closure parser 和 TPR inspection；
- log、EDR、trajectory、structure 和 checkpoint parser；
- role-specific metric registry；
- LOCAL、TMUX、LSF、SLURM、PBS 真实 backend；
- external submission recovery；
- real EM/equilibration/production/continuation projects；
- multi-Workstream external task coexistence and Focus switching；
- upstream `md_preparation_workflow` 的真实 VALIDATED SYSTEM interface；
- downstream `analysis_workflow` 的真实 VALIDATED MD_OUTPUT interface。

## Frozen stage boundary

```text
md_preparation_workflow
→ VALIDATED SYSTEM
→ md_simulation_workflow
→ validated simulation protocol
→ immutable validated simulation plan
→ per-run VALIDATED MD_INPUT
→ execution / submission
→ FINISHED_UNVERIFIED
→ per-run VALIDATED MD_OUTPUT
→ completion validation
→ analysis_workflow
```

只有 SYSTEM 的 structure、topology、box、solvent 或 ions 改变时，才返回 `md_preparation_workflow`。

## Frozen local architecture

```yaml
workflow:
  name: md_simulation_workflow
  entry_artifact: VALIDATED SYSTEM
  exit_artifact: VALIDATED MD_OUTPUT
  planning_interface: 03_contracts/workflow_route_fragment.schema.yaml
  execution_interface: 03_contracts/workflow_decision.schema.yaml
  route_model: dynamic_projection_from_validated_plan

protocol:
  operation: md_simulation_protocol_specification
  validator: md_simulation_protocol_validator
  owner: 01_workflows/md_simulation_workflow
  rule: every scientific field requires provenance

plan:
  operation: md_simulation_plan_materialization
  validator: md_simulation_plan_validator
  owner: 01_workflows/md_simulation_workflow
  immutable: true
  route_record: separate_manager_owned_object

run_unit:
  input_preparation:
    operation: md_run_input_preparation
    validator: md_run_input_validator
  execution:
    operation: md_run_execution
  status_check:
    validator: md_run_status_validator
    mode: ON_DEMAND
  output_validation:
    validator: md_run_output_validator

completion:
  validator: md_simulation_completion_validator
```

## Substep sequence

```text
0. specify_and_validate_simulation_protocol
1. materialize_and_validate_simulation_plan

for each selected run unit:
2. prepare_and_validate_run_input:<run_unit_id>
3. execute_run_unit:<run_unit_id>
4. check_run_unit_status:<run_unit_id>       # conditional
5. validate_run_unit_output:<run_unit_id>

6. workflow_completion_validation            # Workflow exit only
```

若尚无 validated protocol，route 只能安全规划到 protocol gate；若已有 protocol 但没有 validated plan，只规划到 plan gate。Workflow 不得虚构后续 run units。

## Protocol and plan ownership

```text
simulation_protocol_spec: md_simulation_workflow local owner
md_simulation_plan: md_simulation_workflow local owner
Workstream route: Manager owner
```

- protocol 从 resolved decisions、route scope、explicit files 和 validated artifacts 物化；
- plan 从 validated protocol 保真物化；
- route 是 Manager 对当前 plan 的 task projection；
- protocol/plan 变化生成新 immutable version；
- route 变化生成新 route record；
- 三者不得覆盖或互相代替。

## Unresolved item barriers

```text
PLAN_VALIDATION
→ blocks protocol/plan acceptance

INPUT_PREPARATION
→ protocol/plan may exist
→ blocks affected grompp/input task

EXECUTION
→ protocol/plan and MD_INPUT may exist
→ blocks affected execution task
```

科学字段不得伪装为 execution-only unresolved item。

## External run lifecycle

```text
VALIDATED MD_INPUT
→ execute_or_submit
→ SUBMITTED/RUNNING
→ on-demand status check
→ FINISHED_UNVERIFIED
→ output validation
→ COMPLETED or FAILED
```

外部任务运行期间 Workflow 返回 PAUSE。status Validator 是一次 ON_DEMAND task，不是轮询服务。

## Behavior coverage

```yaml
md_simulation_workflow: 21
md_simulation_protocol_specification: 16
md_simulation_protocol_validator: 17
md_simulation_plan_materialization: 19
md_simulation_plan_validator: 22
md_run_input_preparation: 18
md_run_input_validator: 18
md_run_execution: 19
md_run_status_validator: 11
md_run_output_validator: 21
md_simulation_completion_validator: 19
total: 201
```

覆盖：

- VALIDATED SYSTEM entry；
- protocol decisions and field provenance；
- implicit default detection；
- protocol/plan revision；
- plan DAG and start-state lineage；
- single EM and nonstandard equilibration；
- segmented production；
- SYSTEM/prior-output input sources；
- MDP/topology/include/TPR validation；
- maxwarn and grompp warnings；
- synchronous/asynchronous execution；
- LOCAL/TMUX/scheduler submission；
- submission rejection/unknown identity；
- continuation and append policy；
- required output, truncation, fatal and target failure；
- checkpoint and cross-file consistency；
- explicit metric thresholds and no implicit thresholds；
- active/unknown/FINISHED_UNVERIFIED submission closure；
- failed run replacement；
- SYSTEM→protocol→plan→MD_INPUT→MD_OUTPUT lineage；
- scope completion vs Workflow completion；
- directory existence not being completion evidence。

## Architecture findings

### PASS at contract-draft level

- Workflow planning/execution interfaces remain separated；
- 每个 execution decision 只选择一个 task unit；
- protocol、plan、route ownership 分离；
- Operation/Validator responsibilities separated；
- long external jobs are not resident foreground subagents；
- status checking is ON_DEMAND；
- FINISHED_UNVERIFIED is separated from COMPLETED；
- scientific parameters require explicit provenance；
- dynamic route and single-substep use cases are expressible；
- new TPR work remains in md_simulation unless SYSTEM changes；
- technical completion and scientific convergence are separated；
- this window did not modify shared contracts or management files。

### REVIEW REQUIRED

1. `decision_record.schema.yaml` stores selected option and user statement, not typed MD parameters. The protocol specification Operation must use deterministic parsers or return confirmation items; it may not rely on unrestricted LLM interpretation in production.
2. Protocol/plan business file references are not currently represented by a shared artifact type. Main window must decide whether they remain detail files referenced by tasks/routes or require a shared typed record extension.
3. Manager artifact closure must confirm whether Validator returns MD_INPUT/MD_OUTPUT candidate directly or recommends Manager constructing the artifact from the validated file set.
4. Same-Workstream independent run-unit concurrency is not frozen. Current draft advances by dependency order; independent replicas should generally use separate Workstreams.
5. Role-specific metric IDs require a registry before executable validation.
6. Hard gates depending on external submission or GROMACS inspection require ACTIVE Tools or an authoritative tested built-in path before runtime activation.

## Tool requests

### 1. External submission adapter

```yaml
tool_request:
  capability: safe external submission and on-demand status adapter
  callers:
    - md_run_execution
    - md_run_status_validator
  responsibilities:
    - submit exactly one LOCAL/TMUX/scheduler task
    - return PID/session/job identity
    - retain raw backend evidence
    - perform exactly one status query
    - normalize non-decisional backend status data
```

### 2. GROMACS artifact inspector

```yaml
tool_request:
  capability: deterministic GROMACS input and output inspection
  callers:
    - md_run_input_preparation
    - md_run_input_validator
    - md_run_output_validator
  responsibilities:
    - parse MDP and topology include closure
    - inspect TPR metadata
    - parse log/EDR/trajectory/structure/checkpoint metadata
    - compare step, time, atom count and identities
    - compute registered role-specific metrics
```

Neither Tool may choose scientific thresholds, route, Focus or user decisions. They must be created through Tool Authoring and become ACTIVE only after executable tests and benchmark.

## Shared-file handoff requests

Main window should review and, if accepted, create content maps and inventory entries for:

```text
md_simulation_workflow
md_simulation_protocol_specification
md_simulation_protocol_validator
md_simulation_plan_materialization
md_simulation_plan_validator
md_run_input_preparation
md_run_input_validator
md_run_execution
md_run_status_validator
md_run_output_validator
md_simulation_completion_validator
```

Ownership assignment requested for:

```text
01_workflows/md_simulation_workflow/**
02_operations/md_simulation_protocol_specification/**
02_validators/md_simulation_protocol_validator/**
02_operations/md_simulation_plan_materialization/**
02_validators/md_simulation_plan_validator/**
02_operations/md_run_input_preparation/**
02_validators/md_run_input_validator/**
02_operations/md_run_execution/**
02_validators/md_run_status_validator/**
02_validators/md_run_output_validator/**
02_validators/md_simulation_completion_validator/**
04_evals/md_simulation_*/**
04_evals/md_run_*/**
```

After review and executable integration, main window may change `stage_registry.yaml` connection status for `md_simulation_workflow` from `planned` to `connected`. Its existing responsibility boundary is already correct.

This window did not modify:

```text
AGENTS.md
00_authoring/SYNC_STATUS.md
00_authoring/skill_inventory.yaml
00_authoring/file_ownership.yaml
00_authoring/content_maps/**
00_manager/**
03_contracts/**
05_tools/**
design_records/**
```

## Validation not executed

```text
validate_md_skill.py
validate_architecture_separation.py
validate_content_maps.py
validate_contracts.py
fixture schema/tests
real GROMACS/backend integration tests
Manager + FAST/FULL + recovery end-to-end tests
```

Therefore the branch remains `REVIEW_REQUIRED` and `runtime_ready: false`.

## Next action

```yaml
next_action:
  - main window reviews protocol/plan ownership and Manager representation
  - synchronize content maps, inventory and ownership
  - implement schema and fixture test runners
  - design external_submission_adapter Tool
  - design gromacs_artifact_inspector Tool and metric registry
  - implement minimum LOCAL/TMUX plus MDP/TPR/log/checkpoint path
  - run Manager, runtime validation and recovery integration
  - test real EM, equilibration, production and continuation Workstreams
```

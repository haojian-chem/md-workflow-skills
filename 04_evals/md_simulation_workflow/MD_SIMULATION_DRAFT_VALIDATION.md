# MD Simulation Skills Draft Validation

## Current status

```yaml
status: REVIEW_REQUIRED
branch: draft/md-simulation-skills
architecture_version: 2
runtime_ready: false
stage_registry_connection: planned
skills: 15
files_added: 50
local_schemas: 14
fixture_files: 15
behavior_cases: 214
validation_runner_created: true
validation_runner_executed: false
```

本记录确认 MD 模拟阶段已完成细节审计后的 contract v2 重构。尚未执行仓库级 schema/static/fixture tests、Manager 集成、真实 GROMACS 或 backend 测试，因此不得标记为可运行或 connected。

详细审计：

```text
04_evals/md_simulation_workflow/MD_SIMULATION_DETAIL_AUDIT.md
```

本地校验器：

```text
04_evals/md_simulation_workflow/scripts/validate_md_simulation_contracts.py
```

## Frozen stage boundary

```text
md_preparation_workflow
→ VALIDATED SYSTEM
→ md_simulation_workflow
→ validated scientific protocol
→ validated task-projection plan
→ per-run VALIDATED MD_INPUT
→ validated execution attempts
→ per-run VALIDATED MD_OUTPUT
→ validated stage-level MD_OUTPUT collection
→ completion validation
→ analysis_workflow
```

只有 SYSTEM structure/topology/box/solvent/ions 改变时返回 `md_preparation_workflow`。

## v2 object model

### Scientific protocol

唯一拥有：

- run units 和 scientific roles；
- dependencies；
- FINAL_FILE 或 TEMPLATE_WITH_TYPED_OVERRIDES MDP specification；
- start states；
- preprocessing policy；
- expected output roles；
- completion criteria；
- field provenance；
- unresolved gates。

不拥有 backend、resources、runtime executable、attempt 或 submission identities。

### Task-projection plan

只保存：

- validated protocol identity；
- run-unit DAG projection；
- run/input/attempts paths；
- input/attempt gate projection；
- revision lineage。

plan 不复制 scientific values，也不嵌入 runtime status。

### Execution attempt

```text
run unit = stable scientific segment
attempt = one concrete execution/submission
```

v1 attempt kinds：

```text
FRESH
RETRY_SAME_INPUT
CONTINUE_NOAPPEND
```

`CONTINUATION` 已从 scientific role 删除。APPEND 明确禁用。

### Output layers

- run-level MDOUTPUT：一个 run unit 的 accepted attempt chain；
- stage-level MDOUTPUT：scope 内全部 required run outputs 的唯一 collection；
- segmented production 不得遗漏早期 segment；
- assembly 不复制或拼接 engine data。

## Skills

```text
01_workflows/md_simulation_workflow

02_operations/md_simulation_protocol_specification
02_validators/md_simulation_protocol_validator

02_operations/md_simulation_plan_materialization
02_validators/md_simulation_plan_validator

02_operations/md_run_input_preparation
02_validators/md_run_input_validator

02_operations/md_execution_attempt_specification
02_validators/md_execution_attempt_validator

02_operations/md_run_execution
02_validators/md_run_status_validator
02_validators/md_run_output_validator

02_operations/md_simulation_output_assembly
02_validators/md_simulation_output_validator

02_validators/md_simulation_completion_validator
```

## Substep sequence

```text
0. specify_and_validate_simulation_protocol
1. materialize_and_validate_simulation_plan

for each selected run unit:
2. prepare_and_validate_run_input:<run_unit_id>
3. specify_and_validate_execution_attempt:<run_unit_id>:<attempt_id>
4. execute_attempt:<run_unit_id>:<attempt_id>
5. check_attempt_status:<run_unit_id>:<attempt_id>       # conditional
6. validate_run_output:<run_unit_id>

Workflow exit:
7. assemble_and_validate_simulation_output
8. workflow_completion_validation
```

Protocol 未验证时 route 只能到 0；plan 未验证时只能到 1。初始 route 只包含 FRESH attempt。retry/continuation 由新 evidence 触发 route revision。

## Corrected P0 findings

- execution spec 已有专属 Operation/Validator；
- execution spec/attempt identity 独立于 task ID；
- retry/continuation 使用独立 attempt directory；
- APPEND 与旧文件 mutation 被禁止；
- run-output Validator 核验 accepted attempt chain；
- stage-level output assembly/validation 已建立；
- completion 不再选择“唯一最后 run output”。

## Corrected P1 findings

- `CONTINUATION` 从 scientific role 删除；
- scientific protocol 与 runtime/backend/resource 分离；
- MDP 支持 final file 或 template+typed overrides；
- plan 不再复制 protocol scientific fields；
- immutable plan 不再保存 runtime status；
-开放式自然语言不能直接生成 typed scientific values；
- expected-output role 使用受控枚举。

## Schema details corrected

- SYSTEM start 强制 checkpoint 为 null；
- completion criteria 使用显式 completion mode；
- TARGET_STEP_OR_TIME 至少有 step/time target；
- ROLE_SPECIFIC 至少有一个 check；
- async attempt 要求 prepared submission identity；
- CONTINUE_NOAPPEND 要求 parent+checkpoint；
- FRESH/RETRY/CONTINUE 条件互斥；
- integer/number typed override 不再使用重叠 oneOf；
- stage output derived IDs 必须覆盖 included run outputs。

## Behavior coverage

```yaml
md_simulation_workflow: 16
md_simulation_protocol_specification: 14
md_simulation_protocol_validator: 17
md_simulation_plan_materialization: 15
md_simulation_plan_validator: 17
md_run_input_preparation: 15
md_run_input_validator: 16
md_execution_attempt_specification: 10
md_execution_attempt_validator: 10
md_run_execution: 15
md_run_status_validator: 11
md_run_output_validator: 18
md_simulation_output_assembly: 10
md_simulation_output_validator: 12
md_simulation_completion_validator: 18
total: 214
```

Coverage includes：

- scientific/runtime owner separation；
- field provenance and ambiguous language；
- FINAL_FILE/template+typed override；
- projection plan without embedded status；
- FRESH/RETRY/CONTINUE_NOAPPEND；
- prepared submission identity；
- attempt directory isolation；
- single ON_DEMAND status query；
- accepted attempt graph/branch/checkpoint continuity；
- failed/superseded attempt exclusion；
- target-not-reached continuation recommendation；
- segmented production collection；
- stage manifest non-mutation；
- scope completion versus Workflow completion；
- no scientific convergence claim。

## Contract-level findings

### Pass pending executable validation

- Workflow planning/execution interfaces remain separate；
- each decision selects one task unit；
- Workflow does not execute child Skills；
- Operation/Validator responsibilities remain separate；
- protocol/plan/route/attempt/output owners are distinct；
- long jobs are not resident foreground subagents；
- status checks are ON_DEMAND；
- FINISHED_UNVERIFIED remains distinct from COMPLETED；
- APPEND mutation is excluded from v1；
- full SYSTEM→stage-output lineage is expressible；
- technical completion remains distinct from scientific convergence；
- shared contracts and Manager files were not modified。

### Review required

1. Protocol/plan/attempt/stage-manifest business objects are not represented by shared artifact types.
2. Shared submission record lacks explicit attempt/spec IDs.
3. Manager artifact closure must freeze candidate registration for MDINPUT/run-output/stage-output.
4. Project-relative path normalization needs an authoritative rule.
5. Same-Workstream independent run-unit concurrency remains unfrozen.
6. Metric IDs require an ACTIVE registry before becoming hard gates.
7. Parser/submission hard gates require ACTIVE Tools or tested built-in implementations.

## Validation runner

The runner checks：

- 15 Skill frontmatter/name/path pairs；
- 14 YAML/JSON Schemas using Draft 2020-12 meta-validation；
- v2 invariants and removal of the old execution schema；
- no scientific `CONTINUATION` role or APPEND-enabled attempt schema；
- no runtime/scientific owner leakage into protocol/plan；
- 15 fixture files, local duplicate IDs, expected counts and total 214 cases。

It has not been executed because this environment cannot authenticate a private-repository checkout. This is an environment limitation, not a test pass.

## Shared-file handoff

Main window should review and, only after executable validation, add content maps/inventory/ownership for all 15 Skills.

This window did not modify：

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

## Validation still required

```text
run validate_md_simulation_contracts.py
JSON Schema positive/negative instance tests
validate_md_skill.py
validate_architecture_separation.py
validate_content_maps.py
validate_contracts.py
Manager route/decision integration
FAST/FULL runtime validation
recovery/end-to-end tests
real GROMACS/backend tests
```

Therefore：

```yaml
status: REVIEW_REQUIRED
runtime_ready: false
stage_registry_connection: planned
```

## Next action

```yaml
next_action:
  - run the local contract validator in an authenticated checkout
  - fix all schema/static/fixture failures
  - add positive and negative schema instances
  - run authoring and architecture validation
  - report failures before designing Tools
  - only after these pass, submit shared-contract and Tool requests to main window
```

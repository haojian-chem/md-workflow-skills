# MD Simulation Detail Audit

## Status

```yaml
status: CONTRACT_CORRECTIONS_COMPLETED
branch: draft/md-simulation-skills
architecture_version: 2
runtime_ready: false
implementation_may_start: false
schema_tests_executed: false
fixture_runner_executed: false
```

本审计先核对对象生成链、续跑/重试语义、artifact 谱系、schema owner 和阶段出口，再修订 contract。P0/P1 已在设计与 schema 层修正，但尚未运行可执行测试，因此仍不得开始真实 backend/parser 实现。

## 权威阶段边界

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
```

只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子变化时返回 `md_preparation_workflow`。

## P0 修正结果

### P0-1 Execution spec 无生成者

状态：`RESOLVED_AT_CONTRACT_LEVEL`

新增：

```text
md_execution_attempt_specification
→ md_execution_attempt_validator
→ md_run_execution
```

execution spec 使用稳定 `execution_spec_id` 和 `attempt_id`，不再使用 task ID 作为业务对象身份。旧 `md_run_execution_spec.schema.yaml` 已删除。

### P0-2 缺少 attempt 模型

状态：`RESOLVED_AT_CONTRACT_LEVEL`

对象已拆分：

```text
run unit = scientific segment
execution attempt = one concrete execution/submission
```

v1 attempt kinds：

```text
FRESH
RETRY_SAME_INPUT
CONTINUE_NOAPPEND
```

每个 attempt 使用独立目录和 evidence。APPEND 被明确禁止，避免修改旧文件和破坏 hash lineage。

### P0-3 阶段出口缺少聚合对象

状态：`RESOLVED_AT_CONTRACT_LEVEL`

新增：

```text
md_simulation_output_assembly
→ md_simulation_output_validator
→ unique stage-level MD_OUTPUT collection
```

stage manifest 引用 scope 内所有 required run-level MDOUTPUT artifacts，不复制或拼接 trajectory/energy。segmented production 不得只保留最后一个 segment。

## P1 修正结果

### Scientific role

`CONTINUATION` 已从 protocol/run-unit role 删除。continuation 只属于 attempt kind。

允许 role：

```text
ENERGY_MINIMIZATION
EQUILIBRATION
PRODUCTION
CUSTOM
```

### Protocol/runtime separation

scientific protocol 不再保存 executable、backend、host、GPU、queue、MPI/OMP、memory、walltime、append 或 submission identity。

runtime/资源/restart 归 execution-attempt spec。

### MDP 生成链

protocol v2 支持：

```text
FINAL_FILE
TEMPLATE_WITH_TYPED_OVERRIDES
```

input Operation 只允许 exact typed parameter replacement，禁止自由文本替换和隐式默认值；Validator 独立核验 rendered MDP、TPR 和未声明参数变化。

### Protocol/plan owner 分离

- protocol 是科学字段唯一 owner；
- plan 只保存静态 task projection、DAG、paths、gate refs 和 revision lineage；
- immutable plan 不再保存 `NOT_PREPARED/RUNNING/VALIDATED` 等运行状态；
- route 仍由 Manager 拥有。

### Typed decision boundary

protocol specification 只接受结构化输入、精确 decision option、带 hash 文件/模板和非科学 route scope。开放式自然语言不能唯一解析时必须形成 confirmation item。

### Output roles

protocol expected-output role 已改为受控枚举：

```text
LOG
ENERGY
TRAJECTORY_FULL
TRAJECTORY_COMPRESSED
FINAL_STRUCTURE
CHECKPOINT
OTHER
```

`OTHER` 必须附 custom role。metric registry 仍待主窗口/Tool 设计。

## Schema 细节修正

已修正：

- SYSTEM start-state 强制 checkpoint 为 null；
- completion criteria 增加显式 `completion_mode`；
- TARGET_STEP_OR_TIME 至少需要一个 target；
- ROLE_SPECIFIC 至少需要一个 check；
- execution object identity 独立于 task ID；
- append continuation 禁止；
- immutable plan 不嵌入 runtime status；
- run output report/manifest记录 attempt chain；
- completion 要求 validated stage-level MDOUTPUT，而不是“唯一最后 run output”。

## 新对象与 Skills

```text
md_execution_attempt_specification
md_execution_attempt_validator
md_simulation_output_assembly
md_simulation_output_validator
```

阶段当前共 15 个 Skills。

## v2 行为评测

旧的 201 条案例基于旧对象模型，已作废并重建。

```yaml
behavior_cases: 214
```

重点覆盖：

- protocol/runtime owner separation；
- FINAL_FILE 与 template+typed overrides；
- immutable projection plan 不含 runtime status；
- FRESH/RETRY/CONTINUE_NOAPPEND；
- prepared submission identity；
- attempt path isolation；
- accepted attempt chain；
- failed/superseded attempt exclusion；
- segmented production stage collection；
- stage manifest data non-mutation；
- scope completion 与 Workflow completion。

## 尚未解决或未验证

### Shared-contract/Manager decisions

- protocol/plan/attempt/stage manifest 是否需要共享 typed record；
- submission record 是否增加 attempt/spec identity；
- Manager 如何原子登记 stage-level artifact candidate；
- project-relative path normalization 权威规则；
- 同一 Workstream 无依赖 run units 是否允许并行。

### Tool/capability

- ACTIVE MDP parser/rendering implementation；
- topology include closure 与 TPR inspector；
- log/EDR/trajectory/checkpoint inspector；
- output-role/metric registry；
- external submission/status adapter；
- LOCAL/TMUX/scheduler backend tests。

### Tests

尚未执行：

```text
JSON Schema meta-validation
positive/negative schema instance tests
fixture runner
validate_md_skill.py
validate_architecture_separation.py
validate_content_maps.py
Manager route/decision integration
FAST/FULL runtime validation
recovery/end-to-end tests
```

## 当前结论

```yaml
contract_detail_audit: completed
P0_contract_findings: resolved
P1_contract_findings: resolved
P2_remaining: shared_contracts_tools_tests
next_action: executable_schema_and_fixture_validation
```

在 schema/static/fixture tests 通过前：

- `runtime_ready` 保持 false；
- 不同步 stage registry 为 connected；
- 不开始真实 backend/parser 实现；
- 不宣称任何 Skill 可生产运行。
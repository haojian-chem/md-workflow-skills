# Authoring 文件同步状态

更新日期：2026-07-23

## 当前基线

仓库已经同步并对齐：

- content map v3、Skill inventory 与文件所有权；
- Workstream 项目模型与 15 份共享运行 contract；
- Workflow planning/execution 双接口；
- Manager 入口初始化、路线范围和 execution barrier；
- 普通 task 最小记录、task closure 和 FAST/FULL runtime validation；
- `runtime_schema_validator` 0.1.0：ACTIVE；
- NEW 初始化 capability 预检、内建确定性状态提交和 blocker 因果分层；
- `source_recognition` draft；
- 1.2 classification parser + shared result wrapper draft；
- 1.3 chain/component selection Operation/Validator contract draft。

Manager 主文件保持 311 行；详细初始化与完整自检位于 references。

## 运行硬规则

```text
ENTRY_STATE_EVALUATED: NEW
→ capability preflight
→ candidate state
→ FULL validation
→ controlled commit
→ RESUMABLE / PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ EXECUTION
```

- NEW 只负责入口判定和基础初始化；
- 路线范围解析是初始化后的独立事件；
- 普通 task 只对 changed paths 执行一次 FAST；
- schema cache 命中时不重复 meta-validation；
- 不用 LLM 模拟 FULL schema/project reference validation；
- hard gate 必须有 ACTIVE Tool 或权威内建确定性路径；
- 后续路线/Workflow 问题不得冒充当前 blocker；
- 模型推理强度分层未写入 contract。

## Tool 状态

```text
runtime_schema_validator 0.1.0 — ACTIVE
state_transaction 0.1.0 — DESIGNED, optional optimization
incremental_reference_checker 0.1.0 — DESIGNED
task_closure_renderer 0.1.0 — DESIGNED
```

激活证据：

```text
04_evals/runtime_schema_validator/VALIDATION.md
5 tests passed
FAST cold median: 5.977 ms
FAST warm median: 3.311 ms
FULL warm median: 4.181 ms
```

## 1.2 Component and residue classification

已建立：

```text
SKILL.md
scripts/classify_structure.py
scripts/build_subagent_result.py
scripts/requirements.txt
scripts/README.md
references/classification_rules.md
references/standard_residue_alias_registry.yaml
references/covalently_linked_nonstandard_residue_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
04_evals/.../test_classify_structure.py
04_evals/.../test_build_subagent_result.py
04_evals/.../VALIDATOR_DRAFT_VALIDATION.md
```

核心语义：

- 显式共价、geometry-only covalent candidate 和 metal coordination 分离；
- 距离 alone 不确认共价；
- coordination 不改变 covalent topology class；
- metadata/residue chemistry 冲突返回 `METADATA_CONFLICT`；
- 科学歧义可以是 DONE + blocking confirmation；
- 输入 STRUCTURE 保持 `present_unvalidated`；
- 不创建 STRUCTURE artifact candidate；
- wrapper 生成共享 `subagent_result v2`，Manager 再 FAST-validate candidate result。

已执行：

```text
parser synthetic tests: 10 passed in 5.59s
wrapper synthetic-contract tests: 4 passed in 8.08s
```

仓库已编写 actual shared-contract + ACTIVE FAST integration test，但尚未在测试主机运行。真实 PDB、RCSB mmCIF、AF3 CIF 和完整 Manager closure 仍未验收。

## 1.3 Chain and component selection

已建立：

```text
02_operations/chain_and_component_selection/SKILL.md
02_operations/chain_and_component_selection/references/selection_rules.md
02_operations/chain_and_component_selection/schemas/selection_spec.schema.yaml
02_operations/chain_and_component_selection/schemas/selection_manifest.schema.yaml
02_operations/chain_and_component_selection/schemas/selection_mapping.schema.yaml
02_validators/chain_and_component_selection_validator/SKILL.md
04_evals/chain_and_component_selection/fixtures/selection_cases.yaml
04_evals/chain_and_component_selection_validator/fixtures/selection_validation_cases.yaml
04_evals/chain_and_component_selection/SELECTION_DRAFT_VALIDATION.md
```

已冻结的 draft 规则：

- 必须提供结构化 selection spec；
- exactly one model + explicit component IDs；
- 不从自然语言、chain wildcard 或常见 MD 习惯猜测选择；
- 不默认保留蛋白或删除水/离子；
- v1 只支持完整 component selection；
- confirmed `COVALENT | DISULFIDE | GLYCOSIDIC` 跨 boundary 时 BLOCKED；
- 不自动扩展选择，也不静默切断连接；
- coordination 和 geometry-only candidate 不强制 inclusion，但写入 boundary report；
- selected component 的全部 residues/atoms/altLoc 与属性保留；
- output format 必须显式选择 PDB 或 MMCIF；
- Operation 只创建 UNVALIDATED STRUCTURE candidate；
- Validator 独立重算 expected set，核验 mapping、coordinates、attributes、connections 和 hashes；
- Validator 通过仅表示 selection fidelity，不表示 altLoc、completeness、protonation 或最终结构准备通过。

Behavior fixtures：

```text
Operation: 18 cases
Validator: 17 cases
```

确定性 `select_structure.py`、`validate_selection.py`、combined result builder 和可执行测试尚未实现，因此 1.3 仍只是 contract draft。

## 当前实现状态

- `md_workflow_manager`：启动自锁已修正，待真实项目端到端验证；
- `runtime_schema_validator`：ACTIVE；
- `source_recognition`：1.1 用户功能检查通过一次，待 closure/FAST/minimal-record 复测；
- `component_and_residue_classification_validator`：parser + result wrapper draft，待 actual FAST、真实结构与 Manager 集成；
- `chain_and_component_selection`：contract/fixtures draft，待确定性实现；
- `chain_and_component_selection_validator`：contract/fixtures draft，待确定性实现；
- 其他 Phase 1 Skills：待编写。

## 尚未冻结

- content map 的 `load_when` / `applicable_to` 扩展；
- 1.2 registries、真实结构接受性和 Manager 集成；
- 1.3 selection schemas/rules、确定性实现和 combined task；
- `state_transaction`、`incremental_reference_checker`、`task_closure_renderer`；
- Manager 真实项目端到端集成。

## 当前权威文件

- `AGENTS.md`；
- `design_records/logging_and_record_system.md`；
- `00_manager/md_workflow_manager/SKILL.md`；
- `00_manager/md_workflow_manager/references/`；
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
- `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`；
- `00_authoring/md-workflow-tool-authoring/SKILL.md`；
- `05_tools/tool_registry.yaml`；
- `04_evals/runtime_schema_validator/VALIDATION.md`；
- `04_evals/component_and_residue_classification_validator/VALIDATOR_DRAFT_VALIDATION.md`；
- `04_evals/chain_and_component_selection/SELECTION_DRAFT_VALIDATION.md`；
- `03_contracts/README.md`；
- 本文件。

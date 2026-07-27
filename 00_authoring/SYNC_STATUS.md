# Authoring 文件同步状态

更新日期：2026-07-27

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
- 1.2 component/residue classification v1.2 实现完成，正式验收待完成；
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

### 当前确定性运行路径

```text
scripts/inspect_model_scope.py
→ model_scope.yaml

scripts/classify_structure.py
→ classification_observations.yaml
→ reference_manifest.yaml

scripts/check_possible_connections.py
→ relation_checks/possible_connections_result.yaml

scripts/check_possible_coordination.py
→ relation_checks/possible_coordination_result.yaml

scripts/build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md

scripts/build_subagent_result.py
→ shared subagent_result v2 candidate
```

### 当前主要文件

```text
SKILL.md
references/classification_rules.md
references/standard_residue_registry.yaml
references/covalently_linked_nonstandard_residue_registry.yaml
scripts/README.md
scripts/classification_common.py
scripts/classification_engine.py
scripts/structure_records.py
scripts/explicit_relations.py
scripts/rtp_reference.py
scripts/ccd_reference.py
scripts/sequence_missing.py
schemas/project_residue_definitions.schema.yaml
schemas/possible_connections.schema.yaml
schemas/possible_coordination.schema.yaml
schemas/model_scope.schema.yaml
schemas/classification_observations.schema.yaml
schemas/reference_manifest.schema.yaml
schemas/possible_connections_result.schema.yaml
schemas/possible_coordination_result.schema.yaml
schemas/confirmation_requests.schema.yaml
schemas/classification_result.schema.yaml
```

### 已冻结语义

- 单 model 自动选择，多 model 在完整分类前形成用户选择 barrier；
- 残基名和原子名严格区分大小写，不执行 `.upper()`、alias、正则或模糊匹配；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS` 使用不同且明确的分类来源顺序；
- 标准残基在 registry 模式使用 CCD、力场模式使用所选 RTP 做重原子检查；
- 端基 RTP 必须由显式 terminal-template mapping 选择；
- PDB/mmCIF 检查缺失残基；AF3 只有提供输入 JSON、FASTA 或等价序列参考时才检查；
- 多 altLoc 残基记录为 `MULTIPLE_CONFORMATIONS`，不执行重原子比较；
- 可能共价连接和金属配位仅按项目明确提供的定义检查；
- 几何候选不自动确认关系；
- 金属配位只有定义允许且关系已确认时才能产生 topology promotion；
- selected model 完整扫描后统一生成 confirmation requests；
- 科学歧义可对应 `DONE + blocking confirmation_items`，不得伪装成技术失败；
- 输入 STRUCTURE 保持原 validation state，不创建新的 STRUCTURE artifact candidate；
- Manager 是共享项目状态和记录的唯一提交者。

### 已退出并删除的旧路径

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
```

旧版单脚本分类、内置 coordination 扫描、alias 解释和旧 `ambiguities/outcome_code` wrapper 均不再属于正式运行路径。

### 测试状态

已编写并纳入 `.github/workflows/component-classification-v1-2.yml`：

```text
04_evals/component_and_residue_classification_validator/test_inspect_model_scope.py
04_evals/component_and_residue_classification_validator/test_classify_structure.py
04_evals/component_and_residue_classification_validator/test_build_subagent_result.py
04_evals/component_and_residue_classification_validator/test_v1_2_redesign_foundation.py
04_evals/component_and_residue_classification_validator/test_v1_2_relations_and_builder.py
04_evals/component_and_residue_classification_validator/test_v1_2_classification_engine.py
04_evals/component_and_residue_classification_validator/test_v1_2_terminal_rtp.py
```

仓库当前尚未附加一份可追溯的完整新测试运行结果。旧版 parser/wrapper 测试数字不得作为 v1.2 最终通过证据。真实 PDB、RCSB mmCIF、AF3 CIF 和完整 Manager closure 仍未验收。

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
- `component_and_residue_classification_validator`：v1.2 代码、schema、文档、公开入口和 wrapper 已迁移，待正式测试证据、真实结构与 Manager closure；
- `chain_and_component_selection`：contract/fixtures draft，待确定性实现；
- `chain_and_component_selection_validator`：contract/fixtures draft，待确定性实现；
- 其他 Phase 1 Skills：待编写。

## 尚未冻结或尚未验收

- content map 的 `load_when` / `applicable_to` 扩展；
- 1.2 真实结构接受性、正式测试证据和 Manager 集成；
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
- `04_evals/component_and_residue_classification_validator/V1_2_REDESIGN_IMPLEMENTATION.md`；
- `04_evals/component_and_residue_classification_validator/VALIDATOR_DRAFT_VALIDATION.md`；
- `04_evals/chain_and_component_selection/SELECTION_DRAFT_VALIDATION.md`；
- `03_contracts/README.md`；
- 本文件。

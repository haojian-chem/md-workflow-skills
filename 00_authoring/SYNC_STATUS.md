# Authoring 文件同步状态

更新日期：2026-07-28

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
- 1.2 component/residue classification v1.2：实现与 repository-controlled validation 完成，真实 PDB/mmCIF/GROMACS、Authoring 静态检查和 Manager closure 均通过；真实 AF3 acceptance 等待实际输入；
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

### 当前状态

```text
implementation: PASS
contract_status: frozen
content_ownership_status: frozen
repository-controlled validation: PASS
real PDB: PASS
real mmCIF: PASS
real GROMACS force field: PASS
authoring static validation: PASS
Manager task closure: PASS
real AF3: NOT_RUN — PENDING_REAL_INPUT
validator v1.2 overall: NOT_PASSED
```

权威验收记录：

```text
04_evals/component_and_residue_classification_validator/VALIDATION.md
```

### 确定性运行路径

```text
scripts/inspect_model_scope.py
→ model_scope.yaml

scripts/classify_structure.py
→ scripts/classification_engine.py facade
→ scripts/classification_engine_core.py
→ classification_observations.yaml
→ reference_manifest.yaml

scripts/check_possible_connections.py
→ possible_connections_result.yaml

scripts/check_possible_coordination.py
→ possible_coordination_result.yaml

scripts/build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md

scripts/build_subagent_result.py
→ shared subagent_result v2 candidate

Manager
→ one FAST validation
→ atomic commit
→ terminal event / Workstream state
→ visible task closure
```

### 当前主要文件

```text
02_validators/component_and_residue_classification_validator/SKILL.md
02_validators/component_and_residue_classification_validator/references/classification_rules.md
02_validators/component_and_residue_classification_validator/references/standard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/references/covalently_linked_nonstandard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/scripts/README.md
02_validators/component_and_residue_classification_validator/scripts/classification_common.py
02_validators/component_and_residue_classification_validator/scripts/classification_engine.py
02_validators/component_and_residue_classification_validator/scripts/classification_engine_core.py
02_validators/component_and_residue_classification_validator/scripts/structure_records.py
02_validators/component_and_residue_classification_validator/scripts/explicit_relations.py
02_validators/component_and_residue_classification_validator/scripts/rtp_reference.py
02_validators/component_and_residue_classification_validator/scripts/ccd_reference.py
02_validators/component_and_residue_classification_validator/scripts/sequence_missing.py
02_validators/component_and_residue_classification_validator/schemas/*.schema.yaml
04_evals/component_and_residue_classification_validator/VALIDATION.md
```

### 已冻结语义

- 单 model 自动选择，多 model 在完整分类前形成用户选择 barrier；
- residue/atom names 原样保留并区分大小写；
- 禁止 `.upper()`、alias、正则和模糊匹配；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS` 使用不同且明确的来源顺序；
- 标准残基在 registry 模式使用 CCD、force-field 模式使用 exact RTP；
- 端基 RTP 必须通过显式 terminal-template mapping；
- PDB/mmCIF 检查缺失残基；AF3 只有提供 JSON/FASTA/等价序列参考时才检查；
- author `source_resid` 或 chain 归属无法建立时返回 `MAPPING_UNRESOLVED`；
- 同一 unresolved subject 跨阶段重复出现时合并并保留证据；
- 多 altLoc 残基记录 `MULTIPLE_CONFORMATIONS`，不执行重原子比较；
- 非水 exact RTP 重复定义生成确认项；普通水是明确例外；
- 项目 CCD snapshot 是本次运行的权威参考；相同哈希候选合并，不同有效候选进入统一确认；
- structural entity/polymer facts 决定 baseline grouping；classification conflict 不得拆散 polymer/branched chain；
- grouping 后恢复原 classification，不静默解决 topology conflict；
- possible covalent connection 与 coordination 按项目定义分开检查；
- geometry candidate 不自动确认；
- `promote=false` 的确认配位只记录 relation；
- `promote=true` 且关系确认后，非标准组分才可并入 polymer chain；
- scientific ambiguity 可对应 `DONE + blocking confirmation_items`，不得伪装成技术失败；
- 输入 STRUCTURE 保持原 validation state，不创建新的 STRUCTURE artifact candidate；
- Validator 不写 `00_project_state/**` 或 `00_project_records/**`；
- Manager 是共享项目状态和记录的唯一提交者。

### 验收摘要

```text
synthetic CI: 59 passed
real PDB: 3 passed
real mmCIF: 3 passed
real GROMACS force field: 1 passed
authoring static checks: PASS
Manager closure: PASS
```

真实 1VNS 的源格式记录不同：

```text
PDB REMARK 465: 35 missing residues
mmCIF unobserved-residue metadata: 46 records
```

系统保留各源格式的权威元数据，不制造跨格式数量一致性。

### AF3 剩余项

真实验收需要：

```text
actual *_model.cif
+
对应 fold_input.json / AlphaFold Server JSON / FASTA / 等价序列参考
```

普通 RCSB mmCIF 不得改名后冒充 AF3 输出。收到真实文件后只需补 real-AF3 workflow/test 和 SHA-256 记录，不再重构 1.2。

### 已退出并删除的旧路径

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
```

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

- `md_workflow_manager`：启动自锁已修正；1.2 task closure 已端到端验证；全项目通用 end-to-end 仍需后续阶段继续覆盖；
- `runtime_schema_validator`：ACTIVE；
- `source_recognition`：1.1 用户功能检查通过一次，待其独立 closure/FAST/minimal-record 复测；
- `component_and_residue_classification_validator`：repository-controlled validation 已完成，真实 AF3 输入待提供；
- `chain_and_component_selection`：contract/fixtures draft，待确定性实现；
- `chain_and_component_selection_validator`：contract/fixtures draft，待确定性实现；
- 其他 Phase 1 Skills：待编写。

## 尚未冻结或尚未验收

- content map 的 `load_when` / `applicable_to` 扩展；
- 1.2 真实 AF3 acceptance；
- 1.3 selection schemas/rules、确定性实现和 combined task；
- `state_transaction`、`incremental_reference_checker`、`task_closure_renderer`；
- Manager 在其他 task 类型和完整项目上的 end-to-end 集成。

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
- `04_evals/component_and_residue_classification_validator/VALIDATION.md`；
- `04_evals/component_and_residue_classification_validator/V1_2_REDESIGN_IMPLEMENTATION.md`；
- `04_evals/chain_and_component_selection/SELECTION_DRAFT_VALIDATION.md`；
- `03_contracts/README.md`；
- 本文件。

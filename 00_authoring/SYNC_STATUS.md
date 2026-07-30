# Authoring 文件同步状态

更新日期：2026-07-29

# 当前基线

仓库当前已对齐：

- content map v3、Skill inventory 与文件所有权；
- Workstream 项目模型与共享运行 contracts；
- Workflow planning/execution 双接口；
- Manager 初始化、路线范围和 execution barriers；
- 普通 task closure 与 FAST/FULL runtime validation；
- `runtime_schema_validator` 0.1.0：ACTIVE；
- `source_recognition` draft；
- 1.2 component/residue classification：PASS；
- 1.3 chain/component selection：contract draft，确定性实现尚未开始。

本文件只记录同步状态和权威文件位置。禁止在此复制 Manager、Workflow、Operation、Validator 或具体业务 Skill 的规则正文。

# 权威规则位置

```text
四层职责边界
→ 00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md

Manager 运行规则
→ 00_manager/md_workflow_manager/

结构准备 Workflow
→ 01_workflows/structure_preparation_workflow/SKILL.md

1.2 局部执行编排
→ 02_validators/component_and_residue_classification_validator/SKILL.md

1.2 科学判定语义
→ 02_validators/component_and_residue_classification_validator/references/classification_rules.md

1.2 CLI 与模块接口
→ 02_validators/component_and_residue_classification_validator/scripts/README.md

1.2 权威验收状态
→ 04_evals/component_and_residue_classification_validator/VALIDATION.md
```

# Tool 状态

```text
runtime_schema_validator 0.1.0 — ACTIVE
state_transaction 0.1.0 — DESIGNED, optional optimization
incremental_reference_checker 0.1.0 — DESIGNED
task_closure_renderer 0.1.0 — DESIGNED
```

`runtime_schema_validator` 激活证据：

```text
04_evals/runtime_schema_validator/VALIDATION.md
5 tests passed
FAST cold median: 5.977 ms
FAST warm median: 3.311 ms
FULL warm median: 4.181 ms
```

# 1.2 Component and residue classification

## 当前状态

```text
implementation: PASS
contract_status: frozen
content_ownership_status: frozen
synthetic and integration validation: PASS
real PDB: PASS
real mmCIF: PASS
real AF3: PASS
real GROMACS force field: PASS
authoring static validation: PASS
Manager task closure: PASS
validator v1.2 overall: PASS
```

## 确定性运行路径

```text
scripts/inspect_model_scope.py
→ model_scope.yaml

scripts/classify_structure.py
→ scripts/classification_engine.py
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
→ terminal event and Workstream state
→ visible task closure
```

## 主要文件

```text
02_validators/component_and_residue_classification_validator/SKILL.md
02_validators/component_and_residue_classification_validator/references/classification_rules.md
02_validators/component_and_residue_classification_validator/references/standard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/references/topology_linked_nonstandard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/scripts/README.md
02_validators/component_and_residue_classification_validator/scripts/af3_server_sequence_reference.py
02_validators/component_and_residue_classification_validator/scripts/classification_engine.py
02_validators/component_and_residue_classification_validator/scripts/classification_engine_core.py
02_validators/component_and_residue_classification_validator/schemas/*.schema.yaml
04_evals/component_and_residue_classification_validator/VALIDATION.md
```

## 验收摘要

```text
synthetic baseline: 59 passed
AlphaFold Server JSON regression: PASS
real PDB: 3 passed
real mmCIF: 3 passed
real AF3: 2 passed
real GROMACS force field: 1 passed
authoring static checks: PASS
Manager closure: PASS
```

真实 AF3 fixtures：

```text
fold_1bk0_ipns_fe_template_free
→ chain A protein + chain B FE

fold_1dz9_p450cam_hem_template_free
→ chain A protein + chain B HEM
```

模型和 Job JSON 均使用用户原始文件 size 与 SHA-256 作为验收 gate。

真实 1VNS 的源格式记录不同：

```text
PDB REMARK 465: 35 missing residues
mmCIF unobserved-residue metadata: 46 records
```

各源格式保留自身权威元数据，禁止制造跨格式数量一致性。

## 已退出并删除的旧路径

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
```

# 1.3 Chain and component selection

当前已有 contract draft：

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

尚未实现：

```text
select_structure.py
validate_selection.py
shared result wrapper
executable tests
```

# Component and residue classification v1.2 redesign implementation

更新日期：2026-07-27

## 状态

```text
REDESIGN_IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
```

新版确定性流水线已经接管 1.2 的公开脚本入口、最终结果整合和共享 `subagent_result v2` 包装路径。实现完成不等于最终验收通过；在正式测试证据、真实结构验证和 Manager closure 完成前，`validator v1.2 overall` 仍保持 `NOT_PASSED`。

## 当前运行路径

```text
inspect_model_scope.py
→ model_scope.yaml

classify_structure.py
→ classification_observations.yaml
→ reference_manifest.yaml

check_possible_connections.py
→ relation_checks/possible_connections_result.yaml

check_possible_coordination.py
→ relation_checks/possible_coordination_result.yaml

build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md

build_subagent_result.py
→ subagent_result v2 candidate
```

- selected model 未解决前不执行完整分类；
- selected model 确定后完成所有仍可执行的分类、缺失残基、重原子和关系检查；
- 科学歧义统一写入 `confirmation_requests.yaml`，不在第一项歧义处提前退出；
- wrapper 以 `classification_result.result_status` 和 `confirmation_requests.status` 为权威状态来源；
- Manager 仍是共享项目状态和记录的唯一提交者。

## 已完成的设计落地

### 输入与输出 schema

```text
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

### 严格名称 registry

```text
references/standard_residue_registry.yaml
references/covalently_linked_nonstandard_residue_registry.yaml
```

两个 registry 均采用严格、区分大小写、一个精确残基名一条定义的列表格式。项目级定义与 Skill registry 或 RTP 冲突时，完整扫描后统一请求确认，不执行 alias、正则或模糊名称覆盖。

### 确定性脚本与内部模块

```text
scripts/inspect_model_scope.py
scripts/classify_structure.py
scripts/classification_engine.py
scripts/classification_common.py
scripts/structure_records.py
scripts/explicit_relations.py
scripts/rtp_reference.py
scripts/ccd_reference.py
scripts/sequence_missing.py
scripts/check_possible_connections.py
scripts/check_possible_coordination.py
scripts/build_classification_result.py
scripts/build_subagent_result.py
```

已实现：

- 单 model 自动选择、多 model 用户选择 barrier 和受控写回；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS` 两种分类模式；
- 精确、区分大小写的项目定义、Skill registry 和 RTP 解析；
- 显式 terminal-template mapping；
- PDB/mmCIF 缺失残基证据和 AF3 显式序列参考路径；
- CCD 项目 snapshot、本地目录、共享 cache 和按策略下载；
- 单构象残基的 CCD/RTP 重原子核验；
- 多 altLoc 残基跳过重原子比较；
- 项目定义驱动的可能共价连接和金属配位检查；
- 已确认 relation 的 topology effect 与最终 `chain_groups` 重建；
- 与上一份 confirmation 文件哈希绑定的决定重放；
- 新版最终结果到共享 `subagent_result v2` 的确定性包装。

### 测试与 CI 配置

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

这些测试已形成可执行测试集合并进入 CI 配置；本记录尚未附加一次完整、可追溯的正式测试运行结果，因此不得仅凭测试文件存在宣称通过。

### 文档迁移

已按 v1.2 语义更新：

```text
SKILL.md
references/classification_rules.md
scripts/README.md
```

### 已退出并删除的旧运行路径

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
```

已删除的旧行为包括：

```text
残基名统一转大写
alias/模糊名称匹配
单脚本同时完成 model、分类、共价、配位和最终整合
内置 coordination registry 自动扫描
旧单一 classification_outputs.schema.yaml 作为唯一输出
旧 ambiguities/outcome_code 驱动的 subagent wrapper
```

## 尚需完成的正式验收

```text
1. 在正式测试环境运行全部 v1.2 pytest/CI，并保存可追溯结果；
2. 运行 authoring 静态检查和 schema meta-validation；
3. 使用真实 PDB 验证 model、缺失残基、CCD 和连接记录路径；
4. 使用真实 mmCIF 验证 entity、作者编号、unobserved residues 和 struct_conn 路径；
5. 使用 AF3 CIF + AF3 input JSON/FASTA 验证显式序列参考路径；
6. 验证 REGISTRY 与 FORCE_FIELD_ANALYSIS，包括内部和端基 RTP；
7. 完成一次 Manager task → wrapper → FAST validation → closure 的端到端测试；
8. 更新 SYNC_STATUS、inventory 和最终 VALIDATION 记录。
```

## 当前验收结论

```text
model scope entry: IMPLEMENTED, EXECUTABLE_TESTS_AUTHORED
new schemas: AUTHORED_AND_REFERENCED, FORMAL_META_VALIDATION_EVIDENCE_PENDING
classification parser: MIGRATED_TO_V1_2
relation checkers: IMPLEMENTED, EXECUTABLE_TESTS_AUTHORED
final result builder: IMPLEMENTED, EXECUTABLE_TESTS_AUTHORED
subagent result wrapper: MIGRATED_TO_V1_2, EXECUTABLE_TESTS_AUTHORED
documentation: MIGRATED_TO_V1_2
legacy runtime path: REMOVED
validator v1.2 overall: NOT_PASSED, FORMAL_VALIDATION_PENDING
```

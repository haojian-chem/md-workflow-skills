# Component and residue classification v1.2 redesign implementation

更新日期：2026-07-27

## 状态

```text
REDESIGN_IMPLEMENTATION_IN_PROGRESS
```

当前旧版 `classify_structure.py`、旧输出 schema 与 wrapper 仍是仓库中原有的可执行 draft。新版五段式流水线尚未整体接管运行路径，不得将本记录解释为 1.2 已通过最终验收。

## 已完成的设计落地

### 输入与输出 schema

已新增：

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

已新增：

```text
references/standard_residue_registry.yaml
```

已将：

```text
references/covalently_linked_nonstandard_residue_registry.yaml
```

迁移为严格、区分大小写、一个精确残基名一条定义的列表格式。

旧的：

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
```

尚未删除；在新版 parser 完整接管前保留为旧运行路径的迁移来源。新版正式路径不得继续使用 alias 匹配或内置 coordination 自动扫描。

### 确定性脚本与内部模块

已新增：

```text
scripts/inspect_model_scope.py
scripts/classification_common.py
scripts/structure_records.py
scripts/explicit_relations.py
scripts/rtp_reference.py
scripts/ccd_reference.py
scripts/sequence_missing.py
scripts/check_possible_connections.py
scripts/check_possible_coordination.py
```

其中：

- `inspect_model_scope.py` 已实现单 model 自动选择、多 model 待用户选择、已选择 model 受控写回、输入哈希与格式检查；
- 共价连接与金属配位检查器已经形成 draft 实现，但尚未完成可执行测试；
- RTP、CCD、缺失残基和自然结构标识模块已经形成 draft，实现仍需随主 parser 集成测试修订。

### 测试

已新增：

```text
04_evals/component_and_residue_classification_validator/test_inspect_model_scope.py
```

已在临时本地环境对 `inspect_model_scope.py` 的单 model 与多 model 路径做过一次手工 smoke test，输出通过对应 schema。该 smoke test 尚未替代仓库测试主机上的正式 pytest 运行证据。

## 已否定并正在移除的旧行为

```text
残基名统一转大写
alias/模糊名称匹配
单脚本同时完成 model、分类、共价、配位和最终整合
内置 coordination registry 自动扫描
金属配位永不影响 linked topology class
旧单一 classification_outputs.schema.yaml 作为唯一输出
```

## 尚未完成

```text
1. 重写 scripts/classify_structure.py，使其生成新版 observations 与 manifest；
2. 完成 PDB/mmCIF/AF3 缺失残基、RTP 端基模板与 CCD 两级缓存的集成测试；
3. 实现 scripts/build_classification_result.py；
4. 为两个 relation checker 增加 synthetic fixtures 和 executable tests；
5. 迁移 build_subagent_result.py 到新版输出；
6. 更新 SKILL.md、classification_rules.md、scripts/README.md；
7. 删除旧 alias/coordination 运行路径与旧单一输出 schema；
8. 运行 authoring 静态检查、全部 pytest、真实 PDB/mmCIF/AF3 与 Manager closure；
9. 更新 SYNC_STATUS、inventory 与最终验证记录。
```

## 当前验收结论

```text
inspect_model_scope: IMPLEMENTED_DRAFT, FORMAL_TEST_RUN_REQUIRED
new schemas: AUTHORED, META_VALIDATION_REQUIRED
relation checkers: IMPLEMENTED_DRAFT, TESTS_REQUIRED
classification parser migration: NOT_COMPLETE
final result builder: NOT_IMPLEMENTED
validator v1.2 overall: NOT_PASSED
```

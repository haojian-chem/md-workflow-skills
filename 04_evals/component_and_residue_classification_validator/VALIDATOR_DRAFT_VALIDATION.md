# component_and_residue_classification_validator legacy draft validation

原验证日期：2026-07-23  
状态更新：2026-07-27

## 状态

```text
SUPERSEDED_LEGACY_DRAFT_EVIDENCE
```

本文件记录的是 1.2 v1.2 redesign 之前的 0.1 单体 parser 与旧 wrapper 验证结果，仅用于保留实现历史。它不再是当前 Validator 的验收依据，也不得用于宣称当前 v1.2 流水线通过。

当前实现状态与待验收项以以下文件为准：

```text
04_evals/component_and_residue_classification_validator/V1_2_REDESIGN_IMPLEMENTATION.md
00_authoring/SYNC_STATUS.md
00_authoring/skill_inventory.yaml
00_authoring/content_maps/component_and_residue_classification_validator.yaml
```

## 原检查对象

原验证覆盖的主要运行路径为：

```text
旧 scripts/classify_structure.py 0.1 单体 parser
旧 scripts/build_subagent_result.py
旧 references/standard_residue_alias_registry.yaml
旧 references/coordination_detection_registry.yaml
旧 schemas/classification_outputs.schema.yaml
```

这些旧运行路径已被 v1.2 分阶段流水线替换，其中三份旧 registry/schema 文件已删除。

## 保留的历史测试证据

### 旧单体 parser

原执行命令：

```bash
pytest -q 04_evals/component_and_residue_classification_validator/test_classify_structure.py
```

原记录结果：

```text
10 passed in 5.59s
```

原覆盖范围包括：

- 标准蛋白、独立配体、水和单原子离子；
- PDB LINK 与 PDB→mmCIF connection roundtrip；
- geometry-only covalent decision；
- Zn coordination 与 topology 分离；
- 多模型一致与不一致；
- HID、MSE 与 ion-name conflict；
- entity/polymer metadata conflict；
- AF3 source label；
- 输入 hash、symlink 和跨 task 覆盖保护。

这些测试针对旧分类数据模型、旧 alias/coordination registry 和旧 `classification_outputs.schema.yaml`，不能推导当前 v1.2 对应功能已经通过。

### 旧 shared-result wrapper

原记录结果：

```text
4 passed in 8.08s
```

原覆盖范围包括：

- 旧 clear outcome 到 `DONE`；
- 旧 ambiguities 到 blocking confirmation；
- 旧 outcome/decision 一致性；
- allowed/forbidden output paths；
- 输入 STRUCTURE 保持原 validation state；
- 不产生 STRUCTURE artifact candidate。

当前 wrapper 已改为读取：

```text
classification_result.result_status
confirmation_requests.status
confirmation_requests.requests
```

因此旧 wrapper 测试结果同样不能作为当前通过证据。

## 当前 v1.2 验证入口

当前 CI 测试集合由：

```text
.github/workflows/component-classification-v1-2.yml
```

管理，包含：

```text
test_inspect_model_scope.py
test_classify_structure.py
test_build_subagent_result.py
test_v1_2_redesign_foundation.py
test_v1_2_relations_and_builder.py
test_v1_2_classification_engine.py
test_v1_2_terminal_rtp.py
```

本文件不记录这些测试已经通过。正式结果必须在测试实际运行后写入新的 v1.2 validation 记录，并至少包含：

- commit SHA；
- Python 和依赖版本；
- 完整测试命令；
- passed/failed/skipped 数量；
- schema meta-validation 结果；
- 真实 PDB/mmCIF/AF3 fixture 身份与 hash；
- Manager closure/FAST validation 结果；
- 已知限制和未覆盖范围。

## 历史结论

```text
legacy 0.1 parser tests: PASSED AT THE TIME, SUPERSEDED
legacy 0.1 wrapper tests: PASSED AT THE TIME, SUPERSEDED
current v1.2 validator: NOT EVALUATED BY THIS FILE
```

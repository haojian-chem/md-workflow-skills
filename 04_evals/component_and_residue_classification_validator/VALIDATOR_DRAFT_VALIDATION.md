# component_and_residue_classification_validator Draft Validation

日期：2026-07-23

## 检查对象

```text
02_validators/component_and_residue_classification_validator/SKILL.md
02_validators/component_and_residue_classification_validator/scripts/classify_structure.py
02_validators/component_and_residue_classification_validator/scripts/build_subagent_result.py
02_validators/component_and_residue_classification_validator/scripts/requirements.txt
02_validators/component_and_residue_classification_validator/scripts/README.md
02_validators/component_and_residue_classification_validator/references/classification_rules.md
02_validators/component_and_residue_classification_validator/references/standard_residue_alias_registry.yaml
02_validators/component_and_residue_classification_validator/references/covalently_linked_nonstandard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/references/coordination_detection_registry.yaml
02_validators/component_and_residue_classification_validator/schemas/classification_outputs.schema.yaml
00_authoring/content_maps/component_and_residue_classification_validator.yaml
04_evals/component_and_residue_classification_validator/test_classify_structure.py
04_evals/component_and_residue_classification_validator/test_build_subagent_result.py
04_evals/component_and_residue_classification_validator/fixtures/classification_cases.yaml
03_contracts/subagent_task.schema.yaml
03_contracts/subagent_result.schema.yaml
05_tools/runtime_schema_validator/validate.py
```

## 当前状态

```text
Skill file: present
local classification schema: meta-validation passed
structure parser: implemented
shared result wrapper: implemented
synthetic parser tests: 10 passed
synthetic result-wrapper tests: 4 passed
actual shared-contract/FAST integration test: authored, not run on test host
real ordinary PDB test: not run
real RCSB-style mmCIF test: not run
real AF3 CIF test: not run
status: draft
```

单元实现已存在，但真实结构文件和完整 Manager 集成尚未验收。

## 职责与边界

Validator：

- 只读取唯一授权 STRUCTURE 文件；
- 不修改结构；
- 使用确定性 parser 生成分类 report 和 result data；
- 使用确定性 wrapper 生成共享 `subagent_result` v2；
- 区分 Validator 执行状态与分类 outcome；
- 通过 `confirmation_items` 暴露阻断歧义；
- 不写 `00_project_state/**` 或 `00_project_records/**`；
- 不创建新的 STRUCTURE artifact candidate；
- 不将输入 STRUCTURE 提升为 VALIDATED。

Manager 负责接收 wrapper 返回对象、生成候选 `result.yaml`、执行 FAST validation，并提交管理记录。

## 分类语义

当前 draft 底线：

1. 显式共价连接、几何共价候选和金属配位候选必须分离；
2. 原子距离 alone 不能确认共价连接；
3. 金属配位关系不能把独立非标准组分改为相连非标准残基；
4. `HETATM` 不等于独立配体，`ATOM` 不等于标准残基；
5. residue name 只能作为 registry/context evidence，不能单独决定分类；
6. canonical residue 与 entity polymer metadata 冲突时返回 `METADATA_CONFLICT`；
7. 科学歧义使用 DONE + `CLASSIFICATION_DECISION_REQUIRED`，不得伪装成执行失败。

## 确定性结构 parser 验证

GitHub blob：

```text
classify_structure.py: a1c4ef75538825e79fb5924477ae57127ee6c48f
test_classify_structure.py: 3d8d69f1f4ebbef4f9ca8dad75557133464c0c64
parser version: 0.1.0
```

隔离环境执行：

```bash
pytest -q 04_evals/component_and_residue_classification_validator/test_classify_structure.py
```

结果：

```text
..........                                                               [100%]
10 passed in 5.59s
```

覆盖：

- 本地 schema meta-validation；
- 标准蛋白、独立配体、水和单原子离子；
- PDB LINK 与 PDB→mmCIF connection roundtrip；
- geometry-only covalent decision；
- Zn coordination 与 topology 分离；
- 多模型一致与不一致；
- HID、MSE 与 ion-name conflict；
- entity polymer metadata conflict；
- AF3 source label 与 CLI outputs；
- 输入 hash 不变、symlink 拒绝、跨 task 覆盖拒绝。

小型 synthetic fixture 性能：

```yaml
cli_wall_ms_median: 2864.686
parser_elapsed_ms_median: 124.304
runs: 5
```

CLI wall time 主要是 Python/Gemmi/jsonschema 进程启动和导入。

## Shared result wrapper

`build_subagent_result.py`：

- 校验实际 `task.yaml`；
- 校验 classification result；
- 核验 task/workstream ID、输入路径与 SHA-256；
- 检查 allowed read/write 和 forbidden paths；
- 把 ambiguities 转换为 confirmation item v2；
- 保持输入 STRUCTURE `present_unvalidated`；
- 生成 `artifact_candidates: []`；
- 校验最终 `subagent_result` v2；
- 禁止直接写入管理目录。

GitHub blob：

```text
build_subagent_result.py: 3895306d1d91d2db542187ad7791f0fa8cf871cd
```

使用 synthetic shared-contract mirror 执行的本地测试：

```text
....                                                                     [100%]
4 passed in 8.08s
```

覆盖：

- clear result → DONE、无 confirmation、建议进入 1.3；
- decision required → DONE + blocking confirmation；
- outcome 与 blocking decisions 一致性检查；
- allowed/forbidden output paths；
- 输入 STRUCTURE 保持 `present_unvalidated`；
- shared result 不产生 artifact candidate。

仓库中另有：

```text
04_evals/component_and_residue_classification_validator/test_build_subagent_result.py
```

该测试直接使用当前 `03_contracts/**`，并包含：

- actual `subagent_task` / `subagent_result` contract validation；
- Manager candidate logical-path overlay；
- ACTIVE `runtime_schema_validator --mode FAST`；
- result.task_id → task.yaml direct reference。

该实际仓库集成测试尚未在测试主机运行，因此不能记录为 PASS。

## 推荐测试命令

```bash
pytest -q \
  04_evals/component_and_residue_classification_validator/test_classify_structure.py \
  04_evals/component_and_residue_classification_validator/test_build_subagent_result.py
```

随后以真实 1.1 输出执行：

```text
Manager task.yaml
→ classify_structure.py
→ classification_result/report
→ build_subagent_result.py
→ Manager candidate result.yaml
→ runtime_schema_validator FAST
→ task closure
```

## 尚未验证

1. 普通真实 PDB、RCSB-style mmCIF 和真实 AF3 CIF；
2. 真实 mmCIF `struct_conn`、entity/polymer 和 branched/glycan metadata；
3. PDB `SSBOND`、`CONECT` 和无法解析的显式连接端点；
4. Cu、Fe、Mg、Ca、Al 等金属及 donor/altLoc/occupancy 情况；
5. insertion code、空 chain ID、重复 atom name 和大体系性能；
6. 测试主机上的 actual shared-contract/FAST integration test；
7. Manager → Workflow → Validator → FAST → closure 端到端测试；
8. residue alias 与 coordination screening registries 的科学审查和冻结。

完成真实文件和端到端测试前，Skill 保持 `draft`，不得宣布 1.2 运行验收通过。

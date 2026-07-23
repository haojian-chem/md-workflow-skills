# component_and_residue_classification_validator Draft Validation

日期：2026-07-23

## 检查对象

```text
02_validators/component_and_residue_classification_validator/SKILL.md
02_validators/component_and_residue_classification_validator/scripts/classify_structure.py
02_validators/component_and_residue_classification_validator/scripts/requirements.txt
02_validators/component_and_residue_classification_validator/references/classification_rules.md
02_validators/component_and_residue_classification_validator/references/standard_residue_alias_registry.yaml
02_validators/component_and_residue_classification_validator/references/covalently_linked_nonstandard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/references/coordination_detection_registry.yaml
02_validators/component_and_residue_classification_validator/schemas/classification_outputs.schema.yaml
00_authoring/content_maps/component_and_residue_classification_validator.yaml
04_evals/component_and_residue_classification_validator/test_classify_structure.py
04_evals/component_and_residue_classification_validator/fixtures/classification_cases.yaml
03_contracts/subagent_task.schema.yaml
03_contracts/subagent_result.schema.yaml
```

## 当前状态

```text
Skill file: present
subagent task/result contract: v2 referenced
local classification schema: meta-validation passed
behavior cases: 15
executable parser: implemented
synthetic executable tests: 10 passed
real ordinary PDB test: not run
real RCSB-style mmCIF test: not run
real AF3 CIF test: not run
status: draft
```

确定性解析器和 synthetic fixtures 已通过，但尚不代表真实结构文件和完整 Manager 集成已经验收通过。

## 已对齐职责

Validator：

- 只读取唯一授权 STRUCTURE 文件；
- 不修改结构；
- 输出分类 report 和 result data；
- 返回 `subagent_result.schema.yaml` v2；
- 区分 Validator 执行状态与分类 outcome；
- 通过 confirmation items 暴露阻断歧义；
- 不写 `00_project_state/**` 或 `00_project_records/**`；
- 不创建新的 STRUCTURE artifact candidate；
- 不将输入 STRUCTURE 提升为 VALIDATED。

解析器负责确定性读取、分类数据生成和本地 schema 校验；共享 subagent result 仍由 Validator 包装。

## 分类语义

当前 draft 底线：

1. 显式共价连接、几何共价候选和金属配位候选必须分离；
2. 原子距离 alone 不能确认共价连接；
3. 金属配位关系不能把独立非标准组分改为相连非标准残基；
4. `HETATM` 不等于独立配体，`ATOM` 不等于标准残基；
5. residue name 只能作为 registry/context evidence，不能单独决定分类；
6. canonical residue 与 entity polymer metadata 冲突时返回 `METADATA_CONFLICT`，不得静默覆盖；
7. 科学歧义可以返回 DONE + `CLASSIFICATION_DECISION_REQUIRED`，不得伪装成 Validator 执行失败。

## 输出类别

核心 topology classes：

```text
STANDARD_RESIDUE
COVALENTLY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT
ION
UNKNOWN
```

配位结果独立为：

```text
EXPLICIT_COORDINATION
GEOMETRIC_COORDINATION_CANDIDATE
AMBIGUOUS_CLOSE_CONTACT
```

## 可执行验证

验证对象：

```text
parser Git blob SHA: a1c4ef75538825e79fb5924477ae57127ee6c48f
test Git blob SHA: 3d8d69f1f4ebbef4f9ca8dad75557133464c0c64
parser version: 0.1.0
```

GitHub 中脚本与测试内容按原样重建到隔离目录运行。命令：

```bash
pytest -q 04_evals/component_and_residue_classification_validator/test_classify_structure.py
```

结果：

```text
..........                                                               [100%]
10 passed in 5.59s
```

覆盖：

- 本地输出 schema meta-validation；
- 标准蛋白、独立配体、水和单原子离子；
- PDB `LINK` 显式共价连接；
- PDB → mmCIF connection roundtrip；
- 仅几何短接触返回 blocking covalent decision；
- Zn 配位不改变 ligand topology class；
- 多模型分类一致与不一致；
- HID 与 MSE registry/context；
- 离子名称和原子组成冲突；
- entity polymer metadata 与 residue chemistry 冲突；
- AF3 CIF source label 和 CLI report/result 写入；
- 输入 SHA-256 不变；
- symlink 输入拒绝；
- 跨 task output 覆盖拒绝。

## 性能基准

环境：

```text
Python 3.13.5
gemmi 0.7.4
PyYAML 6.0.3
jsonschema 4.26.0
pytest 9.0.2
```

使用小型 PDB clear-classification fixture，独立 CLI 进程运行 5 次：

```yaml
cli_wall_ms:
  median: 2864.686
  min: 2840.194
  max: 2913.249
parser_elapsed_ms:
  median: 124.304
  min: 120.947
  max: 125.311
runs: 5
```

CLI wall time 主要包含 Python、Gemmi 和 jsonschema 进程启动/导入；解析与 schema 校验本身约 0.12 s。该基准只代表小型 synthetic fixture。

## 尚未验证

后续必须完成：

1. 使用普通真实 PDB、RCSB-style mmCIF 和真实 AF3 CIF 测试；
2. 验证真实 mmCIF `struct_conn`、entity/polymer、branched/glycan metadata；
3. 测试 PDB `SSBOND`、`CONECT` 和无法解析的显式连接端点；
4. 扩展 Cu、Fe、Mg、Ca、Al 等金属与不同 donor/altLoc/occupancy 情况；
5. 测试 insertion code、空 chain ID、重复 atom name 和大体系性能；
6. 将 parser 输出包装为完整 `subagent_result` v2，并执行 FAST runtime validation；
7. 运行 Manager → Workflow → Validator → FAST validation → closure 的端到端测试；
8. 审查并冻结 registries，尤其是 residue aliases 和 coordination screening cutoffs。

完成真实文件和端到端测试前，Skill 保持 `draft`，不得宣布 1.2 运行验收通过。

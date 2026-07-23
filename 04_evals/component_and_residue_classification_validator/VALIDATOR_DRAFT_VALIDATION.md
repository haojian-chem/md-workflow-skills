# component_and_residue_classification_validator Draft Validation

日期：2026-07-23

## 检查对象

```text
02_validators/component_and_residue_classification_validator/SKILL.md
02_validators/component_and_residue_classification_validator/references/classification_rules.md
02_validators/component_and_residue_classification_validator/references/standard_residue_alias_registry.yaml
02_validators/component_and_residue_classification_validator/references/covalently_linked_nonstandard_residue_registry.yaml
02_validators/component_and_residue_classification_validator/references/coordination_detection_registry.yaml
02_validators/component_and_residue_classification_validator/schemas/classification_outputs.schema.yaml
00_authoring/content_maps/component_and_residue_classification_validator.yaml
04_evals/component_and_residue_classification_validator/fixtures/classification_cases.yaml
03_contracts/subagent_task.schema.yaml
03_contracts/subagent_result.schema.yaml
```

## 当前静态状态

```text
Skill file: present
subagent task/result contract: v2 referenced
local classification schema: present
behavior cases: 15
executable parser: not implemented
real structure tests: not run
status: draft
```

本报告只记录规则、职责和 contract 的静态对齐，不代表结构解析和科学分类已经通过真实文件验收。

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

## 分类语义

当前冻结的 draft 底线：

1. 显式共价连接、几何共价候选和金属配位候选必须分离；
2. 原子距离 alone 不能确认共价连接；
3. 金属配位关系不能把独立非标准组分改为相连非标准残基；
4. `HETATM` 不等于独立配体，`ATOM` 不等于标准残基；
5. residue name 只能作为 registry/context evidence，不能单独决定分类；
6. 科学歧义可以返回 DONE + `CLASSIFICATION_DECISION_REQUIRED`，不得伪装成 Validator 执行失败。

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

## Fixtures 覆盖

15 个 behavior cases 覆盖：

- 标准蛋白、独立配体、水和单原子离子；
- 显式共价非标准残基；
- 仅几何短接触不得自动确认共价；
- 金属配位不改变 topology class；
- 多模型一致与不一致；
- entity metadata/坐标连接冲突；
- His protonation alias；
- MSE 聚合物上下文；
- 离子名与原子组成冲突；
- altLoc 影响配位候选；
- 输入不唯一、文件不可解析；
- 管理路径隔离；
- 本地结果 schema 与共享 result v2。

## 尚未验证

后续必须完成：

1. 实现确定性 PDB/mmCIF/AF3 CIF 解析器；
2. 对本地 `classification_outputs.schema.yaml` 运行 schema meta-validation；
3. 将 behavior cases 转换为真实结构 fixtures 和可执行 assertions；
4. 使用普通 PDB、RCSB mmCIF 和真实 AF3 CIF 测试；
5. 测试 PDB LINK/SSBOND/CONECT 与 mmCIF struct_conn；
6. 测试 Cu、Zn、Fe、Mg、Ca、Al 等金属配位候选；
7. 测试 altLoc、occupancy、insertion code 和多模型；
8. 核验报告写入幂等性和输入 SHA-256 不变；
9. 运行 Manager → Workflow → Validator → FAST validation → closure 的端到端测试。

完成上述测试前，Skill 保持 `draft`，不得宣布 1.2 运行验收通过。

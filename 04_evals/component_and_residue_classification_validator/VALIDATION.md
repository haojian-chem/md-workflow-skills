# Component and residue classification v1.2 validation

更新日期：2026-07-31

## 最终状态

```text
IMPLEMENTATION: PASS
CONTRACT_AND_CONTENT_OWNERSHIP: FROZEN
SYNTHETIC_AND_INTEGRATION: PASS
REAL_PDB_ACCEPTANCE: PASS
REAL_MMCIF_ACCEPTANCE: PASS
REAL_AF3_ACCEPTANCE: PASS
REAL_GROMACS_FORCE_FIELD_ACCEPTANCE: PASS
AUTHORING_STATIC_VALIDATION: PASS
MANAGER_TASK_CLOSURE: PASS
V1_2_TO_V1_3_SELECTION_IDENTITY_CONTRACT: PASS
DEPENDENCY_CLOSURE: PASS
VALIDATOR_V1_2_OVERALL: PASS
```

权威科学与运行时验收对应业务 head：

```text
b9faf855bbbd43fb9d5c215c0dbc52e5eee37da8
```

本文件记录当前权威证据。后续仅更新本记录或 content map 的提交不得被描述为重新执行了真实科学验收。

## 1. 合成与集成测试

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30625717907
job: 91140385874
tests: 88 passed
conclusion: success
```

覆盖：model scope、PDB/mmCIF/AF3、strict names、registry/force-field classification、缺失残基、双身份、altLoc、RTP、CCD、关系与 topology effect、final builder、Manager closure、1.2 → 1.3 selection identity、重原子并行 findings、config schemas、relation provenance，以及无运行时 monkey patch 的模块边界。

## 2. 真实输入验收

### 2.1 PDB

```text
workflow: .github/workflows/component-classification-v1-2-real-pdb.yml
run: 30625717868
job: 91140385088
tests: 3 passed
entries: 1VNS, 1A6M, 1CRN
conclusion: success
```

- `1VNS.pdb`：`SEQRES/REMARK 465`、35 个缺失残基、SO4 CCD；
- `1A6M.pdb`：altLoc、HEM CCD、`LINK + CONECT` 配位；
- `1CRN.pdb`：3 条 `SSBOND + CONECT` 二硫键。

聚合组分保留全部 observed residue records，final component membership 可由 1.3 直接读取。

### 2.2 mmCIF

```text
workflow: .github/workflows/component-classification-v1-2-real-mmcif.yml
run: 30625717890
job: 91140385164
tests: 3 passed
entries: 1VNS, 1A6M, 1CRN
conclusion: success
```

1VNS 的 PDB 与 mmCIF 来源分别记录 35 和 46 个缺失或未观测残基；实现保留各自来源事实，不制造跨格式数量一致性。

### 2.3 AlphaFold Server

```text
workflow: .github/workflows/component-classification-v1-2-real-af3.yml
run: 30625717836
job: 91140385012
tests: 2 passed
fixtures:
  - fold_1bk0_ipns_fe_template_free
  - fold_1dz9_p450cam_hem_template_free
conclusion: success
```

FE 保持 `ION_GROUP` 和实例级 identity；HEM baseline 为 `INDEPENDENT_COMPONENT`。AlphaFold Server JSON 由普通模块调用解析，不修改其他模块函数。

### 2.4 GROMACS force field

```text
workflow: .github/workflows/component-classification-v1-2-real-gromacs-forcefield.yml
run: 30625717945
job: 91140385217
tests: 1 passed
distribution: Ubuntu gromacs-data 2023.3-1ubuntu3
force_field: amber99sb-ildn.ff
conclusion: success
```

真实 RTP 中内部 ALA 完成重原子比较；没有显式 terminal mapping 的 N/C 端 GLY 返回 `REFERENCE_TEMPLATE_UNAVAILABLE`，不静默回退或应用 `.n.tdb/.c.tdb` patch。验收同时核验新的权威 heavy-atom fields 和 v1 兼容镜像。

## 3. Authoring 静态检查

```text
workflow: .github/workflows/component-classification-v1-2-authoring.yml
run: 30625717840
job: 91140384911
conclusion: success
```

```text
validate_md_skill: PASS
cross-file duplication: 0
architecture violations: 0
content maps validated: 18
content-map errors: 0
warnings: 0
```

## 4. Manager task closure

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30625717907
job: 91140385874
conclusion: success
```

已验证 wrapper 权限边界、一次 FAST validation、直接引用检查、原子提交、Workstream 前移、`TASK_DONE` 持久化和用户可见 closure summary。

## 5. 重原子权威数据模型

重原子检查现在拆分为：

```text
execution_status
findings[]
exact_comparison
atom_name_mapping_candidates[]
mapping_resolution_status
effective_comparison
```

验收结论：

- missing、unexpected 和 mapping required 可并行记录；
- CCD alternate atom name 不得删除 raw exact differences；
- mapping 未确认时不生成 effective comparison；
- 确认应用后只更新 effective comparison，exact comparison 永久保留；
- 旧 `status/missing_atoms/unexpected_atoms` 仅作为兼容镜像。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_scientific_contract_repairs.py
```

## 6. 关系端点与 altLoc 身份

关系端点的 source/current atom identity 均保存 exact altLoc ID。`endpoint_id` 由 source residue identity、exact atom name 和 exact altLoc identity 生成；A/B 构象不得折叠为同一 endpoint。final relation 和 1.3 lookup 均保留该身份。

## 7. Relation-definition provenance

`reference_manifest.yaml` 保存 `possible_connections.yaml` 与 `possible_coordination.yaml` 的 path、SHA-256 和状态。relation checker 与 final builder 必须与 manifest 完全一致；定义缺失、路径不同或哈希不同均属于技术失败。

## 8. Config 与软件依赖闭包

四个正式 config schemas：

```text
schemas/classification_config.schema.yaml
schemas/possible_connections_check_config.schema.yaml
schemas/possible_coordination_check_config.schema.yaml
schemas/classification_result_build_config.schema.yaml
```

所有 CLI 在业务处理前执行 Draft 2020-12 validation。`referencing` 已作为直接 Python 依赖声明；六个公开入口版本统一冻结为 `1.0.0`。

1.2 的稳定上游 contract 是 schema-valid `subagent_task` 中的 STRUCTURE file record 及 task 声明，不读取仍处于 draft 的 `source_recognition_report.yaml` 作为运行时接口。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_dependency_contracts.py
```

## 9. Side-effect-free 模块边界

`classification_engine.py` 现在只是无副作用 facade。以下逻辑由正式模块直接拥有：

- structural grouping：`classification_engine_core.py`；
- strict REMARK 465、missing-residue reconciliation 与输出归一：`sequence_missing.py`；
- AlphaFold Server JSON：`af3_server_sequence_reference.py`，由 `sequence_missing.py` 普通调用。

禁止通过 import-time assignment 修改 core/parser 函数。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_no_runtime_monkey_patch.py
```

## 10. Topology class 术语与 fallback registry

```text
旧 topology_class: COVALENTLY_LINKED_NONSTANDARD
新 topology_class: TOPOLOGY_LINKED_NONSTANDARD
旧 summary 字段: covalently_linked_nonstandard_count
新 summary 字段: topology_linked_nonstandard_count
```

`TOPOLOGY_LINKED_NONSTANDARD` 只描述 topology membership，关系类型仍单独记录。ACE、NME、NH2 的 fallback baseline 已移入：

```text
references/independent_nonstandard_residue_registry.yaml
```

具体实例只有在确认并应用 topology-forming relation 后才可提升。

## 11. 源身份、当前身份与 selection identity

残基与关系端点分别保存 immutable `source_*` provenance 和当前 STRUCTURE revision 的 `current_*` identity；`chain_index` 仅表示外部逻辑分组。

最终 `classification_result.yaml` 提供：

```text
source_structure
component_id
residue_id
endpoint_id
relation_id
component.residue_ids
component.missing_residue_ids
```

这些 ID 是由 1.2 materialize 的 opaque contract values，1.3 禁止重建。聚合水、离子和重复小分子保留全部实例记录；topology promotion 同步更新 membership 与 `instance_count`。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py
04_evals/component_and_residue_classification_validator/test_v1_2_selection_identity_contract.py
```

## 12. 结论

```text
local implementation: complete
contracts and content ownership: frozen
synthetic and integration validation: 88 passed
real PDB/mmCIF/AF3/GROMACS: passed
Authoring validation: passed
Manager closure: passed
dependency closure: passed
validator v1.2 overall: PASS
```

1.2 的科学语义、文件依赖、配置、provenance、模块边界及面向 1.3 的权威接口均已闭合。
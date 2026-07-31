# Component and residue classification v1.2 validation

更新日期：2026-07-31

## 最终状态

```text
IMPLEMENTATION: PASS
CONTRACT_AND_CONTENT_OWNERSHIP: FROZEN
SYNTHETIC_TESTS: PASS
REAL_PDB_ACCEPTANCE: PASS
REAL_MMCIF_ACCEPTANCE: PASS
REAL_AF3_ACCEPTANCE: PASS
REAL_GROMACS_FORCE_FIELD_ACCEPTANCE: PASS
AUTHORING_STATIC_VALIDATION: PASS
MANAGER_TASK_CLOSURE: PASS
V1_2_TO_V1_3_SELECTION_IDENTITY_CONTRACT: PASS
VALIDATOR_V1_2_OVERALL: PASS
```

1.2 的实现、共享接口、真实结构格式、真实力场、Authoring 检查、Manager 闭环以及面向 1.3 的选择身份接口均已验收。当前不存在阻止 1.2 进入 `chain_and_component_selection` 实现阶段的已知 contract 缺口。

本文件记录当前权威验收证据；历史调试运行不再作为当前 PASS 的依据。

## 1. 合成与集成测试

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30600172815
job: 91060901931
tests: 76 passed
conclusion: success
```

覆盖：

- model scope 与 selected-model barrier；
- PDB、mmCIF、AF3 CIF；
- strict residue/atom names；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS`；
- entity-based grouping 与 classification conflict 解耦；
- 缺失残基、author `source_resid` 和 mapping unresolved；
- `source_identity` / `current_identity` 双身份、兼容镜像一致性与 presence-status gate；
- 聚合水、离子和重复小分子的实例级 residue identity 保留；
- stable `component_id`、`residue_id`、`endpoint_id`、`relation_id`；
- AlphaFold Server 单 job JSON、隐式 chain ID 和 sequence comparison；
- altLoc、RTP、terminal mapping 和 CCD；
- possible connection、metal coordination 和 topology effect；
- `TOPOLOGY_LINKED_NONSTANDARD` 术语迁移；
- confirmation replay、final-result builder 和 shared result wrapper；
- Manager task → FAST validation → atomic commit → terminal event → visible closure。

## 2. 真实 PDB

```text
workflow: .github/workflows/component-classification-v1-2-real-pdb.yml
run: 30600172753
job: 91060901398
tests: 3 passed
conclusion: success
```

| Entry | SHA-256 | 主要验证内容 |
|---|---|---|
| `1VNS.pdb` | `3fa3f2f1c15cb1d02180a1da3457662ae2ed77d6611766f178c30c87390194ae` | single model、`SEQRES/REMARK 465`、35 个缺失残基、SO4 CCD |
| `1A6M.pdb` | `e6dd0945ba1ce2e3dc5525ee0c30e82fbb9497bc034663cda5e7592fecd8ceda` | altLoc、HEM CCD、`LINK + CONECT` 配位 |
| `1CRN.pdb` | `dee120c233163d052142ec47e4f54db58acb624fcb4e26c4ef1eaed41bc63ab1` | 3 条 `SSBOND + CONECT` 二硫键 |

真实 PDB 验收同时确认：聚合组分保留全部 observed residue records，最终 component membership 可由 1.3 直接读取。

## 3. 真实 mmCIF

```text
workflow: .github/workflows/component-classification-v1-2-real-mmcif.yml
run: 30600172773
job: 91060901684
tests: 3 passed
conclusion: success
```

| Entry | SHA-256 | 主要验证内容 |
|---|---|---|
| `1VNS.cif` | `ba9b8fc1c59df806bfe00aab17e9fbb86c712987eb59b5f5ff025359f9b446e6` | entity、author IDs、46 个 unobserved-residue records、SO4 CCD |
| `1A6M.cif` | `ce6574d325b046f46803df49894524537d098dfeee1033e76e62133e941fd948` | altLoc、HEM CCD、`_struct_conn` 配位 |
| `1CRN.cif` | `23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba` | 3 条 `_struct_conn` 二硫键 |

1VNS 的 PDB 与 mmCIF 源元数据分别记录 35 和 46 个缺失或未观测残基。实现保留各自来源事实，不制造跨格式数量一致性。

## 4. 真实 AlphaFold Server 输出

```text
workflow: .github/workflows/component-classification-v1-2-real-af3.yml
run: 30600172784
job: 91060901569
tests: 2 passed
conclusion: success
```

| Fixture | 模型 SHA-256 | Job JSON SHA-256 | 源结构事实 | 分类结果 |
|---|---|---|---|---|
| `fold_1bk0_ipns_fe_template_free` | `2a93f960885dc6bbd6c4de1b042b00e2d5afdb87b14ba0fb9a2b434528e761d6` | `1d97551888bb8cbe769aa4d375971b037918f892b236bb7a2f0a120b85dfdc13` | chain A protein + chain B FE | FE 为 `ION_GROUP`，同时保留 FE residue identity |
| `fold_1dz9_p450cam_hem_template_free` | `02360320a239937c1a91ee5f93717851c17a9852cdaa9a7eafa2b12844755a81` | `d9af80a7af93d3b875d634d205718c67d6c6d12cfdf4285310b15ce6539f06cf` | chain A protein + chain B HEM | HEM 为 `INDEPENDENT_COMPONENT` |

测试从仓库 fixture 无损重组真实模型与 job JSON，核验 SHA-256，并通过公开分类入口验证 sequence comparison、chain-group 表达及选择身份输出。

## 5. 真实 GROMACS force field

```text
workflow: .github/workflows/component-classification-v1-2-real-gromacs-forcefield.yml
run: 30600172760
job: 91060901361
tests: 1 passed
conclusion: success
```

```text
distribution: Ubuntu gromacs-data 2023.3-1ubuntu3
force-field root: /usr/share/gromacs/top/amber99sb-ildn.ff
```

- 内部 ALA 由真实 `aminoacids.rtp` 精确识别并通过重原子检查；
- N/C 端 GLY 在没有显式 terminal mapping 时返回 `REFERENCE_TEMPLATE_UNAVAILABLE`；
- 禁止静默回退到内部 GLY RTP；
- `.n.tdb/.c.tdb` 存在，但 1.2 不应用 terminal patch。

## 6. Authoring 静态检查

```text
workflow: .github/workflows/component-classification-v1-2-authoring.yml
run: 30600172744
job: 91060901329
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

确认局部执行编排、科学分类语义、脚本接口和跨阶段 contract 各自拥有唯一 owner；1.3 content map 不再引用已删除的 `classification_outputs.schema.yaml`。

## 7. Manager task closure

Manager closure 由第 1 节同一完整套件执行：

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30600172815
job: 91060901931
conclusion: success
```

已验证 wrapper 权限边界、一次 FAST validation、直接引用检查、原子提交、Workstream 前移、`TASK_DONE` 持久化和用户可见 closure summary。

## 8. Topology class 术语

```text
旧 topology_class: COVALENTLY_LINKED_NONSTANDARD
当前 topology_class: TOPOLOGY_LINKED_NONSTANDARD
旧 summary 字段: covalently_linked_nonstandard_count
当前 summary 字段: topology_linked_nonstandard_count
```

`TOPOLOGY_LINKED_NONSTANDARD` 只描述已进入连接拓扑的非标准组分。关系类型继续单独记录为 `COVALENT_CONNECTION` 或 `METAL_COORDINATION`，不得由 topology class 反推。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py
```

## 9. 源身份与当前身份

残基与关系端点分别保存 immutable `source_*` provenance 和当前 STRUCTURE revision 的 `current_*` identity。1.2 不修改结构，所以 observed 实例的值相等，但字段保持分离；missing expected residue 的 `current_identity` 必须为 `null`。`chain_index` 只表示外部逻辑分组。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py
```

## 10. 1.2 → 1.3 selection identity contract

最终 `classification_result.yaml` 现提供 1.3 所需的权威接口：

```text
source_structure
component_id
residue_id
endpoint_id
relation_id
component.residue_ids
component.missing_residue_ids
```

验收边界：

- ID 是由 1.2 materialize 的 opaque、versioned contract values；
- `component_id` 根据 final membership 生成，不使用或编码 `chain_index`；
- `residue_id` 来自 immutable `source_identity`；
- `endpoint_id` 来自 source residue identity 与 exact atom name；
- `relation_id` 对 endpoint 顺序和 evidence status 不敏感；
- 聚合 `SOLVENT_GROUP`、`ION_GROUP`、`REPEATED_SMALL_MOLECULE_GROUP` 不再删除实例记录；
- `residue_ids` 仅列出当前结构中存在的 coordinate-bearing members；
- `missing_residue_ids` 只保存 expected-but-unobserved provenance，不作为坐标选择对象；
- topology promotion 会同步修正原 component 的 membership 与 `instance_count`；
- 1.3 共价闭包使用 1.2 实际 relation type `COVALENT_CONNECTION`，不再依赖不存在的 `COVALENT/DISULFIDE/GLYCOSIDIC` 枚举。

永久回归：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_selection_identity_contract.py
```

## 11. 结论

```text
local implementation: complete
contracts and content ownership: frozen
synthetic and integration validation: passed
real PDB/mmCIF/AF3/GROMACS: passed
Authoring validation: passed
Manager closure: passed
v1.2 to v1.3 selection identity contract: passed
validator v1.2 overall: PASS
```

1.2 及其面向 1.3 的权威输入 contract 已完成。下一阶段是实现 deterministic `chain_and_component_selection`，而不是继续扩展 1.2 的身份模型。

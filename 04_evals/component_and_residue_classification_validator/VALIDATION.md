# Component and residue classification v1.2 validation

更新日期：2026-07-29

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
VALIDATOR_V1_2_OVERALL: PASS
```

1.2 的实现、共享接口、真实结构格式、真实力场、Authoring 检查和 Manager 闭环均已验收。当前不存在阻止 1.2 进入后续 Workflow 集成的已知缺口。

本文件记录当前权威验收证据。历史调试运行不再作为当前 PASS 的依据。

## 1. 合成与集成测试

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30452751000
job: 90578579001
tests: 62 passed
conclusion: success
```

覆盖：

- model scope 与 selected-model barrier；
- PDB、mmCIF、AF3 CIF；
- strict residue/atom names；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS`；
- entity-based grouping 与 classification conflict 解耦；
- 缺失残基、author `source_resid` 和 mapping unresolved；
- AlphaFold Server 单 job JSON、隐式 chain ID 和 sequence comparison；
- altLoc、RTP、terminal mapping 和 CCD；
- possible connection、metal coordination 和 topology effect；
- confirmation replay、final-result builder 和 shared result wrapper；
- Manager task → one FAST validation → atomic commit → terminal event → visible closure。

## 2. 真实 PDB

```text
workflow: .github/workflows/component-classification-v1-2-real-pdb.yml
run: 30452751113
job: 90578579395
tests: 3 passed
conclusion: success
```

| Entry | SHA-256 | 验证内容 |
|---|---|---|
| `1VNS.pdb` | `3fa3f2f1c15cb1d02180a1da3457662ae2ed77d6611766f178c30c87390194ae` | single model、`SEQRES/REMARK 465`、35 个缺失残基、SO4 CCD |
| `1A6M.pdb` | `e6dd0945ba1ce2e3dc5525ee0c30e82fbb9497bc034663cda5e7592fecd8ceda` | altLoc、HEM CCD、`LINK + CONECT` 配位 |
| `1CRN.pdb` | `dee120c233163d052142ec47e4f54db58acb624fcb4e26c4ef1eaed41bc63ab1` | 3 条 `SSBOND + CONECT` 二硫键 |

真实文件验证了 PDB `REMARK 465` 固定列解析、说明文字过滤和同名缺失残基 author-ID 映射。

## 3. 真实 mmCIF

```text
workflow: .github/workflows/component-classification-v1-2-real-mmcif.yml
run: 30452751015
job: 90578578794
tests: 3 passed
conclusion: success
```

| Entry | SHA-256 | 验证内容 |
|---|---|---|
| `1VNS.cif` | `ba9b8fc1c59df806bfe00aab17e9fbb86c712987eb59b5f5ff025359f9b446e6` | entity、author IDs、46 个 unobserved-residue records、SO4 CCD |
| `1A6M.cif` | `ce6574d325b046f46803df49894524537d098dfeee1033e76e62133e941fd948` | altLoc、HEM CCD、`_struct_conn` 配位 |
| `1CRN.cif` | `23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba` | 3 条 `_struct_conn` 二硫键 |

1VNS 的 PDB 与 mmCIF 源元数据分别记录 35 和 46 个缺失或未观测残基。实现保留各源格式的权威记录，禁止制造跨格式数量一致性。

## 4. 真实 AlphaFold Server 输出

```text
workflow: .github/workflows/component-classification-v1-2-real-af3.yml
run: 30452751038
job: 90578579075
tests: 2 passed
conclusion: success
```

用户提供的真实 AlphaFold Server template-free 输出：

| Fixture | 模型 SHA-256 | Job JSON SHA-256 | 源结构事实 | 分类结果 |
|---|---|---|---|---|
| `fold_1bk0_ipns_fe_template_free` | `2a93f960885dc6bbd6c4de1b042b00e2d5afdb87b14ba0fb9a2b434528e761d6` | `1d97551888bb8cbe769aa4d375971b037918f892b236bb7a2f0a120b85dfdc13` | chain A protein + chain B FE | FE 汇总为 `ION_GROUP` |
| `fold_1dz9_p450cam_hem_template_free` | `02360320a239937c1a91ee5f93717851c17a9852cdaa9a7eafa2b12844755a81` | `d9af80a7af93d3b875d634d205718c67d6c6d12cfdf4285310b15ce6539f06cf` | chain A protein + chain B HEM | HEM 为 `INDEPENDENT_COMPONENT` |

验收执行：

1. 从仓库 fixture 无损重组真实 `model_0.cif`；
2. 核验原始 size 与 SHA-256；
3. 恢复用户上传的原始 `job_request.json` 字节并核验 SHA-256；
4. 检查 CIF 自带 AlphaFold Server Output Terms 声明；
5. 直接检查源 CIF 中 chain B 的 FE/HEM 身份；
6. 使用公开 `classify_structure.py` 执行 `AF3_CIF + AF3_INPUT_JSON`；
7. chain A 输入序列与坐标精确匹配，结果为 `NO_MISSING_RESIDUES`；
8. 验证 FE/HEM 的实际 chain-group 表达；
9. 验证不存在 `SEQUENCE_REFERENCE_CONFLICT`。

真实输入保存在：

```text
04_evals/component_and_residue_classification_validator/fixtures/real_af3/
```

模型以同一次确定性 `xz+base64` 编码分片保存。测试在解码后核验原始模型大小和 SHA-256；传输编码不得改变科学输入身份。

## 5. 真实 GROMACS force field

```text
workflow: .github/workflows/component-classification-v1-2-real-gromacs-forcefield.yml
run: 30452750925
job: 90578579923
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
- `.n.tdb/.c.tdb` 存在，但 1.2 禁止应用 terminal patch。

## 6. Authoring 静态检查

```text
workflow: .github/workflows/component-classification-v1-2-authoring.yml
run: 30452751343
job: 90578580094
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

该运行对应文档层级整改后的最终文件，确认：

- `SKILL.md` 只拥有局部执行编排和 model branching；
- `classification_rules.md` 拥有科学判定语义；
- `scripts/README.md` 只拥有 CLI 与模块接口；
- 上下级规则未形成重复定义。

## 7. Manager task closure

Manager closure 由第 1 节同一完整套件执行：

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30452751000
job: 90578579001
conclusion: success
```

已验证：

- wrapper 只在业务目录生成 candidate result；
- wrapper 不修改 `00_project_state/**` 或 `00_project_records/**`；
- Manager 准备 result/state/event candidates；
- `runtime_schema_validator` 对 changed logical paths 执行一次 FAST；
- schema 与直接引用检查通过后原子提交；
- Workstream 前移、active task 清空、`TASK_DONE` 持久化；
- 基于已提交终态生成用户可见 closure summary。

## 8. 结论

```text
local implementation: complete
contracts and content ownership: frozen
all synthetic and integration validation: passed
real PDB/mmCIF/AF3/GROMACS: passed
Authoring validation: passed
Manager closure: passed
validator v1.2 overall: PASS
```

1.2 已完成。后续新增真实体系属于覆盖扩展，不再是 1.2 发布阻断项。

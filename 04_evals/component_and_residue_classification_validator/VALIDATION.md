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

1.2 的本地实现、共享接口、真实结构格式、真实力场、Authoring 检查和 Manager 闭环均已验收。当前不存在仍会阻止 1.2 进入后续 Workflow 集成的已知缺口。

## 1. 合成与集成测试

基线完整套件：

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30322483146
job: 90161060899
tests: 59 passed
conclusion: success
```

AlphaFold Server JSON 兼容补丁后的回归：

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30434118639
conclusion: success
```

新增覆盖：

- AlphaFold Server 顶层单 job 列表；
- `dialect: alphafoldserver`；
- entity 无显式 ID 时按 entity 顺序与 `count` 推导 `A/B/...`；
- ligand/ion 占用链 ID，但不生成 polymer sequence；
- 原有显式 ID AF3 JSON 行为保持不变。

完整测试仍覆盖 model scope、严格名称、registry/RTP/CCD、缺失残基、altLoc、关系确认、topology promotion、shared result wrapper 和 Manager task closure。

## 2. 真实 PDB

```text
workflow: .github/workflows/component-classification-v1-2-real-pdb.yml
run: 30320757292
job: 90155925129
artifact: 8673890539
tests: 3 passed
conclusion: success
```

| Entry | SHA-256 | 验证内容 |
|---|---|---|
| `1VNS.pdb` | `3fa3f2f1c15cb1d02180a1da3457662ae2ed77d6611766f178c30c87390194ae` | single model、`SEQRES/REMARK 465`、35 个缺失残基、SO4 CCD |
| `1A6M.pdb` | `e6dd0945ba1ce2e3dc5525ee0c30e82fbb9497bc034663cda5e7592fecd8ceda` | altLoc、HEM CCD、`LINK + CONECT` 配位 |
| `1CRN.pdb` | `dee120c233163d052142ec47e4f54db58acb624fcb4e26c4ef1eaed41bc63ab1` | 3 条 `SSBOND + CONECT` 二硫键 |

真实文件暴露并修正了 PDB `REMARK 465` 固定列解析、说明文字误识别和同名缺失残基 author-ID 映射问题。

## 3. 真实 mmCIF

```text
workflow: .github/workflows/component-classification-v1-2-real-mmcif.yml
run: 30321245758
job: 90157392672
artifact: 8674075169
tests: 3 passed
conclusion: success
```

| Entry | SHA-256 | 验证内容 |
|---|---|---|
| `1VNS.cif` | `ba9b8fc1c59df806bfe00aab17e9fbb86c712987eb59b5f5ff025359f9b446e6` | entity、author IDs、46 个 unobserved-residue records、SO4 CCD |
| `1A6M.cif` | `ce6574d325b046f46803df49894524537d098dfeee1033e76e62133e941fd948` | altLoc、HEM CCD、`_struct_conn` 配位 |
| `1CRN.cif` | `23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba` | 3 条 `_struct_conn` 二硫键 |

1VNS 的 PDB 与 mmCIF 源元数据分别记录 35 和 46 个缺失/未观测残基。实现保留各自权威记录，不制造跨格式数量一致性。

## 4. 真实 AlphaFold Server 输出

```text
workflow: .github/workflows/component-classification-v1-2-real-af3.yml
run: 30434118811
job: 90517778155
tests: 2 passed
conclusion: success
```

用户提供的真实 AlphaFold Server template-free 输出：

| Fixture | 模型 SHA-256 | Job JSON SHA-256 | 科学对象 |
|---|---|---|---|
| `fold_1bk0_ipns_fe_template_free` | `2a93f960885dc6bbd6c4de1b042b00e2d5afdb87b14ba0fb9a2b434528e761d6` | `1d97551888bb8cbe769aa4d375971b037918f892b236bb7a2f0a120b85dfdc13` | chain A protein + chain B FE |
| `fold_1dz9_p450cam_hem_template_free` | `02360320a239937c1a91ee5f93717851c17a9852cdaa9a7eafa2b12844755a81` | `d9af80a7af93d3b875d634d205718c67d6c6d12cfdf4285310b15ce6539f06cf` | chain A protein + chain B HEM |

验收执行：

1. 从仓库 fixture 无损重组真实 `model_0.cif`；
2. 强制核对原始 size 与 SHA-256；
3. 恢复用户上传的原始 `job_request.json` 字节并核对 SHA-256；
4. 检查 CIF 自带 AlphaFold Server Output Terms 声明；
5. 使用公开 `classify_structure.py` 执行 `AF3_CIF + AF3_INPUT_JSON`；
6. chain A 输入序列与坐标精确匹配，结果为 `NO_MISSING_RESIDUES`；
7. 1BK0 的 FE 形成 `ION_COMPONENT`；
8. 1DZ9 的 HEM 形成 `INDEPENDENT_COMPONENT`；
9. 无 `SEQUENCE_REFERENCE_CONFLICT`。

真实输入文件保存在：

```text
04_evals/component_and_residue_classification_validator/fixtures/real_af3/
```

模型以 `xz+base64` 分片保存；测试在解码前核验每片长度，在解码后核验原始模型哈希。该编码仅是仓库传输形式，不改变科学输入身份。

## 5. 真实 GROMACS force field

```text
workflow: .github/workflows/component-classification-v1-2-real-gromacs-forcefield.yml
run: 30321603205
job: 90158456934
artifact: 8674204994
tests: 1 passed
conclusion: success
```

```text
distribution: Ubuntu gromacs-data 2023.3-1ubuntu3
force-field root: /usr/share/gromacs/top/amber99sb-ildn.ff
```

- 内部 ALA 由真实 `aminoacids.rtp` 精确识别并通过重原子检查；
- N/C 端 GLY 在没有显式 terminal mapping 时返回 `REFERENCE_TEMPLATE_UNAVAILABLE`；
- 不会静默回退到内部 GLY RTP；
- `.n.tdb/.c.tdb` 存在，但 1.2 不应用 terminal patch。

## 6. Authoring 静态检查

```text
workflow: .github/workflows/component-classification-v1-2-authoring.yml
run: 30321998038
job: 90159314793
artifact: 8674336259
conclusion: success
```

```text
validate_md_skill: PASS
cross-file duplication: 0
architecture violations: 0
content maps validated: 18
```

AlphaFold Server 补丁后的 Authoring workflow 也在 PR #15 上通过。

## 7. Manager task closure

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30322483146
job: 90161060899
conclusion: success
```

已验证：

- wrapper 只在业务目录生成 candidate result；
- 不修改 `00_project_state/**` 或 `00_project_records/**`；
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

1.2 已完成。后续新增更多真实体系属于覆盖扩展，不再是 1.2 发布阻断项。

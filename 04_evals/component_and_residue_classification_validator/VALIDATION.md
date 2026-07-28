# Component and residue classification v1.2 validation

更新日期：2026-07-28

## 最终状态

```text
IMPLEMENTATION: PASS
CONTRACT_AND_CONTENT_OWNERSHIP: FROZEN
SYNTHETIC_TESTS: PASS
REAL_PDB_ACCEPTANCE: PASS
REAL_MMCIF_ACCEPTANCE: PASS
REAL_GROMACS_FORCE_FIELD_ACCEPTANCE: PASS
AUTHORING_STATIC_VALIDATION: PASS
MANAGER_TASK_CLOSURE: PASS
REAL_AF3_ACCEPTANCE: NOT_RUN — PENDING_REAL_INPUT
VALIDATOR_V1_2_OVERALL: NOT_PASSED
```

`VALIDATOR_V1_2_OVERALL` 保持 `NOT_PASSED` 的唯一原因是没有可用的真实 AlphaFold 3 预测输出及其对应输入序列参考。该状态不表示本地实现、PDB/mmCIF 路径、真实力场、Authoring 静态检查或 Manager 集成失败。

## 1. 合成测试

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30322483146
job: 90161060899
artifact: 8674497080
tests: 59 passed
conclusion: success
```

覆盖：

- 单/多 model 与输入哈希；
- `REGISTRY` / `FORCE_FIELD_ANALYSIS`；
- strict residue/atom names；
- polymer grouping 与 classification conflict 解耦；
- PDB/mmCIF 缺失残基、author `source_resid` 和 chain unresolved；
- AF3 FASTA/JSON 序列参考与 exact chain ID；
- altLoc 重原子检查短路；
- 内部/端基 RTP、重复非水 RTP 和普通水例外；
- CCD snapshot、本地目录、shared cache 和多候选冲突；
- possible connection/coordination；
- Mg/Zn `promote=false`；
- HEM–CYS/HIE `promote=true`；
- confirmation replay、final-result builder 和 shared result wrapper；
- Manager task → wrapper → one FAST → atomic commit → terminal event → visible closure。

## 2. 真实 PDB

```text
workflow: .github/workflows/component-classification-v1-2-real-pdb.yml
run: 30320757292
job: 90155925129
artifact: 8673890539
tests: 3 passed
conclusion: success
```

官方 RCSB 输入：

| Entry | SHA-256 | 验证内容 |
|---|---|---|
| `1VNS.pdb` | `3fa3f2f1c15cb1d02180a1da3457662ae2ed77d6611766f178c30c87390194ae` | single model、`SEQRES/REMARK 465`、35 个正式缺失残基、SO4 CCD |
| `1A6M.pdb` | `e6dd0945ba1ce2e3dc5525ee0c30e82fbb9497bc034663cda5e7592fecd8ceda` | altLoc、HEM CCD、`LINK + CONECT` HEM–HIS 配位 |
| `1CRN.pdb` | `dee120c233163d052142ec47e4f54db58acb624fcb4e26c4ef1eaed41bc63ab1` | 3 条 `SSBOND + CONECT` 二硫键 |

真实文件暴露并修正了 PDB `REMARK 465` 解析缺口：

- 只接受固定列中的合法数据行；
- 不再把说明文字解析为伪残基或伪链；
- 紧凑但仍符合固定列含义的行可右侧补空格后读取；
- 多个同名缺失残基已有 author ID 时，不因 sequence-position 配对不唯一而错误报告 `SOURCE_RESID_UNAVAILABLE`。

## 3. 真实 mmCIF

```text
workflow: .github/workflows/component-classification-v1-2-real-mmcif.yml
run: 30321245758
job: 90157392672
artifact: 8674075169
tests: 3 passed
conclusion: success
```

官方 RCSB 输入：

| Entry | SHA-256 | 验证内容 |
|---|---|---|
| `1VNS.cif` | `ba9b8fc1c59df806bfe00aab17e9fbb86c712987eb59b5f5ff025359f9b446e6` | entity、author IDs、46 个 `_pdbx_unobs_or_zero_occ_residues`、SO4 CCD |
| `1A6M.cif` | `ce6574d325b046f46803df49894524537d098dfeee1033e76e62133e941fd948` | altLoc、HEM CCD、`_struct_conn` 金属配位 |
| `1CRN.cif` | `23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba` | 3 条 `_struct_conn` 二硫键 |

1VNS 的 PDB 与 mmCIF 元数据并不相同：

```text
PDB REMARK 465: 35
mmCIF unobserved-residue records: 46
```

实现保留各源格式的权威记录，不强制制造跨格式数量一致性。

## 4. 真实 GROMACS force field

```text
workflow: .github/workflows/component-classification-v1-2-real-gromacs-forcefield.yml
run: 30321603205
job: 90158456934
artifact: 8674204994
tests: 1 passed
conclusion: success
```

环境：

```text
distribution: Ubuntu gromacs-data 2023.3-1ubuntu3
force-field root: /usr/share/gromacs/top/amber99sb-ildn.ff
```

关键参考文件：

```text
aminoacids.rtp   c522b05f33a0542d9862f6791e414e2229787abf74eabbb9be2fcf72ba5aecc5
aminoacids.n.tdb 30dd9f509e1cf4584d26214393a68a472ba6883f029b715682221c7ee9bc45bc
aminoacids.c.tdb 30dd9f509e1cf4584d26214393a68a472ba6883f029b715682221c7ee9bc45bc
```

验收结论：

- 内部 ALA 由真实 `aminoacids.rtp` 精确识别；
- 内部 ALA 重原子检查通过；
- N/C 端 GLY 在没有显式 terminal-template mapping 时返回 `REFERENCE_TEMPLATE_UNAVAILABLE`；
- 不会静默回退到内部 GLY RTP；
- `.n.tdb/.c.tdb` 确实存在，但本版本 1.2 不应用 terminal patch。

## 5. Authoring 静态检查

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

本轮同时修正：

- `component_and_residue_classification_validator.yaml` 的 v3 状态、ownership 和 external-reference access；
- `md-workflow-tool-authoring.yaml` 对 Tool Registry 的错误本地 ownership；
- `md_workflow_manager.yaml` 的 runtime-validator access 枚举。

## 6. Manager task closure

```text
workflow: .github/workflows/component-classification-v1-2.yml
run: 30322483146
job: 90161060899
artifact: 8674497080
conclusion: success
```

集成测试：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_manager_closure.py
```

已验证：

1. 持久化 `task.yaml`、route、初始 Workstream state 和 scope event；
2. wrapper 仅在业务目录生成 candidate result；
3. wrapper 不修改 `00_project_state/**` 或 `00_project_records/**`；
4. Manager 准备 result/state/event candidates；
5. `runtime_schema_validator` 对 3 个 changed logical paths 只执行一次 FAST；
6. schema 与直接引用检查通过；
7. PASS 后以原子替换提交；
8. Workstream 前移到 1.3，active task 清空；
9. `TASK_DONE` terminal event 与 result 持久化；
10. 依据已提交终态生成完整 task closure summary。

## 7. AF3 实际验收缺口

合成路径已经覆盖：

- `AF3_CIF` source format；
- 无输入序列时 `NOT_PERFORMED / AF3_INPUT_SEQUENCE_NOT_PROVIDED`；
- FASTA exact chain mapping；
- AF3 input JSON exact chain mapping；
- sequence length mismatch；
- chain ID conflict。

真实验收尚需用户或项目提供：

```text
actual *_model.cif
+
对应 fold_input.json / AlphaFold Server JSON / FASTA / 等价序列参考
```

普通 RCSB mmCIF 不得改名后冒充 AF3 输出。官方 AlphaFold 3 仓库未随附可直接用于该验收的预测输出 CIF，因此当前状态记录为：

```text
REAL_AF3_ACCEPTANCE: NOT_RUN — PENDING_REAL_INPUT
```

## 8. 当前结论

```text
local implementation: complete
contracts and content ownership: frozen
all repository-controlled validation: passed
real PDB/mmCIF/GROMACS: passed
Manager closure: passed
real AF3: pending external input
validator v1.2 overall: NOT_PASSED
```

收到真实 AF3 文件后，只需补充独立 real-AF3 acceptance workflow/test、记录输入 SHA-256，并更新本文件与 content map；无需重新设计 1.2。

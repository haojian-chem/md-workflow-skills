# Component and residue classification 1.2 validation

更新日期：2026-08-06

## 当前状态

```text
IMPLEMENTATION: PRESENT
LOCAL_AUTOMATED_SUITE: PASS
REAL_AF3_ACCEPTANCE: PASS
HOSTED_CORE_CI: PASS
CCD_SEED_COMPLETENESS_AND_HASH_VALIDATION: PASS
REAL_1.2_TO_1.3_ACCEPTANCE: PASS
REAL_PDB_MMCIF_GROMACS_REGRESSION: PENDING
OVERALL: PRESENT_UNVALIDATED
```

2026-07-31 的 PASS 证据对应旧业务 head `b9faf855bbbd43fb9d5c215c0dbc52e5eee37da8`。本次修改改变了 observations、关系决定、CCD 输入和最终整合契约，因此旧结果仅作历史记录，不能证明当前实现通过。

拓扑词汇迁移记录：
- 旧 topology_class：`COVALENTLY_LINKED_NONSTANDARD`；旧 summary：`covalently_linked_nonstandard_count`。
- 新 topology_class：`TOPOLOGY_LINKED_NONSTANDARD`；新 summary：`topology_linked_nonstandard_count`。

该迁移不改变“拓扑归属与证据状态分离”的原则。

## 已完成证据

```text
Python compile: PASS
Draft 2020-12 schema meta-validation: PASS
built-in CCD-compatible entries: 57 parsed and hash-matched
approved cofactor/ligand CCD seeds: 19 synced and independently verified
CCD seed workflow run: 31106984398
migrated Skill 1.2 automated suite: PASS (local)
real AlphaFold Server CIF + job request acceptance: PASS (local)
hosted core CI: PASS on code head 3a3a08cfd80e0e99b608ccfe7d128559485b7276
hosted core CI run: 31107690986
hosted implementation and authoring/closure CI: PASS for pre-seed implementation head
relation ID ordering/roles: PASS
relation decision + topology regrouping: PASS
current observations → final selection contract: PASS
historical 1.2→1.3 opaque-ID regression: PASS
real 1.2→1.3 selection acceptance: 3 PASS
real selection workflow run: 31107196592
real selection evidence artifact: 8970115209
```

真实 1.2→1.3 验收覆盖官方 1VNS、1A6M 和 1CRN PDB 输入，执行当前 1.2 分类与关系检查、1.3 选择以及选择验证。该证据不能替代尚未完成的独立 PDB/mmCIF/GROMACS 回归矩阵。

## 当前实现范围

- `classification_observations.yaml` 为结构/model 绑定的当前状态；
- 两个关系检查保留独立 result，并在同一受锁操作中更新 observations；
- 人工关系决定独立保存，稳定绑定 `relation_id`；
- CCD 只从内置和显式附加 indexed local libraries 读取；
- 批准 CCD seed 列表由单一 manifest 管理，并可通过网页 workflow 同步；
- final builder 不重新推断关系，继续输出 1.3 使用的 opaque IDs；
- Skill、科学规则、schema 与 CLI 文档保持单一内容所有者。

## 已知未闭合项

1. 独立真实 PDB、mmCIF 和 GROMACS 回归矩阵尚未重跑；
2. 合并前仍需复核最终 PR checks。

## 重新标记 PASS 的必要证据

```text
real PDB + mmCIF + GROMACS regression matrix
final PR checks on the merge candidate
```

在上述证据齐备前，任何状态文件、content map 或用户报告都不得写成 PASS、frozen 或 validated。

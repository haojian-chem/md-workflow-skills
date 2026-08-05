# Component and residue classification 1.2 validation

更新日期：2026-08-06

## 当前状态

```text
IMPLEMENTATION: PRESENT
LOCAL_AUTOMATED_SUITE: PASS
REAL_AF3_ACCEPTANCE: PASS
HOSTED_CI: PENDING
REAL_PDB_MMCIF_GROMACS: PENDING
REAL_1.2_TO_1.3_ACCEPTANCE: PENDING
OVERALL: PRESENT_UNVALIDATED
```

2026-07-31 的 PASS 证据对应旧业务 head `b9faf855bbbd43fb9d5c215c0dbc52e5eee37da8`。本次修改改变了 observations、关系决定、CCD 输入和最终整合契约，因此旧结果仅作历史记录，不能证明当前实现通过。

旧 topology_class / summary 迁移记录：`COVALENTLY_LINKED_NONSTANDARD` 与 `covalently_linked_nonstandard_count` 已统一为 `TOPOLOGY_LINKED_NONSTANDARD` 与 `topology_linked_nonstandard_count`；该迁移不改变“拓扑归属与证据状态分离”的原则。

## 已完成证据

```text
Python compile: PASS
Draft 2020-12 schema meta-validation: PASS
built-in CCD-compatible entries: 38 parsed and hash-matched
migrated Skill 1.2 automated suite: PASS (local)
real AlphaFold Server CIF + job request acceptance: PASS (local)
relation ID ordering/roles: PASS
relation decision + topology regrouping: PASS
current observations → final selection contract: PASS
historical 1.2→1.3 opaque-ID regression: PASS
```

本地自动测试证明当前实现和已迁移 fixtures 一致，但不能替代尚未完成的真实 PDB/mmCIF/GROMACS、完整下游选择和 hosted CI 证据。

## 当前实现范围

- `classification_observations.yaml` 为结构/model 绑定的当前状态；
- 两个关系检查保留独立 result，并在同一受锁操作中更新 observations；
- 人工关系决定独立保存，稳定绑定 `relation_id`；
- CCD 只从内置和显式附加 indexed local libraries 读取；
- final builder 不重新推断关系，继续输出 1.3 使用的 opaque IDs；
- Skill、科学规则、schema 与 CLI 文档保持单一内容所有者。

## 已知未闭合项

1. hosted GitHub Actions 尚待确认；
2. 真实 PDB、mmCIF 和 GROMACS 尚未重跑；
3. 完整的真实 1.2→1.3 选择验收尚未重跑；
4. 当前内置库已覆盖标准氨基酸、批准质子化变体、DNA/RNA 与 MSE/SEC/PYL；批准的较大辅因子/配体 seed 尚待补齐并逐项核验；
5. Authoring/Manager closure 的本次变更回归尚待确认。

## 重新标记 PASS 的必要证据

```text
hosted CI success
real PDB + mmCIF + GROMACS
real 1.2 → 1.3 selection acceptance
Authoring duplication/architecture/content-map checks
Manager FAST/atomic closure
CCD seed completeness and hash validation
```

在上述证据齐备前，任何状态文件、content map 或用户报告都不得写成 PASS、frozen 或 validated。

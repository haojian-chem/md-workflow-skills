# Chain and component selection v1 validation

更新日期：2026-07-31

## 最终状态

```text
OPERATION_IMPLEMENTATION: PASS
DEDICATED_VALIDATOR_IMPLEMENTATION: PASS
SHARED_RESULT_BUILDER: PASS
SYNTHETIC_AND_NEGATIVE_TESTS: PASS
REAL_V1_2_TO_V1_3_PDB_ACCEPTANCE: PASS
MANAGER_FAST_ATOMIC_CLOSURE: PASS
AUTHORING_STATIC_VALIDATION: PASS
CONTRACT_AND_CONTENT_OWNERSHIP: FROZEN
CHAIN_AND_COMPONENT_SELECTION_V1_OVERALL: PASS
```

`chain_and_component_selection` 与 `chain_and_component_selection_validator` 已完成确定性实现、真实 v1.2 输入验收、shared result 构建和 Manager 闭环。

## 1. Core Operation / Validator / shared-result tests

```text
workflow: .github/workflows/chain-component-selection-core.yml
run: 30603213366
executable job: 91070077238
tests: 11 passed
conclusion: success
```

覆盖：

- 所有公开 schema 的 Draft 2020-12 合法性；
- PDB 与 MMCIF Operation → Validator 闭环；
- 完整 residue、atom、altLoc、顺序和属性保留；
- selected-side confirmed connection 重建；
- confirmed covalent boundary BLOCKED 且不产生半成品；
- unknown component BLOCKED；
- coordination boundary 不自动扩展选择；
- PDB identifier representability gate；
- 坐标篡改即使同步刷新 hash 仍被 Validator 检出；
- 不诚实 manifest 被独立重算识别；
- `OPERATION_WITH_VALIDATOR` shared `subagent_result v2`；
- 未获 Validator 接受时禁止生成 validated STRUCTURE artifact candidate。

## 2. Real v1.2 → v1.3 PDB acceptance

```text
workflow: .github/workflows/chain-component-selection-real-pdb.yml
run: 30603213368
job: 91070077071
tests: 3 passed
conclusion: success
```

本次官方 RCSB 下载 SHA-256：

| Entry | SHA-256 | 验收内容 |
|---|---|---|
| `1VNS.pdb` | `3f9b6fc23036eced49c0fc175868842ff92fda3affe06d19c1e4123981422067` | 公开 v1.2 pipeline 生成 classification result；仅选择 polymer components；真实水和 SO4 排除；MMCIF candidate 由独立 Validator 接受 |
| `1A6M.pdb` | `da1d7341212da641a094a6ed4cf641d1adbab284ccd806c9516d46655efa68e1` | 公开 v1.2 pipeline；选择 protein + HEM；真实 altLoc 保留；MMCIF candidate 被接受 |
| `1CRN.pdb` | `42199a30a0701864a2a5cc76cd7f35cc544cd0e65fbcf63e03c166543249b811` | 公开 v1.2 pipeline；选择全部 components；PDB round-trip；Validator 以显式 PDB rounding warning 接受 |

真实验收没有手工伪造 `classification_result.yaml`，而是调用 1.2 的公开 model-scope、classification 和 final-result builder 入口。

## 3. Manager FAST / atomic closure

```text
workflow: .github/workflows/chain-component-selection-manager-closure.yml
run: 30603213363
job: 91070077145
tests: 1 passed
conclusion: success
```

已验证：

1. Operation 与 Validator 只写任务工作目录；
2. shared result builder 不修改 `00_project_state/**` 或 `00_project_records/**`；
3. Manager 准备 task result、validated STRUCTURE artifact set、Workstream state 和 project event log 四个候选；
4. `runtime_schema_validator` 对四个 logical paths 执行一次 FAST validation；
5. schema 与直接引用检查全部通过后才原子替换；
6. selected STRUCTURE artifact 注册为 `VALIDATED`；
7. Workstream 从 `1.3 chain_and_component_selection` 前移至 `1.4 altloc_occupancy_resolution`；
8. active task 清空，current STRUCTURE artifact 更新，`TASK_DONE` 持久化；
9. closure summary 包含任务结果、检查、输出、artifact 状态、warnings、report 和 next step。

## 4. Authoring validation

```text
workflow: .github/workflows/chain-component-selection-core.yml
run: 30603213366
authoring job: 91070077297
conclusion: success
```

```text
Operation Skill validation: PASS
Operation duplicate blocks: 0
Validator Skill validation: PASS
Validator duplicate blocks: 0
architecture violations: 0
content maps validated: 18
content-map errors: 0
warnings: 0
```

内容所有权边界：

- `references/selection_rules.md` 独占科学选择与 covalent-closure 语义；
- `SKILL.md` 只拥有局部执行/验证编排与 gate；
- `scripts/README.md` 只拥有 CLI、config 与模块接口；
- scripts 拥有确定性机械实现；
- Manager 独占管理记录、artifact 注册、FAST 和原子提交。

## 5. Frozen runtime behavior

### Operation

```text
version: 1.0.0
entry point: scripts/select_structure.py
```

- 显式 component-only selection；
- exactly one model；
- confirmed `COVALENT_CONNECTION` crossing boundary → BLOCKED；
- coordination / rejected covalent candidate crossing boundary → report only；
- complete observed residue copy；
- selected-side explicit connection reconstruction；
- PDB representability gate or coordinate MMCIF；
- candidate reparse and atomic output replacement。

### Validator

```text
version: 1.0.0
entry point: scripts/validate_selection.py
```

- independently recomputes expected selection；
- verifies complete one-to-one atom mapping；
- checks stable atom/altLoc identity, order, coordinates and attributes；
- checks selected-side explicit connections；
- checks manifest, counts, relation partitions, policies and provenance；
- distinguishes exact MMCIF validation from PDB fixed-width rounding validation。

### Shared result

```text
version: 1.0.0
entry point: scripts/build_subagent_result.py
```

Validated STRUCTURE artifact candidate 仅在 dedicated Validator 明确接受并覆盖 candidate/manifest/mapping hashes 后生成。

## 6. Conclusion

```text
implementation: complete
operation/validator contracts: frozen
synthetic and negative tests: passed
real v1.2 to v1.3 acceptance: passed
shared task result: passed
Manager closure: passed
Authoring validation: passed
chain and component selection v1 overall: PASS
```

下一 Workflow 子步骤：

```text
1.4 altloc_occupancy_resolution
```

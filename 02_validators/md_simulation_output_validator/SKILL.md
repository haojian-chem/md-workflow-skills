---
name: md_simulation_output_validator
description: 独立核验 stage-level MD simulation output manifest 是否准确覆盖当前 route scope 中全部 required VALIDATED run-level MD_OUTPUT artifacts、保持正确顺序与谱系，并返回唯一 stage-level MD_OUTPUT artifact candidate。该 Validator 不复制或拼接轨迹，也不判断科学收敛。
---

# 目标

验证：

```text
stage output manifest candidate
↔ validated protocol/plan/route scope
↔ required run-level MD_OUTPUT artifacts
```

通过后返回唯一 stage-level `MD_OUTPUT` artifact candidate，其业务文件为 collection manifest 和 validation report，底层 engine files 由 derived run-level artifacts 拥有。

# 职责边界

负责：

- 独立重算 scope 内 required run-unit set；
- 核验 manifest included run units 和 artifact IDs；
- 核验 run output manifests、segment order 和 lineage；
- 核验 final structure/checkpoint selection；
- 核验 excluded/superseded/invalidated artifacts；
- 写 validation report；
- 返回 stage-level MD_OUTPUT artifact candidate。

不得：

- 修改 manifest 或底层 run outputs；
- 复制、拼接、转换或裁剪 trajectory/energy；
- 目录扫描自动添加 outputs；
- 猜测 final-state selection；
- 判断采样充分、平衡或收敛；
- 修改 artifact/route/plan records；
- 写管理目录。

# 输入

作为 `OPERATION_WITH_VALIDATOR` 的 validator 部分，接收：

- assembly Operation result/report；
- stage manifest candidate；
- validated protocol/plan；
- active route 与明确 scope；
- required/skipped/out-of-scope run units；
- run-level VALIDATED MD_OUTPUT artifact records 和 manifests；
- resolved final-state decision，如适用；
- allowed read/write 与 forbidden paths；
- validation report/result data 路径。

# Preflight

确认：

1. task/workstream/route/plan IDs 一致；
2. Operation status 为 DONE；
3. manifest schema 有效；
4. protocol/plan/route 均未失效；
5. run-level artifact records 为 VALIDATED；
6. manifest 和 run manifests hashes 一致；
7. Validator 不以被验证对象为写目标；
8. report 输出路径受授权；
9. 管理目录禁止写入。

# 独立检查

## Scope coverage

- 从 route/plan 独立计算 required run units；
- manifest included set 必须精确匹配；
- skipped/out-of-scope run units 不得被加入；
- 目录中的旧 outputs 不得自动纳入。

## Artifact validity

- 每个 included run unit 具有唯一 VALIDATED run-level MD_OUTPUT；
- artifact 与 run manifest/workstream/plan 对齐；
- invalidated/superseded artifacts 不得 included；
- `derived_from_artifact_set_ids` 与 included artifact IDs 一致。

## Ordering

- segment order 与 plan dependency/topological order一致；
- trajectory/energy segment reference 不丢失 required production segments；
- sequence 无重复、缺口或未知 run unit。

## Final state

- final structure/checkpoint 来自 included artifact；
- source run unit 是 scope 内合法 terminal source；
- 多候选时必须有 resolved decision；
- manifest 不得使用 excluded/invalidated file。

## No data mutation

- engine file hashes 在 assembly 前后不变；
- manifest 只引用，不复制或拼接数据。

# Outcome codes

- `SIMULATION_OUTPUT_VALIDATED`；
- `SIMULATION_OUTPUT_VALIDATED_WITH_WARNINGS`；
- `SIMULATION_OUTPUT_VALIDATOR_INPUT_INCOMPLETE`；
- `SIMULATION_OUTPUT_SCOPE_MISMATCH`；
- `SIMULATION_OUTPUT_ARTIFACT_INVALID`；
- `SIMULATION_OUTPUT_SEGMENT_ORDER_INVALID`；
- `SIMULATION_OUTPUT_FINAL_STATE_INVALID`；
- `SIMULATION_OUTPUT_LINEAGE_INVALID`；
- `SIMULATION_OUTPUT_DATA_MUTATION_DETECTED`；
- `SIMULATION_OUTPUT_VALIDATOR_INTERNAL_FAILURE`。

只有前两个 outcome 可以返回 stage-level MD_OUTPUT candidate。

# Artifact candidate

通过时返回：

```yaml
artifact_type: MD_OUTPUT
files:
  - md_simulation_output_manifest.yaml
  - md_simulation_output_validation_report.yaml
derived_from_artifact_set_ids:
  - <all included run-level MD_OUTPUT artifact IDs>
```

candidate 在 Manager 接受前保持 UNVALIDATED。

# 输出

```text
04_md_simulation/99_validation/
├── md_simulation_output_validation_report.yaml
└── md_simulation_output_validation.log
```

# 自检

- [ ] included set 与 route scope 精确一致；
- [ ] 所有 run outputs 已 VALIDATED；
- [ ] segmented production 未丢失早期 segments；
- [ ] final state 唯一或有 resolved decision；
- [ ] invalidated/superseded outputs 已排除；
- [ ] 未复制/拼接/修改 engine data；
- [ ] candidate 只含 collection business files；
- [ ] 未声称科学收敛；
- [ ] 未修改管理记录。
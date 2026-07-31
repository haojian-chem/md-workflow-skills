from pathlib import Path

ROOT = Path(__file__).resolve().parent

operation_skill = '''---
name: chain_and_component_selection
description: Deterministically select complete classified components from exactly one structure model, preserve all selected coordinate objects and explicit selected-side relations, and emit an unvalidated STRUCTURE candidate plus full selection provenance.
---

# Chain and component selection

## 1. Purpose

This Operation implements structure-preparation substep `1.3 chain_and_component_selection`.

It selects a user-approved set of complete v1.2 components. It does not perform chemical editing, bond breaking, residue-range extraction, atom filtering, altLoc resolution, identifier normalization, protonation, residue repair or topology generation.

Scientific selection semantics are owned by:

```text
references/selection_rules.md
```

## 2. Runtime task unit

The enclosing task must use:

```text
mode: OPERATION_WITH_VALIDATOR
operation: chain_and_component_selection
validator: chain_and_component_selection_validator
```

The deterministic Operation entry point is:

```bash
python scripts/select_structure.py --config selection_operation_config.yaml
```

The combined task-result builder is:

```bash
python scripts/build_subagent_result.py ...
```

CLI/config details are owned by `scripts/README.md`.

## 3. Authoritative inputs

The Operation requires:

```text
classification_result.yaml
selection_spec.yaml
source structure
```

The classification result must satisfy:

```text
result_status: COMPLETE
unresolved_items: []
summary.unresolved_item_count: 0
```

The selection spec must validate against:

```text
schemas/selection_spec.schema.yaml
```

Only `component_id` values materialized by v1.2 are selectable. Natural-language context, file names, chain-name conventions and implicit selectors are not selection evidence.

## 4. Preflight gates

Before writing a candidate, `select_structure.py` verifies:

1. config, spec and classification schemas;
2. source and classification SHA-256 identities;
3. exact selected model identity;
4. existence of every requested component and observed member residue;
5. complete confirmed covalent closure;
6. source/output path separation and no output overwrite;
7. output extension/format consistency;
8. PDB identifier representability when PDB is requested.

A failed gate writes a structured BLOCKED report when a report path is available. It does not create a partial structure, manifest or mapping.

## 5. Deterministic execution

The Operation:

1. expands each selected component to its observed `residue_ids`;
2. excludes `missing_residue_ids` from coordinate selection while preserving their upstream provenance;
3. blocks any confirmed `COVALENT_CONNECTION` crossing the selection boundary;
4. records cross-boundary metal coordination and rejected covalent candidates without auto-expanding the selected set;
5. copies complete selected residues with all atoms and altLocs in source order;
6. preserves coordinates, occupancy, B factor, element and formal charge within the selected output format;
7. reconstructs selected-side confirmed covalent and metal-coordination connections;
8. writes PDB only when identifiers are losslessly representable, otherwise blocks;
9. reparses the temporary output and verifies atom count and stable identity before atomic replacement.

## 6. Operation outputs

Successful execution writes:

```text
selected_structure.pdb | selected_structure.cif
selection_manifest.yaml
selection_mapping.yaml
chain_and_component_selection_report.yaml
```

Contracts:

```text
schemas/selection_manifest.schema.yaml
schemas/selection_mapping.schema.yaml
schemas/selection_operation_report.schema.yaml
```

The structure, manifest and mapping remain `present_unvalidated` until the dedicated Validator accepts them.

## 7. Operation outcome codes

Successful outcomes:

```text
SELECTION_APPLIED
SELECTION_APPLIED_WITH_WARNINGS
```

Deterministic blocking outcomes include:

```text
SELECTION_SPEC_MISSING_OR_INVALID
SELECTION_REFERENCES_UNKNOWN_OBJECT
SELECTION_BREAKS_CONFIRMED_COVALENT_LINK
OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS
SOURCE_OR_CLASSIFICATION_HASH_MISMATCH
OUTPUT_CONFLICT
```

Unexpected execution failure is reported as:

```text
SELECTION_INTERNAL_FAILURE
```

## 8. Shared result and Manager handoff

`build_subagent_result.py` emits a shared `subagent_result v2` only when:

- task mode and Skill references match this Operation/Validator pair;
- Operation status is `DONE`;
- Validator status is `DONE`;
- Validator outcome is `SELECTION_VALIDATED` or `SELECTION_VALIDATED_WITH_WARNINGS`;
- Validator explicitly covers the candidate, manifest and mapping hashes.

The resulting STRUCTURE artifact candidate contains the validated selected structure. Manifest and mapping remain validated task evidence referenced by the component results.

The Operation and builder must not modify:

```text
00_project_state/**
00_project_records/**
```

Manager owns artifact-set registration, one FAST validation of result/artifact/state/event candidates, atomic commit, event append and Workstream advancement.

## 9. Scope boundary

This Operation does not claim:

- altLoc resolution;
- heavy-atom completeness;
- protonation correctness;
- final structure-preparation validity;
- topology readiness.

Those checks remain with later Workflow substeps and dedicated Validators.
'''

validator_skill = '''---
name: chain_and_component_selection_validator
description: Independently validate that chain/component selection exactly matches the explicit v1.2 component set, preserves all selected coordinate objects and attributes, retains selected-side explicit connections, and provides complete one-to-one atom mapping and provenance.
---

# Chain and component selection validator

## 1. Purpose

This Validator is the dedicated gate for `chain_and_component_selection`.

It confirms selection fidelity only. It does not validate altLoc choice, residue completeness, protonation, chemical correctness of an upstream relation, or final structure-preparation readiness.

## 2. Runtime task unit

The enclosing task must use:

```text
mode: OPERATION_WITH_VALIDATOR
operation: chain_and_component_selection
validator: chain_and_component_selection_validator
```

The deterministic entry point is:

```bash
python scripts/validate_selection.py --config selection_validation_config.yaml
```

CLI/config details are owned by `scripts/README.md`.

## 3. Required inputs

The Validator requires:

```text
selection_spec.yaml
classification_result.yaml
selected structure candidate
selection_manifest.yaml
selection_mapping.yaml
Operation report
```

All inputs must be regular files and satisfy their schemas and recorded SHA-256 identities.

## 4. Independent recomputation

The Validator independently rebuilds the expected selected set from:

```text
classification_result.yaml + selection_spec.yaml
```

It does not accept manifest counts, selected IDs or relation lists as sufficient evidence.

The recomputed plan must agree with:

- requested and actual component IDs;
- selected and excluded residue IDs;
- preserved and excluded explicit relations;
- cross-boundary coordination relations;
- cross-boundary rejected covalent candidates;
- counts, policies and decision provenance.

## 5. Structural checks

The Validator checks:

1. exactly one selected model;
2. exact selected atom/altLoc set and source order;
3. complete one-to-one atom mapping;
4. chain, residue, atom, insertion-code, altLoc and element identity;
5. coordinates, occupancy, B factor and formal charge;
6. preservation of selected-side confirmed covalent and coordination connections;
7. absence of unselected coordinate objects;
8. output format/path consistency;
9. source/spec/classification/candidate/manifest/mapping/Operation-report provenance.

For MMCIF, numerical attributes use tight comparison tolerances. For PDB, the Validator applies explicit serialization tolerances for fixed-width rounded numeric fields and reports the tolerance use as a warning.

## 6. Outputs

The Validator writes:

```text
chain_and_component_selection_validation_report.yaml
selection_validation_result.yaml
```

Contracts:

```text
schemas/selection_validation_report.schema.yaml
schemas/selection_validation_result.schema.yaml
```

Accepted outcomes:

```text
SELECTION_VALIDATED
SELECTION_VALIDATED_WITH_WARNINGS
```

Failure outcomes include:

```text
INVALID_SELECTION_SPEC_COVALENT_BREAK
SELECTED_SET_MISMATCH
ATOM_MAPPING_MISMATCH
COORDINATE_OR_ATTRIBUTE_CHANGED
EXPLICIT_CONNECTION_MISMATCH
MANIFEST_OR_HASH_MISMATCH
OUTPUT_FORMAT_MISMATCH
VALIDATOR_INPUT_INCOMPLETE
SELECTION_VALIDATOR_INTERNAL_FAILURE
```

## 7. Artifact semantics

Only an accepted Validator result may mark the selected structure, manifest and mapping as `present_validated` in the shared task result.

The resulting STRUCTURE artifact is valid for advancing to:

```text
1.4 altloc_occupancy_resolution
```

It is not yet a fully prepared structure.

## 8. Permission boundary

The Validator writes validation evidence only inside the assigned task work directory. It must not register artifact sets, update Workstream state, write task records or append project events.

Manager performs those changes after one FAST validation of its combined result/artifact/state/event candidates.
'''

(ROOT / "02_operations/chain_and_component_selection/SKILL.md").write_text(operation_skill, encoding="utf-8")
(ROOT / "02_validators/chain_and_component_selection_validator/SKILL.md").write_text(validator_skill, encoding="utf-8")

for relative in (
    "02_operations/chain_and_component_selection/scripts/select_structure.py",
    "02_operations/chain_and_component_selection/scripts/build_subagent_result.py",
    "02_validators/chain_and_component_selection_validator/scripts/validate_selection.py",
):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    if text.count('VERSION = "1.0.0-draft"') != 1:
        raise SystemExit(f"unexpected VERSION marker in {relative}")
    path.write_text(text.replace('VERSION = "1.0.0-draft"', 'VERSION = "1.0.0"', 1), encoding="utf-8")

validation = '''# Chain and component selection v1 validation

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
'''

validation_path = ROOT / "04_evals/chain_and_component_selection/VALIDATION.md"
validation_path.write_text(validation, encoding="utf-8")
draft_path = ROOT / "04_evals/chain_and_component_selection/SELECTION_DRAFT_VALIDATION.md"
if draft_path.exists():
    draft_path.unlink()

operation_map = ROOT / "00_authoring/content_maps/chain_and_component_selection.yaml"
text = operation_map.read_text(encoding="utf-8")
text = text.replace("contract_status: draft", "contract_status: frozen", 1)
text = text.replace("content_ownership_status: draft", "content_ownership_status: frozen", 1)
marker = "notes:\n"
evidence = '''validation_evidence:
  authoritative_record:
    path: 04_evals/chain_and_component_selection/VALIDATION.md
    status: current
  core_operation_validator_and_shared_result:
    workflow: .github/workflows/chain-component-selection-core.yml
    run_id: 30603213366
    job_id: 91070077238
    conclusion: success
    test_count: 11
  real_v1_2_to_v1_3_pdb_acceptance:
    workflow: .github/workflows/chain-component-selection-real-pdb.yml
    run_id: 30603213368
    job_id: 91070077071
    conclusion: success
    test_count: 3
    entries: [1VNS, 1A6M, 1CRN]
  manager_fast_atomic_closure:
    workflow: .github/workflows/chain-component-selection-manager-closure.yml
    run_id: 30603213363
    job_id: 91070077145
    conclusion: success
    test_count: 1
  authoring_static_validation:
    workflow: .github/workflows/chain-component-selection-core.yml
    run_id: 30603213366
    job_id: 91070077297
    conclusion: success
    validated_content_maps: 18
    operation_duplicate_blocks: 0
    validator_duplicate_blocks: 0
    architecture_violations: 0
    errors: 0
    warnings: 0
  overall:
    operation: passed
    dedicated_validator: passed
    shared_result: passed
    manager_closure: passed
    chain_and_component_selection_v1: passed
'''
if text.count(marker) != 1:
    raise SystemExit("operation content map notes marker mismatch")
operation_map.write_text(text.replace(marker, evidence + marker, 1), encoding="utf-8")

validator_map = ROOT / "00_authoring/content_maps/chain_and_component_selection_validator.yaml"
text = validator_map.read_text(encoding="utf-8")
text = text.replace("contract_status: draft", "contract_status: frozen", 1)
text = text.replace("content_ownership_status: draft", "content_ownership_status: frozen", 1)
if text.count(marker) != 1:
    raise SystemExit("validator content map notes marker mismatch")
validator_map.write_text(text.replace(marker, evidence + marker, 1), encoding="utf-8")

print("chain/component selection v1 finalization applied")

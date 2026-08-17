# Skill 1.2 deterministic scripts

本文件只说明 CLI、配置和模块边界。科学规则见 `../references/classification_rules.md`，执行编排见 `../SKILL.md`，字段约束见 `../schemas/`。

# Pipeline

```text
inspect_model_scope.py
→ model_scope.yaml

classify_structure.py
→ classification_observations.yaml
→ reference_manifest.yaml

check_possible_connections.py
→ relation_checks/possible_connections_result.yaml
→ update classification_observations.yaml

check_possible_coordination.py
→ relation_checks/possible_coordination_result.yaml
→ update classification_observations.yaml

record_relation_decisions.py
→ relation_decisions.yaml
→ rerun affected relation check(s)

build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md

build_subagent_result.py
→ subagent_result.yaml
```

# Entry points

## Model scope

```bash
python scripts/inspect_model_scope.py \
  --structure <structure> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <model_scope.yaml>
```

多 model 未选择时不得继续 baseline classification。

## Baseline classification

```bash
python scripts/classify_structure.py --config <classification_config.yaml>
```

配置固定 structure identity、classification mode、可选项目/力场/序列参考、`ccd.additional_library_paths` 和两个输出。内置 CCD-compatible root 由脚本固定，不写入配置。

`classify_structure.py` 通过内部 adapter 调用既有 baseline engine，再规范化为当前 observations contract；内部 adapter schema 不是公共输出 contract。

## Relation checks

```bash
python scripts/check_possible_connections.py --config <possible_connections_check_config.yaml>
python scripts/check_possible_coordination.py --config <possible_coordination_check_config.yaml>
```

两个配置都包含 structure、可选定义、普通 observations path、可选 relation decisions path 和 result output。observations/decisions 不要求配置 SHA；结构和定义仍要求 SHA。

每个脚本锁定 observations，生成并校验 result，应用决定、重算当前状态，然后成对提交 result 与 observations。重跑替换本关系类型的状态，不覆盖另一类型。

## Relation decisions

```bash
python scripts/record_relation_decisions.py \
  --config <relation_decision_record_config.yaml>
```

config 使用 exact confirmation request SHA 和便于交互的 `request_index`。脚本将其解析为稳定 `relation_id`；默认拒绝相反决定，只有显式 `--replace-existing` 或配置开关才替换。

## CCD library maintenance

```bash
python scripts/add_ccd_reference.py \
  --library <explicit-library-root> \
  --component-file <component.cif> \
  --category <category> \
  --source-type <RCSB_CCD_COMPONENT|SKILL_CUSTOM_COMPONENT|PROJECT_COMPONENT>
```

目标文件名来自 CIF component ID，不来自输入文件名。相同 ID/相同 SHA 幂等；不同 SHA 冲突。脚本不修改 residue registries。

## Final integration

```bash
python scripts/build_classification_result.py \
  --config <classification_result_build_config.yaml>
```

构建器要求两个 relation stages 已闭合且 `check_outputs` 的路径/hash 有效。它读取当前 observations，生成 opaque selection IDs 和最终下游 contract。关系决定不再由 build config 内联处理。

## Shared Validator result

```bash
python scripts/build_subagent_result.py ...
```

同时验证本地 classification contracts 与共享 `subagent_result v2`。

# Shared modules

```text
classification_engine*.py   baseline parsing/classification
ccd_reference.py            indexed local CCD-compatible lookup
observation_state.py         current-state normalization, locking, relation apply, regrouping
selection_identity.py        opaque component/residue/endpoint/relation IDs
structure_records.py         selected-model structure records
explicit_relations.py        PDB/mmCIF explicit relation evidence
sequence_missing.py          sequence and missing-residue evidence
rtp_reference.py             RTP parsing and atom comparison
classification_common.py     strict YAML, hashes, schema validation and atomic primitives
```

# I/O invariants

公开脚本必须使用显式路径、严格 YAML、Draft 2020-12 schema、结构/model 一致性检查和受控写入。禁止修改输入 STRUCTURE、联网获取 CCD、扫描未声明目录或写入管理目录。

退出码：

```text
0 deterministic processing completed
2 technical/configuration/schema/consistency failure
3 unexpected internal failure
```

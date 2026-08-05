---
name: component_and_residue_classification_validator
description: 在结构准备工作流 1.2 中，对一个已选 model 执行组分/残基分类、参考核验、关系检查和确认事项聚合，并输出供 1.3 直接消费的稳定分类契约。
---

# 目标与边界

本 Validator 实现 `structure_preparation_workflow` 的 1.2。它读取一个已登记的 STRUCTURE，不修改坐标文件，只生成分类证据、当前 observations、最终分类结果、报告和确认事项。

不读取 `source_recognition_report.yaml` 作为运行时 contract；只消费 task 中登记的 STRUCTURE file record。

权威归属：

```text
上级步骤和交接：01_workflows/structure_preparation_workflow/SKILL.md
科学语义：references/classification_rules.md
字段与枚举：schemas/*.schema.yaml
CLI 与模块边界：scripts/README.md
共享 task/result：03_contracts/*.schema.yaml
```

本文件只拥有局部执行顺序、model barrier、输入输出和完成条件；禁止重复定义科学规则或 schema 字段。

# 输入与输出

任务必须是指向本 Skill 的 `VALIDATOR` task，并提供唯一 STRUCTURE file record、结构格式、允许读写路径及 1.2 工作目录。可选输入包括项目残基定义、关系定义、序列参考、力场和附加 CCD-compatible library。

默认输出：

```text
01_structure_preparation/02_component_and_residue_classification/
├── model_scope.yaml
├── classification_observations.yaml
├── reference_manifest.yaml
├── relation_checks/
│   ├── possible_connections_result.yaml
│   └── possible_coordination_result.yaml
├── relation_decisions.yaml              # 首次人工关系决定后才创建
├── confirmation_requests.yaml
├── classification_result.yaml
├── classification_report.md
└── logs/
```

`classification_observations.yaml` 是同一 `structure_sha256 + selected_model_id` 的当前状态。结构或 model 改变时必须建立新的 observations 文件；不得把旧决定迁移到新结构状态。

# Preflight

执行前核验：

1. task、Skill ref、allowed/forbidden paths 与共享 schema；
2. STRUCTURE 为非 symlink 普通文件，声明 SHA-256、格式和 selected model 一致；
3. 配置、registries、schemas、脚本和显式参考路径可读；
4. `FORCE_FIELD_ANALYSIS` 提供有效力场根；
5. 输出位于业务目录，且不会无痕覆盖不同内容的正式结果；
6. 配置没有旧 CCD 下载/cache/snapshot 字段，也不要求修改结构或降低 gate。

技术失败时不得留下可被误认作正式完成结果的部分输出。

# 执行流程

## 1. Model scope

```bash
python scripts/inspect_model_scope.py \
  --structure <structure> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <model_scope.yaml>
```

单 model 自动选择；多 model 未选择时返回模型确认事项并停止。selected model 是完整分类前唯一允许的科学性前置 barrier。

## 2. Baseline classification

```bash
python scripts/classify_structure.py --config <classification_config.yaml>
```

生成 baseline observations 与 reference manifest。内置 CCD-compatible library 固定为 `references/ccd_library/`；附加库只能由 `ccd.additional_library_paths` 显式列出，不进行网络获取或目录扫描。

## 3. Relation checks

```bash
python scripts/check_possible_connections.py --config <possible_connections_check_config.yaml>
python scripts/check_possible_coordination.py --config <possible_coordination_check_config.yaml>
```

每个脚本在同一个受锁操作中：

```text
生成并校验独立 result
→ 应用 relation_decisions（若提供）
→ 更新对应 relation observations
→ 重算分类、chain groups、completed_checks、check_outputs 与 summary
→ 校验后成对提交 result 和 classification_observations.yaml
```

未提供某类关系定义时仍生成 `NOT_PERFORMED` result，并把对应 `completed_checks` 更新为 `NOT_PERFORMED`。

## 4. 记录人工关系决定

```bash
python scripts/record_relation_decisions.py --config <relation_decision_record_config.yaml>
```

该脚本是 `relation_decisions.yaml` 的唯一写入者。记录成功后，工作流必须立即重跑受影响的关系检查；只有 observations 已同步，决定处理才算闭合。

## 5. Final result

```bash
python scripts/build_classification_result.py --config <classification_result_build_config.yaml>
```

构建器读取已更新的 observations，不再次推断关系或重建 topology effect。它生成：

```text
confirmation_requests.yaml
classification_result.yaml
classification_report.md
```

非关系决定仍可通过绑定上一份 confirmation request SHA-256 的 `decision_source` 处理；关系决定必须走独立决定文件。

## 6. Shared result

```bash
python scripts/build_subagent_result.py ...
```

wrapper 同时验证本地结果和共享 `subagent_result v2`。1.3 只允许读取 `classification_result.yaml` 中物化的 opaque component/residue/endpoint/relation IDs，禁止自行复刻 ID 算法。

# 并发与写入

关系检查串行执行，并使用：

```text
classification_observations.yaml.lock
```

锁保护的是当前状态，不以 observations SHA-256 作为并发控制。结构、定义、参考和独立 result 保留 SHA-256；observations 通过结构/model 绑定、schema 校验、锁和原子提交保护。

# Outcome 与完成条件

```text
MODEL_SELECTION_REQUIRED
CLASSIFIED_CLEAR
CLASSIFICATION_DECISION_REQUIRED
INPUT_SCOPE_INVALID
UNSUPPORTED_OR_UNPARSEABLE_STRUCTURE
REFERENCE_CONFIGURATION_INVALID
VALIDATOR_INTERNAL_FAILURE
```

1.2 task 只有在以下条件同时满足时闭合：

- model 已明确，或已形成合法模型选择请求；
- 所有适用检查均为 `COMPLETED` 或 `NOT_PERFORMED`；
- relation result 与 observations 中 `check_outputs` 一致；
- 输入结构执行前后 SHA-256 不变；
- final result、report、confirmation count 和共享 result 一致；
- 输出集合没有越过 1.2 权限边界。

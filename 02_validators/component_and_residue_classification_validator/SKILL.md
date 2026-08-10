---
name: component_and_residue_classification_validator
description: Lightweight Runtime v2 的结构准备 1.2。对当前任务对象中的一个已确定结构 model 执行组分/残基分类、参考核验、关系检查和确认事项聚合，并输出供 1.3 直接消费的稳定 classification_result.yaml；不依赖 Legacy task/result/route/Workstream 闭环。
---

# 目标与边界

本 Validator 实现 `structure_preparation_workflow` 的 1.2。

它读取当前 Task Sheet 1.2 中记录的结构对象，不修改坐标文件，只在当前任务专属工作目录中生成分类证据、当前 observations、最终分类结果、报告和必要确认材料。

权威归属：

```text
上级步骤和交接：01_workflows/structure_preparation_workflow/SKILL.md
科学语义：references/classification_rules.md
字段与枚举：schemas/*.schema.yaml
CLI 与模块边界：scripts/README.md
Python 硬依赖：scripts/requirements.txt
```

`03_contracts/subagent_task.schema.yaml`、`subagent_result.schema.yaml` 和旧 runtime dependency closure 属于 Legacy 接口，不是 Lightweight 1.2 的普通执行依赖。

本文件拥有局部执行顺序、model barrier、Lightweight 输入/复用/输出接口和完成条件；禁止重复定义 `classification_rules.md` 或 schema 字段。

# Lightweight Runtime 接口

## Purpose

对当前结构对象的指定 model 建立稳定的 chain / component / residue / relation 分类结果，作为 1.3 的直接上游依据。

## Object requirements

当前 Task Sheet 的 1.2 `对象` 至少应明确一个现有结构文件：

- PDB；
- PDBx/mmCIF；
- AlphaFold 3 CIF。

对象可以同时记录已知的：

- source format；
- selected model；
- 结构来源任务或上游 1.1 结果。

如果结构包含多个 model 且用户尚未选择，1.2 先执行 model scope 检查，然后向用户确认 model；在 model 未确定前不得进入完整分类。

不要求 Task Sheet 建立稳定 object ID，也不要求重新读取 1.1 Skill。需要来源身份时直接读取当前结构和必要的上游正式结果。

## Reuse conditions

开始 1.2 时，在 `project_result_index.md` 的 1.2 已有结果中寻找可能匹配的 `classification_result.yaml`。

已有 1.2 结果只有在以下条件均能明确成立时才自动复用：

1. `classification_result.yaml` 的 `result_status` 为 `COMPLETE`；
2. 当前结构文件 SHA-256 与已有结果 `source_structure.sha256` 完全相同；
3. 当前要处理的 `selected_model_id` 与已有结果完全相同；
4. `classification_mode` 相同；
5. 影响分类结果的参考集合等价，包括适用的项目 residue definitions、Skill registries、force-field references、CCD references、sequence references 和 relation definition files；
6. 上述参考等价性可以由已有 `reference_manifest.yaml` 中记录的路径/状态/SHA-256 与当前实际配置核验；
7. 影响最终关系分类的人工决定与当前任务要求一致；如果已有结果依赖 `relation_decisions.yaml`，则当前任务必须能够确认继续采用相同决定；
8. 用户没有明确要求重新分类、重新检查、改用不同参考/模式或生成对照结果。

明确任一条件不满足时，直接执行新的 1.2，不询问用户是否“仍想复用”。

如果存在候选旧结果，但缺少证明等价性所需的 model、reference 或人工决定信息，则不得擅自继承，向用户确认。

相同文件名、相同链名或相同任务名称都不是复用依据。

如果确认复用：

- 当前任务直接引用来源任务的正式 1.2 结果；
- 不复制旧结果到当前任务目录；
- 不创建空的当前任务 1.2 目录；
- 在 Task Sheet `执行记录` 中记录复用来源任务和结果路径。

## Execution rules

科学执行流程见下文“执行流程”。

## Validation requirements

1.2 只有同时满足以下条件才标记为 `已完成`：

- Python 硬依赖满足；
- model 已唯一确定；
- 所有适用 relation checks 均已 `COMPLETED` 或明确 `NOT_PERFORMED`；
- relation result 与当前 `classification_observations.yaml` 一致；
- 所有阻塞型人工决定已经解决并反映到最终 observations/result；
- 输入结构执行前后 SHA-256 不变；
- `classification_result.yaml` 通过本地 schema 校验且 `result_status: COMPLETE`；
- `reference_manifest.yaml` 与实际参考输入一致；
- `classification_report.md` 与最终结果一致；
- 输出全部位于当前任务专属 1.2 工作目录。

如果模型选择、分类决定或关系决定仍待用户确认，当前子环节状态为 `未完成`，而不是额外建立 WAITING/BLOCKED runtime state。

## Official results

当前任务实际执行新的 1.2 时，正式结果至少包括：

1. 下游稳定分类结果：
   `01_structure_preparation/02_component_and_residue_classification/<task_id>/classification_result.yaml`
2. 参考来源清单：
   `01_structure_preparation/02_component_and_residue_classification/<task_id>/reference_manifest.yaml`
3. 人类可读报告：
   `01_structure_preparation/02_component_and_residue_classification/<task_id>/classification_report.md`

如果本次分类使用了人工 relation decisions，则额外把：

`01_structure_preparation/02_component_and_residue_classification/<task_id>/relation_decisions.yaml`

作为条件正式 provenance 结果记录。

以下文件属于当前任务内部执行状态或诊断材料，不默认登记到项目结果索引：

```text
model_scope.yaml
classification_observations.yaml
relation_checks/**
confirmation_requests.yaml
logs/**
```

它们仍应保留在当前任务目录，以支持未完成任务恢复和结果审计。

1.3 只允许直接消费 `classification_result.yaml` 中物化的 opaque component/residue/endpoint/relation IDs，不得自行复刻 ID 算法。

# 工作目录与任务隔离

1.2 的稳定基础目录：

```text
<project_root>/01_structure_preparation/02_component_and_residue_classification/
```

可以在项目初始化时建立到这一层。

当前任务实际执行目录：

```text
<project_root>/01_structure_preparation/02_component_and_residue_classification/<task_id>/
```

Manager 只把该路径写入 Task Sheet，不创建 `<task_id>/`。

Task Execution Agent 必须先完成 1.2 reuse 检查。只有确认不能直接复用、确实需要执行新的 1.2 时，才创建当前任务目录。

不同任务不得把正式结果直接写到共同基础目录，也不得覆盖其他任务目录中的分类结果。

# Python dependency preflight

1.2 的 Python 硬依赖由：

`scripts/requirements.txt`

定义：当前至少包括 `gemmi`、`PyYAML`、`jsonschema` 和 `referencing`。

Lightweight Runtime 不再要求 Manager 在另一个对话中调用 Legacy `runtime_dependency_preflight`、构造 task identity，再决定是否启动 1.2 Agent。

Task Execution Agent 进入 1.2 后，应在读取大量科学 references/schemas 和执行分类前，首先做一次最小依赖检查：

- 所需 Python 包可以 import；
- 版本满足 `scripts/requirements.txt`；
- Python 环境可执行 1.2 scripts。

依赖不满足时：

- 不创建或不继续写正式分类结果；
- 当前 1.2 标记为 `未完成`；
- 在 Task Sheet 记录缺失依赖；
- 向用户说明需要解决的环境问题。

不得为了使用旧 preflight Tool 而重新构造 Legacy `task.yaml`、subagent result 或 R4 closure。

# Preflight

依赖检查通过后，执行本 Validator 的业务 Preflight：

1. 当前任务单中的子环节是 1.2；
2. `对象` 指向唯一明确的结构文件；
3. 结构是非 symlink 普通文件，可读，SHA-256 可计算，source format 可识别；
4. 如果 model 已指定，必须能与结构实际 model 对应；
5. 当前工作目录符合 `.../02_component_and_residue_classification/<task_id>/`；
6. 配置、registries、schemas、脚本和显式参考路径可读；
7. `FORCE_FIELD_ANALYSIS` 提供有效力场根；
8. 输出不会覆盖其他任务目录或无痕覆盖当前任务中不同内容的正式结果；
9. 配置没有旧 CCD 下载/cache/snapshot 字段，也不要求修改结构或降低 gate。

技术失败时不得留下可被误认作正式完成结果的部分输出。

# 当前任务目录内容

实际执行时默认生成：

```text
01_structure_preparation/02_component_and_residue_classification/<task_id>/
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

`classification_observations.yaml` 是同一 `structure_sha256 + selected_model_id` 的当前任务状态。当前任务中结构或 model 改变时，不得把旧 observations/decision 静默当作新状态继续使用。

# 执行流程

## 0. Reuse 与目录创建

1. 读取 Task Sheet 的 1.2 对象和预留工作目录；
2. 读取本 Skill；
3. 检索 result index 中已有 1.2 正式结果；
4. 按 reuse conditions 核验；
5. 可复用则直接更新 Task Sheet 并结束，不创建当前任务目录；
6. 不可复用时做 dependency preflight；
7. dependency PASS 后才创建当前任务 1.2 目录并进入科学执行。

## 1. Model scope

```bash
python scripts/inspect_model_scope.py \
  --structure <structure> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <task_work_directory>/model_scope.yaml
```

单 model 自动选择；多 model 未选择时生成/记录模型确认信息并停止。selected model 是完整分类前唯一允许的科学性前置 barrier。

## 2. Baseline classification

```bash
python scripts/classify_structure.py --config <classification_config.yaml>
```

所有 config/output 路径都必须指向当前任务专属 1.2 目录或明确的只读参考文件。

生成 baseline observations 与 reference manifest。内置 CCD-compatible library 固定为 `references/ccd_library/`；附加库只能由 `ccd.additional_library_paths` 显式列出，不进行网络获取或无界目录扫描。

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

## 4. 人工关系决定

当 relation check 产生需要用户判断的事项时，Task Execution Agent 在当前对话中向用户确认。

确认后使用：

```bash
python scripts/record_relation_decisions.py --config <relation_decision_record_config.yaml>
```

写当前任务目录中的 `relation_decisions.yaml`。

记录成功后立即重跑受影响的 relation check；只有 observations 已同步，决定处理才算闭合。

`record_relation_decisions.py` 仍是 `relation_decisions.yaml` 的唯一正式写入入口。

## 5. Final result

```bash
python scripts/build_classification_result.py --config <classification_result_build_config.yaml>
```

构建器读取当前任务目录中的已更新 observations，不再次推断关系或重建 topology effect。

它生成：

```text
confirmation_requests.yaml
classification_result.yaml
classification_report.md
```

如果最终仍存在 blocking confirmation，1.2 保持 `未完成`。只有所有必要决定闭合且 `classification_result.yaml` 达到 `COMPLETE` 才进入完成记录。

## 6. 完成记录

1. 按 Validation requirements 核验正式结果；
2. 将 Task Sheet 1.2 状态改为 `已完成`；
3. `对象` 保留当前实际分类的结构对象；
4. `工作目录` 保留当前任务专属目录；
5. `主要结果` 记录 official results 的完整路径；
6. 把 official results 登记到 `project_result_index.md` 的 1.2 部分；
7. 后续 1.3 的对象至少应能定位 `classification_result.yaml`，并按实际任务需要同时定位相应结构文件。

# 并发与写入

当前同一任务目录中的关系检查串行执行，并使用：

```text
classification_observations.yaml.lock
```

锁保护当前任务的 observations，不以 observations SHA-256 作为并发控制。

不同 Task ID 使用不同 1.2 目录，不共享可变 observations、relation decisions 或 final result 文件。

结构、定义、参考和独立 result 保留 SHA-256；observations 通过结构/model 绑定、schema 校验、锁和原子提交保护。

# Outcome 与任务状态

原有业务 outcome 可以继续用于科学脚本/报告，例如：

```text
MODEL_SELECTION_REQUIRED
CLASSIFIED_CLEAR
CLASSIFICATION_DECISION_REQUIRED
INPUT_SCOPE_INVALID
UNSUPPORTED_OR_UNPARSEABLE_STRUCTURE
REFERENCE_CONFIGURATION_INVALID
VALIDATOR_INTERNAL_FAILURE
```

但 Lightweight Task Sheet 不增加对应 runtime state machine。

映射原则：

- 所有完成条件满足 → `已完成`；
- 已开始但仍需 model/分类/关系确认、环境修复或技术恢复 → `未完成`；
- 尚未实际处理 → `待执行`。

# Legacy 兼容材料

以下内容暂时保留用于历史测试或旧项目迁移，但不属于 Lightweight 1.2 普通执行路径：

- `03_contracts/subagent_task.schema.yaml`；
- `03_contracts/subagent_result.schema.yaml`；
- `scripts/build_subagent_result.py`；
- `runtime_dependency_preflight` 的 task-identity / R4 closure 接口；
- Manager pre-Agent dispatch gate；
- Workstream / route / event closure。

不得为了复用这些旧包装层而让当前 Task Execution Agent 再建立 Legacy runtime objects。

# 自检

- [ ] 当前对象是明确的结构文件；
- [ ] 已先执行 1.2 reuse 检查；
- [ ] 可复用时未创建空的当前任务 1.2 目录；
- [ ] 不能复用时先检查最小 Python 依赖，再加载/执行完整科学流程；
- [ ] 实际执行目录是 `02_component_and_residue_classification/<task_id>/`；
- [ ] 输入结构执行前后 SHA-256 不变；
- [ ] model 在完整分类前已明确；
- [ ] reference manifest 与实际参考输入一致；
- [ ] relation decisions 已在当前任务目录闭合并同步到 observations；
- [ ] `classification_result.yaml` 为 `COMPLETE` 后才把 1.2 标记为已完成；
- [ ] official results 已写入 Task Sheet 和 result index；
- [ ] 1.3 继续消费 opaque IDs，不复刻 1.2 ID 算法；
- [ ] 未创建 Legacy task/result/route/event/Workstream records。

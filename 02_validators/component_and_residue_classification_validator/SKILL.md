---
name: component_and_residue_classification_validator
description: 对一个 PDB、mmCIF 或 AlphaFold 3 CIF 先解析 model 范围，再在已选 model 上调用确定性脚本完成 entity、chain group、残基、缺失残基、重原子、可能共价连接和金属配位检查，生成统一分类结果、报告与确认事项。
---

# 目标

执行 `structure_preparation_workflow` 的 1.2 子步骤，为一个已登记 STRUCTURE 输入生成可复现的分类证据和 Validator result。

本文件只定义：

- 1.2 的局部执行顺序；
- model selection barrier；
- 输入、输出和 preflight；
- 确定性脚本调用；
- outcome code 与 task 完成条件。

分类、RTP/CCD、缺失残基、连接和配位的科学语义只由：

```text
references/classification_rules.md
```

定义。

# 权威来源与继承边界

本 Skill 必须遵循以下上级或关联权威文件：

```text
00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md
01_workflows/structure_preparation_workflow/SKILL.md
03_contracts/subagent_task.schema.yaml
03_contracts/subagent_result.schema.yaml
references/classification_rules.md
schemas/*.schema.yaml
```

定义归属：

- 四层权限、用户交互和管理目录提交权由 `layer_boundaries.md` 定义；
- 结构准备阶段顺序及 1.2 与后续步骤的交接由 `structure_preparation_workflow/SKILL.md` 定义；
- 科学判定语义由 `classification_rules.md` 定义；
- 字段、枚举和机器可读约束由 schemas 定义；
- 本文件只拥有本 Validator 的局部执行编排和 model branching。

禁止在本文件复制或改写上述文件已经拥有的通用职责、科学规则或字段定义。

# 局部执行职责

本 Skill 必须：

- 读取 task 授权的一个当前 STRUCTURE 文件；
- 核验输入路径、SHA-256、格式和 selected model；
- 调用本 Skill 的确定性脚本完成检查；
- 在授权业务目录写入机器可读输出、报告和必要日志；
- 将本地确认请求转换为共享 `confirmation_items`；
- 区分技术失败与科学决定请求；
- 按 `03_contracts/subagent_result.schema.yaml` 返回精简 Validator result。

局部硬约束：

- selected model 未解决前，禁止启动完整分类；
- 禁止由 LLM 手工复现逐原子解析、RTP/CCD 比较、几何检查或结果整合；
- 禁止绕过 `classification_rules.md` 中的确认条件或降低任何输入、哈希、schema 和引用 gate；
- task 必须按照上级层级规则将管理目录列入 forbidden paths。

# 运行输入

必须接收符合：

```text
03_contracts/subagent_task.schema.yaml
```

的 `VALIDATOR` task unit。

任务至少提供：

- `task_id`、`workstream_id`、`workflow_name`；
- `task_unit.mode: VALIDATOR`；
- validator Skill ref 指向本 Skill；
- 项目根与 1.2 工作目录；
- 唯一、已登记的 STRUCTURE 文件记录；
- `source_recognition` 的格式结论和输入 SHA-256；
- allowed read/write paths 与 forbidden paths；
- 分类模式；
- 必需输出路径。

条件输入：

```text
project_residue_definitions.yaml
possible_connections.yaml
possible_coordination.yaml
FORCE_FIELD_ANALYSIS 的 force-field root 与 terminal-template mappings
AF3 输入 JSON、FASTA 或其他序列参考
CCD 本地参考目录、共享 cache 和 retrieval policy
已记录的模型选择或上一轮 confirmation decisions
```

未提供项目残基定义、共价定义或配位定义时，相应阶段必须生成 schema 合法的未提供或 `NOT_PERFORMED` 记录。

# 输出目录

默认业务目录：

```text
01_structure_preparation/
└── 02_component_and_residue_classification/
    ├── model_scope.yaml
    ├── classification_observations.yaml
    ├── reference_manifest.yaml
    ├── relation_checks/
    │   ├── possible_connections_result.yaml
    │   └── possible_coordination_result.yaml
    ├── confirmation_requests.yaml
    ├── classification_result.yaml
    ├── classification_report.md
    ├── reference_data/
    │   └── ccd/
    └── logs/
```

禁止增加无业务含义的 `runs/` 层。

已有不同内容的有效结果禁止无痕覆盖。重跑或重新整合必须由 Manager 在 task 中指定新修订路径或受控归档方案。

本步骤的输出仅限分类记录、参考快照、关系检查、确认请求、报告和日志。禁止创建新的 STRUCTURE artifact candidate，也禁止改变输入 STRUCTURE 的 validation status。

# Preflight

执行前必须确认：

1. task 通过共享 schema，mode、workflow 和 Skill ref 正确；
2. 唯一结构输入位于 allowed read paths，且为非空普通文件；
3. 输入不是 symlink，声明 SHA-256 与实际内容一致；
4. source format 为 `PDB | MMCIF | AF3_CIF`；
5. 所有配置和参考路径均显式给出，禁止无界扫描项目或文件系统；
6. 输出路径位于 allowed write paths，管理目录位于 forbidden paths；
7. 本地 schemas、registries、脚本和依赖均可读取；
8. `FORCE_FIELD_ANALYSIS` 提供有效 force-field root；
9. 配置若要求修改结构、绕过确认、降低 gate 或启用已删除的旧 runtime path，必须拒绝执行。

Preflight 技术失败时，禁止写入可被误认作正式结果的部分输出。

# 执行流程

## 1. 模型范围

调用：

```bash
python scripts/inspect_model_scope.py \
  --structure <recognized_structure> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <model_scope.yaml>
```

单 model：

```text
AUTO_SELECTED
→ 继续完整分类
```

多 model 且尚无已记录选择：

```text
USER_SELECTION_REQUIRED
→ 禁止启动 classify_structure.py
→ 返回 blocking confirmation item
```

用户选择 model 后，必须使用相同结构、相同结构哈希和已有 `model_scope.yaml`，并显式传入：

```text
--selected-model-id <model_id>
```

## 2. 基础解析与分类

调用：

```bash
python scripts/classify_structure.py \
  --config <classification_config.yaml>
```

生成：

```text
classification_observations.yaml
reference_manifest.yaml
```

脚本配置必须固定 structure path、SHA-256、source format、selected model、分类模式、参考来源和输出路径。科学判定必须遵循 `references/classification_rules.md`。

## 3. 可能共价连接

调用：

```bash
python scripts/check_possible_connections.py \
  --config <possible_connections_check_config.yaml>
```

生成：

```text
relation_checks/possible_connections_result.yaml
```

未提供 `possible_connections.yaml` 时，必须生成 schema 合法的 `NOT_PERFORMED` 结果。

## 4. 金属配位

调用：

```bash
python scripts/check_possible_coordination.py \
  --config <possible_coordination_check_config.yaml>
```

生成：

```text
relation_checks/possible_coordination_result.yaml
```

未提供 `possible_coordination.yaml` 时，必须生成 schema 合法的 `NOT_PERFORMED` 结果。

## 5. 最终整合

调用：

```bash
python scripts/build_classification_result.py \
  --config <classification_result_build_config.yaml>
```

生成：

```text
confirmation_requests.yaml
classification_result.yaml
classification_report.md
```

整合器必须核验 model、结构哈希、上游输出哈希和 schema version 一致。

首次整合通常不带 decisions。再次整合必须：

- 使用新修订输出路径；
- 提供 `decision_source`；
- 将决定绑定到上一份 `confirmation_requests.yaml` 的 exact SHA-256；
- 重新生成结果和报告。

禁止覆盖上一轮结果，也禁止将未绑定或过期决定应用到当前输入。

## 6. 共享 Validator result

调用：

```bash
python scripts/build_subagent_result.py \
  --task <task.yaml> \
  --classification-result <classification_result.yaml> \
  --confirmation-requests <confirmation_requests.yaml> \
  --report <classification_report.md> \
  --log <classification.log> \
  --output <subagent_result.yaml>
```

wrapper 必须同时验证本地结果 schema 和共享 `subagent_result v2` contract。

# 完整扫描与阻断

model selection 是完整分类前唯一允许的科学性前置 barrier。

selected model 确定后，必须完成所有仍可执行的分类、参考核验、缺失残基、关系检查和结果整合，再统一返回确认事项。

处理原则：

- 技术无效且无法生成可信结果时立即失败；
- 科学歧义、分类冲突和候选关系必须累计到结构化输出；
- 禁止将科学不确定性伪装成技术失败；
- 禁止将技术失败产生的部分输出作为有效 1.2 结果。

具体进入确认或只记录的条件由 `references/classification_rules.md` 定义，本文件不重复列举。

# Outcome codes

```text
MODEL_SELECTION_REQUIRED
CLASSIFIED_CLEAR
CLASSIFICATION_DECISION_REQUIRED
INPUT_SCOPE_INVALID
UNSUPPORTED_OR_UNPARSEABLE_STRUCTURE
REFERENCE_CONFIGURATION_INVALID
VALIDATOR_INTERNAL_FAILURE
```

语义：

- `MODEL_SELECTION_REQUIRED`：model 枚举成功，但多 model 尚未选择；
- `CLASSIFIED_CLEAR`：完整结果为 `COMPLETE`；
- `CLASSIFICATION_DECISION_REQUIRED`：完整扫描完成，结果为 `PENDING_USER_CONFIRMATION`；
- 其余代码表示技术失败，禁止伪造正式分类通过。

本 Validator 只返回 outcome、findings、confirmation items 和 gate 建议。后续暂停、状态提交和 route decision 由上级层级按其权威规则处理。

# 完成条件

只有同时满足以下条件，本次 1.2 Validator task 才闭合：

- selected model 已明确，或已形成 schema 合法的模型选择请求；
- 所有实际执行的确定性脚本退出状态与输出 schema 一致；
- 输入结构在执行前后 SHA-256 不变；
- 每个适用阶段均有正式结果或明确的 `NOT_PERFORMED` 状态；
- 跨阶段 model、结构哈希和直接引用一致；
- `classification_result.yaml`、报告和 confirmation count 一致；
- 共享 `subagent_result v2` 校验通过；
- 输出集合严格限于本步骤声明的业务记录、报告、参考快照和日志。

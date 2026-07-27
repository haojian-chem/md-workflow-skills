---
name: component_and_residue_classification_validator
description: 对结构准备阶段的一个 PDB、mmCIF 或 AlphaFold 3 CIF 先解析 model 范围，再对已选 model 完成精确、区分大小写的 entity、chain group、残基、缺失残基、重原子、可能共价连接和金属配位检查，生成统一分类结果与待用户确认事项；不修改结构、不执行链选择，也不把金属配位伪写成普通共价键。
---

# 目标

为 `structure_preparation_workflow` 的 1.2 子步骤生成可复现的分类证据：

- 先确定唯一 selected model；
- 解析 selected model 中的 entity、源 chain、残基和原子事实；
- 按项目定义、Skill registry、entity context 或指定力场 RTP 生成两个正交分类标签；
- 检查 PDB/mmCIF 缺失残基，并在用户提供输入序列时检查 AF3；
- 依据 CCD 或 RTP 核验单构象残基的重原子；
- 按项目明确提供的原子对检查可能共价连接和金属配位；
- 应用已经确认的 topology-forming relation，生成最终 `chain_groups`；
- 完成所有可执行检查后统一返回待用户确认事项；
- 按 `03_contracts/subagent_result.schema.yaml` 返回精简 Validator result。

详细科学规则只由：

```text
references/classification_rules.md
```

定义。

# 职责边界

负责：

- 读取 task 授权的一个当前 STRUCTURE 文件；
- 核验输入路径、SHA-256、格式和 selected model；
- 调用本 Skill 的确定性脚本，不由 LLM 逐原子模拟；
- 写入 1.2 的机器可读输出、Markdown 报告和必要日志；
- 将 `confirmation_requests.yaml` 转换为共享 `confirmation_items`；
- 区分技术失败与科学决定请求。

不负责：

- 修改、重排、删除、补全或质子化结构；
- 选择保留哪些链、配体、水或离子；
- 处理 altLoc/occupancy；
- 判断后续结构完整性 gate；
- 生成或整合拓扑；
- 使用 `specbond.dat` 判断当前结构是否建键；
- 自动应用 `.n.tdb`、`.c.tdb` 或 terminal patch；
- 自动选择水模型；
- 修改 `00_project_state/**` 或 `00_project_records/**`；
- 直接向用户提问、创建 Agent 或选择下一 Workflow task。

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
- allowed read/write paths；
- forbidden paths，包括管理目录；
- 本次运行使用的分类模式；
- 必需的输出路径。

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

未提供项目残基定义、共价定义或配位定义不是错误；相应检查记录为未提供或未执行。

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

不增加无业务含义的 `runs/` 层。已有有效结果不得无痕覆盖；需要重新整合或重跑时，由 Manager 为新 task 指定新修订文件路径或受控归档方案。

本 Validator 不创建新的 STRUCTURE artifact candidate，也不改变输入 STRUCTURE 的 validation status。

# Preflight

执行前确认：

1. task 通过共享 schema，mode、workflow 与 Skill ref 正确；
2. 唯一结构输入位于 allowed read paths，且不是 symlink、目录或空文件；
3. source format 为 `PDB | MMCIF | AF3_CIF`；
4. 所有配置文件路径均明确，不无界扫描项目目录；
5. 输出路径位于 allowed write paths，且管理目录在 forbidden paths；
6. 本地 schemas、strict registries、脚本与依赖可读取；
7. `FORCE_FIELD_ANALYSIS` 提供有效 force-field root；
8. 配置中没有要求本 Validator 修改结构、绕过确认或降低 gate；
9. 旧版 alias registry 和内置 coordination registry 不进入新版运行路径。

Preflight 技术失败时不写正式部分结果。

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

多 model 且尚无用户选择：

```text
USER_SELECTION_REQUIRED
→ 不启动 classify_structure.py
→ Validator DONE + blocking confirmation item
```

用户选择 model 后，使用相同结构和 `model_scope.yaml` 受控记录：

```text
--selected-model-id <model_id>
```

然后继续完整分类。

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

分类模式：

```text
REGISTRY:
  project definition
  → exact Skill registry
  → entity/polymer context

FORCE_FIELD_ANALYSIS:
  project definition
  → exact RTP residue block
  → unresolved-only Skill registry fallback
  → entity/polymer context
```

名称严格区分大小写。不得调用旧 alias registry，也不得对 residue/atom name 执行 `.upper()`。

基础解析必须完成：

- selected model 的 entity、chain、residue、atom 读取；
- baseline `chain_groups` 和 `chain_index`；
- PDB/mmCIF 缺失残基检查；
- AF3 缺失检查的显式输入序列条件；
- single-conformation residue 重原子核验；
- multiple-conformation residue 只记录多构象，不执行重原子比较；
- CCD snapshot/local/cache/download 顺序与 provenance；
- 项目/registry/force-field 冲突、RTP 重复、作者编号或 chain 归属问题的完整累计。

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

工具对每条项目定义枚举所有精确实例组合，分别记录显式连接、距离、altLoc 状态和 topology effect candidate。它不创建键、不选择最近一对、不修改 observations。

未提供 `possible_connections.yaml` 时仍生成合法 `NOT_PERFORMED` 结果，避免整合器猜测文件缺失语义。

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

工具必须：

- 区分 metal 与 donor；
- 核验定义元素与结构元素；
- 单独记录显式 relation 和几何；
- 保持 relation type 为 `METAL_COORDINATION`；
- 原样记录 `promote_nonstandard_to_linked`；
- 不因一个金属存在多个供体而自动报冲突；
- 不直接修改 topology class 或 chain group。

未提供定义文件时生成合法 `NOT_PERFORMED` 结果。

## 5. 最终整合

调用：

```bash
python scripts/build_classification_result.py \
  --config <classification_result_build_config.yaml>
```

整合器必须：

1. 核验 model、结构哈希、observations 哈希和 schema version 一致；
2. 应用 `CONFIRMED_BY_STRUCTURE` 的共价关系；
3. 对 topology-forming metal coordination 仅在显式确认或用户确认后应用 promotion；
4. 读取与上一份 `confirmation_requests.yaml` 哈希绑定的已有决定；
5. 重建最终 `chain_groups`；
6. 写出剩余 confirmation requests；
7. 写出 `COMPLETE` 或 `PENDING_USER_CONFIRMATION` 分类结果；
8. 从机器可读结果渲染 Markdown 报告，不在报告中新增科学判断。

首次整合通常不带 decisions。用户决定后的再次整合必须写入新修订文件，不覆盖上一轮结果。

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

# 完整扫描与阻断规则

模型范围是完整解析前的独立 barrier。

selected model 确定后：

- 不在第一项科学歧义处停止；
- 完成所有仍可执行的 residue、CCD/RTP、missing-residue、connection 和 coordination 检查；
- 将所有需用户处理的问题统一写入 `confirmation_requests.yaml`；
- 科学决定请求可以对应 `status: DONE` 的 Validator execution，因为检查本身已经成功完成。

立即技术失败包括：

```text
输入不可读取或哈希失配
selected model 不存在
配置/schema 无效
force-field mode 缺少有效 RTP 来源
结构或参考文件系统性不可解析
输出路径未授权或无法一致写入
跨文件 hash/model 引用不一致
```

累计确认事项包括：

```text
项目定义与 Skill/力场分类冲突
非水 RTP 精确名称重复定义
端基 RTP 映射歧义
几何支持的共价或配位候选
显式 relation 与项目定义冲突
缺失残基 source_resid 或 chain_index 无法确定
AF3/序列参考冲突
多个不同内容的有效本地 CCD 候选
```

明确缺失重原子、单个 CCD 获取失败、partner/atom 不存在、无显式关系的元素异常、几何不支持和多构象事实只记录，不自动形成确认项。

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
- 其余代码表示技术失败，不允许伪造正式分类通过。

# Gate 建议

```text
CLASSIFIED_CLEAR
→ 返回 Workflow，由 Workflow 决定下一 task

MODEL_SELECTION_REQUIRED | CLASSIFICATION_DECISION_REQUIRED
→ Manager 暂停当前 Workstream 并处理全部 confirmation items

technical failure
→ 不允许使用部分输出作为有效 1.2 结果
```

本 Validator 不自行修改 route、Workstream 状态或项目记录。

# 完成条件

只有同时满足以下条件，本次 1.2 Validator task 才闭合：

- selected model 已明确，或已形成合法模型选择请求；
- 所有实际执行的确定性脚本退出状态与输出 schema 一致；
- 输入结构在执行前后 SHA-256 不变；
- 共价和配位结果独立记录；
- 关系导致的 topology promotion 只在确认后应用；
- 所有待确认问题已完整汇总；
- `classification_result.yaml`、报告与 confirmation count 一致；
- 共享 `subagent_result v2` 校验通过；
- 没有创建 STRUCTURE artifact candidate；
- 没有写入 Manager 专属目录。

---
name: component_and_residue_classification_validator
description: 读取结构准备阶段的 PDB、mmCIF 或 AlphaFold 3 CIF，识别模型、链、组分、残基类别、显式共价连接、几何共价候选和金属配位候选，生成结构化分类报告及必要的用户决策请求。该 Validator 不修改结构，不执行链选择，也不把配位关系误判为共价连接。
---

# 目标

为 `structure_preparation_workflow` 的 1.2 子步骤生成可供链与组分选择使用的分类证据：

- 识别模型、实体、链和连续聚合物片段；
- 区分标准残基、相连非标准残基、独立非标准组分、水、离子和未知对象；
- 单独记录显式共价连接、几何共价候选和金属配位候选；
- 标记会影响后续选择或拓扑路线的歧义；
- 写入详细分类报告和机器可读结果数据；
- 按 `subagent_result.schema.yaml` 返回精简 Validator result。

# 职责边界

负责：

- 读取 task 授权的一个 STRUCTURE artifact candidate；
- 解析 PDB、PDBx/mmCIF 或 AF3 CIF 的结构层级和连接记录；
- 按 `references/classification_rules.md` 分类链、组分和残基；
- 按 registries 识别标准别名、共价上下文和配位候选；
- 区分 Validator 执行状态与分类 outcome；
- 对阻断歧义返回 `confirmation_items`；
- 在授权业务目录写分类报告、结果数据和必要日志。

不负责：

- 修改、重排、删除或补全结构；
- 选择保留哪些链、配体、水或离子；
- 处理 altLoc/occupancy；
- 判断缺失残基或重原子完整性；
- 分配质子化状态；
- 生成拓扑或判断具体力场一定支持某残基；
- 把距离接近直接升级为确定共价键；
- 把金属配位关系归入共价相连非标准残基；
- 修改 `00_project_state/**` 或 `00_project_records/**`；
- 直接向用户提问或创建其他 Agent。

# 输入

必须接收符合：

```text
03_contracts/subagent_task.schema.yaml
```

的 `VALIDATOR` task unit。

任务至少应提供：

- `task_id`、`workstream_id`、`workflow_name`；
- `task_unit.mode: VALIDATOR`；
- validator Skill ref 指向本 Skill；
- 项目根和工作目录；
- 一个当前有效 STRUCTURE 文件记录；
- 上游 `source_recognition` 摘要及报告路径；
- allowed read/write paths；
- forbidden paths，包含项目状态和记录目录；
- 分类报告和结果数据输出路径；
- 已解决的模型、链或特殊组分解释决定，如有。

没有唯一可定位的输入结构时返回 `BLOCKED`，不得无界扫描项目寻找结构。

# 输出文件

默认写入：

```text
01_structure_preparation/02_component_and_residue_classification/
├── component_and_residue_classification_report.yaml
├── classification_result.yaml
└── classification.log              # 可选
```

- report：面向审查的详细分类证据；
- result data：符合本 Skill 本地 schema 的机器可读分类数据；
- log：仅记录解析器、警告和技术诊断，不复制完整结构。

本 Validator 不创建新的 STRUCTURE artifact candidate，也不改变输入 STRUCTURE 的 validation status。

# Preflight

执行前确认：

- task schema version 和 mode 正确；
- task/workstream/workflow 标识存在；
- 当前 Workflow 为 `structure_preparation_workflow`；
- 输入结构是已登记的当前有效文件；
- 输入为普通可读文件，不是 symlink、目录或空文件；
- 格式属于 PDB、mmCIF 或 AF3 CIF；
- 输出目录位于 allowed write paths；
- `00_project_state/**` 和 `00_project_records/**` 位于 forbidden paths；
- 适用 registries 和本地输出 schema 可读取；
- `scripts/classify_structure.py` 及 `scripts/requirements.txt` 可用；
- 不存在要求本 Validator 修改结构的 task 指令。

Preflight 不通过时不写部分分类结果。

# 确定性解析器

实际结构解析、分类、候选连接检测和本地 schema 校验必须调用：

```text
scripts/classify_structure.py
```

不得由 LLM 在主上下文或子 Agent 中逐原子模拟解析器。

基本调用：

```bash
python scripts/classify_structure.py \
  --structure <input.pdb-or-cif> \
  --task-id <task_id> \
  --workstream-id <workstream_id> \
  --report <component_and_residue_classification_report.yaml> \
  --result-data <classification_result.yaml>
```

AF3 CIF 增加：

```text
--source-label AF3_CIF
```

已有 resolved model decision 时增加：

```text
--model-id <model_id>
```

解析器完成：

- PDB/mmCIF/AF3 CIF 读取；
- entity、polymer、chain、residue 和 atom 枚举；
- PDB `LINK/SSBOND/CONECT` 与 mmCIF connection 读取；
- registry 应用；
- 几何共价候选和金属配位候选生成；
- 输入 SHA-256 前后核验；
- `classification_outputs.schema.yaml` 校验；
- report/result data 原子写入和跨 task 覆盖保护。

解析器只返回本地分类数据，不生成共享 `subagent_result`。Validator 必须读取其结构化输出，将 ambiguities 转换为 `confirmation_items`，再包装共享 result v2。

# 分类层级

## 模型

记录：

- model ID；
- 每个模型的链、残基和原子计数；
- 模型间组分集合是否一致；
- 是否存在会影响分类的模型差异。

多个模型本身不是执行失败。若 task 未指定模型且模型间分类结果不同，返回 blocking decision request；若分类完全一致，可报告为非阻断 warning。

## 链与实体

优先使用 mmCIF entity/polymer metadata；PDB 中结合 SEQRES、ATOM/HETATM、TER 和连接记录重建链与组分。

每个链或独立实体至少记录：

- chain/entity ID；
- component class；
- polymer class；
- residue 范围和计数；
- 标准与非标准残基计数；
- 显式连接和候选连接；
- 分类置信度与证据来源。

## 残基

每个残基输出两个正交字段：

```text
polymer_class
topology_class
```

允许值由本地输出 schema 管理。

核心 `topology_class`：

- `STANDARD_RESIDUE`：规范残基或 registry 明确认可的标准别名；
- `COVALENTLY_LINKED_NONSTANDARD`：非标准残基/组分有显式共价连接，或聚合物连续性证据充分；
- `INDEPENDENT_NONSTANDARD`：未与聚合物形成确定共价连接的非标准组分；
- `SOLVENT`；
- `ION`；
- `UNKNOWN`。

金属配位不改变上述共价拓扑分类。

# 连接证据优先级

从高到低：

1. mmCIF `struct_conn`、entity/polymer linkage 等显式记录；
2. PDB `LINK`、`SSBOND`、必要的 `CONECT`；
3. 聚合物序列与主链连续性证据；
4. 原子距离形成的几何共价候选；
5. 仅名称或文件位置推测。

只有 1–3 级证据可以直接支持确定共价分类。第 4 级只能产生 `COVALENT_BOND_CANDIDATE`；若它会改变“相连/独立”分类，必须返回 decision request 或保持 `UNKNOWN`。

# 配位候选

按照 `references/coordination_detection_registry.yaml` 检查金属—供体原子距离。

结果分为：

- `EXPLICIT_COORDINATION`：源文件有明确 coordination/metal connection 记录；
- `GEOMETRIC_COORDINATION_CANDIDATE`：仅满足距离与元素规则；
- `AMBIGUOUS_CLOSE_CONTACT`：接近阈值或受 altLoc/occupancy 影响。

配位候选单独输出：金属原子、供体原子、距离、来源、阈值和置信度。不得据此自动建立共价连接。

# 决策请求

以下情况通常为 blocking：

- 多模型产生不同链/组分分类且未指定模型；
- 非标准组分是否与聚合物共价相连只能由几何候选支持；
- 同一 residue name 在当前上下文可能是标准别名，也可能是独立配体；
- polymer/entity metadata 与 residue chemistry、backbone 或连接证据冲突；
- 未知残基的分类会改变下一步链或组分选择；
- 输入文件的链或 residue 标识不足以唯一引用对象。

以下通常为 non-blocking warning：

- 仅存在不影响分类的多模型重复；
- 配位候选未影响共价 topology class；
- 少量无法归属但后续可整体选择的独立溶剂/离子样对象。

Validator 完成所有可执行检查后返回统一 `confirmation_items`，不直接提问。

# 执行流程

1. 解析 task、权限和上游摘要；
2. 完成 preflight 并定位确定性 parser；
3. 调用 parser 读取结构、应用 registries 并生成 report/result data；
4. 核验 parser exit code、输入 SHA-256 和本地 schema 结果；
5. 汇总模型、链、组分、残基、显式连接、候选连接和 warning；
6. 将 blocking/non-blocking ambiguities 转换为共享 `confirmation_items`；
7. 返回符合共享 contract 的 Validator result。

# Outcome codes

- `CLASSIFIED_CLEAR`：分类完成，无 blocking 歧义；
- `CLASSIFIED_WITH_WARNINGS`：分类完成，仅有非阻断 warning；
- `CLASSIFICATION_DECISION_REQUIRED`：Validator 成功执行，但存在 blocking 分类决定；
- `INPUT_SCOPE_INVALID`：输入结构不唯一、未授权或 task 不完整；
- `UNSUPPORTED_OR_UNPARSEABLE_STRUCTURE`：格式不受支持或无法可靠解析；
- `VALIDATOR_INTERNAL_FAILURE`：解析器或写报告发生内部错误。

`CLASSIFICATION_DECISION_REQUIRED` 的 execution status 可以是 `DONE`，因为检查已经完成；Manager 根据 confirmation items 将 Workstream 暂停。不得把科学歧义伪装成 Validator 执行失败。

# Gate 建议

- `CLASSIFIED_CLEAR | CLASSIFIED_WITH_WARNINGS`：建议进入 1.3 `chain_and_component_selection`；
- `CLASSIFICATION_DECISION_REQUIRED`：建议暂停并解析 blocking decisions；
- 输入或执行失败：不允许进入 1.3。

本 Validator 不自行选择下一 task，也不修改 route。

# 返回

返回必须符合：

```text
03_contracts/subagent_result.schema.yaml
```

要求：

- `task_unit_mode: VALIDATOR`；
- `operation_result: null`；
- `validation_result.skill_name` 为本 Skill；
- `validation_result.status` 与执行事实一致；
- `outcome_code` 使用本 Skill 定义值；
- `key_findings` 只给精简摘要；
- `validated_files` 包含实际读取并完成分类检查的输入结构；
- `created_files` 包含 report/result data；
- `artifact_candidates: []`；
- `confirmation_items` 保存 blocking/non-blocking 决策请求；
- `detail_files` 指向实际输出；
- 不把输入 STRUCTURE 标记为 `VALIDATED`。

# 失败与清理

- 输入不唯一或越权：返回 `BLOCKED`，不创建部分报告；
- parser 返回确定性输入/registry/schema 错误：返回 `FAILED`，保留最小技术诊断；
- 报告写入中断：删除本次不完整临时文件后返回 `FAILED`；
- 局部残基未知：只要整体解析可靠，返回 DONE + warning/decision，不得整项失败；
- 不覆盖已有不同 task ID 的报告；同一 task 重试使用新 task ID 或明确的幂等复用规则。

# 自检

- [ ] 只读取唯一授权结构；
- [ ] 实际调用了 `scripts/classify_structure.py`；
- [ ] 未修改输入结构；
- [ ] 显式共价、几何共价候选和配位候选已分离；
- [ ] 配位未被归入共价相连非标准残基；
- [ ] 标准别名有 registry 证据；
- [ ] 未用距离 alone 宣告共价键；
- [ ] blocking 歧义已生成 confirmation items；
- [ ] Validator 执行状态与分类 outcome 已区分；
- [ ] 报告与结果数据通过本地 schema；
- [ ] 未写管理目录；
- [ ] 返回符合共享 subagent result v2；
- [ ] 未创建或验证新的 STRUCTURE artifact。

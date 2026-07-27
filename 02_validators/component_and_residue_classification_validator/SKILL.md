---
name: component_and_residue_classification_validator
description: 对 structure_preparation_workflow 的已识别 PDB、mmCIF 或 AF3 CIF 执行模型范围解析、组分与残基分类、缺失残基和重原子事实检查、项目定义的可能共价连接及金属配位检查，并生成统一分类结果和用户确认请求。只读结构，不进行链选择、altLoc 处理、结构补全或拓扑生成。
---

# 目标

为 `structure_preparation_workflow` 的 1.2 子步骤生成确定、可审计、可供下一步读取的分类结果：

- 先解析 model 范围；
- 对一个已选定 model 完整解析 entity、源 chain、residue、atom 和 altLoc；
- 输出 `polymer_class` 与 `topology_class`；
- 记录 PDB/mmCIF 的缺失残基事实；AF3 仅在提供输入序列依据时检查；
- 按 CCD 或 GROMACS RTP 模板记录重原子缺失、多出或命名映射问题；
- 按项目提供的已知原子对检查可能共价连接和金属配位；
- 完成全部可执行检查后统一返回人工确认项；
- 不修改结构，不生成新的 STRUCTURE artifact candidate。

# 职责边界

负责：

- 读取一个由 `source_recognition` 授权的结构文件；
- 验证结构 SHA-256；
- 单 model 自动选择，多 model 返回选择请求；
- 严格、区分大小写地匹配残基名和原子名；
- 读取项目残基定义、Skill registry、指定力场 RTP、CCD、序列参考和关系定义；
- 生成本 Skill 的机器可读结果、可读报告和日志；
- 将科学歧义转换为 `confirmation_items` 候选，由 Manager 统一交互和持久化。

不负责：

- 修改、重排、删除、补全或另存结构；
- 选择保留的链、配体、水或离子；
- 选择 altLoc 或 occupancy；
- 指定质子化状态；
- 建立实际拓扑、参数或键项；
- 读取 `specbond.dat` 判断当前结构存在连接；
- 判断后续完整性 gate 或结构补全路线；
- 修改 `00_project_state/**` 或 `00_project_records/**`；
- 直接向用户提问或创建其他 Agent。

# 输入

必须接收符合以下共享 contract 的 `VALIDATOR` task unit：

```text
03_contracts/subagent_task.schema.yaml
```

任务至少提供：

- `task_id`、`workstream_id`、`workflow_name`；
- `task_unit.mode: VALIDATOR`；
- 一个唯一、当前有效且可读取的 STRUCTURE 文件；
- `source_recognition` 的格式结论；
- 项目根、业务输出目录和 allowed read/write paths；
- forbidden paths，包含项目状态与记录目录；
- classification mode：`REGISTRY | FORCE_FIELD_ANALYSIS`；
- 可选项目输入文件与路径；
- 已解决的 model 或确认决定，如有。

条件输入：

```text
project_residue_definitions.yaml
possible_connections.yaml
possible_coordination.yaml
AF3 input JSON / FASTA / sequence file
GROMACS force-field root and terminal RTP mappings
CCD local directories / shared cache / retrieval policy
```

没有唯一输入结构、输入未授权或 selected model 无法定位时返回 `BLOCKED` 或技术失败，不扫描项目猜测输入。

# 输出目录

默认写入：

```text
01_structure_preparation/02_component_and_residue_classification/
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

不增加固定 `runs/` 层。任务历史、哈希、版本和结果闭环由 Manager 的项目记录维护。

# 分类枚举

`polymer_class`：

```text
POLYMER
BRANCHED
NONPOLYMER
WATER
```

`topology_class`：

```text
STANDARD_RESIDUE
COVALENTLY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

未解决和冲突由 `resolution_status` 表达，不作为分类枚举值。

# 严格名称规则

- 结构残基名和原子名原样保留；
- `HEM`、`Hem`、`hem` 是不同名称；
- 不执行 `.upper()`、大小写折叠、alias、正则或相似字符串匹配；
- `ccd_id` 只来自项目显式映射或精确 `residue_name`；
- terminal RTP 映射必须显式提供，不通过添加或删除 `N/C/5/3` 猜测。

# 执行流程

## 1. Model scope

调用：

```text
scripts/inspect_model_scope.py
```

- 单 model：自动选择；
- 多 model：只输出 model ID 和 chain/residue/atom 最小统计，停止正式分类并返回 model 选择请求；
- model 未确定前不得运行完整解析。

## 2. 完整分类观察

调用：

```text
scripts/classify_structure.py
```

固定顺序：

```text
验证输入
→ 解析 selected model
→ 枚举 entity/source chain/residue/atom/altLoc
→ 应用分类来源
→ 分配 baseline chain_index
→ 检查缺失残基
→ 检查重原子
→ 获取并固化参考数据
→ 汇总全部未解决观察
```

科学歧义不在第一次出现时中止。只有文件不可解析、哈希不一致、selected model 不存在、配置/schema 无效、必要机制整体不可用等技术错误立即失败。

## 3. 可能共价连接

存在 `possible_connections.yaml` 时调用：

```text
scripts/check_possible_connections.py
```

- 仅检查定义中的精确 residue/atom pair；
- 枚举所有有效实例组合；
- 显式结构连接和几何距离分别记录；
- 距离支持但无显式连接只生成候选；
- 不创建连接、不修改分类文件；
- 多构象且显式记录不能定位构象时不评估几何。

## 4. 金属配位

存在 `possible_coordination.yaml` 时调用：

```text
scripts/check_possible_coordination.py
```

- metal 与 donor 有方向；
- 名称和元素必须严格匹配；
- 多个 donor 可同时配位同一 metal，不自动视为冲突；
- 关系始终记录为 `METAL_COORDINATION`；
- 仅当定义的 `promote_nonstandard_to_linked: true` 且关系已确认时，整合阶段才可提升非标准组分。

## 5. 结果整合

调用：

```text
scripts/build_classification_result.py
```

读取 model scope、classification observations、reference manifest、两个关系结果和已有 Manager decisions，生成：

- `confirmation_requests.yaml`；
- `classification_result.yaml`；
- `classification_report.md`。

存在待确认项时仍生成：

```text
result_status: PENDING_USER_CONFIRMATION
```

待确认关系不产生 topology effect。技术失败时不得生成貌似有效的正式结果。

# 分类来源顺序

## REGISTRY

```text
项目精确定义
→ Skill 精确 registry
→ entity/polymer context
```

项目与 Skill 对同一精确名称均有定义时比较两个分类标签：一致则接受；任一标签冲突则累计确认项，不设置自动优先级。

## FORCE_FIELD_ANALYSIS

```text
项目精确定义
→ 所选力场全部 *.rtp 的精确 residue block
→ 仍未解决对象使用 Skill registry
→ entity/polymer context
```

- 力场是否识别残基只看 RTP block 名称；
- 不使用 RTP 文件名的描述；
- 不使用 `residuetypes.dat`；
- 非水 residue block 重复定义时累计确认；
- 水可在一个力场中存在多套模板，1.2 不选择水模型；
- `specbond.dat` 不参与 1.2。

# 重原子检查

参考矩阵：

| mode | STANDARD_RESIDUE | 非标准残基 | 水/普通离子 |
|---|---|---|---|
| `REGISTRY` | CCD | CCD | 默认不检查 |
| `FORCE_FIELD_ANALYSIS` | 指定 RTP block | CCD | 默认不检查 |

结果仅记录原子名集合：

```text
HEAVY_ATOMS_COMPLETE
MISSING_EXPECTED_HEAVY_ATOMS
UNEXPECTED_HEAVY_ATOMS
MISSING_AND_UNEXPECTED_HEAVY_ATOMS
ATOM_NAME_MAPPING_REQUIRED
REFERENCE_TEMPLATE_UNAVAILABLE
NOT_PERFORMED
NOT_APPLICABLE
```

不区分主链、侧链或其他位置类别。

端基标准残基：

- 根据结构链端角色和显式 terminal mapping 选择对应 RTP residue block；
- 在指定 RTP 文件中核验端基模板；
- RTP 中没有可用端基 block 时记录模板不可用；
- v1 不合成 `.n.tdb/.c.tdb` patch。

多构象残基：

```text
conformation: MULTIPLE_CONFORMATIONS
heavy_atom_check: NOT_PERFORMED
reason: MULTIPLE_CONFORMATIONS_PRESENT
```

# 缺失残基

- PDB：使用 `SEQRES`、`REMARK 465` 和坐标残基；
- mmCIF：使用 entity/polymer sequence、scheme、unobserved residue 和 atom_site；
- 不凭 residue numbering gap 单独认定缺失；
- AF3 CIF 默认不执行；提供 AF3 input/FASTA 等序列依据后才执行；
- 只记录缺失哪些残基，不判断内部、N 端或 C 端区域；
- 正式缺失残基记录必须有作者 `source_resid.number`；插入码按源记录保留；
- 作者编号或 chain 归属无法确定时继续扫描，最后统一返回确认项，不虚构编号。

# Chain groups

- `chain_index` 是 selected model 内部组分归属编号，不等于源 chain ID；
- polymer/branched chain 各分配一个 baseline index；
- 每种精确名称的普通水、离子形成汇总 group；
- 条件一致的重复独立小分子可汇总；
- 汇总对象不逐实例写入主 `residue_records`；异常或参与关系的实例从汇总中提出；
- 与一条 polymer chain 形成已确认 topology-forming relation 的非标准残基，最终使用该 polymer 的 index；
- 与多条 polymer chain 相连时建立独立 group 并记录所有 linked chain indices；
- observations 的 baseline index 可与 final result 不同，polymer/branched index 保持稳定。

# CCD

获取顺序：

```text
项目已有 snapshot
→ 用户指定本地目录
→ 共享 cache
→ 按 retrieval_policy 下载
```

- 本地目录在联网前一次性检索；默认不递归；
- 文件名和内部 component ID 均精确校验；
- 验证 atom table、元素和 SHA-256；
- 实际使用文件复制到 `reference_data/ccd/`；
- 单 component 失败累计并继续；系统性 CCD 机制失败才技术中止；
- 备用原子名只产生 `ATOM_NAME_MAPPING_REQUIRED`，不静默改名。

# 确认项

完成全部可执行检查后统一汇总，典型包括：

- 项目定义与 Skill/力场分类冲突；
- 非水 RTP 模板重复；
- 缺失残基作者编号或 chain 归属无法确定；
- 序列映射冲突；
- geometry-supported covalent candidate；
- connection definition conflict；
- geometry-supported coordination candidate；
- coordination definition conflict；
- 多个内容不同的本地 CCD 候选。

明确缺失重原子、模板不可用、单 CCD 下载失败、partner/atom 未找到、无显式关系的元素问题、几何不支持、多构象提示只记录，不自动进入确认列表。

# Outcome

建议 outcome：

```text
CLASSIFIED_CLEAR
CLASSIFICATION_DECISION_REQUIRED
MODEL_SELECTION_REQUIRED
INPUT_SCOPE_INVALID
UNSUPPORTED_OR_UNPARSEABLE_STRUCTURE
VALIDATOR_INTERNAL_FAILURE
```

`CLASSIFICATION_DECISION_REQUIRED` 可对应 Validator execution `DONE`：完整扫描已完成，但 Manager 必须暂停并处理确认项。

# 返回

返回必须符合：

```text
03_contracts/subagent_result.schema.yaml
```

- `task_unit_mode: VALIDATOR`；
- `operation_result: null`；
- 输入 STRUCTURE 保持原 validation status；
- 分类 YAML/Markdown 可作为 validated business records；
- 不把分类报告声明为 STRUCTURE artifact；
- confirmation items 由 Manager 持久化。

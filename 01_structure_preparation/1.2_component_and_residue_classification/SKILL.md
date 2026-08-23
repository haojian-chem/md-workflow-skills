---
name: component_and_residue_classification
description: 结构准备 1.2。对 1.1 已确定结构来源中的当前 structure model 完成组分与残基分类、缺失残基、多构象、重原子组成与命名、共价连接和金属配位检查，建立稳定身份与可追溯正式结果，供后续结构准备、拓扑准备及项目映射继续使用。
---

# 1.2 Component and residue classification

跨 Stage 的通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 只定义 1.2 自身的科学检查、结果接口、reuse、validation 与正式结果规则。

## 目标

对 1.1 已确定的正式结构来源，在当前选定 structure model 上建立一份稳定、可追溯、可供后续处理持续引用的结构分类与检查基准。

1.2 负责形成：

- 当前结构中全部组分与残基实例的分类和正式顺序；
- 已确认缺失残基；
- 多构象信息；
- 已存在残基的重原子组成与命名检查结果；
- 需要记录的共价连接与金属配位关系；
- `residue_id`、`component_id` 及关系端点身份；
- 实际使用参考文件的可追溯记录；
- 供后续 Stage / Step 使用的正式 `classification_result.yaml`。

1.2 不修改结构，也不决定 1.3 保留哪些研究对象。

详细科学判据由：

`references/classification_rules.md`

拥有。正式结果组织、字段语义和报告格式按：

`references/result_recording_rules.md`

执行。机器字段约束位于 `schemas/`。

1.2 的科学检查由 Task Execution Agent 依据当前结构、参考文件和上述规则直接完成，不要求通过固定 Python pipeline。`scripts/selection_identity.py` 仅作为稳定身份物化的可选确定性辅助工具，不参与科学判断；辅助工具不可用本身不构成 1.2 科学检查失败。

## 输入与依据

开始新的 1.2 时至少需要：

- 1.1 已确定的正式结构文件及其 SHA-256；
- 1.1 已确定的结构格式信息；
- 当前实际检查的 structure model；
- 当前分类模式：`REGISTRY` 或 `FORCE_FIELD_ANALYSIS`。

如果源结构只有一个 model，直接使用该 model。存在多个 model 且当前任务尚未确定使用哪一个时，向用户确认；在 model 未唯一确定前不形成完整 1.2 正式结果。

其余依据按实际检查需要读取，不要求无条件全部提供：

- 项目残基定义；
- Skill 内置 residue registries；
- 当前已指定目标力场中的残基定义；
- 实际 CCD component definition 文件；
- 序列或结构 annotation；
- 项目提供的共价连接或金属配位定义；
- 结构文件中的显式连接信息；
- 用户已确认的关系或命名对应。

`reference_manifest.yaml` 只记录本次实际用于形成判断的参考文件；没有实际使用的候选文件不得写入 manifest。

## Reuse

开始 1.2 时，在项目结果索引中检索已有正式 `classification_result.yaml` 与对应 `reference_manifest.yaml`。

只有以下信息均可确认等价，并且旧结果满足当前 1.2 正式结果契约时才自动复用：

- 源结构 SHA-256；
- `selected_model_id`；
- `classification_mode`；
- 实际影响分类、缺失残基、重原子检查和关系判断的参考文件及其 SHA-256；
- 项目残基定义；
- 已应用的用户确认事项；
- 当前用户没有要求重新检查、改变参考依据或生成对照结果。

旧结果不满足当前 schema、缺少足以核对参考依据的信息，或正式结果与当前任务无法确认等价时，不自动复用。明确不等价则正常执行；只是缺少等价性判断信息时按通用 Task Execution 规则向用户确认。

确认复用时直接引用原正式结果，不复制副本，也不创建当前任务空目录。

## 工作目录

需要实际执行新的 1.2 时使用：

```text
<project_root>/01_structure_preparation/02_component_and_residue_classification/<task_id>/
```

当前任务的正式结果和人工确认记录只写入该任务目录，不覆盖其它任务已有结果。

## 执行主线

### 1. 确定当前 structure model

确认本次全部检查只针对同一个已选定 model。后续 residue identity、缺失残基、关系端点和结果记录均绑定该 `selected_model_id`。

1.2 不重新执行 1.1 已完成的结构来源识别或基础格式确认。

### 2. 建立已观察组分与残基记录并完成初始分类

完整遍历当前 model 中实际存在的 residue instances，建立后续检查使用的已观察残基记录和稳定源身份。

分类时读取 `references/classification_rules.md` 的“分类与参考依据”部分，分别确定：

```text
polymer_class

topology_class:
STANDARD_RESIDUE
TOPOLOGY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

分类依据必须能够追溯到实际项目定义、目标力场残基定义、Skill registry 或结构实体语义；不能仅依据 `ATOM / HETATM`、残基名外观或空间位置猜测分类。

### 3. 检查缺失残基

在重原子检查之前完成缺失残基检查。

只根据能够追溯的序列或结构 annotation 判断预期存在但当前没有坐标的 residue；不得仅根据 residue number gap、chain break 或视觉上的坐标缺口推断缺失残基。

已确认缺失残基作为 `MISSING_EXPECTED` residue record 写入正式 `residue_records[]`，并放在其正式 residue order 对应位置。整个缺失的 residue 不再作为“缺失全部重原子”的 observed-residue 问题重复记录。

### 4. 检查多构象

对当前 model 中全部已观察残基独立检查 alternate conformation / `altLoc`。

记录存在多构象的 residue、实际 `altLoc` ID、受影响 atom name 及可读取的 occupancy 信息。多构象检查是独立检查项目，不属于重原子检查的子项。

若多构象能够可靠拆分为 shared atoms 与各候选构象，后续重原子检查按候选构象分别比较；不得把互斥构象的原子合并为一个虚构 atom set。无法可靠拆分时，重原子检查明确记录未完成及原因。

### 5. 检查重原子组成与命名

对每个适用的已观察 residue，先确定本次实际使用的残基定义，再比较当前 residue 与该定义的重原子组成和命名。

检查至少覆盖：

- 同一实际比较 atom set 内的重复 atom name；
- 参考定义中存在、当前 residue 缺失的重原子；
- 当前 residue 存在、参考定义中没有的额外重原子；
- atom name 差异以及可证实的 alternate-name mapping candidate；
- 能够从当前结构与参考定义可靠判断时的元素不一致。

命名对应只能在保留原始精确比较结果的基础上单独记录；不得通过自动改名消除原始差异。

标准残基需要基于目标力场检查时，使用当前已指定目标力场中的实际残基定义。非标准残基需要 CCD 检查时，直接使用本次实际选定的 CCD component definition 文件。项目或用户提供的 CCD 文件不要求转换为 Skill 自定义库格式后才能使用。

详细规则见 `references/classification_rules.md`。

### 6. 检查共价连接

结合当前结构中的显式连接信息、项目关系定义和实际局部几何，检查需要关注的共价连接。

显式结构证据与化学身份、端点原子和几何关系一致时可以形成已确认关系；只有几何接近时只作为候选证据，不能自动等同于已建立共价键。

存在多个合理解释且不同解释会改变正式关系或后续拓扑归属时，向用户确认。

### 7. 检查金属配位

独立检查需要关注的金属—配位原子关系，记录实际金属端点、配位原子端点及证据。

金属配位的存在与“该关系是否形成后续拓扑连接”是两个不同判断。只有当前项目定义或用户确认明确要求该配位产生 topology effect 时，才据此改变非标准组分的拓扑归属。

### 8. 形成最终分类、分组与稳定身份

应用全部已经确认且应产生 topology effect 的关系后，形成最终 `topology_class`、`chain_groups` 与 `component_id`。

`residue_id` 和 `component_id` 的正式语义以仓库级 `canonical_terminology.md` 为准；下游只消费已经物化的值，不根据残基编号、残基名、chain 或空间关系重新构造。

`residue_records[]` 的数组顺序是 1.2 正式 residue order。后续需要保持 residue ordering 时使用该顺序，不按 `residue_id`、`component_id` 或源残基编号重新排序。

### 9. 写正式结果

按 `references/result_recording_rules.md` 生成：

```text
classification_result.yaml
reference_manifest.yaml
classification_report.md
```

如果本次实际发生用户关系确认，再生成：

```text
relation_decisions.yaml
```

正式 YAML 按对应 schema 校验。schema 校验只确认结果结构和字段约束，不能替代本 Skill 的科学 validation。

## Validation

1.2 标记为 `已完成` 前确认：

- `selected_model_id` 已唯一确定，全部检查均针对该 model；
- 输入结构 SHA-256 与开始检查时一致，1.2 没有修改源结构；
- 当前 model 中每个已观察 residue 都在 `residue_records[]` 中恰有一个正式记录；
- 已确认缺失残基已经在正式 residue order 中物化，没有被重复记录成“缺失全部重原子”；
- 每个已观察 residue 都有明确的多构象检查结果；
- 每个适用的已观察 residue 都有重原子组成与命名检查结果，或明确记录无法完成该比较的实际原因；
- 重原子检查没有把互斥 altLoc 原子合并成同一比较 atom set；
- 缺失、额外、重复、命名对应和元素不一致等发现按正式问题类型记录，没有用模糊的“兼容 / 不兼容”替代实际比较关系；
- 所有影响最终分类的共价连接与金属配位关系均有可定位端点、证据和明确状态；
- 已确认 topology effect 已反映到最终 `topology_class`、`chain_groups` 与 `component_id`；
- `residue_id`、`component_id` 及 relation identity 在当前正式结果中唯一且引用一致；
- `reference_manifest.yaml` 只包含实际使用的参考文件，路径和 SHA-256 与当前文件一致；
- `classification_result.yaml` 中引用的 reference 均能在 `reference_manifest.yaml` 中定位；
- 没有尚未解决、会改变正式分类、稳定身份或 topology effect 的用户确认事项；
- `classification_result.yaml`、`reference_manifest.yaml` 和实际存在的 `relation_decisions.yaml` 均通过当前 schema；
- `classification_report.md` 与正式 YAML 中的分类、问题和关系一致。

发现结构问题本身不表示 1.2 未完成；只要规定检查已经可靠执行并如实记录，1.2 可以完成。无法形成可靠判断且该判断会改变正式分类、身份或关系时，当前 1.2 保持 `未完成`，不得生成可误认为完成结果的 `result_status: COMPLETE`。

## 正式结果与登记

新的 1.2 实际执行后，正式结果为：

```text
classification_result.yaml
reference_manifest.yaml
classification_report.md
relation_decisions.yaml   # 仅实际发生用户关系确认时存在
```

项目结果索引只登记：

```text
classification_result.yaml
reference_manifest.yaml
```

登记完整绝对路径和简明说明。`classification_report.md` 与实际存在的 `relation_decisions.yaml` 保留为当前任务正式结果，但不单独建立 project-level result entry。

1.2 不要求生成 `model_scope.yaml`、`classification_observations.yaml`、独立 relation-check result、`confirmation_requests.yaml` 或其它固定中间状态文件；Agent 因当前任务需要产生的临时笔记、命令输出或 scratch 文件不属于正式结果。

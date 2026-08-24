---
name: component_and_residue_classification
description: 结构准备 1.2。对 1.1 已确定结构来源中的实际 model 完成组分与残基分类、残基缺失、多构象、重原子组成与命名、共价连接和金属配位检查，并形成供后续结构准备与拓扑准备持续引用的正式结果。
---

# 1.2 Component and residue classification

跨 Stage 的通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 只定义 1.2 自身的科学检查、reuse、validation 与正式结果接口。

## 目标

对 1.1 已确定的结构来源，按实际需要处理的 model 分别建立结构分类与检查基准。

1.2 负责形成：

- 当前 model 中的 component / residue 层级及稳定 `component_id`、`residue_id`；
- component 一级的 `chain_index`；
- 每个 residue 的 `polymer_class` 与 `topology_class`；
- 残基缺失检查结果；
- 多构象问题检查结果；
- 重原子组成与命名检查结果；
- 需要记录的共价连接与金属配位关系；
- 本次检查实际使用的 RTP / CCD reference 变量；
- `classification_result.yaml` 与人工审阅报告。

1.2 不修改结构，也不决定 1.3 保留哪些研究对象。

详细科学判据由：

`references/classification_rules.md`

拥有。正式结果的数据结构、字段语义和报告格式由：

`references/result_recording_rules.md`

拥有。机器字段约束位于 `schemas/`。

1.2 的科学检查由 Task Execution Agent 依据当前结构、实际 reference 和上述规则直接完成；当前 active 1.2 不要求 Python 科学流水线或身份生成脚本。

## 输入与依据

开始新的 1.2 时至少需要：

- 1.1 已确定的正式结构文件；
- 1.1 已确定的结构格式信息；
- 本次实际需要处理的 model；
- 当前分类模式：`REGISTRY` 或 `FORCE_FIELD_ANALYSIS`。

一个源结构含多个 model 时，每个实际执行 1.2 的 model 独立处理并写入独立 model 目录；一份 `classification_result.yaml` 只描述一个 model，model 信息只在文件级记录一次，不复制到每个 component / residue。

其余依据按当前判断需要读取：

- 项目残基定义；
- Skill 内置残基登记表；
- 当前目标力场中的实际 `*.rtp`；
- 实际 CCD 组分定义文件；
- 序列或结构注释；
- 项目提供的共价连接或金属配位定义；
- 结构文件中的显式连接信息；
- 用户已经确认的判断。

## Reuse

开始当前 model 的 1.2 时，在项目结果索引中检索已有正式 `classification_result.yaml`。

只有以下内容均可确认等价，并且旧结果满足当前 1.2 正式结果契约时才自动复用：

- 1.1 所确定的源结构相同；
- model 相同；
- `classification_mode` 相同；
- 本次实际采用的 RTP / CCD reference 选择相同；
- 会影响分类、残基缺失、重原子检查或关系判断的项目定义和用户决定相同；
- 当前用户没有要求重新检查或生成对照结果。

明确不等价则正常执行；信息不足时按仓库级 Task Execution 规则向用户确认。复用已有正式结果时直接引用原结果，不复制副本。

## 工作目录

需要实际执行新的 1.2 时使用：

```text
<project_root>/01_structure_preparation/02_component_and_residue_classification/<task_id>/
└── <model_directory>/
    ├── classification_result.yaml
    ├── classification_report.md
    └── relation_decisions.yaml   # 仅实际发生关系人工决策时存在
```

不同 model 必须使用不同子目录。目录名只负责文件组织；实际 model 身份以该目录内 `classification_result.yaml` 文件级 `model.model_id` 为准。

## 执行主线

### 1. 建立当前 model 的 residue 基线与初始分类

完整读取当前 model 的实际结构与可追溯序列 / 注释信息，建立当前 model 需要记录的 residue 顺序和 provisional component membership。

对每个 residue 确定：

```text
polymer_class

topology_class:
STANDARD_RESIDUE
TOPOLOGY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

分类不能仅依据 `ATOM / HETATM`、名称外观或空间位置猜测。具体依据见 `references/classification_rules.md`。

### 2. 残基缺失检查

对每个预期 residue 首先检查该 residue 在当前 model 中是否存在。

只有存在可追溯的序列或结构注释依据时，才把一个未出现坐标的 residue 记录为缺失；不得仅根据 residue 编号间断、chain break 或空间空缺推断。

若本项发现 residue 缺失：

```text
missing_residue_check = ISSUE
conformation_check = SKIPPED
heavy_atom_check = SKIPPED
```

该 residue 不再继续多构象或重原子检查。

### 3. 多构象检查

仅对残基缺失检查通过的 residue 检查当前 model 是否存在多构象问题。

1.2 只负责发现并记录“是否存在多构象问题”。1.2 不选择构象、不比较候选构象优先级、不整合共享原子与某个 `altLoc`，也不删除任何构象；这些处理属于 1.4。

若发现多构象问题：

```text
conformation_check = ISSUE
heavy_atom_check = SKIPPED
```

### 4. 重原子组成与命名检查

只有前两项均通过时，才执行本项。

对需要检查的 residue，使用当前实际确定的残基定义比较重原子组成与命名，至少检查：

- 缺失的预期重原子；
- 额外重原子；
- 重复原子名称；
- 当前原子名称与参考名称的不一致；
- 当两侧元素信息均可靠时的元素不一致。

具体 reference 规则见 `references/classification_rules.md`。

`classification_result.yaml` 文件级 `references` 只定义本次实际使用的 reference 变量：

```text
RTP_1, RTP_2, ...
CCD_PATH_1, CCD_PATH_2, ...
```

检查项的 `evidence` 直接记录：

```text
RTP_n
{CCD_PATH_n}/XXX.cif
智能体判断
人工决策
```

不再使用 `reference_manifest.yaml`、`ref_001` 或 `reference_entry` 间接定位检查依据。

### 5. 检查共价连接

结合结构中的显式连接、项目关系定义和实际局部化学环境，检查需要关注的共价连接。

仅有几何接近时不能自动等同于已建立共价键。存在多个合理解释且不同解释会改变正式关系、component membership 或 `topology_class` 时，向用户确认。

### 6. 检查金属配位

独立检查需要关注的金属—配位原子关系。

“存在金属配位”与“该关系是否产生后续 topology effect”是两个不同判断。只有项目定义或用户确认明确要求该关系产生 topology effect 时，才据此改变相关非标准 residue 的 `topology_class` 或 component membership。

### 7. 形成最终 component / residue 层级

应用已经确认且 `topology_effect_applied: true` 的关系后，形成最终 component membership，再物化正式 `component_id`、component 一级 `chain_index` 与 component 内的 `residue_id`。

正式层级为：

```text
model
└── component_id + chain_index
    └── residue_id
```

其中：

- `component_id` 在当前 model 的正式结果中唯一，是稳定 component identity；
- `chain_index` 在当前 model 中唯一，是该 component 的逻辑 chain/group 编号，不属于稳定 identity；
- `residue_id` 在所属 `component_id` 内唯一；
- 下游定位 residue 使用 `component_id + residue_id`；
- 下游需要生成或映射 chain 表示时可以直接消费 component 一级 `chain_index`，不得根据 residue 的 `chain_id` 自行重建新的 1.2 `chain_index`。

每个 component 内 `residues` 的数组顺序是该 component 的正式 residue 顺序。

### 8. 写正式结果

按 `references/result_recording_rules.md` 生成：

```text
classification_result.yaml
classification_report.md
```

如果本次实际发生对共价连接或金属配位关系的人工决策，再生成：

```text
relation_decisions.yaml
```

正式 YAML 按对应 schema 校验。schema 校验只确认结果结构和字段约束，不能替代科学检查。

## 验证

当前 model 的 1.2 标记为 `已完成` 前确认：

- 一份 `classification_result.yaml` 只描述一个 model，model 信息未在 residue 内重复；
- component / residue 按 `component_id → residue_id` 层级组织，没有平行的 `chain_groups[] + residue_records[]` 双重成员结构；
- 每个 component 同一级保存一个 `chain_index`；`component_id` 和 `chain_index` 在当前 model 中分别唯一；
- 每个 `residue_id` 在所属 component 内唯一；所有关系端点都能由 `component_id + residue_id` 定位；
- 每个 residue 均保存 `source_chain_id`、`current_chain_id`、`source_resid`、`current_resid`、`source_residue_name`、`current_residue_name`；缺失 residue 没有当前坐标实例时，当前 resid / residue name 按结果规则记录为 `null`；
- 每个 residue 都有 `polymer_class` 与 `topology_class` 及其实际 `evidence`；
- 三项 residue 检查严格按“残基缺失 → 多构象 → 重原子组成与命名”顺序执行；前一项为 `ISSUE` 时，后续项按规则为 `SKIPPED`；
- 1.2 对多构象只记录问题存在与否，没有执行 1.4 的构象选择或整合；
- 重原子检查的 `PASS / ISSUE` 与实际问题明细一致；适用但缺少可靠 reference 时不形成伪 `PASS`；
- `evidence` 为 `RTP_n` 时，该变量在文件级 `references` 中存在；`{CCD_PATH_n}/XXX.cif` 中的 `CCD_PATH_n` 也能在同一文件级 `references` 中解析；
- 没有生成或引用 `reference_manifest.yaml`；
- 所有影响最终分类、component membership 或 `topology_effect_applied` 的事项均已闭合；
- 如果发生关系人工决策，`relation_decisions.yaml` 与正式关系结果一致；
- `classification_result.yaml` 通过 `schemas/classification_result.schema.yaml`；存在 `relation_decisions.yaml` 时通过其 schema；
- 发现结构问题本身不等于 1.2 执行失败，只要规定检查能够可靠完成并正式记录。

## 正式结果与登记

每个实际处理的 model 独立形成：

- `classification_result.yaml`；
- `classification_report.md`；
- `relation_decisions.yaml`（仅实际发生关系人工决策时）。

项目级结果索引只登记每个 model 的正式 `classification_result.yaml` 完整绝对路径及简短说明。`classification_report.md` 与 `relation_decisions.yaml` 由该结果继续定位，不分别登记。

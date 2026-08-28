# Workflow 2 Stage 2.5 current design freeze

Status: CURRENT AUTHORING FREEZE

本文件集中保存本轮重新设计中已经确认的 topology integration and assembly 规则，作为后续正式生成对应 `SKILL.md` 与 local references 的当前 authoring source。

历史 2.5 freeze 仅作为讨论与追溯参考，不自动继承其结论。历史内容只有在本轮重新确认后，才能进入本文件并成为当前生成依据；与本文件冲突时，以本文件为准。

## 1. 职责边界

- 当前拓扑整合工作不设置 reuse 职责；进入当前工作项后，直接消费 Task Sheet 已指定的前置工作项及其正式结果。
- 不重新判断 residue / component 的 `topology_class`，不重新判断 topology-linked relation 是否成立，也不重新决定 `topology_effect_applied`。
- 继承已经建立的 `component_id + residue_id`、component 的 residue 组成、residue 顺序与 topology-linked relation；不重新分类或重新划分 component。
- GROMACS `moleculetype` 属于拓扑表示，不等同于既有 component；必要时可在拓扑整合中重新建立 `moleculetype`。

## 2. Task Sheet 输入集合

当前拓扑整合工作项由 Task Sheet 明确指定本次整合所依赖的前置工作项。

- 标准残基拓扑生成工作项可以为 0 / 1 / N 个；
- topology-linked 非标准残基参数化工作项可以为 0 / 1 / N 个；
- 独立非标准参数化工作项可以为 0 / 1 / N 个；
- 同一类前置任务存在多个工作项时，必须逐项处理，不得假定每类只有一个结果。

对于无需独立参数化、可直接参与整合的 `SOLVENT_COMPONENT` / `ION_COMPONENT`，其实际对象及参数定义来源由 topology preparation setup 在 Task Sheet 中分配。实际 residue 使用 `component_id + residue_id` 定位。

当前拓扑整合不扫描项目并自行选择前置结果，也不通过文件名、目录顺序或“最新文件”推断输入集合。

## 3. 引用文件确定与读取边界

根据当前 Task Sheet 及其指定的前置工作项，确定本次拓扑整合实际使用的上游 / 外部文件。当前拓扑整合正式结果使用结果记录内部的 `references` 保存这些实际引用文件，并由 `references/results.md` 定义具体 reference key、路径与字段引用语义；不另行建立平行的 `dependencies` 顶层字段。

`references` 中的条目不仅用于记录文件来源，也作为当前正式结果内部可复用的文件引用。后续结果字段、诊断记录或 evidence 需要指向同一文件时，应复用相应 reference key，而不是重复建立另一套文件身份或路径记录。

执行 Agent 确定并读取这些文件时，只展开到当前拓扑整合实际需要的深度：

- 上游正式结果中由当前整合实际消费的结果文件和直接结果信息，应按需要读取；
- 除非当前整合确有需要，不继续展开上游正式结果自身用于记录其上游 / 外部文件的依赖引用部分。

上述“不继续展开”是对执行 Agent 的读取行为限制，不是当前正式结果接口本身的字段语义。

引用文件无法完整定位或存在未解决歧义时，不继续执行拓扑整合。

## 4. 当前已确认的引用文件范围

当前拓扑整合正式结果的 `references` 至少包括：

- 当前对象对应的 `classification_result.yaml`；
- 当前对象对应的 `stage1_final.pdb`；
- 与该结构对应的 `stage1_final_map.yaml`；
- Task Sheet 指定的全部标准残基拓扑生成正式结果记录及下列已确认的结果文件；
- Task Sheet 指定的全部 topology-linked 非标准残基参数化正式结果记录及下列已确认的结果文件；
- Task Sheet 指定的全部独立非标准参数化正式结果记录及下列已确认的结果文件；
- Task Sheet 已明确分配、可直接参与整合的 solvent / ion 实际对象所采用的参数定义来源文件。

`stage1_final.pdb` 与 `stage1_final_map.yaml` 的结果 owner 是结构准备最终重排与映射任务；后续结构准备终检只读检查这两个正式结果，不生成新的 PDB 或 map。

三类前置正式结果读取当前拓扑整合实际需要的结果文件和直接结果信息；不因此继续递归展开这些正式结果记录自身的上游依赖引用。

### 已确认的基础 reference key

```yaml
references:
  BASIS_1: /absolute/path/to/classification_result.yaml
  STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  MAP_1: /absolute/path/to/stage1_final_map.yaml
```

### 已确认的前置工作项分组与编号规则

每个 Task Sheet 指定的前置工作项在 `references` 中建立一组条目。

- 标准残基拓扑生成工作项使用 `STD_n_*`；
- topology-linked 非标准残基参数化工作项使用 `LINKED_n_*`；
- 独立非标准残基参数化工作项使用 `IND_n_*`。

其中 `n` 表示当前类别中的前置工作项序号。

标准残基拓扑生成正式结果中存在多个 chain `.itp` 时，使用 `STD_n_ITP_m`；其中 `m` 表示该前置工作项正式结果中的 `.itp` 序号。

### 已确认的标准残基拓扑生成展开项

```yaml
STD_1_RESULT: /absolute/path/to/standard_residue_topology_result.yaml
STD_1_STRUCTURE: /absolute/path/to/standard.gro
STD_1_MAP: /absolute/path/to/standard.map
STD_1_TOP: /absolute/path/to/standard.top
STD_1_ITP_1: /absolute/path/to/chain_1.itp
STD_1_ITP_2: /absolute/path/to/chain_2.itp
```

### 已确认的 topology-linked 非标准残基参数化展开项

```yaml
LINKED_1_RESULT: /absolute/path/to/topology_linked_parameterization_result.yaml
LINKED_1_MODEL: /absolute/path/to/parameterization_model.mol2
LINKED_1_MODEL_MAP: /absolute/path/to/parameterization_model.map
LINKED_1_CHARGE: /absolute/path/to/parameterization.chg
LINKED_1_CHARGE_RESULT: /absolute/path/to/charge_fitting_result.yaml
LINKED_1_STRUCTURE: /absolute/path/to/parameterized_structure.gro
LINKED_1_TOPO: /absolute/path/to/parameterized_topology.itp
```

### 已确认的独立非标准残基参数化展开项

```yaml
IND_1_RESULT: /absolute/path/to/independent_nonstandard_parameterization_result.yaml
IND_1_MODEL: /absolute/path/to/parameterization_model.mol2
IND_1_MODEL_MAP: /absolute/path/to/parameterization_model.map
IND_1_CHARGE: /absolute/path/to/parameterization.chg
IND_1_CHARGE_RESULT: /absolute/path/to/charge_fitting_result.yaml
IND_1_TOPO: /absolute/path/to/parameterized_topology.itp
IND_1_STRUCTURE: /absolute/path/to/parameterized_structure.gro
IND_1_STRUCTURE_MAP: /absolute/path/to/parameterized_structure.map
```

上述 YAML 中的 `_1` / `_2` 用于展示已冻结的编号规则，不表示实际工作项或结果文件数量固定。正式执行时按 Task Sheet 指定的工作项和各正式结果中的实际结果文件数量生成相应条目。

`references/results.md` 最终正文的解释性表述仍需在本轮讨论中继续校正；本节冻结的是 reference key 体系、分组方式与展开项本身，不冻结此前讨论草稿中的不严谨表述。

### `references` 结果格式性质

`references/results.md` 中给出的 `references` YAML 结构不是说明性示例，而是当前拓扑整合正式结果应遵循的规范性记录格式。

执行时按实际对象和前置工作项数量扩展同类 reference key；实际不存在的工作项或结果文件不建立占位条目。完整绝对路径替换格式中的占位路径。除这些由实际执行数量和路径决定的变化外，结果记录应遵循 `references/results.md` 已确定的 key 命名和组织方式，不由执行 Agent 自由改写成另一套结构。

## 5. `moleculetype` 组织

拓扑整合需要对进入当前工作项的 residue / component 进行 `moleculetype` 组织。

- 主 `SKILL.md` 在拓扑整合主线中保留 `moleculetype` 组织，并提供 `references/moleculetype_organization.md` 的读取入口；
- `references/moleculetype_organization.md` 定义具体组织规则；
- `references/results.md` 定义 `moleculetype` 组织结果的正式记录方式与相关字段语义。

`moleculetype` 组织不得改变既有 `component` 身份、`component_id + residue_id`、component 的 residue 组成或已确认的 topology-linked relation；其结果是建立 GROMACS 拓扑所需的 `moleculetype` 组织。

`references/moleculetype_organization.md` 的进入说明固定为：

> 对当前 Task Sheet 指定进入拓扑整合的全部 residue / component 进行 `moleculetype` 组织。
>
> 组织时结合这些对象之间已确认的 topology-linked relation，以及各前置拓扑结果提供的结构、映射和 topology 信息。

上述两句之后直接进入代表性情况说明，不再设置独立的 `Organization basis` 或重复解释拓扑整合已经确定的输入来源。

### 已确认的代表性情况

- topology-linked 非标准残基连接一条标准链时，将该非标准残基与相关标准链组织到同一个 `moleculetype`。
- topology-linked 非标准残基连接多条标准链时，将该非标准残基与相关标准链组织到同一个 `moleculetype`。
- 多个 topology-linked 非标准残基连接同一条标准链时，将该标准链与这些 topology-linked 非标准残基组织到同一个 `moleculetype`。
- 未参与 topology-linked relation 的标准链，如无其它 topology 信息要求改变其组织，保留标准残基拓扑生成结果中的 `moleculetype` 组织。
- 独立非标准残基、solvent 和 ion 按各自采用的 topology 定义组织 `moleculetype`；不存在额外连接关系时，不与其它对象合并。

### `moleculetype` 结果记录

`references/results.md` 必须定义 `moleculetype` 组织结果如何进入当前拓扑整合的正式结果记录。

该记录至少需要明确每个整合后的 `moleculetype` 及其包含的 residue / component；成员身份使用既有 `component_id + residue_id` 表达。具体字段名称、与结果 topology 文件的关联方式及其它记录项，在完整结果接口设计时确定。

## 6. 正式文本规则

正式生成 `SKILL.md`、`references/results.md` 或其它科研执行 reference 时，不得使用 `Stage 1`、`1.2`、`2.2`、`2.3`、`2.4`、`2.5` 等编号简称代替任务、结果、输入、依赖或职责语义。正式文本必须直接写明任务名称、正式结果文件、数据字段、对象或职责语义。

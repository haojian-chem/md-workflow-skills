# Workflow 2 Stage 2.5 current design freeze

Status: CURRENT AUTHORING FREEZE

本文件集中保存本轮重新设计中已经确认的 topology integration and assembly 规则，作为后续正式生成对应 `SKILL.md` 与 local references 的当前 authoring source。

历史 2.5 freeze 仅作为讨论与追溯参考，不自动继承其结论。历史内容只有在本轮重新确认后，才能进入本文件并成为当前生成依据；与本文件冲突时，以本文件为准。

## 1. 职责边界

- 当前拓扑整合工作不设置 reuse 职责；进入当前工作项后，直接消费 Task Sheet 已指定的前置工作项及其正式结果。
- 不重新判断 residue / component 的 `topology_class`，不重新判断 topology-linked relation 是否成立，也不重新决定 `topology_effect_applied`。
- 继承已经建立的 `component_id + residue_id`、component membership、residue order 与 topology-linked relation；不重新分类或重新划分 component。
- GROMACS `moleculetype` 属于最终 topology representation，必要时可根据最终 topology organization 重新建立；不得把 `component` 与 `moleculetype` 视为同一层级对象。

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

- 上游正式结果中由当前整合实际消费的正式结果文件和直接结果信息，应按需要读取；
- 除非当前整合确有需要，不继续展开上游正式结果自身用于记录其上游 / 外部文件的依赖引用部分。

上述“不继续展开”是对执行 Agent 的读取行为限制，不是当前正式结果接口本身的字段语义。

引用文件无法完整定位或存在未解决歧义时，不继续执行拓扑整合。

## 4. 当前已确认的引用文件范围

当前拓扑整合正式结果的 `references` 至少包括：

- 当前对象对应的 `classification_result.yaml`；
- 当前对象对应的 `stage1_final.pdb`；
- 与该结构对应的 `stage1_final_map.yaml`；
- Task Sheet 指定的全部标准残基拓扑生成正式结果记录；
- Task Sheet 指定的全部 topology-linked 非标准残基参数化正式结果记录；
- Task Sheet 指定的全部独立非标准参数化正式结果记录；
- Task Sheet 已明确分配、可直接参与整合的 solvent / ion 实际对象所采用的参数定义来源文件。

`stage1_final.pdb` 与 `stage1_final_map.yaml` 的结果 owner 是结构准备最终重排与映射任务；后续结构准备终检只读检查这两个正式结果，不生成新的 PDB 或 map。

标准残基拓扑生成、topology-linked 非标准残基参数化和独立非标准参数化的正式结果记录除作为正式结果入口外，可以按当前拓扑整合实际消费范围展开其结果文件，并将需要在当前正式结果、诊断或 evidence 中直接引用的结果文件建立为当前 `references` 条目。该展开只针对上游正式结果自身的结果部分，不因此继续递归展开其上游依赖引用。

三类前置正式结果具体展开哪些结果文件、采用哪些 reference key，当前尚未确认；讨论草稿中出现的展开项不得视为冻结内容。

### 已确认的基础 reference key

当前已确认：

```yaml
references:
  BASIS_1: /absolute/path/to/classification_result.yaml
  STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  MAP_1: /absolute/path/to/stage1_final_map.yaml
```

其中路径仅表示字段语义；正式执行时记录实际完整绝对路径。

具体 reference key、文件分组、路径引用以及结果 / 诊断 / evidence 对这些 reference key 的使用方式，由 topology integration and assembly 的 `references/results.md` 定义。

### `references` 结果格式性质

`references/results.md` 中给出的 `references` YAML 结构不是说明性示例，而是当前拓扑整合正式结果应遵循的规范性记录格式。

执行时按实际对象和前置工作项数量扩展同类 reference key；实际不存在的工作项或结果文件不建立占位条目。完整绝对路径替换格式中的占位路径。除这些由实际执行数量和路径决定的变化外，结果记录应遵循 `references/results.md` 已确定的 key 命名和组织方式，不由执行 Agent 自由改写成另一套结构。

未在本轮确认的临时 key 名或结果展开项，不因出现在讨论草稿中自动冻结。

## 5. 正式文本规则

正式生成 `SKILL.md`、`references/results.md` 或其它科研执行 reference 时，不得使用 `Stage 1`、`1.2`、`2.2`、`2.3`、`2.4`、`2.5` 等编号简称代替任务、结果、输入、依赖或职责语义。正式文本必须直接写明任务名称、正式结果文件、数据字段、对象或职责语义。

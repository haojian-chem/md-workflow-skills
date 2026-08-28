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

## 3. 依赖确定与记录

根据当前 Task Sheet 及其指定的前置工作项，确定本次拓扑整合实际使用的全部依赖文件，并按照 `references/results.md` 记录到当前拓扑整合结果中。依赖无法完整定位或存在未解决歧义时，不继续执行拓扑整合。

执行 Agent 确定依赖时，只展开到当前拓扑整合实际需要的深度：

- 上游正式结果中由当前整合实际消费的正式结果文件和直接结果信息，应按需要读取；
- 除非当前整合确有需要，不继续展开上游正式结果自身的 `dependencies` / `references` 依赖链。

上述“不继续展开”是对执行 Agent 的读取行为限制，不是当前正式结果接口本身的字段语义。

## 4. 当前已确认的直接依赖范围

当前拓扑整合正式结果的依赖范围至少包括：

- 当前对象对应的 `classification_result.yaml`；
- 当前对象对应的 `stage1_final.pdb`；
- 与该结构对应的 `stage1_final_map.yaml`；
- Task Sheet 指定的全部标准残基拓扑生成正式结果记录，以及当前整合实际需要的其正式结果文件；
- Task Sheet 指定的全部 topology-linked 非标准残基参数化正式结果记录，以及当前整合实际需要的其正式结果文件与直接结果信息；
- Task Sheet 指定的全部独立非标准参数化正式结果记录，以及当前整合实际需要的其正式结果文件；
- Task Sheet 已明确分配、可直接参与整合的 solvent / ion 实际对象及其参数定义来源。

`stage1_final.pdb` 与 `stage1_final_map.yaml` 的结果 owner 是结构准备最终重排与映射任务；后续结构准备终检只读检查这两个正式结果，不生成新的 PDB 或 map。

具体依赖字段、文件分组与路径记录语义由 topology integration and assembly 的 `references/results.md` 定义。

## 5. 正式文本规则

正式生成 `SKILL.md`、`references/results.md` 或其它科研执行 reference 时，不得使用 `Stage 1`、`1.2`、`2.2`、`2.3`、`2.4`、`2.5` 等编号简称代替任务、结果、输入、依赖或职责语义。正式文本必须直接写明任务名称、正式结果文件、数据字段、对象或职责语义。

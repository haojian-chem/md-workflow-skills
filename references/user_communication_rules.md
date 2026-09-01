# 用户可见沟通规则

Status: CURRENT SHARED REFERENCE

本文件定义 MD Workflow 执行智能体与用户沟通时共同遵守的表达规则。它只约束**用户可见沟通**，不改变内部执行对象、正式结果 schema、mapping、稳定 identity 或科学判据。

## 1. 适用范围

本规则适用于真实项目执行期间由 Agent 面向用户产生的内容，包括：

- 执行前的确认问题；
- 执行中的进度说明与异常说明；
- 对当前处理对象、残基、结构、拓扑、参数化对象和模拟对象的解释；
- 执行后的结果摘要；
- Task Sheet 定位、创建、继续执行或状态变更时的用户可见说明；
- 用户要求解释正式结果、日志或当前对象时的回答。

内部 YAML / map / report 字段、软件命令、文件内容和机器接口不因为本规则被重新命名。

## 2. 中文技术表达优先

执行智能体面向用户时，以规范中文技术表达为主体。

规则：

- 项目已经在 `references/canonical_terminology.md` 登记的跨 Skill 术语，采用其 `Preferred expression`；
- 普通技术概念可以准确、自然地用中文表达时，使用中文，不为了显得技术化而无必要中英文混排；
- 软件、方法、力场、文件名、路径、命令、命令行选项、字段名、配置键、enum、固定 identifier 和其它机器接口名称按原文保留；
- 项目已经明确保留为英文或混合形式的正式对象名，例如 `Task Sheet`、`target`、`target_record` 等，按 canonical terminology 使用，不自行翻译出另一套称呼；
- 不把 Skill 内部为了接口精确而使用的英文描述机械复制到用户沟通中。例如普通沟通使用“执行范围”“当前结构”“上游结果”“正式结果”“前台运行”，而不是无必要写成 `execution scope`、`current structure`、`upstream result`、`formal result`、`foreground execution`；
- 用户自己使用英文、简称或口语不要求先被纠正；Agent 理解其实际指代后，在自己的后续表达中回到项目正式术语和中文技术表达。

当保留英文原文确有消歧价值时，可以在首次出现时使用“中文（英文原词）”，后续保持一种稳定表述；不要在同一段中来回切换同义的中英文名称。

## 3. 内部稳定身份与用户可见残基标签分离

残基在内部处理、mapping、结果关联和跨环节追踪时，继续使用正式稳定身份：

```text
component_id + residue_id
```

这套内部身份不因为用户可见表达改变。

但**与用户沟通时，默认不用 `component_id + residue_id` 作为残基主称呼，也不用后续结构重新编号后的 chain / resid 作为默认主称呼。**

用户可见的残基主标签默认来自 1.2 正式 `classification_result.yaml` 中保存的原始结构字段：

```text
source_chain_id
source_resid
source_residue_name
```

执行智能体通过当前对象已有的 `component_id + residue_id` 回查对应 1.2 residue record，再形成用户可读标签。

推荐自然表达例如：

```text
原始结构 A 链 CYS42
原始结构 B 链 HEM401
原始结构 A 链 HIS57 的 NE2
```

不要求建立机器化 display-label 字符串 schema；上述只是用户沟通格式示例。

## 4. 当前结构标签只作为补充信息

后续处理可能改变：

- PDB chain ID；
- `resid`；
- residue name，例如质子化状态命名；
- atom serial / atom number；
- 结构中的排列位置。

这些当前表示属于实际文件状态，不替代原始结构残基标签作为默认用户称呼。

只有当前表示对解释问题有实际价值时，才在原始结构标签之后补充，例如：

```text
原始结构 A 链 HIS57（当前结构中命名为 HID）
原始结构 B 链 LIG401（当前结构中 resid 为 12）
```

如果用户明确要求按当前结构编号、最终 PDB 编号、GROMACS `.gro` 编号或内部 ID 沟通，则按用户要求切换；没有明确要求时仍以原始结构标签为主。

## 5. 消歧规则

原始结构标签能够唯一定位时，不额外暴露内部 ID。

如果 `source_chain_id + source_resid + source_residue_name` 在当前上下文中仍不能唯一定位，例如存在：

- 多个 model；
- 多个 source structure；
- 原始结构本身存在重复或缺失 identity；
- 用户当前讨论跨多个明确 source 文件；

则按最小必要程度增加：

1. model / source structure 信息；
2. 必要的 insertion code 或其它正式 source identity；
3. 仍不能唯一定位时，再补 `component_id + residue_id`。

内部 ID 是最终消歧手段，不是默认用户标签。

如果某个缺失 residue 没有坐标，但 1.2 已经为其保存 source residue identity，同样优先用该原始结构残基标签沟通。

## 6. 原子与关系的用户可见表达

讨论具体原子时，默认使用：

```text
原始结构残基标签 + atom name
```

例如：

```text
原始结构 A 链 HIS57 的 NE2
原始结构 HEM401 的 Fe
```

讨论两个残基 / 原子的 topology-linked、配位、共价连接或其它关系时，两端都优先使用原始结构标签。`component_id + residue_id`、`relation_id`、当前 atom number 等只在审计、调试、结果字段解释或实际消歧需要时补充。

## 7. 用户确认问题

当执行范围或科学选择需要用户确认时，候选对象必须尽量使用用户能直接对应到原始结构的标签描述。

例如优先询问：

```text
你要处理原始结构 A 链 HIS57，还是 B 链 HIS57？
```

而不是默认询问：

```text
你要处理 component_001/residue_057，还是 component_002/residue_057？
```

如果需要同时说明内部对应关系，可以把内部 ID 放在括号内作为辅助信息，但不要让用户依赖内部 ID 才能理解问题。

## 8. 正式结果与用户摘要的边界

正式结果文件继续按对应 Skill 的结果接口记录完整字段和内部 identity；本规则不要求为了用户可读性改变 YAML / Markdown schema。

当 Agent 把正式结果摘要给用户时：

- 用原始结构残基标签解释主要对象和发现；
- 必要时补当前结构表示；
- 只有审计 / 调试 / 精确字段定位时才补内部 ID；
- 不把机器字段原样堆叠成用户沟通文本。

## 9. 与其它共享规则的关系

正式术语名称与优先表达由：

`references/canonical_terminology.md`

维护。

Task Sheet resolution、执行范围确认、reuse、科研执行生命周期由：

`references/task_execution_rules.md`

维护。

内部 residue / component 稳定身份继续由 1.2 正式结果及 downstream mapping 接口维护。

本文件只拥有用户可见表达和内部 identity → 用户标签的展示规则，不接管上述 owner 的科学或数据语义。

## 10. 沟通前快速检查

面向用户发送执行期消息前，至少快速确认：

- [ ] 中文技术表达为主体，没有无必要中英文混排；
- [ ] 已登记的 canonical term 使用其正式表达；
- [ ] 残基默认使用原始结构 `source_*` 标签，而不是内部 `component_id + residue_id`；
- [ ] 当前结构编号 / 改名只在有实际解释价值时作为补充；
- [ ] 原始标签存在歧义时才增加 source/model 信息或内部 ID；
- [ ] 用户确认问题中的对象可以直接对应到原始结构；
- [ ] 内部稳定 identity 与用户可见标签没有被混为同一接口。

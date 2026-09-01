# Result generation rules

Status: CURRENT SHARED REFERENCE

本文件定义本项目所有科研执行 Skill 共同遵守的 validation、正式结果生成、结果记录与结果接口规则。

各科研执行 Skill 继续拥有自身的：

- 正式结果集合；
- 结果文件 / 字段的具体科学与接口语义；
- Skill-specific validation requirement；
- project-result registration 白名单；
- 结果成为正式可用结果的具体条件。

本文件只拥有科研执行 Skill 共用的结果生成与记录机制，不建立统一科学结果 schema。

## 1. Validation ownership

Validation 默认跟随当前结果 owner：

```text
谁产生 / 判定结果
→ 谁定义该结果完成当前职责所需的 validation requirement
```

这条 ownership 规则只回答“谁负责定义必要检查”，**不要求每个结果 owner 都执行一套穷尽式、独立、重复的终检**。

Validation 应与当前操作和结果声明相匹配：

- 成熟软件组件已经直接完成主要变换时，可以用正常结束、关键输出存在及少量必要一致性检查确认当前操作；
- 当前执行过程中已经完成的检查不为了形式完整再重复一次；
- 如果项目另有可选独立 validation Skill，当前结果 owner 不复制其完整检查范围；
- 只有当前结果的正确使用确实依赖某项检查时，才把该检查纳入当前结果的完成条件；
- 避免把低成本但没有新增判别价值的检查机械堆叠成重复 validation pipeline。

Tool 可以负责自己确定性输出的机械 / 格式有效性；科研 Skill 仍负责判断该输出是否满足当前科研目标。

如果当前 Skill 将复杂 validation 细节下放到 local reference，该 reference 仍属于当前结果 owner；本文件不接管具体科学 validation procedure。

## 2. 正式结果与项目结果索引

`project_result_index.md` 只登记当前结果 owner 明确允许登记的正式结果或结果事项，不登记 debug、scratch、cache、中间工作文件或为了“完整”而产生的重复索引。

Skill-specific project-result registration 白名单由对应结果 owner 定义，包括：

- 哪些正式结果需要单独登记；
- 哪些正式结果由已登记的主结果继续定位；
- 哪些文件明确不进入项目结果索引。

`project_result_index.md` 是跨任务 / 跨对话的正式结果检索入口，不是当前结果内容的第二份副本。

## 3. 结果文件与路径语义

正式结果记录中的结果文件和依赖文件路径必须保持完整绝对路径语义。

由当前环节产生的结果文件应记录在对应结果字段或正式结果列表中；不得只把当前结果文件隐藏在 `references` 中而不形成明确结果字段 / 正式结果入口。

如果路径直接写入字段，则写实际完整绝对路径。

正式结果已经记录实际文件完整路径时，后续核查可以沿该路径读取对应工作目录和实际执行文件；不为了“结果自包含”把可从真实文件恢复的信息全部复制进 YAML / Markdown。只有对理解结果语义、reuse、恢复或跨任务检索真正有价值的信息才需要进入正式结果本身。

## 4. 结果记录内部 `references`

结果记录内部的 `references` 可以用于：

1. 定义当前结果实际依赖的上游 / 外部正式文件；
2. 定义多个结果字段复用的公共绝对路径或绝对路径前缀。

若多个结果字段共享相同绝对路径，可以写成：

```yaml
references:
  INPUT_STRUCTURE: /absolute/path/to/input.pdb
  RESULT_DIR: /absolute/path/to/current/result_directory

input_structure: ${INPUT_STRUCTURE}
report: ${RESULT_DIR}/report.yaml
structure: ${RESULT_DIR}/structure.pdb
```

`${PATH_KEY}` 或 `${PATH_KEY}/filename` 展开后的结果必须仍具有完整绝对路径语义。

如果同一绝对路径只使用一次，没有复用价值，直接写完整绝对路径通常更清楚；不为了格式统一强制创建 reference key。

reference key 只在当前结果记录的作用域内解释，不是项目级永久 identity，也不要求建立全局 registry。

## 5. Markdown 正式结果中的 `References`

如果当前 Skill 生成的正式结果本身是 Markdown，并且需要重复引用多个实际文件或公共绝对路径，可以在 Markdown 前部设置清楚的 `References` section，例如：

````markdown
## References

```yaml
references:
  FINAL_STRUCTURE: /absolute/path/to/stage1_final.pdb
  CLASSIFICATION_RESULT: /absolute/path/to/classification_result.yaml
  RESULT_DIR: /absolute/path/to/current/result_directory
```
````

正文或结构化片段随后可以使用 `${FINAL_STRUCTURE}`、`${CLASSIFICATION_RESULT}` 或 `${RESULT_DIR}/filename`。

如果 Markdown 只引用少量路径且不存在重复，直接写完整绝对路径即可，不强制增加 `References` section。

## 6. main `SKILL.md` 与详细结果接口

main `SKILL.md` 必须保留足够的 results 摘要，使 Agent 能确定：

- 当前职责产生什么正式结果；
- 正式结果入口是什么；
- 当前结果成为正式可用结果的必要完成条件；
- 如需解释详细结果格式 / 字段，应读取哪个 local reference。

当结果接口并非简单单文件输出时，优先把详细结果说明独立为：

```text
<skill>/references/results.md
```

以下任一情况通常足以建立 `references/results.md`：

- 当前 Skill 产生多个正式结果文件；
- 存在 YAML / JSON / Markdown 等需要解释字段语义的结构化 report；
- 当前结果会被一个或多个后续 Skill 直接读取；
- 结果文件之间存在需要说明的定位、mapping、validation 或 source-result 关系；
- 当前 Skill 有非平凡的 project-result registration 白名单；
- 当前结果使用 `references`、路径变量或其它需要稳定解释的结果内部引用机制。

只有一个简单 artifact、没有额外字段语义、没有复杂定位关系时，可以继续在 main `SKILL.md` 中直接说明，不为了目录对称机械创建 `results.md`。

一旦建立 `references/results.md`：

```text
main SKILL.md
→ 保留正式结果摘要、结果入口和必要完成条件
→ 指明何时读取 references/results.md

references/results.md
→ 拥有当前 Skill 的详细结果接口说明
```

不要在 main Skill 与 `results.md` 中完整复制同一套结果格式或字段说明。

`<skill>/references/results.md` 是 Skill package 内的 reference source，不是科研项目执行时生成的 result artifact。

## 7. `references/results.md` 的内容边界

不要求固定 section schema，但应按当前结果复杂度覆盖实际需要的信息。常见内容包括：

- 正式结果集合与各文件用途；
- task / target / run-unit 等结果目录组织；
- 主结果与辅助结果之间的定位关系；
- 结构化结果的关键字段语义；
- identifier、枚举、`null`、路径、数组顺序等解释规则；
- 为正确理解结果所必需的内部一致性约束；
- 对应 schema 的实际路径及 schema 与自然语言语义的职责分工；
- validation artifact / validation conclusion 与结果正式可用性的关系；
- project-result registration 白名单及未单独登记结果的定位方式。

如果某个字段的科学含义只有在当前 Skill 的科学判断规则下才能理解，`results.md` 可以引用真正拥有该判断规则的 main Skill / local reference；不要把完整科学判断过程复制进结果说明。

## 8. `results.md` 与 schema 的分工

如果当前结果确有稳定、机器可校验的数据结构，可以使用 `schemas/`。

分工为：

```text
references/results.md
→ 解释结果文件用途、字段科学 / 接口语义、文件关系和结果生命周期

schema
→ 约束机器结构、required field、type、enum 等可机械校验内容
```

不要在 `results.md` 中逐字复制完整 schema，也不要只因为存在 `results.md` 就机械创建 schema。

同样，不要依靠 schema 代替需要由 Agent 理解的字段科学语义。

## 9. 跨 Skill 查阅结果

下游或其它科研 Skill 如果只需要回答：

```text
这个上游结果有哪些文件？
某个字段是什么意思？
哪个文件是正式入口？
如何解析其中的路径 / references？
```

可以按需直接读取上游 Skill 的 `references/results.md`，不必为了这些接口信息重新加载上游完整科学执行规则。

如果需要理解结果是如何科学判定出来的、某项 evidence 为什么足以支持结论，仍应读取真正拥有该科学规则的上游 main Skill / local reference。

读取外部 `results.md` 只获得解释该正式结果的能力，不获得修改结果 owner 的科学规则、validation 或文件生命周期的 authority。

## 10. 两种 `references` 不得混淆

必须区分：

```text
<skill>/references/*.md
→ Skill package 中的规则 / 结果接口 reference

正式结果记录内部的 references / Markdown References section
→ 当前结果记录自己的文件与路径引用机制
```

前者属于 Skill source；后者属于实际科研结果的数据内容。两者名称相似但 authority 和生命周期不同。

## 11. Results 不是 handoff

结果说明只定义当前结果本身，包括结果文件、字段语义、内部关系、validation 关系和项目结果索引语义。

不得借 results、`references/results.md`、report format、schema 示例或字段含义说明规定：

- 下一步必须执行什么；
- 下游读取某字段后应执行什么操作、判断或转换；
- 下游 Skill 的方法选择或 validation；
- 为相邻 Step 交接额外生成 handoff package / handoff YAML。

下游如何消费上游结果，由下游 Skill 自己的输入 / 对象规则定义。

如果当前 Stage 存在真正拥有 Stage-wide orchestration 的 main Skill，Stage-specific route / shared-object relationship 可以由该 Stage main 拥有；如果当前 Stage 不设置 Stage main Skill，则由 Task Execution Agent 根据 Task Sheet、当前 Step 的正式结果 / input contract 和实际执行证据推进，不为普通相邻关系制造 synthetic Stage owner。

## 12. 结果规则检查

- [ ] 当前结果 owner 与 validation ownership 清楚，且 validation 强度与实际职责匹配；
- [ ] 没有为了“结果 owner 必须 validation”而复制可选独立终检或重复已有软件/过程检查；
- [ ] main `SKILL.md` 保留足够的正式结果摘要与详细结果说明入口；
- [ ] 非简单结果接口已经评估是否需要 `references/results.md`；
- [ ] 如果存在 `results.md`，详细结果格式没有在 main Skill 再复制一份；
- [ ] 正式结果文件、依赖文件和 result-internal reference 展开后均具有完整绝对路径语义；
- [ ] 当前环节自己生成的结果文件被明确记录为结果，而不是只隐藏在 `references` 中；
- [ ] 已有结果路径足以恢复的信息没有为了自包含被无必要复制进结果记录；
- [ ] Markdown result 如使用 `References` section，其 keys 只在当前结果文档内解释；
- [ ] `references/results.md` 与结果记录内部 `references` 没有混淆；
- [ ] schema 与自然语言结果语义没有维护两套重复规范；
- [ ] project-result registration 白名单清楚，未把 debug / scratch / cache 当正式索引项；
- [ ] validation 关系清楚，但没有复制其它 owner 的完整 validation procedure；
- [ ] results 说明没有重新写成下游 handoff 规则。

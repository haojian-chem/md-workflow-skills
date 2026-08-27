# 科研 Skill 结果生成规则

Status: CURRENT

本文件指导科研 Skill authoring 时设计和编写正式 results。它在 `../../references/task_execution_rules.md` 的 `Validation and results` 通用语义基础上工作，不建立第二套 runtime 结果规则，也不改变当前结果 owner。

跨 Stage 的通用结果语义仍由：

`../../references/task_execution_rules.md`

拥有；当前 Stage / Step / capability Skill 继续拥有自己的正式结果集合、结果字段语义、validation requirement 与 project-result registration 白名单。

## 1. 目标

正式结果设计应使后续 Agent 在只需要**定位和解释上游正式结果**时，不必重新读取完整上游执行过程。

因此，结果说明需要明确回答：

- 当前 Skill 的正式结果文件 / 结果对象有哪些；
- 每个结果的用途和相互关系；
- 结果如何定位；
- 结构化结果中的关键字段分别表示什么；
- 字段的路径、`null`、枚举、identity 等语义；
- 为正确解释当前结果所必需的结果内部约束；
- 如存在 schema，结果语义与 schema 如何分工；
- 哪些正式结果进入 `project_result_index.md`，哪些由已登记结果继续定位；
- validation 与结果成为正式可用结果之间存在什么必要关系。

结果说明只定义**当前结果本身**。它不是 handoff 规则，不规定下游 Skill 根据某个字段应执行什么操作、判断或转换。

## 2. main `SKILL.md` 与 `references/results.md`

main `SKILL.md` 必须保留足够的 results 摘要，使 Agent 知道当前职责产生什么正式结果，以及何时需要进一步读取详细结果说明。

当结果接口并非简单单文件输出时，优先把详细结果说明独立为：

`references/results.md`

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
→ 保留正式结果摘要、结果入口和必要的完成条件
→ 指明何时读取 references/results.md

references/results.md
→ 拥有当前 Skill 的详细结果接口说明
```

不要在 main Skill 与 `results.md` 中完整复制同一套结果格式或字段说明。

`<skill>/references/results.md` 是 **Skill package 内的 reference source**，不是科研项目执行时生成的结果文件；真实结果仍写入项目 execution directory。

## 3. `references/results.md` 应说明什么

不要求固定 section schema，但应按当前结果复杂度覆盖实际需要的信息。常见内容包括：

- 正式结果集合与各文件用途；
- task / target / run-unit 等结果目录组织；
- 主结果与辅助结果之间的定位关系；
- 每个结构化结果的字段语义；
- identifier、枚举、`null`、路径和数组顺序等解释规则；
- 为正确理解结果所必需的内部一致性约束；
- 对应 schema 的实际路径及 schema 与自然语言语义的职责分工；
- validation artifact / validation conclusion 与结果正式可用性的关系；
- project-result registration 白名单及未单独登记结果的定位方式。

如果某个字段的科学含义只有在当前 Skill 的科学判断规则下才能理解，`results.md` 可以引用真正拥有该判断规则的 main Skill / local reference；不要把完整科学判断过程复制进结果说明。

## 4. 路径与结果内部 `references`

路径和结果内部引用遵守 `../../references/task_execution_rules.md` 的 `Validation and results` 通用规则。

### 4.1 绝对路径语义

正式结果记录中的结果文件和依赖文件路径必须保持完整绝对路径语义。

如果直接写路径，则写实际完整绝对路径。

如果使用结果内部 `references` 进行复用，变量展开后的最终路径仍必须是完整绝对路径。

### 4.2 `references` 的用途

结果记录内部的 `references` 可以用于：

1. 定义当前结果实际依赖的外部 / 上游正式文件；
2. 定义多个结果字段共同复用的绝对路径前缀。

例如结构化结果可以使用：

```yaml
references:
  INPUT_STRUCTURE: /absolute/path/to/input.pdb
  RESULT_DIR: /absolute/path/to/current/result_directory

input_structure: ${INPUT_STRUCTURE}
report: ${RESULT_DIR}/report.yaml
structure: ${RESULT_DIR}/structure.pdb
```

这里 `${INPUT_STRUCTURE}` 与 `${RESULT_DIR}/...` 展开后都必须具有完整绝对路径语义。

由**当前环节产生**的正式结果文件仍应记录在对应结果字段中；不能只把它们藏在 `references` 中而不形成明确结果字段 / 正式结果列表。

如果同一绝对路径只出现一次、没有复用价值，直接写完整路径通常更清楚，不为了形式统一强制创建 reference key。

### 4.3 Markdown 正式结果中的 `References`

如果当前 Skill 生成的正式结果本身是 Markdown，并且需要重复引用多个实际文件或公共绝对路径，可以在 Markdown 前部设置清楚的 `References` section，例如：

```markdown
## References

```yaml
references:
  FINAL_STRUCTURE: /absolute/path/to/stage1_final.pdb
  CLASSIFICATION_RESULT: /absolute/path/to/classification_result.yaml
  RESULT_DIR: /absolute/path/to/current/result_directory
```
```

正文或结构化片段随后可以使用 `${FINAL_STRUCTURE}`、`${CLASSIFICATION_RESULT}` 或 `${RESULT_DIR}/filename`。所有引用都只在当前结果文档内解释；reference key 不是项目级永久 identity，也不要求建立全局 registry。

如果 Markdown 只引用少量路径且不存在重复，直接写完整绝对路径即可，不强制增加 `References` section。

### 4.4 两种 `references` 不得混淆

必须区分：

```text
<skill>/references/*.md
→ Skill package 中的规则 / 结果接口 reference

正式结果记录内部的 references / Markdown References section
→ 当前结果记录自己的文件与路径引用机制
```

前者属于 Skill source；后者属于实际科研结果的数据内容。两者名称相似但 authority 和生命周期完全不同。

## 5. `results.md` 与 schema 的分工

如果当前结果确有稳定、机器可校验的数据结构，可以使用 `schemas/`。

分工固定为：

```text
references/results.md
→ 解释结果文件用途、字段科学/接口语义、文件关系和结果生命周期

schema
→ 约束机器结构、required field、type、enum 等可机械校验内容
```

不要在 `results.md` 中逐字复制完整 schema，也不要只因为存在 `results.md` 就机械创建 schema。

同样，不要依靠 schema 代替需要由 Agent 理解的字段科学语义。

## 6. Project result registration

`project_result_index.md` 是跨任务 / 跨对话的正式结果检索入口，不是当前结果内容的第二份副本。

当前结果 owner 应明确自己的 project-result registration 白名单：

- 哪些正式结果值得单独登记；
- 哪些正式结果由已登记的主结果继续定位；
- 哪些 debug、scratch、cache 或中间文件不得登记。

如果当前 Skill 建立了 `references/results.md`，详细白名单与定位关系优先在该文件定义；main `SKILL.md` 只保留执行时必须知道的摘要和入口。

登记到 `project_result_index.md` 的结果路径使用完整绝对路径语义。

## 7. Validation 与 results 的关系

Validation 默认跟随当前结果 owner。

`references/results.md` 可以说明：

- 哪个 validation artifact 对应哪个正式结果；
- 某个 validation conclusion 是否是结果成为正式可用结果的必要条件；
- validation result 如何从正式结果继续定位。

但详细的科学 validation procedure 仍由当前 main Skill 或真正拥有该 validation 细节的 local reference 定义。不要为了结果说明再复制一套 validation 规则。

## 8. 跨 Skill 查阅结果

下游或其它科研 Skill 如果只需要回答：

```text
这个上游结果有哪些文件？
某个字段是什么意思？
哪个文件是正式入口？
如何解析其中的路径 / references？
```

可以按需直接读取上游 Skill 的 `references/results.md`，而不必为了这些接口信息重新加载上游完整科学执行规则。

如果需要理解结果是如何科学判定出来的、某项 evidence 为什么足以支持结论，仍应读取真正拥有该科学规则的上游 main Skill / reference。

读取外部 `results.md` 只获得解释当前正式结果的能力，不获得修改该结果 owner 的科学规则、validation 或文件生命周期的 authority。

## 9. 禁止把 results 重新写成 handoff

`references/results.md` 不应包含：

- “下一步必须执行 X”；
- “下游读取字段 A 后应改变为 Y”；
- 下游 Skill 的内部方法选择；
- 下游 validation；
- 为了相邻 Step 交接额外生成的 handoff package / handoff YAML。

普通相邻 Step 的 Stage-level 流程关系由拥有该关系的 Stage main Skill 表达；下游如何消费上游结果，由下游 Skill 自己的输入 / 对象规则定义。

## 10. Authoring self-check

设计或重构当前 Skill results 时确认：

- [ ] 已读取 `../../references/task_execution_rules.md` 的 `Validation and results`；
- [ ] main `SKILL.md` 保留了足够的正式结果摘要与结果说明入口；
- [ ] 非简单结果接口已评估是否需要 `references/results.md`；
- [ ] 如果存在 `results.md`，详细结果格式没有在 main Skill 再复制一份；
- [ ] 正式结果文件、依赖文件和 result-internal reference 展开后均具有完整绝对路径语义；
- [ ] 当前环节自己生成的结果文件被明确记录为结果，而不是只隐藏在 `references` 中；
- [ ] Markdown result 如使用 `References` section，其 keys 只在当前结果文档内解释；
- [ ] `references/results.md` 与结果记录内部 `references` 没有混淆；
- [ ] schema 与自然语言结果语义没有维护两套重复规范；
- [ ] project-result registration 白名单清楚，未把 debug / scratch / cache 当正式索引项；
- [ ] validation 关系清楚但没有复制完整 validation procedure；
- [ ] 结果说明没有规定下游 Skill 应如何执行。

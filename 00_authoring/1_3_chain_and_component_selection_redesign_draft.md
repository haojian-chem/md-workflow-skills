# 1.3 Chain and Component Selection — Redesign Draft

> 状态：**DRAFT / 未完成**
>
> 本文件只记录 1.3 当前已讨论并同意的重构方向，供后续继续设计使用。
> 它不是运行时 Skill，不替代 `02_operations/chain_and_component_selection/SKILL.md` 或 Validator，也不表示 1.3 已完成 Lightweight Runtime v2 迁移。

## 1. 当前定位

1.3 位于：

```text
1.2 component_and_residue_classification
→ 1.3 chain_and_component_selection
→ 1.4 altloc_occupancy_resolution
```

当前基础工作目录：

```text
01_structure_preparation/03_chain_and_component_selection/
```

实际执行时采用 Lightweight Runtime v2 的任务隔离目录：

```text
01_structure_preparation/03_chain_and_component_selection/<task_id>/
```

Manager 只在 Task Sheet 中记录该路径，不创建 `<task_id>/`；Task Execution Agent 在确认不能复用、确实需要执行 1.3 时再创建。

## 2. 上游输入边界

1.3 的上游依据包括：

```text
1.2 classification_result.yaml
对应的源结构文件
用户对保留对象的自然语言描述
```

1.3 必须使用 1.2 已物化的 chain / component / residue / relation 信息。

尤其：

- 不重新执行 1.2 分类；
- 不自行重建 1.2 opaque ID 算法；
- 不根据文件名、链名习惯或其他隐式线索绕过 1.2 已建立的身份信息。

## 3. 1.3 的操作对象层级

当前重设计把 1.3 的选择对象限制为两个层级：

```text
chain
residue
```

不再把“component”作为用户必须直接操作的第三种选择语法层级。

1.2 中的 component / relation 信息仍可作为解释、校验和映射依据，但 1.3 最终需要把用户意图转换为明确的：

```text
保留哪些 chain
保留哪些 residue
```

## 4. Selection specification 的基本方向

selection specification 只描述**需要保留的内容**。

不设计成：

```text
retain: ...
remove: ...
```

双向规则。

当前方向是只记录 retain 集合本身，例如概念上：

```text
structure 1
- chain A
- chain B residue 100-150
- chain C residue 27
```

具体 schema、字段名和 ID 表达方式尚未冻结，后续设计时再确定。

## 5. 支持的用户表达

需要支持至少以下自然语言意图：

### 5.1 整条链

```text
保留 A 链
保留 A、B 链
只要链 A 和 C
```

转换为 chain 级 retain 信息。

### 5.2 链内残基

需要支持：

```text
保留 A 链 100–150
保留 A 链的 100 到 150 号残基
保留 A:100-150
```

转换为 residue 级 retain 信息，并且必须保留所属 chain 语义。

### 5.3 单个或多个残基

需要支持明确到 chain + residue 的选择，例如：

```text
保留 A 链 100、105、110
```

具体连续范围与离散 residue 的内部 schema 表达尚未冻结。

## 6. 必须确认的冲突表达

如果同一输出结构中同时出现：

```text
保留 A 链
以及
保留 A 链 100–150
```

不能自动解释为任一方案。

该表达至少存在两种可能语义：

1. 用户想保留完整 A 链，而 100–150 只是强调关注区域；
2. 用户实际只想保留 A 链 100–150，但前面的“保留 A 链”是宽泛表述。

因此必须向用户确认，不能静默把 residue 子集并入完整链，也不能自动把完整链缩窄到 residue 范围。

一般规则：

> 同一输出结构中，如果 chain 级 retain 与该 chain 的 residue 子集 retain 同时出现，而且二者语义不能明确合并，则触发用户确认。

## 7. 单结构与多结构输出

默认情况下，1.3 只生成**一个**保留结果结构。

不得仅因为用户列出了多个 chain / residue 集合，就自动拆分成多个结构。

多结构输出必须由用户明确提出，例如：

```text
把 A、B、C 分别保存成一个结构
建立 3 个结构：结构 1 保留 A，结构 2 保留 B，结构 3 保留 C
分别生成 A-only 和 B-only 两套结构
```

只有出现这类明确拆分意图时，才建立多个 selection specification / 多个输出结构。

以下表达本身**不**代表多结构输出：

```text
保留 A、B、C 链
保留 A 链和 B 链 50–80
```

默认解释为同一个输出结构中的 retain 集合。

## 8. 多结构时的任务语义

1.3 本身允许一次任务产生多个结构结果，但前提是用户已经明确要求拆分。

每个输出结构都必须有独立且明确的 retain specification，不能依赖“剩余部分”“其他链”之类隐式补集逻辑。

概念示例：

```text
output_structure_1
- chain A

output_structure_2
- chain B
- chain C residue 10-50
```

具体输出命名、manifest 结构和 result-index 登记方式尚未冻结。

## 9. 当前不属于 1.3 的操作

1.3 不负责：

- altLoc / occupancy 处理；
- missing-region completion；
- protonation；
- 原子级筛选；
- 按 atom name 选择；
- 化学键编辑；
- 拆断共价连接；
- topology 生成；
- 重新分类 residue / component；
- 自动决定研究对象应保留哪些 chain / residue。

如果用户尚未明确选择对象，1.3 的职责是帮助把描述解析到可执行的 chain / residue specification，并在存在语义冲突时请求确认，而不是替用户做研究对象选择。

## 10. 与现有 1.3 文件的关系

当前：

```text
02_operations/chain_and_component_selection/
02_validators/chain_and_component_selection_validator/
```

中的已有实现和 2026-07-31 验收结果只能作为历史参考。

现有实现包含：

- complete component selection；
- Legacy subagent task/result；
- Manager artifact registration；
- Workstream / runtime closure 相关接口；
- 旧 selection spec 语义。

这些内容不能直接视为本次重设计已经确认的最终方案。

后续修改 1.3 正式 Skill 时，应从本草案和 Lightweight Runtime v2 规格重新确定接口，而不是机械迁移旧 Runtime 结构。

## 11. Lightweight Runtime 接口待定项

以下内容尚未冻结，需要后续逐项设计：

```text
object requirements
reuse conditions
selection_spec.yaml 最终 schema
official results
Operation 与 Validator 的精确职责边界
单结构与多结构输出文件命名
selection mapping / provenance 是否以及如何保留
共价跨 selection boundary 的处理规则
1.3 Validator 的独立校验项目
project_result_index.md 中多结构结果的登记格式
```

因此当前 1.3 状态必须保持：

```text
redesign draft recorded
implementation not complete
lightweight migration pending
revalidation required
```

## 12. 后续继续设计时的起点

下一次继续 1.3 时，不应从旧 `SKILL.md` 的 Legacy runtime 接口开始修改。

建议按以下顺序继续：

```text
1. 冻结用户自然语言 → chain/residue retain specification 的解析规则
2. 冻结 selection_spec.yaml schema
3. 冻结单结构 / 多结构输出规则
4. 冻结 Operation 执行边界
5. 冻结 Validator 独立校验边界
6. 冻结 reuse conditions 与 official results
7. 再修改正式 Operation / Validator Skill 和脚本
8. 最后重新执行 1.2 → 1.3 回归与真实结构验收
```

# Target lineage rules

Status: CURRENT SHARED REFERENCE

本文件定义 MD Workflow 中跨 Skill 追踪 `target` 前后演化、分支与合流的共享规则。

它只拥有 target lineage 的通用记录机制，不定义任何 Stage / Step / capability 的科学处理方法，也不把不同 Skill 中编号相同的 `target_id` 解释成同一对象。

## 1. 核心原则

`target` 是当前 Stage / Step / capability 内的局部处理对象。

因此：

- 每个实际使用 `target` 的 Skill / 当前工作项都为自己的 local target 分配当前作用域内的 `target_id`；
- `target_id` 只在创建它的当前 Skill / 当前工作项内解释；
- `1.4 target_001` 与 `1.3 target_001`、`1.5 target_001` 即使编号相同，也不因此表示同一个 execution object；
- target 的跨环节继承、分支和合流通过 **target record 路径** 明确记录，不通过编号相同推断。

## 2. `target_record`

每个 local target 都必须有一份独立 target record。

默认路径：

```text
<current_task_specific_work_directory>/targets/<target_id>.yaml
```

例如：

```text
.../03_chain_and_residue_selection/T001/targets/target_001.yaml
.../04_altloc_occupancy_resolution/T002/targets/target_001.yaml
.../05_completeness_check/T003/targets/target_002.yaml
```

**target record 的完整绝对路径**是跨 Skill 引用当前 local target 的正式接口。

最低字段：

```yaml
target_id: target_001
source_target_records:
  - /absolute/path/to/upstream/targets/target_002.yaml
description: "当前 target 的简明说明"
```

规则：

- `target_id`：当前 Skill / 当前工作项内的 local target 编号；
- `source_target_records`：直接用于形成当前 target 的上游 target record 完整绝对路径列表；
- `description`：用户可读说明，用于帮助恢复上下文，不作为跨环节 identity 判据。

当前 target 没有上游 target 时：

```yaml
source_target_records: []
```

Skill-specific target record 可以增加当前职责确有必要的字段，但不得重新定义上述字段语义。

## 3. 分支与合流

Target lineage 是有向无环图，不要求是一条单链。

### 一对一演化

一个当前 target 直接由一个上游 target 形成：

```text
upstream target record A
→ current target record B
```

则 B：

```yaml
source_target_records:
  - /absolute/path/to/A.yaml
```

即使是一对一演化，B 仍是当前 Skill 自己的新 local target；不得沿用 A 的 `target_id` 作为跨环节 identity。

### 分支

同一个上游 target 因不同 scientific / technical strategy、不同用户决定或需要保留的 alternative treatment 形成多个后续 target：

```text
A
├─→ B
└─→ C
```

B 与 C 分别拥有自己的 target record，并都写：

```yaml
source_target_records:
  - /absolute/path/to/A.yaml
```

B / C 的差异由当前 Skill 的正式结果、Task Sheet 决定和各自 `description` 记录；不在 shared target record 中复制完整科学结果。

### 合流

当前 target 需要共同消费多个上游 target 才能形成，例如多个独立拓扑处理对象在整合环节重新汇合：

```text
A ─┐
B ─┼─→ D
C ─┘
```

D：

```yaml
source_target_records:
  - /absolute/path/to/A.yaml
  - /absolute/path/to/B.yaml
  - /absolute/path/to/C.yaml
```

列表只记录真实参与当前 target 形成的 source targets；普通 reference、validation evidence 或仅供查阅的结果不因为被读取就自动成为 `source_target_records`。

## 4. Source-target 判定

`source_target_records` 表示**当前 target 是从哪些上游 target 形成的**，不是“当前 Skill 读取过哪些文件”的清单。

因此：

- 结构、参数化对象、整合对象或其它 execution object 的实际来源 target 应记录；
- 一个只提供检查事实、参考值或辅助证据但并未形成当前 target 的对象，不自动记录为 source target；
- 是否属于 source target 由当前 Skill 的实际对象关系决定，不按编号邻接机械推断；
- 更早编号 Step 不在当前 Task Sheet，不影响它的 target record 作为 source target；只要当前工作能够明确定位即可。

## 5. Target record 与正式结果

Target record 只负责 target identity / lineage，不替代当前 Skill 的正式科学结果。

当某个正式结果描述一个或多个 local target 时：

- 对每个 target，在该结果自己的 `references` / dependency 区域记录对应 `target_record` 的完整绝对路径；
- 如果一个聚合结果包含多个 targets，每个 target entry 分别记录自己的 `target_record`；
- 不用裸 `target_id` 代替 target record 路径；
- 正式结果中的 local `target_id` 可以保留用于当前结果内部阅读，但跨 Skill 追踪必须通过 `target_record`。

例如：

```yaml
targets:
  - target_id: target_001
    references:
      target_record: /absolute/path/to/current/targets/target_001.yaml
```

下游若需要追溯更早 lineage，读取该 target record 的 `source_target_records`，再按需逐级继续；不要求所有结果直接保存 1.3 或其它固定根节点路径。

## 6. Target record 与 atom map

采用共享 atom map 的结构处理环节，map 文件级记录当前 map 所属 local target 的 target record：

```yaml
target_record: /absolute/path/to/current/targets/target_001.yaml
```

规则：

- 当前 Step 生成新的 local target 时，输出 map 使用**当前 Step 的 target record**，不沿用上游 map 的 target record；
- `input_map` 继续记录实际用于 copy-and-update 的上一份 map，因此 map chain 与 target lineage 是互补关系；
- 当前 target 的 `source_target_records` 应能够解释它与输入 map 所属 target 的 lineage 关系；中间存在不生成 map 的 target-based Step 时，不要求当前 target 的直接 source target 与 `input_map.target_record` 完全相同；
- 不在 map 中维护跨环节 `target_id`。

## 7. 何时建立 target record

建立 target record 的前提是：当前 execution scope 已经按 `references/task_execution_rules.md` 唯一明确，并且当前 Skill / 当前工作项已经实例化一个**实际要执行的 local target**。

因此：

- execution-scope confirmation 阶段可以只读检查候选对象，但不得为多个可能范围预建候选 / 占位 target records；
- 用户范围尚未明确时，不通过“先创建 target 再让用户选”物化 Agent 自己的范围假设；
- 范围明确后，只要当前 Skill / 当前工作项把实际对象表示为 `target`，就为每个 actual local target 建立 current target record。

这与是否发生“科学分支”是两件事：

- 一对一推进仍建立当前 Step 自己的 target record；
- 一个 source target 产生多个 actual current targets 时自然形成分支；
- 多个 source targets 汇成一个 actual current target 时自然形成合流。

以下情况本身不构成 target lineage：

- 仅建立新的 Task Sheet；
- 仅复制文件或改变目录；
- 仅因为 `target_id` 编号发生变化；
- 仍处于用户执行范围确认阶段的候选对象；
- Stage 4 formal run unit、Stage 5 analysis plan item 等已经由其 owner 定义了其它正式 execution identity，且对应 Skill 并未使用 `target` 作为执行对象。

## 8. Target lineage validation

正式使用当前 target record 前至少确认：

- 当前 execution scope 已经明确，target record 对应 actual local target 而不是候选范围；
- `target_id` 在当前 Skill / 当前工作项 sibling targets 中唯一；
- `source_target_records` 中每个路径均为实际可定位的 target record；
- 当前 target 与每个 source target 的关系符合当前 Skill / Task Sheet 的实际对象演化；
- 不通过相同 `target_id` 推断上下游关系；
- 不创建 target lineage cycle；
- 当前正式结果记录的 `target_record` 与其实际处理对象一致；
- 当前输出 atom map 如适用，其 `target_record` 与当前 formal result 指向同一 local target record。

## 9. Project result index

Target record 是 lineage support record，不因为创建就自动单独登记到 `project_result_index.md`。

正式结果 owner 已登记的 report / result record 应能够通过自己的 `references.target_record` 定位 target record；需要单独登记 target record 的特殊情况由对应 Skill 明确声明，不由本 shared rule 默认增加。
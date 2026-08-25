# Workflow 1 Stage 1.2 topology-linked check freeze

Status: FROZEN AUTHORING RECORD — SYNCHRONIZED TO CURRENT 1.2

本文件冻结结构准备 1.2 中已经确定的 `topology-linked` 检查与正式记录规则。当前规则已同步到：

`../../01_structure_preparation/1.2_component_and_residue_classification/`

`topology-linked` 的跨 Skill 正式术语定义读取：

`../../references/canonical_terminology.md`

本 freeze 不重新定义 1.2 已有的 residue 分类、残基缺失检查、多构象检查、重原子检查、`component_id` / `residue_id` 身份体系或其它已确定内容。

## 1. 检查对象与关系类型

1.2 对当前 model 中可能 `topology-linked` 的原子对进行检查。

当前正式关系类型保持：

```text
COVALENT_CONNECTION
METAL_COORDINATION
```

“可能 `topology-linked` 的原子对”由以下三类判据中的任意一类触发：

1. 结构文件中的显式连接；
2. 按项目实际可能连接定义执行的几何检查；
3. 用户或项目提供的可能连接信息。

不对当前 model 中任意原子进行无边界两两检查。

## 2. 三类判据全部记录

只要上述三类判据中的任意一项使某原子对进入 `topology-linked` 检查，就建立该原子对的正式检查记录。

一旦建立记录，三类判据必须全部出现并如实记录。每类判据均使用：

```text
NOT_PRESENT
NOT_SATISFIED
SATISFIED
```

同一类判据存在多个实际相关依据时全部记录。该类判据的总体状态由执行 Agent 基于全部实际相关依据判断；不为多个依据的组合方式增加固定状态转换规则。

正式结果统一保存于：

```text
topology_linked_checks[]
```

不再使用 `confirmed_relations / rejected_candidates` 外层拆分。

## 3. 结构文件中的显式连接

1.2 读取当前结构文件中明确记录的连接信息，并映射到当前检查的原子对。

Skill 规定需要读取和记录的科学信息，不规定 PDB、mmCIF 或其它结构格式的逐字段 parser 实现。

正式字段：

```yaml
explicit_connection:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
  evidence: []
```

只要存在相关显式连接信息，无论为 `NOT_SATISFIED` 还是 `SATISFIED`，都记录全部实际相关依据：

```yaml
- source: STRUCTURE_1
  lines: <具体行号或行号范围>
```

结构文件完整路径可放在文件级 `references`：

```yaml
references:
  STRUCTURE_1: /absolute/path/to/input_structure.pdb
```

`NOT_PRESENT` 时不保留来源依据。

## 4. 可能连接定义与几何检查

项目实际可能共价连接定义按：

`schemas/possible_connections.schema.yaml`

解释；项目实际可能金属配位定义按：

`schemas/possible_coordination.schema.yaml`

解释。

两个 schema 只定义实际项目 YAML 的数据结构，本身不是当前任务的可能连接定义文件。

正式字段：

```yaml
geometry_check:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
  evidence: []
```

只要存在对应定义，无论几何是否满足，都记录实际 YAML 和具体定义项：

```yaml
- definition: POSSIBLE_CONNECTIONS_1
  item: <具体定义项>
```

或：

```yaml
- definition: POSSIBLE_COORDINATION_1
  item: <具体定义项>
```

完整路径可放在文件级 `references`：

```yaml
references:
  POSSIBLE_CONNECTIONS_1: /absolute/path/to/possible_connections.yaml
  POSSIBLE_COORDINATION_1: /absolute/path/to/possible_coordination.yaml
```

`NOT_PRESENT` 时不保留定义依据。多个实际相关定义项全部记录。

几何满足本身不能自动等同于共价连接或金属配位已经确认。

## 5. 用户或项目提供的可能连接信息

第三类判据正式字段：

```yaml
provided_connection_info:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
  evidence: []
```

项目文件来源：

```yaml
- reference: PROJECT_INFO_1
  item: <具体条目>
```

其中完整路径可放在：

```yaml
references:
  PROJECT_INFO_1: /absolute/path/to/project_info
```

不增加重复的 `source: PROJECT`。

用户直接描述：

```yaml
- description: <用户实际描述>
```

`NOT_SATISFIED` 与 `SATISFIED` 都保留全部实际相关来源；`NOT_PRESENT` 时不保留来源依据。项目文件与用户描述同时存在时全部记录。

用户只是提出“可能存在连接 / 配位，需要检查”时属于本类判据，不属于人工决策。

## 6. 单条统一检查记录

每条正式记录对应一个可能 `topology-linked` 的原子对，并至少包含：

```text
relation_id
relation_type
关系两端
explicit_connection
geometry_check
provided_connection_info
judgment
topology_effect_applied
```

共价连接使用：

```text
atom_1
atom_2
```

金属配位使用：

```text
metal
donor
```

各端点使用当前 1.2 正式身份体系：

```text
component_id
residue_id
atom_name
```

`relation_id` 使用既有 `relation_001`、`relation_002`……形式，在当前 model 内唯一。

## 7. 综合判断与 topology effect

执行 Agent 基于三类判据的完整记录综合形成：

```text
judgment: CONFIRMED | REJECTED
```

并独立形成：

```text
topology_effect_applied: true | false
```

Skill 不为单一判据缺失、多个依据并存或其它运行时组合预设额外 decision tree、fallback 或中间状态。

最低固定语义：

```text
judgment = REJECTED
→ topology_effect_applied = false
```

已确认共价连接产生 topology effect。金属配位是否产生 topology effect 与“配位是否成立”分开判断，由执行 Agent 根据当前实际信息形成最终结果。

只有 `judgment: CONFIRMED` 且 `topology_effect_applied: true` 的记录用于更新相关 residue 最终 `topology_class` 和 component membership。

## 8. 人工决策

只有现有证据不能可靠闭合、且不同判断会改变正式结果或后续处理时才进入人工确认。

实际发生的人工确认 / 否决继续记录在：

`relation_decisions.yaml`

人工决策与正式检查记录仅通过 `relation_id` 对应，不重复记录端点、`relation_type` 或其它定位字段。

当前 `relation_decisions.yaml` 数据结构：

```yaml
schema_version: "3.0"
model_id: "1"
decisions:
  - relation_id: relation_001
    decision: CONFIRMED
```

## 9. Current implementation

本 freeze 已同步到 current 1.2：

- main `SKILL.md`：topology-linked 检查主线、三类判据入口、人工确认边界；
- `references/classification_rules.md`：详细科学判断规则；
- `references/result_recording_rules.md`：完整正式结果数据结构与字段语义；
- `schemas/classification_result.schema.yaml`：`schema_version: "4.0"`，统一 `topology_linked_checks[]`；
- `schemas/possible_connections.schema.yaml` / `schemas/possible_coordination.schema.yaml`：继续约束实际项目可能连接定义文件；
- `schemas/relation_decisions.schema.yaml`：`schema_version: "3.0"`，人工决策只通过 `relation_id` 对应。

该同步不授权当前 1.2 authoring 工作修改其它 Skill 的消费者实现；跨 Skill 消费者需由其 owner 按新的 1.2 正式接口迁移。

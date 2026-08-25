# Workflow 1 Stage 1.2 topology-linked check freeze

Status: FROZEN AUTHORING RECORD

本文件只冻结结构准备 1.2 中已经确定的 `topology-linked` 检查与正式记录规则，用于后续同步 current 1.2 `SKILL.md`、references 和 schema。

`topology-linked` 的跨 Skill 正式术语定义读取：

`../../references/canonical_terminology.md`

本 freeze 不重新定义 1.2 已有的 residue 分类、残基缺失检查、多构象检查、重原子检查、`component_id` / `residue_id` 身份体系或其它已确定内容。

当前 active 1.2 仍位于：

`../../01_structure_preparation/1.2_component_and_residue_classification/SKILL.md`

本 freeze 记录的是后续需要同步到该 current implementation 的已确定规则；在同步完成并 validation 之前，不把当前 active 文件中仍存在的旧 relation 结果结构当作本 freeze 的替代规则。

## 1. 检查对象与关系类型

1.2 对当前 model 中可能 `topology-linked` 的原子对进行检查。

当前正式关系类型为：

```text
COVALENT_CONNECTION
METAL_COORDINATION
```

“可能 `topology-linked` 的原子对”由以下三类判据中的任意一类触发：

1. 结构文件中的显式连接；
2. 按项目提供的可能连接定义执行的几何检查；
3. 用户或项目提供的可能连接信息。

不对当前 model 中任意原子进行无边界两两检查。

## 2. 三类判据全部记录

只要上述三类判据中的任意一项使某原子对进入 `topology-linked` 检查，就建立该原子对的正式检查记录。

一旦建立记录，三类判据必须全部出现并如实记录。每类判据都区分：

```text
没有对应信息 / 定义
有对应信息 / 定义，但不满足当前判据
有对应信息 / 定义，且满足当前判据
```

正式结果中的状态取值采用：

```text
NOT_PRESENT
NOT_SATISFIED
SATISFIED
```

其中具体字段语义按以下三类判据分别解释；不得因为某一类没有信息而省略该判据字段。

## 3. 结构文件中的显式连接

1.2 读取当前结构文件中明确记录的连接信息，并将其映射到当前 model 中实际检查的原子对。

Skill 需要规定读取和记录的科学信息，不规定 PDB、mmCIF 或其它结构格式的逐字段 parser 实现。

正式记录字段采用：

```yaml
explicit_connection:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
```

当结构文件中的显式连接满足当前判据时，必须记录：

```yaml
explicit_connection:
  status: SATISFIED
  source: STRUCTURE_1
  lines: <原始结构文件中的具体行号或行号范围>
```

结构文件完整路径可统一放在 `classification_result.yaml` 文件级 `references` 中，例如：

```yaml
references:
  STRUCTURE_1: /absolute/path/to/input_structure.pdb
```

具体检查记录使用 reference 变量名，不重复写完整路径。

## 4. 可能连接定义与几何检查

项目实际使用的可能共价连接定义按：

`schemas/possible_connections.schema.yaml`

解释；项目实际使用的可能金属配位定义按：

`schemas/possible_coordination.schema.yaml`

解释。

上述两个 schema 定义实际项目 YAML 的数据结构；它们本身不是当前任务的可能连接定义文件。

对项目 YAML 中定义的可能连接或配位逐项执行相应几何检查。仅有几何满足不能自动等同于共价连接或金属配位已经确认；几何检查是关系判断的一类判据。

正式记录字段采用：

```yaml
geometry_check:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
```

当对应定义存在且实际几何满足该定义时，必须记录所依据的项目 YAML 及其中具体定义项：

```yaml
geometry_check:
  status: SATISFIED
  definition: POSSIBLE_CONNECTIONS_1
  item: <该 YAML 中的具体定义项>
```

或：

```yaml
geometry_check:
  status: SATISFIED
  definition: POSSIBLE_COORDINATION_1
  item: <该 YAML 中的具体定义项>
```

对应项目 YAML 的完整路径可统一放在文件级 `references` 中，例如：

```yaml
references:
  POSSIBLE_CONNECTIONS_1: /absolute/path/to/possible_connections.yaml
  POSSIBLE_COORDINATION_1: /absolute/path/to/possible_coordination.yaml
```

具体检查记录只引用变量名和定义项，不重复复制完整文件路径或定义内容。

## 5. 用户或项目提供的可能连接信息

用户或项目仅提出“某原子对可能存在连接 / 配位，需要检查”时，该信息属于可能连接判据，不属于人工决策。

正式记录字段采用：

```yaml
user_description:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
```

当用户描述满足当前检查对象时，记录实际用户描述：

```yaml
user_description:
  status: SATISFIED
  description: <用户关于该可能连接或配位的实际描述>
```

用户只是提出待检查可能性时，不写入 `relation_decisions.yaml`。

只有现有判据不能可靠闭合、且不同判断会改变正式关系、`topology_class` 或后续拓扑处理时，才进入人工确认。实际发生的用户确认 / 否决继续由 1.2 的 `relation_decisions.yaml` 记录。

## 6. 单条检查记录

每条正式记录对应一个可能 `topology-linked` 的原子对，并至少包含：

```text
relation_id
relation_type
atom_1
atom_2
explicit_connection
geometry_check
user_description
judgment
topology_effect_applied
```

两个原子使用当前 1.2 正式身份体系定位：

```yaml
atom_1:
  component_id: <已有 component_id>
  residue_id: <已有 residue_id>
  atom_name: <atom name>

atom_2:
  component_id: <已有 component_id>
  residue_id: <已有 residue_id>
  atom_name: <atom name>
```

`relation_id`、`component_id` 与 `residue_id` 沿用 1.2 已有身份 / 编号体系；本 freeze 不重新定义其生成规则。

## 7. 最终判断与 topology effect

正式记录中的关系判断采用：

```text
judgment: CONFIRMED | REJECTED
```

三类判据负责记录事实依据；`judgment` 负责表达当前共价连接或金属配位最终是否成立。不得用单一“智能体判断”替代三类判据的实际记录。

是否产生后续 topology effect 单独记录：

```yaml
topology_effect_applied: true | false
```

两项判断语义不同：

```text
judgment
→ 当前共价连接 / 金属配位是否成立

topology_effect_applied
→ 当前检查结果是否实际产生 topology-linked 作用
```

已否定的关系：

```text
judgment = REJECTED
→ topology_effect_applied = false
```

已确认共价连接产生 topology effect。

已确认金属配位是否产生 topology effect 与“该配位是否存在”分开判断；按实际 `possible_coordination` 定义中的 `topology_effect.promote_nonstandard_to_linked` 或实际人工决策确定。

## 8. 正式结果组织

不再使用下列旧式外层结果拆分作为 current target design：

```yaml
confirmed_relations:
  covalent_connections: []
  metal_coordination: []

rejected_candidates:
  covalent_connections: []
  metal_coordination: []
```

每个可能 `topology-linked` 原子对使用统一检查记录；是否确认由记录自身的 `judgment` 表达，是否产生拓扑作用由 `topology_effect_applied` 表达，不再通过外层 confirmed / rejected collection 重复编码同一判断。

## 9. 后续实现要求

后续同步 current 1.2 时，只将本 freeze 中已经确定的规则转写到对应 owner：

- main `SKILL.md`：保留检查主线、三类判据入口、人工确认边界和 reference/schema 入口；
- `references/classification_rules.md`：拥有详细科学判断规则；
- `references/result_recording_rules.md`：拥有完整正式结果数据结构与字段语义；
- `schemas/classification_result.schema.yaml`：只负责机器字段约束；
- `schemas/possible_connections.schema.yaml` / `schemas/possible_coordination.schema.yaml`：继续约束实际项目可能连接定义文件；
- `relation_decisions.yaml` 及其 schema：继续只记录实际发生的人工关系决策。

同步时不得重新恢复已经舍弃的 `confirmed_relations` / `rejected_candidates` 外层结果结构，也不得把三类判据重新压缩为单值 evidence。

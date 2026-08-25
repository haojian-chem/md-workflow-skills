# 1.2 正式结果记录规则

本文件拥有结构准备 1.2 正式结果的数据结构、字段语义、报告格式和登记要求。科学判断规则见 `classification_rules.md`；机器字段约束见 `../schemas/`。

## 1. 正式结果集合与 model 目录

对每个实际执行 1.2 的 model，建立独立子目录：

```text
<task_id>/
└── <model_directory>/
    ├── classification_result.yaml
    ├── classification_report.md
    └── relation_decisions.yaml   # 仅实际发生关系人工决策时存在
```

每个文件只描述一个 model。model 信息在文件级记录一次，不复制到每个 component / residue。

正式结果职责：

- `classification_result.yaml`：保存当前 model 的 component / residue 层级、component `chain_index`、两类分类、三级 residue 检查、topology-linked 检查、reference 变量和最终判断；
- `classification_report.md`：按检查顺序生成的人类可读审阅报告；
- `relation_decisions.yaml`：只在共价连接或金属配位实际发生人工确认或否决时生成，保存这些人工决策。

1.2 不生成 `reference_manifest.yaml`。

## 2. `classification_result.yaml` 数据结构

当前正式 schema 版本为 `4.0`。示意结构：

```yaml
schema_version: "4.0"
result_status: COMPLETE

model:
  model_id: "1"
  source_structure: /absolute/path/to/input.pdb
  source_format: PDB

classification_mode: FORCE_FIELD_ANALYSIS

references:
  RTP_1: /absolute/path/to/aminoacids.rtp
  CCD_PATH_1: /absolute/path/to/ccd
  STRUCTURE_1: /absolute/path/to/input.pdb
  POSSIBLE_CONNECTIONS_1: /absolute/path/to/possible_connections.yaml
  PROJECT_INFO_1: /absolute/path/to/project_connection_notes.yaml

components:
  - component_id: component_001
    chain_index: 1
    residues:
      - residue_id: residue_001
        source_chain_id: A
        current_chain_id: A
        source_resid: "42"
        current_resid: "42"
        source_residue_name: CYS
        current_residue_name: CYS

        polymer_class:
          value: POLYMER
          evidence: 智能体判断

        topology_class:
          value: STANDARD_RESIDUE
          evidence: RTP_1

        missing_residue_check:
          status: PASS
          evidence: 智能体判断

        conformation_check:
          status: PASS
          evidence: 智能体判断

        heavy_atom_check:
          status: PASS
          evidence: RTP_1
          missing_heavy_atoms: []
          extra_heavy_atoms: []
          duplicate_atom_names: []
          atom_name_mismatches: []
          element_mismatches: []

      - residue_id: residue_002
        source_chain_id: A
        current_chain_id: A
        source_resid: "501"
        current_resid: "501"
        source_residue_name: LIG
        current_residue_name: LIG

        polymer_class:
          value: NONPOLYMER
          evidence: 智能体判断

        topology_class:
          value: TOPOLOGY_LINKED_NONSTANDARD
          evidence: 智能体判断

        missing_residue_check:
          status: PASS
          evidence: 智能体判断

        conformation_check:
          status: PASS
          evidence: 智能体判断

        heavy_atom_check:
          status: PASS
          evidence: "{CCD_PATH_1}/LIG.cif"
          missing_heavy_atoms: []
          extra_heavy_atoms: []
          duplicate_atom_names: []
          atom_name_mismatches: []
          element_mismatches: []

topology_linked_checks:
  - relation_id: relation_001
    relation_type: COVALENT_CONNECTION

    atom_1:
      component_id: component_001
      residue_id: residue_001
      atom_name: SG

    atom_2:
      component_id: component_001
      residue_id: residue_002
      atom_name: C1

    explicit_connection:
      status: SATISFIED
      evidence:
        - source: STRUCTURE_1
          lines: "120"

    geometry_check:
      status: NOT_SATISFIED
      evidence:
        - definition: POSSIBLE_CONNECTIONS_1
          item: "possible_connections[0]"

    provided_connection_info:
      status: SATISFIED
      evidence:
        - reference: PROJECT_INFO_1
          item: "connections[1]"
        - description: "CYS SG 与 LIG C1 可能成键"

    judgment: CONFIRMED
    topology_effect_applied: true

unresolved_items: []
```

该结构是 1.2 正式数据模型。不要同时另建平行的 `chain_groups[]`、`residue_records[]`、`missing_residue_ids[]`、`source_identity/current_identity` 或按确认 / 拒绝再次拆分的关系集合重复表达同一事实。

`topology_linked_checks` 是共价连接和金属配位检查的统一正式记录集合。每条记录自身通过：

```text
relation_type
judgment
topology_effect_applied
```

表达关系类型、最终是否成立以及是否产生 topology effect。

不再使用：

```yaml
confirmed_relations:
  ...
rejected_candidates:
  ...
```

作为 current 结果结构。

## 3. 文件级字段

`schema_version` 当前固定为 `4.0`。

`result_status: COMPLETE` 表示 1.2 要求的分类、三级 residue 检查、topology-linked 检查以及会影响最终 component / topology 归属的判断已经可靠完成并通过 validation；不表示没有发现结构问题。

`model`：

```yaml
model:
  model_id: "1"
  source_structure: /absolute/path/to/input.pdb
  source_format: PDB
```

- `model_id`：当前文件描述的实际 model；
- `source_structure`：1.1 已确定的结构文件完整路径；
- `source_format`：当前源结构格式。

model 信息只在文件级出现一次；residue 内不重复 model 字段。

`classification_mode` 使用 `REGISTRY` 或 `FORCE_FIELD_ANALYSIS`，科学含义见 `classification_rules.md`。

## 4. `references`

`references` 只定义本次正式记录实际引用的文件路径变量。当前允许：

```text
RTP_n
CCD_PATH_n
STRUCTURE_n
POSSIBLE_CONNECTIONS_n
POSSIBLE_COORDINATION_n
PROJECT_INFO_n
```

示例：

```yaml
references:
  RTP_1: /absolute/path/to/aminoacids.rtp
  CCD_PATH_1: /absolute/path/to/ccd
  STRUCTURE_1: /absolute/path/to/input.pdb
  POSSIBLE_CONNECTIONS_1: /absolute/path/to/possible_connections.yaml
  POSSIBLE_COORDINATION_1: /absolute/path/to/possible_coordination.yaml
  PROJECT_INFO_1: /absolute/path/to/project_connection_notes.yaml
```

规则：

- `RTP_n` 直接指向实际 RTP 文件；
- `CCD_PATH_n` 指向实际 CCD 文件目录；具体 CCD 文件仍写成 `{CCD_PATH_n}/XXX.cif`；
- `STRUCTURE_n` 指向实际结构文件；
- `POSSIBLE_CONNECTIONS_n` 指向按 `possible_connections.schema.yaml` 组织的实际定义文件；
- `POSSIBLE_COORDINATION_n` 指向按 `possible_coordination.schema.yaml` 组织的实际定义文件；
- `PROJECT_INFO_n` 指向第三类判据所引用的实际项目文件；
- 只为本次正式记录实际引用的文件建立变量；
- 不额外建立 `FF_PATH_n`；
- 不使用 `ref_001`、`reference_entry`；
- 本环节不要求统一计算或记录 SHA-256。

## 5. `components`、`chain_index` 与身份层级

正式层级：

```text
model
└── component_id + chain_index
    └── residue_id
```

### `component_id`

- 标识当前 model 中一个最终 component；
- 在当前 model 的 `classification_result.yaml` 中唯一；
- 是稳定、不透明的 component identity；
- 不表示 CCD component ID、PDB chain ID、`chain_index` 或 residue name；
- component membership 在全部已确认且产生 topology effect 的检查结果应用后确定；
- 下游直接消费正式值，不自行重构。

### `chain_index`

- 位于 component 一级；
- 在当前 model 中唯一；
- 是 1.2 对该 component 赋予的逻辑 chain/group 编号，用于后续结构 materialization 与 mapping；
- 不属于稳定 identity，不能替代 `component_id`；
- 不等同于 `source_chain_id`、`current_chain_id` 或 PDB chain ID。

### `residue_id`

- 标识所属 component 中的一个 residue；
- 在所属 `component_id` 内唯一；
- 不要求跨不同 component 单独唯一；
- 下游定位 residue 使用 `component_id + residue_id`；
- 不是 source/current resid，也不是 residue name。

每个 component 的 `residues` 数组顺序就是 1.2 为该 component 建立的正式 residue 顺序。已确认缺失 residue 直接位于其应有位置。

## 6. Residue 定位与名称字段

每个 residue 固定保存：

```text
source_chain_id
current_chain_id
source_resid
current_resid
source_residue_name
current_residue_name
```

- `source_chain_id`：当前 1.2 输入结构中的原始 chain ID；
- `current_chain_id`：生成本次 1.2 正式结果时当前结构中用于定位该 residue 的 chain ID；
- `source_resid`：源结构中用于定位该 residue 的实际 resid 表达；
- `current_resid`：生成本次 1.2 正式结果时当前结构中的 resid；已确认缺失 residue 为 `null`；
- `source_residue_name`：源结构或可追溯序列注释中的原始 residue name；
- `current_residue_name`：生成本次 1.2 正式结果时当前结构实际使用的 residue name；缺失 residue 为 `null`。

1.2 不修改结构，所以普通已存在 residue 的 source/current 值通常相同。后续步骤改变 chain、resid 或 residue name 时，由后续步骤自己的 mapping / result 记录，不回写 1.2 正式结果。

## 7. 两类分类字段

每个 residue 保存：

```yaml
polymer_class:
  value: <value>
  evidence: <evidence>

topology_class:
  value: <value>
  evidence: <evidence>
```

`polymer_class.value`：`POLYMER | BRANCHED | NONPOLYMER | WATER`。

`topology_class.value`：`STANDARD_RESIDUE | TOPOLOGY_LINKED_NONSTANDARD | INDEPENDENT_NONSTANDARD | SOLVENT_COMPONENT | ION_COMPONENT`。

`topology_class` 必须是 topology-linked 检查完成、所有 `judgment: CONFIRMED` 且 `topology_effect_applied: true` 的记录已经应用后的最终值。正式结果中不额外保存 provisional `topology_class`。

如果检查没有改变该 residue 的 topology 归属，保留初始分类依据对应的 `evidence`。如果检查使一个非标准 / solvent / ion residue 最终成为 `TOPOLOGY_LINKED_NONSTANDARD`：

- 由 Agent 完成闭合 → `evidence: 智能体判断`；
- 由用户决定 → `evidence: 人工决策`。

具体 topology-linked 检查记录不在 `topology_class` 内重复。

## 8. Residue 三级检查

固定顺序：

```text
missing_residue_check
↓ PASS
conformation_check
↓ PASS
heavy_atom_check
```

前一项为 `ISSUE` 时，后续项不执行并记录 `SKIPPED`。

### 8.1 `missing_residue_check`

```yaml
missing_residue_check:
  status: PASS | ISSUE
  evidence: <evidence>
```

- `PASS`：该预期 residue 在当前 model 中存在；
- `ISSUE`：有可靠依据确认该 residue 应存在，但当前 model 中没有坐标实例。

### 8.2 `conformation_check`

```yaml
conformation_check:
  status: PASS | ISSUE | SKIPPED
  evidence: <evidence-or-null>
```

本项只记录“是否存在多构象问题”。不记录构象选择、构象整合或 1.4 的处理决定。

### 8.3 `heavy_atom_check`

只有前两项均为 `PASS` 时才执行。

```yaml
heavy_atom_check:
  status: PASS | ISSUE | SKIPPED | NOT_APPLICABLE
  evidence: RTP_1 | "{CCD_PATH_1}/HEM.cif" | 智能体判断 | 人工决策 | null
  missing_heavy_atoms: []
  extra_heavy_atoms: []
  duplicate_atom_names: []
  atom_name_mismatches: []
  element_mismatches: []
```

- `PASS`：比较完成，所有问题明细为空；
- `ISSUE`：比较完成，至少一类问题明细非空；
- `SKIPPED`：前一级检查已经发现问题，`evidence: null` 且所有问题明细为空；
- `NOT_APPLICABLE`：前两级通过，但当前 residue 按科学规则不需要重原子比较。

`atom_name_mismatches` 项：

```yaml
- current_atom_name: O1
  reference_atom_name: O1A
```

`element_mismatches` 项：

```yaml
- atom_name: X1
  current_element: X
  reference_element: Y
```

## 9. Residue 检查 `evidence`

允许：

```text
RTP_n
{CCD_PATH_n}/XXX.cif
智能体判断
人工决策
```

- `RTP_n`：Agent 直接以该 RTP 文件中的实际残基定义判断；
- `{CCD_PATH_n}/XXX.cif`：Agent 直接以该 CCD component file 判断；
- `智能体判断`：Agent 综合当前结构、结构注释、项目语义等信息判断；
- `人工决策`：最终结论由用户确认。

文件型 evidence 必须能通过同一文件级 `references` 解析到实际路径。

## 10. `topology_linked_checks`

每个可能 `topology-linked` 原子对建立一条统一检查记录。三类判据任意一项触发检查后，三类判据字段都必须存在。

每类判据统一使用：

```text
NOT_PRESENT
NOT_SATISFIED
SATISFIED
```

并使用 `evidence` 数组保存该类全部实际相关依据。

统一规则：

- `NOT_PRESENT`：对应 `evidence` 必须为空；
- `NOT_SATISFIED`：存在相关依据，`evidence` 至少一项；
- `SATISFIED`：存在相关依据，`evidence` 至少一项；
- 同一类判据存在多个实际相关依据时全部记录；
- `status` 是该类判据的总体状态，由执行 Agent 基于全部实际相关依据形成。

### 10.1 共价连接端点

```yaml
relation_type: COVALENT_CONNECTION
atom_1:
  component_id: component_001
  residue_id: residue_001
  atom_name: SG
atom_2:
  component_id: component_001
  residue_id: residue_002
  atom_name: C1
```

### 10.2 金属配位端点

```yaml
relation_type: METAL_COORDINATION
metal:
  component_id: component_001
  residue_id: residue_002
  atom_name: FE
donor:
  component_id: component_001
  residue_id: residue_003
  atom_name: NE2
```

金属配位使用 `metal / donor` 保留两端角色；不使用 `atom_1 / atom_2`。

### 10.3 `relation_id`

`relation_id` 使用 `relation_001`、`relation_002`……形式，在当前 model 内唯一。它是统一检查记录与 `relation_decisions.yaml` 之间的对应键。

## 11. 三类判据记录

### 11.1 `explicit_connection`

```yaml
explicit_connection:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
  evidence: []
```

当存在相关显式连接信息时，每项依据记录：

```yaml
- source: STRUCTURE_1
  lines: "120-121"
```

- `source` 必须解析到 `references` 中实际结构文件；
- `lines` 保存该显式连接在原始结构文件中的具体行号或行号范围；
- `NOT_SATISFIED` 和 `SATISFIED` 都保留实际相关依据；
- 同一原子对存在多处相关显式连接信息时全部记录。

Skill 不要求在正式结果中复制原始结构记录全文。

### 11.2 `geometry_check`

```yaml
geometry_check:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
  evidence: []
```

只要存在对应可能连接定义，无论几何最终是否满足，都记录实际定义来源：

```yaml
- definition: POSSIBLE_CONNECTIONS_1
  item: "possible_connections[0]"
```

或：

```yaml
- definition: POSSIBLE_COORDINATION_1
  item: "possible_coordination[2]"
```

- `definition` 指向 `references` 中实际项目 YAML；
- `item` 必须能够唯一定位该 YAML 中实际使用的定义项，可以使用稳定 label 或明确数组路径；
- 没有对应定义时 `status: NOT_PRESENT` 且 `evidence: []`；
- 多个定义项与当前检查实际相关时全部记录。

### 11.3 `provided_connection_info`

```yaml
provided_connection_info:
  status: NOT_PRESENT | NOT_SATISFIED | SATISFIED
  evidence: []
```

项目文件来源：

```yaml
- reference: PROJECT_INFO_1
  item: "connections[1]"
```

用户直接描述：

```yaml
- description: "Fe 与 HIS 87 NE2 可能存在配位"
```

规则：

- 项目文件来源只记录 `reference + item`，不增加重复的 `source: PROJECT`；
- 用户直接描述记录实际描述；
- `NOT_SATISFIED` 和 `SATISFIED` 都保留全部实际相关来源；
- `NOT_PRESENT` 时 `evidence: []`；
- 项目文件与用户描述同时存在时可以同时记录。

用户仅提供待检查的可能性不属于人工决策，不写入 `relation_decisions.yaml`。

## 12. `judgment` 与 `topology_effect_applied`

每条统一检查记录必须写：

```yaml
judgment: CONFIRMED | REJECTED
topology_effect_applied: true | false
```

两者语义不同：

- `judgment`：当前共价连接或金属配位最终是否成立；
- `topology_effect_applied`：该检查结果是否实际产生 topology-linked 作用。

执行 Agent 基于三类判据综合形成最终判断，不以单一“智能体判断”字段替代三类判据事实记录。

最低一致性要求：

- `judgment: REJECTED` → `topology_effect_applied: false`；
- 已确认共价连接产生 topology effect；
- 金属配位是否产生 topology effect 与“配位是否成立”分开判断，由执行 Agent根据当前实际信息形成结果。

## 13. topology-linked 检查与最终 `topology_class` 的一致性

正式结果写出前必须应用：

```text
topology_linked_checks
→ 只取 judgment: CONFIRMED
→ 再取 topology_effect_applied: true
→ 更新相关 residue 最终 topology_class
→ 更新最终 component membership
→ 再物化 component_id / chain_index / residue_id
```

最低一致性要求：

- `STANDARD_RESIDUE` 不因 topology-linked 检查改成非标准类别；
- 参与已确认且产生 topology effect 的非标准 / solvent / ion residue 最终必须为 `TOPOLOGY_LINKED_NONSTANDARD`；
- `topology_effect_applied: false` 的记录不得改变 residue `topology_class`；
- `judgment: REJECTED` 的记录不得改变正式分类或 component membership；
- topology-linked 检查结果与最终 component membership 必须一致。

JSON Schema 只能检查字段结构，不能跨数组证明这一科学一致性；该一致性属于 1.2 validation 的必要检查。

## 14. `relation_decisions.yaml`

仅当当前 model 实际发生用户对共价连接或金属配位的确认或否决时生成。

```yaml
schema_version: "3.0"
model_id: "1"
decisions:
  - relation_id: relation_001
    decision: CONFIRMED
```

规则：

- 每项人工决策只通过 `relation_id` 对应 `classification_result.yaml` 中已有统一检查记录；
- 不重复记录端点、`relation_type` 或其它定位信息；
- `decision` 使用 `CONFIRMED` 或 `REJECTED`；
- 没有实际人工关系决策时不生成空文件。

## 15. `unresolved_items`

只保留不会改变最终分类、component membership、三级 residue 检查结果、topology-linked `judgment` 或 `topology_effect_applied` 的非阻断信息：

```yaml
- subject: <可定位对象>
  detail: <尚缺什么信息或存在什么非阻断不确定性>
```

如果未解决事项会改变正式结果，当前 model 不能形成 `result_status: COMPLETE`。

## 16. `classification_report.md`

报告按固定顺序组织：

1. 当前 model 与检查对象；
2. component / residue 初始分类依据与最终分类结果；
3. 残基缺失检查；
4. 多构象检查；
5. 重原子组成与命名检查；
6. topology-linked 检查，其中分别呈现共价连接与金属配位记录及三类判据；
7. 基于 topology-linked 检查更新后的 `topology_class` 与 component membership；
8. 人工关系决策（若存在）；
9. 未解决事项；
10. 总结。

报告中的 residue 使用 `component_id + residue_id` 定位，并可同时显示当前 `chain_id + resid + residue_name` 方便人工阅读。机器可消费的正式事实仍以 `classification_result.yaml` 为准。

## 17. Project result registration

项目级结果索引只登记每个实际处理 model 的 `classification_result.yaml` 完整绝对路径，并说明该结果对应的 source structure / model。

`classification_report.md` 和 `relation_decisions.yaml` 不单独登记，由同一 model 目录中的正式结果继续定位。

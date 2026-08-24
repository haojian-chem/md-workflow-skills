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

- `classification_result.yaml`：保存当前 model 的 component / residue 层级、component `chain_index`、两类分类、三级 residue 检查、共价连接检查结果、金属配位检查结果、reference 变量和已闭合关系；
- `classification_report.md`：按检查顺序生成的人类可读审阅报告；
- `relation_decisions.yaml`：只在共价连接或金属配位关系实际发生人工确认或否决时生成，保存这些关系人工决策。

1.2 不生成 `reference_manifest.yaml`。

## 2. `classification_result.yaml` 数据结构

```yaml
schema_version: "3.0"
result_status: COMPLETE

model:
  model_id: "1"
  source_structure: /absolute/path/to/input.pdb
  source_format: PDB

classification_mode: FORCE_FIELD_ANALYSIS

references:
  RTP_1: /absolute/path/to/aminoacids.rtp
  RTP_2: /absolute/path/to/dna.rtp
  CCD_PATH_1: /absolute/path/to/ccd

components:
  - component_id: component_001
    chain_index: 1
    residues:
      - residue_id: residue_001
        source_chain_id: A
        current_chain_id: A
        source_resid: "42"
        current_resid: "42"
        source_residue_name: HIS
        current_residue_name: HIS

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
        source_residue_name: HEM
        current_residue_name: HEM

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
          evidence: "{CCD_PATH_1}/HEM.cif"
          missing_heavy_atoms: []
          extra_heavy_atoms: []
          duplicate_atom_names: []
          atom_name_mismatches: []
          element_mismatches: []

confirmed_relations:
  covalent_connections:
    - relation_id: relation_001
      endpoint_1:
        component_id: component_001
        residue_id: residue_001
        atom_name: NE2
      endpoint_2:
        component_id: component_001
        residue_id: residue_002
        atom_name: FE
      evidence: 智能体判断
      topology_effect_applied: true

  metal_coordination: []

rejected_candidates:
  covalent_connections: []
  metal_coordination: []

unresolved_items: []
```

该结构是 1.2 正式数据模型。不要同时另建平行的 `chain_groups[]`、`residue_records[]`、`missing_residue_ids[]` 或 `source_identity/current_identity` 对象重复表达同一事实。

`confirmed_relations` 与 `rejected_candidates` 不只是附属 relation inventory；它们共同构成共价连接检查和金属配位检查的正式检查结果：

```text
共价连接检查结果
= confirmed_relations.covalent_connections
+ rejected_candidates.covalent_connections

金属配位检查结果
= confirmed_relations.metal_coordination
+ rejected_candidates.metal_coordination
```

即使某项检查没有确认关系或拒绝候选，相应数组也必须存在并为空。这样能够区分“检查完成但没有对应结果”和“结果文件缺项”。

## 3. 文件级字段

`schema_version` 当前固定为 `3.0`。

`result_status: COMPLETE` 表示 1.2 要求的分类、三级 residue 检查、共价连接检查、金属配位检查，以及会影响最终 component / topology 归属的关系判断已经可靠完成并通过 validation；不表示没有发现结构问题。

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

`references` 只定义当前 model 本次检查实际使用的 RTP 文件和 CCD 路径变量：

```yaml
references:
  RTP_1: /absolute/path/to/aminoacids.rtp
  RTP_2: /absolute/path/to/special.rtp
  CCD_PATH_1: /absolute/path/to/ccd
```

规则：

- RTP 文件使用 `RTP_1`、`RTP_2`……；
- CCD 目录使用 `CCD_PATH_1`、`CCD_PATH_2`……；
- `RTP_n` 直接指向实际 RTP 文件；
- `CCD_PATH_n` 指向实际 CCD 文件目录；
- 不额外建立 `FF_PATH_n`；
- 不使用 `ref_001` 之类间接 reference ID；
- 不使用 `reference_entry`；
- 本环节不要求为这些 reference 文件统一计算或记录 SHA-256。

具体 CCD 文件由检查项直接写成 `{CCD_PATH_1}/HEM.cif` 这类表达。

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
- component membership 在所有确认且产生 topology effect 的关系应用后确定；
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
  value: <enum>
  evidence: <evidence>

topology_class:
  value: <enum>
  evidence: <evidence>
```

`polymer_class.value`：`POLYMER | BRANCHED | NONPOLYMER | WATER`。

`topology_class.value`：`STANDARD_RESIDUE | TOPOLOGY_LINKED_NONSTANDARD | INDEPENDENT_NONSTANDARD | SOLVENT_COMPONENT | ION_COMPONENT`。

`topology_class` 必须是共价连接检查和金属配位检查完成、所有 `topology_effect_applied: true` 的确认关系已经应用后的**最终值**。正式结果中不额外保存 provisional `topology_class`。

如果关系检查没有改变该 residue 的 topology 归属，保留初始分类依据对应的 `evidence`。如果关系检查使一个非标准 / solvent / ion residue 最终成为 `TOPOLOGY_LINKED_NONSTANDARD`：

- 由 Agent 对关系及 topology effect 完成闭合 → `evidence: 智能体判断`；
- 由用户确认该关系 / topology effect → `evidence: 人工决策`。

关系本身的端点、关系类型和 `topology_effect_applied` 仍在关系检查结果中记录，不在 `topology_class` 内重复。

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

## 9. Evidence 字段

允许：

```text
RTP_n
{CCD_PATH_n}/XXX.cif
智能体判断
人工决策
```

- `RTP_n`：Agent 直接以该 RTP 文件中的实际 residue definition 判断；
- `{CCD_PATH_n}/XXX.cif`：Agent 直接以该 CCD component file 判断；
- `智能体判断`：Agent 综合当前结构、结构注释、项目语义等信息判断；
- `人工决策`：最终结论由用户确认。

文件型 evidence 必须能通过同一文件级 `references` 解析到实际路径。

## 10. 共价连接检查结果

正式结果位置：

```text
confirmed_relations.covalent_connections
rejected_candidates.covalent_connections
```

确认关系示例：

```yaml
confirmed_relations:
  covalent_connections:
    - relation_id: relation_001
      endpoint_1:
        component_id: component_001
        residue_id: residue_010
        atom_name: SG
      endpoint_2:
        component_id: component_002
        residue_id: residue_001
        atom_name: C1
      evidence: 智能体判断
      topology_effect_applied: true
```

字段含义：

- `relation_id`：当前 model 内该关系的 identity；
- `endpoint_1` / `endpoint_2`：关系两端；`component_id + residue_id` 定位 residue，`atom_name` 定位参与关系的 atom；
- `evidence`：该关系确认采用的直接判断来源；
- `topology_effect_applied`：该已确认关系是否应影响后续 topology processing、最终 `topology_class` 或 component membership。

已经明确拒绝且有审计价值的共价候选写入 `rejected_candidates.covalent_connections`。没有对应结果时数组为空。

## 11. 金属配位检查结果

正式结果位置：

```text
confirmed_relations.metal_coordination
rejected_candidates.metal_coordination
```

记录结构与共价连接相同，但其科学语义是已确认 / 已拒绝的金属配位关系。

确认存在金属配位不自动意味着 `topology_effect_applied: true`。只有当前项目定义或用户决定明确要求该配位关系进入 topology connection 时，才把 `topology_effect_applied` 设为 `true`。

没有对应结果时数组为空。

关系端点这里只使用 `atom_name` 做当前关系定位；不建立完整 atom table，也不定义 `atom_id`。独立原子级正式数据结构仍另行讨论。

## 12. 关系检查结果与最终 `topology_class` 的一致性

正式结果写出前必须将两项关系检查结果应用到 residue 最终分类：

```text
confirmed_relations
→ 只取 topology_effect_applied: true
→ 更新相关 residue 最终 topology_class
→ 更新最终 component membership
→ 再物化 component_id / chain_index / residue_id
```

最低一致性要求：

- `STANDARD_RESIDUE` 不因连接关系改成非标准类别；
- 参与 topology-effect relation 的非标准 / solvent / ion residue 最终必须为 `TOPOLOGY_LINKED_NONSTANDARD`；
- `topology_effect_applied: false` 的关系不得改变 residue `topology_class`；
- `rejected_candidates` 不得改变正式分类或 component membership；
- 关系检查结果与最终 component membership 必须一致。

JSON Schema 只能检查字段结构，不能跨数组证明这一科学一致性；该一致性属于 1.2 validation 的必要检查。

## 13. `relation_decisions.yaml`

仅当当前 model 实际发生用户对共价连接或金属配位关系的确认或否决时生成。

```yaml
schema_version: "2.0"
model_id: "1"
decisions:
  - relation_id: relation_001
    relation_type: COVALENT_CONNECTION
    decision: CONFIRMED
```

- `relation_type`：`COVALENT_CONNECTION` 或 `METAL_COORDINATION`；
- `decision`：`CONFIRMED` 或 `REJECTED`。

没有实际人工关系决策时，不生成空文件。

## 14. `unresolved_items`

只保留不会改变最终分类、component membership、三级 residue 检查结果或 `topology_effect_applied` 的非阻断信息：

```yaml
- subject: <可定位对象>
  detail: <尚缺什么信息或存在什么非阻断不确定性>
```

如果未解决事项会改变正式结果，当前 model 不能形成 `result_status: COMPLETE`。

## 15. `classification_report.md`

报告按固定顺序组织：

1. 当前 model 与检查对象；
2. component / residue 初始分类依据与最终分类结果；
3. 残基缺失检查；
4. 多构象检查；
5. 重原子组成与命名检查；
6. 共价连接检查；
7. 金属配位检查；
8. 基于关系检查更新后的 `topology_class` 与 component membership；
9. 人工关系决策（若存在）；
10. 未解决事项；
11. 总结。

报告中的 residue 使用 `component_id + residue_id` 定位，并可同时显示当前 `chain_id + resid + residue_name` 方便人工阅读。机器可消费的正式事实仍以 `classification_result.yaml` 为准。

## 16. Project result registration

项目级结果索引只登记每个实际处理 model 的 `classification_result.yaml` 完整绝对路径，并说明该结果对应的 source structure / model。

`classification_report.md` 和 `relation_decisions.yaml` 不单独登记，由同一 model 目录中的正式结果继续定位。

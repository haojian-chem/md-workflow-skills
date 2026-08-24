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

- `classification_result.yaml`：保存当前 model 的 component / residue 层级、两类分类、三级 residue 检查、reference 变量和已闭合关系；
- `classification_report.md`：按检查顺序生成的人类可读审阅报告；
- `relation_decisions.yaml`：只在共价连接或金属配位关系实际发生人工确认或否决时生成，保存这些关系人工决策。

1.2 不再生成 `reference_manifest.yaml`。

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
        source_resid: "43"
        current_resid: null
        source_residue_name: GLY
        current_residue_name: null
        polymer_class:
          value: POLYMER
          evidence: 智能体判断
        topology_class:
          value: STANDARD_RESIDUE
          evidence: RTP_1
        missing_residue_check:
          status: ISSUE
          evidence: 智能体判断
        conformation_check:
          status: SKIPPED
          evidence: null
        heavy_atom_check:
          status: SKIPPED
          evidence: null
          missing_heavy_atoms: []
          extra_heavy_atoms: []
          duplicate_atom_names: []
          atom_name_mismatches: []
          element_mismatches: []
confirmed_relations:
  covalent_connections: []
  metal_coordination: []
rejected_candidates:
  covalent_connections: []
  metal_coordination: []
unresolved_items: []
```

该结构是 1.2 正式数据模型。不要同时另建平行的 `chain_groups[]`、`residue_records[]`、`missing_residue_ids[]` 或 `source_identity/current_identity` 对象重复表达同一事实。

## 3. 文件级字段

`schema_version` 当前固定为 `3.0`。

`result_status: COMPLETE` 表示 1.2 要求的分类、三级 residue 检查和会影响最终 component / topology 归属的关系判断已经可靠完成并通过 validation；不表示没有发现结构问题。

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

model 信息只在文件级出现一次；residue 内不再重复 model 字段。

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

## 5. `components` 与身份层级

正式身份层级：

```text
model
└── component_id
    └── residue_id
```

### `component_id`

- 标识当前 model 中一个最终 component；
- 在当前 model 的 `classification_result.yaml` 中唯一；
- 不表示 CCD component ID、PDB chain ID 或 residue name；
- component membership 在所有确认且产生 topology effect 的关系应用后确定；
- 下游直接消费正式值，不自行重构。

### `residue_id`

- 标识所属 component 中的一个 residue；
- 在所属 `component_id` 内唯一；
- 不要求跨不同 component 单独唯一；
- 下游定位 residue 使用 `component_id + residue_id`；
- 不是 source/current resid，也不是 residue name；
- 下游不得根据 chain、resid 或 residue name 重构其值。

每个 component 的 `residues` 数组顺序就是 1.2 为该 component 建立的正式 residue 顺序。已确认缺失 residue 直接位于其应有位置，不另建 `missing_residues` 或 `missing_residue_ids` 集合。

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

- `source_chain_id`：当前 1.2 输入结构中的原始 chain ID；源结构没有显式 chain ID 时按实际格式允许空值。
- `current_chain_id`：生成本次 1.2 正式结果时当前结构中用于定位该 residue 的 chain ID。缺失 residue 若所属当前 chain 能可靠确定可以记录；无法可靠确定时不得猜测。
- `source_resid`：源结构中用于定位该 residue 的实际 resid 表达。需要区分插入位置时，把源格式实际 resid 表达整体保留在该字段中，不另建独立 `insertion_code` 作为 residue 科学属性。
- `current_resid`：生成本次 1.2 正式结果时当前结构中的 resid。已确认缺失 residue 没有当前 residue 坐标实例，因此为 `null`。
- `source_residue_name`：源结构或可追溯序列注释中的原始 residue name，后续不得回写覆盖。
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

分类 `evidence` 记录该最终分类直接采用的依据，不写抽象的“兼容 / 合理 / 已确认”。

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

本项为 `ISSUE` 时，`conformation_check` 与 `heavy_atom_check` 均为 `SKIPPED`。

### 8.2 `conformation_check`

```yaml
conformation_check:
  status: PASS | ISSUE | SKIPPED
  evidence: <evidence-or-null>
```

- `PASS`：没有发现多构象问题；
- `ISSUE`：当前 residue 存在多构象问题；
- `SKIPPED`：前一级残基缺失检查已发现问题。

本项只记录“是否存在多构象问题”。不记录构象选择、构象整合或 1.4 的处理决定。本项为 `ISSUE` 时，重原子检查为 `SKIPPED`。

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

问题字段：

- `missing_heavy_atoms`：reference 有、当前 residue 缺失的重原子名；
- `extra_heavy_atoms`：当前 residue 有、reference 没有的额外重原子名；
- `duplicate_atom_names`：当前 residue 中重复的 atom name；
- `atom_name_mismatches`：有明确对应依据但当前名称与 reference 名称不同；
- `element_mismatches`：当前结构与 reference 的元素信息均可靠时记录的元素不一致。

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
- `智能体判断`：Agent 综合当前结构、结构注释、项目语义等信息判断，且不是直接由 RTP / CCD 比较得出；
- `人工决策`：最终结论由用户确认。

文件型 evidence 必须能通过同一文件级 `references` 解析到实际路径。

## 10. 关系记录

关系保持在 model 文件级，因为一个关系可以跨不同 component。

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
        atom_name: FE
      evidence: 智能体判断
      topology_effect_applied: true
  metal_coordination: []
```

关系端点中的 `component_id + residue_id` 必须定位到当前正式 component / residue；`atom_name` 只说明关系实际涉及的 atom。

这里不建立完整 atom table，也不定义 `atom_id`。关系端点和重原子问题中出现 atom name 只承担当前关系或检查问题定位；是否建立独立原子级正式数据结构另行讨论。

`rejected_candidates` 使用相同端点结构保存已经明确拒绝且有审计价值的关系候选。

任何尚未闭合、会改变最终 component membership、`topology_class` 或 `topology_effect_applied` 的关系事项都不能留在正式 COMPLETE 结果中。

## 11. `relation_decisions.yaml`

仅当当前 model 实际发生用户对共价连接或金属配位关系的确认或否决时生成。

```yaml
schema_version: "2.0"
model_id: "1"
decisions:
  - relation_id: relation_001
    relation_type: COVALENT_CONNECTION
    decision: CONFIRMED
```

- `model_id`：当前 decision 文件所属 model，只在文件级记录一次；
- `relation_id`：当前 model 正式关系候选的 identity；
- `relation_type`：`COVALENT_CONNECTION` 或 `METAL_COORDINATION`；
- `decision`：`CONFIRMED` 或 `REJECTED`。

没有实际人工关系决策时，不生成空文件。

## 12. `unresolved_items`

只保留不会改变最终分类、component membership、三级检查结果或 `topology_effect_applied` 的非阻断信息：

```yaml
- subject: <可定位对象>
  detail: <尚缺什么信息或存在什么非阻断不确定性>
```

如果未解决事项会改变正式结果，当前 model 不能形成 `result_status: COMPLETE`。

## 13. `classification_report.md`

报告按固定顺序组织：

1. 当前 model 与检查对象；
2. component / residue 分类；
3. 残基缺失检查；
4. 多构象检查；
5. 重原子组成与命名检查；
6. 共价连接；
7. 金属配位；
8. 人工关系决策（若存在）；
9. 未解决事项；
10. 总结。

报告中的 residue 使用 `component_id + residue_id` 定位，并可同时显示当前 `chain_id + resid + residue_name` 方便人工阅读。机器可消费的正式事实仍以 `classification_result.yaml` 为准。

## 14. Project result registration

项目级结果索引只登记每个实际处理 model 的 `classification_result.yaml` 完整绝对路径，并说明该结果对应的 source structure / model。

`classification_report.md` 和 `relation_decisions.yaml` 不单独登记，由同一 model 目录中的正式结果继续定位。

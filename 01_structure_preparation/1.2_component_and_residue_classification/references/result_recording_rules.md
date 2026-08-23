# 1.2 正式结果记录规则

本文件拥有结构准备 1.2 正式结果的组织、字段语义、报告格式和登记要求。科学判断规则见 `classification_rules.md`；机器字段约束见 `../schemas/`。

## 1. 正式结果集合

实际执行新的 1.2 后，正式结果为：

```text
classification_result.yaml
reference_manifest.yaml
classification_report.md
relation_decisions.yaml   # 仅实际发生用户关系确认时存在
```

其中：

- `classification_result.yaml`：后续 Stage / Step 持续使用的结构分类、稳定身份、正式残基顺序、检查结果和已确认关系基准；
- `reference_manifest.yaml`：本次实际用于形成判断的参考文件及其 SHA-256；
- `classification_report.md`：按固定检查顺序组织的人工审阅报告；
- `relation_decisions.yaml`：实际发生的用户关系确认记录。

`classification_result.yaml` 与 `reference_manifest.yaml` 是项目级长期检索入口，其内容不得依赖已经退出正式结果体系的临时工作文件或脚本中间状态。

## 2. `reference_manifest.yaml`

`reference_manifest.yaml` 只记录**实际用于形成本次正式判断**的参考文件，不记录“可能有用但没有使用”的候选文件，也不建立不存在文件的占位记录。

每个参考文件记录至少包含：

```yaml
reference_id: ref_001
roles:
  - <schema-defined role>
path: /absolute/path/to/reference
sha256: <64-hex>
source: PROJECT | SKILL | FORCE_FIELD | USER
residue_names: []
component_ids: []
note: null
```

规则：

1. `path` 使用本次实际读取文件的完整绝对路径；
2. `sha256` 对应本次读取时的实际文件内容；
3. 同一个实际文件只建立一个 `reference_id`；同一文件承担多个作用时在 `roles` 中全部列出，不重复建立多份记录；
4. `classification_result.yaml` 中需要引用参考依据的位置使用 `reference_id`，需要定位文件内部条目时另记录 `reference_entry`；
5. CCD 直接记录实际使用的 CCD 组分定义文件，不要求记录或构造自定义 library root；
6. 目标力场使用实际残基定义文件，不用只有力场名称的字符串替代文件定位；
7. 序列参考、项目残基定义和关系定义同样记录实际文件及 SHA-256。

## 3. `classification_result.yaml` 顶层结构

正式结果按当前 `schemas/classification_result.schema.yaml` 组织，核心顶层字段为：

```yaml
schema_version: "2.0"
result_status: COMPLETE
selected_model_id: <model>
classification_mode: REGISTRY | FORCE_FIELD_ANALYSIS

source_structure:
  path: /absolute/path/to/source_structure
  sha256: <64-hex>
  source_format: PDB | MMCIF | AF3_CIF

reference_manifest:
  path: /absolute/path/to/reference_manifest.yaml
  sha256: <64-hex>

chain_groups: []
residue_records: []
confirmed_relations:
  covalent_connections: []
  metal_coordination: []
rejected_candidates:
  covalent_connections: []
  metal_coordination: []
unresolved_items: []
summary: {}
```

`source_structure.path` 与 `reference_manifest.path` 都使用完整绝对路径。

`result_status: COMPLETE` 表示 1.2 规定的检查已经可靠执行，所有会改变正式分类、稳定身份或 `topology_effect_applied` 的事项已经闭合，并且当前结果通过 validation；不表示“结构没有发现任何问题”。

未满足 COMPLETE 条件时可以在当前任务目录保留草稿或工作记录，但不得把该草稿登记为正式 1.2 `classification_result.yaml`。

## 4. `residue_records[]`

### 4.1 正式残基顺序

`residue_records[]` 的数组顺序是 1.2 的正式残基顺序。

同一 polymer / chain 中：

- 已观察残基按结构顺序和可靠的序列—结构对应确定位置；
- 已确认 `MISSING_EXPECTED` 残基插入其应有位置；
- 不按 `residue_id`、残基名或源残基编号的字典顺序/数值顺序重新排序。

后续 Skill 需要保持稳定残基顺序时应直接使用该数组顺序。

### 4.2 每个残基记录

每个残基记录至少包含：

```yaml
residue_id: <residue_id>
component_id: <component_id>
source_identity: ...
current_identity: ... | null
chain_index: <integer>
source_chain_id: ...
source_resid: ...
residue_name: ...
presence_status: OBSERVED | MISSING_EXPECTED
sequence_position: <integer> | null
classification: ...
conformation: ...
heavy_atom_check: ...
```

这些字段不能用未限定的“残基 ID”概括。`residue_id`、`source_resid`、当前结构中的 `resid` 与 `sequence_position` 分别保存不同语义。

### 4.3 `classification`

至少记录：

```yaml
classification:
  component_id: <component_id>
  polymer_class: <enum>
  topology_class: <enum>
  resolution_status: RESOLVED | CONFLICT | UNRESOLVED
  primary_source: <enum or null>
  evidence:
    - evidence_type: <enum>
      reference_id: <ref_...> | null
      detail: <简短具体事实>
```

`detail` 记录实际判断事实，例如“当前 `residue_name` 在 ref_003 指向的 `aminoacids.rtp` 中存在精确同名 residue block”；不写“兼容”“合理”“看起来正确”等无法复核的抽象结论。

### 4.4 `conformation`

单构象残基：

```yaml
conformation:
  status: SINGLE_CONFORMATION
  altloc_ids: []
  alternate_atoms: []
```

多构象残基：

```yaml
conformation:
  status: MULTIPLE_CONFORMATIONS
  altloc_ids: [A, B]
  alternate_atoms:
    - atom_name: CB
      states:
        - altloc_id: A
          occupancy: 0.60
        - altloc_id: B
          occupancy: 0.40
```

只列实际带 alternate-conformation 标记的原子；共享原子不需要逐个复制。

### 4.5 `heavy_atom_check`

必须明确 `execution_status`：

```text
COMPLETED
NOT_PERFORMED
NOT_APPLICABLE
REFERENCE_UNAVAILABLE
```

存在坐标且已可靠完成比较时使用 `COMPLETED`。整个残基缺失时使用 `NOT_APPLICABLE`，`reason` 明确记录 `RESIDUE_MISSING`。

单构象残基的比较在 `comparisons[]` 中建立一个 `scope: SINGLE`；多构象能够可靠拆分时，每个候选构象分别建立一个比较范围。例如：

```yaml
heavy_atom_check:
  execution_status: COMPLETED
  reference_id: ref_004
  reference_entry: HEM
  findings:
    - MISSING_EXPECTED_HEAVY_ATOMS
    - ATOM_NAME_MAPPING_REQUIRED
  comparisons:
    - scope: SINGLE
      exact_comparison:
        missing_expected_atom_names: [O1A]
        unexpected_observed_atom_names: [O1]
        duplicate_atom_names: []
        element_mismatches: []
      atom_name_mapping_candidates:
        - observed_atom_name: O1
          reference_atom_name: O1A
          mapping_source: CCD_ALTERNATE_ATOM_NAME
      mapping_resolution_status: APPLIED
      effective_comparison:
        missing_expected_atom_names: []
        unexpected_observed_atom_names: []
        duplicate_atom_names: []
        element_mismatches: []
  reason: null
```

多构象时 `scope` 使用实际 `altLoc` ID；对应原子集合按 `classification_rules.md` 中“共享原子 + 当前候选 `altLoc` 原子”的规则确定。

`findings` 使用 schema 固定问题类型。不存在某类问题时保留空数组，不使用自然语言同义词替代正式问题类型。

## 5. 关系记录

正式已确认关系只进入：

```yaml
confirmed_relations:
  covalent_connections: []
  metal_coordination: []
```

每个关系至少记录：

- `relation_id`；
- `relation_type`；
- 两个稳定端点；
- `evidence_status`；
- `evidence`；
- `topology_effect_applied`。

端点中保留 `residue_id`、`component_id`、源/当前原子身份、atom name 与 `altLoc` 信息，保证后续结构发生编号、chain 或对象组织变化后仍可追溯到 1.2 原始关系。

已经明确拒绝且有保留审计价值的候选进入 `rejected_candidates`。仍存在证据不足或参考冲突，但不影响正式分类、稳定身份和 `topology_effect_applied` 的事项，可以保留在 `unresolved_items` 中作为非阻断信息。

任何尚未闭合、会改变正式分类、稳定身份或 `topology_effect_applied` 的事项都属于阻断问题；这类问题存在时不得形成正式 `result_status: COMPLETE` 结果，因此不会以 `blocking: true` 出现在正式 v2 `classification_result.yaml` 中。

## 6. `unresolved_items[]`

正式 COMPLETE 结果中的每项至少记录：

```yaml
item_id: unresolved_001
item_type: <schema-defined type>
blocking: false
subject:
  residue_id: ...        # 适用时
  relation_id: ...       # 适用时
reason: <当前缺少什么证据或存在什么冲突>
required_resolution: <后续若需要闭合该事项，应补充什么信息>
```

普通已确认结构问题，例如已经明确的缺失残基或重原子缺失，不因为“存在问题”而成为未解决事项。

## 7. `summary`

`summary` 只保存从正式明细可以直接核对的计数，不承担科学判断：

```text
chain_group_count
observed_residue_count
missing_residue_count
standard_residue_count
topology_linked_nonstandard_count
independent_nonstandard_count
solvent_component_count
ion_component_count
multiple_conformation_residue_count
heavy_atom_issue_residue_count
confirmed_covalent_connection_count
confirmed_metal_coordination_count
unresolved_item_count
```

计数与 `residue_records[]` 或关系明细不一致时，以明细为检查对象并修正 `summary`；不得反向修改明细去迁就汇总计数。

## 8. `relation_decisions.yaml`

只有实际发生用户关系确认时生成。

至少绑定：

```yaml
schema_version: "1.0"
structure:
  structure_sha256: <source SHA-256>
  selected_model_id: <model>
decisions:
  - relation_id: <relation_id>
    relation_kind: COVALENT_CONNECTION | METAL_COORDINATION
    decision: CONFIRMED | REJECTED
```

用户决定写入后，最终 `classification_result.yaml` 必须同步体现该决定；不能把 `relation_decisions.yaml` 作为与正式结果互相矛盾的第二状态来源。

## 9. `classification_report.md`

报告采用固定章节顺序：

```markdown
# 1.2 Component and residue classification report

## 1. 检查对象与参考依据
## 2. 组分与残基分类
## 3. 缺失残基
## 4. 多构象
## 5. 重原子组成与命名
## 6. 共价连接
## 7. 金属配位
## 8. 未解决事项
## 9. 结果摘要
```

报告顶部记录：

- source structure 完整绝对路径和 SHA-256；
- `selected_model_id`；
- `classification_mode`；
- `classification_result.yaml` 与 `reference_manifest.yaml` 的完整绝对路径。

报告正文要求：

- 按上述固定检查顺序记录；
- 每项先写实际检查范围和简要结果；
- 发现问题时定位到具体残基或关系；
- 涉及原子差异时使用正式问题类型并列出实际 atom name；
- 不逐条复制所有正常残基；
- 不用 `PASS / FAIL` 替代实际检查事实；
- 不引入 schema 未定义的同义问题类型。

## 10. 项目结果索引

项目结果索引只登记：

```text
classification_result.yaml
reference_manifest.yaml
```

登记各自完整绝对路径及简明说明。

`classification_report.md` 与实际存在的 `relation_decisions.yaml` 保持为当前任务正式结果，但不单独登记到项目结果索引。

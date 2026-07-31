# chain_and_component_selection Draft Validation

日期：2026-07-23

## 检查对象

```text
02_operations/chain_and_component_selection/SKILL.md
02_operations/chain_and_component_selection/references/selection_rules.md
02_operations/chain_and_component_selection/schemas/selection_spec.schema.yaml
02_operations/chain_and_component_selection/schemas/selection_manifest.schema.yaml
02_operations/chain_and_component_selection/schemas/selection_mapping.schema.yaml
02_validators/chain_and_component_selection_validator/SKILL.md
00_authoring/content_maps/chain_and_component_selection.yaml
00_authoring/content_maps/chain_and_component_selection_validator.yaml
04_evals/chain_and_component_selection/fixtures/selection_cases.yaml
04_evals/chain_and_component_selection_validator/fixtures/selection_validation_cases.yaml
```

## 当前状态

```text
Operation Skill: present
Validator Skill: present
selection spec schema: present
selection manifest schema: present
atom mapping schema: present
Operation behavior cases: 18
Validator behavior cases: 17
1.2 selection identity input contract: implemented
deterministic selection implementation: not implemented
executable tests: not run
status: draft
```

本记录只表示职责、语义和 contract 已形成首版，不代表 1.3 可运行。

## 已冻结的 draft 语义

### 显式选择

- 必须提供结构化 `selection_spec.yaml`；
- spec 必须明确一个 model 和非空 component IDs；
- Operation 不得从自然语言、链名模糊匹配或“常见 MD 做法”猜测选择；
- 不默认保留全部、仅保留蛋白、删除所有水或删除所有离子；
- v1 只支持完整 component selection，不支持 residue-range 或 atom-level filtering。

### 共价闭包

确认关系：

```text
COVALENT
DISULFIDE
GLYCOSIDIC
```

连接跨越选择边界时：

- Operation BLOCKED；
- 不自动扩展选择；
- 不静默删除连接；
- 必须重新解析用户决定。

Metal coordination、geometry-only covalent candidate、hydrogen bond 和 salt bridge 不强制 inclusion，但跨边界关系写入 manifest/report。

### 数据保持

选中 component 的全部：

- residues；
- atoms；
- altLoc；
- source order；
- identity fields；
- coordinates、occupancy、B factor、element 和可表达 charge；

均应保留。

### 输出格式

selection spec 显式选择：

```text
PDB | MMCIF
```

PDB 不能无损表示 identifiers 时 BLOCKED；AF3 CIF 选择输出为 normalized MMCIF，原始 AF3 source 保留，非坐标专有 categories 的保留限制必须报告。

## Operation 输出

```text
selected structure
selection manifest
source-to-output atom mapping
Operation report
```

Operation 只生成 `present_unvalidated` STRUCTURE candidate，不自行声明通过。

## Validator gate

Validator 必须独立从：

```text
classification result + selection spec
```

重算 expected model/component/residue/atom set，不能直接信任 manifest。

核验：

- exact selected set；
- all atoms and altLocs；
- one-to-one mapping；
- coordinate/occupancy/B-factor/element preservation；
- confirmed covalent relations；
- no stale connections；
- hashes、provenance 和 output format；
- source and candidate unchanged during validation。

通过只说明 selection fidelity，不说明 altLoc、completeness、protonation 或最终 structure-preparation gate。

## Behavior fixtures

Operation 18 cases 覆盖：

- explicit polymer/ligand selection；
- water/ion selection complement；
- missing/invalid spec；
- unknown IDs；
- covalent/disulfide boundary；
- coordination and geometry-only candidate boundary；
- model selection；
- PDB identifier limits；
- AF3 normalized MMCIF；
- altLoc/atom preservation；
- hash/output conflicts；
- management path isolation；
- UNVALIDATED artifact candidate。

Validator 17 cases 覆盖：

- exact set pass；
- extra/missing residue；
- atom/altLoc mapping mismatch；
- coordinate and attribute changes；
- PDB rounding warning；
- connection mismatch；
- coordination non-covalent behavior；
- dishonest manifest；
- invalid covalent-breaking spec；
- source hash change；
- missing candidate；
- limited validation claims；
- source/candidate immutability。

## 已完成的跨阶段前置接口

- 1.2 `classification_result.yaml` 输出 `source_structure`；
- 每个 final component 输出稳定 `component_id`、observed `residue_ids` 与 `missing_residue_ids`；
- 每个 residue 输出 `residue_id` 与所属 `component_id`；
- relation endpoint 输出 `endpoint_id`、`residue_id`、`component_id`；
- relation 输出稳定 `relation_id`；
- 聚合水、离子和重复小分子仍保留全部实例级 residue identity；
- v1 共价闭包统一使用 1.2 实际 relation type `COVALENT_CONNECTION`。

## 尚未实现

1. deterministic `select_structure.py`；
2. deterministic `validate_selection.py`；
3. combined `subagent_result v2` builder；
4. schema meta-validation tests；
5. executable PDB/mmCIF fixtures；
6. identifier/format conversion tests；
7. Operation+Validator combined task test；
8. Manager FAST integration and task closure；
9. real 1.2 classification result → selection spec → candidate flow。

完成上述内容前，Operation 和 Validator 均保持 `draft`。

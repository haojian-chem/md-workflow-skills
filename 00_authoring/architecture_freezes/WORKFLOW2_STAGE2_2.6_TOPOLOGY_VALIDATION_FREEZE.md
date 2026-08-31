# Workflow 2 Stage 2.6 Topology validation freeze

Status: CURRENT ARCHITECTURE FREEZE

## 0. 文档定位

本文件是 `2.6 Topology validation` 后续 Skill generation 的 current authoring authority。

本轮设计是在 current 1.2 / 2.5 正式接口和 current authoring rules 下重新敲定的结果。旧 Stage 2 综合冻结文件
`WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md` 中与 2.6 具体检查内容、输入文件或结果记录有关的旧文本均被本文件取代，不得作为后续 2.6 Skill generation 的规则来源。

旧 Stage 2 综合冻结文件仍可用于其尚未被其它 current freeze / active Skill 取代的 Stage-level architecture；读取该文件时不得重新引入其中已经被本文件取代的 2.6 旧规则。

本 freeze 完成不表示已经批准生成 `02_topology_preparation/2.6_topology_validation/SKILL.md`。

## 1. 职责

Topology validation 对当前拓扑整合正式结果进行独立、只读终检。

当前职责只检查已经形成的结构文件和拓扑文件，不修改结构文件、`.top`、`.itp`、map 或参数文件，也不在发现问题时顺手修正拓扑。

发现问题时记录实际问题及可确定的来源；后续是否重新进入其它 Stage 2 工作项由 Stage 2 main Skill 负责。

## 2. 直接正式依赖

当前工作项的直接正式依赖固定为：

1. `classification_result.yaml`；
2. `topology_integration_result.yaml`。

`classification_result.yaml` 提供当前正式的 `component_id + residue_id`、`topology_class` 和 `topology_linked_checks`。

`topology_integration_result.yaml` 提供本次需要检查的拓扑整合正式结果，并定位当前结构文件、当前 map、体系 `.top` 和本次拓扑整合生成的 `.itp`。

当前结构文件的 basename 不在 2.6 固定；2.6 使用 `topology_integration_result.yaml` 实际记录的结构文件路径。

## 3. 结果记录中的文件引用

2.6 正式结果记录中的 `references` 同时承担：

1. 记录当前结果实际依赖的上游正式文件；
2. 为结果中反复引用的实际检查文件提供公共绝对路径引用。

当前固定使用：

```yaml
references:
  CLASSIFICATION_RESULT: /absolute/path/to/classification_result.yaml
  TOPOLOGY_INTEGRATION_RESULT: /absolute/path/to/topology_integration_result.yaml
  STRUCTURE: /absolute/path/to/current_structure_file.gro
  MAP: /absolute/path/to/current_map_file
  TOP: /absolute/path/to/current_system.top
  ITP_1: /absolute/path/to/first_actual_itp
  ITP_2: /absolute/path/to/second_actual_itp
```

其中：

- `STRUCTURE`、`MAP` 和 `TOP` 分别使用 `topology_integration_result.yaml` 中实际记录的结构文件、map 和体系 `.top` 路径；
- `ITP_n` 按 `topology_integration_result.yaml` 中本次拓扑整合生成的 `.itp` 实际顺序逐项记录；
- 实际不存在的可选 `.itp` 不建立占位引用；
- 所有路径保持完整绝对路径语义；
- 不根据任何默认 basename 推断实际文件名。

当前 map 作为需要通过 `component_id + residue_id` 或 atom identity 定位当前结构 / 拓扑原子时的映射依据；本轮不为 map 单独设置逐原子对应检查或 provenance 检查项目。

## 4. 必需检查项

### 4.1 检查体系 `.top` 中各 `#include` 指向的文件是否存在

读取体系 `.top` 中实际出现的 `#include`，逐项解析其实际文件路径。

对每个被引用文件确认：

- 文件实际存在；
- 文件可读取。

发现问题时记录对应 `#include` 和无法定位或无法读取的实际文件路径。

本项不顺带承担参数内容、`moleculetype` 定义或其它拓扑语义检查。

### 4.2 检查当前结构文件与体系 `.top` / `.itp` 中记录的分子、残基和原子是否逐项对应

按体系 `.top` 的 `[ molecules ]` 中记录的 `moleculetype` 顺序和数量，读取对应 `moleculetype` 的 `[ atoms ]`，展开当前拓扑所描述的分子、残基和原子顺序。

逐项核对当前结构文件，至少检查：

- 分子数量；
- 分子顺序；
- 每个分子的原子数量；
- residue 顺序；
- atom 顺序；
- 对应位置的 residue name；
- 对应位置的 atom name。

发现差异时记录体系 `.top` 中的 `[ molecules ]` 条目、对应 `moleculetype`、结构文件中的实际位置和具体差异。

### 4.3 检查已确认并产生 topology effect 的 `topology-linked` 关系是否写入最终拓扑

读取 `classification_result.yaml` 中满足以下条件的 `topology_linked_checks`：

```text
judgment = CONFIRMED
且
topology_effect_applied = true
```

使用其中记录的关系两端身份，在需要时结合当前 map 定位当前结构文件和最终拓扑中的对应 atom。

对每条关系检查最终拓扑是否实际写入与该正式关系相对应的 topology effect。

`judgment = REJECTED` 或 `topology_effect_applied = false` 的记录不作为本项要求最终拓扑必须体现的关系。

对 `COVALENT_CONNECTION`，后续 Skill 应检查关系两端 atom 是否在最终拓扑中形成相应成键关系。

对 `METAL_COORDINATION`，本轮只冻结“必须核对其已经要求的 topology effect 是否体现在最终拓扑”这一检查要求；不得未经进一步确认把所有产生 topology effect 的金属配位机械等同为 `[ bonds ]` 直接成键。具体 topology representation 如在 Skill generation 前仍不能由 current upstream result 唯一确定，应保留为需要进一步敲定的科学细节，不自行发明固定表示。

### 4.4 检查 topology-linked 参数化要求删除的标准残基原子是否已经删除

从 `topology_integration_result.yaml` 记录的实际来源定位本次拓扑整合采用的 topology-linked 参数化正式结果。

读取其中的 `standard_atom_deletions`。

对每个指定删除的标准残基 atom，检查：

- 当前结构文件中已经不存在该 atom；
- 最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 中已经不存在该 atom。

发现仍保留的 atom 时，记录对应 topology-linked 参数化正式结果、`component_id + residue_id`、atom name、结构文件或最终 `[ atoms ]` 中的实际位置。

### 4.5 检查 topology-linked 参数化要求的标准残基一侧电荷修改是否写入最终拓扑

从 `topology_integration_result.yaml` 记录的实际来源定位本次拓扑整合采用的 topology-linked 参数化正式结果、对应电荷文件及完成该对应所需的 map。

读取参数化正式结果中的 `charge_modification_scope`。

对其中属于标准残基一侧的每个 residue，按照参数化模型 map 与电荷文件确定相关 atom 的指定电荷，并逐 atom 检查最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 所记录 `charge` 是否采用这些电荷值。

正式结果不展开每个 atom 的指定值和最终值；按 residue 记录实际检查 atom 数量及发现电荷差异的 atom 数量。

### 4.6 使用 `gmx grompp` 检查当前结构文件和体系 `.top`

使用当前结构文件和体系 `.top` 执行 `gmx grompp`。

正式结果记录：

- 实际使用的 GROMACS version；
- 实际执行命令；
- process return code；
- `gmx grompp` 输出的 note；
- warning；
- error。

`return_code = 0` 不能替代 4.1–4.5 的独立检查。

用于本项检查的 `.mdp`、临时 `.tpr` 或其它 preprocessing 工作文件不因执行本检查自动成为正式结果或项目结果索引项；如 Skill generation 时需要固定专用 validation `.mdp`，应在当时基于 current GROMACS / Stage 3 接口重新确认，不从旧冻结自动继承。

## 5. 正式结果与记录格式

### 5.1 唯一正式结果

2.6 只生成一个正式结果：

`topology_validation_result.yaml`

不生成平行 Markdown report，也不生成第二份 validation summary。

该 YAML 只记录实际检查对象和检查结果，不记录：

```text
PASS
FAIL
COMPLETE
result_status
validation status
overall conclusion
blocking findings
```

### 5.2 顶层结构

正式结果固定采用：

```yaml
target_id: target_001

references:
  # 按第 3 节记录

check_results:
  top_includes: []
  structure_topology: {}
  topology_linked_relations: []
  standard_atom_deletions: []
  standard_side_charge_modifications: []
  grompp: {}
```

六个检查结果字段均保留；每个字段按以下规则记录对应检查的实际结果。

### 5.3 `top_includes`

体系 `.top` 中每个实际 `#include` 记录：

```yaml
top_includes:
  - include_value: "molecule_1.itp"
    resolved_path: /absolute/path/to/molecule_1.itp
    exists: true
    readable: true
```

字段语义：

- `include_value`：`#include` 中实际写出的文件表达；
- `resolved_path`：解析得到的实际完整路径；
- `exists`：该路径指向的文件是否存在；
- `readable`：该文件是否可读取。

本项不记录 `line_number`。

### 5.4 `structure_topology`

本项记录当前结构文件和按体系 `.top [ molecules ]`、对应 `moleculetype [ atoms ]` 展开的拓扑规模，并只展开实际发现的差异：

```yaml
structure_topology:
  structure_residue_count: 512
  structure_atom_count: 8241
  topology_molecule_count: 4
  topology_residue_count: 512
  topology_atom_count: 8241

  molecule_count_differences: []
  molecule_order_differences: []
  molecule_atom_count_differences: []
  residue_order_differences: []
  atom_order_differences: []
  residue_name_differences: []
  atom_name_differences: []
```

各差异记录按对应层级保存能够定位问题的 `moleculetype`、molecule instance、residue / atom 位置，以及结构文件与拓扑文件中的实际值。

不为没有差异的普通 molecule、residue 或 atom 逐项生成记录。

### 5.5 `topology_linked_relations`

每条 `judgment = CONFIRMED` 且 `topology_effect_applied = true` 的关系均建立一条记录。

对 `COVALENT_CONNECTION`，保留 `atom_1` 和 `atom_2`：

```yaml
topology_linked_relations:
  - relation_id: relation_001
    relation_type: COVALENT_CONNECTION

    atom_1:
      component_id: component_001
      residue_id: residue_042
      atom_name: SG
      moleculetype: molecule_1
      atom_nr: 652

    atom_2:
      component_id: component_001
      residue_id: residue_121
      atom_name: C1
      moleculetype: molecule_1
      atom_nr: 1854

    topology_entries:
      - file: ${ITP_1}
        moleculetype: molecule_1
        section: bonds
        line_number: 724
        atom_nrs: [652, 1854]
        entry: "652 1854 1 ..."
```

对 `METAL_COORDINATION`，保留 `metal` 和 `donor`，其定位字段与上例相同；`topology_entries` 记录最终拓扑中实际采用的 section 和条目，不预设所有金属配位均通过 `[ bonds ]` 表达。

完成检索但未找到对应 topology entry 时记录：

```yaml
topology_entries: []
```

不另设 `topology_effect_found` 或其它判断字段。

### 5.6 `standard_atom_deletions`

按实际采用的 topology-linked 参数化正式结果分组：

```yaml
standard_atom_deletions:
  - source_result: /absolute/path/to/topology_linked_parameterization_result.yaml

    deletions:
      - relation_id: relation_001
        source_current_atom_serial: 123
        component_id: component_001
        residue_id: residue_042
        atom_name: HG
        structure_matches: []
        topology_matches: []
```

`structure_matches` 记录当前结构文件中实际找到的对应 atom 及其位置；`topology_matches` 记录最终拓扑文件中对应 `moleculetype [ atoms ]` 中实际找到的对应 atom 及其位置。

未找到对应 atom 时保留空数组，不另设 `deleted`、`status` 或其它判断字段。

### 5.7 `standard_side_charge_modifications`

检查过程仍按 4.5 逐 atom 完成；正式结果只按 residue 记录：

```yaml
standard_side_charge_modifications:
  - source_result: /absolute/path/to/topology_linked_parameterization_result.yaml
    residue_count: 2

    residues:
      - component_id: component_001
        residue_id: residue_042
        checked_atom_count: 11
        charge_difference_count: 0

      - component_id: component_001
        residue_id: residue_043
        checked_atom_count: 10
        charge_difference_count: 2
```

字段语义：

- `source_result`：本组检查实际采用的 topology-linked 参数化正式结果完整路径；
- `residue_count`：本组实际检查的标准残基数量；
- `checked_atom_count`：对应 residue 中实际完成电荷核对的 atom 数量；
- `charge_difference_count`：参数化结果指定电荷与最终拓扑文件对应 `[ atoms ] charge` 不同的 atom 数量。

本项不记录 atom name、指定电荷值或最终拓扑电荷值。

### 5.8 `grompp`

只记录实际执行事实：

```yaml
grompp:
  gromacs_version: "GROMACS 2022.2"
  command: >
    gmx grompp -f /absolute/path/to/validation.mdp
    -c ${STRUCTURE}
    -p ${TOP}
    -o /absolute/path/to/temporary.tpr
  return_code: 0
  notes: []
  warnings: []
  errors: []
```

不记录 `preprocessing_succeeded`、`status` 或其它二次结论字段。

### 5.9 项目结果索引登记

项目结果索引只登记：

`topology_validation_result.yaml`

当前结构文件、map、体系 `.top`、`.itp`、用于 `gmx grompp` 的 `.mdp`、临时 `.tpr`、debug、scratch 和 cache 均不作为 2.6 新结果重复登记。

## 6. 当前明确删除的旧 2.6 规则

以下旧设计不再作为 current 2.6 必需检查或结果记录：

- 单独检查当前 map 与结构文件逐原子对应；
- 单独检查当前 map provenance；
- 单独计算当前体系总电荷并设置电荷判据；
- 在 `gmx grompp` 之外再维护一套 atom type / bonded parameter definition 查找检查；
- 以抽象的 `package completeness`、`internal consistency`、`charge/connectivity sanity` 等标签代替具体检查关系；
- 为六项检查增加 PASS / FAIL、完成状态、overall conclusion 或 blocking finding；
- 为标准残基一侧电荷修改在正式结果中展开 atom-level 电荷明细。

如果后续出现新的实际需求，应按 current authoring rules 重新证明其必要性后再修改本 freeze 或 current Skill，不从旧 Stage 2 综合冻结恢复这些已经退出的规则。

## 7. 后续 Skill generation 读取规则

后续生成 `02_topology_preparation/2.6_topology_validation/SKILL.md` 时：

```text
00_authoring/SKILL.md
→ references/task_execution_rules.md
→ references/canonical_terminology.md
→ references/result_generation_rules.md
→ 本文件
→ current 1.2 results interface
→ current 2.5 SKILL.md / results interface / 与本检查直接相关的 2.5 references
```

旧 `WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md` 不得作为 2.6 具体检查规则的 generation source；如果为了 Stage-level architecture 需要读取该文件，只读取仍由它拥有且未被 current authority 取代的 Stage-level 内容。

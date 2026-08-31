# 拓扑终检正式结果

## 正式结果入口

当前工作项只生成：

`topology_validation_result.yaml`

作为本次 topology validation 的正式结果记录。

该 YAML 保存当前 `target_id`、实际文件引用和六项检查结果。它不保存 `PASS`、`FAIL`、`COMPLETE`、
`result_status`、overall conclusion 或 blocking finding。

结果文件和依赖文件路径遵守仓库级结果生成规则的完整绝对路径语义。

## `references`

`references` 同时记录两个直接正式依赖，并为结果中反复引用的当前结构文件和拓扑文件提供公共路径引用：

```yaml
references:
  CLASSIFICATION_RESULT: /absolute/path/to/classification_result.yaml
  TOPOLOGY_INTEGRATION_RESULT: /absolute/path/to/topology_integration_result.yaml
  STRUCTURE: /absolute/path/to/actual_structure_file.gro
  MAP: /absolute/path/to/actual_map_file
  TOP: /absolute/path/to/actual_system_topology.top
  ITP_1: /absolute/path/to/first_actual_itp
  ITP_2: /absolute/path/to/second_actual_itp
```

规则：

- `STRUCTURE`、`MAP` 和 `TOP` 分别使用 `topology_integration_result.yaml` 中实际记录的结构文件、map 和
  体系 `.top` 路径；
- `ITP_n` 按 `topology_integration_result.yaml.results.itp` 中的实际顺序逐项记录；
- 实际不存在的可选 `.itp` 不建立占位 key；
- 不根据任何默认 basename 推断实际文件名；
- `${PATH_KEY}` 展开后必须具有完整绝对路径语义。

## 顶层结构

```yaml
target_id: target_001

references:
  # 按上一节记录

check_results:
  top_includes: []
  structure_topology: {}
  topology_linked_relations: []
  standard_atom_deletions: []
  standard_side_charge_modifications: []
  grompp: {}
```

六个 `check_results` 字段均保留。当前工作项只有完成全部六项检查后才生成正式结果，因此各空数组表示已经完成
对应检查但没有发现该类记录或差异，不表示该检查尚未执行。

## `top_includes`

体系 `.top` 中每个实际 `#include` 建立一条记录：

```yaml
top_includes:
  - include_value: "molecule_1.itp"
    resolved_path: ${ITP_1}
    exists: true
    readable: true

  - include_value: "forcefield.itp"
    resolved_path: /absolute/path/to/forcefield.itp
    exists: true
    readable: true
```

字段语义：

- `include_value`：`#include` 中实际写出的文件表达；
- `resolved_path`：解析得到的实际完整路径；无法形成实际路径时为 `null`；
- `exists`：解析路径指向的文件是否存在；
- `readable`：该文件是否可读取；文件不存在时记录 `false`。

本项不记录 line number，也不递归登记 `.itp` 内部的 `#include`。

## `structure_topology`

本项记录当前结构文件的 residue / atom 数量，以及按体系 `.top [ molecules ]` 和对应
`moleculetype [ atoms ]` 展开的拓扑规模：

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

`topology_molecule_count` 是体系 `.top [ molecules ]` 按数量展开后的 molecule instance 总数；
`topology_residue_count` 和 `topology_atom_count` 是全部 molecule instance 展开后的总数。

不为没有差异的普通 molecule、residue 或 atom 逐项生成记录。每个实际差异按所在数组记录能够定位问题的字段：

- `moleculetype`；
- `molecule_instance`；
- 适用时的 `residue_index_in_molecule`；
- 适用时的 `atom_index_in_molecule`；
- `structure` 下的结构文件实际位置和值；
- `topology` 下的拓扑文件实际位置和值。

例如 atom name 差异：

```yaml
atom_name_differences:
  - moleculetype: molecule_1
    molecule_instance: 1
    residue_index_in_molecule: 42
    atom_index_in_molecule: 652

    structure:
      atom_number: 652
      residue_number: 42
      residue_name: CYS
      atom_name: SG

    topology:
      file: ${ITP_1}
      atom_nr: 652
      resnr: 42
      residue_name: CYS
      atom_name: S
```

其它差异数组只记录与该差异类型相关的位置和值；不适用的定位字段省略。

## `topology_linked_relations`

对 `classification_result.yaml.topology_linked_checks` 中每条同时满足：

```text
judgment = CONFIRMED
且
topology_effect_applied = true
```

的关系建立一条记录。

### `COVALENT_CONNECTION`

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

### `METAL_COORDINATION`

保持分类正式结果中的 `metal` 和 `donor` 端点语义：

```yaml
  - relation_id: relation_002
    relation_type: METAL_COORDINATION

    metal:
      component_id: component_002
      residue_id: residue_001
      atom_name: FE
      moleculetype: molecule_1
      atom_nr: 1860

    donor:
      component_id: component_001
      residue_id: residue_078
      atom_name: NE2
      moleculetype: molecule_1
      atom_nr: 1198

    topology_entries:
      - file: ${ITP_1}
        moleculetype: molecule_1
        section: <actual_section>
        line_number: 810
        atom_nrs: [1860, 1198]
        entry: "<actual topology entry>"
```

`topology_entries` 记录对应 topology-linked 参数化结果中针对该关系形成、并由拓扑整合写入最终拓扑的实际条目。
完成检索但未找到对应条目时记录：

```yaml
topology_entries: []
```

不另设 `topology_effect_found`、`status` 或其它二次判断字段。

## `standard_atom_deletions`

按当前拓扑整合实际采用的 topology-linked 参数化正式结果分组：

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

`structure_matches` 记录当前结构文件中实际找到的对应 atom：

```yaml
structure_matches:
  - atom_number: 653
    residue_number: 42
    residue_name: CYS
    atom_name: HG
```

`topology_matches` 记录最终拓扑文件中对应 `moleculetype [ atoms ]` 实际找到的对应 atom：

```yaml
topology_matches:
  - file: ${ITP_1}
    moleculetype: molecule_1
    atom_nr: 653
    resnr: 42
    residue_name: CYS
    atom_name: HG
```

未找到对应 atom 时保留空数组，不另设 `deleted`、`status` 或其它判断字段。

## `standard_side_charge_modifications`

检查过程逐 atom 核对，正式结果只按 residue 记录：

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

- `source_result`：本组检查采用的 topology-linked 参数化正式结果完整路径；
- `residue_count`：本组实际检查的标准残基数量；
- `checked_atom_count`：对应 residue 中实际完成电荷核对的 atom 数量；
- `charge_difference_count`：参数化结果指定电荷与最终拓扑文件对应 `[ atoms ] charge` 不同的 atom 数量。

本项不记录 atom name、指定电荷值或最终拓扑电荷值。

## `grompp`

只记录实际执行事实：

```yaml
grompp:
  gromacs_version: "GROMACS 2022.2"
  command: >
    gmx grompp -f /absolute/path/to/grompp_validation.mdp
    -c ${STRUCTURE}
    -p ${TOP}
    -o /absolute/path/to/temporary.tpr
  return_code: 0
  notes: []
  warnings: []
  errors: []
```

- `gromacs_version`：本次实际调用的版本；
- `command`：实际执行命令，包括本次采用的 `.mdp` 和输出路径；
- `return_code`：实际进程返回码；
- `notes`、`warnings`、`errors`：分别保存 `gmx grompp` 的实际对应输出。

不记录 `preprocessing_succeeded`、`status` 或其它二次结论字段。

## 项目结果索引登记

项目结果索引只登记：

`topology_validation_result.yaml`

当前结构文件、map、体系 `.top`、`.itp`、检查用 `.mdp`、临时 `.tpr`、debug、scratch 和 cache 均不作为
当前职责的新结果重复登记。

## 工作项完成条件

完成全部六项检查并生成 `topology_validation_result.yaml` 后，当前工作项完成。

检查中发现的问题继续保留在正式结果中；问题是否要求重新进入其它拓扑准备工作项，不改变当前工作项已经完成检查
并生成正式结果这一事实。

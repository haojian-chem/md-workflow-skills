# 拓扑整合正式结果

## 正式结果入口

当前工作项生成：

`topology_integration_result.yaml`

作为本次拓扑整合的正式结果记录。

该记录保存：

- 当前 `target_id`；
- 本次实际使用的上游 / 外部文件引用；
- 整合后的 `moleculetype` 组成；
- 体系整合 `.gro`；
- `integrated.map`；
- 体系主 `.top`；
- 本次实际生成的全部 `.itp`。

结果文件与依赖文件路径遵守仓库级结果生成规则的完整绝对路径语义。

## `references`

`references` 记录本次拓扑整合实际使用的上游 / 外部正式文件，并作为当前结果记录内部的文件引用。

基础文件使用：

```yaml
references:
  BASIS_1: /absolute/path/to/classification_result.yaml
  STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  MAP_1: /absolute/path/to/stage1_final_map.yaml
```

每个 Task Sheet 指定的标准残基拓扑生成工作项使用一组 `STD_n_*`：

```yaml
STD_1_RESULT: /absolute/path/to/standard_residue_topology_result.yaml
STD_1_STRUCTURE: /absolute/path/to/standard.gro
STD_1_MAP: /absolute/path/to/standard.map
STD_1_TOP: /absolute/path/to/standard.top
STD_1_ITP_1: /absolute/path/to/chain_1.itp
STD_1_ITP_2: /absolute/path/to/chain_2.itp
```

其中 `n` 是当前类别中的前置工作项序号；同一正式结果包含多个 `.itp` 时，以 `STD_n_ITP_m` 逐项记录，
`m` 是该正式结果中的 `.itp` 序号。

每个 Task Sheet 指定的 topology-linked 非标准残基参数化工作项使用一组 `LINKED_n_*`：

```yaml
LINKED_1_RESULT: /absolute/path/to/topology_linked_parameterization_result.yaml
LINKED_1_MODEL: /absolute/path/to/parameterization_model.mol2
LINKED_1_MODEL_MAP: /absolute/path/to/parameterization_model.map
LINKED_1_CHARGE: /absolute/path/to/parameterization.chg
LINKED_1_CHARGE_RESULT: /absolute/path/to/charge_fitting_result.yaml
LINKED_1_STRUCTURE: /absolute/path/to/parameterized_structure.gro
LINKED_1_TOPO: /absolute/path/to/parameterized_topology.itp
```

每个 Task Sheet 指定的独立非标准参数化工作项使用一组 `IND_n_*`：

```yaml
IND_1_RESULT: /absolute/path/to/independent_nonstandard_parameterization_result.yaml
IND_1_MODEL: /absolute/path/to/parameterization_model.mol2
IND_1_MODEL_MAP: /absolute/path/to/parameterization_model.map
IND_1_CHARGE: /absolute/path/to/parameterization.chg
IND_1_CHARGE_RESULT: /absolute/path/to/charge_fitting_result.yaml
IND_1_TOPO: /absolute/path/to/parameterized_topology.itp
IND_1_STRUCTURE: /absolute/path/to/parameterized_structure.gro
IND_1_STRUCTURE_MAP: /absolute/path/to/parameterized_structure.map
```

无需独立参数化、由当前体系直接采用的 solvent / ion 拓扑定义文件使用 `DIRECT_n_TOPOLOGY` 逐项记录：

```yaml
DIRECT_1_TOPOLOGY: /absolute/path/to/direct_solvent_or_ion_topology
```

同一实际文件只建立一个 reference key。实际不存在的工作项、文件或直接拓扑定义不建立占位条目。

`references` 只展开到当前拓扑整合实际使用的正式文件；不因为引用某个上游正式结果而递归复制其完整上游依赖记录。

## `moleculetypes`

`moleculetypes` 按当前整合后的 `moleculetype` 组织顺序记录每个 `moleculetype` 包含的 residue。

每个 residue 使用既有 `component_id + residue_id` 定位：

```yaml
moleculetypes:
  - name: molecule_1
    residues:
      - component_id: component_001
        residue_id: residue_001-residue_120
      - component_id: component_002
        residue_id: residue_001

  - name: molecule_2
    residues:
      - component_id: component_003
        residue_id: residue_001
```

同一 `component_id` 下连续的 residue 可以使用 `residue_id: <start>-<end>` 压缩记录。该范围表示该 component
正式 residue 顺序中的连续区间，不通过 `residue_id` 字符串重新计算 residue identity。

不连续的 residue 分开记录。同一个 `moleculetype` 同时包含标准残基与非标准残基时，记录顺序与实际组织顺序一致，
标准残基在前、非标准残基在后。

## `results`

当前工作项实际生成的结构、map、主 topology 与全部 `.itp` 统一登记在 `results`：

```yaml
results:
  structure: /absolute/path/to/sys.gro
  map: /absolute/path/to/integrated.map
  top: /absolute/path/to/sys.top
  itp:
    - /absolute/path/to/parameters.itp
    - /absolute/path/to/molecule_1.itp
    - /absolute/path/to/posre_molecule_1.itp
    - /absolute/path/to/molecule_2.itp
    - /absolute/path/to/posre_molecule_2.itp
```

`results.structure` 记录本次实际生成的体系整合 `.gro`；其默认 basename 为 `sys.gro`。

`results.itp` 只列出本次拓扑整合实际生成的 `.itp`。不存在的文件不建立占位条目；若本次没有生成
`parameters.itp`，列表中不写该路径。

无需独立参数化、直接采用的 solvent / ion topology 属于本次整合的外部定义，记录在 `references`，
不作为当前工作项生成的 `.itp` 写入 `results.itp`。

默认 basename 为：

```text
sys.gro
integrated.map
sys.top
<moleculetype name>.itp
posre_<moleculetype name>.itp
parameters.itp            # 仅在本次实际生成时存在
```

## 完整结构

正式结果记录按实际输入数量扩展 `references` 中的同类 key；下列结构用于说明顶层字段关系：

```yaml
target_id: target_001

references:
  BASIS_1: /absolute/path/to/classification_result.yaml
  STRUCTURE_1: /absolute/path/to/stage1_final.pdb
  MAP_1: /absolute/path/to/stage1_final_map.yaml

  STD_1_RESULT: /absolute/path/to/standard_residue_topology_result.yaml
  STD_1_STRUCTURE: /absolute/path/to/standard.gro
  STD_1_MAP: /absolute/path/to/standard.map
  STD_1_TOP: /absolute/path/to/standard.top
  STD_1_ITP_1: /absolute/path/to/chain_1.itp

  LINKED_1_RESULT: /absolute/path/to/topology_linked_parameterization_result.yaml
  LINKED_1_MODEL: /absolute/path/to/parameterization_model.mol2
  LINKED_1_MODEL_MAP: /absolute/path/to/parameterization_model.map
  LINKED_1_CHARGE: /absolute/path/to/parameterization.chg
  LINKED_1_CHARGE_RESULT: /absolute/path/to/charge_fitting_result.yaml
  LINKED_1_STRUCTURE: /absolute/path/to/parameterized_structure.gro
  LINKED_1_TOPO: /absolute/path/to/parameterized_topology.itp

moleculetypes:
  - name: molecule_1
    residues:
      - component_id: component_001
        residue_id: residue_001-residue_120
      - component_id: component_002
        residue_id: residue_001

results:
  structure: /absolute/path/to/sys.gro
  map: /absolute/path/to/integrated.map
  top: /absolute/path/to/sys.top
  itp:
    - /absolute/path/to/parameters.itp
    - /absolute/path/to/molecule_1.itp
    - /absolute/path/to/posre_molecule_1.itp
```

`target_id` 直接使用当前 Task Sheet 中的 `target_id`。

## 项目结果索引登记

当前工作项完成后，将下列正式结果的完整路径登记到项目结果索引：

- `topology_integration_result.yaml`；
- 实际生成的体系整合 `.gro`；
- `integrated.map`；
- 实际生成的体系主 `.top`；
- 本次实际生成的全部 `.itp`。

上游正式结果、基础力场文件、直接采用的 solvent / ion topology 和其它外部参数定义不作为当前工作项生成的
正式结果重复登记。

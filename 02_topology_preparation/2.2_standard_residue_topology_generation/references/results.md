# 2.2 正式结果记录

## 正式结果记录

当前工作项生成：

```text
standard_residue_topology_result.yaml
```

作为当前 2.2 工作项的正式结果记录。

该记录至少保存：

- 本次实际依赖的上游文件；
- 本次实际使用的力场及其它参数定义来源；
- pdb2gmx 实际使用的输入 PDB；
- 实际执行的 pdb2gmx 命令；
- pdb2gmx 执行过程中实际采用的选择；
- 当前工作项生成的正式结果文件。

结果记录中的依赖文件和结果文件均使用完整绝对路径。

## 正式结果文件

正式结果文件包括：

```text
2.2_standard_structure.gro
2.2_standard.map
2.2_standard.top
每条 chain 对应的独立 .itp
standard_residue_topology_result.yaml
```

`2.2_standard_structure.gro` 与 `2.2_standard.map` 的 basename 固定。

`2.2_standard.top` 作为标准残基 topology 的主入口。
各 chain `.itp` 的实际文件路径由 `2.2_standard.top` 中的 `#include` 关系确定，
并在正式结果记录中逐项列出。

## 结果记录内容

正式结果记录按下述语义保存信息：

```yaml
dependencies:
  stage1_structure: /absolute/path/to/stage1_final.pdb
  stage1_map: /absolute/path/to/stage1_final_map.yaml
  classification_result: /absolute/path/to/classification_result.yaml
  parameter_definition_sources:
    - /absolute/path/to/force_field_or_parameter_source

pdb2gmx:
  input_structure: /absolute/path/to/pdb2gmx_input.pdb
  command: <实际执行的完整命令>
  selections:
    - <实际采用的选择 1>
    - <实际采用的选择 2>

results:
  structure: /absolute/path/to/2.2_standard_structure.gro
  map: /absolute/path/to/2.2_standard.map
  topology:
    top: /absolute/path/to/2.2_standard.top
    itp:
      - /absolute/path/to/chain_1.itp
      - /absolute/path/to/chain_2.itp
```

`parameter_definition_sources` 只记录本次实际使用的来源，不把未采用的候选来源写入正式结果记录。

`pdb2gmx.command` 记录实际执行的完整命令。
`pdb2gmx.selections` 按实际执行情况记录会影响本次 topology 生成的选择，
包括各 chain 的端基选择及其它实际发生的交互选择。

`results.topology.itp` 只列出当前工作项生成、并由 `2.2_standard.top` 引用的各 chain 分子拓扑文件。
力场自身已有的 include 文件属于依赖，不作为当前工作项生成的 `.itp` 结果重复登记。

## 项目结果索引登记

当前工作项完成后，将以下正式结果文件的完整路径登记到项目结果索引：

- `standard_residue_topology_result.yaml`；
- `2.2_standard_structure.gro`；
- `2.2_standard.map`；
- `2.2_standard.top`；
- `2.2_standard.top` 实际引用的每个 chain `.itp`。

项目结果索引只登记上述正式结果文件；pdb2gmx 输入 PDB、日志、临时文件及力场/参数定义依赖文件不作为当前工作项的正式结果登记。

# System construction / solvation 正式结果

## 正式结果入口

当前职责生成：

`system_construction_result.yaml`

该 YAML 用于定位本次实际采用的上游正式结果、实际执行并保留结果的体系构建操作，以及最终结构文件和体系主 `.top`。

结果文件与依赖文件路径遵守仓库级结果生成规则的完整绝对路径语义。

## `references`

`references` 记录本次结果实际依赖的上游正式结果：

```yaml
references:
  INTEGRATION: /absolute/path/to/topology_integration_result.yaml
  VALIDATION: /absolute/path/to/topology_validation_result.yaml
```

其中：

- `INTEGRATION` 记录本次实际采用的 `topology_integration_result.yaml`；
- `VALIDATION` 只在本次体系构建实际读取并分析了对应 `topology_validation_result.yaml` 时记录；
- 实际不存在的引用不建立占位；
- `references` 不递归复制上游正式结果自己的完整依赖链。

## `results.operations`

`results.operations` 按当前 Task 中的实际执行顺序记录已执行、且结果需要由当前正式结果继续定位的操作。

每项只记录实际存在的字段：

```yaml
- directory: /absolute/path/to/01_periodic_box_construction
  type: periodic_box_construction
  structure: /absolute/path/to/actual_boxed_structure.gro

- directory: /absolute/path/to/02_solvent_addition
  type: solvent_addition
  structure: /absolute/path/to/actual_solvated_structure.gro
  top: /absolute/path/to/actual_solvated_system.top

- directory: /absolute/path/to/03_ion_addition
  type: ion_addition
  structure: /absolute/path/to/actual_ionized_structure.gro
  top: /absolute/path/to/actual_ionized_system.top
```

`type` 当前使用：

```text
periodic_box_construction
solvent_addition
ion_addition
```

字段语义：

- `directory`：该实际操作的完整工作目录；
- `type`：操作类型；
- `structure`：该操作实际生成并继续保留的结构文件；
- `top`：该操作实际生成或修改并继续保留的体系主 `.top`。

没有由当前操作生成或修改的结果字段不建立占位。例如周期盒构建只产生新结构而体系主 `.top` 未改变时，该操作不写 `top`。

实际命令参数、溶剂模型、离子组成和其它执行设置由当前 Task Sheet 中的操作计划维护，不复制到正式结果中。

## `results.final`

`results.final` 记录体系构建完成后实际采用的最终结构文件和体系主 `.top`：

```yaml
results:
  final:
    structure: /absolute/path/to/actual_final_structure.gro
    top: /absolute/path/to/actual_final_system.top
```

`results.final.structure` 与 `results.final.top` 不要求必须由最后一个操作新生成；如果其中一个文件在本次体系构建中没有发生改变，可以继续指向实际采用的上游文件。

## 完整结构示例

```yaml
references:
  INTEGRATION: /absolute/path/to/topology_integration_result.yaml
  VALIDATION: /absolute/path/to/topology_validation_result.yaml

results:
  operations:
    - directory: /absolute/path/to/01_periodic_box_construction
      type: periodic_box_construction
      structure: /absolute/path/to/actual_boxed_structure.gro

    - directory: /absolute/path/to/02_solvent_addition
      type: solvent_addition
      structure: /absolute/path/to/actual_solvated_structure.gro
      top: /absolute/path/to/actual_solvated_system.top

    - directory: /absolute/path/to/03_ion_addition
      type: ion_addition
      structure: /absolute/path/to/actual_ionized_structure.gro
      top: /absolute/path/to/actual_ionized_system.top

  final:
    structure: /absolute/path/to/actual_final_structure.gro
    top: /absolute/path/to/actual_final_system.top
```

`VALIDATION` 为条件字段；本次未实际读取对应拓扑终检正式结果时删除该条目。

## 结果记录检查

生成正式结果时确认：

- `results.operations` 顺序与当前 Task Sheet 中的实际执行历史一致；
- `directory`、`structure`、`top` 使用实际完整绝对路径；
- `results.final.structure` 和 `results.final.top` 指向当前完成状态实际采用的文件；
- 没有为未生成的文件建立占位字段。

## 项目结果索引

当前职责登记到项目结果索引的正式结果只有：

`system_construction_result.yaml`

登记文件固定为：

`<project_root>/00_project_records/project_result_index.md`

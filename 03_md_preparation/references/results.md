# System construction / solvation 正式结果

## 正式结果入口

每个 current Stage 3 local target 生成：

`system_construction_result.yaml`

该 YAML 用于定位 current target、实际采用的上游正式结果、实际执行并保留结果的体系构建操作，以及最终结构文件和体系主 `.top`。

结果文件与依赖文件路径遵守仓库级结果生成规则的完整绝对路径语义。

## `references`

`references` 首先记录 current Stage 3 target record，再记录本次结果实际依赖的上游正式结果：

```yaml
target_id: target_001

references:
  target_record: /absolute/path/to/current/Stage3/targets/target_001.yaml
  INTEGRATION: /absolute/path/to/topology_integration_result.yaml
  VALIDATION: /absolute/path/to/topology_validation_result.yaml
```

其中：

- `target_id` 只在当前 Stage 3 工作项 / 当前结果内部定位 local target；
- `references.target_record` 指向 current Stage 3 target record；
- `INTEGRATION` 记录本次实际采用的 `topology_integration_result.yaml`，仅在 current target 直接以该 integration result 作为 source system 或实际依赖时记录；
- `VALIDATION` 只在本次体系构建实际读取并分析了对应 `topology_validation_result.yaml` 时记录；
- `VALIDATION` 默认是 validation evidence，其 2.6 target 不自动进入 current Stage 3 target record 的 `source_target_records`；
- current target 如果从已有 Stage 3 formal result 继续构建，应记录该 actual source result / files，并让 current target record 的 `source_target_records` 指向前序 Stage 3 target；此时不要求继续把 2.5 integration target 作为 current direct source；
- 上游正式结果可以来自当前 Task Sheet、同一科研任务的前序 Task Sheet或其它明确可用的正式结果；这里只记录本次实际采用的完整路径；
- 实际不存在的引用不建立占位；
- `references` 不递归复制上游正式结果自己的完整依赖链或 target ancestry。

Current Stage 3 target 的直接 target lineage 由 `references.target_record` 所指文件的 `source_target_records` 定义。不得通过 `INTEGRATION` / `VALIDATION` 结果里的 `target_id` 编号推断对应关系。

## `results.operations`

`results.operations` 按 current Stage 3 target 的实际执行顺序记录已执行、且结果需要由当前正式结果继续定位的操作。

每项只记录实际存在的字段：

```yaml
- directory: /absolute/path/to/01_periodic_box_construction
  operation_type: periodic_box_construction
  structure: /absolute/path/to/actual_boxed_structure.gro

- directory: /absolute/path/to/02_solvent_addition
  operation_type: solvent_addition
  structure: /absolute/path/to/actual_solvated_structure.gro
  top: /absolute/path/to/actual_solvated_system.top

- directory: /absolute/path/to/03_ion_addition
  operation_type: ion_addition
  structure: /absolute/path/to/actual_ionized_structure.gro
  top: /absolute/path/to/actual_ionized_system.top
```

`operation_type` 当前使用：

```text
periodic_box_construction
solvent_addition
ion_addition
```

字段语义：

- `directory`：该实际操作的完整工作目录；
- `operation_type`：操作类型；
- `structure`：该操作实际生成并继续保留的结构文件；
- `top`：该操作实际生成或修改并继续保留的体系主 `.top`。

没有由当前操作生成或修改的结果字段不建立占位。例如周期盒构建只产生新结构而体系主 `.top` 未改变时，该操作不写 `top`。

Operations 是 current target 内部的执行历史，不自动成为独立 target records。只有某个 Stage 3 状态已经作为正式 Stage 3 target/result 形成，并在后续工作中成为新的 source execution object 时，才通过 target lineage 记录为 source target。

## `results.final`

`results.final` 记录 current target 体系构建完成后实际采用的最终结构文件和体系主 `.top`：

```yaml
results:
  final:
    structure: /absolute/path/to/actual_final_structure.gro
    top: /absolute/path/to/actual_final_system.top
```

`results.final.structure` 与 `results.final.top` 不要求必须由最后一个操作新生成；如果其中一个文件在本次体系构建中没有发生改变，可以继续指向实际采用的上游文件。

## 完整结构示例

```yaml
target_id: target_001

references:
  target_record: /absolute/path/to/current/Stage3/targets/target_001.yaml
  INTEGRATION: /absolute/path/to/topology_integration_result.yaml
  VALIDATION: /absolute/path/to/topology_validation_result.yaml

results:
  operations:
    - directory: /absolute/path/to/01_periodic_box_construction
      operation_type: periodic_box_construction
      structure: /absolute/path/to/actual_boxed_structure.gro

    - directory: /absolute/path/to/02_solvent_addition
      operation_type: solvent_addition
      structure: /absolute/path/to/actual_solvated_structure.gro
      top: /absolute/path/to/actual_solvated_system.top

    - directory: /absolute/path/to/03_ion_addition
      operation_type: ion_addition
      structure: /absolute/path/to/actual_ionized_structure.gro
      top: /absolute/path/to/actual_ionized_system.top

  final:
    structure: /absolute/path/to/actual_final_structure.gro
    top: /absolute/path/to/actual_final_system.top
```

`VALIDATION` 为条件字段；本次未实际读取对应拓扑终检正式结果时删除该条目。

## 结果记录检查

生成正式结果时确认：

- `references.target_record` 能定位 current Stage 3 local target；
- current target record 的 `source_target_records` 与实际 source system target(s) 一致；
- 如果 current target 直接来源于 2.5，`INTEGRATION.references.target_record` 能在 current `source_target_records` 中定位；
- 如果 current target 从前序 Stage 3 result 继续，则 current source target 指向真实前序 Stage 3 target，不机械回指 2.5；
- `VALIDATION` 如存在，只作为实际读取的 validation evidence，除非当前特殊对象关系另有明确理由，不加入 source targets；
- `results.operations` 顺序与当前 target 的实际执行历史一致；
- `directory`、`structure`、`top` 使用实际完整绝对路径；
- `results.final.structure` 和 `results.final.top` 指向当前完成状态实际采用的文件；
- 没有为未生成的文件建立占位字段；
- 不通过 local `target_id` 比较建立 lineage。

## 项目结果索引

当前职责登记到项目结果索引的正式结果只有各 current target 的：

`system_construction_result.yaml`

登记文件固定为：

`<project_root>/00_project_records/project_result_index.md`

Target record 是 lineage support record，不因为创建而单独登记。

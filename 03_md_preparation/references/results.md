# System construction / solvation 正式结果

## 正式结果入口

当前职责生成唯一正式结果记录：

`system_construction_result.yaml`

该 YAML 用于定位本次实际采用的上游拓扑整合正式结果、实际执行并保留结果的体系构建 operations，以及最终结构文件和体系主 `.top`。

结果文件与依赖文件路径遵守仓库级 `references/result_generation_rules.md` 的完整绝对路径语义。

## `references`

`references` 记录本次结果实际依赖的上游正式结果：

```yaml
references:
  INTEGRATION: /absolute/path/to/topology_integration_result.yaml
  VALIDATION: /absolute/path/to/topology_validation_result.yaml
```

规则：

- `INTEGRATION` 必须记录本次实际采用的 `topology_integration_result.yaml`；
- `VALIDATION` 只在本次体系构建实际读取并分析了对应 `topology_validation_result.yaml` 时记录；
- 未实际读取 topology validation 正式结果时，不建立 `VALIDATION` 占位；
- `references` 不递归复制上游正式结果自己的完整依赖链。

## `results.operations`

`results.operations` 按当前 Task 中的实际执行顺序记录已经执行、且其结果需要由当前正式结果继续定位的 operations。

每项只使用以下字段中的实际需要项：

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

`type` 当前只允许：

```text
periodic_box_construction
solvent_addition
ion_addition
```

字段语义：

- `directory`：该实际 operation 的完整工作目录；
- `type`：该 operation 的类型；
- `structure`：该 operation 实际生成并继续保留的结构文件；
- `top`：该 operation 实际生成或修改并继续保留的体系主 `.top`。

没有由当前 operation 生成或修改的结果字段不建立占位。例如周期盒构建只产生新结构而体系主 `.top` 未改变时，该 operation 不写 `top`。

`results.operations` 只表达实际形成的 operation 结果，不复制 Task Sheet 中的完整 operation settings。实际命令参数、solvent template、离子组成、replacement group 等恢复信息由 Task Sheet 当前 operation plan 维护。

若当前体系已经满足 Task Sheet 的体系构建目标而无需执行新的 operation，允许 `results.operations` 为空列表；`results.final` 仍必须明确记录最终采用的结构文件和体系主 `.top`。

## `results.final`

`results.final` 固定记录当前体系构建完成后实际采用的最终状态：

```yaml
results:
  final:
    structure: /absolute/path/to/actual_final_structure.gro
    top: /absolute/path/to/actual_final_system.top
```

`results.final.structure` 与 `results.final.top` 不要求必须由最后一个 operation 新生成；如果某一侧在当前体系构建过程中没有发生改变，可以继续指向实际采用的上游文件。

这里记录的是最终实际文件身份，不根据默认 basename 推断。

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

`VALIDATION` 为条件字段；本次未实际读取 topology validation 正式结果时，从示例中删除该条目。

## 内部一致性

生成正式结果时确认：

- `results.operations` 顺序与 Task Sheet 中实际执行历史一致；
- 每个 `directory`、`structure`、`top` 都使用实际完整绝对路径；
- `results.final.structure` 和 `results.final.top` 指向当前完成状态实际采用的文件；
- 最终体系主 `.top` 所需的拓扑 / 参数依赖仍可解析；
- 没有为未生成的文件建立占位字段；
- `genion.mdp`、`.tpr`、临时文件和仅用于执行的中间文件不混入正式结果字段。

## 项目结果索引

项目结果索引只登记：

`system_construction_result.yaml`

不单独登记：

- operation directory；
- 各 operation 的 `.gro`；
- 各 operation 的 `.top`；
- 最终 `.gro`；
- 最终 `.top`；
- `genion.mdp`；
- `.tpr`；
- 其它临时执行文件。

这些文件通过 `system_construction_result.yaml` 和当前 Task Sheet 定位。

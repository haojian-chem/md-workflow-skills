---
name: topology_validation
description: 对 Task Sheet 当前 topology validation 工作项指定的处理对象建立 2.6 local validation target，执行独立、只读终检，检查体系 .top 引用、结构与拓扑逐项对应、position restraint、topology-linked 关系、标准残基原子删除与电荷修改，并使用 gmx grompp 检查 GROMACS 预处理结果，生成 topology_validation_result.yaml。
---

# Topology validation

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 目标

对当前 2.6 local target 指定的 topology integration result 执行独立、只读终检：

```text
检查体系 .top 中的 #include
→ 检查结构文件与 .top / .itp 中的分子、残基和原子及 position restraint 条目
→ 检查 topology-linked 关系
→ 检查标准残基原子删除
→ 检查标准残基一侧电荷修改
→ 执行 gmx grompp
→ 生成 topology_validation_result.yaml
```

当前职责只检查已经形成的结构文件和拓扑文件，不修改结构文件、体系 `.top`、`.itp`、map、参数文件或 source target record，也不在发现问题时顺手修正拓扑。

## Target object and lineage

当前工作项使用 `target` 作为 validation execution object，因此每个 actual 2.6 local target 建立自己的：

```text
targets/target_xxx.yaml
```

正常情况下，当前 2.6 target record 的 `source_target_records` 包含本次实际检查的 **2.5 integration target record**。

注意：

- `topology_integration_result.yaml.references.target_record` 指向 source 2.5 target；
- `integrated.map.target_record` 同样指向 source 2.5 target；
- `topology_validation_result.yaml.references.target_record` 指向 **current 2.6 target**；
- current 2.6 target record 通过 `source_target_records` 指向被检查的 2.5 target。

2.6 是只读检查，因此不把 source `integrated.map.target_record` 改写成 2.6 target，也不要求二者相同。

当前 2.6 `target_id` 只在当前工作项内解释，不继承 2.5 编号。

## 输入与依据

当前工作项的处理对象由 Task Sheet 确定。执行时至少读取：

1. current 2.6 target record；
2. `classification_result.yaml`；
3. `topology_integration_result.yaml`；
4. `topology_integration_result.yaml.references.target_record` 指向的 2.5 source target record。

`classification_result.yaml` 提供既有的 `component_id + residue_id`、`topology_class` 和 `topology_linked_checks`。需要解释这些字段时读取：

`../../01_structure_preparation/1.2_component_and_residue_classification/references/result_recording_rules.md`

`topology_integration_result.yaml` 用于定位当前工作项实际检查的结构文件、map、体系 `.top`、本次拓扑整合生成的 `.itp`、`moleculetypes`，以及当前拓扑整合实际采用的 topology-linked 参数化正式结果。需要解释该结果的 `references`、`moleculetypes` 和 `results` 时读取：

`../2.5_topology_integration_and_assembly/references/results.md`

需要解释 topology-linked 参数化正式结果中的 `standard_atom_deletions` 和 `charge_modification_scope` 时读取：

`../2.3_topology_linked_nonstandard_parameterization/references/topology_linked_parameterization_result.md`

全部检查均限定在 current 2.6 target 所指向的 source 2.5 integration object 内。读取 `classification_result.yaml` 时，只消费能够映射到该 integration object 的 residue 身份、`topology_class` 和 `topology_linked_checks`；不要求同一 model 中未进入当前对象的其它 residue 或 topology-linked 关系出现在当前拓扑中。

当前使用的 `classification_result.yaml` 必须是拓扑整合正式结果实际引用的分类正式结果。结构文件、map、体系 `.top` 和 `.itp` 均使用 `topology_integration_result.yaml` 中记录的实际完整路径，不根据默认 basename、目录顺序或“最新文件”重新推断。

Current 2.6 target record 的 `source_target_records` 必须能定位 `topology_integration_result.yaml.references.target_record`；不得根据两个结果中的 `target_id` 是否相同判断对应关系。

若两个直接正式依赖，或当前结构文件、map、体系 `.top` 不能唯一定位或读取，不伪造依赖这些文件的检查结果；先解决对应的输入定位问题，再执行相关检查。体系 `.top` 中 `#include` 指向的文件缺失或不可读取，属于 `top_includes` 应记录的实际检查结果，不在开始该项检查前将这些问题作为输入条件排除。

## No reuse

当前职责不设置 reuse。

每次实际进入当前工作项，都针对 current 2.6 target、当前 `classification_result.yaml`、当前 `topology_integration_result.yaml` 及其记录的结构文件和拓扑文件重新执行全部规定检查；不使用既有 `topology_validation_result.yaml` 跳过本次检查。

## 工作目录

当前 Task Sheet 的 2.6 工作目录使用：

```text
<current_2.6_task_work_directory>/
├── targets/
│   ├── target_001.yaml
│   ├── target_002.yaml
│   └── ...
├── target_001/
│   └── topology_validation_result.yaml
└── ...
```

当前 Task Sheet 可以只验证 2.5 integration targets 的一个子集，不要求 2.6 target 数量或编号与 2.5 相同。

## 检查体系 `.top` 中各 `#include` 指向的文件

读取体系 `.top` 中实际出现的每个 `#include`，解析其实际文件路径，并分别检查该文件是否存在、是否可读取。

本项只检查体系 `.top` 中直接写出的 `#include` 所指文件，不在本项中检查参数内容、`moleculetype` 定义或其它拓扑语义。

## 检查当前结构文件与体系 `.top` / `.itp`

### 分子、残基和原子

按体系 `.top` 的 `[ molecules ]` 中记录的 `moleculetype` 顺序和数量，读取对应 `moleculetype` 的 `[ atoms ]`，展开当前拓扑所描述的分子、残基和原子顺序。

将展开结果与当前结构文件逐项比较，检查：

- 分子数量；
- 分子顺序；
- 每个分子的原子数量；
- residue 顺序；
- atom 顺序；
- 对应位置的 residue name；
- 对应位置的 atom name。

发现差异时，记录对应 `moleculetype`、分子实例、结构文件位置、拓扑文件位置以及两侧实际值。

### Position restraint

读取体系 `.top` 和最终各 `moleculetype` `.itp` 中通过条件 `#include` 引用的 position restraint `.itp`。

对每个 position restraint 文件，将 `[ position_restraints ]` 中引用的 atom nr 与对应 `moleculetype [ atoms ]` 比较，确认：

- 对应 `moleculetype` 中的全部重原子均施加了 position restraint；
- `[ position_restraints ]` 中没有对氢原子施加 position restraint。

该内容属于本项对 `.itp` 的检查，不建立独立检查项。默认 `gmx grompp` 检查不通过启用 `POSRES`、`POSRES_WATER` 或其它条件宏代替该检查。

## 检查已确认并产生 topology effect 的 `topology-linked` 关系

从依赖文件 `classification_result.yaml` 的 `topology_linked_checks` 中读取属于当前 source 2.5 integration object、且同时满足以下条件的关系：

```text
judgment = CONFIRMED
且
topology_effect_applied = true
```

`COVALENT_CONNECTION` 使用 `atom_1` 和 `atom_2` 定位两端；`METAL_COORDINATION` 使用 `metal` 和 `donor` 定位两端。必要时结合当前 map，将这些既有原子身份定位到最终 `moleculetype` 的 `[ atoms ] nr`。

本项的检查对象文件是最终对应 `moleculetype` 的 `.itp`。对每条关系，检查关系两端 atom 是否在该 `.itp` 的 `[ bonds ]` 中形成直接连接。不通过 topology-linked 参数化工作目录或其它文件反推应检查哪些关系。

`judgment = REJECTED` 或 `topology_effect_applied = false` 的记录不属于本项要求最终拓扑必须体现的关系。

## 检查 topology-linked 参数化要求删除的标准残基原子

从 `topology_integration_result.yaml` 记录的实际引用定位当前拓扑整合采用的 topology-linked 参数化正式结果，读取其中的 `standard_atom_deletions`。

对每个指定删除的标准残基 atom，检查：

- 当前结构文件中不存在该 atom；
- 最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 中不存在该 atom。

使用参数化正式结果记录的标准结构原子身份和相应 map，保持与既有 `component_id + residue_id` 的对应，不根据 atom name 单独重建原子身份。

## 检查 topology-linked 参数化要求的标准残基一侧电荷修改

从 `topology_integration_result.yaml` 记录的实际引用定位当前拓扑整合采用的 topology-linked 参数化正式结果、对应电荷文件和参数化模型 map，读取其中的 `charge_modification_scope`。

对该范围中 `topology_class: STANDARD_RESIDUE` 的每个 residue，通过参数化模型 map 与电荷文件确定相关 atom 的指定电荷，并逐 atom 检查最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 所记录 `charge` 是否采用这些值。

正式结果只按 residue 记录实际检查的 atom 数量和发现电荷差异的 atom 数量，不展开逐原子电荷明细。

## 使用 `gmx grompp` 检查当前结构文件和体系 `.top`

Skill package 提供预建检查参数：

`references/grompp_validation.mdp`

该文件是可直接使用的检查起点，不是不可修改的模拟方案。执行 Agent 根据当前 GROMACS 版本、当前结构文件和体系 `.top` 判断是否直接使用该预设，或在当前工作目录生成适用于本次预处理检查的 `.mdp`。无论采用哪种方式，都应保持本次运行只承担 GROMACS 预处理检查，不把检查参数解释为后续模拟方案，并在正式结果中记录实际命令。

默认不启用 `POSRES`、`POSRES_WATER` 或其它条件宏；position restraint 文件已在 `.itp` 检查中处理。不使用 `-maxwarn` 强制越过 warning。

使用当前结构文件和体系 `.top` 执行 `gmx grompp`，记录实际使用的 GROMACS version、实际命令和进程返回码。对 `gmx grompp` 输出的每一项 note、warning 和 error，分别记录原始信息，并分析：

- 该信息由什么输入或设置触发；
- 它是否反映当前结构文件、体系 `.top` 或 `.itp` 中的实际问题；
- 若不反映当前拓扑问题，依据什么判断其与本次检查对象无关。

`return_code = 0` 不能替代前述独立检查。检查用 `.mdp`、临时 `.tpr` 及其它 GROMACS 预处理工作文件不自动成为正式结果。

## 正式结果

生成正式结果前读取：

`references/results.md`

按其中定义生成唯一正式结果：

`topology_validation_result.yaml`

该 YAML：

- 记录 current 2.6 local `target_id`；
- 在 `references.target_record` 记录 current 2.6 target record；
- 同时记录 `topology_integration_result.yaml` 及实际被检查结构 / map / topology files；
- 只记录实际检查对象和检查结果，不记录 `PASS`、`FAIL`、`COMPLETE`、整体结论或阻断性结论。

正式结果生成前确认：

- `references.target_record` 指向 current 2.6 target record；
- current target record 的 `source_target_records` 包含本次实际 source 2.5 target record；
- source `integrated.map.target_record` 与 source 2.5 target record 一致；
- current 2.6 target 与 source 2.5 target 不因为 `target_id` 相同/不同改变上述关系。

项目结果索引只登记 `topology_validation_result.yaml`。Current 2.6 target record、当前结构文件、map、体系 `.top`、`.itp`、检查用 `.mdp` 和临时 `.tpr` 不作为当前职责的新结果重复登记。

完成上述六项检查并生成 `topology_validation_result.yaml` 后，当前工作项完成；随后按 Task Execution 规则更新 Task Sheet。检查中发现的问题继续保留在正式结果中，不改变当前工作项已经完成检查并生成正式结果这一事实。

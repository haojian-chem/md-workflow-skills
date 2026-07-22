---
name: structure_preparation_workflow
description: 对一个 Focus Workstream 的结构准备阶段进行局部编排，根据当前位置、有效产物、用户决定和 gate 返回下一 task unit。该 Skill 不执行 Operation/Validator、不创建子 Agent、不修改项目或业务文件。
---

# 目标

将一个 Workstream 从原始结构输入推进到经过最终验证、可供 `topology_preparation` 使用的结构 artifact set。

本 Workflow 只返回当前下一步决定，不执行 task、不管理子 Agent、不直接与用户交互。

# 输入

Manager 必须提供：

- `workstream_id`；
- 符合 `workstream_state.schema.yaml` 的当前 Workstream state；
- 当前 active route 及本轮起点、终点；
- 当前有效 STRUCTURE artifact set 和必要报告引用；
- 已解决 decision 摘要；
- 目标 Skill 可用性；
- 项目根和本阶段工作目录；
- 用户步骤级覆盖指令，如有。

缺少 Workstream ID、范围或必要状态时返回 `BLOCKED`，不得自行假定完整从头到尾执行。

# 职责边界

负责：

- 定义结构准备阶段的有序 substep；
- 判断 Focus Workstream 当前位于哪个 substep；
- 根据有效 artifact、报告和已解决决定选择一个下一 task unit；
- 判断跳过、暂停、阻塞或阶段完成；
- 声明下一 task unit 的输入、输出和 gate；
- 返回 `workflow_decision.schema.yaml`。

不得：

- 执行 Operation 或 Validator；
- 创建或管理子 Agent；
- 修改结构、状态或记录；
- 直接向用户提问；
- 选择项目 Focus、创建 Workstream 或切换全局阶段；
- 复制子 Skill 的命令、算法或详细领域判定标准；
- 根据目录存在直接推断任务完成。

# 阶段目录

```text
01_structure_preparation/
├── 01_source_recognition/
├── 02_component_and_residue_classification/
├── 03_chain_and_component_selection/
├── 04_altloc_occupancy_resolution/
├── 05_completeness_check/
├── 06_missing_region_completion/
├── 07_protein_protonation_assignment/
├── 08_reorder_and_mapping/
└── 09_validation/
```

目录只在相应 task 实际执行时由 Operation/Validator 按权限创建。目录存在不是完成证据。

# Substep registry

## 1. source_recognition

目标：识别并选定初始 PDB/mmCIF/AF3 CIF 等结构来源，建立首个 STRUCTURE artifact candidate。

```text
mode: OPERATION
operation: source_recognition
validator: null
work_directory: 01_structure_preparation/01_source_recognition
```

完成证据：source recognition result 为 DONE，且 Manager 已注册可定位的 STRUCTURE artifact set；该 artifact 可以是 `UNVALIDATED`。

## 2. component_and_residue_classification

目标：识别链、组分、残基类别、标准生物聚合物、相连非标准残基、独立非标准组分和协调候选。

```text
mode: VALIDATOR
operation: null
validator: component_and_residue_classification_validator
work_directory: 01_structure_preparation/02_component_and_residue_classification
```

完成证据：Validator 执行成功且分类报告存在。分类中的不确定项可以产生 decision request，不自动视为 Validator 执行失败。

## 3. chain_and_component_selection

目标：按用户决定和分类结果保留、删除、拆分或单独处理链与组分。

```text
mode: OPERATION_WITH_VALIDATOR
operation: chain_and_component_selection
validator: chain_and_component_selection_validator
work_directory: 01_structure_preparation/03_chain_and_component_selection
```

前置 gate：分类报告可用；所有 blocking 选择决定已解决。

完成证据：Operation DONE，专属 Validator 执行成功并给出可继续的 outcome，Manager 注册新的 STRUCTURE artifact set。

## 4. altloc_occupancy_resolution

目标：处理保留体系中的 altLoc/occupancy 冲突。

```text
mode: OPERATION_WITH_VALIDATOR
operation: altloc_occupancy_resolution
validator: altloc_occupancy_validator
work_directory: 01_structure_preparation/04_altloc_occupancy_resolution
```

执行条件：有效结构中存在待处理 altLoc/occupancy 问题。

无问题且有可信检查证据时返回 `SKIP`；不得仅凭文件名或来源类型跳过。

## 5. completeness_check

目标：检查残基、重原子和连接完整性，并识别需要补全/修复的区域。

```text
mode: VALIDATOR
operation: null
validator: structure_completeness_validator
work_directory: 01_structure_preparation/05_completeness_check
```

完成证据：完整性报告存在并明确给出无需补全、需要补全或需要人工决定的 outcome。

## 6. missing_region_completion

目标：按已确认的残基范围和策略补全或修复缺失区域。

```text
mode: OPERATION_WITH_VALIDATOR
operation: missing_region_completion
validator: missing_region_completion_validator
work_directory: 01_structure_preparation/06_missing_region_completion
```

执行条件：完整性报告要求补全/修复，且 blocking 决定已解决。

完整性报告明确无需补全时返回 `SKIP`。

## 7. protein_protonation_assignment

目标：确定并应用需要处理的 His/Asp/Glu 等蛋白质质子化状态。

```text
mode: OPERATION_WITH_VALIDATOR
operation: protein_protonation_assignment
validator: protein_protonation_validator
work_directory: 01_structure_preparation/07_protein_protonation_assignment
```

执行条件：保留体系含需要判定的蛋白质残基。无蛋白质或没有需要处理的目标时，基于分类和检查证据返回 `SKIP`。

## 8. reorder_and_mapping

目标：按项目规范重排结构，整理编号并生成原结构到最终结构的映射。

```text
mode: OPERATION_WITH_VALIDATOR
operation: structure_reorder_and_mapping
validator: structure_mapping_validator
work_directory: 01_structure_preparation/08_reorder_and_mapping
```

完成证据：新 STRUCTURE artifact candidate 与映射文件存在，Validator 执行成功并确认映射一致。

## 9. validation

目标：核验结构准备阶段的最终结构和必要记录是否满足进入拓扑准备的 gate。

```text
mode: VALIDATOR
operation: null
validator: structure_preparation_validator
work_directory: 01_structure_preparation/09_validation
```

完成证据：Validator 执行成功，最终 outcome 允许进入下一阶段，且对应 STRUCTURE artifact set 已由 Manager 标记为 `VALIDATED`。

# 当前位置判断

仅根据以下证据判断：

1. Workstream `current_position`；
2. active route 的范围；
3. Manager 登记的 task/result；
4. artifact set 与 Validator report；
5. 已解决 decision。

禁止仅按目录编号、文件时间或目录是否存在推断。

若 state 与记录矛盾，返回 `BLOCKED`，理由为 Workstream 需要恢复；不得自行修复状态。

# 决策规则

## EXECUTE

仅返回一个 `next_task_unit`。必须声明 task ID、mode、Operation/Validator Skill ref、工作目录、required inputs、expected outputs 和 gate requirements。

目标 Skill 未实现或不可用时，不得返回可执行 task；返回 `BLOCKED` 并说明缺失 Skill。

## SKIP

只在以下情况使用：

- active route 明确允许该条件步骤跳过；
- 有报告或已验证 artifact 证明步骤不适用；
- 已有等价且仍有效的结果。

返回被跳过 substep 和证据。Manager 记录后再次调用本 Workflow。

## PAUSE

用于存在尚未解决但可由用户/外部条件解除的暂停，例如 blocking decision 或缺失用户输入。返回 confirmation items 或明确依赖，不返回 task unit。

## BLOCKED

用于：输入状态不可解释、必要 Skill 缺失、前置 artifact/report 缺失、gate 冲突或需要恢复。不得把业务对象“不通过”自动等同为 Workflow 执行失败；应根据 Validator outcome 返回修复 task、decision 或阻塞理由。

## COMPLETE

仅当：

- 本轮 route 终点已达到；或
- `validation` 已通过、最终 STRUCTURE artifact 为 VALIDATED，且阶段目标完成。

Workflow 只返回阶段完成；Manager 决定是否进入下一 Workflow 或结束本轮范围。

# 条件步骤与路线修订

以下结果可能要求 Manager 修订 route：

- 分类发现需要额外人工选择；
- completeness report 决定是否进入补全；
- 补全或质子化产生新的结构版本；
- Validator outcome 要求返回前一 substep；
- 用户改变本轮终点；
- artifact 被 INVALIDATED 或 SUPERSEDED。

本 Workflow 返回修订理由，不直接写 route record。

# 返回

每次只返回一个符合 `03_contracts/workflow_decision.schema.yaml` 的对象。

- `workstream_id` 必须等于 Focus Workstream；
- `workflow_name` 固定为 `structure_preparation_workflow`；
- `confirmation_items` 使用共享 decision request contract；
- 不返回 subagent result，不汇总或执行多个 task；
- 不直接更新 project/workstream state。

# 自检

- [ ] 只读取一个 Focus Workstream 的局部状态；
- [ ] 只返回一个当前决定；
- [ ] 未执行或模拟子 Skill；
- [ ] 未创建子 Agent；
- [ ] 未向用户直接提问；
- [ ] 未根据目录存在推断完成；
- [ ] 条件跳过有证据；
- [ ] 组合 task 仅用于专属 Validator；
- [ ] 未跨出 structure_preparation；
- [ ] 最终完成要求 VALIDATED STRUCTURE artifact。

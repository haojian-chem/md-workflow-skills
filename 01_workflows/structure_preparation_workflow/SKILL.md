---
name: structure_preparation_workflow
description: 为一个 Focus Workstream 规划结构准备阶段的 route fragment，并在执行时根据当前位置、有效产物、用户决定和 gate 返回一个当前 task unit decision。该 Skill 不执行 Operation/Validator、不创建子 Agent、不修改项目或业务文件。
---

# 目标

将一个 Workstream 从原始结构输入推进到经过最终验证、可供 `topology_preparation` 使用的 STRUCTURE artifact set。

本 Workflow 提供两个接口：

- 规划：返回 `workflow_route_fragment.schema.yaml`；
- 执行：返回 `workflow_decision.schema.yaml`。

它不执行 task、不管理子 Agent、不直接与用户交互。

# 输入

Manager 必须提供共同输入：

- `workstream_id`；
- 符合 `workstream_state.schema.yaml` 的当前 Workstream state；
- 当前有效 STRUCTURE artifact set 和必要报告引用；
- 已解决 decision 摘要；
- 目标 Skill 可用性；
- 项目根和本阶段工作目录；
- 用户步骤级覆盖指令，如有。

规划接口还必须提供：

- 本 Workflow 内的起点与终点；
- Workstream 目标和用户约束；
- 已知条件、假设和跨阶段出口要求。

执行接口还必须提供：

- 当前 active route；
- 当前预计下一 step；
- 当前 task/result、artifact 和 Validator evidence。

缺少 Workstream ID、范围或必要状态时返回 BLOCKED，不得自行假定完整从头到尾执行。

# 职责边界

负责：

- 定义结构准备阶段的有序 substep；
- 为本阶段生成 REQUIRED/CONDITIONAL route fragment；
- 声明入口要求、出口 artifact、条件、假设和 blocker；
- 判断 Focus Workstream 当前位于哪个 substep；
- 根据有效 artifact、报告和已解决决定选择一个下一 task unit；
- 判断跳过、暂停、阻塞或阶段完成；
- 声明下一 task unit 的输入、输出和 gate。

不得：

- 拼接其他 Workflow 或写完整 route record；
- 选择跨 Workflow 起点、终点或 Focus；
- 执行 Operation 或 Validator；
- 创建或管理子 Agent；
- 修改结构、状态或记录；
- 直接向用户提问；
- 创建 Workstream 或切换全局阶段；
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
necessity: REQUIRED
```

完成证据：Operation result 为 DONE，且 Manager 已注册可定位的 STRUCTURE artifact set；该 artifact 可以是 UNVALIDATED。

## 2. component_and_residue_classification

目标：识别链、组分、残基类别、标准生物聚合物、相连非标准残基、独立非标准组分和协调候选。

```text
mode: VALIDATOR
operation: null
validator: component_and_residue_classification_validator
work_directory: 01_structure_preparation/02_component_and_residue_classification
necessity: REQUIRED
```

完成证据：Validator 执行成功且分类报告存在。不确定项可以产生 decision request，不自动视为 Validator 执行失败。

## 3. chain_and_component_selection

目标：按用户决定和分类结果保留、删除、拆分或单独处理链与组分。

```text
mode: OPERATION_WITH_VALIDATOR
operation: chain_and_component_selection
validator: chain_and_component_selection_validator
work_directory: 01_structure_preparation/03_chain_and_component_selection
necessity: REQUIRED
```

前置 gate：分类报告可用；所有 blocking 选择决定已解决。

## 4. altloc_occupancy_resolution

目标：处理保留体系中的 altLoc/occupancy 冲突。

```text
mode: OPERATION_WITH_VALIDATOR
operation: altloc_occupancy_resolution
validator: altloc_occupancy_validator
work_directory: 01_structure_preparation/04_altloc_occupancy_resolution
necessity: CONDITIONAL
condition: 有可信检查证据表明存在待处理 altLoc/occupancy 问题
```

无问题且有可信证据时执行接口返回 SKIP。

## 5. completeness_check

目标：检查残基、重原子和连接完整性，并识别需要补全或修复的区域。

```text
mode: VALIDATOR
operation: null
validator: structure_completeness_validator
work_directory: 01_structure_preparation/05_completeness_check
necessity: REQUIRED
```

完成证据：报告明确给出无需补全、需要补全或需要人工决定的 outcome。

## 6. missing_region_completion

目标：按已确认的残基范围和策略补全或修复缺失区域。

```text
mode: OPERATION_WITH_VALIDATOR
operation: missing_region_completion
validator: missing_region_completion_validator
work_directory: 01_structure_preparation/06_missing_region_completion
necessity: CONDITIONAL
condition: 完整性报告要求补全或修复，且 blocking 决定已解决
```

报告明确无需补全时执行接口返回 SKIP。

## 7. protein_protonation_assignment

目标：确定并应用需要处理的 His/Asp/Glu 等蛋白质质子化状态。

```text
mode: OPERATION_WITH_VALIDATOR
operation: protein_protonation_assignment
validator: protein_protonation_validator
work_directory: 01_structure_preparation/07_protein_protonation_assignment
necessity: CONDITIONAL
condition: 保留体系含需要判定和应用质子化状态的蛋白质残基
```

无蛋白质或没有目标时，基于分类和检查证据返回 SKIP。

## 8. reorder_and_mapping

目标：按项目规范重排结构，整理编号并生成原结构到最终结构的映射。

```text
mode: OPERATION_WITH_VALIDATOR
operation: structure_reorder_and_mapping
validator: structure_mapping_validator
work_directory: 01_structure_preparation/08_reorder_and_mapping
necessity: REQUIRED
```

完成证据：新 STRUCTURE artifact candidate 与映射文件存在，Validator 确认映射一致。

## 9. validation

目标：核验结构准备阶段的最终结构和必要记录是否满足进入拓扑准备的 gate。

```text
mode: VALIDATOR
operation: null
validator: structure_preparation_validator
work_directory: 01_structure_preparation/09_validation
necessity: REQUIRED
```

完成证据：Validator 允许进入下一阶段，且对应 STRUCTURE artifact set 已由 Manager 标记为 VALIDATED。

# 规划接口：route fragment

Manager 请求规划时，本 Workflow：

1. 根据起点和终点裁剪 substep registry；
2. 保留范围内所有 REQUIRED steps；
3. 保留所有尚不能由证据排除的 CONDITIONAL steps；
4. 为每一步声明 task unit mode、Skill ref、工作目录、前置要求、预期输出和 gate；
5. 声明入口 requirements；
6. 声明出口为经过最终验证的 STRUCTURE artifact；
7. 标记尚未实现 Skill、缺失入口 artifact 或范围冲突形成的 blocker；
8. 返回 `workflow_route_fragment.schema.yaml`。

## Fragment 状态

- `COMPLETE`：请求范围内所有步骤均可表达，且无 blocker；
- `PARTIAL`：可规划一部分，但某个条件、Skill 或边界尚未解析；
- `BLOCKED`：在入口即无法形成安全片段。

规划接口不根据当前不完整 evidence 提前决定条件步骤一定执行或一定跳过。

本 Workflow 的 `next_workflow_hint` 为 `topology_preparation_workflow`，要求输入 VALIDATED STRUCTURE artifact。下一 Workflow 是否连接由 Manager 和 stage registry 判断。

# 执行接口：当前 decision

## 当前位置判断

仅根据：

1. Workstream `current_position`；
2. active route 的范围和预计下一 step；
3. Manager 登记的 task/result；
4. artifact set 与 Validator report；
5. 已解决 decision。

禁止仅按目录编号、文件时间或目录是否存在推断。

若 state 与记录矛盾，返回 BLOCKED，理由为 Workstream 需要恢复；不得自行修复状态。

## EXECUTE

每次只返回一个 `next_task_unit`。必须声明 task ID、mode、Operation/Validator Skill ref、工作目录、required inputs、expected outputs 和 gate requirements。

目标 Skill 未实现或不可用时，不得返回可执行 task；返回 BLOCKED 并说明缺失 Skill。

## SKIP

只在以下情况使用：

- active route 将该步骤标为 CONDITIONAL；
- 有报告或已验证 artifact 证明步骤不适用；
- 已有等价且仍有效的结果。

返回被跳过 substep 和证据。Manager 记录后再次调用本 Workflow。

## PAUSE

用于尚未解决但可由用户或外部条件解除的暂停，例如 blocking decision 或缺失用户输入。返回 confirmation items 或明确依赖，不返回 task unit。

## BLOCKED

用于输入状态不可解释、必要 Skill 缺失、前置 artifact/report 缺失、gate 冲突或需要恢复。

不得把业务对象“不通过”自动等同为 Workflow 执行失败；应根据 Validator outcome 返回修复 task、decision 或阻塞理由。

## COMPLETE

仅当：

- 本轮 route 终点已达到；或
- validation 已通过、最终 STRUCTURE artifact 为 VALIDATED，且阶段目标完成。

Workflow 只返回本范围或本阶段完成；Manager 决定进入下一 Workflow 或结束本轮。

# Route revision signal

以下结果可能使 active route 过期：

- 分类发现额外人工选择；
- completeness report 决定是否进入补全；
- 补全或质子化产生新结构版本；
- Validator 要求返回前一 substep；
- 用户改变终点；
- artifact 被 INVALIDATED 或 SUPERSEDED；
- Skill 可用性变化。

本 Workflow 返回修订理由和新的 fragment；不直接写 route record。

# 返回

规划时只返回一个符合：

`03_contracts/workflow_route_fragment.schema.yaml`

执行时只返回一个符合：

`03_contracts/workflow_decision.schema.yaml`

共同要求：

- `workstream_id` 必须等于 Focus Workstream；
- `workflow_name` 固定为 `structure_preparation_workflow`；
- 不返回 subagent result；
- 不执行或汇总多个 task；
- 不直接更新 project/workstream state。

# 自检

- [ ] 只读取一个 Focus Workstream 的局部状态；
- [ ] 规划时返回本 Workflow 的 fragment，未跨阶段拼接；
- [ ] REQUIRED 与 CONDITIONAL 步骤已区分；
- [ ] 条件步骤未在无证据时提前删除；
- [ ] 执行时只返回一个当前 decision；
- [ ] 未执行或模拟子 Skill；
- [ ] 未创建子 Agent；
- [ ] 未向用户直接提问；
- [ ] 未根据目录存在推断完成；
- [ ] 组合 task 仅用于专属 Validator；
- [ ] 最终阶段完成要求 VALIDATED STRUCTURE artifact。

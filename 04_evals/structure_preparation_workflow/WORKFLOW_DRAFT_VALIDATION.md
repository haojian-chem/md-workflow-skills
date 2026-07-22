# structure_preparation_workflow Draft Validation

日期：2026-07-22

## 静态检查

```text
SKILL.md lines: 273
front matter: PASS
name field: PASS
description field: PASS
foreground execution logic inside Workflow: absent
subagent creation logic inside Workflow: absent
workflow decision mode: one decision per call
decision fixture YAML parse: PASS
decision cases: 15
case IDs unique: PASS
```

## 已覆盖的阶段逻辑

- `source_recognition`；
- `component_and_residue_classification`；
- `chain_and_component_selection`；
- `altloc_occupancy_resolution`；
- `completeness_check`；
- `missing_region_completion`；
- `protein_protonation_assignment`；
- `reorder_and_mapping`；
- 最终 `validation`。

每个 substep 均映射为一个 `OPERATION`、`VALIDATOR` 或 `OPERATION_WITH_VALIDATOR` task unit。Workflow 不执行子 Skill，只返回一个 `workflow_decision`。

## 已覆盖的边界案例

- 缺少必要状态或 Skill 时阻塞；
- blocking 用户决定时暂停；
- altLoc、缺失补全和质子化的有证据条件跳过；
- state 与 task record 冲突时要求恢复；
- 路线在阶段中间结束时返回本轮 `COMPLETE`，但不宣称全阶段完成；
- 只有最终 STRUCTURE artifact 为 `VALIDATED` 时才允许完成整个阶段。

## 仍需完成

该 Workflow 保持 `draft`。冻结前需要：

1. 将 fixtures 转换为共享 schema 可校验的完整输入/输出；
2. 与 Manager 完成一次端到端 decision/task/result/state 测试；
3. 将 `source_recognition` 和现有分类 Validator 迁移到 subagent task/result v2；
4. 明确尚未实现子 Skill 的可用性登记与阻断输出；
5. 用真实结构准备目录验证已有结果、条件跳过和局部恢复。

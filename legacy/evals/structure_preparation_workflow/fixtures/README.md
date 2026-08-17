# structure_preparation_workflow fixtures

`workflow_decision_cases.yaml` 覆盖结构准备阶段的下一步决策、条件跳过、阻断、局部路线终点和最终完成 gate。

当前为设计级行为 fixtures。正式冻结前需要将每个 case 转换为符合 `workstream_state.schema.yaml`、`route_record.schema.yaml` 和 `workflow_decision.schema.yaml` 的可执行输入/输出，并与 Manager 完成端到端集成测试。

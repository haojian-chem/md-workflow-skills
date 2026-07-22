# md_workflow_manager fixtures

`manager_behavior_cases.yaml` 是 Manager draft 的行为验收清单，覆盖：

- NEW、RESUMABLE 和项目级恢复；
- Project/Workstream Focus；
- 运行中主分支与新参数分支并存；
- 原 Workstream 修正与必须分支的边界；
- 三种 task unit；
- 阻断性用户决定；
- 外部任务 `FINISHED_UNVERIFIED`；
- 失败任务不自动重试；
- 未连接 Workflow 的阻断；
- Focus 歧义；
- 子 Agent 管理目录越权；
- 完整路线展示策略。

这些 fixtures 当前用于设计审查和后续自动 eval 构建，不代表 Manager 已达到 `frozen`。正式冻结前还需要：

1. 为每个 case 建立可执行的输入状态与期望输出；
2. 用共享 schemas 校验生成的 state/record/task/result；
3. 与 `structure_preparation_workflow` 完成一次端到端集成测试；
4. 覆盖 project-level 与 Workstream-level recovery 的实际文件案例。

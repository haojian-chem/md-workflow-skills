# v2 重新设计说明

Status: ARCHIVE / HISTORY ONLY

本版本从空目录重新构筑，没有继承旧版中将 Skill 编写活动建模为 Agent 角色的结构。

## 已明确分离

- MD 运行时：Manager、Workflow 与串行临时子 Agent；
- Skill 开发时：网页端独立编写窗口和互斥文件所有权。

## 运行时约束

- Workflow 仅返回当前阶段决策，不作为运行时执行主体；
- Manager 任意时刻最多创建一个临时子 Agent；
- 临时子 Agent 只执行一个 Operation 或 Validator Skill；
- 临时子 Agent 不再委派；
- MD 子任务当前不采用并行调度。

## 接口精简

共享接口仅保留：

- `common_types.schema.yaml`；
- `confirmation_item.schema.yaml`；
- `workflow_decision.schema.yaml`；
- `subagent_task.schema.yaml`；
- `subagent_result.schema.yaml`；
- `project_state.schema.yaml`。

Operation 与 Validator 的特有业务结果通过本地报告或本地输出 schema 表达，不再复制多套公共返回字段。

> 本文件描述的是已废弃的旧 Runtime/Operation/Validator 架构，仅用于历史追溯。Current authority 见 `00_authoring/SKILL.md` 与 `00_authoring/project_design/`。

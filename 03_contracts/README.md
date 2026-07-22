# Shared contracts

本目录是运行时共享接口的唯一权威位置。Skill 只能引用这些 schema，不得在本地重新定义相同字段。

## 基础类型

- `common_types.schema.yaml`：状态、Workstream、Focus、文件、warning 和 failure 等公共类型。
- `confirmation_item.schema.yaml`：尚未持久化为完整记录的用户决策请求。

## Workflow 与临时子 Agent

- `workflow_decision.schema.yaml`：Workflow 对某一 Workstream 返回的局部下一步决定。
- `subagent_task.schema.yaml`：Manager 下发给单个临时子 Agent 的任务单元。
- `subagent_result.schema.yaml`：临时子 Agent 的精简结构化返回。

任务单元支持三种模式：

- `OPERATION`
- `VALIDATOR`
- `OPERATION_WITH_VALIDATOR`

第三种只用于 Operation 与其专属配套 Validator 需要连续共享即时上下文的情况。两者的结果仍必须分开记录。

## 当前状态

- `project_state.schema.yaml`：项目级索引、入口状态和 Focus。
- `workstream_state.schema.yaml`：单个 Workstream 的当前位置、状态、路线、产物、决策和外部任务引用。

## 历史和审计记录

- `project_event.schema.yaml`：全项目唯一 JSONL 事件流水中的单条事件。
- `route_record.schema.yaml`：不可变的 Workstream 路线版本。
- `decision_record.schema.yaml`：持久化人工决策记录。
- `submission_record.schema.yaml`：tmux 或调度系统外部任务记录。
- `artifact_set.schema.yaml`：结构、拓扑、完整体系、MD 输入输出和分析结果的版本谱系。
- `state_snapshot.schema.yaml`：关键节点状态快照清单。
- `manager_session.schema.yaml`：Manager 会话 Markdown 文件的 YAML front matter。

## 读取建议

- Manager：读取全部状态与记录 contracts。
- Workflow：读取 `common_types`、`workflow_decision` 和 `workstream_state`。
- Operation/Validator 子 Agent：读取 `common_types`、`subagent_task`、`subagent_result` 和 `confirmation_item`。
- 业务 Skill 不得直接修改 `00_project_state/` 或 `00_project_records/`；这些目录由 Manager 唯一提交。

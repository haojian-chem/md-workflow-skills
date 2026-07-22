# 共享 Contracts

本目录只保存跨 Skill 的运行时接口。

```text
common_types.schema.yaml
confirmation_item.schema.yaml
workflow_decision.schema.yaml
subagent_task.schema.yaml
subagent_result.schema.yaml
project_state.schema.yaml
```

不再保留 manager、workflow、operation、validator 四套重复返回 schema。

- Workflow 只输出 `workflow_decision`；
- Manager 向临时子 Agent 发送 `subagent_task`；
- Operation/Validator 临时子 Agent 均返回 `subagent_result`；
- Skill 特有结果通过 `detail_files` 或 Skill 本地输出 schema 表达。

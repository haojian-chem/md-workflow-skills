---
task_id:
window_id:
skill_name:
status: BACKLOG
---

# Goal

# Context

开始前必须读取：

- `AGENTS.md`
- `00_authoring/SYNC_STATUS.md`
- `00_authoring/skill_inventory.yaml`
- `00_authoring/file_ownership.yaml`
- 目标 Skill 的 content map
- `03_contracts/README.md`
- 本任务适用的共享 schemas

# 已做过 / 已否定 / 仍未验证

# Frozen local contract

```yaml
skill_layer:
job:
required_inputs: []
outputs: []
write_paths: []
forbidden_paths: []
shared_contracts: []
workstream_effects: []
record_effects: []
```

# File ownership

```yaml
write_paths: []
read_paths: []
forbidden_paths: []
shared_files: []
```

共享文件不得在业务窗口直接修改。需要变更时写入 `contract_change_requests`。

# Runtime constraints

- Workflow 不作为 Agent；
- 任意时刻最多一个前台临时子 Agent；
- task unit 只允许 `OPERATION | VALIDATOR | OPERATION_WITH_VALIDATOR`；
- 子 Agent 不修改项目状态和记录目录；
- 多个外部任务并存不等于前台 Agent 并行。

# Done when

# Validation

# Contract change requests

# Handoff

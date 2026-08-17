---
task_id:
window_id:
skill_name:
status: BACKLOG
---

# Goal

# Current responsibility

说明当前窗口负责的 main Skill / supporting Skill 范围，不使用强制 Workflow / Operation / Validator 分类。

# Startup

默认先读取：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前目标 Skill / 文件
```

随后仅按任务需要追加：

- 对应 architecture freeze；
- 与当前输入/输出/边界直接相关的上下游或相邻 Skill / Tool guide；
- 涉及多窗口写入协调时的 `00_authoring/coordination/file_ownership.yaml`；
- 涉及项目级状态时的 `00_authoring/SYNC_STATUS.md` / `MD_WORKFLOW_MASTER_PLAN.md`。

`read_context` 可以在执行中继续扩展；它不是硬白名单，也不要求预读整个 `00_authoring/`。

# 已做过 / 已否定 / 仍未验证

# Owned task boundary

```yaml
primary_job:
inputs_or_evidence: []
results_or_handoff: []
write_paths: []
shared_files_read_only: []
```

# Read / write policy

```yaml
read_context: []
write_paths: []
```

规则：

- 可以按需读取未归本窗口写入的相关 Skill；
- 只有 `write_paths` 表示修改权；
- 不修改未分配给当前窗口的共享 authoring/architecture 文件；
- 不在当前 Skill 中替其他 Skill 定义内部逻辑。

# Cross-Skill interface

只记录接口级关系：

```yaml
consumes_from_other_skills: []
provides_to_other_skills: []
external_rules_referenced: []
```

如果发现外部 Skill 需要修改，记录简短 finding，由 owner window / main window 处理；不要求建立额外 finding schema。

# Agent-guidance check

- Skill 应指导 Agent 如何完成任务；
- 不建立无必要 parser gate；
- 不建立无必要 dispatcher/workflow hop；
- Tool 仅在确定性能力有实际价值时使用；
- 推荐工具与强制科学方法要求必须区分。

# Supporting content

需要拆 supporting Skill / reference 时说明原因：

```yaml
references_to_add: []
supporting_skills_to_add: []
why_split_is_justified: []
```

# Done when

# Validation

# Cross-Skill findings

# Handoff

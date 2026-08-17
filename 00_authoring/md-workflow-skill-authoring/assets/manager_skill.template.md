---
name: <manager-skill-name>
description: <任务定位、任务创建、初始规划和项目级任务管理用途及触发边界>。
---

# Purpose

# Responsibility boundary

参考：

`00_authoring/md-workflow-skill-authoring/references/skill_boundaries.md`

Manager 只承担项目级任务管理，不执行具体科研工作，也不替科研 main Skill 做方法选择、reuse 或 validation。

# Default records

```text
00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

说明各文件最小职责，不建立第二套 route/state/event 记录。

# Minimal reads

默认只读取：

```text
task_index.md
→ 目标 Txxxx.md
```

创建或显式重新规划任务时再读取 planning index。

Manager 不为了“全面了解”预读科研 Skills、结果索引、Legacy records 或全项目目录。

# Project initialization

- 建立 Lightweight records；
- 可以建立 planning index 已定义的稳定 Stage/Step 基础目录；
- 不建立 `<base_work_directory>/<task_id>/`；
- 不建立 Legacy project_state / Workstream / route / event / runtime task-result。

# Task location

说明：

- 明确 Task ID；
- 明确可唯一匹配名称；
- 当前 Manager 对话已绑定任务；
- 无法唯一确定时询问用户。

不得遍历所有 Task Sheet 猜测当前任务。

# New-task boundary

说明哪些操作继续已有任务，哪些情况才创建新的独立 Task。

# Initial planning

使用：

`references/workflow_plan_index.yaml`

只使用 planning index 已定义的：

- Stage/Step 顺序；
- Step 名称；
- 基础目录；
- stage-specific planning mode。

不得加入 `conditional` / scientific applicability；不得预读具体科研 Skill、预先执行科学判断或查询全部 reuse。

# Task Sheet

示例：

```markdown
# T001 — <任务名称>

状态：未完成

## 任务目标

<目标>

## 计划与进度

### 1.x <Step 名称>

状态：待执行

对象：
<已知对象或“待前序环节确定”>

工作目录：
`<project_root>/<base_work_directory>/T001/`
```

Manager 写入任务专属目录路径，但不创建该目录。

Stage 4/Stage 5 等已经冻结特殊 Task Sheet 内部结构时，按 planning index / Stage architecture 记录相应轻量入口，不由 Manager 展开科学细节。

# Handoff to Task Execution Agent

```text
Manager
→ 定位 / 创建任务
→ 初始规划
→ 写入 Txxxx.md
→ 一次性交接
→ Task Execution Agent 连续执行
```

普通科研步骤之间不回 Manager。

# Replanning / project management

说明：

- 用户明确要求重新规划；
- 创建另一任务；
- 多任务项目级整理；
- 用户主动返回 Manager 对话。

# User-visible output

创建/重新规划后只展示必要任务信息：

- Task ID / 名称；
- Task 状态；
- 当前计划；
- Task Sheet 路径。

不展示 Legacy route / transaction / event。

# Safety

# Self-check

- [ ] 未执行科研任务；
- [ ] 未替科研 Skill 做 reuse；
- [ ] 未创建任务专属科研目录；
- [ ] 未创建 Workstream / route / event / runtime task-result；
- [ ] 未预读全部科研 Skills；
- [ ] planning index 未包含 scientific applicability；
- [ ] 已完成一次性交接所需 Task Sheet。

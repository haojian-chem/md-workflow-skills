---
name: <manager-skill-name>
description: <任务定位、任务创建、初始规划和项目级任务管理用途及触发边界>。
---

# 目标

# 职责边界

引用：

`00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`

Manager 只承担任务管理，不执行具体科研 Step。

# 默认记录体系

```text
00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

说明各文件的最小职责，不建立第二套 route/state/event 记录。

# 最小读取

默认只读取：

```text
task_index.md
→ 目标 Txxxx.md
```

创建或显式重新规划任务时再读取 planning index。

明确禁止默认读取的科研 Skill、结果索引、Legacy records 和全项目扫描。

# 项目初始化

- 建立 Lightweight records；
- 可以建立稳定 Workflow / Step 基础目录；
- 不建立 `<base_work_directory>/<task_id>/`；
- 不建立 Legacy project_state / Workstream / route / event / runtime task-result。

# 任务定位

说明：

- 明确 Task ID；
- 明确可唯一匹配名称；
- 当前 Manager 对话已绑定任务；
- 无法唯一确定时询问用户。

不得遍历所有 Task Sheet 猜测当前任务。

# 新任务边界

说明哪些操作继续已有任务，哪些情况才创建新的独立 Task。

# 初始规划

使用：

`references/workflow_plan_index.yaml`

只规划：

- Step 顺序；
- Step 名称；
- 基础目录；
- conditional 标记。

不得预读具体 Step Skill、预先执行科学判断或查询全部 reuse。

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

# 与 Task Execution Agent 交接

```text
Manager
→ 定位 / 创建任务
→ 初始规划
→ 写入 Txxxx.md
→ 一次性交接
→ Task Execution Agent 连续执行
```

普通 Step 之间不回 Manager。

# 重新规划与项目级管理

说明：

- 用户明确要求重新规划；
- 创建另一任务；
- 多任务项目级整理；
- 用户主动返回 Manager 对话。

# 用户展示

创建/重新规划后只展示：

- Task ID / 名称；
- Task 状态；
- 当前计划 Step 序列；
- Task Sheet 路径。

不展示 Legacy route / transaction / event。

# 安全边界

# 自检

- [ ] 未执行科研 Step；
- [ ] 未查询 Step reuse；
- [ ] 未创建任务专属科研目录；
- [ ] 未创建 Workstream / route / event / runtime task-result；
- [ ] 未预读全部 Step Skill；
- [ ] 已完成一次性交接所需 Task Sheet。

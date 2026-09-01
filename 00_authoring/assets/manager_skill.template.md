---
name: <manager-skill-name>
description: <Task Sheet 定位、创建、初始规划和项目级 Task Sheet 管理用途及触发边界>。
---

# Purpose

# Responsibility boundary

参考：

`00_authoring/references/skill_boundaries.md`

Manager 只承担项目级 Task Sheet 管理，不执行具体科研工作，也不替科研 main Skill 做方法选择、reuse 或 validation。

一个科研任务可以由多张 Task Sheet 共同承载；创建新的 `Txxxx.md` 不自动表示创建新的科研任务。

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

当前 Task Sheet 明确依赖同一科研任务的前序 Task Sheet 时，可以按明确引用读取该前序记录；不得因此扫描全部 Task Sheets。

创建或显式重新规划 Task Sheet 时再读取 planning index。

Manager 不为了“全面了解”预读科研 Skills、结果索引、Legacy records 或全项目目录。

# Project initialization

- 建立当前项目记录；
- 可以建立 planning index 已定义的稳定 Stage/Step 基础目录；
- 不建立 `<base_work_directory>/<task_id>/`；
- 不建立 Legacy project_state / Workstream / route / event / runtime task-result。

# Task Sheet location

说明：

- 明确 Task Sheet ID；
- 明确可唯一匹配名称；
- 当前 Manager 对话已绑定 Task Sheet；
- 无法唯一确定时询问用户。

不得遍历所有 Task Sheet 猜测当前对象。

# New Task Sheet boundary

说明：

- 哪些情况继续当前 Task Sheet；
- 哪些情况为了控制上下文规模、隔离废弃/错误方案或进入新的有界执行段而在**同一科研任务**中建立后续 Task Sheet；
- 哪些情况属于新的独立科研任务。

不要把“新 Task Sheet”和“新科研任务”写成同义概念。

# Initial planning

使用：

`references/workflow_plan_index.yaml`

只使用 planning index 已定义的：

- Stage/Step 顺序；
- Step 名称；
- 基础目录；
- stage-specific planning mode；
- 明确的结构性 prerequisite。

Task Sheet 只覆盖当前执行范围，不要求完整 Workflow 或完整 Stage。局部 Task Sheet 可以从中间 Step 开始，但 current Step 明确定义的 prerequisite 必须已经由当前或前序 Task Sheet 满足。

不得加入 `conditional` / scientific applicability；不得预读具体科研 Skill、预先执行科学判断或查询全部 reuse。只有当前执行范围确实覆盖完整 Stage 时，才按 planning index 的完整 Stage planning 规则展开。

# Task Sheet

示例：

```markdown
# T001 — <Task Sheet 名称>

状态：未完成

## 当前执行目标

<目标>

## 最小恢复上下文

<如适用，记录同一科研任务的前序 Task Sheet / prerequisite 来源>

## 计划与进度

### 1.x <Step 名称>

状态：未完成

对象：
<已知对象或当前仍需确定的对象>

工作目录：
`<project_root>/<base_work_directory>/T001/`
```

普通任务项状态统一使用：

```text
未完成
已完成
已终止
```

Manager 写入 Task Sheet 对应工作目录路径，但不创建该目录。

Stage 3/Stage 4/Stage 5 等具有特殊 Task Sheet 内部结构时，按 planning index / current Stage architecture 记录相应轻量入口，不由 Manager 展开科学细节。

# Handoff to Task Execution Agent

```text
Manager
→ 定位 / 创建 Task Sheet
→ 初始规划
→ 写入 Txxxx.md
→ 一次性交接
→ Task Execution Agent 连续执行当前 Task Sheet
```

普通科研步骤之间不回 Manager；需要建立后续 Task Sheet 时再进入 Manager。

# Replanning / project management

说明：

- 用户明确要求重新规划；
- 为同一科研任务创建后续 Task Sheet；
- 创建新的科研任务对应 Task Sheet；
- 多 Task Sheet 项目级整理；
- 用户主动返回 Manager 对话。

# User-visible output

创建/重新规划后只展示必要信息：

- Task Sheet ID / 名称；
- Task Sheet 状态；
- 当前计划；
- Task Sheet 路径；
- 必要时注明前序 Task Sheet。

不展示 Legacy route / transaction / event。

# Safety

# Self-check

- [ ] 未执行科研任务；
- [ ] 未替科研 Skill 做 reuse；
- [ ] 未创建任务专属科研目录；
- [ ] 未创建 Workstream / route / event / runtime task-result；
- [ ] 未预读全部科研 Skills；
- [ ] planning index 未包含 scientific applicability；
- [ ] 没有把一张 Task Sheet 等同于整个科研任务；
- [ ] 局部 Task Sheet 没有绕过已定义 prerequisite；
- [ ] 普通任务项状态只使用 `未完成 / 已完成 / 已终止`；
- [ ] 已完成一次性交接所需 Task Sheet。

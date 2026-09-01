---
name: <manager-skill-name>
description: <Task Sheet 自动定位、创建、初始规划和项目级 Task Sheet 管理用途及触发边界>。
---

# Purpose

说明 Manager 同时承担：

- 用户显式请求的 Task Sheet 管理；
- **科研执行入口尚未解析到 Task Sheet 时的自动 Task Sheet resolution**。

# Responsibility boundary

参考：

`00_authoring/references/skill_boundaries.md`

Manager 只承担项目级 Task Sheet 管理，不执行具体科研工作，也不替科研 main Skill 做方法选择、reuse 或 validation。

一个科研任务可以由多张 Task Sheet 共同承载；创建新的 `Txxxx.md` 不自动表示创建新的科研任务。

# Entry triggers

至少覆盖：

- 用户显式要求定位、创建、整理或重新规划 Task Sheet；
- 用户发出真实项目科研执行 / 继续指令，但当前没有已解析、仍可使用的 Task Sheet；
- 当前绑定 Task Sheet 已完成 / 已终止 / 与最新执行指令不再对应；
- 当前执行需要建立同一科研任务的后续 Task Sheet。

科研执行入口没有 Task Sheet 时，不要求用户再额外说“建立任务单”。

# Default records

```text
00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

说明各文件最小职责，不建立第二套 route/state/event 记录。

Task Sheet 状态只使用：

```text
未完成
已完成
已终止
```

其中 `未完成` 是 automatic resolution 时默认可恢复的 active 状态，不另建 `active` 枚举。

# Minimal reads

默认先读取：

```text
task_index.md
```

然后：

- 已明确 Task Sheet → 读取目标 `Txxxx.md`；
- 尚未明确 → 先用索引中的 `未完成` entries 做候选发现；
- 索引信息不足且只有少数合理 candidates → 只读取这些候选 Task Sheets；
- 不遍历全部历史 Task Sheets。

当前 Task Sheet 明确依赖同一科研任务的前序 Task Sheet 时，可以按明确引用读取该前序记录。

创建或显式重新规划 Task Sheet 时再读取 planning index。

Manager 不为了“全面了解”预读科研 Skills、结果索引、Legacy records 或全项目目录。

# Task Sheet resolution / location

按以下语义设计：

1. 用户明确 ID / 名称或当前上下文已有绑定 → 先核对 `task_index.md` 状态；
2. 状态为 `未完成` 且仍与当前科研指令一致 → 直接绑定；
3. 没有明确绑定 → 主动检查与当前科研指令相关的 `未完成` Task Sheets；
4. 唯一相关 `未完成` Task Sheet → 自动绑定，不要求用户确认；
5. 多个合理相关 `未完成` Task Sheets → 向用户确认；
6. 没有相关 `未完成` Task Sheet → 进入新 Task Sheet 创建；
7. `已完成 / 已终止` 默认只作为历史，不静默重新激活。

不得按“最新”“编号最大”“文件顺序”选择 Task Sheet，也不得把项目中唯一一个但与当前科研指令无关的 `未完成` Task Sheet 自动绑定。

# New Task Sheet boundary

说明：

- 哪些情况继续当前 `未完成` Task Sheet；
- 哪些情况为了控制上下文规模、隔离废弃/错误方案、原 Task Sheet 已闭合或进入新的有界执行段而在**同一科研任务**中建立后续 Task Sheet；
- 哪些情况属于新的独立科研任务。

没有相关 active Task Sheet 且用户当前执行目标已经足够明确时，**直接创建并规划新的 Task Sheet**，不额外询问“是否创建任务单”。

如果新 Task Sheet 的执行范围本身仍有用户意图歧义，先按 shared Task Execution scope-confirmation gate 确认，再创建；不要把 Agent 猜测写成正式计划。

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

Task Sheet 只覆盖当前**已经明确**的执行范围，不要求完整 Workflow 或完整 Stage。局部 Task Sheet 可以从中间 Step 开始，但 current Step 明确定义的 prerequisite 必须已经由当前或前序 Task Sheet 满足。

不得用 planning index 替用户决定仍未明确的执行范围；不得加入 `conditional` / scientific applicability；不得预读具体科研 Skill、预先执行科学判断或查询全部 reuse。只有当前执行范围确实覆盖完整 Stage 时，才按 planning index 的完整 Stage planning 规则展开。

# Task Sheet

示例：

```markdown
# T001 — <Task Sheet 名称>

状态：未完成

## 当前执行目标

<已明确的目标>

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
科研执行请求
→ Task Sheet resolution
  ├─ 唯一相关未完成 Task Sheet → bind
  ├─ 多个相关未完成 Task Sheets → user confirmation
  └─ 无相关未完成 Task Sheet → Manager creates Task Sheet
→ initial planning when creating
→ write / bind Txxxx.md
→ Task Execution Agent continuously executes current Task Sheet
```

普通科研步骤之间不回 Manager，也不重复扫描 `task_index.md`；需要建立后续 Task Sheet 时再进入 Manager。

# Replanning / project management

说明：

- 用户明确要求重新规划；
- 为同一科研任务创建后续 Task Sheet；
- 创建新的科研任务对应 Task Sheet；
- 多 Task Sheet 项目级整理；
- 用户主动返回 Manager；
- 当前执行入口的 Task Sheet resolution 失败或当前绑定已失效。

# User-visible output

定位已有 Task Sheet 时只需简明说明实际绑定对象；创建/重新规划后只展示必要信息：

- Task Sheet ID / 名称；
- Task Sheet 状态；
- 当前计划；
- Task Sheet 路径；
- 必要时注明前序 Task Sheet。

不展示 Legacy route / transaction / event。

# Safety

# Self-check

- [ ] 科研执行入口没有已解析 Task Sheet 时，主动读取 `task_index.md`；
- [ ] automatic active candidate 只使用 `未完成` Task Sheet；
- [ ] 唯一相关未完成 Task Sheet 自动绑定，多候选时才询问；
- [ ] 没有按最近更新时间、最大编号或文件顺序猜 Task Sheet；
- [ ] 没有相关 active Task Sheet 且执行目标明确时，直接创建新 Task Sheet；
- [ ] 新 Task Sheet 范围有歧义时先确认，没有把 Agent 猜测写入正式计划；
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

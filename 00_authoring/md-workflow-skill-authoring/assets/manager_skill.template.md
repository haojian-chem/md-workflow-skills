---
name: <manager-skill-name>
description: <全局 MD 项目、Workstream、路线、状态和记录管理用途及触发边界>。
---

# 目标

# 职责边界

引用：

`00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`

# 输入与请求动作

- 解析可组合的 `INSPECT | PLAN | EXECUTE`；
- 确认 Skill root 与 Project root；
- 确定项目级或 Workstream 级 Focus。

# 项目与 Workstream 状态

引用：

- `03_contracts/project_state.schema.yaml`
- `03_contracts/workstream_state.schema.yaml`

# 项目入口与恢复

处理：

```text
NEW
RESUMABLE
NEEDS_RECOVERY
```

区分项目级恢复与 Workstream 级恢复。

# 路线规划循环

读取：

`00_manager/md_workflow_manager/references/route_planning_protocol.md`

1. 解析起点、终点和停止条件；
2. 按 stage registry 确定涉及的 Workflow；
3. 逐个请求 `workflow_route_fragment.schema.yaml`；
4. 核验相邻 fragment 的 artifact 接口；
5. 拼接并写入 `route_record.schema.yaml`；
6. 未连接 Workflow 在边界形成 PARTIAL/BLOCKED，不虚构内部步骤。

# Workflow 执行循环

1. 解析 Focus Workstream；
2. 只加载当前 Workflow；
3. 请求符合 `workflow_decision.schema.yaml` 的一个决定；
4. 比较 decision 与 active route；
5. 因新证据不一致时先创建 route revision；
6. 若 `EXECUTE`，写入 task record 并构建 `subagent_task`；
7. 串行创建一个临时子 Agent；
8. 核验 `subagent_result`；
9. 写入 task result、event、artifact、decision 或 submission record；
10. 原子更新 Workstream 和项目状态；
11. 再次请求当前 Workflow。

# Workstream

- 创建、选择、分支和结束 Workstream；
- 路线属于 Workstream；
- route fragment 由各 Workflow 产生；
- 完整 route 由 Manager 拼接；
- 路线修订创建新文件，不覆盖旧路线。

# 用户决策

- 子 Agent 不直接向用户提问；
- Manager 创建和解决 decision record；
- 不使用与 `confirmation_items` 重复的确认布尔字段。

# 外部任务

- 支持 tmux 和调度系统；
- 多个外部任务可并存；
- 不高频轮询；
- `FINISHED_UNVERIFIED` 必须经过输出核验后才能进入终态。

# 状态和记录写入

Manager 是以下目录的唯一提交者：

```text
00_project_state/**
00_project_records/**
```

读取 `03_contracts/README.md` 中全部 Manager contracts。

# 用户展示

始终展示两个根目录、Focus、当前位置、route planning status、预计下一任务、当前决策、后台任务和其他活动 Workstream 摘要。

# 失败与恢复

# 自检

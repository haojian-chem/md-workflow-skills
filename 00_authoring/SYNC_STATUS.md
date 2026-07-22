# Authoring 文件同步状态

更新日期：2026-07-22

## 同步范围

本仓库已同步 Phase 1 v2r1 的 authoring 基础文件，包括：

- 17 份 `content_maps/*.yaml`；
- `content_map.schema.yaml`；
- Skill inventory 与文件所有权表；
- 多窗口编写任务单模板；
- `md-workflow-skill-authoring` 的 SKILL、references、assets 和 validation scripts；
- `03_contracts/` 中的共享 schema；
- `AGENTS.md`、评测目录说明及原阶段验证记录。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的文件均未冻结。
- 多窗口正式编写前，必须先读取目标 content map、`file_ownership.yaml`、目标 work order 和本文件。
- `AGENTS.md`、`03_contracts/`、authoring references、content maps、inventory 和 ownership 表仍由主窗口统一修改。
- 业务窗口不得依据旧草案自行修改共享 contract。

## 已确认并写入设计记录的项目模型

1. 当前 Workflow 顺序为：

   `structure_preparation → topology_preparation → md_preparation → md_simulation → analysis`

2. Workflow 是可复用阶段流程；Workstream 是真实项目中的具体工作分支。一个 Workstream 可以经过多个 Workflow，一个项目可以同时存在多个 Workstream。

3. 一个前台临时子 Agent 可以承担：

   - 纯 Operation；
   - 纯 Validator；
   - Operation 与其专属配套 Validator 的连续执行。

4. 任意时刻最多一个前台临时子 Agent，但允许多个 Workstream 和多个 tmux/调度系统外部任务并存。Manager 不高频轮询长耗时任务。

5. 用户请求动作采用可组合形式：

   `INSPECT + PLAN + EXECUTE`

6. 项目入口状态采用：

   `NEW | RESUMABLE | NEEDS_RECOVERY`

   外部任务运行状态不再作为项目级独占入口状态，而归属于具体 Workstream 和 submission。

7. Workstream 状态拆分为：

   - 生命周期：`OPEN | COMPLETED | ARCHIVED | ABANDONED`；
   - 活动状态：`IDLE | READY | EXECUTING | RUNNING_EXTERNAL | WAITING | FAILED | NEEDS_RECOVERY`；
   - 暂停原因：`NONE | USER_DECISION | MISSING_INPUT | DEPENDENCY | USER_PAUSED | EXTERNAL_RESOURCE`。

8. Focus 表示当前一轮 Manager 交互的主要项目或 Workstream 目标，不表示项目唯一活动分支。一个运行周期只有一个主要 Focus，但可以读取多个 related Workstreams。

9. 真实 MD 项目的当前顶层目录为：

```text
<project_root>/
├── 00_project_state/
├── 00_project_records/
├── 01_structure_preparation/
├── 02_topology_preparation/
├── 03_md_preparation/
├── 04_md_simulation/
└── 05_analysis/
```

10. 状态目录采用项目索引加独立 Workstream 状态：

```text
00_project_state/
├── project_state.yaml
├── project_state.yaml.bak
└── workstreams/
    └── <workstream_id>.yaml
```

11. 历史记录按 Workstream 分组：

```text
00_project_records/
├── manager/
├── events/
├── workstreams/
│   └── <workstream_id>/
│       ├── routes/
│       ├── tasks/
│       ├── decisions/
│       └── submissions/
└── state_snapshots/
```

## 已确认但尚未回写共享 contracts 的变更

以下设计已经确认，但当前 `03_contracts/`、runtime protocol、Manager content map 和 inventory 仍需统一更新：

- `subagent_task.schema.yaml` 支持 Operation 与配套 Validator 组成的任务单元；
- 公共状态支持 `RUNNING_EXTERNAL`、Workstream 生命周期、活动状态和暂停原因；
- `project_state.schema.yaml` 改为项目索引加 Workstream 状态文件；
- route、task、decision 和 submission 与 `workstream_id` 关联；
- Focus、related Workstreams 和可组合 requested actions；
- 项目级与 Workstream 级恢复范围。

业务窗口在共享 contracts 更新前不得自行发明这些字段的最终 schema。

## 仍未冻结的事项

- 日志文件的精确字段、事件类型、轮转和保留策略；
- state snapshot 的触发条件和命名规范；
- submission 状态检查与任务完成判定的精确 contract；
- content map 的 `load_when` 与 `applicable_to` 扩展。

## 当前权威设计记录

在共享 contracts 完成更新前，最新已确认设计以以下文件为准：

- 根目录 `README.md`；
- `design_records/manager_and_project_structure_decisions.md`；
- 本文件。

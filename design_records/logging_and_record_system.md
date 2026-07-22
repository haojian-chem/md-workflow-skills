# 项目日志与记录体系设计决策

状态：已确认，待统一回写共享 contracts 与 Manager Skill。

## 1. 基本原则

项目记录分为四层：

1. 当前状态：用于恢复和继续执行；
2. 结构化历史记录：用于审计、恢复和产物谱系追踪；
3. Manager 人类可读会话日志：用于快速理解本轮发生了什么；
4. 科研业务日志：保留在对应阶段业务目录，不复制到管理目录。

同一个事实只能有一个权威来源。其他文件只能引用或摘要，不得重复维护可冲突的副本。

## 2. 目录结构

```text
<project_root>/
├── 00_project_state/
│   ├── project_state.yaml
│   ├── project_state.yaml.bak
│   └── workstreams/
│       └── <workstream_id>.yaml
│
└── 00_project_records/
    ├── manager/
    │   └── sessions/
    │       └── <manager_session_id>.md
    ├── events/
    │   └── project_events.jsonl
    ├── workstreams/
    │   └── <workstream_id>/
    │       ├── routes/
    │       ├── tasks/
    │       ├── decisions/
    │       ├── submissions/
    │       └── artifacts/
    └── state_snapshots/
```

不设置项目级 `workflows/` 记录目录。Workflow 是可复用流程定义；项目中的路线、任务和记录均归属于具体 Workstream。

## 3. 权威来源

### 3.1 当前状态

`00_project_state/project_state.yaml` 是项目级权威入口，保存项目根目录、Skill 根目录、项目入口状态、Workstream 索引、当前 Focus、项目级待处理事项和最后事件引用。

`00_project_state/workstreams/<workstream_id>.yaml` 是该 Workstream 当前状态的权威文件，保存当前位置、状态、当前路线引用、待处理人工决策、外部任务和当前有效产物集引用。

状态目录不保存完整历史。

### 3.2 结构化历史记录

`00_project_records/workstreams/<workstream_id>/` 保存该分支的路线、任务、人工决策、外部提交和产物谱系记录。

### 3.3 项目事件流水

`00_project_records/events/project_events.jsonl` 保存全项目唯一的机器可读事件时间线。

事件流水不替代当前状态，也不保存完整任务内容。

### 3.4 Manager 会话日志

`00_project_records/manager/sessions/<manager_session_id>.md` 保存每次 Manager 进入项目后的精简人类可读摘要。

### 3.5 科研业务日志

GROMACS 日志、命令输出、详细 Validator 报告、结构文件、拓扑文件、轨迹和分析数据保留在对应业务目录。管理记录只保存路径、摘要和必要元数据。

## 4. Manager 会话日志

Manager 日志按会话分文件，不使用持续增长的单一 `manager_log.md`。

建议命名：

```text
mgr_20260722_001.md
```

建议结构：

```markdown
# Manager Session

- Session ID:
- Started at:
- Requested actions:
- Entry state:
- Skill root:
- Project root:
- Focus:
- Related workstreams:

## Inspection summary

## Route changes

## Tasks launched

## User decisions

## External runs

## Final state

## Expected next task
```

会话日志不复制完整命令输出、GROMACS 日志、Validator 详细报告或子 Agent 大段输出，只引用相应记录路径。

## 5. 项目事件流水

全项目只维护一个：

```text
00_project_records/events/project_events.jsonl
```

每行一个独立 JSON 事件。必需字段：

```yaml
schema_version:
event_id:
timestamp:
event_type:
scope:
actor:
summary:
```

按需字段：

```yaml
workstream_id:
object_type:
object_id:
previous_state:
new_state:
record_paths:
related_event_ids:
```

`scope`：

```text
PROJECT
WORKSTREAM
```

`actor`：

```text
USER
MANAGER
SUBAGENT
EXTERNAL_BACKEND
SYSTEM
```

建议事件类型：

### 项目级

```text
PROJECT_INITIALIZED
ENTRY_STATE_EVALUATED
ROOTS_UPDATED
FOCUS_CHANGED
PROJECT_RECOVERY_STARTED
PROJECT_RECOVERY_COMPLETED
PROJECT_RECOVERY_FAILED
STATE_SNAPSHOT_CREATED
```

### Workstream

```text
WORKSTREAM_CREATED
WORKSTREAM_FORKED
WORKSTREAM_POSITION_CHANGED
WORKSTREAM_STATUS_CHANGED
WORKSTREAM_COMPLETED
WORKSTREAM_ARCHIVED
WORKSTREAM_ABANDONED
```

### 路线

```text
ROUTE_CREATED
ROUTE_REVISED
ROUTE_COMPLETED
ROUTE_CANCELLED
```

### 任务

```text
TASK_PREPARED
TASK_STARTED
TASK_DONE
TASK_BLOCKED
TASK_FAILED
TASK_CANCELLED
```

### 人工决策

```text
DECISION_REQUESTED
DECISION_RESOLVED
DECISION_WITHDRAWN
```

### 外部运行

```text
SUBMISSION_PREPARED
SUBMISSION_SUBMITTED
SUBMISSION_STATE_CHANGED
SUBMISSION_COMPLETION_VERIFIED
```

### 产物

```text
ARTIFACT_SET_REGISTERED
ARTIFACT_SET_VALIDATED
ARTIFACT_SET_INVALIDATED
ARTIFACT_SET_SUPERSEDED
```

不记录 `FILE_READ`、`FILE_LISTED`、`LOG_VIEWED` 等无管理意义的低层事件。

## 6. 任务记录

每个临时子 Agent 对应一个任务目录：

```text
00_project_records/workstreams/<workstream_id>/tasks/<task_id>/
├── task.yaml
├── result.yaml
└── notes.md          # 可选
```

### 6.1 task.yaml

由 Manager 在子 Agent 启动前写入，保存：

- Workstream 与 Workflow；
- 任务目标；
- Operation 和可选的专属 Validator；
- 输入文件；
- 允许读取范围；
- 允许写入范围；
- 预期输出；
- gate；
- 已确认的用户决定；
- 返回 contract；
- 详细业务日志位置。

任务一旦启动，`task.yaml` 不再修改。任务内容需要变化时创建新的 `task_id`。

### 6.2 result.yaml

保存结构化结果：

```yaml
task_id:
status:
summary:
operation_result:
validation_result:
artifacts_created:
artifacts_modified:
detail_files:
confirmations:
warnings:
failure:
recommendation:
```

当同一个子 Agent 连续执行 Operation 和专属 Validator 时，必须分别记录：

```yaml
operation_result:
  status: DONE
validation_result:
  status: PASSED
```

不得合并为一个模糊的“成功”。

### 6.3 notes.md

仅在结构化字段不足以表达复杂判断时生成，不作为新的完整日志副本。

### 6.4 任务状态

```text
PREPARED
RUNNING
DONE
BLOCKED
FAILED
CANCELLED
```

`BLOCKED` 是任务终止结果；Workstream 对应转为 `WAITING`。`FAILED` 对应 Workstream 转为 `FAILED`。

## 7. 人工决策记录

每项人工决策一个文件：

```text
00_project_records/workstreams/<workstream_id>/decisions/<decision_id>.yaml
```

建议字段：

```yaml
decision_id:
workstream_id:
status: OPEN
requested_by:
  task_id:
  source:
question:
reason:
options:
recommended_option:
blocking:
resolution:
  selected_option:
  user_statement:
  resolved_at:
  applied_by_task_id:
```

状态：

```text
OPEN
RESOLVED
WITHDRAWN
SUPERSEDED
```

决策文件允许从 `OPEN` 更新到终态；每次变化同时追加项目事件。

## 8. 路线记录

路线记录位置：

```text
00_project_records/workstreams/<workstream_id>/routes/<route_id>.yaml
```

路线文件创建后保持不可变。建议字段：

```yaml
route_id:
workstream_id:
created_at:
created_by:
supersedes:
scope:
  start:
  end:
steps:
change_reason:
assumptions:
conditional_steps:
stop_conditions:
```

当前有效路线由 Workstream 状态中的 `active_route_id` 指定。旧路线通过新路线的 `supersedes` 和事件流水表达替换关系。

## 9. 外部运行记录

位置：

```text
00_project_records/workstreams/<workstream_id>/submissions/<submission_id>.yaml
```

状态：

```text
PREPARED
SUBMITTED
RUNNING
FINISHED_UNVERIFIED
COMPLETED
FAILED
CANCELLED
UNKNOWN
```

`FINISHED_UNVERIFIED` 是必需状态。tmux 会话消失或调度任务结束不能直接判定模拟成功，必须核验日志和预期输出后才能转为 `COMPLETED` 或 `FAILED`。

建议字段：

```yaml
submission_id:
workstream_id:
task_id:
backend:
  type: TMUX | LSF | SLURM | PBS | LOCAL
  session_name:
  job_id:
working_directory:
command_record:
submitted_at:
last_checked_at:
status:
check_policy:
  mode: ON_DEMAND
expected_outputs:
completion_validator:
completion_evidence:
failure_evidence:
```

默认按需检查：用户要求、用户报告完成、后续任务依赖该输出或恢复流程需要时检查。Manager 不高频轮询。

## 10. 产物谱系记录

位置：

```text
00_project_records/workstreams/<workstream_id>/artifacts/<artifact_set_id>.yaml
```

产物类型：

```text
STRUCTURE
TOPOLOGY
SYSTEM
MD_INPUT
MD_OUTPUT
ANALYSIS_RESULT
```

建议字段：

```yaml
artifact_set_id:
artifact_type:
workstream_id:
created_by_task_id:
derived_from:
files:
validation_status:
validator_task_id:
supersedes:
```

产物内容发生实质变化时创建新的 `artifact_set_id`，不得把旧产物身份直接覆盖。新版本通过 `supersedes` 指向旧版本。

## 11. 文件指纹

关键小文件记录 SHA-256：

- PDB、CIF、GRO；
- TOP、ITP；
- MDP；
- 配置文件；
- 映射文件；
- 运行脚本。

大型轨迹和大文件默认只记录：

```yaml
path:
size_bytes:
modified_at:
```

只有明确需要时才计算大型文件哈希，避免为了更新状态扫描数十 GB 数据。

## 12. 状态快照

`00_project_records/state_snapshots/` 只复制状态 YAML，不复制科研业务文件。

触发节点：

- 项目初始化完成；
- Project root 或 Skill root 修改前；
- 项目级恢复前和恢复完成后；
- 创建重要新 Workstream 后；
- 修改 Workstream 产物谱系前；
- 提交首个长耗时外部任务后；
- Workstream 完成、归档或放弃前；
- 项目进入 `NEEDS_RECOVERY` 时。

普通任务结束不自动生成完整快照。

## 13. 写入与状态更新顺序

### 13.1 普通任务

```text
1. Manager 写 task.yaml
2. 追加 TASK_PREPARED 事件
3. 原子更新 Workstream 状态为 EXECUTING
4. 启动子 Agent
5. 子 Agent 执行并返回
6. Manager 写 result.yaml
7. 注册新 artifact set
8. 追加 TASK_DONE、TASK_BLOCKED 或 TASK_FAILED 事件
9. 原子更新 Workstream 当前状态
10. 写 Manager session 摘要
```

### 13.2 有外部副作用的提交任务

```text
1. 写 submission.yaml，状态 PREPARED
2. 保存提交命令和确定性 session name 或 job script
3. 实际执行提交
4. 记录 session name 或 job ID
5. 更新 submission 为 SUBMITTED 或 RUNNING
6. 追加提交事件
7. 原子更新 Workstream 状态
```

原则：先记录准备执行的内容，再产生外部副作用，最后记录实际结果并更新当前状态。

## 14. 写权限

### Manager

可写：

```text
00_project_state/**
00_project_records/**
```

Manager 不直接写科研业务结果。

### Operation

只写任务授权的业务目录和文件。

### Validator

只写任务授权的详细验证报告和验证结果文件，不直接修复或覆盖业务对象。

### 临时子 Agent

不得直接修改 `00_project_state/` 或 `00_project_records/`。子 Agent 执行业务任务、写业务日志并返回结构化结果，由 Manager 统一提交状态和历史记录。

## 15. 保留策略

结构化管理记录全部保留：

- task.yaml 与 result.yaml；
- route；
- decision；
- submission；
- artifact manifest；
- event log；
- Manager session summary；
- 关键状态快照。

轨迹、GROMACS 完整日志、大型中间文件和分析数据不复制到管理目录，保留在业务目录并由结构化记录引用。

# 项目日志与记录体系设计决策

状态：已确认。

## 1. 基本原则

项目记录分为四层：

1. 当前状态：用于恢复和继续执行；
2. 结构化历史记录：用于审计、恢复和产物谱系追踪；
3. Manager 会话摘要：用于快速理解本轮发生了什么；
4. 科研业务日志：保留在对应业务目录，不复制到管理目录。

同一个事实只能有一个权威来源。其他文件只能引用或摘要，不得重复维护可冲突的副本。

记录必须满足恢复与审计需要，但不得在普通 task 闭环中机械更新所有记录对象。

## 2. 目录结构

```text
<project_root>/
├── 00_project_state/
│   ├── project_state.yaml
│   ├── project_state.yaml.bak
│   └── workstreams/
│       └── <workstream_id>.yaml
└── 00_project_records/
    ├── manager/sessions/<manager_session_id>.md
    ├── events/project_events.jsonl
    ├── workstreams/<workstream_id>/
    │   ├── routes/
    │   ├── tasks/
    │   ├── decisions/
    │   ├── submissions/
    │   └── artifacts/
    └── state_snapshots/
```

不设置项目级 `workflows/` 记录目录。Workflow 是可复用流程定义；项目中的路线、任务和记录均归属于具体 Workstream。

## 3. 权威来源

### 3.1 项目索引

`00_project_state/project_state.yaml` 只保存：

- project 与两个根目录；
- 持久入口状态；
- Workstream 索引；
- 当前 Focus 与 related Workstreams；
- 项目级 pending decisions；
- 最后项目事件引用。

普通 task 完成时，如果这些字段没有变化，不得重写 `project_state.yaml`。

只在以下情况更新项目索引：

- Focus 改变；
- Workstream 新建、归档、放弃或索引变化；
- 项目级 pending decision 改变；
- 根目录、入口状态或项目级恢复状态改变；
- 最后项目事件引用确需作为项目级恢复锚点更新。

### 3.2 Workstream 当前状态

`00_project_state/workstreams/<workstream_id>.yaml` 是该 Workstream 当前状态的权威文件，保存：

- current position；
- lifecycle/activity status；
- active route/task/submissions；
- hold reason 与 pending decisions；
- 当前有效 artifact set 引用；
- 最后 Workstream 事件。

普通 task 闭环通常只需要更新目标 Workstream state，不需要更新 project state。

### 3.3 结构化历史记录

`00_project_records/workstreams/<workstream_id>/` 保存该分支的不可变路线、任务、submission 和 artifact 记录，以及允许从 OPEN 更新到终态的 decision 记录。

### 3.4 项目事件流水

`00_project_records/events/project_events.jsonl` 保存全项目唯一机器可读时间线。

事件记录管理状态变化，不记录 `FILE_READ`、`FILE_LISTED`、`LOG_VIEWED` 等低层动作。

### 3.5 Manager 会话摘要

Manager 在进入项目时生成 session ID，但会话文件默认在本轮暂停或结束时一次性写入。

只有以下情况允许中途写 checkpoint：

- blocking user decision；
- task failure 或权限违规；
- 外部任务提交；
- 进入恢复；
- 进程即将结束且尚无最终摘要。

普通 task 完成后不得为了追加一段摘要而单独重写 Manager session。任务结果由 `result.yaml`、终态 event 和 Workstream state 表达；会话结束时再汇总引用。

### 3.6 科研业务日志

GROMACS 日志、命令输出、详细 Validator 报告、结构、拓扑、轨迹和分析数据保留在业务目录。管理记录只保存路径、摘要和必要元数据。

## 4. 任务记录

每个临时子 Agent 对应一个任务目录：

```text
00_project_records/workstreams/<workstream_id>/tasks/<task_id>/
├── task.yaml
├── result.yaml
└── notes.md          # 可选
```

### 4.1 task.yaml

由 Manager 在子 Agent 启动前写入，保存任务目标、Skill、输入、路径权限、预期输出、gate、已解决决定、返回 contract 和详细日志位置。

`task.yaml` 写入即表示任务已准备。任务内容变化时创建新 task ID，不修改旧 task。

### 4.2 result.yaml

保存符合共享 contract 的结构化终态结果。Operation 与 Validator 即使在同一子 Agent 中连续执行，也必须分开记录。

### 4.3 notes.md

仅在结构化字段不足以表达复杂判断时生成，不作为新的完整日志副本。

## 5. 普通前台 task 的最小同步闭环

普通前台 task 指：

- 在当前进程内完成；
- 不提交 tmux/调度系统等外部任务；
- 预计耗时较短；
- 不包含难以恢复的高风险或不可逆副作用。

提交前：

```text
1. 写不可变 task.yaml
2. 创建一个临时子 Agent
```

完成后：

```text
1. 校验 subagent_result
2. 写 result.yaml
3. 有新产物、决定或 submission 时才写对应记录
4. 追加一条 TASK_DONE、TASK_BLOCKED 或 TASK_FAILED 终态事件
5. 原子更新目标 Workstream state
6. 输出可见 task closure summary
7. 再请求 Workflow 判断下一步
```

普通前台 task 默认不执行：

- `TASK_PREPARED` event；
- `TASK_STARTED` event；
- 执行前将 Workstream state 改为 `EXECUTING`；
- 无字段变化的 project state 更新；
- Manager session 的逐 task 增量写入；
- state snapshot；
- 无实际变化的 route revision；
- 没有新对象时的 artifact/decision/submission 记录。

`task.yaml` 与缺失的 `result.yaml` 足以在异常中断后识别未闭环任务；恢复时由 Manager 判断其实际状态。

## 6. 需要强化预记录的 task

以下任务在产生副作用前必须先写准备事件并更新状态：

- 外部 submission；
- 长耗时任务；
- 高风险或不可逆操作；
- 中断后必须准确区分“尚未启动”和“已启动”的任务；
- Workflow 或 Operation 明确要求预提交恢复锚点。

此时采用：

```text
1. 写 task.yaml
2. 追加 TASK_PREPARED
3. 原子更新 Workstream 为 EXECUTING
4. 必要时追加 TASK_STARTED
5. 产生副作用
6. 写 result/相关记录/终态事件
7. 原子更新 Workstream
```

`TASK_STARTED` 只用于确有恢复价值的长任务或高风险任务，不作为普通 task 的固定事件。

## 7. 外部 submission

外部任务必须保留：

```text
PREPARED → SUBMITTED → RUNNING → FINISHED_UNVERIFIED
                                      ↓
                              COMPLETED | FAILED
```

另有 `CANCELLED | UNKNOWN`。

提交前先写 submission record、确定性命令、session name 或 job script，再产生外部副作用。tmux/session/job 消失不能直接判定成功，必须由 Validator 核验输出。

## 8. Artifact set

仅在出现新的 artifact candidate、validation status 改变、artifact 失效或 supersedes 关系变化时写 artifact record。

关键小文件记录 SHA-256。大型轨迹默认记录 path、size 和 modified time，仅在明确需要时计算 hash。

## 9. Route

路线文件创建后不可变。只有预计步骤、条件、终点、blocker 或 provenance 实际改变时创建 revision。

当前位置正常前进但预计路线不变时，只更新 Workstream current position，不创建 route revision，也不重写 route。

## 10. State snapshot

只在以下关键节点创建：

- 项目初始化完成；
- Project root 或 Skill root 修改前；
- 项目级恢复前后；
- 重要 Workstream 创建；
- artifact 谱系重大替换前；
- 首个长耗时外部任务提交后；
- Workstream 完成、归档或放弃前；
- 项目进入 NEEDS_RECOVERY。

普通 Operation/Validator 完成后不创建 snapshot。

## 11. Task closure 的用户可见输出

每个前台 task unit 进入 `DONE | BLOCKED | FAILED` 后，Manager 必须在启动下一前台 task 前输出一次精简的 task closure summary。

该输出：

- 不是新的结构化记录；
- 不要求用户确认；
- 不复制完整日志；
- 不把 Operation 完成误写成科学质量验证通过；
- 可引用 result、report 和 artifact 路径。

宿主支持中间可见消息时，输出后可继续既定执行范围；宿主不支持中间消息时，本轮以 closure summary 结束，并把下一任务列为 expected next task。

DONE 至少显示：

- task/substep；
- Operation/Validator 终态与 gate 结果；
- 关键动作或产物；
- warnings；
- 产物 validation status；
- 预计下一任务。

BLOCKED 至少显示：已完成部分、阻断原因、所需决定和未启动的后续任务。

FAILED 至少显示：失败位置、直接证据、保留产物、当前状态及可选后续。

例如 `source_recognition` 完成只能表述为来源识别、复制与 hash 检查通过；其 STRUCTURE artifact 在后续 Validator 前仍是 `UNVALIDATED`。

## 12. 写权限

Manager 是以下目录的唯一提交者：

```text
00_project_state/**
00_project_records/**
```

Operation/Validator 只写 task 授权的业务路径。临时子 Agent 不得直接修改管理目录。

## 13. 保留策略

保留：

- task.yaml 与 result.yaml；
- route；
- decision；
- submission；
- artifact manifest；
- project event；
- Manager session final summary；
- 关键状态快照。

科研大型文件与完整日志不复制到管理目录。
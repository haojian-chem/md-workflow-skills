# 项目日志与记录体系设计决策

状态：已确认。

## 1. 基本原则

项目记录分为四层：

1. 当前状态：用于恢复和继续执行；
2. 结构化历史记录：用于审计、恢复和产物谱系追踪；
3. Manager 会话摘要：用于快速理解本轮发生了什么；
4. 科研业务日志：保留在对应业务目录，不复制到管理目录。

同一个事实只能有一个权威来源。其他文件只能引用或摘要，不得重复维护可冲突的副本。

记录必须满足恢复与审计需要，但普通 task 不得机械更新所有记录对象。

schema、直接引用、机械记录构造和普通 task 事务优先由已注册确定性 Tool 完成，不由 Manager LLM 逐字段模拟。

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

不设置项目级 `workflows/` 记录目录。Workflow 是可复用流程定义；项目路线、任务和记录归属于具体 Workstream。

Tool cache 不属于权威状态或记录，必须可删除、可重建，并使用 Tool 注册的 cache 路径。

## 3. 权威来源

### 3.1 Project state

`00_project_state/project_state.yaml` 只保存：

- project 与两个 root；
- 持久入口状态；
- Workstream 索引；
- 当前 Focus 与 related Workstreams；
- 项目级 pending decisions；
- 最后项目事件引用。

普通 task 若这些项目级字段未变化，不得重写 `project_state.yaml`。

只在以下情况更新 project state：

- Focus 改变；
- Workstream 新建、归档、放弃或索引变化；
- 项目级 pending decision 改变；
- root、entry state 或项目级 recovery 状态改变；
- 最后项目事件确需作为项目级恢复锚点更新。

### 3.2 Workstream state

`00_project_state/workstreams/<workstream_id>.yaml` 是该 Workstream 当前状态的权威文件，保存：

- current position；
- lifecycle/activity status；
- active route/task/submissions；
- hold reason 与 pending decisions；
- 当前 artifact set 引用；
- 最后 Workstream event。

普通 task 闭环通常只更新目标 Workstream state，不更新 project state。

### 3.3 结构化历史记录

`00_project_records/workstreams/<workstream_id>/` 保存该分支的不可变 route、task、submission、artifact 记录，以及允许从 OPEN 更新到终态的 decision 记录。

### 3.4 项目事件流水

`00_project_records/events/project_events.jsonl` 保存全项目唯一机器可读时间线。

事件记录管理状态变化，不记录 `FILE_READ`、`FILE_LISTED`、`LOG_VIEWED` 等低层动作。

### 3.5 Manager 会话摘要

Manager 进入项目时可生成 session ID，但 session 文件默认在本轮暂停或结束时一次性写入。

只有以下情况允许中途 checkpoint：

- blocking user decision；
- task failure 或权限违规；
- 外部任务提交；
- 进入 recovery；
- 进程即将结束且尚无最终摘要。

普通 task 完成后不得为了追加摘要而单独重写 Manager session。task result、终态 event 和 Workstream state 已表达闭环事实。

### 3.6 科研业务日志

GROMACS 日志、命令输出、详细 Validator 报告、结构、拓扑、轨迹和分析数据保留在业务目录。管理记录只保存路径、摘要和必要元数据。

## 4. Task 记录

每个业务 task unit 对应：

```text
00_project_records/workstreams/<workstream_id>/tasks/<task_id>/
├── task.yaml
├── result.yaml
└── notes.md          # 可选
```

task unit 的执行后端可以是：

```text
DETERMINISTIC
AGENT_TASK
AGENT_SEQUENCE       # 未激活前不得使用
```

因此 task 记录不再等同于“一个临时子 Agent 记录”。

### 4.1 task.yaml

由 Manager 在业务执行前写入，保存 task identity、逻辑 Operation/Validator、输入、路径权限、预期输出、gate、已解决决定、返回 contract 和详细日志位置。

`task.yaml` 写入即表示 task 已准备。task 内容变化时创建新 task ID，不修改旧 task。

### 4.2 result.yaml

保存符合共享 result contract 的终态责任结果。Operation 与 Validator 即使共享同一 Agent context，也必须分开记录各自结果。

普通 task 的正式 `result.yaml` 由 ACTIVE `runtime_record_committer` 在候选 FAST PASS 后提交。

### 4.3 notes.md

仅在结构化字段不足以表达复杂判断时生成，不作为新的完整日志副本。

## 5. 普通前台 task 的最小同步闭环

普通前台 task 指：

- 在当前进程内完成；
- 不提交 tmux/调度系统外部任务；
- 预计耗时较短；
- 不包含难以恢复的高风险或不可逆副作用。

### 5.1 执行前

```text
1. 写不可变 task.yaml
2. 根据 runtime spec + ACTIVE capability 解析执行后端
3. DETERMINISTIC：直接调用对应业务 Tool
4. AGENT_TASK：创建一个前台 Agent context
```

`AGENT_SEQUENCE` 未满足激活条件前不得使用。

### 5.2 执行完成后的正常路径

业务后端先返回结构化 terminal responsibility result。

若当前 active route、compact Workflow spec 和结构化证据足以确定 R5 evaluation context：

```text
terminal responsibility result
→ route_fast_path_evaluator
→ ADVANCE | REENTER_WORKFLOW | STOP_SCOPE | BLOCKED
```

- `ADVANCE`：将 evaluator 给出的 `next_route_position` 作为显式 route progression；
- `STOP_SCOPE`：本轮达到用户范围终点，不启动下一 task；
- `REENTER_WORKFLOW`：进入完整 Workflow 语义判断，再形成显式 progression/state delta；
- `BLOCKED`：交由 Manager 处理状态冲突或 recovery，不自行推进。

随后由 ACTIVE `runtime_record_committer` 完成普通 task 机械闭环：

```text
responsibility result
+ explicit semantic state delta
+ explicit route progression
+ explicit artifact/decision/submission updates
→ candidate result/records/Workstream state/event
→ one runtime_schema_validator FAST
→ controlled commit / rollback
→ compact commit receipt
```

Manager 不在 recorder 后重复 FAST，也不重新转写 recorder 已生成的 YAML。

提交成功后：

```text
→ 输出精简 task closure summary
→ 若 fast path 已 ADVANCE 且用户范围未结束，可直接准备下一 route node
→ 只有语义 trigger 才重新进入完整 Workflow
```

### 5.3 默认不执行

普通前台 task 默认不执行：

- `TASK_PREPARED` event；
- `TASK_STARTED` event；
- 无变化的 project state 更新；
- Manager session 逐 task 增量写入；
- state snapshot；
- 无实际变化的 route revision；
- 没有新对象时的 artifact/decision/submission 记录；
- FULL validation；
- task 成功后的机械性 Workflow 全文重判。

`task.yaml` 存在但 `result.yaml` 缺失时，recovery 流程必须将其视为未闭环 task，不假定未启动或已完成。

## 6. 需要强化预记录的 task

以下 task 在产生副作用前必须建立恢复锚点：

- 外部 submission；
- 长耗时 task；
- 高风险或不可逆操作；
- 中断后必须准确区分“未启动”和“已启动”的 task；
- Workflow/Operation 明确要求预提交恢复锚点。

此时采用强化生命周期，不强行套用普通 R4 路径：

```text
1. 写 task.yaml
2. 追加 TASK_PREPARED
3. 原子更新 Workstream 为 EXECUTING
4. 必要时 TASK_STARTED
5. 产生副作用
6. 准备 result/相关记录/state
7. 执行适用 validation
8. 受控提交终态记录和 state
```

`TASK_STARTED` 只用于确有恢复价值的长任务或高风险任务。

## 7. 外部 submission

外部任务保留：

```text
PREPARED → SUBMITTED → RUNNING → FINISHED_UNVERIFIED
                                      ↓
                              COMPLETED | FAILED
```

另有 `CANCELLED | UNKNOWN`。

提交前先写 submission record、确定性命令、session name 或 job script，再产生外部副作用。tmux/session/job 消失不能直接判成功，必须由 Validator 核验输出。

## 8. Artifact set

仅在出现新的 artifact candidate、validation status 改变、artifact 失效或 supersedes 关系变化时写 artifact record。

关键小文件记录 SHA-256。大型轨迹默认记录 path、size、modified time；仅在明确需要时计算 hash。

未经 Validator/明确权威证据不得把 artifact 标为 `VALIDATED`。R4 不推断 validation status，必须由调用方显式提供。

## 9. Route

route record 创建后不可变。只有预计步骤、条件、终点、blocker 或 provenance 实际改变时创建 revision。

正常位置前进但 route 未变时，只更新 Workstream current position；R5 fast path 不创建 route revision。

## 10. State snapshot

snapshot 只在存在明确恢复价值的关键节点创建：

- Project root 或 Skill root 修改前；
- 项目级 recovery 前后；
- 重要 Workstream 创建；
- artifact 谱系重大替换前；
- 首个长耗时外部任务提交后；
- Workstream 完成、归档或放弃前；
- 项目进入 `NEEDS_RECOVERY`。

NEW 初始化不创建 snapshot。首次权威 project/Workstream state、初始化事件及 candidate/backup/失败证据已经构成恢复锚点。

普通 Operation/Validator 完成后不创建 snapshot。

## 11. Task closure 的用户可见输出

每个前台 task unit 进入 `DONE | BLOCKED | FAILED` 后，Manager 必须在启动下一前台 task 前输出一次精简 closure summary。

该输出：

- 不是新的结构化记录；
- 不要求用户确认；
- 不复制完整日志；
- 不把 Operation 完成误写成科学质量验证通过；
- 可引用 result/report/artifact 路径。

DONE 至少显示：task/substep、Operation/Validator 终态、gate、关键动作/产物、warnings、artifact validation status、预计下一任务。

BLOCKED 至少显示：已完成部分、阻断原因、所需决定、未启动后续。

FAILED 至少显示：失败位置、直接证据、保留产物、当前状态、可选后续。

例如 `source_recognition` 完成只能表述为来源识别/复制/hash 检查通过；STRUCTURE 在独立科学 Validator 前仍可保持 `UNVALIDATED`。

## 12. Validation profiles

权威规则：

`00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`

### NEW initialization

使用 `INIT_CANDIDATE_VALIDATION`：

```text
runtime_schema_validator FAST
+ only candidate project_state
+ only candidate initial Workstream state
+ logical-path overlay
+ direct references
```

NEW 初始化**不执行 FULL**，也不把 PDB/mmCIF/业务文件加入 candidate validation target。

### Ordinary task

ACTIVE `runtime_record_committer` 内部对本次 changed runtime candidates 执行一次 FAST；Manager 不重复调用。

### FULL

FULL 仅用于 project-wide audit 节点，例如：

- schema/contract 变化；
- recovery 前后；
- Project root / Skill root 变化；
- 权威协议明确的重要 Workstream / artifact lineage 生命周期节点；
- Workstream 完成/归档/放弃前；
- 用户明确要求完整审计。

FULL 不再是 NEW 初始化 gate。

schema bundle hash 未变化且 cache 有效时，不重复 meta-validation。

Tool FAIL/ERROR 时不得提交候选终态、宣称通过或降低 gate；INIT/FAST failure 也不得通过“改跑 FULL”绕过。

## 13. 写权限

Manager 控制：

```text
00_project_state/**
00_project_records/**
```

“Manager 控制提交”允许 ACTIVE deterministic recorder 在 Manager 显式授权和 contract 范围内完成机械写入；不要求 Manager LLM 手工生成文件。

Operation/Validator/业务 Agent 只写 task 授权业务路径，不直接写管理目录。

Tool 只能使用 registry 与 `tool.yaml` 声明的读写范围。

## 14. 保留策略

保留：

- task.yaml / result.yaml；
- route；
- decision；
- submission；
- artifact manifest；
- project event；
- Manager session final summary；
- 关键 state snapshots。

Tool cache 不属于保留型结构化记录。科研大型文件和完整日志不复制到管理目录。

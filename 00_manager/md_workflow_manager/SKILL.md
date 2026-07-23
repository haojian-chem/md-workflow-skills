---
name: md_workflow_manager
description: 管理真实 MD 项目的入口初始化、Workstream、Focus、跨 Workflow 路线、串行临时子 Agent、项目状态、精简记录、确定性校验工具、用户决策和外部模拟任务。用于检查、规划、执行、续跑或恢复 MD 工作流；不执行具体结构、拓扑、模拟或分析业务操作。
---

# 目标

统一管理真实 MD 项目的入口状态、初始化、路线范围、Workstream、Focus、Workflow 接口、最多一个前台临时子 Agent、外部任务、产物谱系、用户决策和可恢复记录。

Manager 不承担 Operation 或 Validator 的业务工作。确定性 schema、引用和状态事务优先交给已注册 Tool，不由 LLM 逐字段模拟。

# 启动时读取

按需读取：

1. 项目根 `AGENTS.md`；
2. `03_contracts/README.md` 与本轮适用 schema；
3. `00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`；
4. `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
5. `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`；
6. `05_tools/tool_registry.yaml`；
7. `design_records/logging_and_record_system.md`；
8. `references/stage_registry.yaml`；
9. 发生路线范围解析、PLAN、route 创建或 revision 时读取 `references/route_planning_protocol.md`；
10. `references/manager_display_rules.md`；
11. 项目索引、Focus Workstream state 及其 active route、decision、submission、artifact records；
12. 规划时逐个读取涉及范围内的 Workflow，执行时只读取当前 Workflow。

不得一次性载入全部项目历史、科学日志、轨迹或无关 Skill。

# 使用边界

用于：初始化、检查、规划、执行、续跑、恢复、创建参数/对照/重复/测试 Workstream，以及管理结构准备、拓扑准备、MD 准备、MD 模拟和分析流程。

不用作：一般 MD 问答、单个业务命令执行、业务文件修改、科学质量判定、Skill/Tool 编写窗口管理。

# 核心职责

Manager 负责：

- 解析可组合的 `INSPECT | PLAN | EXECUTE`；
- 判断 `NEW | RESUMABLE | NEEDS_RECOVERY`；
- 对 NEW 项目自动完成初始化；
- 在初始化后独立解析路线范围；
- 选择 `PROJECT | WORKSTREAM` Focus；
- 创建、分支、选择、完成、归档或放弃 Workstream；
- 请求 Workflow 返回 route fragment 或实时 execution decision；
- 拼接 route，并在必要时创建 revision；
- 构建一个 task unit 并串行调用一个临时子 Agent；
- 核验 subagent result；
- 调用已注册确定性 Tool 完成 schema、引用和状态事务；
- 唯一提交 `00_project_state/**` 和 `00_project_records/**`；
- 以最小必要写入维护恢复能力；
- 在每个前台 task 闭环后向用户输出精简结果；
- 决定暂停、恢复、重试或重新规划。

Manager 不得：

- 把 NEW 判定、初始化、路线范围解析、规划和执行合并成隐式步骤；
- 在初始化完成前调用 Workflow；
- 在路线范围未明确时选择默认终点；
- 在 active route 不存在或不适用时创建业务 task；
- 根据阶段名称编造 Workflow 内部步骤；
- 脱离 Workflow decision 选择 Operation/Validator；
- 同时创建多个前台子 Agent 或嵌套委派；
- 在主上下文解析大型业务文件；
- 直接修改结构、拓扑、MDP、轨迹或分析结果；
- 因后台任务存在而自动切换 Focus；
- 覆盖已有下游结果；
- 自动重试失败 task、降低 gate、跳过 Validator；
- 为追求记录完整而机械重写全部状态和日志；
- 对普通 task 执行 FULL contract validation；
- 在 schema hash 未变化且 cache 有效时重复 schema meta-validation；
- 用 LLM 逐字段模拟 FULL schema 或项目级引用校验；
- 静默完成前台 task 后直接启动下一 task，而不输出 closure summary。

# 项目目录与权限

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

Manager 可创建管理目录和顶层阶段目录，但不创建阶段业务文件。Operation/Validator 只能写 task 授权的业务路径。

确定性 Tool 只能使用 `tool_registry.yaml` 和自身 `tool.yaml` 声明的权限。cache 必须是可删除、可重建的非权威数据。

# 项目进入

## 1. 根目录

分别确认或读取 Skill architecture root 与 MD project root。

- 首次且无可信状态时确认一次；
- 有效状态下自动读取并核验；
- 路径缺失、移动或冲突时进入恢复；
- 更新根目录不得隐式迁移业务文件；
- 用户展示中始终显示两个根目录。

## 2. 最小检查

检查：状态可解析、schema 受支持、两个根目录有效、Workstream state 可定位、Focus 可解析、无冲突前台 task、无项目级阻断决定和明显目录所有权冲突。

只读取清单和元数据，不扫描大型轨迹或科学内容。

## 3. 入口状态

### NEW

仅当没有可读状态、目录为空或只有初始输入，且没有明显旧结构、拓扑、完整体系或模拟产物。

`NEW` 只是本轮入口判定，不是初始化后的持久状态，也不包含范围解析、规划或执行。

根目录明确且无冲突时，Manager 必须自动初始化，不等待用户额外提示。

初始化事务：

1. 记录入口检查，准备 `ENTRY_STATE_EVALUATED: NEW`；
2. 创建管理目录和顶层阶段目录；
3. 生成 project ID、首个 Workstream 和 Focus；
4. 在候选路径生成 project/workstream state；
5. 候选 project state 的持久 `entry_state` 设为 `RESUMABLE`；
6. 对候选状态执行 FULL schema、路径、索引和交叉引用校验；
7. 通过受控状态事务提交；
8. 追加 `ENTRY_STATE_EVALUATED`；
9. 追加 `PROJECT_INITIALIZED`；
10. 创建初始 snapshot 并重新读取核验。

初始 Workstream：

```yaml
current_position:
  workflow_name: null
  substep: null
  task_id: null
activity_status: IDLE
active_route_id: null
active_task_id: null
```

初始化不创建 route，不调用 Workflow，不创建 task。

`PROJECT_INITIALIZED` 只能在候选状态检查和提交成功后追加。部分提交异常进入 `NEEDS_RECOVERY`；提交前失败返回 `BLOCKED`。

### RESUMABLE

项目索引可信且当前目标可安全解释。NEW 成功初始化后的持久状态也使用 `RESUMABLE`。

### NEEDS_RECOVERY

状态损坏或不兼容、根目录不明、Workstream 索引冲突、目标分支不可解释、目录所有权冲突、artifact 版本冲突、外部状态无法对应事实，或旧项目有大量产物但无可信记录时使用。

项目级恢复完成前不创建写入型 task。

# 初始化后的请求与路线范围

- NEW 必须先完成 `PROJECT_INITIALIZED`；
- RESUMABLE 完成入口检查后进入本节；
- NEEDS_RECOVERY 恢复前不得规划或执行。

## 请求动作

- `INSPECT`：读取并核验状态与记录；科学判断交给 Validator；
- `PLAN`：在范围明确后创建或修订 route；
- `EXECUTE`：仅在范围明确且 active route 有效时推进。

纯 INSPECT 不要求路线范围。

## 路线范围解析

范围解析独立于 NEW 初始化和 PLAN。

只有以下来源明确给出终点时才可解析：

- 用户明确指定 substep、gate、Workflow、artifact、Workstream 目标或项目终点；
- resolved decision 明确记录终点；
- 用户明确要求继续一个有效 active route；
- Workstream 目标已明确记录，且用户明确要求按该目标继续。

“开始处理这个结构”“跑一下流程”“测试一下这个项目”或无 active route 时的“继续做”不构成明确终点。

终点不明确时：

1. 创建 blocking decision；
2. 追加 `ROUTE_SCOPE_REQUESTED`；
3. Workstream 置为 `WAITING / USER_DECISION`；
4. 向用户确认终点；
5. 不调用 Workflow、不创建 route、不创建 task。

不得默认选择下一 task、下一 gate、当前 Workflow 结束、Workstream 目标或项目终点。

范围落盘后追加 `ROUTE_SCOPE_RESOLVED`，再进入 PLAN。范围解析本身不创建 route。

# Focus 与 Workstream

一个 Manager 周期只有一个主要 Focus：

- `PROJECT`：全项目检查、恢复、多分支汇总或全局冲突；
- `WORKSTREAM`：具体分支规划、执行、恢复或决定处理。

Workstream 必须有稳定 ID、用户可读 title 和 purpose。初始 purpose 不得把未确认终点写成既定目标。

Focus 选择优先级：用户指定 → 指定对象所属分支 → 本轮执行目标 → 未闭环前台 task → 最近 Focus → 仍不唯一则确认。

后台 MD 不自动改变 Focus。

Workstream ID：

```text
ws_0001_<slug>
```

ID 创建后不随 title 修改。

首个 Workstream 可在初始化时创建，但范围解析前保持 `active_route_id: null`。

当前步骤未闭合、无有效下游依赖、未开始 EM/NVT/NPT/MD、无需保留旧版本且修改不影响其他结果时，允许在原 Workstream 修正。

已有下游产物、模拟已开始、需保留旧版本、需比较方案/重复/对照/测试，或上游修改可能使既有结果失效时，必须创建新 Workstream。

新 Workstream 创建不自动触发 route；范围必须独立解析。

# Workflow 规划接口

进入 PLAN 前必须满足：

- 项目已初始化或可信 RESUMABLE；
- Focus Workstream 已确定；
- 范围已通过 `ROUTE_SCOPE_RESOLVED` 或有效 active route 明确；
- 不处于项目级恢复。

严格执行 `references/route_planning_protocol.md`：

1. 读取已解析起点、终点和停止条件；
2. 按 registry 确定 Workflow 范围；
3. 串行请求各已连接 Workflow 返回 fragment；
4. 核验相邻 artifact 接口；
5. 拼接并写 `route_record.schema.yaml`；
6. 未连接 Workflow 在边界形成 PARTIAL/BLOCKED。

路线是动态投影，不是硬执行队列。只在实际变化时创建 revision。

# Workflow 执行接口

实际推进前确认：

- 项目已初始化或可信 RESUMABLE；
- 路线范围已解析；
- `active_route_id` 非空且适用；
- 当前执行位置位于 route 范围内。

只加载当前 Workflow，并请求一个：

```text
EXECUTE | SKIP | PAUSE | COMPLETE | BLOCKED
```

- `EXECUTE`：创建一个 task unit；
- `SKIP`：必须有有效证据；
- `PAUSE/BLOCKED`：持久化必要决定或状态，不创建子 Agent；
- `COMPLETE`：核验 gate 和出口 artifact；达到用户终点则停止，否则进入下一个已连接 Workflow。

Decision 与 active route 因新证据不一致时，先 revision，再执行；无法解释时暂停或恢复。

# 临时子 Agent 与 task 闭环

允许：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

组合模式只用于 Operation 与专属 Validator 共享即时上下文，两部分结果必须分开。

严格执行 `runtime_subagent_protocol.md`、`subagent_task.schema.yaml` 和 `subagent_result.schema.yaml`。

## 普通前台 task

普通 task 指短耗时、当前进程内完成、无外部 submission、无难以恢复的高风险副作用。

提交前：

1. 生成 task ID；
2. 写不可变 `task.yaml`；
3. 创建一个临时子 Agent。

普通 task 默认不写 `TASK_PREPARED`、`TASK_STARTED`，也不在执行前机械更新 Workstream 为 EXECUTING。

完成后：

1. 核验 subagent 返回的 ID、mode、分离结果、终态、路径权限、detail files、decision 和 failure；
2. 在候选路径准备 `result.yaml`、必要 artifact/decision/submission 和 Workstream state；
3. 对本次 changed paths 执行一次 FAST schema 与直接引用校验；
4. FAST PASS 后提交必要记录和目标 Workstream state；
5. 追加一条 `TASK_DONE | TASK_BLOCKED | TASK_FAILED`；
6. 输出可见 task closure summary；
7. 再请求 Workflow 判断下一步。

普通 task 完成时，若项目索引字段没有变化，不更新 `project_state.yaml`；不写 snapshot；不逐 task 重写 Manager session；不创建无变化 route revision。

`task.yaml` 存在但 `result.yaml` 缺失时，恢复流程将其视为未闭环 task 并核查实际状态。

## 强化预记录 task

外部 submission、长耗时、高风险、不可逆或中断后必须区分是否已启动的 task，采用：

```text
写 task.yaml
→ TASK_PREPARED
→ Workstream EXECUTING
→ 必要时 TASK_STARTED
→ 产生副作用
→ 候选 result/相关记录
→ FAST 或适用 FULL 校验
→ 终态事件与状态提交
```

# FAST 与 FULL 校验

权威规则见 `deterministic_tool_protocol.md`。

## FAST

普通 task 默认 FAST：

- 只校验本次新增或修改的 runtime instances；
- 只检查这些对象的直接引用；
- 一次 Tool 调用批量处理 changed paths；
- schema bundle hash cache 命中时不重复 meta-validation；
- 不扫描全部项目历史。

FAST 失败时不得提交候选终态，不得宣称 task 闭环成功。

## FULL

FULL 只在以下节点执行：

- 项目初始化候选状态提交前；
- schema/contract 变化；
- 项目恢复前后；
- Project root 或 Skill root 变化；
- 重要 Workstream 创建；
- 重大 artifact 谱系变化；
- 首个外部长任务提交前；
- Workstream 完成、归档或放弃前；
- 用户明确要求完整审计。

FULL 不得在每个普通 task 后机械运行。

## Tool 选择与失败

- 优先使用 `tool_registry.yaml` 中状态为 `ACTIVE` 且版本兼容的 Tool；
- `IMPLEMENTED` 但未测试的 Tool 不得作为默认生产路径；
- Tool 不可用时使用已批准的确定性备用程序或返回 blocker；
- 不得以 LLM 逐字段检查代替 FULL；
- Tool 返回 FAIL/ERROR 时保留结构化错误，不自动修改 schema、降低 gate 或忽略引用错误。

# Task closure 用户输出

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，必须在启动下一前台 task 前向用户输出精简 closure summary。

该摘要不是 confirmation gate，不要求用户确认，也不写入新的结构化记录。

宿主支持中间可见消息时，输出后可继续已授权范围；宿主不支持时，本轮以该摘要结束，并把下一 task 写入 `Expected next task`。

DONE 至少显示：

- task/substep；
- Operation/Validator 终态和 gate 结果；
- 关键动作或产物；
- warning；
- artifact validation status；
- report/result 路径；
- 预计下一 task。

BLOCKED 显示已完成部分、阻断原因、所需决定和未启动后续。

FAILED 显示失败位置、直接证据、保留产物、当前状态和可选后续。

不得把 Operation 完成写成科学质量验证通过。例如 `source_recognition` 完成只能说明来源识别、复制和 hash 检查通过；STRUCTURE artifact 仍为 `UNVALIDATED`。

# 用户决策

范围、Workflow、Operation 或 Validator 返回 decision request 后：创建 record → 更新 pending ID 与 hold reason → 向用户汇总 → 保存原始决定 → 追加终态事件 → 范围解析、重规划或再次请求 Workflow。

不维护与 `confirmation_items` 重复的布尔字段。

# Artifact set

仅在出现新 artifact candidate、validation status 改变、失效或 supersedes 关系变化时写 artifact record。

关键小文件记录 SHA-256；大型轨迹默认记录 path、size 和 mtime。未经 Validator 核验不得标为 `VALIDATED`。

# 外部 submission

状态：

```text
PREPARED → SUBMITTED → RUNNING → FINISHED_UNVERIFIED
                                      ↓
                              COMPLETED | FAILED
```

另有 `CANCELLED | UNKNOWN`。

提交前先写 PREPARED record 和确定性命令/session/job script，再产生副作用。不得因 tmux/job 消失直接判定成功。

# 状态与记录

所有对象必须符合 `03_contracts/README.md`。

状态更新采用：候选文件 → 适用 FAST/FULL 校验 → 备份/回滚准备 → 原子替换或受控事务 → 必要事件。不可变记录不得覆盖。

普通 task 的记录权威核心是：

```text
task.yaml
result.yaml
必要的 artifact/decision/submission record
一条终态 event
目标 Workstream state
```

`project_state.yaml` 仅在项目索引、Focus、Workstream 索引、项目级 decision、根目录或入口/恢复状态变化时更新。

Manager session 在进入项目时生成 ID，默认在本轮暂停或结束时一次性写入；只有 blocking decision、task failure、外部提交或进入恢复时允许中途 checkpoint。

Snapshot 仅用于初始化、根目录修改、恢复前后、重要 Workstream、重大 artifact 谱系变化、首个外部长任务和 Workstream 终结等关键节点。

# 恢复

项目级恢复暂停全部新写入，读取状态、备份、事件和记录，对业务对象安排 Validator，生成候选状态和差异，经用户确认后提交。恢复前后执行 FULL。

Workstream 级恢复可与其他不依赖该分支的 Workstream 并存；影响 Focus、共享依赖或目录所有权时升级为项目级恢复。

# 失败、暂停和完成

失败不自动重试、不降低 gate、不跳过 verifier。用户批准后使用新 task ID；替代方案创建 route revision。

暂停条件包括：范围未明确、blocking decision、缺少输入、恢复要求、初始化失败、Tool FAIL/ERROR、task 失败、高风险操作、用户终点、Workflow 未连接或外部任务运行且无其他安全步骤。

本轮结束前确保：必要状态与记录已落盘、无活动前台子 Agent、应输出的 task closure 已显示、Manager session 已完成，并按显示规则展示当前状态。

# 用户展示

严格使用 `references/manager_display_rules.md`。

完整 route 只在首次创建或实际变化时展示。

NEW 初始化完成但范围未解析时显示：

```text
Project state: RESUMABLE
Initialization: completed
Route scope: unresolved
Current position: none
Expected next task: none
Current decisions: <route-scope decision>
```

# 自检

- [ ] 入口状态有证据，Focus 唯一；
- [ ] NEW 已自动初始化，且没有隐式创建 route；
- [ ] 初始化后持久状态为 RESUMABLE；
- [ ] PROJECT_INITIALIZED 前未调用 Workflow 或创建 task；
- [ ] 模糊请求没有被补成默认终点；
- [ ] ROUTE_SCOPE_RESOLVED 前未创建 route；
- [ ] active route 不适用时未创建 task；
- [ ] route fragment 来自对应 Workflow；
- [ ] 未编造 Workflow 内部步骤；
- [ ] decision 偏离 route 时已先 revision 或暂停；
- [ ] 同时最多一个前台子 Agent；
- [ ] 子 Agent 未写管理目录；
- [ ] 普通 task 只对 changed paths 执行 FAST；
- [ ] 普通 task 未触发 FULL 或重复 schema meta-validation；
- [ ] 未用 LLM 模拟 FULL schema/reference 检查；
- [ ] Tool 版本、状态和权限符合 registry；
- [ ] 必要 artifact/decision/submission 已登记；
- [ ] task 终态事件和 Workstream state 已落盘；
- [ ] task closure summary 已在下一前台 task 前显示；
- [ ] Operation 完成未被表述为科学验证通过；
- [ ] 外部任务未从“消失”直接判为完成；
- [ ] 失败未自动重试；
- [ ] 固定用户显示字段完整。

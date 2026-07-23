---
name: md_workflow_manager
description: 管理真实 MD 项目的入口、初始化、Workstream、Focus、跨 Workflow 路线、串行临时子 Agent、项目状态、确定性校验、用户决策和外部任务。用于检查、规划、执行、续跑或恢复 MD 工作流；不执行具体结构、拓扑、模拟或分析业务操作。
---

# 目标

统一管理真实 MD 项目的入口状态、路线范围、Workstream、Focus、Workflow 接口、最多一个前台临时子 Agent、外部任务、产物谱系、用户决策和可恢复记录。

Manager 不承担 Operation 或 Validator 的业务工作。确定性 schema、引用、事务和渲染优先交给已注册 Tool，不由 LLM 逐字段模拟。

# 启动时读取

按需读取：

1. 项目根 `AGENTS.md`；
2. `03_contracts/README.md` 与本轮适用 schema；
3. `00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`；
4. `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
5. `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`；
6. `05_tools/tool_registry.yaml`；
7. `design_records/logging_and_record_system.md`；
8. `references/project_initialization_protocol.md`；
9. `references/stage_registry.yaml`；
10. 发生路线范围解析、PLAN、route 创建或 revision 时读取 `references/route_planning_protocol.md`；
11. 输出用户状态或 task closure 时读取 `references/manager_display_rules.md`；
12. 需要完整运行核查时读取 `references/manager_runtime_checklist.md`；
13. 项目索引、Focus Workstream state 及其 active route、decision、submission 和 artifact records；
14. 规划时逐个读取涉及范围内的 Workflow，执行时只读取当前 Workflow。

不得一次性载入全部项目历史、科学日志、轨迹或无关 Skill。

# 使用边界

用于：初始化、检查、规划、执行、续跑、恢复、创建参数/对照/重复/测试 Workstream，以及管理结构准备、拓扑准备、MD 准备、MD 模拟和分析流程。

不用作：一般 MD 问答、单个业务命令执行、业务文件修改、科学质量判定、Skill/Tool 编写窗口管理。

# 核心职责

Manager 负责：

- 解析可组合的 `INSPECT | PLAN | EXECUTE`；
- 判断 `NEW | RESUMABLE | NEEDS_RECOVERY`；
- 对 NEW 自动初始化；
- 在初始化后独立解析路线范围；
- 选择 `PROJECT | WORKSTREAM` Focus；
- 管理 Workstream 生命周期；
- 请求 Workflow 返回 route fragment 或当前 execution decision；
- 拼接 route，并在必要时创建 revision；
- 构建一个 task unit 并串行调用一个临时子 Agent；
- 核验 subagent result；
- 调用适用的已注册 Tool；
- 唯一提交 `00_project_state/**` 和 `00_project_records/**`；
- 以最小必要写入维护恢复能力；
- 在每个前台 task 闭环后向用户输出精简结果；
- 决定暂停、恢复、重试或重新规划。

Manager 不得：

- 合并入口判定、初始化、范围解析、规划和执行；
- 在初始化完成前调用 Workflow；
- 在路线范围未明确时选择默认终点；
- 在 active route 不存在或不适用时创建业务 task；
- 根据阶段名称编造 Workflow 内部步骤；
- 脱离 Workflow decision 选择 Operation/Validator；
- 同时创建多个前台子 Agent或嵌套委派；
- 在主上下文解析大型业务文件；
- 直接修改结构、拓扑、MDP、轨迹或分析结果；
- 因后台任务存在而自动切换 Focus；
- 覆盖已有下游结果；
- 自动重试失败 task、降低 gate 或跳过 Validator；
- 对普通 task 执行 FULL validation；
- 用 LLM 模拟 FULL schema 或项目级引用校验；
- 静默完成前台 task 后直接启动下一 task。

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

Manager 可创建管理目录和顶层阶段目录，但不创建业务结果。Operation/Validator 只能写 task 授权路径。

Tool 只能使用 registry 与自身 `tool.yaml` 声明的权限；cache 必须可删除、可重建且非权威。

# 项目进入

## 根目录与最小检查

分别确认或读取 Skill architecture root 与 MD project root。

- 首次且无可信状态时确认一次；
- 有效状态下自动读取并核验；
- 路径缺失、移动或冲突时进入恢复；
- 更新根目录不得隐式迁移业务文件；
- 每次用户状态摘要显示两个根目录。

最小检查仅读取清单和元数据，确认：状态可解析、schema 受支持、根目录有效、Workstream state 可定位、Focus 可解析、无冲突前台 task、无项目级阻断决定和明显目录所有权冲突。

## 入口状态

### NEW

仅当没有可读状态、目录为空或只有初始输入，且没有明显旧业务产物时使用。

`NEW` 只是本轮入口判定。根目录明确且无冲突时自动初始化，不等待用户额外提示。

初始化严格执行 `references/project_initialization_protocol.md`。初始化不创建 route、不调用 Workflow、不创建业务 task。

`PROJECT_INITIALIZED` 是 planning/execution barrier。

### RESUMABLE

项目索引可信且当前目标可安全解释。NEW 初始化完成后的持久 project state 也使用 `entry_state: RESUMABLE`。

### NEEDS_RECOVERY

状态损坏或不兼容、根目录不明、索引或引用冲突、目录所有权冲突、artifact 版本冲突、外部状态不可解释，或旧项目存在大量产物但无可信记录时使用。

项目级恢复完成前不创建新的写入型 task。

# 初始化后的请求与路线范围

- NEW 必须先完成 `PROJECT_INITIALIZED`；
- RESUMABLE 完成入口检查后进入本节；
- NEEDS_RECOVERY 恢复前不得规划或执行。

请求动作：

- `INSPECT`：读取并核验状态与记录；科学判断交给 Validator；
- `PLAN`：范围明确后创建或修订 route；
- `EXECUTE`：范围明确且 active route 有效时推进。

纯 INSPECT 不要求路线范围。

路线范围解析严格执行 `references/route_planning_protocol.md`：

- 终点必须来自用户明确指定、resolved decision、用户明确继续有效 active route，或用户明确按已记录 Workstream 目标继续；
- “开始处理”“跑一下流程”“测试一下项目”和无 active route 时的“继续”不构成明确终点；
- 终点不明确时创建 blocking decision，记录 `ROUTE_SCOPE_REQUESTED`，将 Workstream 置为 `WAITING / USER_DECISION` 并向用户确认；
- 不得默认选择下一 task、下一 gate、当前 Workflow 结束、Workstream 目标或项目终点；
- 范围落盘后记录 `ROUTE_SCOPE_RESOLVED`，再进入 PLAN。

# Focus 与 Workstream

一个 Manager 运行周期只有一个主要 Focus：

- `PROJECT`：全项目检查、恢复、多分支汇总或全局冲突；
- `WORKSTREAM`：具体分支规划、执行、恢复或决定处理。

Focus 选择优先级：用户指定 → 指定对象所属分支 → 本轮执行目标 → 未闭环前台 task → 最近 Focus → 仍不唯一则确认。

后台任务不自动改变 Focus。

Workstream 使用稳定 ID：

```text
ws_0001_<slug>
```

首个 Workstream 可在初始化时创建，但范围解析前 `active_route_id: null`。

当前步骤未闭合、无有效下游依赖、未开始 EM/NVT/NPT/MD、无需保留旧版本且修改不影响其他结果时，可以在原 Workstream 修正。

已有下游产物、模拟已开始、需要保留版本或比较方案，或上游修改可能使结果失效时，必须创建新 Workstream。新 Workstream 不自动触发 route。

# Workflow 规划接口

进入 PLAN 前必须满足：

- 项目已初始化或为可信 RESUMABLE；
- Focus Workstream 已确定；
- 范围已通过 `ROUTE_SCOPE_RESOLVED` 或有效 active route 明确；
- 不处于项目级恢复。

严格执行 `references/route_planning_protocol.md`：

1. 读取起点、终点和停止条件；
2. 按 stage registry 确定 Workflow 范围；
3. 串行请求已连接 Workflow 返回 fragment；
4. 核验相邻 artifact 接口；
5. 拼接并写 route record；
6. 未连接 Workflow 在边界形成 `PARTIAL | BLOCKED`。

路线是动态投影，不是硬执行队列。仅在实际变化时创建 revision。

# Workflow 执行接口

推进前确认：

- 项目已初始化或为可信 RESUMABLE；
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
- `COMPLETE`：核验 gate 和出口 artifact；达到终点则停止，否则进入下一已连接 Workflow。

Decision 与 active route 不一致时，先 revision；无法解释时暂停或恢复。

# 临时子 Agent 与 task 闭环

允许：

```text
OPERATION
VALIDATOR
OPERATION_WITH_VALIDATOR
```

组合模式仅用于 Operation 与专属 Validator 共享即时上下文，两部分职责和结果必须分离。

严格执行 `runtime_subagent_protocol.md`、`subagent_task.schema.yaml` 和 `subagent_result.schema.yaml`。

普通 task 使用 `design_records/logging_and_record_system.md` 定义的最小同步闭环：

```text
task.yaml
→ subagent execution
→ candidate result/related records/state
→ one FAST validation
→ commit
→ one terminal task event
→ Workstream state
→ visible task closure
```

普通 task 不机械写 `TASK_PREPARED`、`TASK_STARTED`、无变化 project state、session 增量、snapshot 或 route revision。

外部 submission、长耗时、高风险、不可逆或中断后必须区分是否已启动的 task，使用强化预记录闭环。

# 校验与 Tool

FAST/FULL、schema cache、权限和 Tool 失败规则由 `deterministic_tool_protocol.md` 定义。

Manager 只保留以下选择规则：

- 普通 task 对 changed paths 执行一次 FAST；
- 初始化、恢复和其他协议列明的关键生命周期节点使用 FULL；
- 优先调用 registry 中 `ACTIVE` 且版本兼容的 Tool；
- `IMPLEMENTED` 但未测试的 Tool 不作为默认生产路径；
- Tool FAIL/ERROR 时不提交候选终态、不降低 gate、不忽略错误；
- Tool 不可用时使用已批准的确定性备用程序或返回 blocker；
- 不得用 LLM 逐字段检查替代 FULL。

# 用户决定、artifact 与外部任务

decision request 由 Manager 统一持久化和展示。用户原始决定落盘后，再进行范围解析、重规划或重新请求 Workflow。

仅在 artifact candidate、新 validation status、失效或 supersedes 关系变化时写 artifact record。未经 Validator 证据不得标为 `VALIDATED`。

外部 submission 必须经过：

```text
PREPARED → SUBMITTED → RUNNING → FINISHED_UNVERIFIED
                                      ↓
                              COMPLETED | FAILED
```

另有 `CANCELLED | UNKNOWN`。tmux/job 消失不能直接判定成功。

# 状态、恢复与结束

状态和记录写入严格执行 `design_records/logging_and_record_system.md`。候选对象通过适用 FAST/FULL 后才能提交；不可变记录不得覆盖。

项目级恢复暂停新的写入型 task，读取状态、备份、事件和记录，生成候选状态与差异，并在恢复前后执行 FULL。

Workstream 级恢复可与不依赖该分支的其他 Workstream 并存；影响 Focus、共享依赖或目录所有权时升级为项目级恢复。

失败不自动重试、不降低 gate、不跳过 verifier。用户批准重试后使用新 task ID；替代方案需要 route revision。

暂停条件包括：范围未明确、blocking decision、缺少输入、恢复要求、初始化失败、Tool FAIL/ERROR、task 失败、高风险操作、用户终点、Workflow 未连接，或外部任务运行且无其他安全步骤。

本轮结束前确保：必要状态和记录已落盘、无活动前台子 Agent、task closure 已显示、Manager session 已完成。

# 用户展示

严格执行 `references/manager_display_rules.md`。

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，必须在下一前台 task 前输出 closure summary。该摘要不是 confirmation gate。

完整 route 只在首次创建或实际变化时展示。

# 自检

执行或审查时使用 `references/manager_runtime_checklist.md`。主文件只保留八个顶层 barrier：

- 初始化完成前不调用 Workflow；
- 路线范围明确前不创建 route；
- active route 不适用时不创建 task；
- task 必须来自当前 Workflow decision；
- 同时最多一个前台子 Agent；
- 子 Agent 不写管理目录；
- 候选对象通过适用校验后才提交；
- task closure 在下一前台 task 前显示。

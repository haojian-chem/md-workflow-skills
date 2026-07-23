# MD Workflow Skills

用于设计和维护基于 Skill 的分子动力学工作流。

## 当前运行架构

- 主智能体加载 Manager Skill，维护项目级状态并统一与用户交互；
- Workflow Skill 定义可复用阶段流程，不作为独立 Agent 运行；
- Workstream 表示真实项目中的一条具体工作分支，可以依次经过多个 Workflow；
- Manager 串行创建临时子 Agent，执行一个 Operation、一个 Validator，或 Operation 与其专属 Validator 组成的上下文连续 task unit；
- 任意时刻最多一个前台临时子 Agent，但允许多个 Workstream 和多个 tmux/调度任务并存；
- Operation 与 Validator 即使由同一子 Agent 连续执行，结果也必须分开；
- Manager 是项目状态和结构化记录的唯一提交者。

## Manager 入口与执行 barrier

入口判定、项目初始化、路线范围解析、路线规划和执行相互独立：

```text
ENTRY_STATE_EVALUATED
→ PROJECT_INITIALIZED（仅 NEW）
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

- `NEW` 只表示入口状态，不包含路线规划或任务执行；
- NEW 项目在根目录明确且无冲突时自动初始化，不要求用户额外提示；
- 初始化创建项目状态和首个 Workstream，但不创建首条 route；
- 路线终点模糊时必须向用户确认，不得自行选择默认终点；
- `PROJECT_INITIALIZED` 前不调用 Workflow；
- `ROUTE_SCOPE_RESOLVED` 前不请求 route fragment；
- 有效 active route 不存在时不创建业务 task。

## Workflow 的两种接口

规划与执行分离：

```text
规划：Manager → 各 Workflow route fragment → Manager 拼接 Workstream route
执行：Manager → 当前 Workflow decision → 一个 task unit
```

- 规划接口：`03_contracts/workflow_route_fragment.schema.yaml`；
- 执行接口：`03_contracts/workflow_decision.schema.yaml`；
- Manager 负责起点、终点、跨 Workflow 拼接和 route revision；
- Workflow 只生成自身阶段 fragment，不跨阶段编造完整路线；
- 预计路线是动态投影，不是硬编码执行队列；
- execution decision 因新证据偏离 active route 时，先修订路线再执行；
- 未连接 Workflow 在边界形成 PARTIAL/BLOCKED，不虚构其内部步骤。

详细规则：

`00_manager/md_workflow_manager/references/route_planning_protocol.md`

## 当前 Workflow 划分

1. `structure_preparation`
2. `topology_preparation`
3. `md_preparation`
4. `md_simulation`
5. `analysis`

职责边界：

- `structure_preparation`：初始结构识别、对象选择、缺失处理、质子化、重排与结构验证；
- `topology_preparation`：标准残基、相连非标准残基和独立非标准组分的拓扑生成与参数准备；
- `md_preparation`：力场与拓扑整合、建盒、加水、加离子，并生成完整可用于模拟的体系；
- `md_simulation`：准备对应阶段的 MDP 与运行输入，执行 EM、NVT、NPT、生产 MD、续跑及完成状态核验；
- `analysis`：模拟结果分析。

目前只有 `structure_preparation_workflow` 正式连接；后续 Workflow 尚未建立时，路线只规划到对应阶段边界。

## Workstream 项目模型

项目不保存唯一的“当前 Workflow”。同一项目可同时存在多个 Workstream，例如：

- 参数 v1 的生产 MD 正在后台运行；
- 参数 v2 返回 `topology_preparation` 重新生成参数并执行测试 MD；
- 对照体系等待人工决策。

每个 Workstream 独立保存目标、当前位置、预计路线、产物谱系、人工决策和外部运行任务。当前一轮 Manager 交互通过 `focus` 指定主要处理对象，其他 Workstream 可以作为关联上下文或继续后台运行。

## 真实 MD 项目顶层目录

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

状态目录：

```text
00_project_state/
├── project_state.yaml
├── project_state.yaml.bak
└── workstreams/
    └── <workstream_id>.yaml
```

记录目录：

```text
00_project_records/
├── manager/
│   └── sessions/
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

- `00_project_state/` 只保存当前有效且可恢复的项目索引与 Workstream 状态；
- `00_project_records/` 保存 Manager 会话、项目事件、路线、任务、人工决策、外部提交、产物谱系和状态快照；
- GROMACS 日志、详细 Validator 报告、结构、拓扑、轨迹和分析数据留在对应业务目录；
- `04_md_simulation/` 的内部目录不在项目级预先排序或固定。

## Source recognition 文件归位

`source_recognition` 当前规则：

- 默认将选定源结构复制到 `01_structure_preparation/01_source_recognition/`；
- 不移动、不删除或修改原始文件；
- 复制前后核验 SHA-256；
- 相同目标复用；
- 不同内容目标不覆盖；
- 只有用户明确授权且 source path 具有写权限时才允许受控移动；
- 受保护 `01_sources/` 不得移动。

## Shared contracts

运行时共享接口统一位于 `03_contracts/`，入口索引为 `03_contracts/README.md`。

当前 15 份 contracts 已覆盖 Workflow route fragment/decision、Workstream、Focus、task unit、project/workstream state、事件、路线、人工决策、submission、artifact set、snapshot 和 Manager session front matter。

`project_event.schema.yaml` 已包含：

```text
ROUTE_SCOPE_REQUESTED
ROUTE_SCOPE_RESOLVED
```

## 当前实现状态

- Manager、项目状态、Workstream 和日志体系设计已经冻结；
- Manager 入口初始化、路线范围解析和执行 barrier 已对齐；
- route planning protocol 与 15 份共享 contracts 已对齐；
- `md_workflow_manager` draft 已建立，仍需可执行 fixtures 与端到端集成；
- `structure_preparation_workflow` 已支持 route fragment 与 execution decision，仍需 Manager 集成；
- `source_recognition` 安全复制 draft 已建立，仍需真实文件测试；
- `component_and_residue_classification_validator` 仍需迁移到 subagent task/result v2；
- 其余 Phase 1 Operations/Validators 尚待编写；
- content map 的 `load_when` 与 `applicable_to` 扩展仍未冻结。

详细设计与验证见：

- `design_records/manager_and_project_structure_decisions.md`
- `design_records/logging_and_record_system.md`
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`
- `00_authoring/CONTRACT_ALIGNMENT_VALIDATION.md`
- `00_authoring/ROUTE_PLANNING_ALIGNMENT_VALIDATION.md`
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`
- `04_evals/structure_preparation_workflow/WORKFLOW_DRAFT_VALIDATION.md`
- `00_authoring/SYNC_STATUS.md`

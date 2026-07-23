# MD Workflow Skills

用于设计和维护基于 Skill 的分子动力学工作流及其确定性共享工具。

## 当前运行架构

- 主智能体加载 Manager Skill，维护项目级状态并统一与用户交互；
- Workflow Skill 定义可复用阶段流程，不作为独立 Agent 运行；
- Workstream 表示真实项目中的一条具体工作分支，可以依次经过多个 Workflow；
- Manager 串行创建临时子 Agent，执行一个 Operation、一个 Validator，或 Operation 与其专属 Validator 组成的 task unit；
- 任意时刻最多一个前台临时子 Agent，但允许多个 Workstream 和多个 tmux/调度任务并存；
- Operation 与 Validator 即使由同一子 Agent 连续执行，结果也必须分开；
- Manager 是项目状态和结构化记录的唯一提交者；
- Tool 是确定性程序，不是 Agent，也不是第五个决策层。

## Manager 入口与执行 barrier

```text
ENTRY_STATE_EVALUATED
→ FULL 初始化候选状态校验
→ PROJECT_INITIALIZED（仅 NEW）
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

- `NEW` 只表示入口状态，不包含路线规划或任务执行；
- NEW 项目在根目录明确且无冲突时自动初始化；
- 初始化创建项目状态和首个 Workstream，但不创建首条 route；
- 路线终点模糊时必须向用户确认，不得选择默认终点；
- `PROJECT_INITIALIZED` 前不调用 Workflow；
- `ROUTE_SCOPE_RESOLVED` 前不请求 route fragment；
- 有效 active route 不存在时不创建业务 task。

## Workflow 的两种接口

```text
规划：Manager → 各 Workflow route fragment → Manager 拼接 Workstream route
执行：Manager → 当前 Workflow decision → 一个 task unit
```

- 规划接口：`03_contracts/workflow_route_fragment.schema.yaml`；
- 执行接口：`03_contracts/workflow_decision.schema.yaml`；
- Manager 负责起点、终点、跨 Workflow 拼接和 route revision；
- Workflow 只生成自身阶段 fragment；
- 预计路线是动态投影，不是硬编码执行队列；
- 未连接 Workflow 在边界形成 PARTIAL/BLOCKED。

详细规则：

`00_manager/md_workflow_manager/references/route_planning_protocol.md`

## FAST/FULL runtime validation

普通 task 不再重复执行全量 contract validation。

### FAST

用于普通前台 task：

```text
changed runtime instances
→ 一次批量 schema validation
→ 直接引用检查
→ structured PASS/FAIL
```

FAST 不扫描完整项目历史。

### FULL

只用于：

- 项目初始化；
- schema/contract 变化；
- 恢复前后；
- root 变化；
- 重要 Workstream 或 artifact 谱系变化；
- 首个外部长任务提交前；
- Workstream 终结；
- 用户明确完整审计。

schema bundle hash 未变化且 cache 有效时，不重复 schema meta-validation。不得用 LLM 逐字段模拟 FULL schema 或全项目引用校验。

模型推理强度分层未纳入本规则。

## 确定性 Tool 体系

```text
00_authoring/md-workflow-tool-authoring/SKILL.md
00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md
05_tools/tool_registry.yaml
05_tools/<tool-name>/tool.yaml
```

共享 Tool 由 Tool Authoring Skill 生成、测试、注册、升级、维护和废弃。业务 Skill 可以提交 `tool_request`，但不得在运行中的业务 task 内修改共享 Tool。

当前状态：

- `runtime_schema_validator` 0.1.0：IMPLEMENTED，支持 FAST、FULL、schema hash cache 和直接引用检查；待 tests/benchmark 后决定是否 ACTIVE；
- `state_transaction`：DESIGNED；
- `incremental_reference_checker`：DESIGNED；
- `task_closure_renderer`：DESIGNED。

## 普通 task 最小闭环

```text
task.yaml
→ subagent execution
→ candidate result/related records/state
→ FAST validation
→ result.yaml
→ 必要 artifact/decision/submission
→ 一条终态 event
→ Workstream state
→ visible task closure summary
```

普通 task 默认不机械写 `TASK_PREPARED`、`TASK_STARTED`、无变化 project state、session 增量、snapshot 或 route revision。

## 当前 Workflow 划分

1. `structure_preparation`
2. `topology_preparation`
3. `md_preparation`
4. `md_simulation`
5. `analysis`

职责边界：

- `structure_preparation`：初始结构识别、对象选择、缺失处理、质子化、重排与结构验证；
- `topology_preparation`：标准残基、相连非标准残基和独立非标准组分的拓扑生成与参数准备；
- `md_preparation`：力场与拓扑整合、建盒、加水、加离子，并生成完整体系；
- `md_simulation`：准备 MDP 与运行输入，执行 EM、NVT、NPT、生产 MD、续跑及完成核验；
- `analysis`：模拟结果分析。

目前只有 `structure_preparation_workflow` 正式连接；后续 Workflow 尚未建立时，路线只规划到对应阶段边界。

## Workstream 项目模型

项目不保存唯一的“当前 Workflow”。每个 Workstream 独立保存目标、当前位置、预计路线、产物谱系、人工决策和外部运行任务。其他 Workstream 可作为关联上下文或继续后台运行。

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

- `00_project_state/` 保存当前有效且可恢复的项目索引与 Workstream 状态；
- `00_project_records/` 保存 Manager 会话、事件、路线、任务、决策、外部提交、产物谱系和快照；
- GROMACS 日志、Validator 报告、结构、拓扑、轨迹和分析数据留在业务目录；
- Tool cache 位于可删除和重建的非权威 cache 路径。

## Source recognition 文件归位

- 默认复制到 `01_structure_preparation/01_source_recognition/`；
- 不移动、删除或修改原始文件；
- 复制前后核验 SHA-256；
- 相同目标复用；
- 不同内容目标不覆盖；
- 只有用户明确授权且 source path 可写时才允许受控移动；
- 受保护 `01_sources/` 不得移动。

## Shared contracts

运行时共享接口统一位于 `03_contracts/`，入口索引为 `03_contracts/README.md`。

## 当前实现状态

- Manager 已接入入口 barrier、最小记录、task closure 和 FAST/FULL Tool 选择；待可执行集成验证；
- Tool Authoring Skill 与 registry 已建立；
- `runtime_schema_validator` 已实现但尚未 ACTIVE；
- `structure_preparation_workflow` 已支持 route fragment 与 execution decision，仍需 Manager 集成；
- `source_recognition` 功能测试已通过一次，需复测 FAST validation 与 closure summary；
- `component_and_residue_classification_validator` 仍需迁移到 subagent task/result v2；
- 其余 Phase 1 Operations/Validators 尚待编写。

详细设计与验证见：

- `AGENTS.md`
- `design_records/logging_and_record_system.md`
- `00_manager/md_workflow_manager/SKILL.md`
- `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`
- `00_authoring/md-workflow-tool-authoring/SKILL.md`
- `05_tools/tool_registry.yaml`
- `04_evals/runtime_schema_validator/`
- `00_authoring/SYNC_STATUS.md`

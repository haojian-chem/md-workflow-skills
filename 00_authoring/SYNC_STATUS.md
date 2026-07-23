# Authoring 文件同步状态

更新日期：2026-07-23

## 当前基线

仓库已经同步并对齐：

- 17 份现有 Skill content map；
- content map v3 schema；
- Skill inventory 与文件所有权表；
- 多窗口 work order 与 authoring Skill；
- Workstream 项目模型；
- 日志和记录体系；
- 15 份共享运行 contract；
- Workflow planning/execution 双接口；
- 跨 Workflow route planning protocol；
- Manager 入口初始化与路线范围 barrier；
- 串行 task-unit 临时子 Agent 协议；
- `md_workflow_manager` draft；
- `structure_preparation_workflow` 双接口 draft；
- `source_recognition` 安全复制 draft。

验证结果：

- `00_authoring/CONTRACT_ALIGNMENT_VALIDATION.md`；
- `00_authoring/ROUTE_PLANNING_ALIGNMENT_VALIDATION.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- `04_evals/structure_preparation_workflow/WORKFLOW_DRAFT_VALIDATION.md`。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的 Skill 尚未冻结；
- 多窗口编写前必须读取 `AGENTS.md`、本文件、`skill_inventory.yaml`、`file_ownership.yaml`、目标 content map、目标 work order 和 `03_contracts/README.md`；
- 涉及 Workflow 或路线时必须读取 `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- `AGENTS.md`、`03_contracts/`、authoring references、content maps、inventory 和 ownership 表仅由主窗口修改；
- 业务窗口不得本地重定义共享状态、路线和记录字段。

## 已确认的 Manager 入口顺序

```text
ENTRY_STATE_EVALUATED
→ PROJECT_INITIALIZED（仅 NEW）
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

硬规则：

- `NEW` 只表示入口判定；
- NEW 项目在根目录明确且无冲突时自动初始化；
- 初始化创建首个 Workstream，但不创建 route；
- `PROJECT_INITIALIZED` 前不得调用 Workflow；
- 路线范围解析是初始化后的独立事件；
- 用户未明确终点时必须请求决定，不得选取默认终点；
- `ROUTE_SCOPE_RESOLVED` 前不得请求 fragment 或创建 route；
- 有效 active route 不存在时不得创建业务 task。

项目事件已加入：

```text
ROUTE_SCOPE_REQUESTED
ROUTE_SCOPE_RESOLVED
```

## 已确认的运行模型

- Workflow 是可复用阶段流程；
- Workstream 是真实项目中的具体工作分支；
- 一个 Workstream 可以经过多个 Workflow；
- 一个项目可以同时存在多个 Workstream；
- Workflow 规划时返回本阶段 route fragment；
- Workflow 执行时返回一个当前 decision；
- Manager 负责跨 Workflow 起终点、fragment 拼接和 route revision；
- Manager 不得自行编造 Workflow 内部步骤；
- 任意时刻最多一个前台临时子 Agent；
- 多个 tmux 或调度系统外部任务可以并存；
- task unit 支持 `OPERATION | VALIDATOR | OPERATION_WITH_VALIDATOR`；
- Operation 与配套 Validator 即使同一子 Agent 连续执行，结果也必须分开；
- Manager 是 `00_project_state/` 和 `00_project_records/` 的唯一提交者。

## 已对齐的共享 contracts

权威索引：`03_contracts/README.md`

包括：

- 公共类型和 decision request；
- Workflow route fragment；
- Workflow execution decision；
- subagent task/result；
- project/workstream state；
- project event；
- Manager session；
- route、decision、submission、artifact set 和 snapshot。

外部任务必须经过：

```text
RUNNING
→ FINISHED_UNVERIFIED
→ Validator 核验
→ COMPLETED 或 FAILED
```

## 当前实现状态

- `md_workflow_manager`：已明确 NEW 自动初始化、独立 route scope resolution、规划循环与执行循环；20 个行为 cases 已建立，待可执行验证；
- `structure_preparation_workflow`：已支持 route fragment 与 execution decision；待 Manager 集成；
- `source_recognition`：默认复制、SHA-256 校验、相同副本复用、不同内容不覆盖；待真实结构文件测试；
- `component_and_residue_classification_validator`：需要迁移到 subagent task/result v2；
- 其他 Phase 1 Skills：尚待编写。

## Source recognition 已确认规则

- 默认复制，不移动源结构；
- 不修改、删除或覆盖原文件；
- 复制前后校验 SHA-256；
- 目标同 hash 时复用；
- 目标不同 hash 时阻塞并请求决定；
- 只有 resolved user decision 与 source write permission 同时存在时才允许移动；
- 受保护 `01_sources/` 不得移动。

## 尚未冻结

- content map 的 `load_when` 与 `applicable_to` 扩展。

## 当前权威文件

- 根目录 `README.md`；
- `design_records/manager_and_project_structure_decisions.md`；
- `design_records/logging_and_record_system.md`；
- `00_manager/md_workflow_manager/SKILL.md`；
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- `03_contracts/README.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- 本文件。

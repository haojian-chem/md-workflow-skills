# Authoring 文件同步状态

更新日期：2026-07-23

## 当前基线

仓库已经同步并对齐：

- 17 份现有 Skill content map；
- content map v3 schema；
- Skill inventory 与文件所有权表；
- Workstream 项目模型；
- 日志和记录体系；
- 15 份共享运行 contract；
- Workflow planning/execution 双接口；
- 跨 Workflow route planning protocol；
- Manager 入口初始化与路线范围 barrier；
- `route_record.schema.yaml` v3；
- 普通 task 最小同步记录策略；
- 前台 task closure 用户可见输出；
- 串行 task-unit 临时子 Agent 协议；
- `md_workflow_manager` draft；
- `structure_preparation_workflow` 双接口 draft；
- `source_recognition` 安全复制 draft。

验证与状态记录：

- `00_authoring/CONTRACT_ALIGNMENT_VALIDATION.md`；
- `00_authoring/ROUTE_PLANNING_ALIGNMENT_VALIDATION.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- `04_evals/structure_preparation_workflow/WORKFLOW_DRAFT_VALIDATION.md`。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的 Skill 尚未冻结；
- 多窗口编写前必须读取 `AGENTS.md`、本文件、inventory、ownership、目标 content map、work order 和 `03_contracts/README.md`；
- 涉及 Workflow 或路线时必须读取 route planning protocol；
- 涉及状态、事件、task、session、snapshot 或 artifact 记录时必须读取 `design_records/logging_and_record_system.md`；
- 业务窗口不得本地重定义共享状态、路线和记录字段。

## Manager 入口顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ 候选 project/workstream state 生成与校验
→ 原子提交状态
→ 持久 project state: RESUMABLE
→ PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

硬规则：

- `NEW` 只是本轮入口判定；
- NEW 项目在根目录明确且无冲突时自动初始化；
- 初始化创建首个 Workstream，但不创建 route；
- `PROJECT_INITIALIZED` 前不得调用 Workflow；
- 路线范围解析是初始化后的独立事件；
- 用户未明确终点时必须请求决定，不得选默认终点；
- `ROUTE_SCOPE_RESOLVED` 前不得创建 route；
- 有效 active route 不存在时不得创建业务 task。

## 普通 task 最小同步记录

普通、短耗时、无外部 submission、无高风险副作用的前台 task 使用：

```text
task.yaml
→ subagent execution
→ result.yaml
→ 必要 artifact/decision/submission record
→ 一条终态 task event
→ Workstream state
→ visible task closure summary
```

普通 task 默认不机械写入：

- `TASK_PREPARED`；
- `TASK_STARTED`；
- 执行前 Workstream EXECUTING 更新；
- 无变化的 project state；
- Manager session 逐 task 增量；
- snapshot；
- 无变化 route revision；
- 空 artifact/decision/submission record。

外部 submission、长耗时、高风险或不可逆 task 仍保留强化预记录。

## Task closure 可见性

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，必须在下一前台 task 启动前显示精简 closure summary。

`source_recognition` 完成只能说明来源识别、复制/复用和 SHA-256 检查通过；STRUCTURE artifact 仍为 `UNVALIDATED`，不得显示“结构验证通过”。

宿主支持中间可见消息时可在显示后继续既定范围；不支持时，本轮以 closure summary 结束并保留 expected next task。

## 已确认的运行模型

- Workflow 是可复用阶段流程；
- Workstream 是具体项目分支；
- 一个 Workstream 可以经过多个 Workflow；
- 一个项目可以存在多个 Workstream；
- Workflow 规划返回 route fragment，执行返回一个当前 decision；
- Manager 负责跨 Workflow 范围、拼接与 revision；
- 任意时刻最多一个前台临时子 Agent；
- 多个外部任务可以并存；
- task unit 支持 `OPERATION | VALIDATOR | OPERATION_WITH_VALIDATOR`；
- Operation 与 Validator 结果必须分开；
- Manager 是管理状态和记录的唯一提交者。

## 当前实现状态

- `md_workflow_manager`：443 行；20 个 behavior cases、4 个 initialization cases、12 个 route planning cases、7 个 task recording/display cases；待可执行验证；
- `structure_preparation_workflow`：已支持双接口，待 Manager 集成；
- `source_recognition`：1.1 功能检查已由用户测试通过；需复测 closure summary 展示与最小记录行为；
- `component_and_residue_classification_validator`：需要迁移到 subagent task/result v2；
- 其他 Phase 1 Skills：尚待编写。

本轮尚未在测试主机重新运行全量 validator。Manager 和 contracts 仍为 draft，不得宣称运行验收通过。

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

- `design_records/logging_and_record_system.md`；
- `00_manager/md_workflow_manager/SKILL.md`；
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- `00_manager/md_workflow_manager/references/manager_display_rules.md`；
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
- `03_contracts/README.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- 本文件。
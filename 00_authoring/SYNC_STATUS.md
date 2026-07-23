# Authoring 文件同步状态

更新日期：2026-07-23

## 当前基线

仓库已经同步并对齐：

- content map v3、Skill inventory 与文件所有权；
- Workstream 项目模型与 15 份共享运行 contract；
- Workflow planning/execution 双接口；
- Manager 入口初始化、路线范围和 execution barrier；
- 跨 Workflow route planning 与 `route_record.schema.yaml` v3；
- 普通 task 最小同步记录和 task closure 用户展示；
- FAST/FULL runtime validation 与 schema hash cache；
- Tool protocol、registry、Tool Authoring Skill；
- `runtime_schema_validator` 0.1.0 初始实现；
- 串行 task-unit 临时子 Agent 协议；
- `structure_preparation_workflow` 与 `source_recognition` drafts。

Manager 已完成渐进披露重构：

```text
00_manager/md_workflow_manager/SKILL.md: 495 → 311 lines
```

新增：

```text
references/project_initialization_protocol.md
references/manager_runtime_checklist.md
```

该重构只迁移和去重，不改变已确认运行语义。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的对象尚未冻结；
- 多窗口编写前读取 `AGENTS.md`、本文件、inventory、ownership、目标 content map、work order 和适用 contracts；
- 涉及 Workflow/route 时读取 route planning protocol；
- 涉及 Tool 时读取 deterministic tool protocol、Tool Authoring Skill 和 registry；
- 涉及状态和记录时读取 `design_records/logging_and_record_system.md`；
- 涉及初始化时读取 `project_initialization_protocol.md`；
- 业务窗口不得本地重定义共享 contract、状态、路线、记录或 Tool contract；
- 未测试 Tool 不得标记为 ACTIVE 或作为默认生产路径。

## Manager 入口顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ candidate state
→ FULL validation
→ controlled commit
→ persistent RESUMABLE
→ PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

硬规则：

- NEW 只是本轮入口判定；
- 根目录明确且无冲突时自动初始化；
- 初始化创建首个 Workstream，但不创建 route；
- `PROJECT_INITIALIZED` 前不调用 Workflow；
- 路线范围解析是初始化后的独立事件；
- 用户未明确终点时必须确认，不得选择默认终点；
- `ROUTE_SCOPE_RESOLVED` 前不创建 route；
- active route 不存在或不适用时不创建业务 task。

## FAST/FULL runtime validation

FAST：

```text
changed runtime instances
→ one batch schema validation
→ direct reference checks
→ structured PASS/FAIL
```

FULL 仅用于初始化、contract/root 变化、恢复前后、重要 Workstream、重大 artifact 谱系变化、首个外部长任务提交前、Workstream 终结或用户明确完整审计。

禁止：

- 普通 task 机械执行 FULL；
- schema hash/cache 命中时重复 meta-validation；
- 用 LLM 逐字段模拟 FULL；
- 将模型推理强度分层写入本 contract。

## 普通 task 最小闭环

```text
task.yaml
→ subagent execution
→ candidate result/records/state
→ FAST validation
→ commit
→ one terminal task event
→ Workstream state
→ visible task closure
```

普通 task 不机械写 `TASK_PREPARED`、`TASK_STARTED`、无变化 project state、session 增量、snapshot、route revision 或空记录。

外部 submission、长耗时、高风险或不可逆 task 保留强化预记录。

## 确定性 Tool 体系

Tool 不是 Agent，也不是第五个决策层。

当前 registry：

- `runtime_schema_validator`：IMPLEMENTED，待 executable tests/benchmark；
- `state_transaction`：DESIGNED；
- `incremental_reference_checker`：DESIGNED；
- `task_closure_renderer`：DESIGNED。

业务 Skill 可以提交 `tool_request`，但不得在运行中的业务 task 内修改共享 Tool。

## 当前实现状态

- `md_workflow_manager`：主文件 311 行；初始化与自检已渐进披露；待 validator 和端到端验证；
- `md-workflow-tool-authoring`：draft；
- `runtime_schema_validator`：已实现 FAST/FULL、cache、直接引用和 candidate overlay；尚未 ACTIVE；
- `structure_preparation_workflow`：双接口 draft，待 Manager 集成；
- `source_recognition`：1.1 功能检查已由用户测试通过；需复测 closure、FAST 和最小记录；
- `component_and_residue_classification_validator`：待迁移到 subagent task/result v2；
- 其他 Phase 1 Skills：待编写。

本轮尚未在测试主机运行新增 Tool tests、全量 validator 和重构后的端到端测试，不得宣称运行验收通过。

## 尚未冻结

- content map 的 `load_when` 与 `applicable_to` 扩展；
- `runtime_schema_validator` ACTIVE 状态；
- `state_transaction`、`incremental_reference_checker`、`task_closure_renderer` 实现。

## 当前权威文件

- `AGENTS.md`；
- `design_records/logging_and_record_system.md`；
- `00_manager/md_workflow_manager/SKILL.md`；
- `00_manager/md_workflow_manager/references/project_initialization_protocol.md`；
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- `00_manager/md_workflow_manager/references/manager_display_rules.md`；
- `00_manager/md_workflow_manager/references/manager_runtime_checklist.md`；
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
- `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`；
- `00_authoring/md-workflow-tool-authoring/SKILL.md`；
- `05_tools/tool_registry.yaml`；
- `03_contracts/README.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- 本文件。

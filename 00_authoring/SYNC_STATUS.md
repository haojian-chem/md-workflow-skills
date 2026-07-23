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
- `runtime_schema_validator` 0.1.0：ACTIVE；
- NEW 初始化 capability 预检与内建确定性状态提交路径；
- current blocker / pending after current barrier 因果分层；
- 串行 task-unit 临时子 Agent 协议；
- `structure_preparation_workflow` 与 `source_recognition` drafts。

Manager 主文件保持 311 行；初始化事务和完整自检位于 references。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的对象尚未冻结；
- 多窗口编写前读取 `AGENTS.md`、本文件、inventory、ownership、目标 content map、work order 和适用 contracts；
- 涉及 Workflow/route 时读取 route planning protocol；
- 涉及 Tool 时读取 deterministic tool protocol、Tool Authoring Skill 和 registry；
- 涉及状态和记录时读取 `design_records/logging_and_record_system.md`；
- 涉及初始化时读取 `project_initialization_protocol.md`；
- 未测试 Tool 不得标记为 ACTIVE 或作为默认生产路径；
- hard gate 在发布前必须有 ACTIVE Tool 或权威内建确定性路径；
- 后续路线和 Workflow 问题不得冒充当前 barrier 的 blocker。

## Manager 入口顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ capability preflight
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
- `FULL_RUNTIME_VALIDATION` 由 ACTIVE `runtime_schema_validator` 提供；
- `CONTROLLED_STATE_COMMIT` 可使用初始化协议规定的内建确定性路径；
- `state_transaction` 为 DESIGNED 不得阻塞 NEW；
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

## Tool 状态

```text
runtime_schema_validator 0.1.0 — ACTIVE
state_transaction 0.1.0 — DESIGNED, optional optimization
incremental_reference_checker 0.1.0 — DESIGNED
task_closure_renderer 0.1.0 — DESIGNED
```

`runtime_schema_validator` 激活证据：

```text
04_evals/runtime_schema_validator/VALIDATION.md
5 executable tests passed
FAST cold median: 5.977 ms
FAST warm median: 3.311 ms
FULL warm median: 4.181 ms
```

## 阻断因果分层

发生停止时使用：

```text
Current blocker:
<当前 barrier 的直接原因或 none>

Pending after current barrier:
<通过当前 barrier 后才处理的问题或 none>
```

初始化阶段：

- FULL capability 缺失才是 capability blocker；
- “开始 MD”的路线终点歧义在 `PROJECT_INITIALIZED` 后处理；
- 未连接 Workflow 在 route planning 到达边界后处理；
- 后两项不得列为初始化失败原因。

## 当前实现状态

- `md_workflow_manager`：主文件 311 行；启动自锁已修正；待真实项目端到端验证；
- `runtime_schema_validator`：ACTIVE，可作为 FAST/FULL 默认确定性实现；
- `state_transaction`：DESIGNED；初始化已有内建提交路径，不构成 blocker；
- `structure_preparation_workflow`：双接口 draft，待 Manager 集成；
- `source_recognition`：1.1 功能检查已由用户测试通过；需复测 closure、FAST 和最小记录；
- `component_and_residue_classification_validator`：待迁移到 subagent task/result v2；
- 其他 Phase 1 Skills：待编写。

Manager 和完整工作流仍为 draft；Tool 激活不等同于 Manager 端到端验收通过。

## 尚未冻结

- content map 的 `load_when` 与 `applicable_to` 扩展；
- `state_transaction`、`incremental_reference_checker`、`task_closure_renderer` 实现；
- Manager 真实项目端到端集成。

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
- `04_evals/runtime_schema_validator/VALIDATION.md`；
- `03_contracts/README.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- 本文件。
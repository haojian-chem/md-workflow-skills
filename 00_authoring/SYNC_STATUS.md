# Authoring 文件同步状态

更新日期：2026-07-23

## 当前基线

仓库已经同步并对齐：

- content map v3 schema 与现有 Skill content maps；
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
- FAST/FULL 两级 runtime validation 规则；
- schema bundle hash cache 规则；
- 确定性 Tool 协议、registry 与 Tool Authoring Skill；
- `runtime_schema_validator` 0.1.0 初始实现；
- 串行 task-unit 临时子 Agent 协议；
- `md_workflow_manager` draft；
- `structure_preparation_workflow` 双接口 draft；
- `source_recognition` 安全复制 draft。

验证与状态记录：

- `00_authoring/CONTRACT_ALIGNMENT_VALIDATION.md`；
- `00_authoring/ROUTE_PLANNING_ALIGNMENT_VALIDATION.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- `04_evals/structure_preparation_workflow/WORKFLOW_DRAFT_VALIDATION.md`；
- `04_evals/runtime_schema_validator/`。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的 Skill 尚未冻结；
- 多窗口编写前必须读取 `AGENTS.md`、本文件、inventory、ownership、目标 content map、work order 和适用 contracts；
- 涉及 Workflow 或路线时读取 route planning protocol；
- 涉及 Tool 时读取 `deterministic_tool_protocol.md`、Tool Authoring Skill 和 `05_tools/tool_registry.yaml`；
- 涉及状态、事件、task、session、snapshot 或 artifact 记录时读取 `design_records/logging_and_record_system.md`；
- 业务窗口不得本地重定义共享状态、路线、记录或 Tool contract；
- 未测试 Tool 不得标记为 ACTIVE 或作为默认生产路径。

## Manager 入口顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ 候选 project/workstream state 生成
→ FULL schema/reference validation
→ 受控状态提交
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

## FAST/FULL runtime validation

### FAST

普通 task 默认：

```text
changed runtime instances
→ 一次批量 schema validation
→ 直接引用检查
→ structured PASS/FAIL
```

FAST 不扫描全部 Workstream、route、artifact、decision、submission 或 event 历史。

### FULL

仅用于：

- 项目初始化；
- schema/contract 变化；
- 恢复前后；
- root 变化；
- 重要 Workstream；
- 重大 artifact 谱系变化；
- 首个外部长任务提交前；
- Workstream 终结；
- 用户明确完整审计。

规则：

- 普通 task 禁止机械执行 FULL；
- schema bundle hash 未变化且 cache 有效时，不重复 schema meta-validation；
- 不得用 LLM 逐字段模拟 FULL schema 或全项目引用校验；
- 模型推理强度分层未采纳，不属于本轮规则。

## 普通 task 最小同步记录

普通、短耗时、无外部 submission、无高风险副作用的前台 task 使用：

```text
task.yaml
→ subagent execution
→ candidate result/related records/state
→ FAST validation
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

## 确定性 Tool 体系

```text
05_tools/tool_registry.yaml
05_tools/<tool-name>/tool.yaml
00_authoring/md-workflow-tool-authoring/SKILL.md
```

Tool 不是 Agent，也不是第五个决策层。

当前 registry：

- `runtime_schema_validator`：IMPLEMENTED，待 executable tests 与 benchmark 后决定是否 ACTIVE；
- `state_transaction`：DESIGNED；
- `incremental_reference_checker`：DESIGNED；
- `task_closure_renderer`：DESIGNED。

业务 Skill 可以提交 `tool_request`，但不得在运行中的业务 task 内修改共享 Tool。

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
- Manager 是管理状态和记录的唯一提交者；
- Tool 只执行确定性逻辑，不承担路线或科学判断。

## 当前实现状态

- `md_workflow_manager`：已接入 FAST/FULL 选择和 Tool registry；待可执行集成验证；
- `md-workflow-tool-authoring`：draft；待完成首个 Tool 的完整生命周期验证；
- `runtime_schema_validator`：已实现 FAST、FULL、schema hash cache 与直接引用检查；尚未在测试主机运行 tests/benchmark，因此不是 ACTIVE；
- `structure_preparation_workflow`：已支持双接口，待 Manager 集成；
- `source_recognition`：1.1 功能检查已由用户测试通过；需复测 closure summary、FAST validation 与最小记录行为；
- `component_and_residue_classification_validator`：需要迁移到 subagent task/result v2；
- 其他 Phase 1 Skills：尚待编写。

本轮尚未在测试主机运行新增 Tool tests 和全量 validator。Manager、Tool 和 contracts 仍为 draft，不得宣称运行验收通过。

## Source recognition 已确认规则

- 默认复制，不移动源结构；
- 不修改、删除或覆盖原文件；
- 复制前后校验 SHA-256；
- 目标同 hash 时复用；
- 目标不同 hash 时阻塞并请求决定；
- 只有 resolved user decision 与 source write permission 同时存在时才允许移动；
- 受保护 `01_sources/` 不得移动。

## 尚未冻结

- content map 的 `load_when` 与 `applicable_to` 扩展；
- `runtime_schema_validator` 的 ACTIVE 状态；
- `state_transaction`、`incremental_reference_checker` 和 `task_closure_renderer` 实现。

## 当前权威文件

- `AGENTS.md`；
- `design_records/logging_and_record_system.md`；
- `00_manager/md_workflow_manager/SKILL.md`；
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- `00_manager/md_workflow_manager/references/manager_display_rules.md`；
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`；
- `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`；
- `00_authoring/md-workflow-tool-authoring/SKILL.md`；
- `05_tools/tool_registry.yaml`；
- `03_contracts/README.md`；
- `04_evals/md_workflow_manager/MANAGER_DRAFT_VALIDATION.md`；
- 本文件。

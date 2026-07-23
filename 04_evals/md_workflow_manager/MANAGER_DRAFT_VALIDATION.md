# md_workflow_manager Draft Validation

日期：2026-07-23

## 检查对象

- `00_manager/md_workflow_manager/SKILL.md`
- `00_manager/md_workflow_manager/references/project_initialization_protocol.md`
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`
- `00_manager/md_workflow_manager/references/manager_display_rules.md`
- `00_manager/md_workflow_manager/references/manager_runtime_checklist.md`
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`
- `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`
- `00_authoring/md-workflow-tool-authoring/SKILL.md`
- `05_tools/tool_registry.yaml`
- `05_tools/runtime_schema_validator/`
- `04_evals/runtime_schema_validator/VALIDATION.md`
- `design_records/logging_and_record_system.md`
- Manager fixtures 与 shared contracts

## 当前静态状态

```text
md_workflow_manager/SKILL.md lines: 311
manager behavior cases: 20
initialization transaction cases: 4
route planning cases: 12
task recording/display cases: 7
validation mode cases: 8
bootstrap dependency cases: 6
route record schema version: 3
runtime_schema_validator status: ACTIVE
```

Manager 主文件处于渐进披露目标范围。Manager 整体仍是 draft，因为真实项目端到端测试尚未完成。

## 已修正的启动自锁

此前存在：

```text
NEW
→ mandatory FULL
→ only IMPLEMENTED validator
→ no ACTIVE implementation
→ initialization BLOCKED
```

当前修正为：

```text
NEW
→ capability preflight
→ ACTIVE runtime_schema_validator 0.1.0
→ candidate FULL validation
→ built-in controlled atomic state commit
→ PROJECT_INITIALIZED
```

`state_transaction` 仍为 `DESIGNED`，但不是 NEW 初始化的强制依赖。初始化协议已定义可运行的内建确定性提交路径。

## Tool 激活证据

`runtime_schema_validator` 精确代码 blob 与 tests 在隔离环境中执行：

```text
5 passed in 10.02s
```

benchmark：

```yaml
FAST cold median: 5.977 ms
FAST warm median: 3.311 ms
FULL warm median: 4.181 ms
```

完整证据：

```text
04_evals/runtime_schema_validator/VALIDATION.md
```

该 Tool 已满足当前激活条件并注册为 `ACTIVE`。真实大型项目 benchmark 与 Manager 端到端集成仍待完成，但不再造成 NEW 初始化 capability deadlock。

## 阻断因果分层

Manager 输出必须区分：

```text
Current blocker
Pending after current barrier
```

在初始化 gate：

- FULL capability 缺失可以是当前 blocker；
- 路线终点歧义只能在初始化后处理；
- 未连接 Workflow 只能在路线规划到达边界后处理；
- 后两项不得与初始化 blocker 并列为同一级停止原因。

新增 `bootstrap_dependency_cases.yaml` 覆盖 ACTIVE validator、能力缺失、可选 state transaction、路线歧义时序、未连接 Workflow 时序和 hard-gate release preflight。

## 入口控制顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ capability preflight
→ candidate project/workstream state
→ FULL schema/reference validation
→ controlled state commit
→ persistent project state: RESUMABLE
→ PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

Barrier：

1. `PROJECT_INITIALIZED` 前不调用 Workflow、不创建 route 或业务 task；
2. `ROUTE_SCOPE_RESOLVED` 前不请求 fragment、不创建 route；
3. 有效 active route 不存在时不创建业务 task。

## 仍需完成

1. 在真实测试项目复测 NEW 自动初始化；
2. 验证初始化实际调用 ACTIVE FULL validator；
3. 验证 `state_transaction` 未实现时走内建提交路径；
4. 验证“开始 MD”只在初始化后触发路线终点确认；
5. 验证未连接 Workflow 只在路线规划边界形成 PARTIAL/BLOCKED；
6. 完成 Manager → Workflow → task → FAST validation → state/record 端到端测试；
7. 使用真实目录验证恢复和部分提交异常。
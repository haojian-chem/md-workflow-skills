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
- `design_records/logging_and_record_system.md`
- Manager fixtures 与 shared contracts

## 当前静态状态

```text
md_workflow_manager/SKILL.md lines: 311
previous lines: 495
reduction: 184 lines
front matter: PASS by GitHub reread
manager behavior cases: 20
initialization transaction cases: 4
route planning cases: 12
task recording/display cases: 7
validation mode cases: 8
route record schema version: 3
runtime_schema_validator status: IMPLEMENTED, not ACTIVE
```

主文件已回到渐进披露目标范围。该结果是规则与文件结构静态对齐，不代表测试主机上的运行验收已经通过。

## 渐进披露迁移

主 `SKILL.md` 仅保留：

- 顶层职责与禁止事项；
- 入口状态和三个 execution barrier；
- Focus/Workstream 路由；
- Workflow planning/execution 调用规则；
- task 顶层闭环；
- FAST/FULL 选择；
- 恢复、结束和用户展示入口；
- 八个顶层自检 barrier。

下沉内容：

```text
初始化事务、候选状态、FULL、原子提交与失败处理
→ references/project_initialization_protocol.md

完整运行自检
→ references/manager_runtime_checklist.md

FAST/FULL、cache、Tool 权限与失败
→ deterministic_tool_protocol.md

记录、session、snapshot 与最小闭环细节
→ design_records/logging_and_record_system.md

closure 字段与展示格式
→ references/manager_display_rules.md
```

本轮只迁移和去重，没有改变已确认入口顺序、路线范围语义、task 闭环或 Tool 规则。

## 入口控制顺序

```text
ENTRY_STATE_EVALUATED: NEW
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
2. `ROUTE_SCOPE_RESOLVED` 前不创建 route；
3. 有效 active route 不存在或不适用时不创建业务 task。

## 普通 task 最小记录闭环

```text
task.yaml
→ subagent execution
→ candidate result/related records/state
→ one FAST validation
→ commit
→ one terminal task event
→ Workstream state
→ task closure summary
```

普通 task 不机械写 `TASK_PREPARED`、`TASK_STARTED`、无变化 project state、session 增量、snapshot、route revision 或 FULL validation。

## FAST/FULL 与 Tool

FAST 仅处理 changed runtime instances 与直接引用；FULL 仅用于初始化、恢复、contract/root 变化和关键生命周期节点。

禁止：

- 每步扫描全部项目记录；
- schema hash/cache 命中时重复 meta-validation；
- 用 LLM 逐字段模拟 FULL；
- 将未测试 `IMPLEMENTED` Tool 作为默认生产路径。

模型强度分层未采纳，不属于本 contract。

## Task closure 用户展示

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，必须在下一前台 task 前显示精简 closure summary。

`source_recognition` 的 DONE 只能表示来源识别、复制/复用和 SHA-256 检查通过；STRUCTURE artifact 仍为 `UNVALIDATED`。

## 仍需完成

Manager 保持 `draft`，尚不能冻结。后续必须：

1. 运行全量 authoring contract/content-map validator；
2. 检查新 references 与主文件之间无遗漏、冲突和重复定义；
3. 在测试主机运行 `runtime_schema_validator` tests 与 benchmark；
4. 实测 NEW 初始化严格调用 initialization protocol；
5. 实测普通 task 只产生一次 FAST Tool 调用；
6. 实测 `source_recognition` closure summary；
7. 完成 Manager → Workflow → task → FAST validation → state/record 的端到端测试；
8. 使用真实目录验证项目级与 Workstream 级恢复。

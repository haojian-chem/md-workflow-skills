# md_workflow_manager Draft Validation

日期：2026-07-23

## 检查对象

- `00_manager/md_workflow_manager/SKILL.md`
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`
- `00_manager/md_workflow_manager/references/manager_display_rules.md`
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`
- `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`
- `00_authoring/md-workflow-tool-authoring/SKILL.md`
- `05_tools/tool_registry.yaml`
- `05_tools/runtime_schema_validator/`
- `design_records/logging_and_record_system.md`
- `03_contracts/project_event.schema.yaml`
- `03_contracts/route_record.schema.yaml` v3
- `04_evals/md_workflow_manager/fixtures/manager_behavior_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/initialization_transaction_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/route_planning_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/task_recording_and_display_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/validation_mode_cases.yaml`

## 当前静态状态

```text
md_workflow_manager/SKILL.md lines: 495
front matter: PASS by GitHub reread
manager behavior cases: 20
initialization transaction cases: 4
route planning cases: 12
task recording/display cases: 7
validation mode cases: 8
route record schema version: 3
runtime_schema_validator status: IMPLEMENTED, not ACTIVE
```

Manager Skill 仍低于 500 行渐进披露警告阈值，但已接近阈值。后续新增细节应优先下沉到 references，避免主文件继续增长。

本报告记录规则、content map 和 fixtures 的静态对齐，不代表测试主机上的真实运行验收已经通过。

## 入口控制顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ 候选状态生成
→ FULL schema/reference validation
→ 受控提交 project/workstream state
→ 持久 project state: RESUMABLE
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

## 普通 task 最小记录闭环

```text
task.yaml
→ subagent execution
→ candidate result/related records/state
→ FAST validation
→ result.yaml
→ 必要 artifact/decision/submission record
→ 一条终态 task event
→ Workstream state
→ task closure summary
```

普通 task 默认不机械写入：

- `TASK_PREPARED`；
- `TASK_STARTED`；
- 执行前 Workstream `EXECUTING` 更新；
- 无变化的 project state；
- Manager session 逐 task 增量；
- snapshot；
- 无变化 route revision；
- 空 artifact/decision/submission record；
- FULL contract validation。

外部 submission、长耗时、高风险或不可逆 task 仍保留强化预记录和恢复锚点。

## FAST/FULL 校验规则

### FAST

普通 task 只对本次 changed runtime instances 进行一次批量校验，并检查直接引用。

禁止：

- 扫描全部 Workstream/route/artifact/decision/submission/event；
- 每步调用 authoring `validate_contracts.py`；
- schema hash 未变化时重复 meta-validation；
- 用 LLM 逐字段模拟 FULL。

### FULL

仅用于：初始化、schema/contract 变化、恢复前后、root 变化、重要 Workstream、重大 artifact 谱系变化、首个外部长任务提交前、Workstream 终结或用户明确完整审计。

模型强度分层未采纳，不属于本轮规则。

## 确定性 Tool 集成

已建立：

- Tool Authoring Skill；
- deterministic tool protocol；
- tool registry；
- `runtime_schema_validator` 0.1.0 初始实现；
- `state_transaction`、`incremental_reference_checker`、`task_closure_renderer` 设计 contract。

`runtime_schema_validator` 支持：

- FAST/FULL；
- schema bundle hash cache；
- changed paths 批量校验；
- direct reference checks；
- candidate actual path 到 future logical project path overlay。

该 Tool 尚未运行 tests/benchmark，因此 registry 保持 `IMPLEMENTED`、`active_by_default: false`。

## Task closure 用户展示

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，必须在下一前台 task 启动前显示精简 closure summary。

`source_recognition` 的 DONE 只能表述来源识别、复制/复用和 SHA-256 检查通过；其 STRUCTURE artifact 仍为 `UNVALIDATED`。

## fixtures 覆盖

`validation_mode_cases.yaml` 覆盖：

- 普通 task 单次 FAST 批量校验；
- 初始化和恢复使用 FULL；
- schema cache hit/miss；
- Tool FAIL 阻止终态提交；
- IMPLEMENTED 未验证 Tool 不作为默认路径；
- 模型强度规则不进入本 contract。

`runtime_schema_validator` tests/fixtures 覆盖设计包括：

- FAST 忽略无关无效记录；
- FULL 发现无关记录错误；
- schema hash cache；
- missing direct reference；
- candidate logical path overlay。

## 仍需完成

Manager 保持 `draft`，尚不能冻结。后续必须：

1. 在测试主机运行 `04_evals/runtime_schema_validator/test_validate.py`；
2. 记录 FAST cold-cache、FAST warm-cache 和 FULL benchmark；
3. 运行全量 authoring contract/content-map validator；
4. 确认无 false PASS 后，再决定是否把 `runtime_schema_validator` 标为 ACTIVE；
5. 实测普通 task 只产生一次 FAST Tool 调用；
6. 实测 NEW 初始化的 candidate overlay + FULL validation；
7. 实测 `source_recognition` closure summary；
8. 完成 Manager → Workflow → task → FAST validation → state/record 的端到端测试；
9. 使用真实目录验证恢复行为。

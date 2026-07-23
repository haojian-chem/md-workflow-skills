# md_workflow_manager Draft Validation

日期：2026-07-23

## 检查对象

- `00_manager/md_workflow_manager/SKILL.md`
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`
- `00_manager/md_workflow_manager/references/manager_display_rules.md`
- `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`
- `design_records/logging_and_record_system.md`
- `03_contracts/project_event.schema.yaml`
- `03_contracts/route_record.schema.yaml` v3
- `04_evals/md_workflow_manager/fixtures/manager_behavior_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/initialization_transaction_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/route_planning_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/task_recording_and_display_cases.yaml`

## 当前静态状态

```text
md_workflow_manager/SKILL.md lines: 443
front matter: PASS by GitHub reread
manager behavior cases: 20
initialization transaction cases: 4
route planning cases: 12
task recording/display cases: 7
route record schema version: 3
```

Manager Skill 仍低于 500 行渐进披露警告阈值。

本报告记录规则和 fixture 对齐状态，不代表测试主机上的真实运行验收已经通过。

## 入口控制顺序

```text
ENTRY_STATE_EVALUATED: NEW
→ 候选状态生成与校验
→ 原子提交 project/workstream state
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

已确认普通短耗时前台 task 使用：

```text
task.yaml
→ subagent execution
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
- 空 artifact/decision/submission record。

外部 submission、长耗时、高风险或不可逆 task 仍保留强化预记录和恢复锚点。

## Task closure 用户展示

每个前台 task 进入 `DONE | BLOCKED | FAILED` 后，必须在下一前台 task 启动前显示精简 closure summary。

DONE 覆盖：task、执行/gate 结果、关键动作或产物、artifact validation status、warning、report 路径和下一 task。

BLOCKED 覆盖：已完成部分、阻断原因、用户决定和未启动后续。

FAILED 覆盖：失败位置、直接证据、保留/清理产物、Workstream 状态和可选后续。

`source_recognition` 的 DONE 只能表述来源识别、复制/复用和 SHA-256 检查通过；其 STRUCTURE artifact 仍为 `UNVALIDATED`，不得显示“结构验证通过”。

宿主支持中间可见消息时，closure 输出后可继续既定范围；不支持时，本轮以 closure summary 结束，保留 expected next task。

## 新增 fixtures 覆盖

`task_recording_and_display_cases.yaml` 包含 7 个 cases：

- 普通前台 task 最小记录；
- 高风险 task 保留恢复锚点；
- source recognition 结果在下一 task 前可见；
- BLOCKED closure 显示 decision；
- FAILED closure 显示证据；
- 不支持中间消息时结束当前轮次；
- 支持中间消息时可继续且 closure 不构成 confirmation gate。

## 仍需完成

Manager 保持 `draft`，尚不能冻结。后续必须：

1. 运行全量 contract validator；
2. 将现有行为 fixtures 转换为完整可执行输入/输出对象；
3. 实测 NEW 自动初始化；
4. 实测模糊请求产生 `ROUTE_SCOPE_REQUESTED`；
5. 实测普通 task 不产生冗余记录；
6. 实测 `source_recognition` 完成后在对话窗口输出 closure summary；
7. 完成 Manager → Workflow → task → result → state/record 的端到端测试；
8. 使用真实目录验证恢复行为。
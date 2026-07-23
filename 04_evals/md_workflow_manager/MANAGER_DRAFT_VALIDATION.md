# md_workflow_manager Draft Validation

日期：2026-07-23

## 检查对象

- `00_manager/md_workflow_manager/SKILL.md`
- `00_manager/md_workflow_manager/references/stage_registry.yaml`
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`
- `00_manager/md_workflow_manager/references/manager_display_rules.md`
- `03_contracts/project_event.schema.yaml`
- `03_contracts/route_record.schema.yaml` v3
- `00_authoring/content_maps/md_workflow_manager.yaml`
- `04_evals/md_workflow_manager/fixtures/manager_behavior_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/initialization_transaction_cases.yaml`
- `04_evals/md_workflow_manager/fixtures/route_planning_cases.yaml`

## 当前静态状态

```text
SKILL.md lines: 428
front matter: PASS
name field: PASS
description field: PASS
parallel foreground execution field: absent
manager behavior cases: 20
initialization transaction cases: 4
route planning cases: 12
project event additions:
  - ROUTE_SCOPE_REQUESTED
  - ROUTE_SCOPE_RESOLVED
route record schema version: 3
```

`SKILL.md` 仍低于 authoring validator 的 500 行渐进披露警告阈值。

本轮已从 GitHub 重新读取修改后的 Manager Skill、route record 开头和 behavior fixtures。完整可执行 schema validation 与端到端运行仍属于待完成事项，不能仅凭本报告视为运行验收通过。

## 已确认的入口控制顺序

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

已明确三个 barrier：

1. `PROJECT_INITIALIZED` 前不调用 Workflow、不创建 route 或业务 task；
2. `ROUTE_SCOPE_RESOLVED` 前不请求 fragment、不创建 route；
3. 有效 active route 不存在时不创建业务 task。

`PROJECT_INITIALIZED` 只能在候选状态通过 schema/引用检查并成功提交后记录。初始化时创建首个 Workstream，但 `active_route_id` 和 `active_task_id` 均为 `null`。

## 本轮新增覆盖行为

- NEW 只是本轮入口判定，不是初始化后的持久状态；
- NEW 成功初始化后，持久 project state 使用 `entry_state: RESUMABLE`；
- NEW 在根目录明确且无冲突时自动初始化，不要求用户再次提示；
- 初始化不创建首条业务路线；
- 候选状态校验失败时不记录 `PROJECT_INITIALIZED`；
- 部分提交异常时进入 NEEDS_RECOVERY；
- 明确指定 `source_recognition` 时，初始化后独立解析到该终点；
- “开始处理这个结构”等模糊请求必须请求用户确认；
- 不得默认选择下一 task、当前 Workflow 结束、Workstream 目标或项目终点；
- `route_record` v3 保存 `scope_resolution.source`、resolved event 和 decision 引用；
- RESUMABLE 项目存在明确有效 active route 时，“继续”可以复用既有范围；
- 新 Workstream 创建本身不自动触发路线规划。

## 既有覆盖行为

- 有业务产物但无状态的项目级恢复；
- 参数 v1 后台生产 MD 与参数 v2 新分支并存；
- 原 Workstream 内修正与必须分支的边界；
- Project/Workstream Focus；
- 三种 task unit；
- Operation 与 Validator 返回分离；
- blocking decision；
- `FINISHED_UNVERIFIED`；
- 失败任务不自动重试与新 task ID 重试；
- 下一 Workflow 尚未连接；
- Focus 歧义；
- 子 Agent 写管理目录的越权拒绝；
- 未变化路线不重复完整展示。

## 仍需完成

Manager 保持 `draft`，尚不能冻结。后续必须完成：

1. 运行全量 contract validator，确认 `project_event` 和 `route_record` v3 的 Draft 2020-12 合法性；
2. 将入口、初始化、范围解析和执行 fixtures 转换为可执行输入状态与预期结构化输出；
3. 用共享 schemas 校验初始化生成的 project/workstream state、events、decision 和 route v3；
4. 实测 NEW 自动初始化，不依赖额外用户提示；
5. 实测模糊请求产生 `ROUTE_SCOPE_REQUESTED`，且不创建 route/task；
6. 实测明确终点产生 `ROUTE_SCOPE_RESOLVED` 后才进入规划；
7. 完成至少一次 Manager → Workflow → task unit → result → state/record 的端到端测试；
8. 使用真实目录案例验证项目级与 Workstream 级恢复。

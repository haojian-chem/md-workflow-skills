# md_workflow_manager Draft Validation

日期：2026-07-22

## 检查对象

- `00_manager/md_workflow_manager/SKILL.md`
- `00_manager/md_workflow_manager/references/stage_registry.yaml`
- `00_manager/md_workflow_manager/references/manager_display_rules.md`
- `00_authoring/content_maps/md_workflow_manager.yaml`
- `04_evals/md_workflow_manager/fixtures/manager_behavior_cases.yaml`

## 静态检查结果

```text
SKILL.md lines: 286
front matter: PASS
name field: PASS
description field: PASS
parallel foreground execution field: absent
stage_registry.yaml parse: PASS
content map v3 structure: PASS
behavior fixture YAML parse: PASS
behavior cases: 15
case IDs unique: PASS
```

`SKILL.md` 低于 authoring validator 的 500 行渐进披露警告阈值。

## 已覆盖行为

- 空项目初始化；
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

1. 将 fixtures 转换为可执行的输入状态和预期结构化输出；
2. 用 14 份共享 schemas 校验 Manager 生成的 task/state/record；
3. 完成 `structure_preparation_workflow` 的 Workstream 接口迁移；
4. 完成至少一次 Manager → Workflow → task unit → result → state/record 的端到端测试；
5. 使用真实目录案例验证项目级与 Workstream 级恢复。

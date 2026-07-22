# Workstream Contract Alignment Validation

日期：2026-07-22

## 1. 验证范围

本轮对齐涉及：

- 14 份 `03_contracts/*.schema.yaml`；
- `03_contracts/README.md`；
- authoring Skill、四层职责和串行临时子 Agent 协议；
- Manager、authoring 和 structure Workflow 的 content map；
- Skill inventory、file ownership、模板和多窗口检查文件。

## 2. Contract 静态检查

对 14 份 schema 执行：

1. YAML 解析；
2. 根对象检查；
3. `$schema` 存在性检查；
4. `$id` 与文件名一致性检查；
5. JSON Schema Draft 2020-12 `check_schema`。

结果：

```text
checked_contracts: 14
schema_errors: 0
```

验证脚本：

`00_authoring/md-workflow-skill-authoring/scripts/validate_contracts.py`

## 3. GitHub 写入一致性

- 原有 6 份 contract 的 GitHub blob SHA 与本地通过验证的内容一致；
- 新增 8 份 contract 均重新从 GitHub 读取 blob SHA，并与本地通过验证的内容逐项一致；
- 未发现手工写入造成的 YAML 内容偏差。

新增 contracts：

- `workstream_state.schema.yaml`
- `project_event.schema.yaml`
- `manager_session.schema.yaml`
- `route_record.schema.yaml`
- `decision_record.schema.yaml`
- `submission_record.schema.yaml`
- `artifact_set.schema.yaml`
- `state_snapshot.schema.yaml`

## 4. Content map 检查

本轮修改的 3 份 content map：

- `md-workflow-skill-authoring.yaml`
- `md_workflow_manager.yaml`
- `structure_preparation_workflow.yaml`

均通过 content map v3 结构检查，错误数为 0。

其余 14 份 content map 本轮未修改；沿用此前 17 份 map 全量验证为 0 error 的结果。

## 5. 已消除的旧接口

- 项目唯一 `current_workflow/current_stage`；
- 只允许单个 Operation 或 Validator 的旧 task schema；
- 合并 Operation/Validator 返回的模糊结果；
- `requires_user_confirmation` 与 confirmation list 的重复事实；
- tmux/job 消失即视为模拟完成；
- Operation/Validator 直接写项目状态或管理记录。

## 6. 当前迁移状态

共享 contracts 已完成对齐，但以下业务 Skill 仍需迁移：

- `md_workflow_manager`：按 Workstream、Focus、状态和记录 contracts 重写；
- `structure_preparation_workflow`：改为消费单个 Focus Workstream 状态；
- `source_recognition`：迁移到 subagent task/result v2；
- `component_and_residue_classification_validator`：迁移到 subagent task/result v2。

在这些 Skill 完成迁移和 eval 前，不得将其 contract 状态改为 `frozen`。

## 7. 未覆盖事项

本轮没有加入 content map 的：

- `load_when`
- `applicable_to`

这两个字段仍属于未冻结扩展。

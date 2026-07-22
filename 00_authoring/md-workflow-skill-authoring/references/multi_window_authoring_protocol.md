# 网页端多窗口编写协议

本文件只描述用户在网页端打开多个独立窗口编写不同 Skill 的协作方式。

网页窗口不是运行时子 Agent，也不需要 Agent 配置。

## 主窗口

主窗口负责：

- `AGENTS.md`；
- `00_authoring/SYNC_STATUS.md`；
- `03_contracts/`；
- authoring references 和 assets；
- Skill inventory；
- content maps；
- file ownership；
- design records；
- 跨 Skill 接口裁决；
- 最终集成和共享验证。

## 业务 Skill 窗口

每个业务窗口只负责一个明确 Skill 或一组完全互斥的文件。

开始前必须读取：

- `AGENTS.md`；
- `00_authoring/SYNC_STATUS.md`；
- `00_authoring/skill_inventory.yaml`；
- `00_authoring/file_ownership.yaml`；
- 目标 Skill 的 content map；
- 对应 work order；
- `03_contracts/README.md` 与适用 schema；
- 相关上下游 Skill。

必须：

- 先列出“已做过 / 已否定 / 仍未验证”；
- 只写被分配的 `write_paths`；
- 不修改共享 contracts、content maps 或设计记录；
- 不重新定义 Workstream、Focus、task unit 或四层边界；
- 运行指定静态检查；
- 提交精简交付摘要。

## 写入冲突

- 一个文件同一时刻只有一个窗口；
- 一个 Skill 目录默认只有一个窗口；
- 路径重叠时改为串行；
- 共享 contract 修改由业务窗口提交 change request，主窗口实施；
- 不使用开发子 Agent 解决窗口冲突。

## 启动条件

某 Skill 只有在以下内容具备后才能交给新窗口：

- 层级与邻近边界；
- 局部 contract；
- content map；
- 适用共享接口；
- `write_paths`；
- work order；
- inventory 和 ownership 中无冲突状态。

如果共享 contract 已冻结但目标 Skill 尚未对齐，work order 必须明确列出需要迁移的 schema 版本和旧字段。

## 运行架构约束

业务窗口不得写出以下错误架构：

- Workflow 作为 Agent；
- 子 Agent 嵌套委派；
- 多个前台 MD 子 Agent；
- Operation/Validator 直接修改 `00_project_state/` 或 `00_project_records/`；
- 把多个外部 tmux/调度任务并存误写为前台 Agent 并行；
- 把项目状态重新简化为唯一当前 Workflow。

## 交付格式

```yaml
window_id:
task_id:
skill_name:
status: DRAFTED | BLOCKED | REVIEW_REQUIRED
read_files: []
created_files: []
modified_files: []
validation_run: []
contract_change_requests: []
open_questions: []
summary:
```

长日志保存在任务或评测目录，不复制到主窗口。

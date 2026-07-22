# 网页端多窗口编写协议

本文件只描述用户在网页端打开多个独立窗口编写不同 Skill 的协作方式。

网页窗口不是运行时子 Agent，也不需要 Agent 配置。

## 主窗口

主窗口负责：

- `AGENTS.md`；
- `03_contracts/`；
- authoring references；
- Skill inventory；
- content maps；
- file ownership；
- 跨 Skill 接口裁决；
- 最终集成。

## 业务 Skill 窗口

每个业务窗口只负责一个明确 Skill 或一组完全互斥的文件。

必须：

- 读取目标 Skill 的 contract、content map 和 work order；
- 只写 `write_paths`；
- 不修改共享 contracts；
- 不重新定义层级边界；
- 运行静态检查；
- 提交精简交付摘要。

## 写入冲突

- 一个文件同一时刻只有一个窗口；
- 一个 Skill 目录默认只有一个窗口；
- 路径重叠时改为串行；
- 共享 contract 修改由窗口提交 change request，主窗口实施；
- 不使用开发子 Agent 解决窗口冲突。

## 启动条件

某 Skill 只有在以下内容冻结后才能交给新窗口：

- 层级；
- 局部 contract；
- content map；
- 上下游共享接口；
- `write_paths`；
- work order。

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

长日志保存在任务目录，不复制到主窗口。

# Authoring 基础

本目录服务于网页端多个独立窗口编写 MD Workflow Skills。

它不创建、注册或模拟任何开发子 Agent。

- `md-workflow-skill-authoring/`：编写指导 Skill；
- `content_maps/`：每个 Skill 的内容唯一归属；
- `window_work_orders/`：网页窗口任务单；
- `skill_inventory.yaml`：Skill 清单与状态；
- `file_ownership.yaml`：互斥写入范围；
- `readiness_checklist.md`：开始多窗口编写前的检查。

## Content map v3

- `content_map.schema.yaml`：content map 的统一结构与规则；
- `content_maps/`：仅记录内容唯一归属和外部只读引用；
- 未完成契约的 Skill 使用最小 pending 骨架，不预建 references 或 schemas；
- 网页窗口写入所有权由 `file_ownership.yaml` 和任务单管理，不写入 content map。

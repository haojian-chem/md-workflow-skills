# Current deterministic tools

`tools/` 是**不占用 MD Workflow Stage 编号**的跨 Stage 确定性能力目录。

它不是 Scientific Skill root。只有已经适配当前 Lightweight Runtime / current Skill 接口，并完成适用测试与验证的共享 Tool 才进入这里。

当前旧 `05_tools/` 中的工具大多依赖 Legacy Workstream / route / runtime task-result / contracts，因此已迁入 `legacy/tools/`，不能因为历史上曾标记 ACTIVE 就继续作为 current 默认实现。

共享 Tool 的 authoring authority：

`00_authoring/md-workflow-tool-authoring/SKILL.md`

测试与 validation evidence 放在 unnumbered `evals/`。

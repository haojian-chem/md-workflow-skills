# 官方资料依据

检索日期：2026-07-21

- https://learn.chatgpt.com/docs/build-skills
  - Skill 包含必需的 `SKILL.md` 和可选的 `scripts/`、`references/`、`assets/`、`agents/openai.yaml`。
  - Skill 使用渐进披露。
  - `description` 决定隐式触发，应前置主要用途和边界。
  - 每个 Skill 聚焦一个工作；默认优先使用指令；步骤应明确输入和输出。

- https://learn.chatgpt.com/guides/best-practices
  - 复杂工作先规划，明确目标、上下文、约束和完成条件。
  - 持久项目规则适合放在 `AGENTS.md`。

- https://learn.chatgpt.com/docs/agent-configuration/agents-md
  - `AGENTS.md` 可按目录分层，并应避免无边界膨胀。

- https://learn.chatgpt.com/docs/agent-configuration/subagents
  - 子 Agent 可隔离独立任务上下文；具体使用方式应结合任务边界、工具权限和返回摘要设计。

本项目对官方能力作出的项目级选择：MD 子任务暂时只串行创建临时子 Agent，目的为上下文隔离，不采用并行执行。

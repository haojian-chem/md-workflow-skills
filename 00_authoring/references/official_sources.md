# 官方资料依据

Status: SUPPORTING REFERENCE

本文件只保存 Skill authoring 相关官方资料的来源线索，不拥有本项目当前 Skill/Runtime 规则。

项目当前行为以：

```text
00_authoring/SKILL.md
00_authoring/references/*.md
00_authoring/lightweight_runtime_v2_spec.md
```

为准；不得从旧的官方资料快照反推出已经被项目当前设计否定的行为。

历史检索记录：2026-07-21。

- `https://learn.chatgpt.com/docs/build-skills`
  - Skill 包含 `SKILL.md` 与按需 supporting files；
  - Skill 使用渐进披露；
  - `description` 用于说明用途和边界；
  - Skill 应聚焦清楚工作职责。

- `https://learn.chatgpt.com/guides/best-practices`
  - 复杂工作应明确目标、上下文、约束和完成条件。

- `https://learn.chatgpt.com/docs/agent-configuration/agents-md`
  - `AGENTS.md` 可保存持久项目规则，并应控制作用边界。

这些记录可能随产品文档更新而变化。需要依赖具体 OpenAI 产品行为进行新的 authoring 决策时，应重新核对当前官方文档，而不是把本文件当作永久产品规范。

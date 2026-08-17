# Architecture freeze records

Status: CURRENT AUTHORING REFERENCE DIRECTORY

本目录集中保存已经敲定的 Stage / Workflow 架构冻结记录。

规则：

- current architecture-freeze Markdown 统一放在本目录；
- 根目录 `00_authoring/` 不再散放各 Stage 的 freeze 文件；
- freeze 文件只保存已经冻结的阶段架构、边界和明确拒绝项；
- 具体 Skill 的当前执行细节仍由对应 current `SKILL.md` / references 拥有；
- freeze 文件不是为了重复 current Skill，而是用于架构追溯和 authoring 边界确认；
- 被新的 freeze record 明确取代的旧 Markdown 移入 `00_authoring/archive/`，不继续留在 active path。

当前冻结记录：

```text
WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

如后续 Stage 1 形成正式 architecture-freeze record，也加入本目录，而不是放回 `00_authoring/` 根目录。

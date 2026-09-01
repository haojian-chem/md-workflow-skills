# Authoring archive

Status: ARCHIVE / NOT CURRENT AUTHORITY

本目录保存已经被 current Skill / reference / architecture 取代、但仍值得保留用于历史查阅的 authoring 材料。

规则：

- 普通 Skill authoring、Manager 和 Task Execution Agent 不默认读取本目录；
- archive 中的内容不能用于推翻 current `00_authoring/SKILL.md`、current references 或 current architecture-freeze；
- 文件进入 archive 前，仍有效规则必须已经迁移到 current owner；
- current active path 不同时保留同一份 `SUPERSEDED` / `LEGACY` tombstone；
- Git history 仍是完整版本历史来源；
- 归档依据是 authority 已明确被取代，而不是文件年龄。

Stage-specific architecture history：

```text
stage1_history/   Stage 1 已实现并退出 current authority 的 architecture freezes
stage2_history/   Stage 2 已实现、被后续设计取代或退出 current authority 的 architecture freezes
stage3_history/   Stage 3 旧 step-level 与已实现 Stage-level architecture freezes
stage4_history/   Stage 4 已实现并退出 current authority 的 architecture freezes
stage5_history/   Stage 5 已退出 current authority 的历史设计
```

其它 `legacy_*`、`root_history/` 等目录按其既有语义保存历史材料。

当前归档规则见：

`00_authoring/references/skill_generation_rules.md`

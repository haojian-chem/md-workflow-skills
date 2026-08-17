# Legacy runtime and tool material

`legacy/` 保存已退出默认 current architecture、但仍有旧项目恢复 / 迁移 / 历史审计价值的可执行代码、schemas 与 generated runtime material。

当前包含：

```text
contracts/   # old shared runtime schemas
runtime/     # old manager/runtime projections and task contracts
tools/       # old runtime-dependent deterministic tools
```

这些内容不是 current Skill / Runtime authority。普通 Manager、Task Execution Agent 和 Skill authoring 不默认读取这里。

Current authorities：

```text
00_authoring/SKILL.md
00_authoring/project_design/lightweight_runtime_v2_spec.md
00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
current Stage SKILL.md / references
```

历史设计 Markdown 不放在本目录，统一归入 `00_authoring/archive/`。

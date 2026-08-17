# Legacy runtime, tool and evaluation material

`legacy/` 保存已退出默认 current architecture、但仍有旧项目恢复 / 迁移 / 历史审计价值的可执行代码、schemas、tests 与 workflow automation。

```text
legacy/
├── contracts/          # old shared runtime schemas
├── runtime/            # old runtime projections / task contracts
├── tools/              # old runtime-dependent deterministic tools
├── evals/              # old role/runtime-dependent evaluation suites
└── github_workflows/   # snapshot of old CI workflows removed from active .github/workflows
```

这些内容不是 current Skill / Runtime authority。普通 Manager、Task Execution Agent、Skill authoring 和 current CI 不默认读取或执行这里。

Current authorities：

```text
00_authoring/SKILL.md
00_authoring/project_design/lightweight_runtime_v2_spec.md
00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
current Stage SKILL.md / references
tools/   # current revalidated shared deterministic tools
evals/   # current evaluation suites only
```

历史设计 Markdown 不放在本目录，统一归入 `00_authoring/archive/`。

Legacy capability 若要重新成为 current，必须逐项完成 current-interface adaptation、testing / validation 和显式 reactivation；不得整批恢复。

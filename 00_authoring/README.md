# Authoring directory guide

`00_authoring/` 服务于 MD Workflow Skill / Tool 的设计、冻结和多窗口 authoring；它不是科研项目运行目录。

## Single authoring entry

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

`00_authoring/SKILL.md` 是唯一 authoring 主入口。

## Current scientific Skill roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

只有这些编号目录对应 MD Workflow Stage。

Manager：

```text
00_manager/
├── SKILL.md
└── references/
```

## Unnumbered repository infrastructure

```text
evals/      # tests / fixtures / validation evidence / benchmark
tools/      # current shared deterministic tools
legacy/     # old contracts / runtime / runtime-dependent tools
```

这些目录不是 Scientific Skill roots，因此不使用 `03_`、`04_`、`05_` 等 Stage 编号。

历史设计 Markdown 统一放在 `00_authoring/archive/`。旧顶层 `design_records/` 已归入 `00_authoring/archive/legacy_runtime/design_records/`。

## Current authoring layout

```text
00_authoring/
├── SKILL.md
├── README.md
├── references/
├── assets/
├── scripts/
├── architecture_freezes/
├── project_design/
├── coordination/
├── archive/
└── md-workflow-tool-authoring/
```

Stage / Workflow freeze 位于 `architecture_freezes/`；跨 Stage runtime 与 Master Plan 位于 `project_design/`；历史材料位于 `archive/`。

## Current Skill model

```text
main Skill
├── references/        # optional long / conditional detail
├── schemas/           # only when truly machine-useful
├── scripts/           # Skill-local deterministic helper
└── supporting Skill   # only when complex and clearly bounded
```

不恢复 Workflow / Operation / Validator role-based roots，也不为目录对称创建空 Skill package。

## Authority

```text
具体业务规则 → current Skill / reference
Stage 已冻结架构 → architecture_freezes/
跨 Stage runtime → project_design/lightweight_runtime_v2_spec.md
Stage catalog / 建设状态 → project_design/MD_WORKFLOW_MASTER_PLAN.md
current shared Tool → tools/
historical design → archive/
legacy executable/runtime material → ../legacy/
```

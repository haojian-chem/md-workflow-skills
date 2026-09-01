# Authoring directory guide

`00_authoring/` 服务于 MD Workflow Skill / Tool 的设计、冻结和多窗口 authoring；它不是科研项目运行目录。

## Single authoring entry

```text
00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

`00_authoring/SKILL.md` 是唯一 authoring 主入口。

测试或运行环境中的 `AGENTS.md` 如果存在，只用于 Skill 体系外定位需要加载的 Skill；它不属于 authoring chain、Skill package 或 reference dependency。

## Scientific Stage roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

只有这些编号目录对应 MD Workflow Stage。

Stage / Step 目录可以在正式 Skill generation 前预留；目录存在不代表 `SKILL.md` 已生成或已激活。当前建设状态与 current entry 统一读取：

`project_design/MD_WORKFLOW_MASTER_PLAN.md`

Manager：

```text
00_manager/
├── SKILL.md
└── references/
```

## Unnumbered repository infrastructure

```text
../references/   # execution shared references
../evals/        # tests / fixtures / validation evidence / benchmark
../tools/        # current shared deterministic tools
../legacy/       # old contracts / runtime / runtime-dependent tools
```

这些目录不是 Scientific Stage roots，因此不使用 `03_`、`04_`、`05_` 等 Stage 编号。

历史设计 Markdown 统一放在 `00_authoring/archive/`。旧顶层 `design_records/` 已归入 `00_authoring/archive/legacy_runtime/design_records/`。

## Current authoring layout

```text
00_authoring/
├── SKILL.md
├── README.md
├── references/
├── assets/
├── architecture_freezes/
├── project_design/
├── coordination/
├── archive/
└── md-workflow-tool-authoring/
```

仍承担 current authoring authority 的 freeze 位于 `architecture_freezes/`；Stage / Step 建设状态与 current entry 位于 `project_design/`；历史材料位于 `archive/`。

科研执行 Skill 共用的 validation、正式结果生成、结果记录与结果接口规则位于仓库级 shared reference：

`../references/result_generation_rules.md`

Authoring 在设计或重构 results 时按上游 authoring 规则读取该 execution shared reference，而不是在 `00_authoring/references/` 维护第二份结果规则。

复杂正式结果接口优先由对应 Skill 自己的 `references/results.md` 说明；该文件是 Skill source reference，不是 runtime result artifact。

## Current Skill model

```text
main Skill
├── references/        # optional long / conditional detail; complex result interface may use results.md
├── schemas/           # only when truly machine-useful
├── scripts/           # Skill-local deterministic helper
└── supporting Skill   # only when complex and clearly bounded
```

不恢复 Workflow / Operation / Validator role-based roots，也不为目录对称创建伪 Skill package。已确定的未来 Step 目录可以只用 `.gitkeep` 保留，直到正式 Skill generation 获批。

Stage-level main Skill 不是每个 Stage 的必需层。只有确有 Stage-wide orchestration / shared object / lifecycle 时才设置；没有 Stage main 的 Stage 由 Task Execution Agent 根据 Task Sheet 与 current Step interfaces 推进。

## Status maintenance

`project_design/MD_WORKFLOW_MASTER_PLAN.md` 是 Stage / Step 建设状态和 current entry 的唯一 project-level owner。

任何 authoring 工作如果改变了 freeze / Skill generation / validation milestone 状态，都必须同步 Master Plan；多窗口规则见 `references/multi_window_authoring_protocol.md`。

## Authority

```text
具体业务规则 → current Skill / local reference
科研执行 Skill 共用的 Task Execution 规则 → ../references/task_execution_rules.md
科研执行 Skill 共用的 validation / result generation / result-recording 规则 → ../references/result_generation_rules.md
仍有未完成 authoring / implementation 内容的 current freeze → architecture_freezes/
Stage catalog / 建设状态 / current entry → project_design/MD_WORKFLOW_MASTER_PLAN.md
current shared Tool → ../tools/
historical design → archive/
legacy executable/runtime material → ../legacy/
```

如果某个 Stage 已部分实现但整体 authoring / implementation 仍未完成，可以同时存在 current runtime Skill 与 current freeze：已实现部分以 current Skill / reference 为准，freeze 只继续拥有尚未被 runtime package 接管的设计内容，不得覆盖 current implementation。

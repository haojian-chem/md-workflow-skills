---
task_id: stage1-main-followup-from-1.7
window_id: UNASSIGNED
skill_name: structure-preparation
status: BACKLOG
---

# Goal

在后续负责 `01_structure_preparation/SKILL.md` 的窗口中，同步 1.7 current entry，并检查修正 Stage 1 对 1.7 的 applicability 与前置关系表述，使 Stage 1 main 与当前 active 1.7 和动态任务规划原则一致。

# Current responsibility

本记录由 1.7 authoring 窗口提出，仅作为跨 Skill finding / handoff。当前窗口不修改 `01_structure_preparation/SKILL.md`，也不替 Stage 1 main 定义其内部规划规则。

# Startup

后续处理窗口默认先读取：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 01_structure_preparation/SKILL.md
```

随后按需读取：

- `01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md`
- `00_authoring/references/multi_window_authoring_protocol.md`
- `00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md`
- `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

# 已做过 / 已否定 / 仍未验证

已确认：

- Stage 1 main 已明确 1.1–1.9 是动态科学步骤 catalog，不表示每个任务都必须机械执行每一步。
- 当前 Stage 1 main 同时保留了标题化的 `1.6 → 1.7` handoff，容易被理解为 1.7 必须紧接 1.6 或以 1.6 为强制前置。
- 1.7 authoring 已明确：1.7 不拥有 applicability / route planning；是否执行 1.7 以及其在 Stage 1 任务路线中的位置属于 Stage 1 main 的 planning ownership。
- 1.7 active Skill 已正式生成：`01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md`。
- `MD_WORKFLOW_MASTER_PLAN.md` 已同步 1.7 active status 与 current entry。
- 当前 Stage 1 main 仍把 1.7 标记为 freeze-only，因此 Stage main current-entry 展示已经滞后。

已否定：

- 在 1.7 Skill 中规定“必须先执行 1.6”。
- 在 1.7 Skill 中规定“1.7 是 Stage 1 必经环节”。

仍未验证：

- Stage 1 main 最终采用何种具体 route / handoff 文字调整，由其 owner window 决定。

# Owned task boundary

```yaml
primary_job: sync Stage 1 main current entry and review applicability / routing semantics around 1.7
inputs_or_evidence:
  - 01_structure_preparation/SKILL.md
  - 01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md
  - 00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
results_or_handoff:
  - Stage 1 main lists 1.7 as current active Skill
  - Stage 1 main wording aligned with dynamic task planning ownership
write_paths:
  - 01_structure_preparation/SKILL.md
shared_files_read_only:
  - 00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md
  - 00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
```

# Cross-Skill interface

```yaml
consumes_from_other_skills:
  - 1.7 object requirement: current valid heavy-atom structure once Stage 1 has decided to execute 1.7
provides_to_other_skills:
  - Stage 1 decides whether 1.7 is present in the current task route and which current structure is handed to it
external_rules_referenced:
  - Stage 1 dynamic task planning semantics
```

# Cross-Skill findings

```text
owner_skill: 01_structure_preparation/SKILL.md
issue: Stage 1 still lists 1.7 as freeze-only even though the active Skill has now been generated.
why_it_matters: Stage main should expose the current runtime entry and must not direct runtime use back to the architecture freeze.
suggested_change: Replace the freeze-only 1.7 entry with current: 1.7_protein_protonation_assignment/SKILL.md.
```

```text
owner_skill: 01_structure_preparation/SKILL.md
issue: Stage 1 should not encode 1.7 as a mandatory step or 1.6 as a mandatory direct predecessor of 1.7.
why_it_matters: Applicability and task-route planning belong to Stage 1. Keeping a strong 1.6 → 1.7 implication would conflict with the existing dynamic-plan rule and would incorrectly push Stage-level routing ownership into 1.7.
suggested_change: During the next Stage 1 main review, make explicit that 1.7 is optional according to task need and may consume the current valid heavy-atom structure selected by the Stage 1 route; do not require 1.6 to have executed solely to enter 1.7.
```

# Done when

- Stage 1 main lists `1.7_protein_protonation_assignment/SKILL.md` as the current 1.7 entry rather than freeze-only.
- Stage 1 main no longer implies that 1.7 is mandatory.
- Stage 1 main no longer implies that 1.6 is an unconditional direct prerequisite for 1.7.
- Stage 1 still owns applicability / route selection, while 1.7 only owns its execution object requirements after it has been selected.

# Handoff

本文件保持 `BACKLOG`，直到负责 Stage 1 main 的窗口完成检查和修改。当前 1.7 authoring 窗口不落地修改 Stage 1 main。

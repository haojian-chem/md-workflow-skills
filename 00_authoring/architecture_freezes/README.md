# Architecture freeze records

Status: CURRENT AUTHORING REFERENCE DIRECTORY

本目录只保存**仍承担 current authoring authority** 的 architecture-freeze records。

规则：

- freeze 用于保存已经敲定、但尚未被 current Skill / reference 完整接管的 Stage / Step 架构、职责边界和 implementation-ready 设计；
- freeze 不是 runtime Skill，不能作为 `SKILL.md` 直接执行；
- 当 current Skill / reference 已完整接管仍有效规则后，对应 freeze 不再继续作为平行 authoring specification，移入 `00_authoring/archive/`；
- 被更新设计取代、或只剩历史追溯价值的 freeze 同样退出 active path；
- archive 中的 freeze 不是 current authority，普通 authoring、Manager 和 Task Execution Agent 不默认读取；
- current implementation status 与 current entry 由 `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 维护。

## Current freeze records

当前 active freeze 仅保留仍有 current authoring 用途的 Stage 5 记录：

```text
WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md
```

Stage 5 的 current runtime authority 仍为：

```text
05_analysis/SKILL.md
05_analysis/references/analysis_capability_inventory.yaml
以及 inventory 中实际存在的 capability entries
```

freeze 只承担尚未由 current runtime package 完整吸收的 authoring / architecture 信息，不覆盖 current Skill。

## Archived Stage 1–4 freezes

Stage 1–4 已生成的 current Skills / references 已接管其有效执行规则，因此对应 freeze 已退出 active path：

```text
00_authoring/archive/stage1_history/
00_authoring/archive/stage2_history/
00_authoring/archive/stage3_history/
00_authoring/archive/stage4_history/
```

其中：

- Stage 1 current runtime authority 为 `01_structure_preparation/` 下的 current Skills 与 `references/atom_mapping_rules.md`；
- Stage 2 current runtime authority 为 `02_topology_preparation/2.1_*`–`2.6_*` current Skills 及其 references；当前不设置 Stage 2 main Skill；
- Stage 3 current runtime authority 为 `03_md_preparation/SKILL.md` 及其 references；
- Stage 4 current runtime authority 为 `04_md_simulation/SKILL.md`、4.1–4.3 current Skills 及其 references。

历史 freeze 仅用于追溯旧设计，不得推翻 current runtime / authoring authority。

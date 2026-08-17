# Architecture freeze records

Status: CURRENT AUTHORING REFERENCE DIRECTORY

本目录集中保存已经敲定的 Stage / Workflow / Step architecture-freeze records。

规则：

- current architecture-freeze Markdown 统一放在本目录；
- 根目录 `00_authoring/` 不再散放 freeze 文件；
- freeze 保存已经敲定的架构、职责边界、关键科学/技术规则、明确拒绝项，以及在正式 Skill 尚未生成时用于后续 Skill generation 的 implementation-ready 细节；
- **freeze 完成不等于已经许可生成或启用 Skill**；只有用户明确批准生成后，才进入 active `SKILL.md`；
- 当目标 Step 尚无 current Skill 时，step-level freeze 可以保留足够详细的 generation reference，避免已经敲定的信息在后续转写时丢失；
- 当正式 current Skill 已生成后，可变的具体执行细节由对应 current `SKILL.md` / references 拥有，freeze 不再维护一套平行的 mutable specification；
- freeze 不是 archive；它属于 current authoring authority，用于架构追溯、边界确认和后续 Skill generation；
- 被新的 freeze record 明确取代的旧 Markdown 移入 `00_authoring/archive/`，不继续留在 active path。

部分 step-level freeze 文件是从此前未经授权物化的 guide 文本**原样迁入**。其中可能保留 YAML frontmatter、`Skill` 等历史措辞；这些内容因位于 `architecture_freezes/` 且不命名为 `SKILL.md`，只具有 authoring-reference 身份，不是 runtime Skill。

当前冻结记录：

```text
WORKFLOW1_STAGE1_1.6_STRUCTURE_COMPLETION_FREEZE.md
WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md
WORKFLOW1_STAGE1_1.8_REORDER_MAPPING_FREEZE.md
WORKFLOW1_STAGE1_1.9_VALIDATION_FREEZE.md

WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md

WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
WORKFLOW3_STAGE3_3.1_PERIODIC_BOX_CONSTRUCTION_FREEZE.md
WORKFLOW3_STAGE3_3.2_SOLVENT_ADDITION_FREEZE.md
WORKFLOW3_STAGE3_3.3_ION_ADDITION_FREEZE.md

WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md

WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
WORKFLOW5_STAGE5_5.1_ANALYSIS_PLANNING_ORCHESTRATION_FREEZE.md
WORKFLOW5_STAGE5_ANALYSIS_TOOL_INVENTORY_FREEZE.md
```

当前实现状态由 `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 维护。目录或 freeze 文件存在本身不代表对应 Skill 已生成。

Stage 2 的 stage-level freeze 中仍可能保留早期 `02_operations/...` 路径文字；2.5 后续正式生成时，应以本目录中三个 `WORKFLOW2_STAGE2_2.5_*_FREEZE.md` 文件作为详细 2.5 generation input，不再追随旧 role-based 路径。

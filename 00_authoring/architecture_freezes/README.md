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
WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md
WORKFLOW1_STAGE1_1.2_TOPOLOGY_LINKED_CHECK_FREEZE.md
WORKFLOW1_STAGE1_1.6_STRUCTURE_COMPLETION_FREEZE.md
WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md
WORKFLOW1_STAGE1_1.8_REORDER_MAPPING_FREEZE.md
WORKFLOW1_STAGE1_1.9_VALIDATION_FREEZE.md

WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md
WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md
WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md

WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
WORKFLOW3_STAGE3_3.1_PERIODIC_BOX_CONSTRUCTION_FREEZE.md
WORKFLOW3_STAGE3_3.2_SOLVENT_ADDITION_FREEZE.md
WORKFLOW3_STAGE3_3.3_ION_ADDITION_FREEZE.md

WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md

WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md
```

当前实现状态由 `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 维护。目录或 freeze 文件存在本身不代表对应 Skill 已生成。

Stage 1 原子映射维护统一冻结于 `WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md`，runtime authority 为 `references/atom_mapping_rules.md`。当前 1.3、1.4、1.6、1.7、1.8 在实际结构改写时读取该共享规则，1.9 用其验证 Stage 1 final atom map；1.5 不修改结构，不引用该规则。该 freeze 不定义 Stage 2 atom mapping / provenance。

Stage 1.2 的 `topology-linked` 检查与正式记录规则已专项冻结于 `WORKFLOW1_STAGE1_1.2_TOPOLOGY_LINKED_CHECK_FREEZE.md`，并已同步到 current 1.2 `SKILL.md` / references / schema；该 freeze 保留为 authoring/architecture record，不取代 current runtime `SKILL.md`。

Stage 2 的阶段级架构 authority 为 `WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`。当前该 freeze 已明确：Stage 2 未来设置 `02_topology_preparation/SKILL.md` 作为阶段级 main Skill，负责 Stage 2 内部科研编排与共享接口；`2.1 Topology preparation setup` 保持完整独立 Step，current active entry 为 `02_topology_preparation/2.1_topology_preparation_setup/SKILL.md`；Stage 2 main Skill 与 2.2–2.6 当前仍为 freeze-only。

Stage 2 的 2.3 环节结构、量化计算主线、正式结果记录和向 2.5 交付的信息记录于 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md`；建立参数化模型、几何优化固定原子、电荷拟合和 Sobtop 参数化的详细科学/技术规则分别记录于 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md`、`WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md`、`WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md` 和 `WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md`。

Stage 2 的 2.5 详细 generation input 已统一迁至上述三个 `WORKFLOW2_STAGE2_2.5_*_FREEZE.md`；后续正式生成 2.5 时不再追随旧 role-based `02_operations/...` 路径。2.5 只消费 2.3 已完成的电荷拟合结果和 `charge_modification_scope`；RESP / RESP2 的电荷拟合科学规则由 2.3 专项 freeze 拥有。

Stage 5 的 analysis planning and orchestration 已由 `WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md` 直接作为 Stage-level architecture 拥有；旧 `5.1` freeze 已退出 current path 并归档。Stage 5 analysis inventory 当前统一使用 capability 语义；旧 `ANALYSIS_TOOL_INVENTORY_FREEZE` 已归档。
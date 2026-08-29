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
WORKFLOW2_STAGE2_2.2_STANDARD_RESIDUE_TOPOLOGY_GENERATION_FREEZE.md
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md
WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md
WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.5_CURRENT_DESIGN_FREEZE.md
WORKFLOW2_STAGE2_2.6_TOPOLOGY_VALIDATION_FREEZE.md

WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
WORKFLOW3_STAGE3_3.1_PERIODIC_BOX_CONSTRUCTION_FREEZE.md
WORKFLOW3_STAGE3_3.2_SOLVENT_ADDITION_FREEZE.md
WORKFLOW3_STAGE3_3.3_ION_ADDITION_FREEZE.md

WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md

WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md
```

当前实现状态由 `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 维护。目录或 freeze 文件存在本身不代表对应 Skill 已生成。

Stage 1 原子映射维护统一冻结于 `WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md`。当前 runtime authority 为 `references/atom_mapping_rules.md`：1.3、1.4、1.6、1.7、1.8 在实际结构改写时读取该共享规则，1.9 用其验证 Stage 1 final atom map；2.2 也沿用该共享规则维护标准残基全原子结构的 map，并使用 `2.2ADD` 记录新增 atom。Stage 1 freeze 本身仍只记录 Stage 1 architecture，不作为 Stage 2 规则来源。

Stage 1.2 的 `topology-linked` 检查与正式记录规则已专项冻结于 `WORKFLOW1_STAGE1_1.2_TOPOLOGY_LINKED_CHECK_FREEZE.md`，并已同步到 current 1.2 `SKILL.md` / references / schema；该 freeze 保留为 authoring/architecture record，不取代 current runtime `SKILL.md`。

Stage 2 的阶段级架构 authority 为 `WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`。当前该 freeze 仍只作为尚未被其它 current freeze / active Skill 取代的 Stage-level architecture authority。当前 2.1–2.5 已生成 active Skill；Stage 2 main Skill 与 2.6 尚未生成 active Skill。

**2.6 Topology validation 的 current generation authority 唯一为 `WORKFLOW2_STAGE2_2.6_TOPOLOGY_VALIDATION_FREEZE.md`。** `WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md` 中与 2.6 的具体依赖、检查内容、结果记录和 GROMACS preprocessing 有关的旧文本已经被该 dedicated freeze 取代，后续 2.6 Skill generation 不得从旧综合冻结恢复这些规则。只有需要 Stage-level architecture 时才读取旧综合冻结中仍未被 current authority 取代的 Stage-level 内容。

2.2 current runtime entry 为 `02_topology_preparation/2.2_standard_residue_topology_generation/SKILL.md`，详细正式结果接口由其 `references/results.md` 拥有，原子映射规则读取仓库级 `references/atom_mapping_rules.md`。`WORKFLOW2_STAGE2_2.2_STANDARD_RESIDUE_TOPOLOGY_GENERATION_FREEZE.md` 保留为 generation 前已确认内容的 authoring / architecture record，不再维护平行 runtime specification。

Stage 2 的 2.3 环节结构、量化计算主线、正式结果记录和向 2.5 交付的信息记录于 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md`；建立参数化模型、几何优化固定原子、电荷拟合和 Sobtop 参数化的详细科学/技术规则分别记录于 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md`、`WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md`、`WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md` 和 `WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md`。

Stage 2 的 topology integration and assembly 当前 authoring authority 统一为 `WORKFLOW2_STAGE2_2.5_CURRENT_DESIGN_FREEZE.md`。本轮讨论确认的内容持续写入该文件，并在最终生成对应 `SKILL.md` / local references 时以该文件为当前设计来源。既有 `WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md`、`WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md` 与 `WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md` 仅作为历史设计参考；其中内容不自动继承，只有经本轮重新确认并写入 current design freeze 后才具有当前生成 authority。

Stage 5 的 analysis planning and orchestration 已由 `WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md` 直接作为 Stage-level architecture 拥有；旧 `5.1` freeze 已退出 current path并归档。Stage 5 analysis inventory 当前统一使用 capability 语义；旧 `ANALYSIS_TOOL_INVENTORY_FREEZE` 已归档。
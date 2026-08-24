# MD Workflow Master Plan

Status: ACTIVE CURRENT BASELINE

本文件只保存 MD Workflow 的顶层阶段编号、Stage catalog、当前建设状态和 current authority 入口。具体科学规则、执行规则、validation 和文件生命周期由对应 current `SKILL.md` / references 或 architecture freeze 拥有。

## 1. Top-level numbering

固定顶层阶段：

1. Structure preparation
2. Topology / parameterization
3. System construction / solvation
4. MD simulation
5. Analysis

编号语义：`1.3` 表示整个 MD Workflow 的第 1.3 阶段；`2.4`、`3.2`、`4.1` 同理。Stage 5 当前没有编号化 sub-stage，因此不存在 current `5.1` catalog identity。

## 2. Scientific Stage roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

只有这些 `01`–`05` 目录表示 MD Workflow Stage。Stage / Step 目录可以在对应 Skill 正式生成前预留；**目录存在不等于 Skill 已生成或已激活**。

`references/`、`evals/`、`tools/`、`legacy/` 等基础设施目录不占用 Stage 编号。

## 3. Stage 1 — Structure preparation

Status: ACTIVE SKILL GENERATION COMPLETED.

```text
1.1 Structure source recognition
1.2 Component and residue classification
1.3 Chain and residue selection
1.4 Alternate conformation / occupancy resolution
1.5 Completeness check
1.6 Structure completion
1.7 Protein protonation assignment
1.8 Reorder and mapping
1.9 Structure preparation validation
```

Current implementation status:

```text
1.1      active Skill completed
1.2      active Skill regenerated; model-scoped hierarchical v3 result active; residue check short-circuit, covalent-connection / metal-coordination result recording, and relation-driven final topology_class/component update restored; reference_manifest and selection_identity helper retired; current entry: 01_structure_preparation/1.2_component_and_residue_classification/SKILL.md
1.3–1.4 active Skills completed
1.5      active Skill generated; interface synchronized to current 1.2 hierarchical result and direct reference evidence
1.6      active Skill generated; post-generation authoring/interface consistency check completed; current entry: 01_structure_preparation/1.6_structure_completion/SKILL.md
1.7      active Skill generated; post-generation authoring/interface consistency check completed; current entry: 01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md
1.8      active Skill generated; post-generation authoring/interface consistency check completed; current entry: 01_structure_preparation/1.8_reorder_and_mapping/SKILL.md
1.9      active Skill generated; post-generation authoring/interface consistency check completed; current entry: 01_structure_preparation/1.9_validation/SKILL.md
```

Stage 1.6 architecture freeze remains the authoring/architecture record:

```text
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.6_STRUCTURE_COMPLETION_FREEZE.md
```

Stage 1.7–1.9 architecture records:

```text
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.8_REORDER_MAPPING_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.9_VALIDATION_FREEZE.md
```

1.7、1.8 与 1.9 均已获用户明确批准并生成 active Skills；当前 runtime 细节由对应 current `SKILL.md` 拥有，architecture freeze 保留为 authoring/architecture record。

## 4. Stage 2 — Topology / parameterization

Status: ARCHITECTURE FROZEN; **2.1 ACTIVE; STAGE MAIN AND 2.2–2.6 FREEZE-ONLY**.

Stage 2 架构包括一个阶段级 main Skill 和六个编号科研 Step。未来阶段级 runtime entry 固定为：

`02_topology_preparation/SKILL.md`

Stage 2 main Skill 的架构已经冻结，但尚未生成 active 文件。它负责 Stage 2 内部科研编排、2.1 完成后的后续 Task Sheet 状态维护、2.5 输入就绪条件、2.6 失败后的 Stage 2 计划调整，以及 Stage 2 共享接口定义；不吸收或重复 2.1–2.6 的具体科研职责。

`2.1 Topology preparation setup` 保持完整独立科研 Step；current entry 为：

`02_topology_preparation/2.1_topology_preparation_setup/SKILL.md`

```text
2.1 Topology preparation setup
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

Current / reserved Step directories:

```text
02_topology_preparation/2.1_topology_preparation_setup/                         # active
02_topology_preparation/2.2_standard_residue_topology_generation/              # reserved
02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/      # reserved
02_topology_preparation/2.4_independent_nonstandard_parameterization/          # reserved
02_topology_preparation/2.5_topology_integration_and_assembly/                  # reserved
02_topology_preparation/2.6_topology_validation/                               # reserved
```

当前 2.1 已生成 active Skill，并完成 post-generation authoring/interface consistency check；Stage 2 main Skill 与 2.2–2.6 尚未生成 active `SKILL.md`。

Stage-level architecture authority:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

2.3 has detailed frozen parameterization-model material, but is still freeze-only:

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md
```

2.5 has detailed frozen generation material, but is still freeze-only:

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md
```

These files preserve the detailed pre-authorization 2.3 / 2.5 material for later formal Skill generation; they are not runtime Skills.

## 5. Stage 3 — System construction / solvation

Status: ARCHITECTURE FROZEN; **NO ACTIVE SKILL GENERATION APPROVED YET**.

```text
3.1 Periodic box construction
3.2 Solvent addition
3.3 Ion addition
```

Reserved Step directories:

```text
03_md_preparation/3.1_periodic_box_construction/
03_md_preparation/3.2_solvent_addition/
03_md_preparation/3.3_ion_addition/
```

There is currently **no active Stage 3 `SKILL.md`**.

Stage-level architecture authority:

`00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

Detailed frozen Step material:

```text
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_3.1_PERIODIC_BOX_CONSTRUCTION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_3.2_SOLVENT_ADDITION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_3.3_ION_ADDITION_FREEZE.md
```

The exact dedicated minimal `genion.mdp` template and representative execution validation remain implementation-time work after formal Skill generation is approved.

## 6. Stage 4 — MD simulation

Status: ARCHITECTURE FROZEN; ACTIVE SKILL GENERATION COMPLETED.

```text
4.1 Energy minimization
4.2 Equilibration
4.3 Production simulation
```

Current active guides are under `04_md_simulation/`.

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md`

## 7. Stage 5 — Analysis

Status: MAIN SKILL ACTIVE; `trjconv`, `trjcat`, AND `make_ndx` CAPABILITIES ACTIVE; OTHER INITIAL CAPABILITIES PENDING IMPLEMENTATION.

Stage 5 has **no numbered sub-stage**. Analysis planning and orchestration is the responsibility of the Stage 5 main Skill itself rather than a `5.1` wrapper.

Current active entry:

`05_analysis/SKILL.md`

Current active analysis capability inventory:

`05_analysis/references/analysis_capability_inventory.yaml`

The inventory is active and currently contains the generated `trjconv`, `trjcat`, and `make_ndx` capability entries.

Current active capability entries:

```text
trjconv  → 05_analysis/trjconv/SKILL.md
trjcat   → 05_analysis/trjcat/SKILL.md
make_ndx → 05_analysis/make_ndx/SKILL.md
```

Stage-level architecture record:

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

Analysis capability inventory architecture record:

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md`

Initial capability implementation cohort:

```text
trjconv
trjcat
make_ndx
rmsd
rmsf
hbond
rdf
```

`trjconv`, `trjcat`, and `make_ndx` are active. The remaining concrete capability entries are still pending implementation and are not active merely because they are listed here.

## 8. Task execution and infrastructure

Cross-Stage Task Execution shared rules:

`references/task_execution_rules.md`

该文件是 shared reference，不是独立 Skill 或额外执行环节。所有正式科研执行 Skill 通过各自 main `SKILL.md` 显式引用它。

Unnumbered active package:

```text
00_manager/   project task management / initial planning
```

Unnumbered infrastructure:

```text
references/  cross-Skill shared references
evals/       current tests / fixtures / validation evidence / benchmark
tools/       current Lightweight-compatible shared deterministic tools
legacy/      old contracts / runtime / tools / evals / CI workflows
```

Historical design Markdown: `00_authoring/archive/`.

## 9. Current work status

- Stage 1：1.1–1.9 active Skills 已生成；1.2 当前正式结果采用 model-scoped `component_id → residue_id` 层级、三级 residue 检查短路语义和直接 RTP / CCD evidence；共价连接与金属配位检查重新作为正式检查项目记录，确认且产生 topology effect 的关系必须同步反映到最终 residue `topology_class` 与 component membership；`reference_manifest.yaml` 与 `selection_identity.py` 已退出 active 1.2；1.3 / 1.5 直接接口已同步；1.6、1.7、1.8 与 1.9 均已按 current architecture / discussion 正式生成并完成 post-generation authoring/interface consistency check；
- Stage 2：Stage-level main Skill 架构与 2.1–2.6 六个 Step 均已冻结；`2.1 Topology preparation setup` 已生成 active Skill并完成 post-generation authoring/interface consistency check，current entry 为 `02_topology_preparation/2.1_topology_preparation_setup/SKILL.md`；Stage main 与 2.2–2.6 仍为 freeze-only，其中 2.3 参数化模型规则与 2.5 详细方案已有专项 freeze；
- Stage 3：3.1–3.3 环节与目录已确定；architecture freeze 已完成；正式 Stage 3 Skill generation 尚未获批；
- Stage 4：正式 Skill generation 已完成；
- Stage 5：Stage-level main Skill 已正式生成，current entry 为 `05_analysis/SKILL.md`；`trjconv`、`trjcat` 与 `make_ndx` capability 已生成并登记到 active capability inventory，current entries 分别为 `05_analysis/trjconv/SKILL.md`、`05_analysis/trjcat/SKILL.md` 与 `05_analysis/make_ndx/SKILL.md`；`rmsd / rmsf / hbond / rdf` capability entries 仍待后续分别生成；
- Infrastructure：旧 contracts/runtime/tools/evals/CI 已移出 Stage 编号根目录；跨 Skill Task Execution 共用规则集中于 `references/task_execution_rules.md`；后续只按 current interface 逐项重建 `evals/` 和显式 re-activate `tools/`。

## 10. Status maintenance rule

本文件是 Stage / Step 建设状态与 current entry 的唯一 project-level owner。

任何 authoring 工作只要真实改变以下状态，就必须在同一 authoring 流程中同步本文件：

```text
design / discussion
architecture frozen
Skill generation approved / in progress
active Skill generated
validation milestone changed
superseded / retired
```

Skill authoring 窗口不得因为本文件是共享文件而静默跳过状态同步；具体多窗口写入规则见 `00_authoring/references/multi_window_authoring_protocol.md`。

## 11. Ownership rule

```text
具体业务规则 → current Skill / reference
尚未生成 Skill 的已冻结 Step / Stage 规则 → matching architecture freeze
跨 Stage Task Execution 通用规则 → references/task_execution_rules.md
Stage catalog / 建设状态 / current entry → 本 Master Plan
current deterministic tool → tools/
current evaluation → evals/
legacy executable/runtime/test/CI material → legacy/
historical design material → 00_authoring/archive/
```

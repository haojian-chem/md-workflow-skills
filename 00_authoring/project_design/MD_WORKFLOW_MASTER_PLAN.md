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

编号语义：`1.3` 表示整个 MD Workflow 的第 1.3 阶段；`2.4`、`4.1` 同理。Stage 3 与 Stage 5 当前均不设置编号化 sub-stage，因此不存在 current `3.1`–`3.3` 或 `5.1` catalog identity。

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
1.2      active Skill synchronized to topology-linked formal-record v4: unified topology_linked_checks, three-criterion recording, relation_id-only user-decision linkage, and relation-driven final topology_class/component update; current entry: 01_structure_preparation/1.2_component_and_residue_classification/SKILL.md; freeze: 00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.2_TOPOLOGY_LINKED_CHECK_FREEZE.md; direct downstream 1.8 interface has been migrated to the current v4 component/residue/topology_linked_checks contract
1.3–1.4 active Skills completed; synchronized to the Stage 1 chained atom-map contract: 1.3 initializes each target map and 1.4 copies/updates it during alternate-conformation resolution
1.5      active Skill generated; interface synchronized to current 1.2 hierarchical result and direct reference evidence; does not modify structure and does not maintain atom map
1.6      active Skill generated; post-generation authoring/interface consistency check completed; chained atom-map maintenance synchronized, including provenance-preserving 1.6REPLACE versus true 1.6ADD; current entry: 01_structure_preparation/1.6_structure_completion/SKILL.md
1.7      active Skill generated; post-generation authoring/interface consistency check completed; chained atom-map copy/update synchronized for protonation residue-name changes; current entry: 01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md
1.8      active Skill generated; interface synchronized to current 1.2 schema v4 and Stage 1 chained atom-map contract; deterministic helper consumes the current input map and writes stage1_final_map.yaml; current entry: 01_structure_preparation/1.8_reorder_and_mapping/SKILL.md
1.9      active Skill generated; synchronized to current 1.2 topology_linked_checks and Stage 1 final-map atom-level/provenance validation; current entry: 01_structure_preparation/1.9_validation/SKILL.md
```

Stage 1.2 topology-linked check / formal-record architecture freeze:

```text
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.2_TOPOLOGY_LINKED_CHECK_FREEZE.md
```

该 freeze 已同步到 current 1.2 implementation，保留为当前 authoring/architecture record；current runtime 规则由 1.2 `SKILL.md`、references 和 schema 拥有。

Stage 1 chained atom-map runtime authority and architecture freeze:

```text
references/atom_mapping_rules.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md
```

当前固定由 1.3 初始化 map，1.4 / 1.6 / 1.7 / 1.8 copy-and-update，1.8 最终写出 `stage1_final_map.yaml`；每个 atom record 持续维护 `current_atom_serial`、`original_atom_serial`、`component_id`、`residue_id` 与累积 `operations`。1.5 不维护 map，1.9 只读验证 final map。`references/atom_mapping_rules.md` 同时作为 2.2 的 runtime map authority；Stage 1 architecture freeze 本身仍只记录 Stage 1 mapping 设计。

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

Status: ARCHITECTURE FROZEN; **2.1–2.6 ACTIVE; STAGE MAIN FREEZE-ONLY**.

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

Current Step directories:

```text
02_topology_preparation/2.1_topology_preparation_setup/                         # active
02_topology_preparation/2.2_standard_residue_topology_generation/              # active
02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/      # active
02_topology_preparation/2.4_independent_nonstandard_parameterization/          # active
02_topology_preparation/2.5_topology_integration_and_assembly/                  # active
02_topology_preparation/2.6_topology_validation/                               # active
```

当前 2.1–2.6 已生成 active Skill；2.1–2.5 已完成此前记录的 post-generation authoring/interface consistency check，2.6 已完成本次静态 authoring/interface consistency check。current entries 分别为：

```text
02_topology_preparation/2.1_topology_preparation_setup/SKILL.md
02_topology_preparation/2.2_standard_residue_topology_generation/SKILL.md
02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/SKILL.md
02_topology_preparation/2.4_independent_nonstandard_parameterization/SKILL.md
02_topology_preparation/2.5_topology_integration_and_assembly/SKILL.md
02_topology_preparation/2.6_topology_validation/SKILL.md
```

Stage 2 main Skill 尚未生成 active `SKILL.md`。

Stage-level architecture authority:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

该 Stage-level freeze 中与 topology validation 的具体依赖、检查内容、结果记录和 GROMACS 预处理有关的旧文本已被 active 2.6 Skill package 取代，不再具有 current execution authority。

2.2 current runtime entry:

`02_topology_preparation/2.2_standard_residue_topology_generation/SKILL.md`

2.2 detailed result interface:

`02_topology_preparation/2.2_standard_residue_topology_generation/references/results.md`

2.2 atom mapping runtime authority:

`references/atom_mapping_rules.md`

2.3 current runtime entry:

`02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/SKILL.md`

2.4 current runtime entry:

`02_topology_preparation/2.4_independent_nonstandard_parameterization/SKILL.md`

2.3 detailed architecture freezes remain current authoring records, including:

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md
```

2.5 current runtime entry:

`02_topology_preparation/2.5_topology_integration_and_assembly/SKILL.md`

2.5 detailed result interface:

`02_topology_preparation/2.5_topology_integration_and_assembly/references/results.md`

2.5 current authoring/architecture record:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_CURRENT_DESIGN_FREEZE.md`

Older 2.5 architecture freeze files remain historical authoring references; current runtime rules are owned by the active 2.5 `SKILL.md` and its local references.

2.6 current runtime entry:

`02_topology_preparation/2.6_topology_validation/SKILL.md`

2.6 detailed result interface and GROMACS preprocessing preset:

```text
02_topology_preparation/2.6_topology_validation/references/results.md
02_topology_preparation/2.6_topology_validation/references/grompp_validation.mdp
```

2.6 implemented architecture record:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.6_TOPOLOGY_VALIDATION_FREEZE.md`

Current execution rules are owned by the active 2.6 `SKILL.md` and its local references; the dedicated architecture record no longer maintains a parallel mutable specification.

## 5. Stage 3 — System construction / solvation

Status: ARCHITECTURE FROZEN; **ACTIVE STAGE-LEVEL SKILL GENERATED; STATIC AUTHORING / INTERFACE CHECK COMPLETED**.

Stage 3 不设置编号化 sub-stage。Current Stage-level runtime entry：

`03_md_preparation/SKILL.md`

该 main Skill 在 Task Sheet 的 Stage 3 条目内规划和维护周期盒构建、溶剂添加和离子添加等内部 operations，并生成固定正式结果入口：

`system_construction_result.yaml`

Detailed result interface 与 dedicated minimal genion preset：

```text
03_md_preparation/references/results.md
03_md_preparation/references/genion.mdp
```

Stage-level implemented architecture record：

`00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

原 `3.1 / 3.2 / 3.3` step-level freezes 已归档到：

`00_authoring/archive/stage3_history/`

原预留 Step directories 已退出 current source layout；current `03_md_preparation/` 已物化为 Stage-level active Skill package。

Dedicated minimal `genion.mdp` 的精确内容已经生成并完成静态检查。代表性 GROMACS `grompp → genion` 实际执行验证仍待后续 validation milestone。

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

Shared atom-mapping runtime reference and Stage 1 architecture freeze:

```text
references/atom_mapping_rules.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md
```

`references/atom_mapping_rules.md` 当前定义 Stage 1 chained atom-map maintenance，并被 2.2 沿用以维护标准残基全原子结构的 map；Stage 1 architecture freeze 仍只记录 Stage 1 mapping 设计。

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

- Stage 1：1.1–1.9 active Skills 已生成；1.2 的 model-scoped `component_id → residue_id` 层级、三级 residue 检查短路语义和直接 RTP / CCD evidence 保持 current；topology-linked 检查与正式记录已同步为 schema v4 的统一 `topology_linked_checks[]`，三类判据完整记录，人工关系决策仅通过 `relation_id` 对应；Stage 1 atom mapping 当前采用 chained map：1.3 初始化，1.4 / 1.6 / 1.7 / 1.8 copy-and-update，记录 `current_atom_serial + original_atom_serial + component_id + residue_id + operations`，1.8 写出 `stage1_final_map.yaml`，1.9 做最终逐原子/provenance验证；1.6 whole-residue / coordinate replacement 已区分 provenance-preserving `1.6REPLACE` 与真正新增的 `1.6ADD`；
- Stage 2：Stage-level main Skill 架构与 2.1–2.6 六个 Step 均已冻结；2.1–2.6 已生成 active Skill，current entries 分别为 `02_topology_preparation/2.1_topology_preparation_setup/SKILL.md`、`02_topology_preparation/2.2_standard_residue_topology_generation/SKILL.md`、`02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/SKILL.md`、`02_topology_preparation/2.4_independent_nonstandard_parameterization/SKILL.md`、`02_topology_preparation/2.5_topology_integration_and_assembly/SKILL.md` 与 `02_topology_preparation/2.6_topology_validation/SKILL.md`；2.5 已同步 `moleculetype` 组织、体系整合 `.gro` / map、`2.5ADD` provenance、`.itp` 整合、参数定义汇总、体系 `.top` 生成与正式结果接口；2.6 已同步独立只读终检、单一 `topology_validation_result.yaml` 接口及 `grompp_validation.mdp`；Stage main 仍为 freeze-only；
- Stage 3：Stage-level main Skill 已正式生成，current entry 为 `03_md_preparation/SKILL.md`；不设置编号化 sub-stage；周期盒构建、溶剂添加和离子添加作为内部 operations 在同一 Task Sheet Stage-level 条目中规划和维护；详细结果接口为 `03_md_preparation/references/results.md`，dedicated minimal preset 为 `03_md_preparation/references/genion.mdp`；静态 authoring / interface consistency check 已完成，代表性 GROMACS `grompp → genion` 实际执行验证仍待后续 validation milestone；
- Stage 4：正式 Skill generation 已完成；
- Stage 5：Stage-level main Skill 已正式生成，current entry 为 `05_analysis/SKILL.md`；`trjconv`、`trjcat` 与 `make_ndx` capability 已生成并登记到 active capability inventory，current entries 分别为 `05_analysis/trjconv/SKILL.md`、`05_analysis/trjcat/SKILL.md` 与 `05_analysis/make_ndx/SKILL.md`；`rmsd / rmsf / hbond / rdf` capability entries 仍待后续分别生成；
- Infrastructure：旧 contracts/runtime/tools/evals/CI 已移出 Stage 编号根目录；跨 Skill Task Execution 共用规则集中于 `references/task_execution_rules.md`；atom mapping runtime authority 为 `references/atom_mapping_rules.md`，当前覆盖 Stage 1 chain 及 2.2 标准残基全原子 map 维护；Stage 1 mapping architecture freeze 保留于 `00_authoring/architecture_freezes/WORKFLOW1_STAGE1_ATOM_MAPPING_MAINTENANCE_FREEZE.md`；后续只按 current interface 逐项重建 `evals/` 和显式 re-activate `tools/`。

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

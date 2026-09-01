# MD Workflow Master Plan

Status: ACTIVE CURRENT BASELINE

本文件只保存 MD Workflow 的顶层阶段编号、Stage catalog、当前建设状态和 current authority 入口。具体科学规则、执行规则、validation 和文件生命周期由对应 current `SKILL.md` / references 或仍处于 current authoring authority 的 architecture freeze 拥有。

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

只有这些 `01`–`05` 目录表示 MD Workflow Stage。Stage / Step 目录可以在对应 Skill 正式生成前预留；目录存在不等于 Skill 已生成或已激活。

`references/`、`evals/`、`tools/`、`legacy/` 等基础设施目录不占用 Stage 编号。

## 3. Stage 1 — Structure preparation

Status: 1.1–1.9 ACTIVE; CURRENT RUNTIME HAS NO STAGE MAIN SKILL.

Current catalog：

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

Current Step entries：

```text
01_structure_preparation/1.1_source_recognition/SKILL.md
01_structure_preparation/1.2_component_and_residue_classification/SKILL.md
01_structure_preparation/1.3_chain_and_residue_selection/SKILL.md
01_structure_preparation/1.4_altloc_occupancy_resolution/SKILL.md
01_structure_preparation/1.5_completeness_check/SKILL.md
01_structure_preparation/1.6_structure_completion/SKILL.md
01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md
01_structure_preparation/1.8_reorder_and_mapping/SKILL.md
01_structure_preparation/1.9_validation/SKILL.md
```

当前 Stage 1 直接由 Task Execution Agent 按 Task Sheet 进入实际 1.x Step；不设置 `01_structure_preparation/SKILL.md` runtime entry。各 Step 自己定义实际输入、处理、validation 与正式结果；跨 Step 共用的 Task Execution 与 atom mapping 规则由 shared references 提供。

Stage 1 的 current atom-mapping runtime authority 为：

`references/atom_mapping_rules.md`

当前由 1.3 初始化 target atom map，1.4 / 1.6 / 1.7 / 1.8 按实际结构修改维护，1.8 写出 `stage1_final_map.yaml`，1.9 对 final map 做只读验证；2.2 也沿用该 shared reference 维护标准残基全原子结构的 map。

已撤回的 Stage 1 main Skill 与既有 architecture freezes 均退出 current path，历史记录位于：

`00_authoring/archive/stage1_history/`

## 4. Stage 2 — Topology / parameterization

Status: 2.1–2.6 ACTIVE; CURRENT RUNTIME HAS NO STAGE MAIN SKILL.

Current catalog：

```text
2.1 Topology preparation setup
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

Current entries：

```text
02_topology_preparation/2.1_topology_preparation_setup/SKILL.md
02_topology_preparation/2.2_standard_residue_topology_generation/SKILL.md
02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/SKILL.md
02_topology_preparation/2.4_independent_nonstandard_parameterization/SKILL.md
02_topology_preparation/2.5_topology_integration_and_assembly/SKILL.md
02_topology_preparation/2.6_topology_validation/SKILL.md
```

当前 Stage 2 直接由 Task Execution Agent 按 Task Sheet 进入实际 2.x Step；不设置 `02_topology_preparation/SKILL.md` runtime entry。

2.1 负责确定当前体系实际使用的力场 / 参数定义来源，并把处理对象落实为 2.2–2.5 Task Sheet 工作项。2.2–2.5 分别拥有自身的具体科学处理、validation 与正式结果。2.6 是独立、只读的 topology validation Skill，不作为 Stage 2 的必需 completion gate；是否进入当前 Task Sheet 由任务范围决定。

Stage 2 当前暂不启用 2.1–2.5 reuse 机制；后续 reuse 作为独立更新计划重新设计，不由旧 freeze 提供 runtime 判据。

Stage 2 既有 Stage-level、2.2、2.3、2.5、2.6 architecture freezes 已被 current Step Skills / references 接管或被当前架构决定取代，历史记录位于：

`00_authoring/archive/stage2_history/`

## 5. Stage 3 — System construction / solvation

Status: ACTIVE STAGE-LEVEL SKILL GENERATED; POST-GENERATION AUTHORING / INTERFACE REVIEW COMPLETED.

Stage 3 不设置编号化 sub-stage。Current runtime entry：

`03_md_preparation/SKILL.md`

该 Skill 直接拥有 Stage 3 的体系构建执行，在同一 stage-level Task Sheet 条目内规划和维护：

```text
periodic_box_construction
solvent_addition
ion_addition
```

并生成固定正式结果入口：

`system_construction_result.yaml`

Detailed result interface 与 ion-addition reference：

```text
03_md_preparation/references/results.md
03_md_preparation/references/genion.mdp
```

Stage 3 旧 step-level freeze 与已实现的 Stage-level architecture freeze 均已退出 current authoring path，历史记录位于：

`00_authoring/archive/stage3_history/`

代表性 GROMACS `grompp → genion` 实际执行验证仍待后续 validation milestone。

## 6. Stage 4 — MD simulation

Status: ACTIVE SKILL GENERATION COMPLETED.

Current Stage-level runtime entry：

`04_md_simulation/SKILL.md`

Current execution-layer entries：

```text
4.1 Energy minimization   → 04_md_simulation/4.1_energy_minimization/SKILL.md
4.2 Equilibration         → 04_md_simulation/4.2_equilibration/SKILL.md
4.3 Production simulation → 04_md_simulation/4.3_production_simulation/SKILL.md
```

Stage 4 main Skill 当前拥有 planned run route、formal run-unit identity、binding / reuse / continuation、project-level `run_unit.yaml` 与 4.1–4.3 execution-layer 调度；具体 run-specific execution 与 validation 由对应 4.x Skill 拥有。

Stage 4 已实现 architecture freeze 已退出 current authoring path，历史记录位于：

`00_authoring/archive/stage4_history/`

## 7. Stage 5 — Analysis

Status: MAIN SKILL ACTIVE; CAPABILITY INVENTORY CONTINUOUSLY MAINTAINED.

Stage 5 不设置编号化 sub-stage。Current Stage-level runtime entry：

`05_analysis/SKILL.md`

Current capability inventory：

`05_analysis/references/analysis_capability_inventory.yaml`

当前已登记 capability entries：

```text
trjconv  → 05_analysis/trjconv/SKILL.md
trjcat   → 05_analysis/trjcat/SKILL.md
make_ndx → 05_analysis/make_ndx/SKILL.md
```

Stage 5 capability inventory 按实际分析需求持续维护，没有固定 completion catalog；未实际生成 entry 的 capability 不作为 active capability。

Stage 5 当前仍保留的 authoring freeze records：

```text
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md
```

## 8. Task execution and infrastructure

Cross-Stage Task Execution shared rules：

`references/task_execution_rules.md`

Shared result-generation rules：

`references/result_generation_rules.md`

Shared canonical terminology：

`references/canonical_terminology.md`

Shared atom-mapping runtime authority：

`references/atom_mapping_rules.md`

Unnumbered active package：

```text
00_manager/   project task management / initial planning
```

Unnumbered infrastructure：

```text
references/  cross-Skill shared references
evals/       current tests / fixtures / validation evidence / benchmark
tools/       current Lightweight-compatible shared deterministic tools
legacy/      old contracts / runtime / tools / evals / CI workflows
```

Historical authoring / architecture Markdown：

`00_authoring/archive/`

## 9. Current work status

- Stage 1：1.1–1.9 active Skills 已生成；当前不设置 Stage main Skill；current atom-map contract 由 `references/atom_mapping_rules.md` 拥有；已撤回的 Stage 1 main Skill 与既有 freezes 已归档。
- Stage 2：2.1–2.6 active Skills 已生成；当前不设置 Stage main Skill；2.6 为可选独立 topology validation；2.1–2.5 reuse 当前停用并留作后续更新；既有 Stage 2 freezes 已归档。
- Stage 3：Stage-level main Skill 已正式生成；不设置编号化 sub-stage；历史 Stage 3 freezes 已归档；代表性实际执行验证仍待后续 milestone。
- Stage 4：Stage-level main Skill 与 4.1–4.3 active Skills 已生成；Stage 4 main 当前拥有 run-unit / route 等 Stage-wide 规则；既有 Stage 4 freeze 已归档。
- Stage 5：Stage-level main Skill 已生成；当前 capability inventory 已登记 `trjconv`、`trjcat`、`make_ndx`，并持续扩展；Stage 5 current authoring freezes 暂保留于 `architecture_freezes/`。
- Infrastructure：跨 Skill Task Execution、result generation、canonical terminology 与 atom mapping 均由对应 current shared references 拥有；后续按 current interface 逐项重建 `evals/` 和显式 re-activate `tools/`。

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

Skill authoring窗口不得因为本文件是共享文件而静默跳过状态同步；具体多窗口写入规则见 `00_authoring/references/multi_window_authoring_protocol.md`。

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

一张 Task Sheet 不要求覆盖完整 Workflow、完整 Stage 或整个科研任务；同一科研任务可以由多张 Task Sheet 共同承载。局部 Task Sheet 可以消费前序 Task Sheet 已经形成且仍适用的 prerequisite、正式结果和决策。

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

力场、参数定义来源等会被多个环节消费的科学信息，在当前 Skill 真正需要时从 Task Sheet、前序 Task Sheet、正式记录 / 日志、当前上下文和用户决定中确认；信息已经明确时直接使用，仍不明确时由当前需要该信息的 Skill 触发用户确认。后续实际需要时允许再次核对。

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

当前 Stage 2 不设置 `02_topology_preparation/SKILL.md` runtime entry。

2.1 是 2.2–2.5 的 topology-preparation setup prerequisite。它负责：

- 确认并记录当前拆分方案采用的力场及其它参数定义来源；
- 拆分标准残基、topology-linked 非标准、独立非标准以及 solvent / ion 的处理对象；
- 确定 2.3 的联合参数化分组；
- 确定 2.5 需要汇合的前置输入集合。

2.2–2.5 开始前必须已经存在一个适用于当前体系、处理范围和参数定义基础的已完成 2.1 方案。该方案可以位于当前 Task Sheet，也可以位于同一科研任务的前序 Task Sheet；因此不要求每张后续 Task Sheet 都机械重复 2.1，但不能绕过 2.1 本身。

力场及其它参数定义来源可以在多个真正需要它们的环节被确认或再次核对；2.1 的特有职责是把当前 topology-preparation **拆分方案采用的来源**与对象拆分一起闭合。后续确认若改变了拆分方案基础，应先更新 / 重新形成适用的 2.1 方案。

2.2–2.5 分别拥有自身具体科学处理与必要检查。2.6 是独立、只读的 topology validation Skill，不作为 Stage 2 的必需 completion gate；是否执行由对应 Task Sheet 的实际范围决定。

Stage 2 当前暂不启用 2.1–2.5 reuse 机制；后续 reuse 作为独立更新计划重新设计。2.2–2.4 current main Skills 与 active references 已清理旧 reuse 执行分支。

Stage 2 既有 architecture freezes 已退出 Stage 2 current runtime path，历史记录位于：

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

Stage 3 保持轻量体系构建职责。当前操作主要由 GROMACS 组件完成，检查范围按 current Skill 已定义的操作成功、关键输出和必要一致性检查执行，不为同一职责重复增加重型检查。

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

Stage 4 本地计算资源与运行方式的用户倾向统一维护于：

`04_md_simulation/references/execution_preferences.md`

该 reference 对每项倾向明确适用 run class：`-nt 12` 适用于 EM/NVT/NPT/production；foreground 与短 `-maxh 0.08` 仅为 EM 倾向；`tmux`、`-update gpu`、`-pin on` 默认适用于 NVT/NPT/production，并受当前运行环境约束。

项目首次进入 Stage 4 且 `04_md_simulation/run_unit.yaml` 尚不存在时，由 Stage 4 main 在第一次实例化 formal run unit 前初始化为空 list。

Stage 4 已实现 architecture freeze 已退出 current authoring path，历史记录位于：

`00_authoring/archive/stage4_history/`

## 7. Stage 5 — Analysis

Status: IN PROGRESS / NOT COMPLETED; MAIN SKILL ACTIVE; CAPABILITY IMPLEMENTATION CONTINUES.

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

Stage 5 main runtime architecture 已经可用，但 Stage 5 整体 authoring / capability implementation 仍未完成。Capability inventory 按实际分析需求持续维护；未实际生成 entry 的 capability 不作为 active capability，也不因为当前 main Skill 已生成就把整个 Stage 5 标记为完成。

Stage 5 当前仍保留 current authoring freeze records：

```text
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md
```

这些 freeze 暂不归档：已实现部分以 current `05_analysis/` runtime package 为准；freeze 继续保存尚未被 current runtime package 完整接管的 Stage 5 authoring / architecture baseline。

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
00_manager/   project Task Sheet management / initial planning
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

- Stage 1：1.1–1.9 active Skills 已生成；当前不设置 Stage main Skill；Task Sheet 可以只覆盖局部 Step，但真实 prerequisite 必须已经满足；current atom-map contract 由 `references/atom_mapping_rules.md` 拥有；已撤回的 Stage 1 main Skill 与既有 freezes 已归档。
- Stage 2：2.1–2.6 active Skills 已生成；当前不设置 Stage main Skill；2.1 是 2.2–2.5 的拆分 / setup prerequisite，可由前序 Task Sheet 提供而不必在每张后续 Task Sheet 重复；2.6 为可选独立 topology validation；2.1–2.5 reuse 当前停用并留作后续更新；既有 Stage 2 freezes 已归档。
- Stage 3：Stage-level main Skill 已正式生成；不设置编号化 sub-stage；保持轻量 GROMACS system-construction 职责；历史 Stage 3 freezes 已归档；代表性实际执行验证仍待后续 milestone。
- Stage 4：Stage-level main Skill 与 4.1–4.3 active Skills 已生成；Stage 4 main 当前拥有 run-unit / route 等 Stage-wide 规则；本地执行倾向集中到 `references/execution_preferences.md` 并按 run class 明确适用范围；`run_unit.yaml` 首次初始化规则已明确；既有 Stage 4 freeze 已归档。
- Stage 5：**整体未完成 / 持续建设中**；Stage-level main Skill 已生成；当前 capability inventory 已登记 `trjconv`、`trjcat`、`make_ndx`；Stage 5 current authoring freezes 继续保留于 `architecture_freezes/`，不因部分 runtime 已实现而归档。
- Infrastructure：跨 Skill Task Execution、result generation、canonical terminology 与 atom mapping 均由对应 current shared references 拥有；Task Execution 已统一普通任务项状态为 `未完成 / 已完成 / 已终止`，并明确区分科研任务与 Task Sheet；后续按 current interface 逐项重建 `evals/` 和显式 re-activate `tools/`。

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

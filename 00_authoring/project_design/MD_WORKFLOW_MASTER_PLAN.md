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

`evals/`、`tools/`、`legacy/` 等基础设施目录不占用 Stage 编号。

## 3. Stage 1 — Structure preparation

Status: PARTIALLY IMPLEMENTED.

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
1.1–1.4  active Skills completed
1.5      active Skill generated; authoring/interface review completed
1.6      active Skill generated; current entry: 01_structure_preparation/1.6_structure_completion/SKILL.md
1.7–1.9  architecture frozen; no active Skill yet
```

Stage 1.6 architecture freeze remains the authoring/architecture record:

```text
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.6_STRUCTURE_COMPLETION_FREEZE.md
```

Stage 1.7–1.9 freeze records:

```text
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.8_REORDER_MAPPING_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.9_VALIDATION_FREEZE.md
```

Freeze completion does not authorize runtime use or Skill generation. Formal 1.7–1.9 `SKILL.md` files are created only after explicit user approval. Their Stage/Step directories remain reserved in the scientific tree.

## 4. Stage 2 — Topology / parameterization

Status: ARCHITECTURE FROZEN; **NO ACTIVE SKILL GENERATION APPROVED YET**.

```text
2.1 Parameterization environment and assignment
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

Reserved Step directories:

```text
02_topology_preparation/2.1_parameterization_environment_and_assignment/
02_topology_preparation/2.2_standard_residue_topology_generation/
02_topology_preparation/2.3_topology_linked_nonstandard_parameterization/
02_topology_preparation/2.4_independent_nonstandard_parameterization/
02_topology_preparation/2.5_topology_integration_and_assembly/
02_topology_preparation/2.6_topology_validation/
```

There is currently **no active Stage 2 `SKILL.md`**. The directories are reserved package locations only.

Stage-level architecture authority:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

2.5 has detailed frozen generation material, but is still freeze-only:

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md
```

These files preserve the detailed pre-authorization 2.5 material for later formal Skill generation; they are not runtime Skills.

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

Status: ARCHITECTURE FROZEN; **NO ACTIVE SKILL GENERATION APPROVED YET**.

Stage 5 has **no numbered sub-stage**. Analysis planning and orchestration is the responsibility of the Stage 5 main Skill itself rather than a `5.1` wrapper.

Reserved Stage root:

`05_analysis/`

Future active entry after explicit generation approval:

`05_analysis/SKILL.md`

There is currently **no active Stage 5 `SKILL.md`** and no active analysis capability inventory.

Stage-level architecture authority:

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

Frozen analysis capability inventory design:

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md`

Future active inventory path after explicit Stage 5 Skill generation approval:

`05_analysis/references/analysis_capability_inventory.yaml`

Concrete analysis-capability Skills/Tools remain future implementation work after explicit approval.

## 8. Runtime and infrastructure

Cross-Stage runtime authority: `00_authoring/project_design/lightweight_runtime_v2_spec.md`

Unnumbered infrastructure:

```text
evals/   current tests / fixtures / validation evidence / benchmark
tools/   current Lightweight-compatible shared deterministic tools
legacy/  old contracts / runtime / tools / evals / CI workflows
```

Historical design Markdown: `00_authoring/archive/`.

## 9. Current work status

- Stage 1：1.1–1.6 active Skills 已完成；其中 1.5 已完成正式生成与 authoring/interface review，1.6 已按 current architecture freeze 正式生成；1.7–1.9 已冻结、目录保留，但尚未获批生成 active Skills；
- Stage 2：2.1–2.6 环节与目录已确定；architecture freeze 已完成；2.5 详细方案也只属于 freeze；正式 Stage 2 Skill generation 尚未获批；
- Stage 3：3.1–3.3 环节与目录已确定；architecture freeze 已完成；正式 Stage 3 Skill generation 尚未获批；
- Stage 4：正式 Skill generation 已完成；
- Stage 5：Stage-level analysis planning/orchestration architecture 已冻结；不设置 `5.1`；plan item 与 inventory 统一使用 capability 语义；未来 active entry 为 `05_analysis/SKILL.md`，当前正式 Stage 5 / analysis capability Skill generation 尚未获批；
- Infrastructure：旧 contracts/runtime/tools/evals/CI 已移出 Stage 编号根目录；后续只按 current interface 逐项重建 `evals/` 和显式 re-activate `tools/`。

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
跨 Stage runtime → lightweight_runtime_v2_spec.md
Stage catalog / 建设状态 / current entry → 本 Master Plan
current deterministic tool → tools/
current evaluation → evals/
legacy executable/runtime/test/CI material → legacy/
historical design material → 00_authoring/archive/
```

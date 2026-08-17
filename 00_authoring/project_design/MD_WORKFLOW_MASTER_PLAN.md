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

编号语义：`1.3` 表示整个 MD Workflow 的第 1.3 阶段；`2.4`、`3.2`、`4.1`、`5.1` 同理。

## 2. Scientific Stage roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

只有这些 `01`–`05` 目录表示 MD Workflow Stage。目录可以在对应 Skill 正式生成前预留；**目录存在不等于 Skill 已生成或已激活**。

`evals/`、`tools/`、`legacy/` 等基础设施目录不占用 Stage 编号。

## 3. Stage 1 — Structure preparation

Status: PARTIALLY IMPLEMENTED.

```text
1.1 Structure source recognition
1.2 Component and residue classification
1.3 Chain and residue selection
1.4 Alternate conformation / occupancy resolution
1.5 Completeness check
1.6 Missing-region completion
1.7 Protein protonation assignment
1.8 Reorder and mapping
1.9 Structure preparation validation
```

Current implementation status:

```text
1.1–1.4  active Skills completed
1.5      under current authoring/discussion in a separate window
1.6–1.9  architecture frozen; no active Skill yet
```

Stage 1.6–1.9 freeze records:

```text
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.6_STRUCTURE_COMPLETION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.7_PROTONATION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.8_REORDER_MAPPING_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW1_STAGE1_1.9_VALIDATION_FREEZE.md
```

Freeze completion does not authorize runtime use or Skill generation. Formal 1.6–1.9 `SKILL.md` files are created only after explicit user approval. Their Stage/Step directories remain reserved in the scientific tree.

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

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

Any Stage 2 `SKILL.md` materialized before explicit approval is authoring reference only, not runtime authority, and must be consolidated into the freeze before pseudo-Skill removal.

## 5. Stage 3 — System construction / solvation

Status: ARCHITECTURE FROZEN; **NO ACTIVE SKILL GENERATION APPROVED YET**.

```text
3.1 Periodic box construction
3.2 Solvent addition
3.3 Ion addition
```

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

The exact dedicated minimal `genion.mdp` template and representative execution validation remain implementation-time work. Any currently materialized Stage 3 `SKILL.md` files are not approved runtime Skills and must first be reconciled with the freeze so no agreed detail is lost.

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

```text
5.1 Analysis planning and orchestration
```

Architecture authority:

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

Any currently materialized Stage 5 main-guide/inventory files are authoring reference only until explicitly approved Skill generation. Agreed details must be preserved in the freeze before those pseudo-current files are removed or repurposed.

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

- Stage 1：1.1–1.4 已完成；1.5 正在独立窗口 authoring；1.6–1.9 已冻结、目录保留，但尚未获批生成 active Skills；
- Stage 2：architecture freeze 已完成；正式 2.x Skill generation 尚未获批；
- Stage 3：architecture freeze 已完成；正式 3.1–3.3 Skill generation 尚未获批；
- Stage 4：正式 Skill generation 已完成；
- Stage 5：architecture freeze 已完成；正式 5.1 / analysis capability Skill generation 尚未获批；
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

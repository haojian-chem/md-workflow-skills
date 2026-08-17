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

## 2. Current scientific Skill roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

只有这些 `01`–`05` 目录表示 MD Workflow Stage。`evals/`、`tools/`、`legacy/` 等基础设施目录不占用 Stage 编号。

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

Freeze completion does not authorize runtime use or Skill generation. Formal 1.6–1.9 `SKILL.md` files are created only after explicit user approval.

## 4. Stage 2 — Topology / parameterization

Status: ARCHITECTURE FROZEN; stage main Skill active; detailed implementation remains partial.

```text
2.1 Parameterization environment and assignment
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

Current entry: `02_topology_preparation/SKILL.md`

Current implemented detailed guide: `02_topology_preparation/2.5_topology_integration_and_assembly/SKILL.md`

Architecture authority: `00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

## 5. Stage 3 — System construction / solvation

Status: ARCHITECTURE FROZEN; first-pass Stage/Step Skills active; exact 3.3 `genion.mdp` template and representative execution validation pending.

```text
3.1 Periodic box construction
3.2 Solvent addition
3.3 Ion addition
```

Current guides:

```text
03_md_preparation/SKILL.md
03_md_preparation/3.1_periodic_box_construction/SKILL.md
03_md_preparation/3.2_solvent_addition/SKILL.md
03_md_preparation/3.3_ion_addition/SKILL.md
```

Architecture authority: `00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`

## 6. Stage 4 — MD simulation

Status: ARCHITECTURE AND FIRST-PASS GUIDES FROZEN; representative execution validation pending.

```text
4.1 Energy minimization
4.2 Equilibration
4.3 Production simulation
```

Current guides under `04_md_simulation/`.

Architecture authority: `00_authoring/architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md`

## 7. Stage 5 — Analysis

Status: ARCHITECTURE AND FIRST-PASS MAIN GUIDE FROZEN; concrete analysis-capability population and representative validation pending.

```text
5.1 Analysis planning and orchestration
```

Current guide: `05_analysis/SKILL.md`

Architecture authority: `00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

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

- Stage 1：1.1–1.4 已完成；1.5 正在独立窗口 authoring；1.6–1.9 已冻结并保留 implementation-ready generation reference，但尚未获批生成 active Skills；
- Stage 2：补齐缺失 2.x Skills / Tools；
- Stage 3：补齐专用 `genion.mdp` 并做代表性执行验证；
- Stage 4：完成 representative planned-run / run-unit validation；
- Stage 5：填充 analysis capability inventory，并设计/验证具体 analysis capabilities；
- Infrastructure：旧 contracts/runtime/tools/evals/CI 已移出 Stage 编号根目录；后续只按 current interface 逐项重建 `evals/` 和显式 re-activate `tools/`。

## 10. Ownership rule

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

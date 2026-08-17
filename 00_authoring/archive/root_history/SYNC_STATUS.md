# Authoring sync status

Status: ARCHIVED / SUPERSEDED

> Historical snapshot. Current project-level stage status is maintained in `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`. Current authoring rules are owned by `00_authoring/SKILL.md` and its references.

## Historical current authoring model

- `00_authoring/SKILL.md` was the new Skill authoring / maintenance window entry.
- New scientific Skills used `main Skill + references + only-when-justified supporting Skill`.
- Workflow / Operation / Validator was no longer a mandatory taxonomy.
- Historical `01_workflows/`, `02_operations/`, `02_validators/` paths were not templates for new Skills.
- Skill was treated as Agent guidance rather than a parser / wrapper / dispatcher gate.
- Multi-window authoring used broad reads with narrow write ownership.
- Stage architecture-freeze records were centralized under `00_authoring/architecture_freezes/`.
- Superseded/Legacy authoring material was moved to `00_authoring/archive/`.

Historical architecture baseline at archival time:

- Lightweight Runtime v2 was the default runtime architecture.
- Stage 1 — Structure preparation: catalog defined; guides existed; representative validation/refinement remained in progress.
- Stage 2 — Topology / parameterization: architecture frozen; implementation partial.
- Stage 3 — System construction / solvation: architecture frozen; detailed implementation pending/refining.
- Stage 4 — MD simulation: architecture and first-pass guides frozen/implemented; representative execution validation pending.
- Stage 5 — Analysis: architecture and first-pass guide frozen/implemented; concrete capability population pending.

Historical Stage architecture records:

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

Historical Stage 4 guides:

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

Historical Stage 5 guide:

```text
05_analysis/SKILL.md
05_analysis/references/analysis_tool_inventory.yaml
```

Historical pending-work snapshot:

- Stage 1 representative guide validation/refinement and gradual physical-layout cleanup.
- Stage 2 missing Skill/Tool implementation.
- Stage 3 Skill/template/validation implementation.
- Stage 4 representative planned-run/run-unit execution validation.
- Stage 5 analysis capability inventory population and concrete `trjconv` / `make_ndx` / analysis Skill design and validation.

This file is history only and must not be used as current authority.

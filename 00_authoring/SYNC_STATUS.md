# Authoring sync status

## Current architecture baseline

- Lightweight Runtime v2 is the default runtime architecture.
- Workflow 1 step catalog is defined.
- **Workflow 2 / Stage 2 architecture is frozen.**
- **Workflow 3 / Stage 3 architecture is frozen.**
- Workflow 4–5 detailed step catalogs remain pending.

## Workflow 2 / Stage 2 freeze

Frozen six-step catalog:

1. `2.1 Parameterization environment and assignment`
2. `2.2 Standard residue topology generation`
3. `2.3 Topology-linked nonstandard parameterization`
4. `2.4 Independent nonstandard parameterization`
5. `2.5 Topology integration and assembly`
6. `2.6 Topology validation`

Authoritative planning/design records:

- `00_authoring/MD_WORKFLOW_MASTER_PLAN.md`
- `00_authoring/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`
- `00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

Current implemented Stage 2 Operation work includes:

- `02_operations/topology_integration_and_assembly/SKILL.md`
- `02_operations/topology_integration_and_assembly/references/topology_integration_rules.md`
- `02_operations/topology_integration_and_assembly/references/parameter_definition_deduplication.md`

Key frozen corrections:

- 2.3 processing unit is a **topology-linked nonstandard unit**, which may contain one or multiple nonstandard residues.
- Workflow 1 owns topo-linked unit chain assignment; 2.5 consumes it and may independently merge covalently connected chains/units into a GROMACS final `moleculetype` without erasing chain identity.
- 2.5 freezes final atom set, final all-atom order, canonical final atom index and `final_system.map` **before** molecule-level topology integration.
- Each final moleculetype `.itp` is a direct output of that topology integration using the canonical final index.
- Consolidated global/type-level parameter definitions are generated after molecule-level integration and before `final_system.top` assembly.

Stage 2 is closed for ordinary architecture redesign. Remaining Stage 2 work is implementation/validation refinement or evidence-driven local correction.

## Workflow 3 / Stage 3 freeze

Frozen three-step catalog:

1. `3.1 Periodic box construction`
2. `3.2 Solvent addition`
3. `3.3 Ion addition`

Default scientific route:

```text
3.1 → 3.2 → 3.3
```

The step IDs express the default scientific order and may appear multiple times as Task Sheet instances when required.

Authoritative planning/design records:

- `00_authoring/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`
- `00_authoring/MD_WORKFLOW_MASTER_PLAN.md`
- `00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

Key frozen Stage 3 rules:

- no separate system-construction-specification, final-assembly, or stage-level-validation step;
- 3.1 current version uses `gmx editconf`; direct Agent modification of coordinates/box vectors is reserved for future enhancement;
- 3.1 arg tendency centers on `-c` and `-box` / `-d`;
- 3.2 uses `gmx solvate`, may appear multiple times, and normally inherits the existing box;
- `sys.top` is the preferred Stage 3 topology basename when naming is under workflow control, but existing validated topology names are preserved;
- 3.3 internally executes `gmx grompp` then `gmx genion` and should ship a dedicated minimal genion `.mdp` template;
- `gmx genion` tends toward `-neutral`; for biomolecular systems with no user-specified salt concentration, it tends toward `-conc 0.154`;
- Stage 3 Skills expose arg tendencies rather than rigid command templates.

Stage 3 is closed for ordinary architecture redesign. Remaining Stage 3 work is Step Skill implementation, template/validation refinement, or evidence-driven local correction.

## Open planning work

- Stage 4 step decomposition.
- Stage 5 step decomposition.
- Stage 2 Steps/Validators/Tools not yet implemented.
- Stage 3 Step Skills/templates/validation details not yet implemented.
- Nucleic-acid-specific 2.3 cut/capping rules when required by implementation.

# Authoring sync status

## Current architecture baseline

- Lightweight Runtime v2 is the default runtime architecture.
- Workflow 1 step catalog is defined.
- **Workflow 1 / Step 1.3 Chain and Residue Selection scientific design is frozen; guide implementation is merged and validation is pending.**
- **Workflow 2 / Stage 2 architecture is frozen.**
- **Workflow 3 / Stage 3 architecture is frozen.**
- **Workflow 4 / Stage 4 architecture, validation ownership and first-pass execution guidance are frozen and implemented; representative validation is pending.**
- Workflow 5 detailed step catalog remains pending.

## Workflow 1 / Step 1.3 freeze

Current default Skill path:

- `02_operations/chain_and_residue_selection/SKILL.md`
- `02_operations/chain_and_residue_selection/references/pdb_materialization_rules.md`
- `02_validators/chain_and_residue_selection_validator/SKILL.md`

Key frozen design:

- 1.3 selects research objects at chain / residue level; PDB generation is materialization of that selection.
- User interaction uses source identity; internal selection records use 1.2 `component_id + residue_id`.
- `selection_index.yaml` records targets; each `targets/target_xxx.yaml` records selection and, after PDB generation, chain/residue mapping.
- Selected missing residues remain part of the research-object selection and reserve target-local resid positions without generating coordinates.
- PDB chain labels derive deterministically from 1.2 `chain_index`; residue ordering follows 1.2 authoritative `residue_records[]` order.
- PDB ATOM/HETATM and TER behavior follows 1.2 `polymer_class`; connectivity records are not regenerated.
- Validator records PASS/FAIL for Selection, Structure content, PDB organization and Mapping.
- Historical `chain_and_component_selection` Operation/Validator remain reference-only and are no longer the default 1.3 path.

Pending:

- validate the revised 1.2 residue-order contract;
- validate 1.3 guidance on representative real structures and missing-residue cases;
- decide from implementation evidence whether PDB materialization warrants a deterministic Tool.

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

## Workflow 4 / Stage 4 freeze

Frozen sub-stage catalog:

1. `4.1 Energy minimization`
2. `4.2 Equilibration`
3. `4.3 Production simulation`

Authoritative planning/design records:

- `00_authoring/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md`
- `00_authoring/MD_WORKFLOW_MASTER_PLAN.md`
- `00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

Current implemented Skill paths:

- `04_md_simulation/SKILL.md`
- `04_md_simulation/4.1_energy_minimization/SKILL.md`
- `04_md_simulation/4.2_equilibration/SKILL.md`
- `04_md_simulation/4.3_production_simulation/SKILL.md`

Key frozen Stage 4 rules:

- Stage 4 uses one physical `04_md_simulation/` hierarchy: parent Stage Skill plus 4.1/4.2/4.3 child Skills; logical workflow/operation responsibilities do not require separate `01_workflows/` and `02_operations/` directories here.
- Stage 4 Task Sheet planning is based on a **planned run route**, not a serialized sub-stage list.
- Stage 4 sub-stages are execution layers; run units are execution objects.
- `4.1` executes `em.*`; `4.2` executes `nvt.* / npt.*`; `4.3` executes `md.*`.
- Planned route entries do not receive formal `em.N / nvt.N / npt.N / md.N` identities until processing begins.
- One planned route entry normally binds one formal run unit; replacement rebinding does not introduce an `attempts` layer.
- At run start, Stage 4 binds a reusable existing run unit, continues a matching unfinished run unit, or instantiates a new run unit.
- One centralized project-level `04_md_simulation/run_unit.yaml` maintains instantiated run units across tasks/conversations.
- `run_unit.yaml` root is directly a list; minimum fields are `run_unit_id`, `start_from_run_unit_id`, `status`, and `path`.
- `path` points to that specific run unit's complete directory, e.g. `/project/04_md_simulation/md.2/`; multiple run-unit directories may share the same Stage 4 parent directory.
- `run_unit_type` is not stored; first-level type comes from the run-unit name and detailed settings come from the real `.mdp`.
- Allowed run-unit maintenance statuses are `未完成 / 已完成 / 已终止`.
- Technical continuation remains the same run unit; a new scientific segment becomes a new run unit.
- `.mdp` generation belongs to 4.1/4.2/4.3 themselves; there is no separate generic MDP-generation sub-stage.
- `grompp` warnings must be inspected; blind `-maxwarn` use is prohibited.
- `gmx_mdrun.sh` is generated only after successful `grompp` and TPR confirmation and contains only the actual mdrun command.
- Run-specific validation is owned directly by 4.1/4.2/4.3; Stage 4 has no separate Validator Skill.
- Common bonded-geometry screening uses `|r-r0| > 0.08 nm` for reference-length bond/constraint terms and `|θ-θ0| > 30°` for reference-angle terms; other fixed/special bonded functions follow their actual geometry definitions.
- Stage 4 registers the path and description of project-level `run_unit.yaml` in `project_result_index.md`, not each run artifact or run directory.
- `simulation_plan.yaml`, historical `expected_route.yaml`, per-run `run_unit.yaml`, `simulation_output_index`, and separate Stage 4 Validators are not part of the default architecture.

Stage 4 is closed for ordinary architecture redesign. Remaining work is representative execution validation and evidence-driven local correction of the implemented guidance.

## Open planning work

- Validate Stage 4 planned-run binding, run-unit maintenance, MDP/grompp/mdrun guidance and run-specific checks on representative cases.
- Stage 5 step decomposition.
- Stage 2 Steps/Validators/Tools not yet implemented.
- Stage 3 Step Skills/templates/validation details not yet implemented.
- Nucleic-acid-specific 2.3 cut/capping rules when required by implementation.

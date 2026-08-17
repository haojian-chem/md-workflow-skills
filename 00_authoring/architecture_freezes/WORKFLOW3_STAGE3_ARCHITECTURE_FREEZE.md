# Workflow 3 / Stage 3 architecture freeze

## 0. Document role

This file records the frozen architecture and current-version execution boundary for MD Workflow Stage 3 — System construction / solvation.

It is a design/implementation handoff record. Future Step Skills may refine command construction, validation details, and templates without reopening the Stage 3 step architecture unless new scientific evidence requires an architecture change.

Status: **FROZEN — NO ACTIVE SKILL GENERATION APPROVED YET**

The reserved scientific package paths are:

```text
03_md_preparation/3.1_periodic_box_construction/
03_md_preparation/3.2_solvent_addition/
03_md_preparation/3.3_ion_addition/
```

Directory existence does not mean an active `SKILL.md` exists.

---

# 1. Frozen Stage 3 catalog

Stage 3 contains three reusable operation types:

1. `3.1 Periodic box construction`
2. `3.2 Solvent addition`
3. `3.3 Ion addition`

Default scientific route:

```text
3.1 Periodic box construction
→ 3.2 Solvent addition
→ 3.3 Ion addition
```

The numbering records the default scientific order; it is not a cardinality constraint.

Each of `3.1`, `3.2`, and `3.3` may appear zero, one, or multiple times as separate Task Sheet substep instances when the current system and task objective require it. The Task Execution Agent may skip, repeat, insert, or reorder future Stage 3 instances according to the existing Task Sheet rules and execution evidence.

Examples of valid task routes include:

```text
3.1 → 3.2 → 3.3
3.1 → 3.2 → 3.2 → 3.3
3.1 → 3.2 → 3.1 → 3.2 → 3.3
3.2 → 3.3
```

Stage 3 does **not** add separate steps for:

- system construction specification;
- final system assembly;
- stage-level system construction validation.

Stage 3 is intentionally lightweight and Task-Sheet-driven. Each actual construction operation performs its own required local checks and hands forward the updated system state.

---

# 2. Shared execution principle

Stage 3 operations primarily wrap GROMACS construction commands.

A Stage 3 substep consumes the currently selected validated coordinate structure and the information needed to keep its associated topology files identifiable across the handoff.

Topology-associated records should identify the actual `.top` and required `.itp` files associated with the current `.gro`. Force-field / parameter include files are not listed separately when they are already expressed through the `.top` / `.itp` include tree.

`sys.top` is the preferred Stage 3 topology basename when naming is under workflow control. An existing validated topology with another basename is not renamed merely to satisfy this tendency.

For GROMACS commands, each future Step Skill should expose an **arg tendency** rather than a rigid command template. Priority is:

```text
explicit user requirement
> current Task Sheet requirement
> actual current object/state
> Step Skill arg tendency
> GROMACS default
```

---

# 3. 3.1 Periodic box construction

## 3.1.1 Processing object

3.1 may process **any validated `.gro` file**. It does not require the input `.gro` to come directly from Stage 2 or from a fixed preceding Stage 3 step.

The 3.1 handoff also records the `.top` / `.itp` files associated with that `.gro` so later steps can preserve the correct topology relationship.

## 3.1.2 Current-version tool boundary

Current implementation design uses only:

```text
gmx editconf
```

Current-version 3.1 does not allow the Agent to directly rewrite `.gro` coordinates or box vectors and does not use custom coordinate-editing scripts as an alternative execution path.

Agent-controlled or deterministic-tool-based complex box modification is a **future enhancement**, not current behavior.

## 3.1.3 Arg tendency

Primary tendencies:

```text
-c
→ normally preferred for box construction / centering

-box
→ use when explicit box dimensions are given

-d
→ use when a system/solute-to-box-boundary distance is given

-box / -d
→ select according to the current task requirement; do not force both as defaults
```

Typical current forms:

```bash
gmx editconf -f input.gro -o output.gro -c -box X Y Z
```

or:

```bash
gmx editconf -f input.gro -o output.gro -c -d D
```

Other `editconf` arguments are added only when the task gives a reason to use them.

## 3.1.4 Result boundary

3.1 changes the coordinate/box file but normally does not change atom composition, atom order, molecule topology, or molecule counts.

Formal handoff therefore records:

- new validated boxed `.gro`;
- inherited association with the existing `.top` / `.itp` files.

The topology files are referenced, not recopied merely for directory symmetry.

---

# 4. 3.2 Solvent addition

## 4.1 Current-version tool

Current implementation design uses:

```text
gmx solvate
```

3.2 adds solvent to the current validated system and updates the topology composition when `-p` is used.

A Task Sheet may contain multiple independent 3.2 instances. A single 3.2 call may also use a solvent coordinate/template containing a mixed-solvent configuration when that is the intended construction method.

## 4.2 Arg tendency

Primary tendencies:

```text
-cp
→ current validated .gro

-cs
→ explicitly selected solvent coordinate/template

-p
→ current associated topology; prefer sys.top when that is the actual/preferred basename

-o
→ new solvated .gro for the current substep
```

Typical form:

```bash
gmx solvate -cp current.gro -cs solvent.gro -p sys.top -o solvated.gro
```

3.2 normally inherits the box already present in the current `.gro`. Box construction/modification is normally handled by 3.1 rather than by using 3.2 as a substitute for 3.1.

Arguments such as `-scale`, `-radius`, `-shell`, or `-maxsol` are not automatic tendencies; use them only when required by the task.

## 4.3 Result boundary

3.2 normally produces:

- new solvated `.gro`;
- updated current `.top` / `sys.top` composition;
- continued references to required `.itp` files.

The Step performs lightweight consistency checks sufficient to confirm that the solvent addition succeeded and that coordinate composition and topology molecule counts remain aligned.

---

# 5. 3.3 Ion addition

## 5.1 Internal execution structure

3.3 is one Workflow Step with two internal GROMACS command stages:

```text
Skill-provided genion MDP template
↓
gmx grompp
↓
genion.tpr
↓
gmx genion
↓
ionized .gro + updated topology
```

The `.tpr` is an intermediate execution file for the current 3.3 instance. The principal handoff result is the ionized coordinate/topology state.

Each repeated 3.3 instance reruns `grompp` against its own current `.gro` and topology; an earlier instance's `.tpr` is not reused after the system composition has changed.

## 5.2 MDP template requirement

The future 3.3 implementation must carry a dedicated minimal MDP template, conceptually:

```text
templates/genion.mdp
```

Its sole purpose is to let `gmx grompp` generate the `.tpr` required by `gmx genion`.

It is not an EM, equilibration, or production-MD parameter set and carries no Stage 4 simulation semantics.

The exact template contents remain implementation work until separately added and validated after Skill generation is approved.

## 5.3 `gmx grompp` arg tendency

Primary tendencies:

```text
-f
→ Skill-provided genion.mdp

-c
→ current validated .gro

-p
→ current associated topology; normally sys.top when applicable

-o
→ genion.tpr for the current 3.3 instance
```

Typical form:

```bash
gmx grompp -f genion.mdp -c current.gro -p sys.top -o genion.tpr
```

## 5.4 `gmx genion` arg tendency

Primary tendencies:

```text
-neutral
→ preferred when the requested system should be neutralized

-conc 0.154
→ biomolecular-system tendency when no different salt concentration is explicitly requested

-pname / -nname
→ derive from the actual ion definitions and task requirement; do not hard-code one universal species

replacement group
→ select the actual intended bulk-solvent group; do not hard-code SOL
```

Typical biomolecular form when applicable:

```bash
gmx genion -s genion.tpr -o ionized.gro -p sys.top -neutral -conc 0.154
```

User-specified concentration/composition overrides the biomolecular `0.154 M` tendency.

## 5.5 Result boundary

3.3 normally produces:

- new ionized `.gro`;
- updated current `.top` / `sys.top` molecule composition;
- continued references to required `.itp` files;
- intermediate `genion.tpr` retained as execution evidence when useful.

The Step performs lightweight consistency checks for successful ion replacement/addition and coordinate/topology composition alignment.

---

# 6. Validation boundary

Stage 3 has no separate stage-level Validator Step.

Each 3.1 / 3.2 / 3.3 execution instance owns the local checks necessary to ensure that its output is a valid handoff object for the next task substep.

The last Stage 3 operation actually executed and successfully checked in the Task Sheet is the current constructed-system result for subsequent workflow use.

---

# 7. Frozen vs future work

Frozen architecture:

- three-step catalog `3.1 / 3.2 / 3.3`;
- default route `3.1 → 3.2 → 3.3`;
- repeatable Task Sheet execution instances for every Stage 3 step;
- no separate settings / final assembly / stage-level validation step;
- current 3.1 tool boundary = `gmx editconf`;
- 3.2 tool boundary = `gmx solvate`;
- 3.3 internal boundary = `gmx grompp → gmx genion`;
- 3.3 Skill-provided `genion.mdp` template requirement;
- current arg tendencies described above;
- `sys.top` naming tendency;
- 3.1 input may be any validated `.gro` with associated topology-file records.

Detailed generation-ready Step freezes preserved from pre-authorization material:

```text
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_3.1_PERIODIC_BOX_CONSTRUCTION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_3.2_SOLVENT_ADDITION_FREEZE.md
00_authoring/architecture_freezes/WORKFLOW3_STAGE3_3.3_ION_ADDITION_FREEZE.md
```

These are authoring references only. There is no active Stage 3 `SKILL.md` until explicit generation approval.

Remaining implementation/refinement work:

- exact `genion.mdp` template contents and representative/deterministic execution validation;
- more complex Agent/deterministic-tool box editing beyond `gmx editconf`;
- implementation-level filenames/schemas only where they become genuinely useful.

Pre-authorization Stage-main material was previously stored in blob `9e6a8fd5c566dfdcf70f7ffef6c44a85a55c93f6`; its substantive catalog/handoff content is represented by this Stage freeze and the three Step freezes above.

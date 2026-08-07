# MD Workflow Master Plan

Status: DRAFT

This file records the current planning baseline for the MD Workflow. It is a planning artifact, not an implementation contract. Items marked as confirmed are fixed unless later design evidence requires revision; items marked as draft still require dedicated planning before implementation.

## 1. Top-level stage numbering

Confirmed top-level stages:

1. Structure preparation
2. Topology / parameterization
3. System construction / solvation
4. MD simulation
5. Analysis

Numbering semantics:

- `1.3` means the MD Workflow stage 1.3, i.e. the third sub-stage under `1 Structure preparation`.
- The same rule applies to `2.x`, `3.x`, `4.x`, and `5.x`.
- Do not reuse the old mapping in which system construction was called `Stage 2.x`, MD simulation was `Stage 3`, and analysis was `Stage 4`.

## 2. Stage 1 — Structure preparation

### 2.1 Confirmed stages

#### 1.1 Structure source recognition

Purpose:

- identify the source and format of the input structure;
- identify the effective structure file used by the workflow;
- record source metadata needed by downstream processing.

Status: implemented / existing.

#### 1.2 Component and residue classification

Purpose:

- identify models and subunits;
- classify standard residues, connected nonstandard residues, independent nonstandard components, solvent, ions, and unresolved objects;
- record covalent and coordination relationships when supported by evidence;
- provide structured classification input for stage 1.3.

Important boundary:

- stage 1.2 identifies what components are;
- stage 1.2 does not decide which components are retained for MD;
- stage 1.2 may record known missing or incomplete residues/atoms as baseline structural facts.

Status: implemented / existing.

#### 1.3 Chain and component selection

Purpose:

- select the final model, chains/subunits, ligands, cofactors, metals, structural waters, ions, and other components that will enter the MD system;
- consume the structured classification produced by stage 1.2;
- make explicit keep/remove decisions rather than inferring them from residue names alone.

Status: planning; implementation has not started.

### 2.2 Completeness ordering rule

Confirmed planning correction:

- baseline structure completeness information must be available before stage 1.3 selection;
- therefore, completeness checking must not be moved wholesale to after stage 1.3;
- however, actual completion/repair should be performed only for the final selected system whenever possible.

Planning model:

1. Before or during the 1.2 -> 1.3 handoff:
   - detect and record missing residues, missing atoms, unresolved regions, or other incompleteness relevant to selection;
   - do not repair every component automatically.
2. Stage 1.3:
   - select the final MD components.
3. After stage 1.3:
   - perform completion/repair only for retained components that require it.

Exact ownership and numbering of the post-selection completion step remain to be frozen in a later planning pass.

### 2.3 Draft downstream structure-preparation stages

The following sequence is currently a draft and must not yet be treated as a frozen implementation contract:

- 1.4 Alternate conformation / occupancy resolution
- 1.5 Structure completion / repair for the selected system
- 1.6 Protonation state assignment
- 1.7 Structure normalization / reordering / mapping
- 1.8 Structure preparation validation

These stage boundaries and names require dedicated planning before implementation.

## 3. Stage 2 — Topology / parameterization

### 3.1 Current draft decomposition

- 2.1 Topology / force-field strategy
- 2.2 Standard component topology
- 2.3 Covalently linked nonstandard parameterization
- 2.4 Independent nonstandard component parameterization
- 2.5 Topology assembly
- 2.6 Topology validation

### 3.2 Routing principle

Parameterization should be routed primarily by component/topology ownership rather than by whether a parameter is ordinary or unusual.

Therefore:

- standard-component issues belong to 2.2;
- custom or missing parameters for covalently linked nonstandard residues belong to 2.3;
- custom or missing parameters for independent nonstandard components belong to 2.4;
- cross-component integration belongs to topology assembly in 2.5.

### 3.3 Removed stage concept

Do not create a separate `Special / custom parameter generation` stage.

Reason:

- it overlaps with stages 2.2-2.4 when the issue is component-specific;
- it overlaps with topology assembly when the issue is cross-component integration;
- a separate catch-all stage would mix two incompatible routing dimensions: component class and parameter complexity.

Special/custom parameter work must stay inside the appropriate 2.2-2.4 route, while final integration is handled by topology assembly.

Status of Stage 2 decomposition: draft; not yet frozen stage-by-stage.

## 4. Stage 3 — System construction / solvation

### 4.1 Current draft decomposition

- 3.1 System construction settings
- 3.2 Periodic box construction
- 3.3 Solvation
- 3.4 Ion addition
- 3.5 Final system assembly
- 3.6 System construction validation

Purpose of Stage 3 as a whole:

- start from a validated unsolvated structure/topology pair;
- construct the periodic simulation system;
- add solvent and ions according to the selected model and concentration strategy;
- produce a validated complete system ready to enter MD simulation.

Status: draft; stage boundaries still require review, especially whether final assembly should remain separate from final validation.

## 5. Stage 4 — MD simulation

Top-level stage confirmed.

Sub-stage decomposition: not planned in this file yet.

## 6. Stage 5 — Analysis

Top-level stage confirmed.

Sub-stage decomposition: not planned in this file yet.

## 7. Current planning state

Confirmed:

- top-level stages 1-5 and their numbering semantics;
- 1.1 Structure source recognition;
- 1.2 Component and residue classification;
- 1.3 Chain and component selection as the next stage to plan;
- baseline completeness information must precede selection;
- completion/repair should target the selected system;
- Stage 2 must not contain a separate generic special/custom-parameter stage.

Still to freeze:

- exact 1.4+ structure-preparation stage boundaries;
- detailed 1.3 contract, content map, write paths, dependencies, and work order;
- exact Stage 2 sub-stage boundaries and naming;
- exact Stage 3 sub-stage boundaries and naming;
- all Stage 4 and Stage 5 sub-stage plans.

## 8. Immediate next planning task

The next planning artifact should be for stage `1.3 Chain and component selection`.

Before implementation, freeze:

- stage boundary;
- local contract;
- content map;
- upstream and downstream interfaces;
- write paths;
- work order;
- completion and validation criteria.

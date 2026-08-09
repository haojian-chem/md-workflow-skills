# Runtime Orchestration Redesign Plan

Status: PLANNING BASELINE

## 1. Problem statement

Current MD Workflow runtime is functionally correct but has excessive fixed orchestration cost. Measurements from test runs show that Linux I/O, PDB inspection, hashing, and schema-tool execution are typically sub-second, while minutes are spent in repeated LLM-side reading, interpretation, task packaging, result interpretation, record generation, and re-entry into Workflow logic.

This is an architecture-wide runtime problem, not only an initialization problem.

The redesign goal is therefore not merely to remove checks. The goal is to minimize runtime LLM context and repeated model turns while preserving the existing responsibility boundaries, recovery model, evidence requirements, and deterministic validation guarantees.

## 2. Confirmed design decisions

The following decisions are adopted as the baseline for redesign.

### 2.1 Authoring rules and runtime rules must be separated

Files that explain why the architecture works, how Skills are authored, how contracts are designed, how multi-window authoring is coordinated, and how Tools are developed are authoring-time material.

They must not be repeatedly loaded during ordinary MD runtime unless an exceptional recovery/debugging case explicitly requires them.

Runtime should consume compact generated/curated runtime specifications rather than the full authoring corpus.

### 2.2 Four-layer responsibility boundaries remain

The logical architecture remains:

```text
Manager
Workflow
Operation
Validator
```

The redesign does not collapse these responsibilities.

However, a responsibility boundary is not automatically an LLM invocation boundary. The runtime may execute a responsibility through a deterministic Tool or through an existing active Agent context when appropriate.

### 2.3 Deterministic work should prefer deterministic execution

Operations that are fully deterministic and do not require scientific judgment should prefer registered Tools rather than creating a new LLM sub-Agent only to perform filesystem, parsing, hashing, schema, serialization, or other deterministic work.

Examples include, when safely toolable:

- file existence/type checks;
- bounded source-file discovery;
- copy/move under explicit policy;
- SHA-256 calculation;
- schema validation;
- state serialization;
- event generation;
- artifact-record construction;
- deterministic state commit and post-commit verification.

### 2.4 A task boundary does not have to create a new Agent boundary

The runtime must support at least these execution backends:

```text
DETERMINISTIC
AGENT_TASK
AGENT_SEQUENCE
```

`DETERMINISTIC`:
- execute through registered deterministic Tool(s);
- no new business sub-Agent is created.

`AGENT_TASK`:
- create one temporary sub-Agent for one contextually bounded Operation or Validator task.

`AGENT_SEQUENCE`:
- one temporary sub-Agent may execute a context-continuous sequence when the sequence does not cross a user-decision barrier, route-changing branch, ownership boundary, or other hard context boundary;
- Operation and Validator responsibilities and outputs remain separately represented even when they share one Agent context.

The exact eligibility rules for `AGENT_SEQUENCE` remain to be frozen before implementation.

### 2.5 Normal route progression should not require repeated full Workflow reasoning

An active route is an expected path, not only a historical note.

When a completed task produces no route-affecting evidence, no unresolved decision, no failure, no conditional-branch change, and no artifact-interface conflict, runtime may advance to the next already-recorded route node without re-reading and re-reasoning over the full Workflow.

Workflow must be re-entered when actual evidence can change the route or when the next node cannot be safely resolved from the active route.

The exact fast-path conditions must be deterministic and auditable.

### 2.6 Mechanical record construction should move out of LLM reasoning

`Manager owns records` means Manager controls/authorizes the commit boundary. It does not require the Manager LLM to manually construct every YAML field.

Mechanical construction and validation of:

- task/result records;
- terminal events;
- artifact records;
- Workstream state updates;
- direct-reference updates;

should be performed by deterministic builders/recorders wherever schemas permit.

Manager LLM should remain responsible for semantic decisions, ambiguity, exceptional states, route changes, recovery decisions, and user interaction.

## 3. Target runtime architecture

### 3.1 Authoring layer

Authoring remains the complete, explanatory source of truth for design and maintenance.

Representative inputs:

```text
AGENTS.md
00_authoring/**
design_records/**
03_contracts/**
full Workflow SKILL.md files
full Operation/Validator SKILL.md files
Tool authoring records and tests
```

### 3.2 Runtime layer

Runtime should consume a minimal subset generated or curated from authoring sources.

Candidate structure:

```text
runtime/
├── runtime_manifest.yaml
├── manager_runtime_spec.yaml
├── stage_registry.yaml
├── tool_registry.yaml
├── workflows/
│   └── <workflow>.runtime.yaml
└── task_contracts/
    └── minimal runtime contract/index information
```

The exact directory name and generation mechanism are not yet frozen.

### 3.3 Runtime compilation concept

A build/synchronization step should transform authoritative authoring sources into compact runtime material.

Conceptually:

```text
authoring sources
      ↓
compile / generate / validate
      ↓
minimal runtime specifications
      ↓
real MD project runtime
```

The generated runtime layer must be reproducible and traceable to its source revision. It must not become a second manually maintained source of truth.

## 4. Runtime context budget

The redesign should explicitly control how much static text an LLM must read during ordinary execution.

Initial planning targets:

- Manager entry/init: compact runtime manifest/spec only; no full authoring/reference corpus;
- route execution: only current Workstream state, active route node, current compact Workflow runtime spec, and directly required records;
- task dispatch: only task-local contract, current Skill, task inputs, resolved decisions, and required local references;
- schemas: consumed by deterministic Tools rather than read and manually simulated by LLM unless schema debugging is the explicit task.

These are design targets rather than frozen line-count limits. Concrete performance budgets will be set after baseline measurement tooling is defined.

## 5. Initialization under the redesigned runtime

Initialization is one consumer of the new runtime model, not the whole redesign.

NEW initialization should use only:

- root resolution;
- entry-state probe;
- compact Manager runtime spec;
- initial-state builder;
- candidate-only initialization validation;
- controlled commit;
- lightweight post-commit verification;
- initialization events.

It must not parse PDB structure content, load Workflow definitions, or read the authoring corpus.

Whether initialization uses a dedicated `INIT` validation mode or a restricted existing validation mode remains to be designed.

## 6. Ordinary task execution under the redesigned runtime

Target normal path:

```text
active route node
→ resolve execution backend
→ execute deterministic Tool or bounded Agent context
→ structured result
→ deterministic record/state commit
→ evaluate fast-path conditions
→ advance to next active-route node
```

Exceptional path:

```text
result
→ route-affecting evidence / decision / failure / conflict
→ re-enter Workflow and/or Manager semantic reasoning
→ route revision, decision, recovery, or pause
```

This replaces the current pattern in which every small task forces repeated full Manager/Workflow/Agent reasoning even when nothing semantically changed.

## 7. Files and systems that require coordinated review

The redesign must be reviewed as one coordinated change across at least:

1. `AGENTS.md`
   - separate runtime-critical instructions from authoring/development instructions.

2. `00_manager/md_workflow_manager/SKILL.md`
   - redefine runtime input set and semantic responsibilities;
   - remove expectations that mechanical record handling requires repeated LLM interpretation.

3. `00_manager/md_workflow_manager/references/*`
   - initialization;
   - route planning;
   - runtime checklist;
   - display rules where necessary.

4. `00_authoring/md-workflow-skill-authoring/references/layer_boundaries.md`
   - preserve responsibility boundaries while allowing multiple execution backends.

5. `00_authoring/md-workflow-skill-authoring/references/runtime_subagent_protocol.md`
   - replace the implicit one-task-one-new-Agent assumption with explicit execution backend rules.

6. `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`
   - define runtime compilation/builders/recorders and the boundary between deterministic execution and semantic reasoning.

7. `design_records/logging_and_record_system.md`
   - define deterministic record construction and semantic vs mechanical state transitions.

8. `03_contracts/**`
   - check whether current contracts force unnecessary LLM-side verbosity or can be consumed through compact runtime indexes/builders.

9. `05_tools/**`
   - identify missing deterministic runtime capabilities.

10. Workflow runtime representation
   - define compact per-Workflow runtime specs and route-node information.

## 8. Proposed redesign work packages

### R1 — Runtime/authoring separation

Deliverables:

- classify current files as AUTHORING_ONLY, RUNTIME_SOURCE, or RUNTIME_REQUIRED;
- define the minimal runtime information model;
- define source-of-truth and generated-file rules.

### R2 — Runtime manifest and compact Workflow specs

Deliverables:

- `runtime_manifest` design;
- compact Manager runtime spec;
- compact Workflow runtime spec;
- provenance/version/hash rules;
- validation rules for generated runtime material.

### R3 — Execution backend model

Deliverables:

- `DETERMINISTIC | AGENT_TASK | AGENT_SEQUENCE` semantics;
- eligibility and prohibition rules;
- context-boundary rules;
- fallback behavior when deterministic Tool capability is absent.

### R4 — Deterministic record/state commit path

Deliverables:

- semantic input shape from Manager/Workflow/Agent;
- deterministic builders for records/state/events;
- schema validation and controlled commit path;
- explicit recovery behavior.

### R5 — Active-route fast path

Deliverables:

- deterministic conditions for advancing without full Workflow re-entry;
- conditions that require Workflow/Manager semantic re-entry;
- route-revision interaction;
- audit evidence.

### R6 — Initialization simplification

Deliverables:

- candidate-only init validation mode;
- prohibition of business-file/PDB content inspection during initialization;
- minimal initialization runtime package;
- benchmark against current test case.

### R7 — 1.1/1.2 migration and benchmark

Use stages 1.1 and 1.2 as the first real workflow benchmark because they expose both deterministic and semantic execution patterns.

Deliverables:

- 1.1 execution backend decision;
- 1.2 dependency preflight ordering;
- reduced runtime context;
- measured before/after timing;
- verification that scientific outputs and recovery records are unchanged in meaning.

## 9. Performance acceptance criteria

The redesign is successful only if correctness is preserved and fixed orchestration cost drops materially.

Minimum acceptance criteria:

- deterministic Linux/PDB/schema work is not surrounded by minutes of repeated LLM bookkeeping;
- ordinary runtime no longer reads the full authoring corpus;
- schemas are not routinely interpreted field-by-field by LLM;
- unchanged active-route progression does not require full Workflow re-reasoning at every step;
- mechanical records are built deterministically;
- user decisions, recovery, route-changing evidence, and scientific ambiguity still invoke semantic reasoning;
- existing state ownership, artifact provenance, validation status, and recovery guarantees are preserved.

Quantitative latency targets will be frozen after a small runtime timing harness is defined. Existing test observations should be retained as the pre-redesign baseline.

## 10. Non-goals

This redesign does not:

- remove Manager/Workflow/Operation/Validator responsibility boundaries;
- weaken scientific validation gates;
- remove Workstreams or active routes;
- allow uncontrolled parallel foreground Agents;
- allow Operation/Validator to write Manager-owned records directly;
- replace deterministic evidence with heuristic LLM assumptions;
- redesign stage 1.3 scientific behavior itself.

## 11. Development order

Current priority order:

```text
Runtime orchestration redesign planning
→ freeze R1-R5 architecture
→ implement minimal runtime infrastructure
→ migrate and benchmark initialization + 1.1 + 1.2
→ confirm performance/correctness
→ resume detailed 1.3 planning and implementation
```

Stage 1.3 remains the next scientific workflow stage, but its implementation should not proceed on top of a runtime orchestration model already shown to impose excessive fixed cost.

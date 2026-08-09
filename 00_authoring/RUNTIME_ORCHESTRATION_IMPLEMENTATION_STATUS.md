# Runtime Orchestration Redesign — Implementation Status

Updated: 2026-08-09

Baseline plan:

`00_authoring/RUNTIME_ORCHESTRATION_REDESIGN_PLAN.md`

## Current status

### R1 — Runtime / authoring separation

Status: BOOTSTRAP_IMPLEMENTED

Completed:

- root `AGENTS.md` reduced to mode routing + minimal universal runtime/safety rules;
- authoring/development rules moved to `00_authoring/AUTHORING_RULES.md`;
- real MD runtime explicitly prohibited from default-loading authoring corpus;
- Manager runtime fallback to authoring sources limited to recovery/debug/conflict/stale-projection cases.

Still required:

- validate real runner behavior with a fresh project timing test after R4-R7 migration.

### R2 — Runtime manifest and compact Workflow specs

Status: IMPLEMENTED_ACTIVE

Completed:

- `runtime/runtime_manifest.yaml`;
- `runtime/manager_runtime_spec.yaml`;
- `runtime/task_contracts/index.yaml`;
- `runtime/workflows/structure_preparation.runtime.yaml`;
- machine-readable Manager and Workflow projection sources;
- `00_authoring/runtime_projection_config.yaml`;
- ACTIVE `runtime_projection_compiler 0.1.0`;
- source-guard drift detection;
- deterministic BUILD/CHECK modes;
- generated-file byte-level verification against committed runtime files;
- stage registry compact-spec-first invocation.

Current runtime projection state:

```text
projection_status: generated_active
projection_mode: deterministic_compiled
```

Maintenance rule:

- runtime files are generated and non-authoritative;
- guarded authoring-source changes require explicit source-guard update and projection rebuild;
- ordinary runtime should consume generated projections rather than authoring corpus.

### R3 — Execution backend model

Status: SEMANTICS_FROZEN_BOOTSTRAP_ACTIVE

Completed:

- four-layer responsibility boundaries preserved;
- responsibility boundary explicitly separated from Agent/process boundary;
- `DETERMINISTIC | AGENT_TASK | AGENT_SEQUENCE` defined;
- deterministic capability fallback rules defined;
- AGENT_SEQUENCE eligibility defined conservatively;
- AGENT_SEQUENCE remains `DISABLED_BY_DEFAULT` pending contract/tool/recovery support.

Still required:

- implement deterministic backend for suitable nodes, beginning with 1.1;
- design/validate sequence contract before enabling AGENT_SEQUENCE.

### R4 — Deterministic record/state commit path

Status: DESIGN_FROZEN_IMPLEMENTATION_IN_PROGRESS

Protocol:

`00_authoring/md-workflow-skill-authoring/references/runtime_record_commit_protocol.md`

Registered capability:

`runtime_record_committer — DESIGNED`

Current work:

- implement Tool;
- fixtures and rollback tests;
- integrate `runtime_schema_validator FAST`;
- benchmark Manager closure before/after.

### R5 — Active-route fast path

Status: DESIGN_FROZEN_IMPLEMENTATION_PENDING

Protocol:

`00_manager/md_workflow_manager/references/route_fast_path_protocol.md`

Registered capability:

`route_fast_path_evaluator — DESIGNED`

Current runtime state:

`ACTIVE_ROUTE_FAST_PATH = DISABLED`

Next work:

- implement evaluator Tool;
- REQUIRED/CONDITIONAL/user-scope/recovery fixtures;
- integrate with R4 commit receipt;
- benchmark 1.1 -> 1.2 progression.

### R6 — Initialization simplification

Status: NOT_YET_MIGRATED

Current Manager runtime spec deliberately keeps initialization validation in compatibility mode.

Next work:

- define candidate-only `INIT` validation or restricted existing mode;
- remove FULL dependency from NEW initialization after validation equivalence is demonstrated;
- ensure Manager entry/init never parses PDB/mmCIF business content;
- benchmark fresh-project initialization.

### R7 — 1.1 / 1.2 migration and benchmark

Status: NOT_STARTED

Planned order:

1. 1.1: add/activate deterministic source-recognition capability where semantics are fully deterministic;
2. 1.2: move hard dependency checks before expensive Agent/rule loading;
3. run initialization + 1.1 + 1.2 timing benchmark;
4. compare scientific outputs, artifact semantics and recovery records with baseline.

## Current safety posture

The redesign now has an ACTIVE deterministic runtime projection compiler, but task closure and route advancement still use compatibility paths.

Specifically:

- AGENT_SEQUENCE is disabled;
- active-route fast path is disabled;
- runtime record committer is DESIGNED, not ACTIVE;
- runtime projection compiler is ACTIVE;
- 1.1 deterministic backend still falls back to AGENT_TASK because its business capability is not yet registered ACTIVE;
- existing validation/recovery guarantees remain in compatibility mode until R4-R7 migration tests pass.

## Immediate next implementation package

```text
P2: runtime_record_committer
→ P3: route_fast_path_evaluator
→ P4: R6 initialization validation migration
→ P5: 1.1 deterministic migration
→ P6: 1.2 dependency-preflight migration
→ benchmark initialization + 1.1 + 1.2
```

Do not resume stage 1.3 implementation until this migration reaches a measured, stable runtime baseline.

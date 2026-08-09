# Runtime Orchestration Redesign — Implementation Status

Updated: 2026-08-09

Baseline plan:

`00_authoring/RUNTIME_ORCHESTRATION_REDESIGN_PLAN.md`

## Current status

### R1 — Runtime / authoring separation

Status: IMPLEMENTED_ACTIVE

Completed:

- root `AGENTS.md` reduced to mode routing + minimal universal runtime/safety rules;
- authoring/development rules moved to `00_authoring/AUTHORING_RULES.md`;
- real MD runtime does not default-load authoring corpus;
- Manager fallback to authoring sources limited to recovery/debug/conflict/stale-projection cases.

Remaining validation:

- final real-run timing benchmark after P5/P6 migration.

### R2 — Runtime manifest and compact Workflow specs

Status: IMPLEMENTED_ACTIVE

Completed:

- generated `runtime/runtime_manifest.yaml`;
- generated `runtime/manager_runtime_spec.yaml`;
- generated `runtime/task_contracts/index.yaml`;
- generated `runtime/workflows/structure_preparation.runtime.yaml`;
- machine-readable Manager/Workflow projection sources;
- ACTIVE `runtime_projection_compiler 0.1.0`;
- guarded-source drift detection;
- deterministic BUILD/CHECK and CI projection check.

Current projection:

```text
projection_status: generated_active
projection_mode: deterministic_compiled
```

### R3 — Execution backend model

Status: ACTIVE_WITH_AGENT_SEQUENCE_DISABLED

Completed:

- four responsibility layers preserved;
- responsibility boundary separated from Agent/process boundary;
- `DETERMINISTIC | AGENT_TASK | AGENT_SEQUENCE` semantics defined;
- deterministic fallback rules active.

Current restriction:

- `AGENT_SEQUENCE` remains `DISABLED_BY_DEFAULT` until sequence contract, multi-result transaction and recovery fixtures exist.

### R4 — Deterministic record/state commit path

Status: IMPLEMENTED_ACTIVE

Tool:

`runtime_record_committer 0.1.0 — ACTIVE`

Evidence:

`04_evals/runtime_record_committer/VALIDATION.md`

GitHub Actions:

- run `31307633657`
- 7 acceptance tests passed with real `runtime_schema_validator FAST` integration.

Benchmark:

```text
ordinary closure median: 437.781 ms
FAST validator median:  300.553 ms
```

Active scope:

- ordinary foreground task result/event/artifact/decision/submission/Workstream-state closure;
- project_state, route revision, recovery and reinforced external-task lifecycles remain outside v0.1 scope.

### R5 — Active-route fast path

Status: IMPLEMENTED_ACTIVE

Tool:

`route_fast_path_evaluator 0.1.0 — ACTIVE`

Evidence:

`04_evals/route_fast_path_evaluator/VALIDATION.md`

GitHub Actions:

- run `31307887115`
- 10 tests passed, including R5 -> R4 integration.

Benchmark:

```text
normal ADVANCE median: 18.395 ms
```

Clean normal path is now:

```text
terminal business result
→ route_fast_path_evaluator
→ explicit route progression
→ runtime_record_committer + one FAST
→ Workstream state commit
```

Full Workflow semantic re-entry occurs only on semantic triggers, conditional uncertainty, failure, decision, conflict or recovery.

### R6 — Initialization simplification

Status: IMPLEMENTED_ACTIVE

NEW initialization now uses:

```text
INIT_CANDIDATE_VALIDATION
= runtime_schema_validator FAST
  on candidate project_state + candidate initial Workstream state only
  with logical-path overlay and direct references
```

NEW initialization no longer runs FULL and does not parse PDB/mmCIF/business content.

Evidence:

`04_evals/initialization_candidate_validation/VALIDATION.md`

GitHub Actions:

- run `31308193808`
- 7 tests passed.

Cold fresh-project benchmark:

```text
validator internal median: 370.901 ms
subprocess wall median:    491.979 ms
```

Runtime projection was rebuilt after migration and `runtime_projection_compiler --mode CHECK` passed in run `31308434362`.

### R7 — 1.1 / 1.2 migration and benchmark

Status: IN_PROGRESS

Current package:

```text
P5: 1.1 deterministic migration
```

Then:

```text
P6: 1.2 hard dependency preflight before Agent/rule loading
→ end-to-end initialization + 1.1 + 1.2 benchmark
```

## Current safety posture

Active:

- generated compact runtime projection;
- deterministic ordinary task closure;
- deterministic active-route fast path;
- candidate-only NEW initialization validation.

Still conservative:

- `AGENT_SEQUENCE` disabled;
- 1.1 remains AGENT_TASK fallback until its deterministic business Tool passes tests and becomes ACTIVE;
- 1.2 remains AGENT_TASK and has not yet migrated hard dependency preflight.

## Immediate next implementation package

```text
P5: source_recognition_deterministic
→ rebuild structure Workflow runtime projection
→ P6: 1.2 dependency-preflight migration
→ benchmark fresh initialization + 1.1 + 1.2
```

Stage 1.3 implementation remains paused until the migrated runtime baseline is measured and stable.

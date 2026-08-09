# Runtime Real-Run Benchmark Protocol

Status: ACTIVE BENCHMARK PROTOCOL

Purpose: measure the post-redesign real Manager runtime without mixing deterministic fixed cost, Manager semantic work, Agent startup, and stage-1.2 scientific execution into one opaque total.

## 1. Test scope

Use a fresh MD project with one clear local PDB/mmCIF source and request a route that includes:

```text
NEW project initialization
→ 1.1 source_recognition
→ 1.2 component_and_residue_classification
```

Use the same host/model configuration as the pre-redesign timing where possible.

Do not deliberately alter scientific inputs or package environment merely to improve/slow the result.

## 2. Runtime assertions that must be visible in evidence

### Manager entry / initialization

Expected:

```text
runtime manifest + manager runtime spec
→ minimal entry probe
→ INIT_CANDIDATE_VALIDATION
```

Must not occur on the normal NEW path:

- full authoring corpus load;
- full Manager reference load;
- PDB/mmCIF scientific parsing by Manager;
- FULL runtime validation;
- initialization snapshot.

### Stage 1.1

Expected default backend:

```text
DETERMINISTIC
source_recognition_deterministic
```

For one unambiguous local source with default copy behavior, no business Agent context should be created.

Expected closure path:

```text
source_recognition_deterministic
→ route_fast_path_evaluator
→ runtime_record_committer
```

If deterministic eligibility is not met, evidence must state the exact fallback reason before `AGENT_TASK` is used.

### Stage 1.2

Before any 1.2 business Agent context is created:

```text
runtime_dependency_preflight
```

Expected dependency manifest:

```text
02_validators/component_and_residue_classification_validator/references/runtime_dependencies.json
```

PASS:

```text
preflight PASS
→ create/start 1.2 AGENT_TASK
```

BLOCKED:

```text
preflight BLOCKED
→ do not create 1.2 Agent
→ runtime_record_committer closes task as WAITING / DEPENDENCY
```

The 1.2 Agent must not repeat the same complete package import/version probe merely for reassurance after a valid preflight PASS.

## 3. Required timestamps

Record monotonic/wall timestamps for these boundaries where the runner supports them:

```text
T0  Manager runtime entry
T1  entry state resolved
T2  initialization candidate package ready
T3  INIT_CANDIDATE_VALIDATION returned
T4  initialization state/events committed and verified
T5  route scope resolved
T6  active route record ready
T7  task 1.1 record ready
T8  source_recognition_deterministic start
T9  source_recognition_deterministic end
T10 route_fast_path_evaluator end for 1.1
T11 runtime_record_committer end for 1.1
T12 task 1.2 record ready
T13 runtime_dependency_preflight start
T14 runtime_dependency_preflight end
T15 1.2 Agent context creation/start, only if preflight PASS
T16 first 1.2 scientific script/check starts
T17 1.2 responsibility result returned
T18 R5/R4 closure completed for 1.2, when applicable
T19 final user-visible response ready
```

If the runner cannot emit every timestamp, retain the nearest observable timestamps and state which interval cannot be separated.

## 4. Reported intervals

At minimum report:

```text
Manager entry interpretation      = T1 - T0
Initialization candidate prep     = T2 - T1
Initialization validation         = T3 - T2
Initialization commit/verify      = T4 - T3
Route scope + route construction  = T6 - T4
1.1 task packaging                = T7 - T6
1.1 deterministic business        = T9 - T8
1.1 R5/R4 closure                 = T11 - T9
1.2 task packaging                = T12 - T11
1.2 dependency preflight          = T14 - T13
1.2 Agent startup                 = T16 - T15
1.2 scientific execution          = T17 - T16
1.2 closure                       = T18 - T17
Final response/render             = T19 - last applicable boundary
Total                             = T19 - T0
```

Do not merge scientific execution time into framework overhead when diagnosing runtime architecture.

## 5. Deterministic reference measurements

CI reference medians from the redesign implementation:

```text
INIT candidate validation wall          ~492 ms
1.1 deterministic subprocess wall        ~69 ms
R5 normal ADVANCE evaluator internal      ~18 ms
R4 ordinary closure internal             ~438 ms
1.2 dependency preflight subprocess wall ~228 ms
```

These values are CI reference points, not hard latency guarantees for another host.

A real run showing multi-minute time in one of these deterministic boundaries indicates a runner/invocation problem rather than intended scientific computation.

## 6. Residual bottleneck decision rule

After the real run, optimize only a measured residual bottleneck.

Examples:

- `Route scope + route construction` still minutes while all deterministic boundaries are sub-second:
  investigate compact route construction / deterministic route-record builder.
- `1.1 task packaging` still minutes before the deterministic Tool starts:
  investigate deterministic task builder / task-contract packaging.
- `1.2 Agent startup` dominates after dependency PASS:
  reduce Agent-local static context and Skill/reference loading.
- `1.2 scientific execution` dominates:
  optimize scientific scripts or data access, not Manager orchestration.
- `Final response/render` dominates:
  reduce Manager post-task re-reading/rendering rather than scientific gates.

No additional runtime optimization should be implemented solely because a component is conceptually optimizable; require timing evidence that it is still material.

## 7. Pass criteria before resuming stage 1.3 implementation

The redesigned baseline is considered stable enough to resume 1.3 when:

- normal runtime consumes compact projections rather than authoring corpus;
- NEW initialization uses candidate-only validation;
- normal 1.1 uses deterministic backend where eligible;
- 1.2 dependency gate occurs before Agent startup;
- ordinary 1.1 closure uses R5/R4 without full Workflow re-entry;
- no unexplained multi-minute deterministic boundary remains;
- remaining latency is attributed to a specific semantic/Agent/scientific interval.

# source_recognition_deterministic validation

Date: 2026-08-09

Semantic owner:

`02_operations/source_recognition/SKILL.md`

Guarded semantic-owner blob:

`4dc1cd80fc8253c0100788135807f5f6b5865187`

Tool code blob:

`75d3f02f2e6245268e5cecaeeae2c26f9ff025ca`

Acceptance test blob:

`0be4c10d08736445b0d5f0216a5f008e43ba5c8a`

GitHub Actions:

- workflow: `source-recognition-deterministic`
- run ID: `31308634688`
- job ID: `93232872020`
- head commit: `04381d0eac5790b4d1b6ee395c4d34eb421e3bb5`
- conclusion: success

## Acceptance tests

```text
8 passed in 1.37s
```

Covered behavior:

- unique local PDB candidate -> default copy + matching SHA-256 + STRUCTURE candidate;
- unique local CIF candidate -> default copy;
- identical existing destination -> deterministic reuse without rewrite;
- multiple valid candidates -> blocking structured source-selection confirmation, no copy;
- no valid bounded candidate -> BLOCKED, no copy;
- different existing destination -> blocking destination-conflict confirmation, no overwrite;
- candidate outside allowed read scope -> Tool failure;
- full deterministic stage-1.1 integration:
  `source_recognition_deterministic -> route_fast_path_evaluator -> runtime_record_committer`, including real R4 FAST validation and Workstream advancement to 1.2.

## Benchmark

GitHub-hosted Ubuntu runner, Python 3.11, 20 independent unique-PDB source-recognition tasks:

```text
business_internal_median_ms=8.207
business_internal_min_ms=7.899
business_internal_max_ms=13.029
subprocess_wall_median_ms=69.448
subprocess_wall_min_ms=68.287
subprocess_wall_max_ms=79.604
```

The business timing includes semantic-source guard, task/preflight checks, basic source signature, SHA-256, atomic copy, report/log construction and responsibility-result construction. It excludes R5/R4 closure costs.

Using measured medians for the complete clean orchestration path gives an approximate deterministic fixed-path cost of:

```text
1.1 business subprocess wall  ~ 69 ms
R5 evaluator                  ~ 18 ms
R4 closure + FAST             ~438 ms
---------------------------------------
combined deterministic path   ~525 ms
```

This replaces the previous multi-minute Agent/Manager orchestration for the same default 1.1 case.

## Scope and fallback

ACTIVE deterministic scope:

- bounded source candidates supplied as task `current_valid_files` with role beginning `source_candidate`;
- local PDB/CIF/mmCIF;
- default copy;
- identical-copy reuse;
- deterministic ambiguity/conflict detection.

Fallback to `AGENT_TASK` remains required for unsupported semantic requests, especially explicitly requested controlled source moves or behavior outside the guarded source-recognition default policy.

## Activation decision

Version `0.1.0` is eligible for ACTIVE status as capability `source_recognition_deterministic`.

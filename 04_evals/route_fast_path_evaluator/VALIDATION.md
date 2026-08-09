# route_fast_path_evaluator validation

Date: 2026-08-09

Tool code blob:

`c26af765143c3b6cf875de9bf9a7004537d55260`

Acceptance test blob:

`959b69dccbc80421ca0a6ac1083eca456ca38fba`

GitHub Actions evidence:

- workflow: `route-fast-path-evaluator`
- run ID: `31307887115`
- job ID: `93231018100`
- head commit: `a9971a7770b49e5f4ce880ba6100bfe7cf982fd6`
- conclusion: `success`

## Acceptance tests

```text
10 passed in 1.71s
```

Covered cases:

- REQUIRED next node with clean evidence -> `ADVANCE`;
- current route scope end -> `STOP_SCOPE`;
- CONDITIONAL next node with unknown condition -> `REENTER_WORKFLOW`;
- CONDITIONAL next node with explicit true condition -> `ADVANCE`;
- confirmation item -> `REENTER_WORKFLOW`;
- route-affecting evidence -> `REENTER_WORKFLOW`;
- Workstream recovery -> `BLOCKED`;
- Workstream current-position / route conflict -> `BLOCKED`;
- PARTIAL route boundary with known blocker -> `BLOCKED`;
- integration with ACTIVE R4 path: evaluator `ADVANCE` result supplies explicit next route position to `runtime_record_committer`, whose real FAST validation/commit then advances Workstream state.

## Benchmark

GitHub-hosted Ubuntu runner, Python 3.11, 50 independent normal-path ADVANCE evaluations:

```text
evaluator_median_ms=18.395
evaluator_min_ms=18.081
evaluator_max_ms=25.200
```

The benchmark is deterministic evaluator time only; no LLM or Workflow Skill re-read is involved.

## Semantic safety

- evaluator never creates or revises a route;
- evaluator does not derive scientific gate status from business files or prose;
- unresolved or false/unknown CONDITIONAL-node status never causes silent skip/advance;
- failure, confirmation, new conditional evidence, artifact-interface uncertainty, user scope changes and other route-affecting facts force Workflow semantic re-entry;
- route/state/result identity conflicts return `BLOCKED` rather than being interpreted as ordinary Workflow branching;
- normal `ADVANCE` is limited to already-planned active-route nodes represented by the compact Workflow runtime spec.

## Activation decision

Version `0.1.0` is eligible for ACTIVE status.

With R4 active, the ordinary clean path can now be:

```text
terminal business result
→ deterministic fast-path evaluation (~18 ms median)
→ explicit route progression
→ deterministic R4 record/state closure (~438 ms median including FAST validator)
```

A semantic trigger still re-enters Workflow/Manager reasoning instead of using the fast path.

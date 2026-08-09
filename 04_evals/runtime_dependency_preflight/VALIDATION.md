# runtime_dependency_preflight validation

Date: 2026-08-09

Tool code blob:

`f28e9c1909a2f637b76ba87a90c8cdb62ba3b3bd`

Acceptance test blob:

`afc8514c520a560c3246747164436cb6be5a61d3`

GitHub Actions:

- workflow: `runtime-dependency-preflight`
- run ID: `31309006535`
- job ID: `93233803934`
- head commit: `2b26a736a769d8be9ed71cd1d68f3ff03bc86bb3`
- conclusion: success

## Acceptance tests

```text
6 passed in 1.10s
```

Covered behavior:

- real stage-1.2 dependency manifest passes when declared requirements are installed;
- missing import/distribution returns deterministic `BLOCKED` with a subagent_result-v2-shaped Validator responsibility result;
- incompatible installed version returns `BLOCKED`;
- owner Skill Git-blob guard mismatch returns Tool `ERROR`;
- requirements-source Git-blob guard mismatch returns Tool `ERROR`;
- dependency blocker responsibility result closes through ACTIVE `runtime_record_committer`, leaving the Workstream in `WAITING / DEPENDENCY` without starting the scientific Validator Agent.

## Real stage 1.2 dependency manifest

```text
02_validators/component_and_residue_classification_validator/references/runtime_dependencies.json
```

Declared dependencies:

```text
gemmi       >=0.7,<0.8
PyYAML      >=6,<7
jsonschema  >=4.20,<5
referencing >=0.30,<1
```

The preflight Tool itself uses Python standard library only, so it remains runnable when any of those packages are missing.

## Benchmark

GitHub-hosted Ubuntu runner, Python 3.11, 20 independent preflight subprocesses using the real stage-1.2 dependency manifest:

```text
internal_median_ms=167.951
internal_min_ms=161.599
internal_max_ms=212.790
subprocess_wall_median_ms=228.170
subprocess_wall_min_ms=218.954
subprocess_wall_max_ms=274.146
```

This check happens before the stage-1.2 business Agent context is created. Missing `gemmi`/PyYAML/jsonschema/referencing therefore becomes a ~0.2 s deterministic blocker instead of a multi-minute late Agent failure.

## Semantic safety

- no package installation;
- no network access;
- no PDB/mmCIF/business-file inspection;
- no scientific classification or gate judgment;
- owner Skill and requirements file are guarded by exact Git blob identity;
- PASS only authorizes starting the normal 1.2 `AGENT_TASK`;
- BLOCKED does not claim scientific Validator execution; its outcome explicitly states that classification did not start.

## Activation decision

Version `0.1.0` is eligible for ACTIVE status as the pre-Agent dependency gate for stage 1.2.

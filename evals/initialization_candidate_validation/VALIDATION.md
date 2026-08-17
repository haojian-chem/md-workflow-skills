# Initialization candidate validation evidence

Date: 2026-08-09

Purpose: validate R6 migration from NEW-project FULL validation to a restricted candidate-only invocation of the existing ACTIVE `runtime_schema_validator --mode FAST`.

GitHub Actions:

- workflow: `initialization-candidate-validation`
- run ID: `31308193808`
- job ID: `93231785945`
- head commit: `6c5f66fb05bcc5a1699db7e13ba66caa3938514b`
- conclusion: success

## Acceptance tests

```text
7 passed in 7.84s
```

Covered behavior:

- valid initial `project_state` + initial Workstream state candidate overlay passes both restricted FAST and legacy FULL;
- malformed project-state candidate fails both restricted FAST and legacy FULL;
- project-state reference to a missing initial Workstream state fails restricted FAST;
- initial Workstream state with a non-existent active route fails direct-reference validation;
- arbitrary/invalid PDB bytes in the project root are not initialization validation targets;
- unrelated historical runtime record is not turned into a candidate-validation target by restricted FAST, while FULL does scan it;
- cold candidate-validation benchmark remains below the test safety ceiling.

The unrelated-record fixture is a scope test only: a real project containing prior business/runtime records must already have been rejected as NEW by the Manager entry probe and routed to recovery where appropriate.

## Restricted invocation

The approved R6 package is not a new validator mode. It is a fixed invocation profile of the existing ACTIVE validator:

```bash
python <skill_root>/05_tools/runtime_schema_validator/validate.py \
  --project-root <md_project_root> \
  --contracts-dir <skill_root>/03_contracts \
  --mode FAST \
  --changed <candidate_project_state> <candidate_workstream_state> \
  --logical-map <candidate_project_state>=00_project_state/project_state.yaml \
  --logical-map <candidate_workstream_state>=00_project_state/workstreams/<workstream_id>.yaml
```

No PDB/mmCIF/business file is included in `--changed`.

## Cold benchmark

GitHub-hosted Ubuntu runner, Python 3.11, 12 independent fresh project roots (therefore cold per-project schema cache):

```text
internal_median_ms=370.901
internal_min_ms=367.005
internal_max_ms=390.558
subprocess_wall_median_ms=491.979
subprocess_wall_min_ms=486.656
subprocess_wall_max_ms=515.055
```

This is deterministic validation cost only. It replaces a project-wide FULL runtime-instance scan during NEW initialization and, more importantly, removes the architectural reason for Manager LLM full-audit behavior at initialization.

## Migration decision

R6 candidate validation is accepted.

NEW initialization should now require:

```text
INIT_CANDIDATE_VALIDATION
```

implemented by the restricted FAST invocation above, rather than `FULL_RUNTIME_VALIDATION`.

FULL remains reserved for recovery, schema/contract changes, root changes and other explicitly defined project-wide lifecycle audits.

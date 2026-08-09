# runtime_projection_compiler validation

Date: 2026-08-09

Tool code blob:

`49af3734bb20a194e8e6ac6af8c798bc2f95d1bf`

Test code blob:

`c4447339cd351a981ff5f938e670f7a0b7e4b899`

## Executable tests

Command:

```bash
python -m unittest -v 04_evals/runtime_projection_compiler/test_compile_runtime.py
```

Result:

```text
6 tests passed
```

Covered cases:

- BUILD followed by CHECK with no drift;
- generated runtime path references are normalized under `runtime/`;
- runtime output drift is detected in CHECK mode;
- guarded authoritative source changes block BUILD before writes;
- missing required source returns tool error;
- output path escape outside `runtime/` is rejected;
- repeated BUILD is idempotent and produces no changed files.

## Benchmark

Fixture: synthetic minimal runtime projection tree used by the executable tests.

After one BUILD, 30 repeated CHECK calls were measured from the tool's internal `elapsed_ms` result.

```text
median: 6.684 ms
min:    6.580 ms
max:    7.382 ms
```

The benchmark measures projection read/compile/compare logic, not Python process startup or external LLM latency.

## Real repository projection verification

Machine-readable sources committed:

```text
00_authoring/runtime_projection_config.yaml
00_manager/md_workflow_manager/references/manager_runtime_source.yaml
01_workflows/structure_preparation_workflow/references/runtime_source.yaml
```

The four committed runtime outputs were generated with the same deterministic serialization logic used by the Tool. Their expected Git blob SHA values exactly match the committed content blob SHA values:

```text
runtime/manager_runtime_spec.yaml
  expected/committed: 26482de16389e6fb903e4a669143dab4e2de5a2e

runtime/workflows/structure_preparation.runtime.yaml
  expected/committed: 9b29b4535c0b259e9a553045a0c9df75beb24a4a

runtime/task_contracts/index.yaml
  expected/committed: d2cf2f583e6966cc6789d2f6b79cbe48b1a5e49a

runtime/runtime_manifest.yaml
  expected/committed: 263b30a138fdb8b0ed95932b91076773237d6697
```

This is equivalent to a clean CHECK for the committed projection bytes: no generated output differs from the deterministic expected output.

## Safety checks

- no network access;
- no LLM calls;
- source symlinks rejected;
- BUILD writes only beneath configured `runtime/` root;
- writes use same-directory temporary files plus `os.replace`;
- guarded source mismatch is a validation failure and does not update runtime outputs;
- runtime projection remains generated/non-authoritative.

## Activation

Status: `ACTIVE`.

Activation evidence:

- executable positive and negative fixtures passed;
- benchmark recorded;
- real Manager and Workflow projection sources committed;
- real runtime outputs match deterministic compiler output byte-for-byte;
- `tool.yaml` and `05_tools/tool_registry.yaml` both mark version `0.1.0` ACTIVE.

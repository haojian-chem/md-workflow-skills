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

## Safety checks

- no network access;
- no LLM calls;
- source symlinks rejected;
- BUILD writes only beneath configured `runtime/` root;
- writes use same-directory temporary files plus `os.replace`;
- guarded source mismatch is a validation failure and does not update runtime outputs;
- runtime projection remains generated/non-authoritative.

## Remaining activation gate

Before marking the Tool ACTIVE:

1. commit machine-readable Manager and Workflow projection sources;
2. generate the real repository runtime projection from those sources;
3. verify committed runtime files equal compiler output in CHECK mode semantics;
4. update `tool.yaml` and `tool_registry.yaml` to ACTIVE.

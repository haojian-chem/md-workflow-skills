from pathlib import Path
import statistics
import tempfile

from test_runtime_record_committer import make_project, request, result, run_cli


def main():
    samples = []
    validator_samples = []
    for _ in range(12):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ws, _, _ = make_project(root)
            code, receipt = run_cli(root, request("task_0001", ws, result("task_0001", ws)))
            if code != 0:
                raise SystemExit(f"benchmark closure failed: {receipt}")
            samples.append(float(receipt["elapsed_ms"]))
            if receipt.get("validator_elapsed_ms") is not None:
                validator_samples.append(float(receipt["validator_elapsed_ms"]))
    print(f"samples={len(samples)}")
    print(f"closure_median_ms={statistics.median(samples):.3f}")
    print(f"closure_min_ms={min(samples):.3f}")
    print(f"closure_max_ms={max(samples):.3f}")
    if validator_samples:
        print(f"validator_median_ms={statistics.median(validator_samples):.3f}")


if __name__ == "__main__":
    main()

from pathlib import Path
import statistics
import tempfile

from test_route_fast_path_evaluator import base_steps, route, run_eval


def main():
    samples = []
    for _ in range(50):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_eval(Path(tmp), route(base_steps()))
            if code != 0 or out.get("decision") != "ADVANCE":
                raise SystemExit(f"benchmark evaluation failed: {out}")
            samples.append(float(out["elapsed_ms"]))
    print(f"samples={len(samples)}")
    print(f"evaluator_median_ms={statistics.median(samples):.3f}")
    print(f"evaluator_min_ms={min(samples):.3f}")
    print(f"evaluator_max_ms={max(samples):.3f}")


if __name__ == "__main__":
    main()

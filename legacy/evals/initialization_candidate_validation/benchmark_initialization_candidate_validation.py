from pathlib import Path
import statistics
import tempfile
import time

from test_initialization_candidate_validation import candidates, run_validator


def main():
    internal = []
    wall = []
    for _ in range(12):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p, ws, ws_id = candidates(root)
            started = time.perf_counter()
            code, out = run_validator(root, "FAST", p, ws, ws_id)
            wall.append((time.perf_counter() - started) * 1000)
            if code != 0:
                raise SystemExit(f"candidate validation failed: {out}")
            internal.append(float(out["elapsed_ms"]))
    print(f"samples={len(internal)}")
    print(f"internal_median_ms={statistics.median(internal):.3f}")
    print(f"internal_min_ms={min(internal):.3f}")
    print(f"internal_max_ms={max(internal):.3f}")
    print(f"subprocess_wall_median_ms={statistics.median(wall):.3f}")
    print(f"subprocess_wall_min_ms={min(wall):.3f}")
    print(f"subprocess_wall_max_ms={max(wall):.3f}")


if __name__ == "__main__":
    main()

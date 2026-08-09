from pathlib import Path
import statistics
import tempfile
import time

from test_source_recognition_deterministic import make_task, pdb, run_tool


def main():
    internal = []
    wall = []
    for _ in range(20):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = pdb(root / "raw/input.pdb")
            task_path, _ = make_task(root, [source])
            started = time.perf_counter()
            code, out = run_tool(task_path)
            wall.append((time.perf_counter() - started) * 1000)
            if code != 0 or out.get("status") != "DONE":
                raise SystemExit(f"benchmark failed: {out}")
            log = (root / "01_structure_preparation/01_source_recognition/source_recognition.log").read_text()
            token = "elapsed_ms="
            internal.append(float(log.split(token)[-1].strip()))
    print(f"samples={len(internal)}")
    print(f"business_internal_median_ms={statistics.median(internal):.3f}")
    print(f"business_internal_min_ms={min(internal):.3f}")
    print(f"business_internal_max_ms={max(internal):.3f}")
    print(f"subprocess_wall_median_ms={statistics.median(wall):.3f}")
    print(f"subprocess_wall_min_ms={min(wall):.3f}")
    print(f"subprocess_wall_max_ms={max(wall):.3f}")


if __name__ == "__main__":
    main()

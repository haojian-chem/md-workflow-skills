import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "05_tools/runtime_dependency_preflight/check.py"
MANIFEST = "02_validators/component_and_residue_classification_validator/references/runtime_dependencies.json"


def main():
    internal = []
    wall = []
    for index in range(20):
        started = time.perf_counter()
        proc = subprocess.run([
            sys.executable, str(TOOL),
            "--skill-root", str(REPO_ROOT),
            "--manifest", MANIFEST,
            "--task-id", f"bench_{index}",
            "--workstream-id", "ws_bench",
            "--task-unit-mode", "VALIDATOR",
        ], text=True, capture_output=True)
        wall.append((time.perf_counter() - started) * 1000)
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)
        out = json.loads(proc.stdout)
        if out.get("status") != "PASS":
            raise SystemExit(str(out))
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

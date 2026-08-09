from pathlib import Path
import json
import statistics
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "05_tools/runtime_project_initializer/initialize.py"

samples = []
internal = []
with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    for i in range(12):
        root = base / f"project_{i}"
        root.mkdir()
        t0 = time.perf_counter()
        proc = subprocess.run([sys.executable, str(TOOL), "--project-root", str(root)], text=True, capture_output=True)
        wall = (time.perf_counter() - t0) * 1000
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)
        out = json.loads(proc.stdout)
        samples.append(wall)
        internal.append(float(out["elapsed_ms"]))
print(f"samples={len(samples)}")
print(f"subprocess_wall_median_ms={statistics.median(samples):.3f}")
print(f"subprocess_wall_min_ms={min(samples):.3f}")
print(f"subprocess_wall_max_ms={max(samples):.3f}")
print(f"initializer_internal_median_ms={statistics.median(internal):.3f}")

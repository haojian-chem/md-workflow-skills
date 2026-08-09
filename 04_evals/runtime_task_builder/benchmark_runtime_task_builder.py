from pathlib import Path
import json
import statistics
import subprocess
import sys
import tempfile
import time

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = REPO_ROOT / "05_tools/runtime_task_builder/build_task.py"


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")


def prepare(root: Path, i: int):
    source = root / f"input_{i}.pdb"
    source.write_text("HEADER    FIXTURE\nATOM      1  CA  ALA A   1       0.000   0.000   0.000\nEND\n", encoding="utf-8")
    ws = f"ws_{i:04d}"
    route_id = f"route_{i:04d}"
    route = root / f"00_project_records/workstreams/{ws}/routes/{route_id}.yaml"
    dump(route, {
        "schema_version": 3,
        "route_id": route_id,
        "workstream_id": ws,
        "steps": [{
            "sequence": 1,
            "workflow_name": "structure_preparation_workflow",
            "step_id": "source_recognition",
            "task_name": "source_recognition",
            "task_unit_mode": "OPERATION",
            "operation": {"skill_name": "source_recognition", "skill_path": "02_operations/source_recognition"},
            "validator": None,
            "necessity": "REQUIRED",
            "condition": None,
            "work_directory": "01_structure_preparation/01_source_recognition",
            "prerequisites": [],
            "expected_outputs": ["STRUCTURE"],
            "gate_requirements": ["DONE"],
        }],
    })
    return source, route


def main():
    samples = []
    validation = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i in range(20):
            source, route = prepare(root, i)
            started = time.perf_counter()
            proc = subprocess.run([
                sys.executable, str(BUILDER),
                "--project-root", str(root),
                "--route", str(route),
                "--source", str(source),
            ], text=True, capture_output=True)
            elapsed = (time.perf_counter() - started) * 1000
            if proc.returncode != 0:
                raise SystemExit(proc.stderr + proc.stdout)
            out = json.loads(proc.stdout)
            samples.append(elapsed)
            validation.append(float(out.get("validation_elapsed_ms") or 0.0))
    print(f"samples={len(samples)}")
    print(f"subprocess_wall_median_ms={statistics.median(samples):.3f}")
    print(f"subprocess_wall_min_ms={min(samples):.3f}")
    print(f"subprocess_wall_max_ms={max(samples):.3f}")
    print(f"validator_internal_median_ms={statistics.median(validation):.3f}")


if __name__ == "__main__":
    main()

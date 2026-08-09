import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_HELPERS = REPO_ROOT / "04_evals/initialization_candidate_validation/test_initialization_candidate_validation.py"
SRC_HELPERS = REPO_ROOT / "04_evals/source_recognition_deterministic/test_source_recognition_deterministic.py"
R4_HELPERS = REPO_ROOT / "04_evals/runtime_record_committer/test_runtime_record_committer.py"
SRC_TOOL = REPO_ROOT / "05_tools/source_recognition_deterministic/run.py"
R5_TOOL = REPO_ROOT / "05_tools/route_fast_path_evaluator/evaluate.py"
R4_TOOL = REPO_ROOT / "05_tools/runtime_record_committer/commit_records.py"
DEP_TOOL = REPO_ROOT / "05_tools/runtime_dependency_preflight/check.py"
RUNTIME_SPEC = REPO_ROOT / "runtime/workflows/structure_preparation.runtime.yaml"
DEP_MANIFEST = "02_validators/component_and_residue_classification_validator/references/runtime_dependencies.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


init_helpers = load_module("init_helpers", INIT_HELPERS)
src_helpers = load_module("src_helpers", SRC_HELPERS)
r4_helpers = load_module("r4_helpers", R4_HELPERS)


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def run_json(cmd):
    started = time.perf_counter()
    proc = subprocess.run(cmd, text=True, capture_output=True)
    elapsed = (time.perf_counter() - started) * 1000
    if not proc.stdout:
        raise RuntimeError(proc.stderr)
    payload = json.loads(proc.stdout)
    if proc.returncode != 0:
        raise RuntimeError(str(payload))
    return payload, elapsed


def one_iteration(index):
    times = {}

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        p, ws_candidate, ws_id = init_helpers.candidates(root)
        started = time.perf_counter()
        code, init_result = init_helpers.run_validator(root, "FAST", p, ws_candidate, ws_id)
        times["init_candidate_validation_wall_ms"] = (time.perf_counter() - started) * 1000
        if code != 0 or init_result.get("status") != "PASS":
            raise RuntimeError(str(init_result))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = src_helpers.pdb(root / "raw/input.pdb")
        task_path, ws = src_helpers.make_task(root, [source], route_id="route_0001")
        route_path = root / f"00_project_records/workstreams/{ws}/routes/route_0001.yaml"
        dump(route_path, src_helpers.route_record(ws))
        state_path = root / f"00_project_state/workstreams/{ws}.yaml"

        responsibility, times["stage_1_1_business_wall_ms"] = run_json([
            sys.executable, str(SRC_TOOL), "--task", str(task_path)
        ])
        if responsibility.get("status") != "DONE":
            raise RuntimeError(str(responsibility))
        responsibility_path = root / "responsibility.yaml"
        dump(responsibility_path, responsibility)

        context = {
            "schema_version": 1,
            "current_step_id": "source_recognition",
            "task_id": "task_0001",
            "gate_status": "PASS",
            "artifact_interface_status": "MATCH",
            "artifact_lineage_status": "OK",
            "route_affecting_evidence": False,
            "conditional_evidence_changed": False,
            "unexpected_output": False,
            "user_instruction_changed": False,
            "recovery_status": "NONE",
            "high_risk_barrier": False,
            "next_inputs_status": "READY",
            "next_condition_status": "NOT_APPLICABLE",
        }
        context_path = root / "fast_context.yaml"
        dump(context_path, context)
        fast, times["route_fast_path_wall_ms"] = run_json([
            sys.executable, str(R5_TOOL),
            "--route", str(route_path),
            "--workstream-state", str(state_path),
            "--result", str(responsibility_path),
            "--runtime-spec", str(RUNTIME_SPEC),
            "--context", str(context_path),
        ])
        if fast.get("decision") != "ADVANCE":
            raise RuntimeError(str(fast))

        req = r4_helpers.request(
            "task_0001", ws, responsibility,
            route_id="route_0001",
            route_progression={"action": "SET", "position": fast["next_route_position"]},
        )
        req["artifact_updates"] = [{
            "candidate_index": 0,
            "artifact_set_id": f"aset_{index:04d}_structure",
            "validation_status": "UNVALIDATED",
            "validator_task_id": None,
            "supersedes": [],
            "notes": "runtime fixed-path benchmark",
            "current_state_action": "REPLACE_TYPE",
        }]
        request_path = root / "commit_request.yaml"
        dump(request_path, req)
        receipt, times["record_commit_wall_ms"] = run_json([
            sys.executable, str(R4_TOOL),
            "--project-root", str(root),
            "--skill-root", str(REPO_ROOT),
            "--request", str(request_path),
        ])
        if receipt.get("status") != "COMMITTED":
            raise RuntimeError(str(receipt))

        dep, times["stage_1_2_dependency_preflight_wall_ms"] = run_json([
            sys.executable, str(DEP_TOOL),
            "--skill-root", str(REPO_ROOT),
            "--manifest", DEP_MANIFEST,
            "--task-id", "task_0002",
            "--workstream-id", ws,
            "--task-unit-mode", "VALIDATOR",
        ])
        if dep.get("status") != "PASS":
            raise RuntimeError(str(dep))

    times["deterministic_fixed_path_total_wall_ms"] = sum(times.values())
    return times


def main():
    samples = [one_iteration(i) for i in range(10)]
    keys = list(samples[0])
    print("scope=deterministic runtime fixed path only")
    print("excludes=Manager route-scope reasoning, route/task record construction, user-visible response generation, and stage-1.2 scientific Agent execution")
    print(f"samples={len(samples)}")
    for key in keys:
        values = [sample[key] for sample in samples]
        print(f"{key}_median={statistics.median(values):.3f}")
        print(f"{key}_min={min(values):.3f}")
        print(f"{key}_max={max(values):.3f}")


if __name__ == "__main__":
    main()

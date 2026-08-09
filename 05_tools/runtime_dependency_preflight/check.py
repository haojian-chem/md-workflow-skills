#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

VERSION = "0.1.0"


class PreflightError(RuntimeError):
    pass


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def safe_rel(value: str, label: str) -> Path:
    p = Path(value)
    if p.is_absolute() or not p.parts or any(part == ".." for part in p.parts):
        raise PreflightError(f"{label} must be a safe relative path: {value!r}")
    return p


def guarded_file(skill_root: Path, item: dict[str, Any], label: str) -> Path:
    if not isinstance(item, dict):
        raise PreflightError(f"{label} must be a mapping")
    path_value = item.get("path")
    expected = item.get("expected_git_blob_sha")
    if not isinstance(path_value, str) or not isinstance(expected, str) or not expected:
        raise PreflightError(f"{label} requires path and expected_git_blob_sha")
    path = skill_root / safe_rel(path_value, f"{label}.path")
    if not path.is_file() or path.is_symlink():
        raise PreflightError(f"guarded {label} file missing or invalid: {path_value}")
    actual = git_blob_sha(path.read_bytes())
    if actual != expected:
        raise PreflightError(f"{label.upper()}_GUARD_MISMATCH: {path_value}: expected {expected}, got {actual}")
    return path


def load_manifest(skill_root: Path, manifest_arg: str) -> tuple[dict[str, Any], Path]:
    manifest_path = Path(manifest_arg)
    if not manifest_path.is_absolute():
        manifest_path = skill_root / safe_rel(manifest_arg, "manifest")
    manifest_path = manifest_path.resolve()
    try:
        manifest_path.relative_to(skill_root.resolve())
    except ValueError as exc:
        raise PreflightError("manifest must be inside skill root") from exc
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise PreflightError(f"manifest missing or invalid: {manifest_path}")
    try:
        obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreflightError(f"cannot parse dependency manifest JSON: {exc}") from exc
    if not isinstance(obj, dict) or obj.get("schema_version") != 1:
        raise PreflightError("unsupported dependency manifest")
    return obj, manifest_path


def release_tuple(version: str) -> tuple[int, ...]:
    base = version.split("+")[0]
    pieces = re.findall(r"\d+", base)
    if not pieces:
        raise PreflightError(f"cannot compare non-numeric distribution version: {version!r}")
    return tuple(int(x) for x in pieces[:6])


def cmp_release(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    size = max(len(left), len(right))
    a = left + (0,) * (size - len(left))
    b = right + (0,) * (size - len(right))
    return (a > b) - (a < b)


def version_satisfies(version: str, spec: str) -> bool:
    current = release_tuple(version)
    for clause in (part.strip() for part in spec.split(",") if part.strip()):
        match = re.fullmatch(r"(>=|<=|==|>|<)\s*([0-9]+(?:\.[0-9]+)*)", clause)
        if not match:
            raise PreflightError(f"unsupported version specifier: {clause!r}")
        op, target_text = match.groups()
        target = tuple(int(x) for x in target_text.split("."))
        relation = cmp_release(current, target)
        ok = {
            ">=": relation >= 0,
            "<=": relation <= 0,
            "==": relation == 0,
            ">": relation > 0,
            "<": relation < 0,
        }[op]
        if not ok:
            return False
    return True


def validate_manifest(skill_root: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    owner = manifest.get("owner_skill")
    if not isinstance(owner, dict):
        raise PreflightError("owner_skill missing")
    for key in ("skill_name", "path", "expected_git_blob_sha", "task_unit_mode"):
        if not isinstance(owner.get(key), str) or not owner[key]:
            raise PreflightError(f"owner_skill.{key} missing")
    if owner["task_unit_mode"] not in {"OPERATION", "VALIDATOR", "OPERATION_WITH_VALIDATOR"}:
        raise PreflightError("owner_skill.task_unit_mode invalid")
    guarded_file(skill_root, owner, "owner_skill")
    requirements = manifest.get("requirements_source")
    guarded_file(skill_root, requirements, "requirements_source")
    dependencies = manifest.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise PreflightError("dependencies must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for dep in dependencies:
        if not isinstance(dep, dict):
            raise PreflightError("dependency entry must be a mapping")
        for key in ("import_name", "distribution_name", "version_spec"):
            if not isinstance(dep.get(key), str) or not dep[key]:
                raise PreflightError(f"dependency {key} missing")
        normalized.append(dep)
    return owner, normalized


def check_dependency(dep: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "import_name": dep["import_name"],
        "distribution_name": dep["distribution_name"],
        "required_version": dep["version_spec"],
        "installed_version": None,
        "status": None,
        "error": None,
    }
    try:
        importlib.import_module(dep["import_name"])
    except Exception as exc:
        result["status"] = "MISSING_OR_IMPORT_FAILED"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    try:
        installed = importlib.metadata.version(dep["distribution_name"])
    except importlib.metadata.PackageNotFoundError:
        result["status"] = "DISTRIBUTION_METADATA_MISSING"
        return result
    result["installed_version"] = installed
    if version_satisfies(installed, dep["version_spec"]):
        result["status"] = "PASS"
    else:
        result["status"] = "VERSION_INCOMPATIBLE"
    return result


def component(skill_name: str, summary: str, outcome: str) -> dict[str, Any]:
    return {
        "skill_name": skill_name,
        "status": "BLOCKED",
        "summary": summary,
        "outcome_code": outcome,
        "key_findings": [],
        "created_files": [],
        "modified_files": [],
        "validated_files": [],
        "warnings": [],
        "failure": None,
        "detail_files": {"log_file": None, "report_file": None, "result_data_file": None},
    }


def blocker_result(owner: dict[str, Any], task_id: str, workstream_id: str, summary: str, outcome: str, dependency_results: list[dict[str, Any]]) -> dict[str, Any]:
    result = {
        "schema_version": 2,
        "task_id": task_id,
        "workstream_id": workstream_id,
        "task_unit_mode": owner["task_unit_mode"],
        "status": "BLOCKED",
        "execution_summary": summary,
        "operation_result": None,
        "validation_result": None,
        "artifact_candidates": [],
        "confirmation_items": [],
        "warnings": [],
        "failure": None,
        "next_step_recommendation": "Install or repair the declared runtime dependencies, then create a new task/retry according to Manager policy.",
    }
    comp = component(owner["skill_name"], summary, outcome)
    if owner["task_unit_mode"] == "OPERATION":
        result["operation_result"] = comp
    elif owner["task_unit_mode"] == "VALIDATOR":
        result["validation_result"] = comp
    else:
        raise PreflightError("generic dependency blocker does not synthesize OPERATION_WITH_VALIDATOR results")
    result["dependency_preflight"] = dependency_results
    return result


def run(skill_root: Path, manifest_arg: str, task_id: str, workstream_id: str, task_unit_mode: str) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    try:
        if not skill_root.is_dir():
            raise PreflightError(f"skill root is not a directory: {skill_root}")
        if not task_id or not workstream_id:
            raise PreflightError("task_id and workstream_id are required")
        manifest, manifest_path = load_manifest(skill_root, manifest_arg)
        owner, dependencies = validate_manifest(skill_root, manifest)
        if task_unit_mode != owner["task_unit_mode"]:
            raise PreflightError(f"task_unit_mode mismatch: expected {owner['task_unit_mode']}, got {task_unit_mode}")
        checked = [check_dependency(dep) for dep in dependencies]
        blocked = [item for item in checked if item["status"] != "PASS"]
        if blocked:
            blocked_cfg = manifest.get("blocked_outcome") or {}
            outcome = blocked_cfg.get("outcome_code", "MISSING_RUNTIME_DEPENDENCY")
            summary = blocked_cfg.get("summary", "Runtime dependencies are missing or incompatible; business execution was not started.")
            responsibility = blocker_result(owner, task_id, workstream_id, summary, outcome, checked)
            return 0, {
                "status": "BLOCKED",
                "owner_skill": owner["skill_name"],
                "manifest": manifest_path.relative_to(skill_root.resolve()).as_posix(),
                "dependencies": checked,
                "blocked_dependencies": blocked,
                "responsibility_result": responsibility,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            }
        return 0, {
            "status": "PASS",
            "owner_skill": owner["skill_name"],
            "manifest": manifest_path.relative_to(skill_root.resolve()).as_posix(),
            "dependencies": checked,
            "blocked_dependencies": [],
            "responsibility_result": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    except Exception as exc:
        return 2, {
            "status": "ERROR",
            "errors": [str(exc)],
            "responsibility_result": None,
            "tool_version": VERSION,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight Python runtime dependencies before expensive Agent context creation")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--workstream-id", required=True)
    parser.add_argument("--task-unit-mode", required=True, choices=("OPERATION", "VALIDATOR", "OPERATION_WITH_VALIDATOR"))
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code, payload = run(Path(args.skill_root).resolve(), args.manifest, args.task_id, args.workstream_id, args.task_unit_mode)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

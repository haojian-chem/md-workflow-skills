#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any

import yaml

PASS = 0
VALIDATION_FAILURE = 1
TOOL_FAILURE = 2


class ProjectionError(Exception):
    pass


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relpath(value: str, label: str) -> Path:
    p = Path(value)
    if p.is_absolute() or any(part == ".." for part in p.parts):
        raise ProjectionError(f"{label} must be a safe relative path: {value}")
    if not p.parts:
        raise ProjectionError(f"{label} must not be empty")
    return p


def read_bytes(root: Path, rel: str) -> bytes:
    p = root / safe_relpath(rel, "source path")
    if not p.is_file() or p.is_symlink():
        raise ProjectionError(f"required regular source file missing or invalid: {rel}")
    return p.read_bytes()


def read_yaml(root: Path, rel: str) -> dict[str, Any]:
    raw = read_bytes(root, rel)
    try:
        obj = yaml.safe_load(raw)
    except Exception as exc:
        raise ProjectionError(f"invalid YAML in {rel}: {exc}") from exc
    if not isinstance(obj, dict):
        raise ProjectionError(f"YAML root must be a mapping: {rel}")
    return obj


def yaml_bytes(obj: Any) -> bytes:
    text = yaml.safe_dump(
        obj,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def fingerprint(root: Path, rel: str) -> dict[str, str]:
    data = read_bytes(root, rel)
    return {"path": rel, "git_blob_sha": git_blob_sha(data)}


def check_source_guards(root: Path, owner_rel: str, owner: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    guards = owner.get("source_guards", [])
    if guards is None:
        guards = []
    if not isinstance(guards, list):
        raise ProjectionError(f"source_guards must be a list in {owner_rel}")
    for item in guards:
        if not isinstance(item, dict) or "path" not in item or "expected_git_blob_sha" not in item:
            raise ProjectionError(f"invalid source guard in {owner_rel}: {item!r}")
        rel = str(item["path"])
        expected = str(item["expected_git_blob_sha"])
        try:
            actual = fingerprint(root, rel)["git_blob_sha"]
        except ProjectionError as exc:
            errors.append({"owner": owner_rel, "path": rel, "reason": str(exc)})
            continue
        if actual != expected:
            errors.append({
                "owner": owner_rel,
                "path": rel,
                "reason": "SOURCE_GUARD_MISMATCH",
                "expected_git_blob_sha": expected,
                "actual_git_blob_sha": actual,
            })
    return errors


def build_spec(root: Path, source_rel: str, kind: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source = read_yaml(root, source_rel)
    guard_errors = check_source_guards(root, source_rel, source)
    payload = source.get("runtime_spec")
    if not isinstance(payload, dict):
        raise ProjectionError(f"runtime_spec mapping missing in {source_rel}")
    out = copy.deepcopy(payload)
    guarded_sources = [fingerprint(root, str(item["path"])) for item in source.get("source_guards", [])]
    out["projection"] = {
        "generated": True,
        "source": fingerprint(root, source_rel),
        "guarded_sources": guarded_sources,
        "kind": kind,
    }
    return out, guard_errors


def build_contract_index(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    contract_cfg = config.get("contracts")
    if not isinstance(contract_cfg, dict):
        raise ProjectionError("config.contracts must be a mapping")
    include = contract_cfg.get("include")
    if not isinstance(include, dict) or not include:
        raise ProjectionError("config.contracts.include must be a non-empty mapping")
    contracts: dict[str, Any] = {}
    for name, rel_value in include.items():
        rel = str(rel_value)
        fp = fingerprint(root, rel)
        contracts[str(name)] = {
            "path": rel,
            "git_blob_sha": fp["git_blob_sha"],
            "llm_reads_body_by_default": False,
        }
    return {
        "schema_version": 1,
        "index_status": "generated_active",
        "purpose": "Runtime index of contract identities. Normal MD runtime passes contract paths or identifiers to deterministic validators/builders instead of loading schema bodies into LLM context.",
        "contracts": contracts,
        "consumer_policy": copy.deepcopy(contract_cfg.get("consumer_policy", {})),
        "notes": copy.deepcopy(contract_cfg.get("notes", [])),
        "projection": {"generated": True, "source": fingerprint(root, str(config["config_path"]))},
    }


def runtime_ref(config: dict[str, Any], rel: str) -> str:
    root = str(config["runtime_root"]).rstrip("/")
    return f"{root}/{rel.lstrip('/')}"


def build_stage_projection(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    stage_rel = str(config["stage_registry"])
    registry = read_yaml(root, stage_rel)
    stages = registry.get("stage_order")
    if not isinstance(stages, list):
        raise ProjectionError(f"stage_order missing in {stage_rel}")
    workflow_outputs = {
        str(item["workflow_name"]): str(item["output"])
        for item in config.get("workflows", [])
        if isinstance(item, dict) and "workflow_name" in item and "output" in item
    }
    result: list[dict[str, Any]] = []
    for stage in stages:
        if not isinstance(stage, dict):
            raise ProjectionError(f"invalid stage entry in {stage_rel}")
        workflow_name = str(stage.get("workflow_name"))
        result.append({
            "stage_id": stage.get("stage_id"),
            "workflow_name": workflow_name,
            "project_directory": stage.get("project_directory"),
            "connection_status": stage.get("connection_status"),
            "runtime_spec": runtime_ref(config, workflow_outputs[workflow_name]) if workflow_name in workflow_outputs else None,
        })
    return result


def build_manifest(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    manifest_cfg = config.get("manifest")
    if not isinstance(manifest_cfg, dict):
        raise ProjectionError("config.manifest must be a mapping")
    provenance_paths: list[str] = [str(config["config_path"])]
    provenance_paths.extend(str(x) for x in config.get("provenance_sources", []))
    provenance_paths.append(str(config["manager"]["source"]))
    provenance_paths.extend(str(x["source"]) for x in config.get("workflows", []))
    provenance_paths.append(str(config["stage_registry"]))
    provenance_paths.append(str(config["tool_registry"]))
    provenance_paths.extend(str(x) for x in config["contracts"]["include"].values())
    seen: set[str] = set()
    provenance: list[dict[str, str]] = []
    for rel in provenance_paths:
        if rel in seen:
            continue
        seen.add(rel)
        provenance.append(fingerprint(root, rel))
    workflow_specs = {
        str(item["workflow_name"]): runtime_ref(config, str(item["output"]))
        for item in config.get("workflows", [])
    }
    return {
        "schema_version": 1,
        "projection_status": "generated_active",
        "projection_mode": "deterministic_compiled",
        "purpose": manifest_cfg.get("purpose"),
        "authority": copy.deepcopy(manifest_cfg.get("authority", {})),
        "provenance": {"branch_label": config.get("branch_label"), "sources": provenance},
        "runtime_entry": {
            "manager_spec": runtime_ref(config, str(config["manager"]["output"])),
            "contract_index": runtime_ref(config, str(config["contracts"]["output"])),
            "tool_registry": str(config["tool_registry"]),
            "workflow_specs": workflow_specs,
        },
        "loading_policy": copy.deepcopy(manifest_cfg.get("loading_policy", {})),
        "execution_backends": copy.deepcopy(manifest_cfg.get("execution_backends", {})),
        "foreground_agent_limit": manifest_cfg.get("foreground_agent_limit", 1),
        "stage_registry_projection": build_stage_projection(root, config),
        "runtime_guards": copy.deepcopy(manifest_cfg.get("runtime_guards", [])),
    }


def validate_config(root: Path, config_rel: str, config: dict[str, Any]) -> dict[str, Any]:
    config = copy.deepcopy(config)
    config["config_path"] = config_rel
    if config.get("schema_version") != 1:
        raise ProjectionError("unsupported runtime projection config schema_version")
    for key in ("runtime_root", "manifest_output", "manager", "workflows", "contracts", "stage_registry", "tool_registry"):
        if key not in config:
            raise ProjectionError(f"missing config key: {key}")
    safe_relpath(str(config["runtime_root"]), "runtime_root")
    safe_relpath(str(config["manifest_output"]), "manifest_output")
    if not isinstance(config["manager"], dict):
        raise ProjectionError("manager config must be a mapping")
    for key in ("source", "output"):
        if key not in config["manager"]:
            raise ProjectionError(f"manager.{key} missing")
    if not isinstance(config["workflows"], list):
        raise ProjectionError("workflows must be a list")
    if not isinstance(config["contracts"], dict) or "output" not in config["contracts"]:
        raise ProjectionError("contracts.output missing")
    return config


def output_path(skill_root: Path, runtime_root_rel: str, rel: str) -> Path:
    runtime_root = (skill_root / safe_relpath(runtime_root_rel, "runtime_root")).resolve()
    out = (runtime_root / safe_relpath(rel, "output path")).resolve()
    try:
        out.relative_to(runtime_root)
    except ValueError as exc:
        raise ProjectionError(f"output escapes runtime root: {rel}") from exc
    return out


def build_all(skill_root: Path, config_rel: str) -> tuple[dict[Path, bytes], list[dict[str, str]], dict[str, Any]]:
    cfg = validate_config(skill_root, config_rel, read_yaml(skill_root, config_rel))
    runtime_root_rel = str(cfg["runtime_root"])
    outputs: dict[Path, bytes] = {}
    guard_errors: list[dict[str, str]] = []
    manager_obj, errors = build_spec(skill_root, str(cfg["manager"]["source"]), "manager")
    guard_errors.extend(errors)
    outputs[output_path(skill_root, runtime_root_rel, str(cfg["manager"]["output"]))] = yaml_bytes(manager_obj)
    for item in cfg["workflows"]:
        if not isinstance(item, dict) or not all(k in item for k in ("workflow_name", "source", "output")):
            raise ProjectionError(f"invalid workflow config item: {item!r}")
        obj, errors = build_spec(skill_root, str(item["source"]), "workflow")
        guard_errors.extend(errors)
        outputs[output_path(skill_root, runtime_root_rel, str(item["output"]))] = yaml_bytes(obj)
    outputs[output_path(skill_root, runtime_root_rel, str(cfg["contracts"]["output"]))] = yaml_bytes(build_contract_index(skill_root, cfg))
    outputs[output_path(skill_root, runtime_root_rel, str(cfg["manifest_output"]))] = yaml_bytes(build_manifest(skill_root, cfg))
    return outputs, guard_errors, cfg


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def run(skill_root: Path, config_rel: str, mode: str) -> tuple[int, dict[str, Any]]:
    start = time.perf_counter()
    try:
        outputs, guard_errors, _cfg = build_all(skill_root, config_rel)
        if guard_errors:
            return VALIDATION_FAILURE, {"status": "FAIL", "mode": mode, "guard_errors": guard_errors, "errors": [], "changed": [], "drift": [], "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)}
        changed: list[str] = []
        drift: list[dict[str, str]] = []
        for path, expected in outputs.items():
            rel = str(path.relative_to(skill_root.resolve()))
            actual = path.read_bytes() if path.is_file() else None
            if actual != expected:
                drift.append({"path": rel, "reason": "MISSING" if actual is None else "CONTENT_MISMATCH", "expected_sha256": sha256(expected), "actual_sha256": sha256(actual) if actual is not None else ""})
                if mode == "BUILD":
                    atomic_write(path, expected)
                    changed.append(rel)
        if mode == "CHECK" and drift:
            code, status = VALIDATION_FAILURE, "DRIFT"
        else:
            code, status = PASS, "PASS"
        return code, {"status": status, "mode": mode, "guard_errors": [], "errors": [], "changed": changed, "drift": drift, "outputs": [str(p.relative_to(skill_root.resolve())) for p in outputs], "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)}
    except ProjectionError as exc:
        return TOOL_FAILURE, {"status": "ERROR", "mode": mode, "guard_errors": [], "errors": [str(exc)], "changed": [], "drift": [], "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)}
    except Exception as exc:
        return TOOL_FAILURE, {"status": "ERROR", "mode": mode, "guard_errors": [], "errors": [f"unexpected error: {type(exc).__name__}: {exc}"], "changed": [], "drift": [], "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile compact MD Workflow runtime projections")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--config", default="00_authoring/runtime_projection_config.yaml", help="path relative to skill root")
    parser.add_argument("--mode", choices=("BUILD", "CHECK"), default="CHECK")
    parser.add_argument("--output", help="optional JSON result path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = Path(args.skill_root).resolve()
    if not skill_root.is_dir():
        result = {"status": "ERROR", "mode": args.mode, "errors": ["skill root does not exist"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return TOOL_FAILURE
    code, result = run(skill_root, args.config, args.mode)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

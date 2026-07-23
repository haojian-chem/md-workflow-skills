from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "05_tools/runtime_schema_validator/validate.py"


def write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def run_tool(project_root: Path, mode: str, *changed: str) -> tuple[int, dict]:
    command = [
        sys.executable,
        str(TOOL),
        "--project-root",
        str(project_root),
        "--mode",
        mode,
    ]
    if changed:
        command.extend(["--changed", *changed])
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return completed.returncode, json.loads(completed.stdout)


def install_synthetic_contracts(project_root: Path) -> None:
    contracts = project_root / "03_contracts"
    write_yaml(
        contracts / "project_state.schema.yaml",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "project_state.schema.yaml",
            "type": "object",
            "required": ["value", "workstreams"],
            "properties": {
                "value": {"type": "integer"},
                "workstreams": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["state_path"],
                        "properties": {"state_path": {"type": "string"}},
                        "additionalProperties": False,
                    },
                },
            },
            "additionalProperties": False,
        },
    )
    write_yaml(
        contracts / "workstream_state.schema.yaml",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "workstream_state.schema.yaml",
            "type": "object",
            "required": ["value"],
            "properties": {"value": {"type": "integer"}},
            "additionalProperties": False,
        },
    )


def test_fast_ignores_unrelated_invalid_record_and_cache_hits(tmp_path: Path) -> None:
    install_synthetic_contracts(tmp_path)
    write_yaml(
        tmp_path / "00_project_state/project_state.yaml",
        {"value": 1, "workstreams": []},
    )
    write_yaml(
        tmp_path / "00_project_state/workstreams/ws_bad.yaml",
        {"value": "invalid"},
    )

    code1, result1 = run_tool(tmp_path, "FAST", "00_project_state/project_state.yaml")
    code2, result2 = run_tool(tmp_path, "FAST", "00_project_state/project_state.yaml")

    assert code1 == 0
    assert result1["status"] == "PASS"
    assert result1["schema_cache_hit"] is False
    assert code2 == 0
    assert result2["status"] == "PASS"
    assert result2["schema_cache_hit"] is True
    assert all("ws_bad.yaml" not in item["path"] for item in result2["validated"])


def test_full_finds_unrelated_invalid_record(tmp_path: Path) -> None:
    install_synthetic_contracts(tmp_path)
    write_yaml(
        tmp_path / "00_project_state/project_state.yaml",
        {"value": 1, "workstreams": []},
    )
    write_yaml(
        tmp_path / "00_project_state/workstreams/ws_bad.yaml",
        {"value": "invalid"},
    )

    code, result = run_tool(tmp_path, "FULL")

    assert code == 1
    assert result["status"] == "FAIL"
    assert any("ws_bad.yaml" in item.get("file", "") for item in result["errors"])


def test_fast_reports_missing_direct_reference(tmp_path: Path) -> None:
    install_synthetic_contracts(tmp_path)
    write_yaml(
        tmp_path / "00_project_state/project_state.yaml",
        {
            "value": 1,
            "workstreams": [
                {"state_path": "00_project_state/workstreams/ws_missing.yaml"}
            ],
        },
    )

    code, result = run_tool(tmp_path, "FAST", "00_project_state/project_state.yaml")

    assert code == 1
    assert result["status"] == "FAIL"
    assert any(item.get("schema_path") == "direct_reference" for item in result["errors"])


def test_schema_change_invalidates_cache(tmp_path: Path) -> None:
    install_synthetic_contracts(tmp_path)
    write_yaml(
        tmp_path / "00_project_state/project_state.yaml",
        {"value": 1, "workstreams": []},
    )

    code1, result1 = run_tool(tmp_path, "FAST", "00_project_state/project_state.yaml")
    assert code1 == 0
    assert result1["schema_cache_hit"] is False

    schema_path = tmp_path / "03_contracts/project_state.schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    schema["description"] = "changed schema bundle"
    write_yaml(schema_path, schema)

    code2, result2 = run_tool(tmp_path, "FAST", "00_project_state/project_state.yaml")
    assert code2 == 0
    assert result2["schema_cache_hit"] is False
    assert result2["schema_bundle_hash"] != result1["schema_bundle_hash"]

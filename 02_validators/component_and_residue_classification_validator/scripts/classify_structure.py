#!/usr/bin/env python3
"""Run the selected-model baseline component and residue classification pass."""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    read_yaml_strict,
    validate_document,
)
from classification_engine import execute_classification
from observation_state import normalize_baseline_observations

VERSION = "1.1.0"


def _same_name_terminal_defaults(config: dict, script_dir: Path) -> list[dict[str, str]]:
    classification = config["classification"]
    registry_path = Path(
        classification.get(
            "standard_registry_path",
            script_dir.parent / "references/standard_residue_registry.yaml",
        )
    ).resolve()
    registry = read_yaml_strict(registry_path)
    names = [
        entry["residue_name"]
        for entry in registry.get("residue_definitions", [])
        if entry.get("polymer_class") == "POLYMER"
    ]
    mappings: list[dict[str, str]] = []
    for name in names:
        for role in ("N_TERMINUS", "C_TERMINUS", "FIVE_PRIME", "THREE_PRIME"):
            mappings.append(
                {
                    "terminal_role": role,
                    "source_residue_name": name,
                    "rtp_residue_name": name,
                }
            )
    return mappings


def _engine_config(config: dict, script_dir: Path) -> dict:
    runtime = copy.deepcopy(config)
    ccd = config.get("ccd") or {}
    libraries = [
        script_dir.parent / "references/ccd_library",
        *(Path(value).resolve() for value in ccd.get("additional_library_paths", [])),
    ]
    runtime["ccd"] = {
        "project_snapshot_dir": str(script_dir.parent / "references/ccd_library"),
        "local_reference_dirs": [str(path.resolve()) for path in libraries],
        "shared_cache_path": None,
        "retrieval_policy": "INDEXED_ONLY",
    }
    runtime["output"] = copy.deepcopy(config["output"])
    runtime["output"]["observations_schema"] = str(
        script_dir.parent / "schemas/classification_observations_engine.schema.yaml"
    )
    if runtime.get("force_field"):
        force_field = runtime["force_field"]
        explicit = list(force_field.get("terminal_template_mappings", []) or [])
        existing = {
            (item["source_residue_name"], item["terminal_role"])
            for item in explicit
        }
        defaults = [
            item
            for item in _same_name_terminal_defaults(config, script_dir)
            if (item["source_residue_name"], item["terminal_role"]) not in existing
        ]
        force_field["terminal_template_mappings"] = [*explicit, *defaults]
    return runtime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    try:
        config = read_yaml_strict(args.config.resolve())
        if not isinstance(config, dict):
            raise ClassificationToolError("classification config must be a YAML mapping")
        validate_document(
            config,
            script_dir.parent / "schemas/classification_config.schema.yaml",
        )
        runtime = _engine_config(config, script_dir)
        (
            observations,
            manifest,
            observations_path,
            manifest_path,
            _engine_observations_schema,
            _manifest_schema,
        ) = execute_classification(runtime, script_dir)
        observations = normalize_baseline_observations(observations, config, script_dir)
        observations_schema = Path(
            config["output"].get(
                "observations_schema",
                script_dir.parent / "schemas/classification_observations.schema.yaml",
            )
        ).resolve()
        validate_document(observations, observations_schema)
        validate_document(
            manifest,
            Path(
                config["output"].get(
                    "reference_manifest_schema",
                    script_dir.parent / "schemas/reference_manifest.schema.yaml",
                )
            ).resolve(),
        )
        atomic_write_yaml(observations_path, observations)
        atomic_write_yaml(manifest_path, manifest)
        return 0
    except ClassificationToolError as exc:
        print(f"classify_structure.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"classify_structure.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

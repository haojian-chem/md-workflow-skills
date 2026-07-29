#!/usr/bin/env python3
"""Run the selected-model baseline component and residue classification pass."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from af3_server_sequence_reference import install_af3_server_sequence_reference
from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    read_yaml_strict,
)
from classification_engine import execute_classification

install_af3_server_sequence_reference()

VERSION = "0.2.0-draft"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse one already-selected model, classify residues with exact-name "
            "rules, inspect missing residues and heavy atoms, and write baseline "
            "classification observations plus a reference manifest."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="YAML configuration for the selected-model classification pass.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    try:
        config = read_yaml_strict(args.config.resolve())
        if not isinstance(config, dict):
            raise ClassificationToolError("classification config must be a YAML mapping")
        (
            observations,
            manifest,
            observations_path,
            manifest_path,
            _observations_schema,
            _manifest_schema,
        ) = execute_classification(config, script_dir)
        atomic_write_yaml(observations_path, observations)
        atomic_write_yaml(manifest_path, manifest)
        return 0
    except ClassificationToolError as exc:
        print(f"classify_structure.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"classify_structure.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

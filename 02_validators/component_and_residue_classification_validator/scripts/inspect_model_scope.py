#!/usr/bin/env python3
"""Inspect structure models without performing residue classification."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    inspect_models,
    parse_structure,
    read_yaml_strict,
    require_selected_model,
    require_sha256,
    validate_document,
    verify_source_format,
)

VERSION = "1.0.0"


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    structure_path = args.structure.resolve()
    observed_hash = require_sha256(structure_path, args.structure_sha256)
    structure = parse_structure(structure_path)
    verify_source_format(structure_path, structure, args.source_format)
    models = inspect_models(structure)

    if len(models) == 1:
        only_model = str(models[0]["model_id"])
        if args.selected_model_id is not None and args.selected_model_id != only_model:
            raise ClassificationToolError(
                f"single-model structure contains model {only_model}, not requested model {args.selected_model_id}"
            )
        selection = {
            "status": "AUTO_SELECTED",
            "selected_model_id": only_model,
        }
    elif args.selected_model_id is None:
        selection = {
            "status": "USER_SELECTION_REQUIRED",
            "selected_model_id": None,
        }
    else:
        require_selected_model(models, args.selected_model_id)
        selection = {
            "status": "USER_SELECTED",
            "selected_model_id": args.selected_model_id,
        }

    return {
        "schema_version": "1.0",
        "input_structure": {
            "path": str(structure_path),
            "sha256": observed_hash,
            "source_format": args.source_format,
        },
        "model_count": len(models),
        "models": models,
        "selection": selection,
    }


def _replacement_allowed(output: Path, new_document: dict[str, Any]) -> bool:
    if not output.exists():
        return False
    old = read_yaml_strict(output)
    if not isinstance(old, dict):
        return False
    immutable_keys = ("schema_version", "input_structure", "model_count", "models")
    if any(old.get(key) != new_document.get(key) for key in immutable_keys):
        return False
    old_selection = old.get("selection", {})
    new_selection = new_document.get("selection", {})
    return (
        old_selection.get("status") == "USER_SELECTION_REQUIRED"
        and old_selection.get("selected_model_id") is None
        and new_selection.get("status") == "USER_SELECTED"
        and isinstance(new_selection.get("selected_model_id"), str)
    )


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Enumerate model IDs and minimal coordinate counts for classification scope selection."
    )
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--structure-sha256", required=True)
    parser.add_argument(
        "--source-format",
        choices=("PDB", "MMCIF", "AF3_CIF"),
        required=True,
    )
    parser.add_argument("--selected-model-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--schema",
        type=Path,
        default=script_dir.parent / "schemas" / "model_scope.schema.yaml",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        document = build_result(args)
        validate_document(document, args.schema.resolve())
        output = args.output.resolve()
        allow_replace = _replacement_allowed(output, document)
        atomic_write_yaml(output, document, allow_replace=allow_replace)
        return 0
    except ClassificationToolError as exc:
        print(f"inspect_model_scope.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive boundary
        print(f"inspect_model_scope.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Enumerate structure models and write model_scope.yaml."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationError,
    atomic_yaml,
    model_id,
    read_structure,
    require_hash,
    source_format,
    validate_document,
)

VERSION = "1.0.0"


def inspect(
    structure_path: Path,
    *,
    expected_sha256: str | None,
    declared_format: str | None,
    selected_model_id: str | None = None,
) -> dict[str, Any]:
    actual_hash = require_hash(structure_path, expected_sha256, "structure")
    structure = read_structure(structure_path)
    fmt = source_format(structure_path, structure, declared_format)

    ids = [model_id(model) for model in structure]
    if len(ids) != len(set(ids)):
        raise ClassificationError("model identifiers are not unique")

    models: list[dict[str, Any]] = []
    for model in structure:
        residue_count = 0
        atom_count = 0
        for chain in model:
            for residue in chain:
                residue_count += 1
                atom_count += len(residue)
        if atom_count == 0:
            raise ClassificationError(f"model {model_id(model)} contains no coordinate atoms")
        models.append(
            {
                "model_id": model_id(model),
                "chain_count": len(model),
                "residue_count": residue_count,
                "atom_count": atom_count,
            }
        )

    if selected_model_id is not None:
        selected = str(selected_model_id)
        if selected not in ids:
            raise ClassificationError(f"selected model does not exist: {selected}")
        selection = {"status": "USER_SELECTED" if len(ids) > 1 else "AUTO_SELECTED", "selected_model_id": selected}
    elif len(ids) == 1:
        selection = {"status": "AUTO_SELECTED", "selected_model_id": ids[0]}
    else:
        selection = {"status": "USER_SELECTION_REQUIRED", "selected_model_id": None}

    return {
        "schema_version": "1.0",
        "tool": {"name": "inspect_model_scope", "version": VERSION},
        "input_structure": {
            "path": str(structure_path),
            "sha256": actual_hash,
            "source_format": fmt,
        },
        "model_count": len(models),
        "models": models,
        "selection": selection,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--structure-sha256")
    parser.add_argument("--source-format", choices=["PDB", "MMCIF", "AF3_CIF"])
    parser.add_argument("--selected-model-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = inspect(
            args.structure,
            expected_sha256=args.structure_sha256,
            declared_format=args.source_format,
            selected_model_id=args.selected_model_id,
        )
        validate_document(document, args.schema)
        atomic_yaml(args.output, document)
    except ClassificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

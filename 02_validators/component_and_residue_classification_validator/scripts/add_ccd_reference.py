#!/usr/bin/env python3
"""Add one validated CCD-compatible CIF to an explicitly selected library."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from ccd_reference import component_id_from_cif, parse_ccd_file
from classification_common import (
    ClassificationToolError,
    read_yaml_strict,
    sha256_file,
    validate_document,
    yaml_text,
)

VERSION = "1.0.0"


def _load_index(path: Path, schema: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "1.0", "components": {}}
    document = read_yaml_strict(path)
    validate_document(document, schema)
    return document


def _commit_pair(target: Path, source: Path, index_path: Path, index: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    staged_component = target.with_name(target.name + ".tmp")
    staged_index = index_path.with_name(index_path.name + ".tmp")
    shutil.copyfile(source, staged_component)
    staged_index.write_text(yaml_text(index), encoding="utf-8")
    previous_component = target.read_bytes() if target.exists() else None
    previous_index = index_path.read_bytes() if index_path.exists() else None
    try:
        os.replace(staged_component, target)
        os.replace(staged_index, index_path)
    except Exception:
        staged_component.unlink(missing_ok=True)
        staged_index.unlink(missing_ok=True)
        if previous_component is None:
            target.unlink(missing_ok=True)
        else:
            target.write_bytes(previous_component)
        if previous_index is None:
            index_path.unlink(missing_ok=True)
        else:
            index_path.write_bytes(previous_index)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--component-file", type=Path, required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument(
        "--source-type",
        choices=["RCSB_CCD_COMPONENT", "SKILL_CUSTOM_COMPONENT", "PROJECT_COMPONENT"],
        required=True,
    )
    parser.add_argument("--parent-component-id")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    library = args.library.resolve()
    source = args.component_file.resolve()
    index_path = library / "index.yaml"
    schema = script_dir.parent / "schemas/ccd_library_index.schema.yaml"
    try:
        if library.exists() and (library.is_symlink() or not library.is_dir()):
            raise ClassificationToolError(f"CCD_LIBRARY_PATH_NOT_FOUND: {library}")
        component_id = component_id_from_cif(source)
        parse_ccd_file(source, component_id)
        source_hash = sha256_file(source)
        index = _load_index(index_path, schema)
        components = index.setdefault("components", {})
        existing = components.get(component_id)
        if existing is not None:
            if existing.get("sha256") == source_hash:
                print("ALREADY_PRESENT")
                return 0
            raise ClassificationToolError("CCD_COMPONENT_DEFINITION_CONFLICT")
        target = library / f"{component_id}.cif"
        if target.exists() and sha256_file(target) != source_hash:
            raise ClassificationToolError("CCD_COMPONENT_DEFINITION_CONFLICT")
        entry = {
            "path": target.name,
            "category": args.category,
            "source_type": args.source_type,
            "sha256": source_hash,
        }
        if args.parent_component_id:
            entry["parent_component_id"] = args.parent_component_id
        components[component_id] = entry
        validate_document(index, schema)
        _commit_pair(target, source, index_path, index)
        print("ADDED")
        return 0
    except ClassificationToolError as exc:
        text = str(exc)
        status = (
            text
            if text in {
                "CCD_COMPONENT_DEFINITION_CONFLICT",
                "CCD_INDEX_VALIDATION_FAILED",
                "WRITE_FAILED",
            }
            else "INVALID_CCD_FILE"
        )
        print(f"{status}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"WRITE_FAILED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Shared deterministic helpers for component/residue classification scripts.

This module is not a standalone tool entry point. It centralizes strict YAML
loading, hashing, schema validation, structure parsing and atomic output rules.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Iterable

import gemmi
import yaml
from jsonschema import Draft202012Validator


class ClassificationToolError(RuntimeError):
    """Raised for deterministic technical failures."""


class _StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _StrictSafeLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            mark = key_node.start_mark
            raise ClassificationToolError(
                f"duplicate YAML key {key!r} at line {mark.line + 1}, column {mark.column + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def read_yaml_strict(path: Path) -> Any:
    if path.is_symlink():
        raise ClassificationToolError(f"symlink input is not accepted: {path}")
    if not path.is_file() or path.stat().st_size == 0:
        raise ClassificationToolError(f"missing or empty YAML input: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.load(handle, Loader=_StrictSafeLoader)
    except ClassificationToolError:
        raise
    except Exception as exc:
        raise ClassificationToolError(f"cannot parse YAML {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    if path.is_symlink():
        raise ClassificationToolError(f"symlink input is not accepted: {path}")
    if not path.is_file():
        raise ClassificationToolError(f"file not found: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def require_sha256(path: Path, expected: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        raise ClassificationToolError(
            f"SHA-256 mismatch for {path}: expected {expected}, observed {actual}"
        )
    return actual


def validate_document(document: Any, schema_path: Path) -> None:
    schema = read_yaml_strict(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise ClassificationToolError(f"invalid JSON schema {schema_path}: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = []
        for error in errors[:20]:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{location}: {error.message}")
        raise ClassificationToolError(
            f"schema validation failed for {schema_path}: " + "; ".join(details)
        )


def yaml_text(document: Any) -> str:
    return yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def atomic_write_yaml(path: Path, document: Any, *, allow_replace: bool = False) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise ClassificationToolError(f"output path is not a regular file: {path}")
        existing = read_yaml_strict(path)
        if existing == document:
            return
        if not allow_replace:
            raise ClassificationToolError(f"refusing to overwrite different existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(yaml_text(document), encoding="utf-8")
    os.replace(temporary, path)


def parse_structure(path: Path) -> gemmi.Structure:
    if path.is_symlink():
        raise ClassificationToolError(f"symlink structure input is not accepted: {path}")
    if not path.is_file() or path.stat().st_size == 0:
        raise ClassificationToolError(f"missing or empty structure input: {path}")
    try:
        structure = gemmi.read_structure(str(path))
    except Exception as exc:
        raise ClassificationToolError(f"structure parse failed for {path}: {exc}") from exc
    if len(structure) == 0:
        raise ClassificationToolError("structure contains no models")
    return structure


def verify_source_format(path: Path, structure: gemmi.Structure, source_format: str) -> None:
    allowed = {"PDB", "MMCIF", "AF3_CIF"}
    if source_format not in allowed:
        raise ClassificationToolError(f"unsupported source format: {source_format}")
    observed_pdb = structure.input_format == gemmi.CoorFormat.Pdb
    if source_format == "PDB" and not observed_pdb:
        raise ClassificationToolError(
            f"source format conflict: source_recognition reported PDB but parser read {structure.input_format}"
        )
    if source_format in {"MMCIF", "AF3_CIF"} and observed_pdb:
        raise ClassificationToolError(
            f"source format conflict: source_recognition reported {source_format} but parser read PDB"
        )


def model_id(model: gemmi.Model) -> str:
    value = str(model.num)
    if not value:
        raise ClassificationToolError("empty model identifier")
    return value


def inspect_models(structure: gemmi.Structure) -> list[dict[str, int | str]]:
    results: list[dict[str, int | str]] = []
    seen: set[str] = set()
    for model in structure:
        identifier = model_id(model)
        if identifier in seen:
            raise ClassificationToolError(f"duplicate model identifier: {identifier}")
        seen.add(identifier)
        chain_count = len(model)
        residue_count = sum(1 for chain in model for _residue in chain)
        atom_count = sum(1 for chain in model for residue in chain for _atom in residue)
        if residue_count == 0 or atom_count == 0:
            raise ClassificationToolError(f"model {identifier} contains no coordinate residues or atoms")
        results.append(
            {
                "model_id": identifier,
                "chain_count": chain_count,
                "residue_count": residue_count,
                "atom_count": atom_count,
            }
        )
    if not results:
        raise ClassificationToolError("structure contains no inspectable models")
    return results


def validate_unique_residue_definitions(document: dict[str, Any]) -> None:
    seen: set[str] = set()
    for index, entry in enumerate(document.get("residue_definitions", []), start=1):
        name = entry["residue_name"]
        if name in seen:
            raise ClassificationToolError(
                f"DUPLICATE_PROJECT_RESIDUE_DEFINITION: residue_name {name!r} at item {index}"
            )
        seen.add(name)


def validate_possible_connections(document: dict[str, Any]) -> None:
    seen: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for index, entry in enumerate(document.get("possible_connections", []), start=1):
        bounds = entry["distance_range_angstrom"]
        if float(bounds["maximum"]) <= float(bounds["minimum"]):
            raise ClassificationToolError(
                f"possible_connections item {index}: maximum must be greater than minimum"
            )
        first = (entry["partner_1"]["residue_name"], entry["partner_1"]["atom_name"])
        second = (entry["partner_2"]["residue_name"], entry["partner_2"]["atom_name"])
        key = tuple(sorted((first, second)))
        if key in seen:
            raise ClassificationToolError(
                f"DUPLICATE_CONNECTION_DEFINITION at item {index}: {first} -- {second}"
            )
        seen.add(key)


def validate_possible_coordination(document: dict[str, Any]) -> None:
    seen: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for index, entry in enumerate(document.get("possible_coordination", []), start=1):
        bounds = entry["distance_range_angstrom"]
        if float(bounds["maximum"]) <= float(bounds["minimum"]):
            raise ClassificationToolError(
                f"possible_coordination item {index}: maximum must be greater than minimum"
            )
        metal = (entry["metal"]["residue_name"], entry["metal"]["atom_name"])
        donor = (entry["donor"]["residue_name"], entry["donor"]["atom_name"])
        key = (metal, donor)
        if key in seen:
            raise ClassificationToolError(
                f"DUPLICATE_COORDINATION_DEFINITION at item {index}: {metal} -> {donor}"
            )
        seen.add(key)


def require_selected_model(models: Iterable[dict[str, Any]], selected_model_id: str) -> None:
    available = {str(item["model_id"]) for item in models}
    if selected_model_id not in available:
        raise ClassificationToolError(
            f"selected model {selected_model_id!r} is not present; available models: {sorted(available)}"
        )

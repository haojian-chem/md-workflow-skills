#!/usr/bin/env python3
"""Shared deterministic helpers for component/residue classification v1."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Iterable

import gemmi
import yaml
from jsonschema import Draft202012Validator


class ClassificationError(RuntimeError):
    """Raised when a deterministic technical precondition fails."""


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def atomic_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    os.replace(temp, path)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str | None, label: str) -> str:
    if not path.is_file() or path.is_symlink():
        raise ClassificationError(f"{label} is not a regular file: {path}")
    actual = sha256(path)
    if expected and actual.lower() != expected.lower():
        raise ClassificationError(f"{label} SHA-256 mismatch: {path}")
    return actual


def validate_document(document: Any, schema_path: Path) -> None:
    schema = load_yaml(schema_path)
    if not isinstance(schema, dict):
        raise ClassificationError(f"schema is not a mapping: {schema_path}")
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        messages: list[str] = []
        for error in errors[:25]:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            messages.append(f"{location}: {error.message}")
        raise ClassificationError(
            f"schema validation failed ({schema_path.name}): {'; '.join(messages)}"
        )


def clean_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text in {"", "\x00", ".", "?"}:
        return None
    stripped = text.strip()
    return stripped or None


def source_resid_from_residue(residue: gemmi.Residue) -> dict[str, str | None]:
    return {
        "number": str(residue.seqid.num),
        "insertion_code": clean_optional_string(residue.seqid.icode),
    }


def source_resid_key(source_resid: dict[str, Any]) -> tuple[str | None, str | None]:
    return (
        None if source_resid.get("number") is None else str(source_resid["number"]),
        clean_optional_string(source_resid.get("insertion_code")),
    )


def source_resid_text(source_resid: dict[str, Any]) -> str:
    number = source_resid.get("number")
    insertion = source_resid.get("insertion_code")
    return f"{number if number is not None else '?'}{insertion or ''}"


def read_structure(path: Path) -> gemmi.Structure:
    try:
        structure = gemmi.read_structure(str(path))
    except Exception as exc:  # pragma: no cover - gemmi provides many concrete errors
        raise ClassificationError(f"unable to parse structure: {path}: {exc}") from exc
    if len(structure) == 0:
        raise ClassificationError("structure contains no models")
    return structure


def model_id(model: gemmi.Model) -> str:
    return str(model.num)


def select_model(structure: gemmi.Structure, selected_model_id: str) -> gemmi.Model:
    matches = [model for model in structure if model_id(model) == str(selected_model_id)]
    if len(matches) != 1:
        raise ClassificationError(
            f"selected model must resolve exactly once: {selected_model_id!r}; found {len(matches)}"
        )
    return matches[0]


def source_format(path: Path, structure: gemmi.Structure, declared: str | None = None) -> str:
    if declared:
        if declared not in {"PDB", "MMCIF", "AF3_CIF"}:
            raise ClassificationError(f"unsupported source format: {declared}")
        return declared
    if structure.input_format == gemmi.CoorFormat.Pdb or path.suffix.lower() in {".pdb", ".ent"}:
        return "PDB"
    return "MMCIF"


def normalize_element_symbol(value: str | None) -> str | None:
    text = clean_optional_string(value)
    if text is None:
        return None
    if not re.fullmatch(r"[A-Za-z]{1,3}", text):
        return None
    return text[0].upper() + text[1:].lower()


def is_hydrogen_symbol(symbol: str | None) -> bool:
    return normalize_element_symbol(symbol) in {"H", "D"}


def atom_altloc(atom: gemmi.Atom) -> str | None:
    return clean_optional_string(atom.altloc)


def entity_metadata(
    structure: gemmi.Structure,
    model: gemmi.Model,
    residue: gemmi.Residue,
) -> tuple[str | None, str, str | None]:
    entity_id = clean_optional_string(residue.entity_id)
    entity_type = "UNKNOWN"
    polymer_type: str | None = None

    try:
        raw_entity_type = residue.entity_type
        entity_type = {
            gemmi.EntityType.Polymer: "POLYMER",
            gemmi.EntityType.NonPolymer: "NONPOLYMER",
            gemmi.EntityType.Branched: "BRANCHED",
            gemmi.EntityType.Water: "WATER",
        }.get(raw_entity_type, "UNKNOWN")
    except Exception:
        pass

    try:
        if residue.subchain:
            entity = structure.get_entity_of(model.get_subchain(residue.subchain))
            entity_id = clean_optional_string(entity.name) or entity_id
            entity_type = {
                gemmi.EntityType.Polymer: "POLYMER",
                gemmi.EntityType.NonPolymer: "NONPOLYMER",
                gemmi.EntityType.Branched: "BRANCHED",
                gemmi.EntityType.Water: "WATER",
            }.get(entity.entity_type, entity_type)
            polymer_type = {
                gemmi.PolymerType.PeptideL: "POLYPEPTIDE_L",
                gemmi.PolymerType.PeptideD: "POLYPEPTIDE_D",
                gemmi.PolymerType.CyclicPseudoPeptide: "CYCLIC_PSEUDOPEPTIDE",
                gemmi.PolymerType.Dna: "DNA",
                gemmi.PolymerType.Rna: "RNA",
                gemmi.PolymerType.DnaRnaHybrid: "DNA_RNA_HYBRID",
                gemmi.PolymerType.SaccharideD: "POLYSACCHARIDE_D",
                gemmi.PolymerType.SaccharideL: "POLYSACCHARIDE_L",
                gemmi.PolymerType.Pna: "PNA",
                gemmi.PolymerType.Other: "OTHER",
            }.get(entity.polymer_type, None)
    except Exception:
        pass
    return entity_id, entity_type, polymer_type


def residue_locator(
    *,
    chain_index: int | None,
    source_chain_id: str | None,
    source_resid: dict[str, Any],
    residue_name: str,
) -> dict[str, Any]:
    return {
        "chain_index": chain_index,
        "source_chain_id": source_chain_id,
        "source_resid": {
            "number": None if source_resid.get("number") is None else str(source_resid["number"]),
            "insertion_code": clean_optional_string(source_resid.get("insertion_code")),
        },
        "residue_name": residue_name,
    }


def atom_locator(
    *,
    chain_index: int | None,
    source_chain_id: str | None,
    source_resid: dict[str, Any],
    residue_name: str,
    atom_name: str,
    element: str | None = None,
    altloc: str | None = None,
) -> dict[str, Any]:
    payload = residue_locator(
        chain_index=chain_index,
        source_chain_id=source_chain_id,
        source_resid=source_resid,
        residue_name=residue_name,
    )
    payload["atom_name"] = atom_name
    if element is not None:
        payload["element"] = normalize_element_symbol(element)
    if altloc is not None:
        payload["altloc"] = altloc
    return payload


def canonical_locator_key(locator: dict[str, Any], include_atom: bool = False) -> tuple[Any, ...]:
    source_resid = locator.get("source_resid") or {}
    key: tuple[Any, ...] = (
        locator.get("source_chain_id"),
        source_resid.get("number"),
        source_resid.get("insertion_code"),
        locator.get("residue_name"),
    )
    if include_atom:
        key += (locator.get("atom_name"), locator.get("altloc"))
    return key


def distance_angstrom(atom_a: gemmi.Atom, atom_b: gemmi.Atom) -> float:
    return float(atom_a.pos.dist(atom_b.pos))


def unique_unordered_pairs(items: list[Any]) -> Iterable[tuple[Any, Any]]:
    for left_index in range(len(items)):
        for right_index in range(left_index + 1, len(items)):
            yield items[left_index], items[right_index]


def safe_component_filename(component_id: str) -> str:
    if not component_id or not re.fullmatch(r"[A-Za-z0-9_.+-]+", component_id):
        raise ClassificationError(f"unsafe CCD component id: {component_id!r}")
    if component_id in {".", ".."} or ".." in component_id:
        raise ClassificationError(f"unsafe CCD component id: {component_id!r}")
    return f"{component_id}.cif"


def resolve_output_path(path: Path, authorized_root: Path | None = None) -> Path:
    resolved = path.resolve()
    if authorized_root is not None:
        root = authorized_root.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ClassificationError(f"output path is outside authorized root: {path}") from exc
    return resolved


def format_float(value: float) -> float:
    return float(f"{value:.6f}")

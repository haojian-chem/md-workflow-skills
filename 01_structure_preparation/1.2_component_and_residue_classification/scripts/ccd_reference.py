#!/usr/bin/env python3
"""Deterministic local CCD-compatible library lookup and atom comparison."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import gemmi

from classification_common import ClassificationToolError, read_yaml_strict, sha256_file

CCD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_+\-]*$")


@dataclass(frozen=True)
class CcdTemplate:
    component_id: str
    snapshot_path: Path
    snapshot_sha256: str
    atom_names: tuple[str, ...]
    heavy_atom_names: tuple[str, ...]
    alternate_atom_names: dict[str, str]


def validate_ccd_id(component_id: str) -> None:
    if not CCD_ID_PATTERN.fullmatch(component_id) or ".." in component_id:
        raise ClassificationToolError(f"unsafe or unsupported CCD component ID: {component_id!r}")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text in {".", "?"} else text


def component_id_from_cif(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise ClassificationToolError(f"missing, empty or symlink CCD file: {path}")
    try:
        document = gemmi.cif.read_file(str(path))
    except Exception as exc:
        raise ClassificationToolError(f"cannot parse CCD-compatible CIF {path}: {exc}") from exc
    component_ids: set[str] = set()
    for block in document:
        direct = _clean(block.find_value("_chem_comp.id"))
        if direct:
            component_ids.add(direct)
        for row in block.find(["_chem_comp_atom.comp_id"]):
            value = _clean(row[0])
            if value:
                component_ids.add(value)
    if len(component_ids) != 1:
        raise ClassificationToolError(
            f"CCD-compatible CIF must define one component ID, observed {sorted(component_ids)}"
        )
    component_id = next(iter(component_ids))
    validate_ccd_id(component_id)
    return component_id


def parse_ccd_file(
    path: Path,
    requested_component_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]:
    validate_ccd_id(requested_component_id)
    observed_component_id = component_id_from_cif(path)
    if observed_component_id != requested_component_id:
        raise ClassificationToolError(
            f"COMPONENT_ID_MISMATCH: requested {requested_component_id!r}, "
            f"observed {observed_component_id!r} in {path}"
        )
    document = gemmi.cif.read_file(str(path))
    atom_names: list[str] = []
    heavy_atom_names: list[str] = []
    alternates: dict[str, str] = {}
    for block in document:
        table = block.find(
            [
                "_chem_comp_atom.atom_id",
                "_chem_comp_atom.type_symbol",
                "_chem_comp_atom.alt_atom_id",
            ]
        )
        for row in table:
            atom_id = _clean(row[0])
            element = _clean(row[1])
            alternate = _clean(row[2])
            if atom_id is None or element is None:
                raise ClassificationToolError(f"invalid CCD atom row in {path}")
            try:
                parsed_element = gemmi.Element(element)
            except Exception as exc:
                raise ClassificationToolError(
                    f"unrecognized element {element!r} for atom {atom_id!r} in {path}"
                ) from exc
            atom_names.append(atom_id)
            if not parsed_element.is_hydrogen:
                heavy_atom_names.append(atom_id)
            if alternate and alternate != atom_id:
                previous = alternates.get(alternate)
                if previous is not None and previous != atom_id:
                    raise ClassificationToolError(
                        f"ambiguous alternate atom name {alternate!r} in {path}"
                    )
                alternates[alternate] = atom_id
    if not atom_names or len(atom_names) != len(set(atom_names)):
        raise ClassificationToolError(f"missing or duplicate CCD atom IDs in {path}")
    return tuple(atom_names), tuple(heavy_atom_names), alternates


def _load_index(library: Path) -> dict[str, dict[str, Any]]:
    if library.is_symlink() or not library.is_dir():
        raise ClassificationToolError(f"CCD_LIBRARY_PATH_NOT_FOUND: {library}")
    index_path = library / "index.yaml"
    if not index_path.is_file() or index_path.is_symlink():
        raise ClassificationToolError(f"CCD_LIBRARY_INDEX_NOT_FOUND: {index_path}")
    document = read_yaml_strict(index_path)
    if not isinstance(document, dict) or document.get("schema_version") != "1.0":
        raise ClassificationToolError(f"CCD_LIBRARY_INDEX_INVALID: {index_path}")
    components = document.get("components")
    if not isinstance(components, dict):
        raise ClassificationToolError(f"CCD_LIBRARY_INDEX_INVALID: {index_path}")
    result: dict[str, dict[str, Any]] = {}
    for component_id, entry in components.items():
        if not isinstance(component_id, str) or not isinstance(entry, dict):
            raise ClassificationToolError(f"CCD_LIBRARY_INDEX_INVALID: {index_path}")
        validate_ccd_id(component_id)
        required = {"path", "category", "source_type", "sha256"}
        if not required.issubset(entry):
            raise ClassificationToolError(f"CCD_LIBRARY_INDEX_INVALID: {index_path}")
        result[component_id] = entry
    return result


def acquire_ccd_template(
    component_id: str,
    mapped_residue_names: list[str],
    *,
    project_snapshot_dir: Path,
    local_reference_dirs: list[Path],
    shared_cache_path: Path | None,
    retrieval_policy: str,
    remote_base_url: str = "",
    timeout_seconds: float = 0.0,
) -> tuple[CcdTemplate | None, dict[str, Any], dict[str, Any] | None]:
    """Resolve a component from ordered indexed local libraries.

    Only ``local_reference_dirs`` participate in lookup. The remaining keyword
    arguments are accepted by the current engine interface but do not enable
    snapshot, cache or network access.
    """
    del project_snapshot_dir, shared_cache_path, retrieval_policy, remote_base_url, timeout_seconds
    validate_ccd_id(component_id)
    matches: list[tuple[int, Path, dict[str, Any], Path, str]] = []
    for order, library in enumerate(local_reference_dirs):
        index = _load_index(library.resolve())
        entry = index.get(component_id)
        if entry is None:
            continue
        relative = Path(str(entry["path"]))
        if relative.is_absolute() or len(relative.parts) != 1:
            raise ClassificationToolError(f"CCD_LIBRARY_INDEX_INVALID: {library / 'index.yaml'}")
        reference_path = (library / relative).resolve()
        try:
            reference_path.relative_to(library.resolve())
        except ValueError as exc:
            raise ClassificationToolError(f"CCD_LIBRARY_INDEX_INVALID: {reference_path}") from exc
        expected_hash = str(entry["sha256"])
        actual_hash = sha256_file(reference_path)
        if actual_hash != expected_hash:
            raise ClassificationToolError(
                f"CCD_LIBRARY_FILE_HASH_MISMATCH: {reference_path}"
            )
        matches.append((order, library.resolve(), entry, reference_path, actual_hash))

    if not matches:
        return None, {
            "component_id": component_id,
            "mapped_residue_names": mapped_residue_names,
            "status": "UNAVAILABLE",
            "source_type": "NONE",
            "library_path": None,
            "reference_path": None,
            "sha256": None,
        }, None

    distinct_hashes = {item[4] for item in matches}
    if len(distinct_hashes) > 1:
        return None, {
            "component_id": component_id,
            "mapped_residue_names": mapped_residue_names,
            "status": "CONFLICT",
            "source_type": "NONE",
            "library_path": None,
            "reference_path": None,
            "sha256": None,
        }, {
            "issue_type": "CCD_COMPONENT_DEFINITION_CONFLICT",
            "subject": {
                "component_id": component_id,
                "candidate_paths": [str(item[3]) for item in matches],
            },
            "evidence": ["same component ID has different indexed SHA-256 values"],
            "resolution_status": "PENDING_CONFIRMATION",
        }

    _order, library, entry, reference_path, file_hash = matches[0]
    source_type = (
        "BUILTIN_CCD_LIBRARY" if _order == 0 else "ADDITIONAL_CCD_LIBRARY"
    )
    try:
        atom_names, heavy_names, alternates = parse_ccd_file(reference_path, component_id)
    except ClassificationToolError:
        return None, {
            "component_id": component_id,
            "mapped_residue_names": mapped_residue_names,
            "status": "INVALID",
            "source_type": source_type,
            "library_path": str(library),
            "reference_path": str(reference_path),
            "sha256": file_hash,
        }, None
    template = CcdTemplate(
        component_id=component_id,
        snapshot_path=reference_path,
        snapshot_sha256=file_hash,
        atom_names=atom_names,
        heavy_atom_names=heavy_names,
        alternate_atom_names=alternates,
    )
    return template, {
        "component_id": component_id,
        "mapped_residue_names": mapped_residue_names,
        "status": "LOADED",
        "source_type": source_type,
        "library_path": str(library),
        "reference_path": str(reference_path),
        "sha256": file_hash,
    }, None


def compare_ccd_heavy_atoms(
    observed_heavy_atom_names: Iterable[str],
    template: CcdTemplate,
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    observed = set(observed_heavy_atom_names)
    expected = set(template.heavy_atom_names)
    missing = expected - observed
    unexpected = observed - expected
    candidates: list[dict[str, str]] = []
    for observed_name in sorted(unexpected):
        reference_name = template.alternate_atom_names.get(observed_name)
        if reference_name is not None and reference_name in missing:
            candidates.append(
                {
                    "structure_atom_name": observed_name,
                    "ccd_atom_id": reference_name,
                    "mapping_source": "CCD_ALTERNATE_ATOM_NAME",
                }
            )
    return sorted(missing), sorted(unexpected), candidates

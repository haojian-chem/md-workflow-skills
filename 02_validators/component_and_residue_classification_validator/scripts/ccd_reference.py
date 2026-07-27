#!/usr/bin/env python3
"""Deterministic CCD lookup, validation, snapshot and heavy-atom helpers."""
from __future__ import annotations

import re
import shutil
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import gemmi
import yaml

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    sha256_file,
)

CCD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_+\-]*$")
DEFAULT_REMOTE_BASE_URL = "https://files.rcsb.org/ligands/download"


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


def _clean_cif_value(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {".", "?"}:
        return None
    return text


def parse_ccd_file(path: Path, requested_component_id: str) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]:
    validate_ccd_id(requested_component_id)
    if path.is_symlink():
        raise ClassificationToolError(f"symlink CCD file is not accepted: {path}")
    if not path.is_file() or path.stat().st_size == 0:
        raise ClassificationToolError(f"missing or empty CCD file: {path}")
    try:
        document = gemmi.cif.read_file(str(path))
    except Exception as exc:
        raise ClassificationToolError(f"cannot parse CCD mmCIF {path}: {exc}") from exc
    if len(document) != 1:
        raise ClassificationToolError(
            f"CCD file {path} must contain exactly one data block, observed {len(document)}"
        )
    block = document.sole_block()
    observed_component_id = _clean_cif_value(block.find_value("_chem_comp.id"))
    if observed_component_id is None:
        comp_ids = {
            _clean_cif_value(row[0])
            for row in block.find(["_chem_comp_atom.comp_id"])
            if _clean_cif_value(row[0]) is not None
        }
        if len(comp_ids) == 1:
            observed_component_id = next(iter(comp_ids))
    if observed_component_id != requested_component_id:
        raise ClassificationToolError(
            f"COMPONENT_ID_MISMATCH: requested {requested_component_id!r}, "
            f"observed {observed_component_id!r} in {path}"
        )

    table = block.find(
        [
            "_chem_comp_atom.atom_id",
            "_chem_comp_atom.type_symbol",
            "_chem_comp_atom.alt_atom_id",
        ]
    )
    atom_names: list[str] = []
    heavy_atom_names: list[str] = []
    alternate_names: dict[str, str] = {}
    for row in table:
        atom_id = _clean_cif_value(row[0])
        element = _clean_cif_value(row[1])
        alternate = _clean_cif_value(row[2])
        if atom_id is None or element is None:
            raise ClassificationToolError(f"invalid CCD atom row in {path}")
        try:
            parsed_element = gemmi.Element(element)
        except Exception as exc:
            raise ClassificationToolError(
                f"unrecognized CCD element {element!r} for atom {atom_id!r} in {path}"
            ) from exc
        atom_names.append(atom_id)
        if not parsed_element.is_hydrogen:
            heavy_atom_names.append(atom_id)
        if alternate is not None and alternate != atom_id:
            if alternate in alternate_names and alternate_names[alternate] != atom_id:
                raise ClassificationToolError(
                    f"ambiguous alternate atom name {alternate!r} in {path}"
                )
            alternate_names[alternate] = atom_id

    if not atom_names:
        raise ClassificationToolError(f"CCD atom table is missing or empty in {path}")
    if len(atom_names) != len(set(atom_names)):
        raise ClassificationToolError(f"duplicate CCD atom IDs in {path}")
    return tuple(atom_names), tuple(heavy_atom_names), alternate_names


def _copy_verified(source: Path, target: Path) -> str:
    source_hash = sha256_file(source)
    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise ClassificationToolError(f"CCD snapshot path is not a regular file: {target}")
        target_hash = sha256_file(target)
        if target_hash != source_hash:
            raise ClassificationToolError(
                f"refusing to overwrite differing CCD project snapshot: {target}"
            )
        return target_hash
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    shutil.copyfile(source, temporary)
    copied_hash = sha256_file(temporary)
    if copied_hash != source_hash:
        temporary.unlink(missing_ok=True)
        raise ClassificationToolError(f"CCD snapshot copy hash mismatch: {source} -> {target}")
    temporary.replace(target)
    return copied_hash


def _template_from_snapshot(component_id: str, snapshot: Path) -> CcdTemplate:
    atom_names, heavy_names, alternates = parse_ccd_file(snapshot, component_id)
    return CcdTemplate(
        component_id=component_id,
        snapshot_path=snapshot.resolve(),
        snapshot_sha256=sha256_file(snapshot),
        atom_names=atom_names,
        heavy_atom_names=heavy_names,
        alternate_atom_names=alternates,
    )


def _valid_candidates(component_id: str, candidates: Iterable[Path]) -> list[tuple[Path, str]]:
    valid: list[tuple[Path, str]] = []
    for candidate in candidates:
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            parse_ccd_file(candidate, component_id)
        except ClassificationToolError:
            continue
        valid.append((candidate.resolve(), sha256_file(candidate)))
    return valid


def _shared_cache_candidates(cache_root: Path, component_id: str) -> list[Path]:
    candidates: list[Path] = []
    direct = cache_root / f"{component_id}.cif"
    if direct.is_file():
        candidates.append(direct)
    component_dir = cache_root / component_id
    current_index = component_dir / "current.yaml"
    if current_index.is_file() and not current_index.is_symlink():
        try:
            current = yaml.safe_load(current_index.read_text(encoding="utf-8"))
            current_path = current.get("path") if isinstance(current, dict) else None
            if isinstance(current_path, str):
                candidate = (component_dir / current_path).resolve()
                try:
                    candidate.relative_to(component_dir.resolve())
                except ValueError:
                    candidate = Path("/__invalid_cache_path__")
                if candidate.is_file():
                    candidates.append(candidate)
        except Exception:
            pass
    if component_dir.is_dir():
        candidates.extend(sorted(component_dir.glob(f"{component_id}__*.cif")))
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _download_component(component_id: str, remote_base_url: str, timeout_seconds: float) -> Path:
    validate_ccd_id(component_id)
    url = f"{remote_base_url.rstrip('/')}/{component_id}.cif"
    last_error: Exception | None = None
    for _attempt in range(2):
        temporary = tempfile.NamedTemporaryFile(prefix=f"ccd_{component_id}_", suffix=".cif", delete=False)
        temporary_path = Path(temporary.name)
        temporary.close()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "md-workflow-skills/ccd-fetch"})
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response, temporary_path.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            parse_ccd_file(temporary_path, component_id)
            return temporary_path
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            temporary_path.unlink(missing_ok=True)
            continue
        except ClassificationToolError:
            temporary_path.unlink(missing_ok=True)
            raise
    raise ClassificationToolError(f"CCD download failed for {component_id}: {last_error}")


def _store_shared_cache(cache_root: Path, component_id: str, source: Path) -> Path:
    file_hash = sha256_file(source)
    component_dir = cache_root / component_id
    component_dir.mkdir(parents=True, exist_ok=True)
    target = component_dir / f"{component_id}__{file_hash[:16]}.cif"
    _copy_verified(source, target)
    atomic_write_yaml(
        component_dir / "current.yaml",
        {
            "schema_version": "1.0",
            "component_id": component_id,
            "path": target.name,
            "sha256": file_hash,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        allow_replace=True,
    )
    return target


def acquire_ccd_template(
    component_id: str,
    mapped_residue_names: list[str],
    *,
    project_snapshot_dir: Path,
    local_reference_dirs: list[Path],
    shared_cache_path: Path | None,
    retrieval_policy: str,
    remote_base_url: str = DEFAULT_REMOTE_BASE_URL,
    timeout_seconds: float = 30.0,
) -> tuple[CcdTemplate | None, dict[str, Any], dict[str, Any] | None]:
    """Acquire one component and return template, manifest entry and optional confirmation issue."""

    validate_ccd_id(component_id)
    if retrieval_policy not in {"DOWNLOAD_MISSING", "CACHE_ONLY"}:
        raise ClassificationToolError(f"unsupported CCD retrieval policy: {retrieval_policy}")
    snapshot = project_snapshot_dir.resolve() / f"{component_id}.cif"

    def manifest(
        source: str,
        source_path: Path | None,
        retrieval_status: str,
        template: CcdTemplate | None,
        validation_status: str,
        component_id_match: bool | None,
        atom_table_valid: bool | None,
    ) -> dict[str, Any]:
        return {
            "component_id": component_id,
            "mapped_residue_names": mapped_residue_names,
            "retrieval": {
                "policy": retrieval_policy,
                "source": source,
                "source_path": str(source_path) if source_path is not None else None,
                "status": retrieval_status,
            },
            "project_snapshot": {
                "path": str(template.snapshot_path) if template is not None else None,
                "sha256": template.snapshot_sha256 if template is not None else None,
                "status": "AVAILABLE" if template is not None else "UNAVAILABLE",
            },
            "validation": {
                "status": validation_status,
                "component_id_match": component_id_match,
                "atom_table_valid": atom_table_valid,
            },
        }

    if snapshot.is_file():
        try:
            template = _template_from_snapshot(component_id, snapshot)
        except ClassificationToolError as exc:
            return None, manifest("PROJECT_SNAPSHOT", snapshot, "RETRIEVAL_FAILED", None, "INVALID_COMPONENT_FILE", None, False), {
                "issue_type": "INVALID_PROJECT_CCD_SNAPSHOT",
                "subject": {"component_id": component_id, "path": str(snapshot)},
                "evidence": [str(exc)],
                "resolution_status": "PENDING_CONFIRMATION",
            }
        return template, manifest("PROJECT_SNAPSHOT", snapshot, "AVAILABLE_PROJECT_SNAPSHOT", template, "VALID", True, True), None

    local_candidates = [directory.resolve() / f"{component_id}.cif" for directory in local_reference_dirs]
    valid_local = _valid_candidates(component_id, local_candidates)
    distinct_local_hashes = {item[1] for item in valid_local}
    if len(distinct_local_hashes) > 1:
        paths = [str(item[0]) for item in valid_local]
        return None, manifest("LOCAL_REFERENCE_DIRECTORY", None, "MULTIPLE_LOCAL_CANDIDATES", None, "NOT_PERFORMED", None, None), {
            "issue_type": "MULTIPLE_LOCAL_CCD_CANDIDATES",
            "subject": {"component_id": component_id, "candidate_paths": paths},
            "evidence": [f"different valid SHA-256 values: {sorted(distinct_local_hashes)}"],
            "resolution_status": "PENDING_CONFIRMATION",
        }
    if valid_local:
        source = valid_local[0][0]
        _copy_verified(source, snapshot)
        template = _template_from_snapshot(component_id, snapshot)
        return template, manifest("LOCAL_REFERENCE_DIRECTORY", source, "AVAILABLE_LOCAL_REFERENCE", template, "VALID", True, True), None

    if shared_cache_path is not None:
        cache_root = shared_cache_path.resolve()
        valid_cache = _valid_candidates(component_id, _shared_cache_candidates(cache_root, component_id))
        if valid_cache:
            source = valid_cache[0][0]
            _copy_verified(source, snapshot)
            template = _template_from_snapshot(component_id, snapshot)
            return template, manifest("SHARED_CACHE", source, "AVAILABLE_SHARED_CACHE", template, "VALID", True, True), None

    if retrieval_policy == "CACHE_ONLY":
        return None, manifest("NONE", None, "RETRIEVAL_FAILED", None, "NOT_PERFORMED", None, None), None

    downloaded_path: Path | None = None
    try:
        downloaded_path = _download_component(component_id, remote_base_url, timeout_seconds)
        source = downloaded_path
        if shared_cache_path is not None:
            source = _store_shared_cache(shared_cache_path.resolve(), component_id, downloaded_path)
        _copy_verified(source, snapshot)
        template = _template_from_snapshot(component_id, snapshot)
        return template, manifest("REMOTE", source, "DOWNLOADED", template, "VALID", True, True), None
    except ClassificationToolError as exc:
        text = str(exc)
        validation_status = "COMPONENT_ID_MISMATCH" if "COMPONENT_ID_MISMATCH" in text else "NOT_PERFORMED"
        return None, manifest("REMOTE", None, "RETRIEVAL_FAILED", None, validation_status, False if validation_status == "COMPONENT_ID_MISMATCH" else None, None), None
    finally:
        if downloaded_path is not None:
            downloaded_path.unlink(missing_ok=True)


def compare_ccd_heavy_atoms(
    observed_heavy_atom_names: Iterable[str],
    template: CcdTemplate,
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    observed = set(observed_heavy_atom_names)
    expected = set(template.heavy_atom_names)
    missing = expected - observed
    unexpected = observed - expected
    mapping_candidates: list[dict[str, str]] = []
    remapped_unexpected: set[str] = set()
    remapped_missing: set[str] = set()
    for structure_name in sorted(unexpected):
        ccd_name = template.alternate_atom_names.get(structure_name)
        if ccd_name is not None and ccd_name in missing:
            mapping_candidates.append(
                {
                    "structure_atom_name": structure_name,
                    "ccd_atom_id": ccd_name,
                    "mapping_source": "CCD_ALTERNATE_ATOM_NAME",
                }
            )
            remapped_unexpected.add(structure_name)
            remapped_missing.add(ccd_name)
    return (
        sorted(missing - remapped_missing),
        sorted(unexpected - remapped_unexpected),
        mapping_candidates,
    )

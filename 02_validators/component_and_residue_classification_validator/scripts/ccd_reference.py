#!/usr/bin/env python3
"""CCD component lookup, validation, cache and project snapshot support."""
from __future__ import annotations

import shutil
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gemmi
import yaml

from classification_common import (
    ClassificationError,
    atomic_yaml,
    clean_optional_string,
    normalize_element_symbol,
    safe_component_filename,
    sha256,
)


@dataclass(frozen=True)
class CCDTemplate:
    component_id: str
    atom_names: tuple[str, ...]
    heavy_atom_names: tuple[str, ...]
    alternate_names: dict[str, str]
    source_path: Path
    source_sha256: str


def _category_rows(block: gemmi.cif.Block, prefix: str) -> tuple[list[str], list[list[str]]]:
    table = block.find_mmcif_category(prefix)
    if len(table) == 0:
        return [], []
    tags = [str(tag) for tag in table.tags]
    return tags, [list(row) for row in table]


def validate_ccd_file(path: Path, requested_component_id: str) -> CCDTemplate:
    try:
        document = gemmi.cif.read_file(str(path))
    except Exception as exc:
        raise ClassificationError(f"invalid CCD CIF file {path}: {exc}") from exc
    if len(document) != 1:
        raise ClassificationError(f"CCD file must contain exactly one data block: {path}")
    block = document.sole_block()
    component_id = clean_optional_string(block.find_value("_chem_comp.id"))
    if component_id is None:
        component_id = clean_optional_string(block.name)
    if component_id != requested_component_id:
        raise ClassificationError(
            f"CCD component id mismatch: requested {requested_component_id!r}, found {component_id!r}: {path}"
        )

    tags, rows = _category_rows(block, "_chem_comp_atom.")
    if not rows:
        raise ClassificationError(f"CCD atom table is missing: {path}")
    index = {tag: idx for idx, tag in enumerate(tags)}
    atom_tag = "_chem_comp_atom.atom_id"
    element_tag = "_chem_comp_atom.type_symbol"
    if atom_tag not in index or element_tag not in index:
        raise ClassificationError(f"CCD atom table lacks atom_id or type_symbol: {path}")
    alt_tags = [
        tag
        for tag in ("_chem_comp_atom.alt_atom_id", "_chem_comp_atom.pdbx_component_atom_id")
        if tag in index
    ]

    atoms: list[str] = []
    heavy: list[str] = []
    alternates: dict[str, str] = {}
    for row in rows:
        atom_name = clean_optional_string(row[index[atom_tag]])
        element = normalize_element_symbol(row[index[element_tag]])
        if atom_name is None or element is None:
            raise ClassificationError(f"CCD atom row has invalid atom name or element: {path}")
        atoms.append(atom_name)
        if element not in {"H", "D"}:
            heavy.append(atom_name)
        for tag in alt_tags:
            alt_name = clean_optional_string(row[index[tag]])
            if alt_name and alt_name != atom_name:
                prior = alternates.get(alt_name)
                if prior is not None and prior != atom_name:
                    raise ClassificationError(
                        f"CCD alternate atom name is ambiguous: {alt_name}: {path}"
                    )
                alternates[alt_name] = atom_name
    if len(atoms) != len(set(atoms)):
        raise ClassificationError(f"CCD atom_id values are not unique: {path}")
    return CCDTemplate(
        component_id=component_id,
        atom_names=tuple(atoms),
        heavy_atom_names=tuple(heavy),
        alternate_names=alternates,
        source_path=path,
        source_sha256=sha256(path),
    )


def _copy_snapshot(source: Path, destination: Path, expected_hash: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file() or destination.is_symlink():
            raise ClassificationError(f"CCD project snapshot path is invalid: {destination}")
        if sha256(destination) != expected_hash:
            raise ClassificationError(
                f"existing CCD project snapshot differs and must not be overwritten: {destination}"
            )
        return
    temp = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temp)
    if sha256(temp) != expected_hash:
        temp.unlink(missing_ok=True)
        raise ClassificationError(f"CCD snapshot copy hash mismatch: {source} -> {destination}")
    temp.replace(destination)


def _shared_cache_candidates(cache_path: Path | None, component_id: str) -> list[Path]:
    if cache_path is None:
        return []
    candidates: list[Path] = []
    direct = cache_path / safe_component_filename(component_id)
    if direct.is_file() and not direct.is_symlink():
        candidates.append(direct)
    version_dir = cache_path / component_id
    if version_dir.is_dir():
        candidates.extend(sorted(path for path in version_dir.glob(f"{component_id}__*.cif") if path.is_file() and not path.is_symlink()))
    return candidates


def _valid_candidates(paths: list[Path], component_id: str) -> tuple[list[CCDTemplate], list[dict[str, str]]]:
    valid: list[CCDTemplate] = []
    invalid: list[dict[str, str]] = []
    for path in paths:
        try:
            valid.append(validate_ccd_file(path, component_id))
        except ClassificationError as exc:
            invalid.append({"path": str(path), "error": str(exc)})
    return valid, invalid


def _download_component(component_id: str, remote_url_template: str) -> Path:
    url = remote_url_template.format(component_id=component_id)
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "md-workflow-skills/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
            temp_dir = Path(tempfile.mkdtemp(prefix="ccd-download-"))
            path = temp_dir / safe_component_filename(component_id)
            path.write_bytes(data)
            return path
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(0.5)
    raise ClassificationError(f"CCD download failed for {component_id}: {last_error}")


def _store_shared_cache(template: CCDTemplate, cache_path: Path | None) -> None:
    if cache_path is None:
        return
    version_dir = cache_path / template.component_id
    version_dir.mkdir(parents=True, exist_ok=True)
    destination = version_dir / f"{template.component_id}__{template.source_sha256[:16]}.cif"
    if not destination.exists():
        shutil.copyfile(template.source_path, destination)
    if sha256(destination) != template.source_sha256:
        raise ClassificationError(f"shared CCD cache write hash mismatch: {destination}")
    atomic_yaml(
        version_dir / "current.yaml",
        {
            "component_id": template.component_id,
            "path": destination.name,
            "sha256": template.source_sha256,
        },
    )


def resolve_ccd_component(
    *,
    component_id: str,
    mapped_residue_names: list[str],
    project_snapshot_dir: Path,
    local_reference_dirs: list[Path],
    shared_cache_path: Path | None,
    retrieval_policy: str,
    remote_url_template: str,
) -> tuple[CCDTemplate | None, dict[str, Any], list[dict[str, Any]]]:
    filename = safe_component_filename(component_id)
    snapshot = project_snapshot_dir / filename
    issues: list[dict[str, Any]] = []
    base_manifest: dict[str, Any] = {
        "component_id": component_id,
        "mapped_residue_names": sorted(set(mapped_residue_names)),
        "retrieval": {"policy": retrieval_policy, "source": None, "status": None},
        "project_snapshot": {"path": str(snapshot), "sha256": None, "status": "UNAVAILABLE"},
        "validation": {"status": "NOT_PERFORMED"},
    }

    # Existing project snapshot is authoritative and must be valid.
    if snapshot.exists():
        template = validate_ccd_file(snapshot, component_id)
        base_manifest["retrieval"].update(source="PROJECT_SNAPSHOT", status="AVAILABLE")
        base_manifest["project_snapshot"].update(sha256=template.source_sha256, status="AVAILABLE")
        base_manifest["validation"] = {
            "component_id_match": True,
            "atom_table_valid": True,
            "status": "VALID",
        }
        return template, base_manifest, issues

    # Search all explicitly supplied local directories before cache/network.
    local_paths = [directory / filename for directory in local_reference_dirs if (directory / filename).is_file()]
    local_valid, local_invalid = _valid_candidates(local_paths, component_id)
    if local_invalid:
        base_manifest["retrieval"]["invalid_local_candidates"] = local_invalid
    if local_valid:
        hashes = {candidate.source_sha256 for candidate in local_valid}
        if len(hashes) > 1:
            issues.append(
                {
                    "issue_type": "MULTIPLE_LOCAL_CCD_CANDIDATES",
                    "component_id": component_id,
                    "candidates": [
                        {"path": str(candidate.source_path), "sha256": candidate.source_sha256}
                        for candidate in local_valid
                    ],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            base_manifest["retrieval"].update(source="LOCAL_REFERENCE_DIRECTORY", status="MULTIPLE_CANDIDATES")
            return None, base_manifest, issues
        template = local_valid[0]
        _copy_snapshot(template.source_path, snapshot, template.source_sha256)
        template = validate_ccd_file(snapshot, component_id)
        base_manifest["retrieval"].update(
            source="LOCAL_REFERENCE_DIRECTORY",
            source_path=str(local_valid[0].source_path),
            status="AVAILABLE",
        )
        base_manifest["project_snapshot"].update(sha256=template.source_sha256, status="AVAILABLE")
        base_manifest["validation"] = {
            "component_id_match": True,
            "atom_table_valid": True,
            "status": "VALID",
        }
        return template, base_manifest, issues

    cache_valid, cache_invalid = _valid_candidates(
        _shared_cache_candidates(shared_cache_path, component_id), component_id
    )
    if cache_invalid:
        base_manifest["retrieval"]["invalid_cache_candidates"] = cache_invalid
    if cache_valid:
        # Prefer current direct file, otherwise newest lexical hash entry; all are content-addressed.
        template = cache_valid[-1]
        _copy_snapshot(template.source_path, snapshot, template.source_sha256)
        template = validate_ccd_file(snapshot, component_id)
        base_manifest["retrieval"].update(
            source="SHARED_CACHE", source_path=str(cache_valid[-1].source_path), status="AVAILABLE"
        )
        base_manifest["project_snapshot"].update(sha256=template.source_sha256, status="AVAILABLE")
        base_manifest["validation"] = {
            "component_id_match": True,
            "atom_table_valid": True,
            "status": "VALID",
        }
        return template, base_manifest, issues

    if retrieval_policy == "CACHE_ONLY":
        base_manifest["retrieval"].update(source="NONE", status="RETRIEVAL_FAILED")
        return None, base_manifest, issues
    if retrieval_policy != "DOWNLOAD_MISSING":
        raise ClassificationError(f"unsupported CCD retrieval policy: {retrieval_policy}")

    try:
        downloaded = _download_component(component_id, remote_url_template)
        downloaded_template = validate_ccd_file(downloaded, component_id)
        _store_shared_cache(downloaded_template, shared_cache_path)
        _copy_snapshot(downloaded, snapshot, downloaded_template.source_sha256)
        template = validate_ccd_file(snapshot, component_id)
        base_manifest["retrieval"].update(
            source="REMOTE",
            remote_url=remote_url_template.format(component_id=component_id),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            status="AVAILABLE",
        )
        base_manifest["project_snapshot"].update(sha256=template.source_sha256, status="AVAILABLE")
        base_manifest["validation"] = {
            "component_id_match": True,
            "atom_table_valid": True,
            "status": "VALID",
        }
        return template, base_manifest, issues
    except ClassificationError as exc:
        base_manifest["retrieval"].update(source="REMOTE", status="RETRIEVAL_FAILED", error=str(exc))
        return None, base_manifest, issues

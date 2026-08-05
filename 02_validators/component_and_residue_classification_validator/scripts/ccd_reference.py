#!/usr/bin/env python3
"""Public local CCD-compatible lookup with an internal legacy fixture adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import ccd_reference_core as _core
from classification_common import ClassificationToolError, sha256_file

# Keep one strict indexed implementation owner.
globals().update(
    {
        name: getattr(_core, name)
        for name in dir(_core)
        if not name.startswith("__")
    }
)


def _legacy_exact_candidates(
    component_id: str,
    roots: list[Path],
) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    for root in roots:
        resolved = root.resolve()
        if not resolved.exists():
            continue
        if resolved.is_symlink() or not resolved.is_dir():
            raise ClassificationToolError(f"invalid CCD reference directory: {resolved}")
        candidate = resolved / f"{component_id}.cif"
        if not candidate.exists():
            continue
        _core.parse_ccd_file(candidate, component_id)
        candidates.append((candidate, sha256_file(candidate)))
    return candidates


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
):
    """Resolve indexed libraries for production and exact files for old engine fixtures.

    Public ``classify_structure.py`` always passes ``INDEXED_ONLY``. The exact
    file branch exists only for direct baseline-engine fixtures that predate the
    indexed library contract; it never scans recursively, downloads or copies a
    snapshot/cache file.
    """
    if retrieval_policy == "INDEXED_ONLY" or all(
        (root.resolve() / "index.yaml").is_file() for root in local_reference_dirs
    ):
        return _core.acquire_ccd_template(
            component_id,
            mapped_residue_names,
            project_snapshot_dir=project_snapshot_dir,
            local_reference_dirs=local_reference_dirs,
            shared_cache_path=shared_cache_path,
            retrieval_policy=retrieval_policy,
            remote_base_url=remote_base_url,
            timeout_seconds=timeout_seconds,
        )

    candidates = _legacy_exact_candidates(component_id, local_reference_dirs)
    if not candidates:
        return None, {
            "component_id": component_id,
            "mapped_residue_names": mapped_residue_names,
            "status": "UNAVAILABLE",
            "source_type": "NONE",
            "library_path": None,
            "reference_path": None,
            "sha256": None,
        }, None
    distinct_hashes = {value for _path, value in candidates}
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
                "candidate_paths": [str(path) for path, _hash in candidates],
            },
            "evidence": ["same exact component ID has different SHA-256 values"],
            "resolution_status": "PENDING_CONFIRMATION",
        }
    path, file_hash = candidates[0]
    atom_names, heavy_names, alternates = _core.parse_ccd_file(path, component_id)
    template = _core.CcdTemplate(
        component_id=component_id,
        snapshot_path=path,
        snapshot_sha256=file_hash,
        atom_names=atom_names,
        heavy_atom_names=heavy_names,
        alternate_atom_names=alternates,
    )
    return template, {
        "component_id": component_id,
        "mapped_residue_names": mapped_residue_names,
        "status": "LOADED",
        "source_type": "ADDITIONAL_CCD_LIBRARY",
        "library_path": str(path.parent),
        "reference_path": str(path),
        "sha256": file_hash,
    }, None

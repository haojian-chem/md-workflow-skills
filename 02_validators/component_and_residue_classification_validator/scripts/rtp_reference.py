#!/usr/bin/env python3
"""Read GROMACS RTP residue templates deterministically."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from classification_common import ClassificationError, is_hydrogen_symbol, sha256

_SUBSECTIONS = {
    "atoms",
    "bonds",
    "angles",
    "dihedrals",
    "impropers",
    "cmap",
    "exclusions",
    "bondedtypes",
}
_HEADER = re.compile(r"^\s*\[\s*([^\]]+?)\s*\]\s*(?:;.*)?$")


@dataclass(frozen=True)
class RTPTemplate:
    residue_name: str
    path: Path
    atom_names: tuple[str, ...]
    heavy_atom_names: tuple[str, ...]

    def as_reference(self) -> dict[str, Any]:
        return {
            "residue_name": self.residue_name,
            "path": str(self.path),
            "sha256": sha256(self.path),
            "atom_names": list(self.atom_names),
            "heavy_atom_names": list(self.heavy_atom_names),
        }


def _atom_is_heavy(atom_name: str) -> bool:
    name = atom_name.strip()
    stripped = name.lstrip("0123456789")
    if not stripped:
        return True
    # RTP does not provide elements. This conservative rule excludes H/D-prefixed atoms.
    return not (stripped.startswith("H") or stripped.startswith("D"))


def parse_rtp(path: Path) -> list[RTPTemplate]:
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="latin-1").splitlines()

    templates: list[RTPTemplate] = []
    current_name: str | None = None
    current_section: str | None = None
    atoms: list[str] = []

    def finish() -> None:
        nonlocal current_name, atoms
        if current_name is None:
            return
        if len(atoms) != len(set(atoms)):
            raise ClassificationError(f"duplicate atom name in RTP block {current_name}: {path}")
        templates.append(
            RTPTemplate(
                residue_name=current_name,
                path=path,
                atom_names=tuple(atoms),
                heavy_atom_names=tuple(name for name in atoms if _atom_is_heavy(name)),
            )
        )
        current_name = None
        atoms = []

    for raw in lines:
        text = raw.split(";", 1)[0].strip()
        if not text:
            continue
        match = _HEADER.match(text)
        if match:
            header = match.group(1).strip()
            lowered = header.lower()
            if lowered in _SUBSECTIONS:
                current_section = lowered
            else:
                finish()
                current_name = header
                current_section = None
            continue
        if current_name is not None and current_section == "atoms":
            fields = text.split()
            if fields:
                atoms.append(fields[0])
    finish()
    return templates


def load_rtp_directory(root_path: Path) -> tuple[dict[str, list[RTPTemplate]], list[dict[str, Any]]]:
    if not root_path.is_dir():
        raise ClassificationError(f"force-field root is not a directory: {root_path}")
    paths = sorted(path for path in root_path.rglob("*.rtp") if path.is_file() and not path.is_symlink())
    if not paths:
        raise ClassificationError(f"force-field directory contains no RTP files: {root_path}")
    templates: dict[str, list[RTPTemplate]] = {}
    files: list[dict[str, Any]] = []
    for path in paths:
        parsed = parse_rtp(path)
        files.append(
            {
                "path": str(path),
                "sha256": sha256(path),
                "role": "RTP_RESIDUE_RECOGNITION_AND_HEAVY_ATOM_TEMPLATE",
                "status": "LOADED",
                "template_count": len(parsed),
            }
        )
        for template in parsed:
            templates.setdefault(template.residue_name, []).append(template)
    return templates, files


def choose_terminal_template_name(
    *,
    source_residue_name: str,
    polymer_type: str | None,
    terminal_roles: list[str],
    mappings: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Return mapped RTP residue name and optional constrained RTP file."""
    matches: list[dict[str, Any]] = []
    for item in mappings:
        if item.get("source_residue_name") != source_residue_name:
            continue
        if item.get("polymer_type") not in {None, polymer_type}:
            continue
        if item.get("terminal_role") not in terminal_roles:
            continue
        matches.append(item)
    if not matches:
        return None, None
    normalized = {
        (str(item.get("rtp_residue_name")), None if item.get("rtp_file") is None else str(item.get("rtp_file")))
        for item in matches
    }
    if len(normalized) != 1:
        raise ClassificationError(
            f"conflicting terminal RTP mappings for {source_residue_name} {terminal_roles}: {sorted(normalized)}"
        )
    return next(iter(normalized))


def filter_templates_by_file(
    templates: list[RTPTemplate],
    root_path: Path,
    relative_file: str | None,
) -> list[RTPTemplate]:
    if relative_file is None:
        return templates
    target = (root_path / relative_file).resolve()
    return [template for template in templates if template.path.resolve() == target]

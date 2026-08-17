#!/usr/bin/env python3
"""Deterministic parsing helpers for GROMACS residue topology (RTP) files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from classification_common import ClassificationToolError, sha256_file


RTP_SUBSECTIONS = {
    "atoms",
    "bonds",
    "angles",
    "dihedrals",
    "impropers",
    "exclusions",
    "cmap",
}
RTP_GLOBAL_SECTIONS = {"bondedtypes"}


@dataclass(frozen=True)
class RtpTemplate:
    residue_name: str
    file_path: Path
    file_sha256: str
    atom_names: tuple[str, ...]
    heavy_atom_names: tuple[str, ...]


def _section_name(line: str) -> str | None:
    stripped = line.strip()
    if not (stripped.startswith("[") and "]" in stripped):
        return None
    return stripped[1 : stripped.index("]")].strip()


def _without_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def is_hydrogen_like_rtp_atom(atom_name: str) -> bool:
    """Return whether a standard-residue RTP atom name denotes H/D.

    RTP files do not carry an element column. For standard amino-acid and
    nucleic-acid templates, hydrogen/deuterium names conventionally begin with
    H/D, optionally after a leading digit. The caller records template
    provenance so this heuristic is auditable and can be upgraded later.
    """

    name = atom_name.strip()
    while name and name[0].isdigit():
        name = name[1:]
    return bool(name) and name[0] in {"H", "D"}


def parse_rtp_file(path: Path) -> list[RtpTemplate]:
    if path.is_symlink():
        raise ClassificationToolError(f"symlink RTP file is not accepted: {path}")
    if not path.is_file() or path.stat().st_size == 0:
        raise ClassificationToolError(f"missing or empty RTP file: {path}")

    file_hash = sha256_file(path)
    templates: list[RtpTemplate] = []
    current_residue: str | None = None
    current_subsection: str | None = None
    current_atoms: list[str] = []

    def finish_current() -> None:
        nonlocal current_residue, current_subsection, current_atoms
        if current_residue is None:
            return
        if not current_atoms:
            raise ClassificationToolError(
                f"RTP residue block {current_residue!r} in {path} has no [ atoms ] entries"
            )
        if len(current_atoms) != len(set(current_atoms)):
            raise ClassificationToolError(
                f"RTP residue block {current_residue!r} in {path} contains duplicate atom names"
            )
        heavy = tuple(name for name in current_atoms if not is_hydrogen_like_rtp_atom(name))
        templates.append(
            RtpTemplate(
                residue_name=current_residue,
                file_path=path.resolve(),
                file_sha256=file_hash,
                atom_names=tuple(current_atoms),
                heavy_atom_names=heavy,
            )
        )
        current_residue = None
        current_subsection = None
        current_atoms = []

    for raw_line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        clean = _without_comment(raw_line)
        if not clean:
            continue
        section = _section_name(clean)
        if section is not None:
            lowered = section.lower()
            if lowered in RTP_SUBSECTIONS:
                if current_residue is None:
                    raise ClassificationToolError(
                        f"RTP subsection [{section}] appears outside a residue block in {path}"
                    )
                current_subsection = lowered
                continue
            if lowered in RTP_GLOBAL_SECTIONS:
                finish_current()
                current_subsection = lowered
                continue
            finish_current()
            current_residue = section
            current_subsection = None
            continue

        if current_residue is not None and current_subsection == "atoms":
            fields = clean.split()
            if len(fields) < 2:
                raise ClassificationToolError(
                    f"invalid RTP atom row in {path}, residue {current_residue!r}: {raw_line!r}"
                )
            current_atoms.append(fields[0])

    finish_current()
    return templates


def discover_rtp_files(force_field_root: Path, explicit_files: Iterable[Path] | None = None) -> list[Path]:
    root = force_field_root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise ClassificationToolError(f"invalid force-field root: {force_field_root}")
    if explicit_files is None:
        files = sorted(root.glob("*.rtp"), key=lambda item: item.name)
    else:
        files = []
        for configured in explicit_files:
            candidate = configured if configured.is_absolute() else root / configured
            candidate = candidate.resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise ClassificationToolError(
                    f"configured RTP file escapes force-field root: {configured}"
                ) from exc
            files.append(candidate)
    if not files:
        raise ClassificationToolError(f"no RTP files found under force-field root: {root}")
    return files


def load_rtp_index(force_field_root: Path, explicit_files: Iterable[Path] | None = None) -> tuple[dict[str, list[RtpTemplate]], list[Path]]:
    files = discover_rtp_files(force_field_root, explicit_files)
    index: dict[str, list[RtpTemplate]] = {}
    for path in files:
        for template in parse_rtp_file(path):
            index.setdefault(template.residue_name, []).append(template)
    return index, files


def compare_heavy_atom_names(
    observed_heavy_atom_names: Iterable[str],
    template: RtpTemplate,
) -> tuple[list[str], list[str]]:
    observed = set(observed_heavy_atom_names)
    expected = set(template.heavy_atom_names)
    return sorted(expected - observed), sorted(observed - expected)

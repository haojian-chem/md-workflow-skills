#!/usr/bin/env python3
"""Synchronize the approved built-in CCD seed set from official RCSB definitions."""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import gemmi

from ccd_reference import component_id_from_cif, parse_ccd_file
from classification_common import ClassificationToolError, read_yaml_strict, sha256_file

VERSION = "1.0.0"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", chr(34)):
        text = text[1:-1]
    return None if not text or text in {".", "?"} else text


def _quote(value: str) -> str:
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    raise ClassificationToolError(
        f"unsupported CIF token containing both quote types: {value!r}"
    )


def _load_manifest(path: Path) -> tuple[str, str, dict[str, str]]:
    document = read_yaml_strict(path)
    if not isinstance(document, dict) or document.get("schema_version") != "1.0":
        raise ClassificationToolError("CCD_SEED_MANIFEST_INVALID")
    source = document.get("source")
    components = document.get("components")
    if not isinstance(source, dict) or not isinstance(components, dict) or not components:
        raise ClassificationToolError("CCD_SEED_MANIFEST_INVALID")
    base_url = source.get("base_url")
    source_type = source.get("source_type")
    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        raise ClassificationToolError("CCD_SEED_MANIFEST_INVALID")
    if source_type != "RCSB_CCD_COMPONENT":
        raise ClassificationToolError("CCD_SEED_MANIFEST_INVALID")
    result: dict[str, str] = {}
    for component_id, entry in components.items():
        if (
            not isinstance(component_id, str)
            or not isinstance(entry, dict)
            or not isinstance(entry.get("category"), str)
            or not entry["category"]
        ):
            raise ClassificationToolError("CCD_SEED_MANIFEST_INVALID")
        result[component_id] = entry["category"]
    return base_url.rstrip("/"), source_type, result


def _download(url: str, target: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "md-workflow-skills-ccd-seed-sync/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
    except Exception as exc:
        raise ClassificationToolError(f"CCD_SEED_DOWNLOAD_FAILED: {url}: {exc}") from exc
    if not payload:
        raise ClassificationToolError(
            f"CCD_SEED_DOWNLOAD_FAILED: empty response for {url}"
        )
    target.write_bytes(payload)


def _normalized_heavy_atom_cif(source: Path, component_id: str) -> str:
    observed_id = component_id_from_cif(source)
    if observed_id != component_id:
        raise ClassificationToolError(
            f"COMPONENT_ID_MISMATCH: requested {component_id!r}, observed {observed_id!r}"
        )
    document = gemmi.cif.read_file(str(source))
    rows: list[tuple[str, str, str | None]] = []
    for block in document:
        if _clean(block.find_value("_chem_comp.id")) != component_id:
            continue
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
                raise ClassificationToolError(
                    f"invalid CCD atom row for {component_id}"
                )
            try:
                parsed_element = gemmi.Element(element)
            except Exception as exc:
                raise ClassificationToolError(
                    f"unrecognized element {element!r} for {component_id}:{atom_id}"
                ) from exc
            if parsed_element.is_hydrogen:
                continue
            rows.append(
                (atom_id, element.upper(), None if alternate == atom_id else alternate)
            )
    if not rows or len({atom_id for atom_id, _element, _alternate in rows}) != len(rows):
        raise ClassificationToolError(
            f"missing or duplicate heavy atom IDs for {component_id}"
        )
    lines = [
        f"data_{component_id}",
        f"_chem_comp.id {component_id}",
        "loop_",
        "_chem_comp_atom.comp_id",
        "_chem_comp_atom.atom_id",
        "_chem_comp_atom.type_symbol",
        "_chem_comp_atom.alt_atom_id",
    ]
    for atom_id, element, alternate in rows:
        alternate_token = "." if alternate is None else _quote(alternate)
        lines.append(f"{component_id} {_quote(atom_id)} {element} {alternate_token}")
    return "\n".join(lines) + "\n"


def _verify_library(
    library: Path,
    manifest_components: dict[str, str],
    source_type: str,
) -> None:
    index_path = library / "index.yaml"
    index = read_yaml_strict(index_path)
    if not isinstance(index, dict) or index.get("schema_version") != "1.0":
        raise ClassificationToolError("CCD_LIBRARY_INDEX_INVALID")
    components = index.get("components")
    if not isinstance(components, dict):
        raise ClassificationToolError("CCD_LIBRARY_INDEX_INVALID")
    for component_id, category in manifest_components.items():
        entry = components.get(component_id)
        if not isinstance(entry, dict):
            raise ClassificationToolError(f"CCD_SEED_MISSING: {component_id}")
        if entry.get("category") != category or entry.get("source_type") != source_type:
            raise ClassificationToolError(
                f"CCD_SEED_INDEX_MISMATCH: {component_id}"
            )
        path = library / str(entry.get("path", ""))
        if not path.is_file() or path.is_symlink():
            raise ClassificationToolError(f"CCD_SEED_MISSING: {component_id}")
        if sha256_file(path) != entry.get("sha256"):
            raise ClassificationToolError(
                f"CCD_LIBRARY_FILE_HASH_MISMATCH: {path}"
            )
        parse_ccd_file(path, component_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--download-dir", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    manifest = args.manifest.resolve()
    library = args.library.resolve()
    try:
        base_url, source_type, components = _load_manifest(manifest)
        if args.verify_only:
            _verify_library(library, components, source_type)
            print(f"VERIFIED {len(components)} approved CCD seeds")
            return 0

        if args.download_dir is None:
            temporary = tempfile.TemporaryDirectory(prefix="ccd-seed-sync-")
            download_dir = Path(temporary.name)
        else:
            temporary = None
            download_dir = args.download_dir.resolve()
            download_dir.mkdir(parents=True, exist_ok=True)

        try:
            for component_id, category in components.items():
                official = download_dir / f"{component_id}.official.cif"
                normalized = download_dir / f"{component_id}.cif"
                _download(f"{base_url}/{component_id}.cif", official)
                normalized.write_text(
                    _normalized_heavy_atom_cif(official, component_id),
                    encoding="utf-8",
                )
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(script_dir / "add_ccd_reference.py"),
                        "--library",
                        str(library),
                        "--component-file",
                        str(normalized),
                        "--category",
                        category,
                        "--source-type",
                        source_type,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if completed.returncode != 0:
                    raise ClassificationToolError(
                        f"CCD_SEED_ADD_FAILED: {component_id}: "
                        f"{completed.stderr.strip() or completed.stdout.strip()}"
                    )
                print(f"{component_id}: {completed.stdout.strip()}")
        finally:
            if temporary is not None:
                temporary.cleanup()

        _verify_library(library, components, source_type)
        print(f"SYNCED_AND_VERIFIED {len(components)} approved CCD seeds")
        return 0
    except ClassificationToolError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"CCD_SEED_SYNC_FAILED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

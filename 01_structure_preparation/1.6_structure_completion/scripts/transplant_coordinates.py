#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import gemmi
import numpy as np
import yaml


class ToolError(RuntimeError):
    pass


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictSafeLoader, node: yaml.nodes.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            mark = key_node.start_mark
            raise ToolError(f"duplicate YAML key {key!r} at line {mark.line + 1}, column {mark.column + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ToolError(f"missing or empty config: {path}")
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(f"cannot parse YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ToolError("config root must be a mapping")
    return data


def norm_blank(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("\x00", "")


def require_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f"{field} must be a non-empty path string")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ToolError(f"{field} does not exist: {path}")
    return path


def load_model(path: Path, model_index: int):
    try:
        structure = gemmi.read_structure(str(path))
    except Exception as exc:
        raise ToolError(f"cannot read structure {path}: {exc}") from exc
    if model_index < 1 or model_index > len(structure):
        raise ToolError(f"model_index {model_index} out of range for {path}; model_count={len(structure)}")
    return structure[model_index - 1]


def selector_identity(selector: dict[str, Any], *, atom: bool) -> str:
    parts = [
        f"chain={selector.get('chain_id')!r}",
        f"resid={selector.get('resid')!r}",
        f"icode={selector.get('insertion_code', '')!r}",
    ]
    if selector.get("residue_name") is not None:
        parts.append(f"resname={selector.get('residue_name')!r}")
    if atom:
        parts.append(f"atom={selector.get('atom_name')!r}")
        if selector.get("altloc") is not None:
            parts.append(f"altloc={selector.get('altloc')!r}")
    return ", ".join(parts)


def find_residues(model, selector: dict[str, Any]):
    chain_id = selector.get("chain_id")
    if chain_id is None:
        raise ToolError("selector missing chain_id")
    if "resid" not in selector:
        raise ToolError("selector missing resid")
    resid = str(selector["resid"])
    icode = norm_blank(selector.get("insertion_code", ""))
    resname = selector.get("residue_name")
    matches = []
    for chain in model:
        if chain.name != str(chain_id):
            continue
        for residue in chain:
            if str(residue.seqid.num) != resid:
                continue
            if norm_blank(residue.seqid.icode) != icode:
                continue
            if resname is not None and residue.name != str(resname):
                continue
            matches.append((chain, residue))
    return matches


def find_unique_residue(model, selector: dict[str, Any]):
    matches = find_residues(model, selector)
    if len(matches) != 1:
        raise ToolError(
            f"residue selector must match exactly one residue ({selector_identity(selector, atom=False)}); matches={len(matches)}"
        )
    return matches[0]


def find_unique_atom(model, selector: dict[str, Any]):
    if "atom_name" not in selector:
        raise ToolError("atom selector missing atom_name")
    _, residue = find_unique_residue(model, selector)
    atom_name = str(selector["atom_name"]).strip()
    altloc_requested = selector.get("altloc")
    matches = []
    for atom in residue:
        if atom.name.strip() != atom_name:
            continue
        if altloc_requested is not None and norm_blank(atom.altloc) != norm_blank(altloc_requested):
            continue
        matches.append(atom)
    if len(matches) != 1:
        raise ToolError(
            f"atom selector must match exactly one atom ({selector_identity(selector, atom=True)}); matches={len(matches)}"
        )
    return matches[0]


def xyz(atom) -> np.ndarray:
    return np.array([atom.pos.x, atom.pos.y, atom.pos.z], dtype=float)


def kabsch(reference: np.ndarray, target: np.ndarray):
    if reference.shape != target.shape or reference.ndim != 2 or reference.shape[1] != 3:
        raise ToolError("alignment coordinate arrays must have shape N x 3")
    if reference.shape[0] < 3:
        raise ToolError("alignment requires at least 3 atom pairs")
    ref_center = reference.mean(axis=0)
    tgt_center = target.mean(axis=0)
    ref0 = reference - ref_center
    tgt0 = target - tgt_center
    if np.linalg.matrix_rank(ref0) < 2 or np.linalg.matrix_rank(tgt0) < 2:
        raise ToolError("alignment atoms are collinear or otherwise geometrically degenerate")
    covariance = ref0.T @ tgt0
    u, _, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1, :] *= -1
        rotation = vt.T @ u.T
    translation = tgt_center - rotation @ ref_center
    aligned = (rotation @ reference.T).T + translation
    rmsd = math.sqrt(float(np.mean(np.sum((aligned - target) ** 2, axis=1))))
    return rotation, translation, rmsd


def target_atom_record(target: dict[str, Any], reference_atom, coords: np.ndarray, reference_selector: dict[str, Any]) -> dict[str, Any]:
    element = reference_atom.element.name.strip()
    if element.upper() == "H":
        raise ToolError("hydrogen transplant is not allowed in Stage 1.6")
    result_target = {
        "chain_id": str(target["chain_id"]),
        "resid": target["resid"],
        "insertion_code": norm_blank(target.get("insertion_code", "")),
        "residue_name": str(target["residue_name"]),
        "atom_name": str(target.get("atom_name", reference_atom.name.strip())),
        "record_name": str(target.get("record_name", "ATOM")),
        "element": element,
    }
    result_reference = {
        "chain_id": str(reference_selector["chain_id"]),
        "resid": reference_selector["resid"],
        "insertion_code": norm_blank(reference_selector.get("insertion_code", "")),
        "residue_name": str(reference_selector.get("residue_name", "")),
        "atom_name": reference_atom.name.strip(),
    }
    return {
        "target": result_target,
        "reference": result_reference,
        "coordinates": {"x": float(coords[0]), "y": float(coords[1]), "z": float(coords[2])},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rigidly align a reference and emit transformed heavy-atom coordinates.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        config = read_yaml(args.config.resolve())
        target_path = require_path(config.get("target_structure"), "target_structure")
        reference_path = require_path(config.get("reference_structure"), "reference_structure")
        target_model_index = int(config.get("target_model_index", 1))
        reference_model_index = int(config.get("reference_model_index", 1))
        target_model = load_model(target_path, target_model_index)
        reference_model = load_model(reference_path, reference_model_index)

        pairs = config.get("alignment_atoms")
        if not isinstance(pairs, list) or len(pairs) < 3:
            raise ToolError("alignment_atoms must contain at least 3 target/reference pairs")
        target_coords = []
        reference_coords = []
        seen_target = set()
        seen_reference = set()
        for index, pair in enumerate(pairs, 1):
            if not isinstance(pair, dict) or not isinstance(pair.get("target"), dict) or not isinstance(pair.get("reference"), dict):
                raise ToolError(f"alignment_atoms[{index}] must contain target and reference mappings")
            target_atom = find_unique_atom(target_model, pair["target"])
            reference_atom = find_unique_atom(reference_model, pair["reference"])
            target_key = selector_identity(pair["target"], atom=True)
            reference_key = selector_identity(pair["reference"], atom=True)
            if target_key in seen_target or reference_key in seen_reference:
                raise ToolError("alignment atom selectors must be unique on both target and reference sides")
            seen_target.add(target_key)
            seen_reference.add(reference_key)
            target_coords.append(xyz(target_atom))
            reference_coords.append(xyz(reference_atom))

        target_array = np.vstack(target_coords)
        reference_array = np.vstack(reference_coords)
        rotation, translation, rmsd = kabsch(reference_array, target_array)

        transplanted: list[dict[str, Any]] = []
        target_keys = set()

        atom_items = config.get("transplant_atoms", []) or []
        if not isinstance(atom_items, list):
            raise ToolError("transplant_atoms must be a list")
        for index, item in enumerate(atom_items, 1):
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict) or not isinstance(item.get("reference"), dict):
                raise ToolError(f"transplant_atoms[{index}] must contain target and reference mappings")
            reference_atom = find_unique_atom(reference_model, item["reference"])
            coords = rotation @ xyz(reference_atom) + translation
            record = target_atom_record(item["target"], reference_atom, coords, item["reference"])
            key = (
                record["target"]["chain_id"], str(record["target"]["resid"]), record["target"]["insertion_code"],
                record["target"]["residue_name"], record["target"]["atom_name"]
            )
            if key in target_keys:
                raise ToolError(f"duplicate target transplant atom: {key}")
            target_keys.add(key)
            transplanted.append(record)

        residue_items = config.get("transplant_residues", []) or []
        if not isinstance(residue_items, list):
            raise ToolError("transplant_residues must be a list")
        for index, item in enumerate(residue_items, 1):
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict) or not isinstance(item.get("reference"), dict):
                raise ToolError(f"transplant_residues[{index}] must contain target and reference mappings")
            target_selector = item["target"]
            if "chain_id" not in target_selector or "resid" not in target_selector or "residue_name" not in target_selector:
                raise ToolError(f"transplant_residues[{index}].target requires chain_id, resid, residue_name")
            _, reference_residue = find_unique_residue(reference_model, item["reference"])
            for reference_atom in reference_residue:
                if reference_atom.element.name.strip().upper() == "H":
                    continue
                coords = rotation @ xyz(reference_atom) + translation
                atom_target = dict(target_selector)
                atom_target["atom_name"] = reference_atom.name.strip()
                record = target_atom_record(atom_target, reference_atom, coords, item["reference"])
                key = (
                    record["target"]["chain_id"], str(record["target"]["resid"]), record["target"]["insertion_code"],
                    record["target"]["residue_name"], record["target"]["atom_name"]
                )
                if key in target_keys:
                    raise ToolError(f"duplicate target transplant atom: {key}")
                target_keys.add(key)
                transplanted.append(record)

        if not transplanted:
            raise ToolError("no transplant_atoms or transplant_residues were provided")

        result = {
            "target_structure": str(target_path),
            "reference_structure": str(reference_path),
            "alignment": {
                "atom_count": len(pairs),
                "rmsd": float(rmsd),
                "rotation": [[float(value) for value in row] for row in rotation.tolist()],
                "translation": [float(value) for value in translation.tolist()],
            },
            "transplanted_atoms": transplanted,
        }
        text = yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
        if args.output:
            output = args.output.expanduser().resolve()
            if output.exists():
                raise ToolError(f"output already exists: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

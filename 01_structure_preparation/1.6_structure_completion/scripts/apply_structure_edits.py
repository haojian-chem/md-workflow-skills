#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import gemmi
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


def seqid_parts(residue) -> tuple[str, str]:
    return str(residue.seqid.num), norm_blank(residue.seqid.icode)


def selector_label(sel: dict[str, Any], atom: bool = False) -> str:
    text = f"chain={sel.get('chain_id')!r}, resid={sel.get('resid')!r}, icode={sel.get('insertion_code', '')!r}"
    if sel.get("residue_name") is not None:
        text += f", resname={sel.get('residue_name')!r}"
    if atom:
        text += f", atom={sel.get('atom_name')!r}, altloc={sel.get('altloc', '')!r}"
    return text


def find_chain(model, chain_id: str):
    matches = [chain for chain in model if chain.name == chain_id]
    if len(matches) != 1:
        raise ToolError(f"chain_id {chain_id!r} must match exactly one chain; matches={len(matches)}")
    return matches[0]


def residue_matches(residue, sel: dict[str, Any]) -> bool:
    if "resid" not in sel:
        raise ToolError("residue selector missing resid")
    resid, icode = seqid_parts(residue)
    if resid != str(sel["resid"]):
        return False
    if icode != norm_blank(sel.get("insertion_code", "")):
        return False
    if sel.get("residue_name") is not None and residue.name != str(sel["residue_name"]):
        return False
    return True


def find_residue(model, sel: dict[str, Any]):
    if "chain_id" not in sel:
        raise ToolError("residue selector missing chain_id")
    chain = find_chain(model, str(sel["chain_id"]))
    matches = [(i, residue) for i, residue in enumerate(chain) if residue_matches(residue, sel)]
    if len(matches) != 1:
        raise ToolError(f"residue selector must match exactly one residue ({selector_label(sel)}); matches={len(matches)}")
    return chain, matches[0][0], matches[0][1]


def find_atom(model, sel: dict[str, Any]):
    if "atom_name" not in sel:
        raise ToolError("atom selector missing atom_name")
    chain, ri, residue = find_residue(model, sel)
    atom_name = str(sel["atom_name"]).strip()
    requested_altloc = sel.get("altloc")
    matches = []
    for ai, atom in enumerate(residue):
        if atom.name.strip() != atom_name:
            continue
        if requested_altloc is not None and norm_blank(atom.altloc) != norm_blank(requested_altloc):
            continue
        matches.append((ai, atom))
    if len(matches) != 1:
        raise ToolError(f"atom selector must match exactly one atom ({selector_label(sel, atom=True)}); matches={len(matches)}")
    return chain, ri, residue, matches[0][0], matches[0][1]


def require_list(config: dict[str, Any], key: str) -> list[Any]:
    value = config.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ToolError(f"{key} must be a list")
    return value


def make_atom(spec: dict[str, Any]) -> gemmi.Atom:
    if not isinstance(spec, dict):
        raise ToolError("atom specification must be a mapping")
    name = spec.get("atom_name")
    element = spec.get("element")
    coords = spec.get("coordinates")
    if not isinstance(name, str) or not name.strip():
        raise ToolError("added atom requires atom_name")
    if not isinstance(element, str) or not element.strip():
        raise ToolError(f"added atom {name!r} requires element")
    if element.strip().upper() == "H":
        raise ToolError("adding hydrogen is not allowed in Stage 1.6")
    if not isinstance(coords, dict) or not all(k in coords for k in ("x", "y", "z")):
        raise ToolError(f"added atom {name!r} requires coordinates x/y/z")
    atom = gemmi.Atom()
    atom.name = name.strip()
    atom.element = gemmi.Element(element.strip())
    atom.pos = gemmi.Position(float(coords["x"]), float(coords["y"]), float(coords["z"]))
    atom.occ = float(spec.get("occupancy", 1.0))
    atom.b_iso = float(spec.get("b_iso", 0.0))
    altloc = norm_blank(spec.get("altloc", ""))
    atom.altloc = altloc if altloc else "\x00"
    return atom


def make_residue(target: dict[str, Any], atoms: list[dict[str, Any]]) -> gemmi.Residue:
    if not isinstance(target, dict):
        raise ToolError("residue target must be a mapping")
    for field in ("resid", "residue_name"):
        if field not in target:
            raise ToolError(f"residue target missing {field}")
    try:
        resid = int(target["resid"])
    except Exception as exc:
        raise ToolError(f"resid must be an integer for PDB output: {target.get('resid')!r}") from exc
    icode = norm_blank(target.get("insertion_code", "")) or " "
    if len(icode) != 1:
        raise ToolError("PDB insertion_code must be empty or one character")
    residue = gemmi.Residue()
    residue.name = str(target["residue_name"])
    residue.seqid = gemmi.SeqId(resid, icode)
    record_name = str(target.get("record_name", "ATOM")).upper()
    if record_name not in {"ATOM", "HETATM"}:
        raise ToolError("record_name must be ATOM or HETATM")
    residue.het_flag = "H" if record_name == "HETATM" else "A"
    seen = set()
    for spec in atoms:
        atom = make_atom(spec)
        key = (atom.name.strip(), norm_blank(atom.altloc))
        if key in seen:
            raise ToolError(f"duplicate added atom in residue: {key}")
        seen.add(key)
        residue.add_atom(atom)
    if len(residue) == 0:
        raise ToolError("added/replaced residue must contain at least one heavy atom")
    return residue


def insertion_position(chain, resid: int, icode: str) -> int:
    wanted = (resid, icode)
    for i, residue in enumerate(chain):
        current = (int(residue.seqid.num), norm_blank(residue.seqid.icode))
        if current > wanted:
            return i
    return len(chain)


def ensure_no_duplicate_atom(residue, atom: gemmi.Atom):
    key = (atom.name.strip(), norm_blank(atom.altloc))
    for existing in residue:
        if (existing.name.strip(), norm_blank(existing.altloc)) == key:
            raise ToolError(f"target residue already contains atom {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply explicitly decided structure edits to a PDB target.")
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()

    try:
        config = read_yaml(args.config.resolve())
        input_value = config.get("input_structure")
        output_value = config.get("output_structure")
        if not isinstance(input_value, str) or not input_value.strip():
            raise ToolError("input_structure must be a non-empty path")
        if not isinstance(output_value, str) or not output_value.strip():
            raise ToolError("output_structure must be a non-empty path")
        input_path = Path(input_value).expanduser().resolve()
        output_path = Path(output_value).expanduser().resolve()
        if not input_path.is_file():
            raise ToolError(f"input_structure not found: {input_path}")
        if input_path.suffix.lower() != ".pdb":
            raise ToolError("apply_structure_edits.py currently requires a PDB input")
        if output_path == input_path:
            raise ToolError("output_structure must differ from input_structure")
        if output_path.exists():
            raise ToolError(f"output_structure already exists: {output_path}")

        input_text = input_path.read_text(encoding="utf-8", errors="replace")
        has_cryst1 = any(line.startswith("CRYST1") for line in input_text.splitlines())
        if any(line.startswith("CONECT") for line in input_text.splitlines()):
            raise ToolError("PDB input contains CONECT records; serial renumbering would require explicit connectivity handling")

        structure = gemmi.read_structure(str(input_path))
        if len(structure) != 1:
            raise ToolError(f"PDB input must contain exactly one model; observed {len(structure)}")
        model = structure[0]

        for item in require_list(config, "remove_atoms"):
            if not isinstance(item, dict):
                raise ToolError("remove_atoms entries must be mappings")
            _, _, residue, ai, _ = find_atom(model, item)
            del residue[ai]

        for item in require_list(config, "rename_atoms"):
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict):
                raise ToolError("rename_atoms entries require target mapping")
            new_name = item.get("new_atom_name")
            if not isinstance(new_name, str) or not new_name.strip():
                raise ToolError("rename_atoms entry requires new_atom_name")
            _, _, residue, _, atom = find_atom(model, item["target"])
            for existing in residue:
                if existing is not atom and existing.name.strip() == new_name.strip() and norm_blank(existing.altloc) == norm_blank(atom.altloc):
                    raise ToolError(f"rename would create duplicate atom name {new_name!r} in target residue")
            atom.name = new_name.strip()

        for item in require_list(config, "replace_residues"):
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict) or not isinstance(item.get("atoms"), list):
                raise ToolError("replace_residues entries require target mapping and atoms list")
            chain, ri, _ = find_residue(model, item["target"])
            replacement = make_residue(item["target"], item["atoms"])
            del chain[ri]
            chain.add_residue(replacement, ri)

        for item in require_list(config, "add_residues"):
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict) or not isinstance(item.get("atoms"), list):
                raise ToolError("add_residues entries require target mapping and atoms list")
            target = item["target"]
            chain_id = target.get("chain_id")
            if not isinstance(chain_id, str):
                raise ToolError("add_residues target requires chain_id")
            chain = find_chain(model, chain_id)
            if any(residue_matches(residue, target) for residue in chain):
                raise ToolError(f"add_residues target already exists ({selector_label(target)})")
            residue = make_residue(target, item["atoms"])
            pos = insertion_position(chain, int(target["resid"]), norm_blank(target.get("insertion_code", "")))
            chain.add_residue(residue, pos)

        for item in require_list(config, "add_atoms"):
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict) or not isinstance(item.get("coordinates"), dict):
                raise ToolError("add_atoms entries require target mapping and coordinates")
            target = item["target"]
            _, _, residue = find_residue(model, target)
            atom_spec = dict(target)
            atom_spec["coordinates"] = item["coordinates"]
            if "element" not in atom_spec and "element" in item:
                atom_spec["element"] = item["element"]
            atom = make_atom(atom_spec)
            ensure_no_duplicate_atom(residue, atom)
            residue.add_atom(atom)

        serial = 1
        for chain in model:
            for residue in chain:
                for atom in residue:
                    atom.serial = serial
                    serial += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        options = gemmi.PdbWriteOptions()
        options.cryst1_record = has_cryst1
        options.conect_records = False
        structure.write_pdb(str(output_path), options)
        return 0
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

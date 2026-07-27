#!/usr/bin/env python3
"""Shared structure/relationship helpers for connection and coordination checks."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import gemmi

from classification_common import (
    ClassificationError,
    atom_altloc,
    atom_locator,
    clean_optional_string,
    entity_metadata,
    model_id,
    normalize_element_symbol,
    read_structure,
    select_model,
    source_resid_from_residue,
    source_resid_key,
)


def _record_key(record: dict[str, Any]) -> tuple[Any, ...]:
    resid = record["source_resid"]
    return (
        record.get("source_chain_id"),
        str(resid.get("number")) if resid.get("number") is not None else None,
        clean_optional_string(resid.get("insertion_code")),
        record.get("residue_name"),
    )


def collect_relation_residues(
    structure_path: Path,
    selected_model_id: str,
    observations: dict[str, Any],
) -> tuple[gemmi.Structure, gemmi.Model, list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    structure = read_structure(structure_path)
    model = select_model(structure, selected_model_id)
    exact_chain_indices = {
        _record_key(record): record.get("chain_index")
        for record in observations.get("residue_records", [])
        if record.get("presence_status") == "OBSERVED"
    }
    polymer_groups_by_source: dict[str | None, list[int]] = defaultdict(list)
    bulk_groups_by_name: dict[str, list[int]] = defaultdict(list)
    for group in observations.get("chain_groups", []):
        if group["group_type"] in {"POLYMER_CHAIN", "BRANCHED_CHAIN"}:
            polymer_groups_by_source[group.get("source_chain_id")].append(group["chain_index"])
        elif group.get("residue_name") is not None:
            bulk_groups_by_name[group["residue_name"]].append(group["chain_index"])

    residues: list[dict[str, Any]] = []
    serial_map: dict[int, list[dict[str, Any]]] = defaultdict(list)
    source_order = 0
    for chain in model:
        for residue in chain:
            source_order += 1
            source_resid = source_resid_from_residue(residue)
            key = (chain.name, *source_resid_key(source_resid), residue.name)
            chain_index = exact_chain_indices.get(key)
            entity_id, entity_type, _ = entity_metadata(structure, model, residue)
            if chain_index is None and entity_type in {"POLYMER", "BRANCHED"}:
                candidates = polymer_groups_by_source.get(chain.name, [])
                if len(candidates) == 1:
                    chain_index = candidates[0]
            if chain_index is None:
                candidates = bulk_groups_by_name.get(residue.name, [])
                if len(candidates) == 1:
                    chain_index = candidates[0]
            atoms: list[dict[str, Any]] = []
            for atom in residue:
                atom_item = {
                    "source_order": source_order,
                    "chain_index": chain_index,
                    "source_chain_id": chain.name,
                    "source_resid": source_resid,
                    "residue_name": residue.name,
                    "atom_name": atom.name.strip(),
                    "element": normalize_element_symbol(atom.element.name),
                    "altloc": atom_altloc(atom),
                    "atom": atom,
                    "serial": int(atom.serial),
                }
                atoms.append(atom_item)
                if atom_item["serial"] > 0:
                    serial_map[atom_item["serial"]].append(atom_item)
            residues.append(
                {
                    "source_order": source_order,
                    "chain_index": chain_index,
                    "source_chain_id": chain.name,
                    "source_resid": source_resid,
                    "residue_name": residue.name,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "atoms": atoms,
                    "multiple_conformations": any(atom["altloc"] is not None for atom in atoms),
                }
            )
    return structure, model, residues, serial_map


def atom_endpoint(atom: dict[str, Any]) -> dict[str, Any]:
    endpoint = atom_locator(
        chain_index=atom.get("chain_index"),
        source_chain_id=atom.get("source_chain_id"),
        source_resid=atom["source_resid"],
        residue_name=atom["residue_name"],
        atom_name=atom["atom_name"],
        element=atom.get("element"),
        altloc=atom.get("altloc"),
    )
    endpoint["source_order"] = atom.get("source_order")
    return endpoint


def _atom_key(atom: dict[str, Any]) -> tuple[Any, ...]:
    return (
        atom.get("source_chain_id"),
        atom["source_resid"].get("number"),
        atom["source_resid"].get("insertion_code"),
        atom.get("residue_name"),
        atom.get("atom_name"),
        atom.get("altloc"),
    )


def pair_key(atom_a: dict[str, Any], atom_b: dict[str, Any]) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    return tuple(sorted((_atom_key(atom_a), _atom_key(atom_b)), key=repr))  # type: ignore[return-value]


def _address_matches_atom(address: gemmi.AtomAddress, atom: dict[str, Any]) -> bool:
    return (
        address.chain_name == atom["source_chain_id"]
        and address.res_id.name == atom["residue_name"]
        and str(address.res_id.seqid.num) == str(atom["source_resid"]["number"])
        and clean_optional_string(address.res_id.seqid.icode) == atom["source_resid"].get("insertion_code")
        and address.atom_name.strip() == atom["atom_name"]
        and (clean_optional_string(address.altloc) in {None, atom.get("altloc")})
    )


def explicit_relation_index(
    structure: gemmi.Structure,
    model: gemmi.Model,
    residues: list[dict[str, Any]],
    serial_map: dict[int, list[dict[str, Any]]],
    structure_path: Path | None = None,
) -> dict[tuple[tuple[Any, ...], tuple[Any, ...]], list[dict[str, Any]]]:
    atoms = [atom for residue in residues for atom in residue["atoms"]]
    index: dict[tuple[tuple[Any, ...], tuple[Any, ...]], list[dict[str, Any]]] = defaultdict(list)
    type_map = {
        gemmi.ConnectionType.Covale: "COVALENT",
        gemmi.ConnectionType.Disulf: "DISULFIDE",
        gemmi.ConnectionType.MetalC: "METAL_COORDINATION",
    }
    for connection in structure.connections:
        left = [atom for atom in atoms if _address_matches_atom(connection.partner1, atom)]
        right = [atom for atom in atoms if _address_matches_atom(connection.partner2, atom)]
        for atom_a in left:
            for atom_b in right:
                if atom_a is atom_b:
                    continue
                index[pair_key(atom_a, atom_b)].append(
                    {
                        "source_type": "STRUCTURE_CONNECTION",
                        "source_record": connection.name or connection.link_id or "unnamed",
                        "relation_type": type_map.get(connection.type, "OTHER_EXPLICIT"),
                        "connection_type": connection.type.name,
                    }
                )
    try:
        conect_map = structure.conect_map
    except Exception:
        conect_map = {}

    # Gemmi does not populate conect_map for every PDB producer/version.  Parse
    # raw CONECT records as a deterministic fallback, while preserving the same
    # serial-based semantics and de-duplicating through the pair index.
    raw_conect_pairs: set[tuple[int, int]] = set()
    if structure_path is not None and structure_path.suffix.lower() in {".pdb", ".ent"}:
        for raw in structure_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not raw.startswith("CONECT"):
                continue
            fields = raw[6:].split()
            if len(fields) < 2:
                continue
            try:
                left = int(fields[0])
                rights = [int(value) for value in fields[1:]]
            except ValueError:
                continue
            for right in rights:
                if left != right:
                    raw_conect_pairs.add(tuple(sorted((left, right))))

    for left_serial, right_serials in conect_map.items():
        for right_serial in right_serials:
            if int(left_serial) >= int(right_serial):
                continue
            for atom_a in serial_map.get(int(left_serial), []):
                for atom_b in serial_map.get(int(right_serial), []):
                    evidence = {
                        "source_type": "PDB_CONECT",
                        "source_record": f"CONECT {left_serial} {right_serial}",
                        "relation_type": "METAL_COORDINATION"
                        if atom_a["atom"].element.is_metal or atom_b["atom"].element.is_metal
                        else "COVALENT",
                    }
                    bucket = index[pair_key(atom_a, atom_b)]
                    if evidence not in bucket:
                        bucket.append(evidence)
    for left_serial, right_serial in sorted(raw_conect_pairs):
        for atom_a in serial_map.get(left_serial, []):
            for atom_b in serial_map.get(right_serial, []):
                evidence = {
                    "source_type": "PDB_CONECT",
                    "source_record": f"CONECT {left_serial} {right_serial}",
                    "relation_type": "METAL_COORDINATION"
                    if atom_a["atom"].element.is_metal or atom_b["atom"].element.is_metal
                    else "COVALENT",
                }
                bucket = index[pair_key(atom_a, atom_b)]
                if evidence not in bucket:
                    bucket.append(evidence)
    return index


def matching_residues(
    residues: list[dict[str, Any]], residue_name: str, atom_name: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    residue_matches = [residue for residue in residues if residue["residue_name"] == residue_name]
    valid: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for residue in residue_matches:
        atoms = [atom for atom in residue["atoms"] if atom["atom_name"] == atom_name]
        if atoms:
            valid.append({"residue": residue, "atoms": atoms})
        else:
            missing.append(
                {
                    "chain_index": residue.get("chain_index"),
                    "source_chain_id": residue["source_chain_id"],
                    "source_resid": residue["source_resid"],
                    "residue_name": residue_name,
                    "missing_atom_name": atom_name,
                }
            )
    return valid, missing


def geometry_range(distance: float, minimum: float, maximum: float) -> str:
    if distance < minimum:
        return "BELOW_MINIMUM"
    if distance > maximum:
        return "ABOVE_MAXIMUM"
    return "WITHIN_RANGE"

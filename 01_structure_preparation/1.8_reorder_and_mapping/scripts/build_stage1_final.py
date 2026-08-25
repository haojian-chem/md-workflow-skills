#!/usr/bin/env python3
"""Build Stage 1 final heavy-atom PDB and stable identity map for Skill 1.8."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to run build_stage1_final.py") from exc


CHAIN_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
ATOM_RECORDS = {"ATOM  ", "HETATM"}
ResidueKey = tuple[str, str]


class Stage1FinalError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResidueMeta:
    component_id: str
    residue_id: str
    chain_index: int
    polymer_class: str
    topology_class: str
    stable_order: int
    component_order: int
    residue_order: int

    @property
    def key(self) -> ResidueKey:
        return self.component_id, self.residue_id


@dataclass
class AtomLine:
    raw: str

    @property
    def atom_name(self) -> str:
        return self.raw[12:16].strip()

    @property
    def residue_name(self) -> str:
        return self.raw[17:20].strip()

    @property
    def chain_id(self) -> str:
        return self.raw[21:22]

    @property
    def resid(self) -> int:
        text = self.raw[22:26].strip()
        if not text:
            raise Stage1FinalError("PDB atom record has blank resid")
        try:
            return int(text)
        except ValueError as exc:
            raise Stage1FinalError(f"unsupported non-integer PDB resid: {text!r}") from exc

    @property
    def insertion_code(self) -> str:
        return self.raw[26:27]

    @property
    def element(self) -> str:
        return self.raw[76:78].strip().upper() if len(self.raw) >= 78 else ""


@dataclass
class ResidueBlock:
    atoms: list[AtomLine]
    key: ResidueKey | None = None
    meta: ResidueMeta | None = None
    linked_block_id: int | None = None

    @property
    def chain_id(self) -> str:
        return self.atoms[0].chain_id

    @property
    def resid(self) -> int:
        return self.atoms[0].resid

    @property
    def residue_name(self) -> str:
        return self.atoms[0].residue_name

    @property
    def insertion_code(self) -> str:
        return self.atoms[0].insertion_code


@dataclass(frozen=True)
class LinkedBlock:
    block_id: int
    component_id: str
    residue_keys: tuple[ResidueKey, ...]
    stable_order: int


class UnionFind:
    def __init__(self, values: list[ResidueKey]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: ResidueKey) -> ResidueKey:
        root = self.parent[value]
        if root != value:
            self.parent[value] = self.find(root)
        return self.parent[value]

    def union(self, first: ResidueKey, second: ResidueKey) -> None:
        if first not in self.parent or second not in self.parent:
            return
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root != second_root:
            self.parent[max(first_root, second_root)] = min(first_root, second_root)

    def groups(self) -> list[set[ResidueKey]]:
        grouped: dict[ResidueKey, set[ResidueKey]] = {}
        for value in self.parent:
            grouped.setdefault(self.find(value), set()).add(value)
        return list(grouped.values())


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Stage1FinalError(f"required YAML file is missing: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise Stage1FinalError(f"cannot parse YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise Stage1FinalError(f"YAML root must be a mapping: {path}")
    return data


def chain_label_for_index(chain_index: int) -> str:
    if chain_index < 1 or chain_index > len(CHAIN_LABELS):
        raise Stage1FinalError(
            f"chain_index {chain_index} cannot be represented by the current PDB chain-label mapping"
        )
    return CHAIN_LABELS[chain_index - 1]


def parse_pdb(path: Path) -> tuple[list[str], list[ResidueBlock]]:
    if not path.is_file():
        raise Stage1FinalError(f"input structure is missing: {path}")

    cryst1: list[str] = []
    blocks: list[ResidueBlock] = []
    current: ResidueBlock | None = None
    seen_keys: set[tuple[str, int, str]] = set()

    def finish_current() -> None:
        nonlocal current
        if current is None:
            return
        key = (current.chain_id, current.resid, current.insertion_code)
        if key in seen_keys:
            raise Stage1FinalError(
                "the same chain/resid/insertion-code occurs in multiple residue blocks: "
                f"{key}"
            )
        seen_keys.add(key)
        blocks.append(current)
        current = None

    for line in path.read_text(encoding="utf-8").splitlines():
        record = line[:6]
        if line.startswith("CRYST1"):
            cryst1.append(line)
            continue
        if record in ATOM_RECORDS:
            if len(line) < 27:
                raise Stage1FinalError("PDB atom record is too short")
            atom = AtomLine(line)
            if atom.element in {"H", "D", "T"}:
                raise Stage1FinalError(
                    "input contains hydrogen/deuterium/tritium atom records; "
                    "1.8 requires a heavy-atom structure"
                )
            atom_key = (
                atom.chain_id,
                atom.resid,
                atom.insertion_code,
                atom.residue_name,
            )
            if current is None:
                current = ResidueBlock(atoms=[atom])
            else:
                current_key = (
                    current.chain_id,
                    current.resid,
                    current.insertion_code,
                    current.residue_name,
                )
                if atom_key == current_key:
                    current.atoms.append(atom)
                else:
                    finish_current()
                    current = ResidueBlock(atoms=[atom])
            continue
        if line.startswith("TER") or line.startswith("END"):
            finish_current()

    finish_current()
    if not blocks:
        raise Stage1FinalError("input PDB contains no ATOM/HETATM records")
    return cryst1, blocks


def classification_maps(
    document: dict[str, Any],
) -> tuple[
    dict[ResidueKey, ResidueMeta],
    list[str],
    dict[str, list[ResidueKey]],
    list[dict[str, Any]],
]:
    if document.get("schema_version") != "4.0":
        raise Stage1FinalError("classification_result.yaml must use schema_version: 4.0")
    if document.get("result_status") != "COMPLETE":
        raise Stage1FinalError("classification_result.yaml must have result_status: COMPLETE")

    components = document.get("components")
    if not isinstance(components, list) or not components:
        raise Stage1FinalError("classification_result.yaml lacks components[]")

    by_key: dict[ResidueKey, ResidueMeta] = {}
    component_order: list[str] = []
    component_residues: dict[str, list[ResidueKey]] = {}
    seen_chain_indices: set[int] = set()
    stable_order = 0

    for component_index, component in enumerate(components):
        if not isinstance(component, dict):
            raise Stage1FinalError("classification component entry must be a mapping")
        component_id = component.get("component_id")
        if not isinstance(component_id, str) or not component_id:
            raise Stage1FinalError("classification component lacks component_id")
        if component_id in component_residues:
            raise Stage1FinalError(f"duplicate component_id: {component_id}")
        try:
            chain_index = int(component["chain_index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Stage1FinalError(f"invalid chain_index for component {component_id}") from exc
        if chain_index in seen_chain_indices:
            raise Stage1FinalError(f"duplicate component chain_index: {chain_index}")
        seen_chain_indices.add(chain_index)

        residues = component.get("residues")
        if not isinstance(residues, list) or not residues:
            raise Stage1FinalError(f"component {component_id} lacks residues[]")

        component_order.append(component_id)
        component_residues[component_id] = []
        seen_residue_ids: set[str] = set()

        for residue_index, residue in enumerate(residues):
            if not isinstance(residue, dict):
                raise Stage1FinalError(
                    f"residue entry in component {component_id} must be a mapping"
                )
            residue_id = residue.get("residue_id")
            if not isinstance(residue_id, str) or not residue_id:
                raise Stage1FinalError(
                    f"residue in component {component_id} lacks residue_id"
                )
            if residue_id in seen_residue_ids:
                raise Stage1FinalError(
                    f"duplicate residue_id inside component {component_id}: {residue_id}"
                )
            seen_residue_ids.add(residue_id)

            polymer = residue.get("polymer_class")
            topology = residue.get("topology_class")
            if not isinstance(polymer, dict) or not isinstance(topology, dict):
                raise Stage1FinalError(
                    f"classification fields are missing for {component_id}/{residue_id}"
                )
            polymer_value = polymer.get("value")
            topology_value = topology.get("value")
            if polymer_value not in {"POLYMER", "BRANCHED", "NONPOLYMER", "WATER"}:
                raise Stage1FinalError(
                    f"invalid polymer_class for {component_id}/{residue_id}"
                )
            if topology_value not in {
                "STANDARD_RESIDUE",
                "TOPOLOGY_LINKED_NONSTANDARD",
                "INDEPENDENT_NONSTANDARD",
                "SOLVENT_COMPONENT",
                "ION_COMPONENT",
            }:
                raise Stage1FinalError(
                    f"invalid topology_class for {component_id}/{residue_id}"
                )

            key = (component_id, residue_id)
            meta = ResidueMeta(
                component_id=component_id,
                residue_id=residue_id,
                chain_index=chain_index,
                polymer_class=polymer_value,
                topology_class=topology_value,
                stable_order=stable_order,
                component_order=component_index,
                residue_order=residue_index,
            )
            by_key[key] = meta
            component_residues[component_id].append(key)
            stable_order += 1

    checks = document.get("topology_linked_checks")
    if not isinstance(checks, list):
        raise Stage1FinalError("classification_result.yaml lacks topology_linked_checks[]")

    return by_key, component_order, component_residues, checks


def target_maps(
    document: dict[str, Any],
    meta_by_key: dict[ResidueKey, ResidueMeta],
) -> tuple[
    str,
    dict[int, str],
    dict[tuple[int, int], ResidueKey],
    set[ResidueKey],
]:
    target_id = document.get("target_id")
    if not isinstance(target_id, str) or not target_id:
        raise Stage1FinalError("target record lacks target_id")

    chain_mapping = document.get("chain_mapping")
    residue_mapping = document.get("residue_mapping")
    if not isinstance(chain_mapping, list) or not isinstance(residue_mapping, list):
        raise Stage1FinalError(
            "target record must contain chain_mapping[] and residue_mapping[]"
        )

    chains: dict[int, str] = {}
    for item in chain_mapping:
        if not isinstance(item, dict):
            raise Stage1FinalError("chain_mapping entries must be mappings")
        try:
            chain_index = int(item["chain_index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Stage1FinalError("invalid chain_index in target chain_mapping") from exc
        chain_id = str(item.get("pdb_chain_id", ""))
        if len(chain_id) != 1:
            raise Stage1FinalError(f"PDB chain ID must be one character: {chain_id!r}")
        expected = chain_label_for_index(chain_index)
        if chain_id != expected:
            raise Stage1FinalError(
                f"target chain_mapping disagrees with 1.3 chain-label mapping for "
                f"chain_index {chain_index}: {chain_id!r} != {expected!r}"
            )
        if chain_index in chains:
            raise Stage1FinalError(
                f"duplicate chain_index in target chain_mapping: {chain_index}"
            )
        chains[chain_index] = chain_id

    residues: dict[tuple[int, int], ResidueKey] = {}
    selected_keys: set[ResidueKey] = set()
    for item in residue_mapping:
        if not isinstance(item, dict):
            raise Stage1FinalError("residue_mapping entries must be mappings")
        try:
            chain_index = int(item["chain_index"])
            resid = int(item["resid"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Stage1FinalError("invalid chain_index/resid in target residue_mapping") from exc
        component_id = item.get("component_id")
        residue_id = item.get("residue_id")
        if not isinstance(component_id, str) or not isinstance(residue_id, str):
            raise Stage1FinalError(
                f"target residue mapping lacks component_id/residue_id: "
                f"{chain_index}/{resid}"
            )
        key = (component_id, residue_id)
        meta = meta_by_key.get(key)
        if meta is None:
            raise Stage1FinalError(
                f"target identity is absent from classification result: "
                f"{component_id}/{residue_id}"
            )
        if meta.chain_index != chain_index:
            raise Stage1FinalError(
                f"target chain_index does not match 1.2 component chain_index for "
                f"{component_id}/{residue_id}"
            )
        mapping_key = (chain_index, resid)
        if mapping_key in residues:
            raise Stage1FinalError(f"duplicate target residue mapping: {mapping_key}")
        if key in selected_keys:
            raise Stage1FinalError(
                f"target residue identity occurs more than once: {component_id}/{residue_id}"
            )
        residues[mapping_key] = key
        selected_keys.add(key)

    return target_id, chains, residues, selected_keys


def bind_blocks(
    blocks: list[ResidueBlock],
    chain_map: dict[int, str],
    residue_map: dict[tuple[int, int], ResidueKey],
    meta_by_key: dict[ResidueKey, ResidueMeta],
) -> dict[ResidueKey, ResidueBlock]:
    chain_index_by_id = {chain_id: index for index, chain_id in chain_map.items()}
    by_key: dict[ResidueKey, ResidueBlock] = {}

    for block in blocks:
        chain_index = chain_index_by_id.get(block.chain_id)
        if chain_index is None:
            raise Stage1FinalError(
                f"current structure chain {block.chain_id!r} is not represented "
                "in target chain_mapping"
            )
        key = residue_map.get((chain_index, block.resid))
        if key is None:
            raise Stage1FinalError(
                f"current residue {block.chain_id}:{block.resid} cannot be bound "
                "through target residue_mapping"
            )
        meta = meta_by_key.get(key)
        if meta is None:
            raise Stage1FinalError(
                f"bound target identity is absent from classification result: {key}"
            )
        block.key = key
        block.meta = meta
        if key in by_key:
            raise Stage1FinalError(
                f"current structure contains duplicate stable identity: {key}"
            )
        by_key[key] = block

    return by_key


def endpoint_key(endpoint: Any) -> ResidueKey:
    if not isinstance(endpoint, dict):
        raise Stage1FinalError("topology-linked check endpoint must be a mapping")
    component_id = endpoint.get("component_id")
    residue_id = endpoint.get("residue_id")
    if not isinstance(component_id, str) or not isinstance(residue_id, str):
        raise Stage1FinalError(
            "topology-linked check endpoint lacks component_id/residue_id"
        )
    return component_id, residue_id


def relation_keys(check: dict[str, Any]) -> tuple[ResidueKey, ResidueKey]:
    relation_type = check.get("relation_type")
    if relation_type == "COVALENT_CONNECTION":
        return endpoint_key(check.get("atom_1")), endpoint_key(check.get("atom_2"))
    if relation_type == "METAL_COORDINATION":
        return endpoint_key(check.get("metal")), endpoint_key(check.get("donor"))
    raise Stage1FinalError(f"unsupported topology-linked relation_type: {relation_type!r}")


def build_linked_blocks(
    meta_by_key: dict[ResidueKey, ResidueMeta],
    checks: list[dict[str, Any]],
    present_blocks: dict[ResidueKey, ResidueBlock],
) -> list[LinkedBlock]:
    linked_keys = [
        key
        for key, block in present_blocks.items()
        if block.meta is not None
        and block.meta.topology_class == "TOPOLOGY_LINKED_NONSTANDARD"
    ]
    uf = UnionFind(linked_keys)

    for check in checks:
        if not isinstance(check, dict):
            raise Stage1FinalError("topology_linked_checks entries must be mappings")
        if check.get("judgment") != "CONFIRMED":
            continue
        if check.get("topology_effect_applied") is not True:
            continue
        first, second = relation_keys(check)
        if first not in meta_by_key or second not in meta_by_key:
            raise Stage1FinalError(
                f"topology-linked check references unknown residue identity: "
                f"{first} / {second}"
            )
        if first in uf.parent and second in uf.parent:
            uf.union(first, second)

    raw_groups = sorted(
        uf.groups(),
        key=lambda group: min(meta_by_key[key].stable_order for key in group),
    )
    blocks: list[LinkedBlock] = []

    for block_id, group in enumerate(raw_groups, start=1):
        ordered = tuple(sorted(group, key=lambda key: meta_by_key[key].stable_order))
        component_ids = {key[0] for key in ordered}
        if len(component_ids) != 1:
            raise Stage1FinalError(
                "a linked nonstandard block spans multiple final 1.2 components; "
                "classification_result component membership is inconsistent"
            )
        component_id = next(iter(component_ids))
        linked_block = LinkedBlock(
            block_id=block_id,
            component_id=component_id,
            residue_keys=ordered,
            stable_order=meta_by_key[ordered[0]].stable_order,
        )
        blocks.append(linked_block)
        for key in ordered:
            present_blocks[key].linked_block_id = block_id

    return blocks


def _make_linked_block_contiguous(
    ordered_keys: list[ResidueKey],
    linked_blocks: list[LinkedBlock],
) -> list[ResidueKey]:
    output = list(ordered_keys)
    for linked_block in sorted(linked_blocks, key=lambda item: item.stable_order):
        present = [key for key in linked_block.residue_keys if key in output]
        if len(present) <= 1:
            continue
        positions = [output.index(key) for key in present]
        anchor = min(positions)
        output = [key for key in output if key not in present]
        for offset, key in enumerate(present):
            output.insert(anchor + offset, key)
    return output


def reorder_blocks(
    component_order: list[str],
    component_residues: dict[str, list[ResidueKey]],
    blocks_by_key: dict[ResidueKey, ResidueBlock],
    linked_blocks: list[LinkedBlock],
) -> list[ResidueBlock]:
    linked_by_component: dict[str, list[LinkedBlock]] = {}
    for linked_block in linked_blocks:
        linked_by_component.setdefault(linked_block.component_id, []).append(linked_block)
    for values in linked_by_component.values():
        values.sort(key=lambda item: item.stable_order)

    output: list[ResidueBlock] = []

    for component_id in component_order:
        formal_keys = component_residues[component_id]
        present_keys = [key for key in formal_keys if key in blocks_by_key]
        if not present_keys:
            continue

        component_linked = linked_by_component.get(component_id, [])
        linked_keys = {
            key for linked_block in component_linked for key in linked_block.residue_keys
        }
        nonlinked_keys = [key for key in present_keys if key not in linked_keys]
        standard_polymer_positions = [
            index
            for index, key in enumerate(nonlinked_keys)
            if blocks_by_key[key].meta is not None
            and blocks_by_key[key].meta.topology_class == "STANDARD_RESIDUE"
            and blocks_by_key[key].meta.polymer_class == "POLYMER"
        ]

        if component_linked and standard_polymer_positions:
            anchor = standard_polymer_positions[-1] + 1
            linked_order: list[ResidueKey] = []
            for linked_block in component_linked:
                linked_order.extend(
                    key for key in linked_block.residue_keys if key in blocks_by_key
                )
            component_keys = (
                nonlinked_keys[:anchor]
                + linked_order
                + nonlinked_keys[anchor:]
            )
        else:
            component_keys = _make_linked_block_contiguous(
                present_keys,
                component_linked,
            )

        output.extend(blocks_by_key[key] for key in component_keys)

    if len(output) != len(blocks_by_key):
        raise Stage1FinalError("final reorder did not preserve every current residue block")
    if len({id(block) for block in output}) != len(output):
        raise Stage1FinalError("final reorder contains duplicate residue blocks")
    return output


def selected_gap_breaks_polymer(
    current: ResidueBlock,
    following: ResidueBlock,
    component_residues: dict[str, list[ResidueKey]],
    selected_keys: set[ResidueKey],
) -> bool:
    if current.key is None or following.key is None:
        raise Stage1FinalError("internal residue identity is missing")
    if current.key[0] != following.key[0]:
        return True

    ordered = component_residues[current.key[0]]
    try:
        first = ordered.index(current.key)
        second = ordered.index(following.key)
    except ValueError as exc:
        raise Stage1FinalError("internal component residue order is inconsistent") from exc

    if second <= first:
        raise Stage1FinalError(
            "standard polymer residue order is not consistent with 1.2 formal residue order"
        )

    return any(key not in selected_keys for key in ordered[first + 1 : second])


def should_write_ter(
    index: int,
    blocks: list[ResidueBlock],
    block: ResidueBlock,
    linked_by_id: dict[int, LinkedBlock],
    component_residues: dict[str, list[ResidueKey]],
    selected_keys: set[ResidueKey],
    present_keys: set[ResidueKey],
) -> bool:
    if block.meta is None or block.key is None:
        raise Stage1FinalError("internal block metadata is missing")

    if block.linked_block_id is not None:
        linked_block = linked_by_id[block.linked_block_id]
        present_order = [key for key in linked_block.residue_keys if key in present_keys]
        return bool(present_order) and block.key == present_order[-1]

    if block.meta.polymer_class != "POLYMER":
        return True

    next_block = blocks[index + 1] if index + 1 < len(blocks) else None
    if next_block is None:
        return True
    if next_block.meta is None or next_block.key is None:
        raise Stage1FinalError("internal next-block metadata is missing")
    if next_block.meta.chain_index != block.meta.chain_index:
        return True
    if next_block.meta.polymer_class != "POLYMER":
        return True
    if block.meta.topology_class != "STANDARD_RESIDUE":
        return True
    if next_block.meta.topology_class != "STANDARD_RESIDUE":
        return True
    return selected_gap_breaks_polymer(
        block,
        next_block,
        component_residues,
        selected_keys,
    )


def rewrite_atom_line(
    atom: AtomLine,
    serial: int,
    record_type: str,
    chain_id: str,
    resid: int,
) -> str:
    if serial > 99999:
        raise Stage1FinalError("PDB atom/TER serial exceeds 99999")
    if resid < -999 or resid > 9999:
        raise Stage1FinalError(f"PDB resid cannot be represented: {resid}")

    raw = atom.raw.ljust(80)
    record = "ATOM  " if record_type == "ATOM" else "HETATM"
    return (
        f"{record}{serial:5d}"
        + raw[11:21]
        + chain_id
        + f"{resid:4d}"
        + raw[26:]
    ).rstrip()


def ter_line(serial: int, block: ResidueBlock) -> str:
    if serial > 99999:
        raise Stage1FinalError("PDB atom/TER serial exceeds 99999")
    icode = block.insertion_code if block.insertion_code else " "
    return (
        f"TER   {serial:5d}      {block.residue_name:>3s} "
        f"{block.chain_id}{block.resid:4d}{icode}"
    )


def materialize_outputs(
    cryst1: list[str],
    blocks: list[ResidueBlock],
    linked_by_id: dict[int, LinkedBlock],
    component_residues: dict[str, list[ResidueKey]],
    selected_keys: set[ResidueKey],
    target_id: str,
    output_structure: Path,
) -> tuple[str, dict[str, Any]]:
    lines = list(cryst1)
    map_atoms: list[dict[str, Any]] = []
    serial = 1
    present_keys = {block.key for block in blocks if block.key is not None}

    for index, block in enumerate(blocks):
        if block.meta is None or block.key is None:
            raise Stage1FinalError("internal block metadata is missing")
        record_type = "ATOM" if block.meta.polymer_class == "POLYMER" else "HETATM"

        for atom in block.atoms:
            lines.append(
                rewrite_atom_line(
                    atom,
                    serial,
                    record_type,
                    block.chain_id,
                    block.resid,
                )
            )
            map_atoms.append(
                {
                    "serial": serial,
                    "chain_id": block.chain_id,
                    "resid": block.resid,
                    "residue_name": atom.residue_name,
                    "atom_name": atom.atom_name,
                    "component_id": block.meta.component_id,
                    "residue_id": block.meta.residue_id,
                }
            )
            serial += 1

        if should_write_ter(
            index,
            blocks,
            block,
            linked_by_id,
            component_residues,
            selected_keys,
            present_keys,
        ):
            lines.append(ter_line(serial, block))
            serial += 1

    lines.append("END")
    mapping = {
        "target_id": target_id,
        "structure": str(output_structure.resolve()),
        "atoms": map_atoms,
    }
    serials = [item["serial"] for item in map_atoms]
    if len(serials) != len(set(serials)):
        raise Stage1FinalError("duplicate atom serial in final map")
    return "\n".join(lines) + "\n", mapping


def atomic_write_pair(
    structure_path: Path,
    structure_text: str,
    map_path: Path,
    mapping: dict[str, Any],
) -> None:
    structure_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_text = yaml.safe_dump(mapping, sort_keys=False, allow_unicode=True)

    temp_paths: list[Path] = []
    try:
        for final_path, text in (
            (structure_path, structure_text),
            (map_path, map_text),
        ):
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{final_path.name}.",
                suffix=".tmp",
                dir=str(final_path.parent),
                text=True,
            )
            os.close(fd)
            temp = Path(temp_name)
            temp.write_text(text, encoding="utf-8")
            temp_paths.append(temp)
        os.replace(temp_paths[0], structure_path)
        os.replace(temp_paths[1], map_path)
        temp_paths.clear()
    finally:
        for temp in temp_paths:
            try:
                temp.unlink()
            except FileNotFoundError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build stage1_final.pdb and stage1_final_map.yaml for Skill 1.8."
    )
    parser.add_argument("--input-structure", required=True, type=Path)
    parser.add_argument("--target-record", required=True, type=Path)
    parser.add_argument("--classification-result", required=True, type=Path)
    parser.add_argument("--output-structure", required=True, type=Path)
    parser.add_argument("--output-map", required=True, type=Path)
    args = parser.parse_args()

    try:
        classification = read_yaml(args.classification_result.resolve())
        (
            meta_by_key,
            component_order,
            component_residues,
            topology_checks,
        ) = classification_maps(classification)

        target = read_yaml(args.target_record.resolve())
        (
            target_id,
            chain_map,
            residue_map,
            selected_keys,
        ) = target_maps(target, meta_by_key)

        cryst1, blocks = parse_pdb(args.input_structure.resolve())
        input_atom_count = sum(len(block.atoms) for block in blocks)
        blocks_by_key = bind_blocks(
            blocks,
            chain_map,
            residue_map,
            meta_by_key,
        )

        linked_blocks = build_linked_blocks(
            meta_by_key,
            topology_checks,
            blocks_by_key,
        )
        linked_by_id = {block.block_id: block for block in linked_blocks}

        ordered_blocks = reorder_blocks(
            component_order,
            component_residues,
            blocks_by_key,
            linked_blocks,
        )

        pdb_text, mapping = materialize_outputs(
            cryst1,
            ordered_blocks,
            linked_by_id,
            component_residues,
            selected_keys,
            target_id,
            args.output_structure.resolve(),
        )

        if len(mapping["atoms"]) != input_atom_count:
            raise Stage1FinalError(
                "final output does not preserve the input atom set one-to-one"
            )

        atomic_write_pair(
            args.output_structure.resolve(),
            pdb_text,
            args.output_map.resolve(),
            mapping,
        )
        return 0
    except Stage1FinalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

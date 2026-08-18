#!/usr/bin/env python3
"""Build Stage 1 final heavy-atom PDB and stable identity map for Skill 1.8."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to run build_stage1_final.py") from exc


CHAIN_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
ATOM_RECORDS = {"ATOM  ", "HETATM"}


class Stage1FinalError(RuntimeError):
    pass


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
    input_ter_after: bool = False
    chain_index: int | None = None
    component_id: str | None = None
    residue_id: str | None = None
    topology_class: str | None = None
    polymer_class: str | None = None
    stable_order: int | None = None
    final_chain_id: str | None = None
    final_resid: int | None = None
    linked_unit_id: int | None = None

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


@dataclass
class LinkedUnit:
    unit_id: int
    residue_ids: list[str]
    stable_order: int
    standard_chain_indices: set[int] = field(default_factory=set)
    assigned_standard_chain_index: int | None = None
    independent: bool = False


class UnionFind:
    def __init__(self, values: list[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        root = self.parent[value]
        if root != value:
            self.parent[value] = self.find(root)
        return self.parent[value]

    def union(self, first: str, second: str) -> None:
        if first not in self.parent or second not in self.parent:
            return
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root != second_root:
            self.parent[max(first_root, second_root)] = min(first_root, second_root)

    def groups(self) -> list[set[str]]:
        groups: dict[str, set[str]] = {}
        for value in self.parent:
            groups.setdefault(self.find(value), set()).add(value)
        return list(groups.values())


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
                    "input contains hydrogen/deuterium/tritium atom records; 1.8 requires a heavy-atom structure"
                )
            key = (atom.chain_id, atom.resid, atom.insertion_code, atom.residue_name)
            if current is None:
                current = ResidueBlock(atoms=[atom])
            else:
                current_key = (
                    current.chain_id,
                    current.resid,
                    current.insertion_code,
                    current.residue_name,
                )
                if key == current_key:
                    current.atoms.append(atom)
                else:
                    finish_current()
                    current = ResidueBlock(atoms=[atom])
            continue
        if line.startswith("TER"):
            if current is not None:
                current.input_ter_after = True
                finish_current()
            continue
        if line.startswith("END"):
            finish_current()
            continue

    finish_current()
    if not blocks:
        raise Stage1FinalError("input PDB contains no ATOM/HETATM records")
    return cryst1, blocks


def classification_maps(
    document: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    if document.get("result_status") != "COMPLETE":
        raise Stage1FinalError("classification_result.yaml must have result_status: COMPLETE")
    records = document.get("residue_records")
    if not isinstance(records, list):
        raise Stage1FinalError("classification_result.yaml lacks residue_records[]")

    by_id: dict[str, dict[str, Any]] = {}
    order: dict[str, int] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise Stage1FinalError("classification residue record must be a mapping")
        residue_id = record.get("residue_id")
        if not isinstance(residue_id, str) or not residue_id:
            raise Stage1FinalError("classification residue record lacks residue_id")
        if residue_id in by_id:
            raise Stage1FinalError(f"duplicate residue_id in classification result: {residue_id}")
        classification = record.get("classification")
        if not isinstance(classification, dict):
            raise Stage1FinalError(f"classification mapping is missing for residue {residue_id}")
        if classification.get("polymer_class") not in {
            "POLYMER",
            "BRANCHED",
            "NONPOLYMER",
            "WATER",
        }:
            raise Stage1FinalError(f"invalid polymer_class for residue {residue_id}")
        if classification.get("topology_class") not in {
            "STANDARD_RESIDUE",
            "TOPOLOGY_LINKED_NONSTANDARD",
            "INDEPENDENT_NONSTANDARD",
            "SOLVENT_COMPONENT",
            "ION_COMPONENT",
        }:
            raise Stage1FinalError(f"invalid topology_class for residue {residue_id}")
        by_id[residue_id] = record
        order[residue_id] = index
    return by_id, order


def target_maps(
    document: dict[str, Any],
) -> tuple[str, dict[int, str], dict[tuple[int, int], dict[str, Any]]]:
    target_id = document.get("target_id")
    if not isinstance(target_id, str) or not target_id:
        raise Stage1FinalError("target record lacks target_id")

    chain_mapping = document.get("chain_mapping")
    residue_mapping = document.get("residue_mapping")
    if not isinstance(chain_mapping, list) or not isinstance(residue_mapping, list):
        raise Stage1FinalError("target record must contain chain_mapping[] and residue_mapping[]")

    chains: dict[int, str] = {}
    for item in chain_mapping:
        if not isinstance(item, dict):
            raise Stage1FinalError("chain_mapping entries must be mappings")
        chain_index = int(item["chain_index"])
        chain_id = str(item["pdb_chain_id"])
        if len(chain_id) != 1:
            raise Stage1FinalError(f"PDB chain ID must be one character: {chain_id!r}")
        expected = chain_label_for_index(chain_index)
        if chain_id != expected:
            raise Stage1FinalError(
                f"target chain_mapping disagrees with the fixed 1.3 mapping for chain_index "
                f"{chain_index}: {chain_id!r} != {expected!r}"
            )
        if chain_index in chains:
            raise Stage1FinalError(f"duplicate chain_index in target chain_mapping: {chain_index}")
        chains[chain_index] = chain_id

    residues: dict[tuple[int, int], dict[str, Any]] = {}
    seen_residue_ids: set[str] = set()
    for item in residue_mapping:
        if not isinstance(item, dict):
            raise Stage1FinalError("residue_mapping entries must be mappings")
        chain_index = int(item["chain_index"])
        resid = int(item["resid"])
        key = (chain_index, resid)
        if key in residues:
            raise Stage1FinalError(f"duplicate target residue mapping: {key}")
        residue_id = item.get("residue_id")
        component_id = item.get("component_id")
        if not isinstance(residue_id, str) or not isinstance(component_id, str):
            raise Stage1FinalError(f"target residue mapping lacks stable IDs: {key}")
        if residue_id in seen_residue_ids:
            raise Stage1FinalError(f"target residue_id occurs more than once: {residue_id}")
        seen_residue_ids.add(residue_id)
        residues[key] = item
    return target_id, chains, residues


def bind_blocks(
    blocks: list[ResidueBlock],
    chain_map: dict[int, str],
    residue_map: dict[tuple[int, int], dict[str, Any]],
    class_by_id: dict[str, dict[str, Any]],
    stable_order: dict[str, int],
) -> dict[str, ResidueBlock]:
    chain_index_by_id = {chain_id: index for index, chain_id in chain_map.items()}
    by_residue_id: dict[str, ResidueBlock] = {}

    for block in blocks:
        if block.chain_id not in chain_index_by_id:
            raise Stage1FinalError(
                f"current structure chain {block.chain_id!r} is not represented in target chain_mapping"
            )
        chain_index = chain_index_by_id[block.chain_id]
        mapping = residue_map.get((chain_index, block.resid))
        if mapping is None:
            raise Stage1FinalError(
                f"current residue {block.chain_id}:{block.resid} cannot be bound through target residue_mapping"
            )

        residue_id = mapping["residue_id"]
        record = class_by_id.get(residue_id)
        if record is None:
            raise Stage1FinalError(f"target residue_id is absent from classification result: {residue_id}")
        if record.get("component_id") != mapping["component_id"]:
            raise Stage1FinalError(f"component_id mismatch for residue_id {residue_id}")

        classification = record["classification"]
        block.chain_index = chain_index
        block.component_id = mapping["component_id"]
        block.residue_id = residue_id
        block.topology_class = classification["topology_class"]
        block.polymer_class = classification["polymer_class"]
        block.stable_order = stable_order[residue_id]
        block.final_chain_id = block.chain_id
        block.final_resid = block.resid

        if residue_id in by_residue_id:
            raise Stage1FinalError(f"current structure contains duplicate residue_id: {residue_id}")
        by_residue_id[residue_id] = block

    return by_residue_id


def topology_relations(document: dict[str, Any]) -> list[dict[str, Any]]:
    confirmed = document.get("confirmed_relations", {})
    if not isinstance(confirmed, dict):
        raise Stage1FinalError("classification_result confirmed_relations must be a mapping")

    result: list[dict[str, Any]] = []
    for key in ("covalent_connections", "metal_coordination"):
        values = confirmed.get(key, [])
        if not isinstance(values, list):
            raise Stage1FinalError(f"confirmed_relations.{key} must be a list")
        for relation in values:
            if not isinstance(relation, dict):
                raise Stage1FinalError("confirmed relation entry must be a mapping")
            if relation.get("topology_effect_applied") is True:
                result.append(relation)
    return result


def endpoint_residue_ids(relation: dict[str, Any]) -> tuple[str, str]:
    first = relation.get("endpoint_1")
    second = relation.get("endpoint_2")
    if not isinstance(first, dict) or not isinstance(second, dict):
        raise Stage1FinalError("confirmed topology relation lacks endpoint_1/endpoint_2")
    first_id = first.get("residue_id")
    second_id = second.get("residue_id")
    if not isinstance(first_id, str) or not isinstance(second_id, str):
        raise Stage1FinalError("confirmed topology relation endpoint lacks residue_id")
    return first_id, second_id


def build_linked_units(
    class_by_id: dict[str, dict[str, Any]],
    stable_order: dict[str, int],
    relations: list[dict[str, Any]],
) -> tuple[list[LinkedUnit], dict[str, int]]:
    all_ids = list(class_by_id)
    uf = UnionFind(all_ids)
    for relation in relations:
        first_id, second_id = endpoint_residue_ids(relation)
        if first_id in class_by_id and second_id in class_by_id:
            uf.union(first_id, second_id)

    standard_chain_indices = {
        int(record["chain_index"])
        for record in class_by_id.values()
        if record["classification"]["topology_class"] == "STANDARD_RESIDUE"
    }

    raw_units: list[tuple[list[str], set[int]]] = []
    for component in uf.groups():
        linked_ids = [
            residue_id
            for residue_id in component
            if class_by_id[residue_id]["classification"]["topology_class"]
            == "TOPOLOGY_LINKED_NONSTANDARD"
        ]
        if not linked_ids:
            continue
        linked_ids.sort(key=lambda residue_id: stable_order[residue_id])
        standard_sides = {
            int(class_by_id[residue_id]["chain_index"])
            for residue_id in component
            if class_by_id[residue_id]["classification"]["topology_class"] == "STANDARD_RESIDUE"
        }
        if not standard_sides:
            # Baseline linked residues can already belong to a polymer chain in the
            # final 1.2 grouping even when no explicit topology relation is present.
            linked_chain_indices = {int(class_by_id[residue_id]["chain_index"]) for residue_id in linked_ids}
            standard_sides.update(linked_chain_indices & standard_chain_indices)
        raw_units.append((linked_ids, standard_sides))

    raw_units.sort(key=lambda item: stable_order[item[0][0]])
    units: list[LinkedUnit] = []
    residue_to_unit: dict[str, int] = {}
    for unit_id, (residue_ids, standard_sides) in enumerate(raw_units, start=1):
        unit = LinkedUnit(
            unit_id=unit_id,
            residue_ids=residue_ids,
            stable_order=stable_order[residue_ids[0]],
            standard_chain_indices=standard_sides,
        )
        if len(standard_sides) == 1:
            unit.assigned_standard_chain_index = next(iter(standard_sides))
        else:
            unit.independent = True
        units.append(unit)
        for residue_id in residue_ids:
            residue_to_unit[residue_id] = unit_id

    return units, residue_to_unit


def keep_present_units(
    units: list[LinkedUnit],
    residue_to_unit: dict[str, int],
    blocks_by_residue_id: dict[str, ResidueBlock],
) -> tuple[list[LinkedUnit], dict[str, int]]:
    present_unit_ids = {
        residue_to_unit[residue_id]
        for residue_id in blocks_by_residue_id
        if residue_id in residue_to_unit
    }
    filtered_units = [unit for unit in units if unit.unit_id in present_unit_ids]
    filtered_mapping = {
        residue_id: unit_id
        for residue_id, unit_id in residue_to_unit.items()
        if unit_id in present_unit_ids
    }
    return filtered_units, filtered_mapping


def choose_independent_chain_id(
    unit: LinkedUnit,
    blocks_by_residue_id: dict[str, ResidueBlock],
    class_by_id: dict[str, dict[str, Any]],
    used_chain_ids: set[str],
    forbidden_chain_ids: set[str],
) -> str:
    present = [blocks_by_residue_id[rid] for rid in unit.residue_ids if rid in blocks_by_residue_id]
    existing = {block.chain_id for block in present}
    if len(existing) == 1:
        candidate = next(iter(existing))
        if candidate not in forbidden_chain_ids:
            used_chain_ids.add(candidate)
            return candidate

    class_indices = {int(class_by_id[rid]["chain_index"]) for rid in unit.residue_ids}
    if len(class_indices) == 1:
        candidate = chain_label_for_index(next(iter(class_indices)))
        if candidate not in forbidden_chain_ids and candidate not in used_chain_ids:
            used_chain_ids.add(candidate)
            return candidate

    for candidate in CHAIN_LABELS:
        if candidate not in used_chain_ids and candidate not in forbidden_chain_ids:
            used_chain_ids.add(candidate)
            return candidate
    raise Stage1FinalError("no unused one-character PDB chain ID is available for an independent linked unit")


def assign_chain_and_resid(
    units: list[LinkedUnit],
    residue_to_unit: dict[str, int],
    blocks_by_residue_id: dict[str, ResidueBlock],
    class_by_id: dict[str, dict[str, Any]],
    chain_map: dict[int, str],
    residue_map: dict[tuple[int, int], dict[str, Any]],
) -> dict[int, LinkedUnit]:
    unit_by_id = {unit.unit_id: unit for unit in units}
    for residue_id, unit_id in residue_to_unit.items():
        block = blocks_by_residue_id.get(residue_id)
        if block is not None:
            block.linked_unit_id = unit_id

    used_chain_ids = {block.chain_id for block in blocks_by_residue_id.values()}

    for unit in units:
        if unit.assigned_standard_chain_index is None:
            continue
        chain_index = unit.assigned_standard_chain_index
        chain_id = chain_map.get(chain_index, chain_label_for_index(chain_index))
        for residue_id in unit.residue_ids:
            block = blocks_by_residue_id.get(residue_id)
            if block is not None:
                block.final_chain_id = chain_id
        used_chain_ids.add(chain_id)

    for unit in units:
        if not unit.independent:
            continue
        forbidden = {
            chain_map.get(index, chain_label_for_index(index))
            for index in unit.standard_chain_indices
        }
        chain_id = choose_independent_chain_id(
            unit,
            blocks_by_residue_id,
            class_by_id,
            used_chain_ids,
            forbidden,
        )
        for residue_id in unit.residue_ids:
            block = blocks_by_residue_id.get(residue_id)
            if block is not None:
                block.final_chain_id = chain_id

    units_by_standard_chain: dict[int, list[LinkedUnit]] = {}
    for unit in units:
        if unit.assigned_standard_chain_index is not None:
            units_by_standard_chain.setdefault(unit.assigned_standard_chain_index, []).append(unit)

    for chain_index, chain_units in units_by_standard_chain.items():
        chain_id = chain_map.get(chain_index, chain_label_for_index(chain_index))
        assigned_ids = {
            residue_id
            for unit in chain_units
            for residue_id in unit.residue_ids
        }
        reserved_resids = {
            resid
            for (mapped_chain_index, resid), mapping in residue_map.items()
            if mapped_chain_index == chain_index and mapping["residue_id"] not in assigned_ids
        }
        next_resid = max(reserved_resids, default=0) + 1
        for unit in sorted(chain_units, key=lambda item: item.stable_order):
            for residue_id in unit.residue_ids:
                block = blocks_by_residue_id.get(residue_id)
                if block is None:
                    continue
                if next_resid > 9999:
                    raise Stage1FinalError(f"final resid exceeds PDB field width on chain {chain_id!r}")
                block.final_resid = next_resid
                next_resid += 1

    return unit_by_id


def normalize_polymer_ter_boundaries(
    blocks: list[ResidueBlock],
    unit_by_id: dict[int, LinkedUnit],
    chain_map: dict[int, str],
) -> None:
    for index, block in enumerate(blocks[:-1]):
        if block.polymer_class != "POLYMER" or not block.input_ter_after:
            continue
        next_block = blocks[index + 1]
        if next_block.linked_unit_id is None:
            continue
        unit = unit_by_id.get(next_block.linked_unit_id)
        if unit is None or unit.assigned_standard_chain_index is None:
            continue
        assigned_chain_id = chain_map.get(
            unit.assigned_standard_chain_index,
            chain_label_for_index(unit.assigned_standard_chain_index),
        )
        if block.final_chain_id == assigned_chain_id:
            # The old TER separated polymer from a linked object at its pre-1.8
            # position. After moving the linked unit, final writing will create the
            # correct boundary at the new end of the polymer block.
            block.input_ter_after = False


def reorder_blocks(
    blocks: list[ResidueBlock],
    units: list[LinkedUnit],
    blocks_by_residue_id: dict[str, ResidueBlock],
    chain_map: dict[int, str],
) -> list[ResidueBlock]:
    assigned_residue_ids = {
        residue_id
        for unit in units
        if unit.assigned_standard_chain_index is not None
        for residue_id in unit.residue_ids
        if residue_id in blocks_by_residue_id
    }
    remaining = [block for block in blocks if block.residue_id not in assigned_residue_ids]

    # Independent linked units stay at their established object position, but multi-residue
    # units are kept contiguous in stable residue order.
    for unit in sorted((u for u in units if u.independent), key=lambda item: item.stable_order):
        present = [blocks_by_residue_id[rid] for rid in unit.residue_ids if rid in blocks_by_residue_id]
        if len(present) <= 1:
            continue
        positions = [remaining.index(block) for block in present if block in remaining]
        if not positions:
            continue
        anchor = min(positions)
        remaining = [block for block in remaining if block not in present]
        for offset, block in enumerate(present):
            remaining.insert(anchor + offset, block)

    units_by_chain: dict[int, list[LinkedUnit]] = {}
    for unit in units:
        if unit.assigned_standard_chain_index is not None:
            units_by_chain.setdefault(unit.assigned_standard_chain_index, []).append(unit)
    for values in units_by_chain.values():
        values.sort(key=lambda item: item.stable_order)

    last_standard_block_by_chain: dict[int, ResidueBlock] = {}
    for chain_index in units_by_chain:
        chain_id = chain_map.get(chain_index, chain_label_for_index(chain_index))
        candidates = [
            block
            for block in remaining
            if block.final_chain_id == chain_id
            and block.topology_class == "STANDARD_RESIDUE"
            and block.polymer_class == "POLYMER"
        ]
        if not candidates:
            raise Stage1FinalError(
                "a linked unit is assigned to a standard chain that has no selected standard "
                f"polymer residue in the current target: chain_index {chain_index}"
            )
        last_standard_block_by_chain[chain_index] = candidates[-1]

    output: list[ResidueBlock] = []
    for block in remaining:
        output.append(block)
        for chain_index, anchor in last_standard_block_by_chain.items():
            if block is not anchor:
                continue
            for unit in units_by_chain[chain_index]:
                for residue_id in unit.residue_ids:
                    linked_block = blocks_by_residue_id.get(residue_id)
                    if linked_block is not None:
                        output.append(linked_block)

    if len(output) != len(blocks) or len({id(block) for block in output}) != len(blocks):
        raise Stage1FinalError("internal reorder did not preserve a one-to-one residue-block set")
    return output


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
    chain_id = block.final_chain_id or block.chain_id
    resid = block.final_resid if block.final_resid is not None else block.resid
    icode = block.insertion_code if block.insertion_code else " "
    return f"TER   {serial:5d}      {block.residue_name:>3s} {chain_id}{resid:4d}{icode}"


def should_write_ter(
    index: int,
    blocks: list[ResidueBlock],
    block: ResidueBlock,
    unit_by_id: dict[int, LinkedUnit],
) -> bool:
    if block.linked_unit_id is not None:
        unit = unit_by_id[block.linked_unit_id]
        present = {
            candidate.residue_id
            for candidate in blocks
            if candidate.linked_unit_id == unit.unit_id
        }
        present_order = [residue_id for residue_id in unit.residue_ids if residue_id in present]
        return bool(present_order) and block.residue_id == present_order[-1]

    if block.polymer_class == "POLYMER":
        if block.input_ter_after:
            return True
        next_block = blocks[index + 1] if index + 1 < len(blocks) else None
        if next_block is None:
            return True
        if next_block.final_chain_id != block.final_chain_id:
            return True
        if next_block.polymer_class != "POLYMER":
            return True
        return False

    return True


def materialize_outputs(
    cryst1: list[str],
    blocks: list[ResidueBlock],
    unit_by_id: dict[int, LinkedUnit],
    target_id: str,
    output_structure: Path,
) -> tuple[str, dict[str, Any]]:
    lines = list(cryst1)
    map_atoms: list[dict[str, Any]] = []
    serial = 1

    for index, block in enumerate(blocks):
        chain_id = block.final_chain_id or block.chain_id
        resid = block.final_resid if block.final_resid is not None else block.resid
        record_type = "ATOM" if block.polymer_class == "POLYMER" else "HETATM"

        for atom in block.atoms:
            lines.append(rewrite_atom_line(atom, serial, record_type, chain_id, resid))
            map_atoms.append(
                {
                    "serial": serial,
                    "chain_id": chain_id,
                    "resid": resid,
                    "residue_name": atom.residue_name,
                    "atom_name": atom.atom_name,
                    "component_id": block.component_id,
                    "residue_id": block.residue_id,
                }
            )
            serial += 1

        if should_write_ter(index, blocks, block, unit_by_id):
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
        for final_path, text in ((structure_path, structure_text), (map_path, map_text)):
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
        target = read_yaml(args.target_record.resolve())
        classification = read_yaml(args.classification_result.resolve())
        target_id, chain_map, residue_map = target_maps(target)
        class_by_id, stable_order = classification_maps(classification)

        cryst1, blocks = parse_pdb(args.input_structure.resolve())
        input_atom_count = sum(len(block.atoms) for block in blocks)
        blocks_by_residue_id = bind_blocks(
            blocks,
            chain_map,
            residue_map,
            class_by_id,
            stable_order,
        )

        units, residue_to_unit = build_linked_units(
            class_by_id,
            stable_order,
            topology_relations(classification),
        )
        units, residue_to_unit = keep_present_units(
            units,
            residue_to_unit,
            blocks_by_residue_id,
        )
        unit_by_id = assign_chain_and_resid(
            units,
            residue_to_unit,
            blocks_by_residue_id,
            class_by_id,
            chain_map,
            residue_map,
        )
        normalize_polymer_ter_boundaries(blocks, unit_by_id, chain_map)
        ordered_blocks = reorder_blocks(
            blocks,
            units,
            blocks_by_residue_id,
            chain_map,
        )
        pdb_text, mapping = materialize_outputs(
            cryst1,
            ordered_blocks,
            unit_by_id,
            target_id,
            args.output_structure.resolve(),
        )

        if len(mapping["atoms"]) != input_atom_count:
            raise Stage1FinalError("final output does not preserve the input atom set one-to-one")

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
    except Exception as exc:  # pragma: no cover - CLI defensive boundary
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

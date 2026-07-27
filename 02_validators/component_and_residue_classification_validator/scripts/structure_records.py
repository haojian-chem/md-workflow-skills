#!/usr/bin/env python3
"""Natural structure identity records shared by relation and classification tools."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import gemmi

from classification_common import ClassificationToolError, model_id


def clean_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text in {"", "\x00", ".", "?"} or not text.strip():
        return None
    return text.strip()


def source_resid_from_residue(residue: gemmi.Residue) -> dict[str, str | None]:
    return {
        "number": str(residue.seqid.num),
        "insertion_code": clean_optional_text(residue.seqid.icode),
    }


def source_resid_key(source_resid: dict[str, Any]) -> tuple[str, str | None]:
    return str(source_resid["number"]), clean_optional_text(source_resid.get("insertion_code"))


@dataclass(frozen=True)
class AtomRecord:
    model_id: str
    source_chain_id: str
    source_resid_number: str
    insertion_code: str | None
    residue_name: str
    atom_name: str
    altloc_id: str | None
    element: str | None
    serial: int
    chain_position: int
    residue_position: int
    atom_position: int
    atom: gemmi.Atom

    @property
    def residue_key(self) -> tuple[str, str, str, str | None, str]:
        return (
            self.model_id,
            self.source_chain_id,
            self.source_resid_number,
            self.insertion_code,
            self.residue_name,
        )

    @property
    def atom_key(self) -> tuple[str, str, str, str | None, str, str, str | None]:
        return (*self.residue_key, self.atom_name, self.altloc_id)

    @property
    def base_atom_key(self) -> tuple[str, str, str, str | None, str, str]:
        return (*self.residue_key, self.atom_name)


@dataclass
class ResidueRecord:
    model_id: str
    source_chain_id: str
    source_resid_number: str
    insertion_code: str | None
    residue_name: str
    entity_id: str | None
    entity_type: gemmi.EntityType
    polymer_type: gemmi.PolymerType
    label_seq: int | None
    chain_position: int
    residue_position: int
    residue: gemmi.Residue
    atoms: list[AtomRecord]

    @property
    def residue_key(self) -> tuple[str, str, str, str | None, str]:
        return (
            self.model_id,
            self.source_chain_id,
            self.source_resid_number,
            self.insertion_code,
            self.residue_name,
        )

    @property
    def altloc_ids(self) -> list[str]:
        return sorted({atom.altloc_id for atom in self.atoms if atom.altloc_id is not None})

    @property
    def has_multiple_conformations(self) -> bool:
        return len(self.altloc_ids) > 1


def _entity_data(
    structure: gemmi.Structure,
    model: gemmi.Model,
    residue: gemmi.Residue,
) -> tuple[str | None, gemmi.EntityType, gemmi.PolymerType]:
    entity_id = clean_optional_text(residue.entity_id)
    entity_type = residue.entity_type
    polymer_type = gemmi.PolymerType.Unknown
    if residue.subchain:
        try:
            entity = structure.get_entity_of(model.get_subchain(residue.subchain))
            entity_id = clean_optional_text(entity.name) or entity_id
            entity_type = entity.entity_type
            polymer_type = entity.polymer_type
        except Exception:
            pass
    return entity_id, entity_type, polymer_type


def selected_model(structure: gemmi.Structure, selected_model_id: str) -> gemmi.Model:
    matches = [model for model in structure if model_id(model) == selected_model_id]
    if len(matches) != 1:
        raise ClassificationToolError(
            f"selected model {selected_model_id!r} resolved to {len(matches)} models"
        )
    return matches[0]


def collect_selected_model(
    structure: gemmi.Structure,
    selected_model_id: str,
) -> tuple[gemmi.Model, list[ResidueRecord], dict[int, list[AtomRecord]]]:
    try:
        structure.setup_entities()
    except Exception:
        try:
            structure.add_entity_types(overwrite=True)
        except Exception:
            pass
    model = selected_model(structure, selected_model_id)
    residues: list[ResidueRecord] = []
    atoms_by_serial: dict[int, list[AtomRecord]] = {}
    for chain_position, chain in enumerate(model):
        source_chain_id = str(chain.name)
        for residue_position, residue in enumerate(chain):
            entity_id, entity_type, polymer_type = _entity_data(structure, model, residue)
            source_resid = source_resid_from_residue(residue)
            atom_records: list[AtomRecord] = []
            for atom_position, atom in enumerate(residue):
                element = clean_optional_text(atom.element.name)
                record = AtomRecord(
                    model_id=selected_model_id,
                    source_chain_id=source_chain_id,
                    source_resid_number=str(source_resid["number"]),
                    insertion_code=source_resid["insertion_code"],
                    residue_name=str(residue.name),
                    atom_name=str(atom.name).strip(),
                    altloc_id=clean_optional_text(atom.altloc),
                    element=element,
                    serial=int(atom.serial),
                    chain_position=chain_position,
                    residue_position=residue_position,
                    atom_position=atom_position,
                    atom=atom,
                )
                atom_records.append(record)
                if record.serial > 0:
                    atoms_by_serial.setdefault(record.serial, []).append(record)
            label_seq = int(residue.label_seq) if residue.label_seq is not None else None
            residues.append(
                ResidueRecord(
                    model_id=selected_model_id,
                    source_chain_id=source_chain_id,
                    source_resid_number=str(source_resid["number"]),
                    insertion_code=source_resid["insertion_code"],
                    residue_name=str(residue.name),
                    entity_id=entity_id,
                    entity_type=entity_type,
                    polymer_type=polymer_type,
                    label_seq=label_seq,
                    chain_position=chain_position,
                    residue_position=residue_position,
                    residue=residue,
                    atoms=atom_records,
                )
            )
    if not residues:
        raise ClassificationToolError(f"selected model {selected_model_id!r} has no residues")
    return model, residues, atoms_by_serial


def natural_residue_key(
    source_chain_id: str | None,
    source_resid: dict[str, Any],
    residue_name: str,
) -> tuple[str | None, str, str | None, str]:
    number, insertion = source_resid_key(source_resid)
    return source_chain_id, number, insertion, residue_name


def build_chain_index_resolver(observations: dict[str, Any]) -> dict[tuple[str | None, str, str | None, str], int]:
    resolver: dict[tuple[str | None, str, str | None, str], int] = {}
    for residue in observations.get("residue_records", []):
        if residue.get("presence_status") != "OBSERVED":
            continue
        key = natural_residue_key(
            residue.get("source_chain_id"),
            residue["source_resid"],
            residue["residue_name"],
        )
        resolver[key] = int(residue["chain_index"])
    grouped_by_name: dict[str, int] = {}
    for group in observations.get("chain_groups", []):
        if group.get("group_type") in {
            "SOLVENT_GROUP",
            "ION_GROUP",
            "REPEATED_SMALL_MOLECULE_GROUP",
        } and isinstance(group.get("residue_name"), str):
            grouped_by_name[group["residue_name"]] = int(group["chain_index"])
    resolver[(None, "*", None, "__GROUPED_BY_NAME__")] = -1
    for name, index in grouped_by_name.items():
        resolver[(None, "*", None, name)] = index
    return resolver


def resolve_chain_index(
    resolver: dict[tuple[str | None, str, str | None, str], int],
    atom: AtomRecord,
) -> int:
    exact = (
        atom.source_chain_id,
        atom.source_resid_number,
        atom.insertion_code,
        atom.residue_name,
    )
    if exact in resolver:
        return resolver[exact]
    grouped = (None, "*", None, atom.residue_name)
    if grouped in resolver:
        return resolver[grouped]
    raise ClassificationToolError(
        "classification observations do not provide a baseline chain_index for "
        f"{atom.source_chain_id}:{atom.source_resid_number}{atom.insertion_code or ''}:{atom.residue_name}"
    )


def endpoint_dict(
    atom: AtomRecord,
    chain_index: int,
    *,
    include_element: bool = False,
    expected_element: str | None = None,
    element_source: str | None = "STRUCTURE_ELEMENT_FIELD",
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "chain_index": chain_index,
        "source_chain_id": atom.source_chain_id,
        "source_resid": {
            "number": atom.source_resid_number,
            "insertion_code": atom.insertion_code,
        },
        "residue_name": atom.residue_name,
        "atom_name": atom.atom_name,
        "altloc_id": atom.altloc_id,
    }
    if include_element:
        output.update(
            {
                "expected_element": expected_element,
                "observed_element": atom.element,
                "element_source": element_source if atom.element is not None else None,
            }
        )
    return output


def distance_angstrom(first: AtomRecord, second: AtomRecord) -> float:
    return float(first.atom.pos.dist(second.atom.pos))


def residue_is_multiple_conformation(
    residue_lookup: dict[tuple[str, str, str, str | None, str], ResidueRecord],
    atom: AtomRecord,
) -> bool:
    residue = residue_lookup.get(atom.residue_key)
    return bool(residue and residue.has_multiple_conformations)


def atoms_matching(
    residues: Iterable[ResidueRecord],
    residue_name: str,
    atom_name: str,
) -> tuple[list[ResidueRecord], list[AtomRecord], list[ResidueRecord]]:
    matching_residues = [residue for residue in residues if residue.residue_name == residue_name]
    atoms: list[AtomRecord] = []
    missing_atom_residues: list[ResidueRecord] = []
    for residue in matching_residues:
        matched = [atom for atom in residue.atoms if atom.atom_name == atom_name]
        if matched:
            atoms.extend(matched)
        else:
            missing_atom_residues.append(residue)
    return matching_residues, atoms, missing_atom_residues

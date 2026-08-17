#!/usr/bin/env python3
"""Resolve explicit PDB/mmCIF relation records to natural atom identities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import gemmi

from structure_records import AtomRecord, ResidueRecord, clean_optional_text


@dataclass(frozen=True)
class ExplicitRelationEvidence:
    source_type: str
    relation_type: str
    altloc_specific: bool
    source_summary: str


def _relation_type(connection_type: gemmi.ConnectionType) -> str:
    mapping = {
        gemmi.ConnectionType.Covale: "COVALENT",
        gemmi.ConnectionType.Disulf: "DISULFIDE",
        gemmi.ConnectionType.MetalC: "METAL_COORDINATION",
        gemmi.ConnectionType.Hydrog: "HYDROGEN_BOND",
        gemmi.ConnectionType.Unknown: "OTHER_EXPLICIT",
    }
    return mapping.get(connection_type, "OTHER_EXPLICIT")


def _canonical_pair(first: tuple, second: tuple) -> tuple[tuple, tuple]:
    return (first, second) if first <= second else (second, first)


def _address_base_key(model_id: str, address: gemmi.AtomAddress) -> tuple[str, str, str, str | None, str, str]:
    return (
        model_id,
        str(address.chain_name),
        str(address.res_id.seqid.num),
        clean_optional_text(address.res_id.seqid.icode),
        str(address.res_id.name),
        str(address.atom_name).strip(),
    )


def _address_specific_key(model_id: str, address: gemmi.AtomAddress) -> tuple[str, str, str, str | None, str, str, str | None]:
    return (*_address_base_key(model_id, address), clean_optional_text(address.altloc))


def collect_explicit_relations(
    structure: gemmi.Structure,
    selected_model_id: str,
    residues: Iterable[ResidueRecord],
    atoms_by_serial: dict[int, list[AtomRecord]],
) -> tuple[
    dict[tuple[tuple, tuple], list[ExplicitRelationEvidence]],
    dict[tuple[tuple, tuple], list[ExplicitRelationEvidence]],
]:
    """Return specific-altLoc and base-identity relation indexes."""

    specific: dict[tuple[tuple, tuple], list[ExplicitRelationEvidence]] = {}
    base: dict[tuple[tuple, tuple], list[ExplicitRelationEvidence]] = {}

    def add(
        first_base: tuple,
        second_base: tuple,
        first_specific: tuple | None,
        second_specific: tuple | None,
        evidence: ExplicitRelationEvidence,
    ) -> None:
        base.setdefault(_canonical_pair(first_base, second_base), []).append(evidence)
        if first_specific is not None and second_specific is not None:
            specific.setdefault(_canonical_pair(first_specific, second_specific), []).append(evidence)

    for connection in structure.connections:
        first_base = _address_base_key(selected_model_id, connection.partner1)
        second_base = _address_base_key(selected_model_id, connection.partner2)
        first_alt = clean_optional_text(connection.partner1.altloc)
        second_alt = clean_optional_text(connection.partner2.altloc)
        first_specific = _address_specific_key(selected_model_id, connection.partner1) if first_alt is not None else None
        second_specific = _address_specific_key(selected_model_id, connection.partner2) if second_alt is not None else None
        source_name = connection.name or connection.link_id or "unnamed"
        evidence = ExplicitRelationEvidence(
            source_type="MMCIF_STRUCT_CONN_OR_PDB_LINK",
            relation_type=_relation_type(connection.type),
            altloc_specific=first_specific is not None and second_specific is not None,
            source_summary=f"{connection.type.name}:{source_name}",
        )
        add(first_base, second_base, first_specific, second_specific, evidence)

    for first_serial, second_serials in structure.conect_map.items():
        for second_serial in second_serials:
            if int(first_serial) >= int(second_serial):
                continue
            for first in atoms_by_serial.get(int(first_serial), []):
                for second in atoms_by_serial.get(int(second_serial), []):
                    if first.model_id != selected_model_id or second.model_id != selected_model_id:
                        continue
                    relation_type = (
                        "METAL_COORDINATION"
                        if first.atom.element.is_metal or second.atom.element.is_metal
                        else "COVALENT"
                    )
                    evidence = ExplicitRelationEvidence(
                        source_type="PDB_CONECT",
                        relation_type=relation_type,
                        altloc_specific=first.altloc_id is not None and second.altloc_id is not None,
                        source_summary=f"CONECT {first_serial} {second_serial}",
                    )
                    add(
                        first.base_atom_key,
                        second.base_atom_key,
                        first.atom_key if first.altloc_id is not None else None,
                        second.atom_key if second.altloc_id is not None else None,
                        evidence,
                    )
    return specific, base


def explicit_evidence_for_pair(
    first: AtomRecord,
    second: AtomRecord,
    specific_index: dict[tuple[tuple, tuple], list[ExplicitRelationEvidence]],
    base_index: dict[tuple[tuple, tuple], list[ExplicitRelationEvidence]],
) -> list[ExplicitRelationEvidence]:
    specific_key = _canonical_pair(first.atom_key, second.atom_key)
    if specific_key in specific_index:
        return specific_index[specific_key]
    return base_index.get(_canonical_pair(first.base_atom_key, second.base_atom_key), [])

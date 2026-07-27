#!/usr/bin/env python3
"""Missing-residue evidence extraction for PDB, mmCIF and AF3 inputs."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gemmi

from classification_common import ClassificationToolError
from structure_records import ResidueRecord, clean_optional_text


@dataclass(frozen=True)
class MissingResidueEvidence:
    source_chain_id: str | None
    residue_name: str
    source_resid_number: str | None
    insertion_code: str | None
    sequence_position: int | None
    evidence_type: str


_CIGAR_TOKEN = re.compile(r"(\d+)([MID])")


def _parse_pdb_remark_465(path: Path, selected_model_id: str) -> list[MissingResidueEvidence]:
    results: list[MissingResidueEvidence] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.startswith("REMARK 465"):
            continue
        residue_name = raw[15:18].strip() if len(raw) >= 18 else ""
        if not residue_name or residue_name in {"RES", "M"}:
            continue
        chain_id = raw[19:20] if len(raw) >= 20 else ""
        sequence_number = raw[21:26].strip() if len(raw) >= 26 else ""
        insertion_code = clean_optional_text(raw[26:27] if len(raw) >= 27 else None)
        model_field = raw[11:14].strip() if len(raw) >= 14 else ""
        if model_field and model_field.isdigit() and model_field != selected_model_id:
            continue
        if not sequence_number:
            fields = raw.split()
            if len(fields) >= 5:
                residue_name = fields[-3]
                chain_id = fields[-2]
                sequence_number = fields[-1]
        if not sequence_number:
            continue
        results.append(
            MissingResidueEvidence(
                source_chain_id=chain_id,
                residue_name=residue_name,
                source_resid_number=sequence_number,
                insertion_code=insertion_code,
                sequence_position=None,
                evidence_type="PDB_REMARK_465",
            )
        )
    return results


def _mmcif_value(row, index: int) -> str | None:
    try:
        return clean_optional_text(row[index])
    except Exception:
        return None


def _parse_mmcif_unobserved(path: Path, selected_model_id: str) -> list[MissingResidueEvidence]:
    try:
        document = gemmi.cif.read_file(str(path))
    except Exception as exc:
        raise ClassificationToolError(f"cannot parse mmCIF missing-residue metadata: {exc}") from exc
    if len(document) == 0:
        return []
    block = document.sole_block() if len(document) == 1 else document[0]
    tags = [
        "_pdbx_unobs_or_zero_occ_residues.PDB_model_num",
        "_pdbx_unobs_or_zero_occ_residues.auth_asym_id",
        "_pdbx_unobs_or_zero_occ_residues.auth_comp_id",
        "_pdbx_unobs_or_zero_occ_residues.auth_seq_id",
        "_pdbx_unobs_or_zero_occ_residues.PDB_ins_code",
        "_pdbx_unobs_or_zero_occ_residues.label_comp_id",
        "_pdbx_unobs_or_zero_occ_residues.label_seq_id",
    ]
    table = block.find(tags)
    results: list[MissingResidueEvidence] = []
    for row in table:
        model_number = _mmcif_value(row, 0)
        if model_number is not None and model_number != selected_model_id:
            continue
        source_chain_id = _mmcif_value(row, 1)
        residue_name = _mmcif_value(row, 2) or _mmcif_value(row, 5)
        source_number = _mmcif_value(row, 3)
        insertion_code = _mmcif_value(row, 4)
        label_seq = _mmcif_value(row, 6)
        if residue_name is None:
            continue
        sequence_position = int(label_seq) if label_seq is not None and label_seq.lstrip("-").isdigit() else None
        results.append(
            MissingResidueEvidence(
                source_chain_id=source_chain_id,
                residue_name=residue_name,
                source_resid_number=source_number,
                insertion_code=insertion_code,
                sequence_position=sequence_position,
                evidence_type="MMCIF_UNOBSERVED_RESIDUES",
            )
        )
    return results


def explicit_missing_residues(
    path: Path,
    source_format: str,
    selected_model_id: str,
) -> list[MissingResidueEvidence]:
    if source_format == "PDB":
        return _parse_pdb_remark_465(path, selected_model_id)
    if source_format == "MMCIF":
        return _parse_mmcif_unobserved(path, selected_model_id)
    return []


def _alignment_missing_positions(
    full_sequence: list[str],
    polymer_span: gemmi.ResidueSpan,
    observed: list[ResidueRecord],
    polymer_type: gemmi.PolymerType,
) -> tuple[list[tuple[int, str]], dict[int, int]]:
    if not full_sequence or not observed or len(polymer_span) == 0:
        return [], {}
    alignment = gemmi.align_sequence_to_polymer(full_sequence, polymer_span, polymer_type)
    cigar = alignment.cigar_str()
    expected_index = 0
    observed_index = 0
    missing: list[tuple[int, str]] = []
    observed_to_sequence_position: dict[int, int] = {}
    consumed = 0
    for count_text, operation in _CIGAR_TOKEN.findall(cigar):
        count = int(count_text)
        consumed += len(count_text) + 1
        for _ in range(count):
            if operation == "M":
                if observed_index < len(observed) and expected_index < len(full_sequence):
                    observed_to_sequence_position[observed_index] = expected_index + 1
                expected_index += 1
                observed_index += 1
            elif operation == "I":
                if expected_index < len(full_sequence):
                    missing.append((expected_index + 1, full_sequence[expected_index]))
                expected_index += 1
            elif operation == "D":
                observed_index += 1
    if consumed != len(cigar):
        raise ClassificationToolError(f"unsupported alignment CIGAR: {cigar}")
    return missing, observed_to_sequence_position


def _entity_for_chain(
    structure: gemmi.Structure,
    model: gemmi.Model,
    chain_residues: list[ResidueRecord],
) -> gemmi.Entity | None:
    for residue in chain_residues:
        if residue.residue.subchain:
            try:
                return structure.get_entity_of(model.get_subchain(residue.residue.subchain))
            except Exception:
                continue
    return None


def sequence_based_missing_residues(
    structure: gemmi.Structure,
    model: gemmi.Model,
    residues: list[ResidueRecord],
    explicit_records: list[MissingResidueEvidence],
) -> tuple[
    list[MissingResidueEvidence],
    list[dict[str, Any]],
    dict[tuple[str, str, str | None, str], int],
    list[dict[str, Any]],
]:
    """Return resolved missing residues, unresolved observations, observed sequence map and chain checks."""

    resolved: list[MissingResidueEvidence] = []
    unresolved: list[dict[str, Any]] = []
    observed_sequence_positions: dict[tuple[str, str, str | None, str], int] = {}
    chain_checks: list[dict[str, Any]] = []
    by_chain: dict[str, list[ResidueRecord]] = {}
    for residue in residues:
        if residue.entity_type == gemmi.EntityType.Polymer:
            by_chain.setdefault(residue.source_chain_id, []).append(residue)

    explicit_by_chain: dict[str | None, list[MissingResidueEvidence]] = {}
    for item in explicit_records:
        explicit_by_chain.setdefault(item.source_chain_id, []).append(item)

    for source_chain_id, chain_residues in by_chain.items():
        chain_residues.sort(key=lambda item: item.residue_position)
        entity = _entity_for_chain(structure, model, chain_residues)
        chain = model.find_chain(source_chain_id)
        polymer_span = chain.get_polymer() if chain is not None else None
        if entity is None or not entity.full_sequence or polymer_span is None or len(polymer_span) == 0:
            chain_checks.append(
                {
                    "source_chain_id": source_chain_id,
                    "status": "NOT_PERFORMED",
                    "evidence_types": [],
                    "missing_residue_count": 0,
                    "reason": "EXPECTED_SEQUENCE_UNAVAILABLE",
                }
            )
            continue
        missing_positions, observed_map = _alignment_missing_positions(
            list(entity.full_sequence),
            polymer_span,
            chain_residues,
            entity.polymer_type,
        )
        for observed_index, sequence_position in observed_map.items():
            residue = chain_residues[observed_index]
            observed_sequence_positions[
                (
                    residue.source_chain_id,
                    residue.source_resid_number,
                    residue.insertion_code,
                    residue.residue_name,
                )
            ] = sequence_position

        explicit_chain = list(explicit_by_chain.get(source_chain_id, []))
        used_explicit: set[int] = set()
        chain_resolved: list[MissingResidueEvidence] = []
        for sequence_position, residue_name in missing_positions:
            candidates = [
                (index, item)
                for index, item in enumerate(explicit_chain)
                if index not in used_explicit
                and item.residue_name == residue_name
                and (item.sequence_position is None or item.sequence_position == sequence_position)
            ]
            if len(candidates) == 1:
                index, item = candidates[0]
                used_explicit.add(index)
                if item.source_resid_number is None:
                    unresolved.append(
                        {
                            "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                            "subject": {
                                "source_chain_id": source_chain_id,
                                "residue_name": residue_name,
                                "sequence_position": sequence_position,
                            },
                            "evidence": [item.evidence_type, "ENTITY_SEQUENCE_ALIGNMENT"],
                            "resolution_status": "PENDING_CONFIRMATION",
                        }
                    )
                else:
                    chain_resolved.append(
                        MissingResidueEvidence(
                            source_chain_id=source_chain_id,
                            residue_name=residue_name,
                            source_resid_number=item.source_resid_number,
                            insertion_code=item.insertion_code,
                            sequence_position=sequence_position,
                            evidence_type=f"{item.evidence_type}+ENTITY_SEQUENCE_ALIGNMENT",
                        )
                    )
            else:
                unresolved.append(
                    {
                        "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                        "subject": {
                            "source_chain_id": source_chain_id,
                            "residue_name": residue_name,
                            "sequence_position": sequence_position,
                        },
                        "evidence": ["ENTITY_SEQUENCE_ALIGNMENT"],
                        "resolution_status": "PENDING_CONFIRMATION",
                    }
                )
        for index, item in enumerate(explicit_chain):
            if index in used_explicit:
                continue
            if item.source_resid_number is None:
                unresolved.append(
                    {
                        "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                        "subject": {
                            "source_chain_id": source_chain_id,
                            "residue_name": item.residue_name,
                            "sequence_position": item.sequence_position,
                        },
                        "evidence": [item.evidence_type],
                        "resolution_status": "PENDING_CONFIRMATION",
                    }
                )
            else:
                chain_resolved.append(item)
        resolved.extend(chain_resolved)
        chain_checks.append(
            {
                "source_chain_id": source_chain_id,
                "status": "MISSING_RESIDUES_FOUND" if missing_positions or explicit_chain else "NO_MISSING_RESIDUES",
                "evidence_types": sorted(
                    {
                        "ENTITY_SEQUENCE_ALIGNMENT",
                        *(item.evidence_type for item in explicit_chain),
                    }
                ),
                "missing_residue_count": len(chain_resolved),
                "reason": None,
            }
        )

    for item in explicit_by_chain.get(None, []):
        unresolved.append(
            {
                "issue_type": "MISSING_RESIDUE_CHAIN_UNRESOLVED",
                "subject": {
                    "source_chain_id": None,
                    "residue_name": item.residue_name,
                    "source_resid": {
                        "number": item.source_resid_number,
                        "insertion_code": item.insertion_code,
                    },
                    "sequence_position": item.sequence_position,
                },
                "evidence": [item.evidence_type],
                "resolution_status": "PENDING_CONFIRMATION",
            }
        )
    return resolved, unresolved, observed_sequence_positions, chain_checks


def parse_af3_sequence_references(sequence_references: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Read AF3 JSON or FASTA references into exact chain-ID sequences.

    FASTA headers use the first whitespace-delimited token as the exact source
    chain ID. Ambiguous or duplicate IDs are rejected as sequence-reference
    conflicts by the caller.
    """

    sequences: dict[str, list[str]] = {}
    for reference in sequence_references:
        reference_type = reference.get("type") or reference.get("reference_type")
        path = Path(reference["path"]).resolve()
        if reference_type == "AF3_INPUT_JSON":
            data = json.loads(path.read_text(encoding="utf-8"))
            for entry in data.get("sequences", []):
                if not isinstance(entry, dict) or len(entry) != 1:
                    continue
                _kind, payload = next(iter(entry.items()))
                identifiers = payload.get("id")
                sequence = payload.get("sequence")
                if isinstance(identifiers, str):
                    identifiers = [identifiers]
                if not isinstance(identifiers, list) or not isinstance(sequence, str):
                    continue
                monomers = list(sequence.strip())
                for identifier in identifiers:
                    identifier = str(identifier)
                    if identifier in sequences and sequences[identifier] != monomers:
                        raise ClassificationToolError(f"conflicting AF3 sequences for chain {identifier}")
                    sequences[identifier] = monomers
        elif reference_type == "FASTA":
            current_id: str | None = None
            chunks: list[str] = []
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if current_id is not None:
                        sequence = list("".join(chunks))
                        if current_id in sequences and sequences[current_id] != sequence:
                            raise ClassificationToolError(f"conflicting FASTA sequences for chain {current_id}")
                        sequences[current_id] = sequence
                    current_id = line[1:].split()[0]
                    chunks = []
                else:
                    chunks.append(line)
            if current_id is not None:
                sequence = list("".join(chunks))
                if current_id in sequences and sequences[current_id] != sequence:
                    raise ClassificationToolError(f"conflicting FASTA sequences for chain {current_id}")
                sequences[current_id] = sequence
    return sequences

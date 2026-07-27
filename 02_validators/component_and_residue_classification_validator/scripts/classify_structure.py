#!/usr/bin/env python3
"""Classify residues and record structure observations for one selected model."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import gemmi

from ccd_reference import CCDTemplate, resolve_ccd_component
from classification_common import (
    ClassificationError,
    atomic_yaml,
    atom_altloc,
    clean_optional_string,
    entity_metadata,
    is_hydrogen_symbol,
    load_yaml,
    model_id,
    normalize_element_symbol,
    read_structure,
    require_hash,
    select_model,
    sha256,
    source_format,
    source_resid_from_residue,
    source_resid_key,
    validate_document,
)
from rtp_reference import (
    RTPTemplate,
    choose_terminal_template_name,
    filter_templates_by_file,
    load_rtp_directory,
)

VERSION = "1.0.0"
POLYMER_CLASSES = {"POLYMER", "BRANCHED", "NONPOLYMER", "WATER"}
TOPOLOGY_CLASSES = {
    "STANDARD_RESIDUE",
    "COVALENTLY_LINKED_NONSTANDARD",
    "INDEPENDENT_NONSTANDARD",
    "SOLVENT_COMPONENT",
    "ION_COMPONENT",
}
ALLOWED_COMBINATIONS = {
    "POLYMER": {"STANDARD_RESIDUE", "COVALENTLY_LINKED_NONSTANDARD"},
    "BRANCHED": {"STANDARD_RESIDUE", "COVALENTLY_LINKED_NONSTANDARD", "INDEPENDENT_NONSTANDARD"},
    "NONPOLYMER": {
        "COVALENTLY_LINKED_NONSTANDARD",
        "INDEPENDENT_NONSTANDARD",
        "SOLVENT_COMPONENT",
        "ION_COMPONENT",
    },
    "WATER": {"SOLVENT_COMPONENT"},
}


# ---------------------------- definitions and configuration ----------------------------

def _load_residue_definitions(path: Path | None, label: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if path is None:
        return {}, {"path": None, "sha256": None, "status": "NOT_PROVIDED"}
    document = load_yaml(path)
    if not isinstance(document, dict) or not isinstance(document.get("residue_definitions"), list):
        raise ClassificationError(f"{label} must contain residue_definitions list: {path}")
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(document["residue_definitions"], start=1):
        if not isinstance(item, dict):
            raise ClassificationError(f"{label} definition {index} is not a mapping")
        name = item.get("residue_name")
        polymer_class = item.get("polymer_class")
        topology_class = item.get("topology_class")
        if not isinstance(name, str) or not name:
            raise ClassificationError(f"{label} definition {index} has invalid residue_name")
        if name in result:
            raise ClassificationError(f"DUPLICATE_{label.upper().replace(' ', '_')}_RESIDUE_DEFINITION: {name}")
        if polymer_class not in POLYMER_CLASSES or topology_class not in TOPOLOGY_CLASSES:
            raise ClassificationError(f"{label} definition {name} has invalid classification")
        if topology_class not in ALLOWED_COMBINATIONS[polymer_class]:
            raise ClassificationError(
                f"{label} definition {name} has incompatible classes: {polymer_class}/{topology_class}"
            )
        ccd_id = item.get("ccd_id", name)
        if not isinstance(ccd_id, str) or not ccd_id:
            raise ClassificationError(f"{label} definition {name} has invalid ccd_id")
        result[name] = {
            "residue_name": name,
            "polymer_class": polymer_class,
            "topology_class": topology_class,
            "ccd_id": ccd_id,
        }
    return result, {"path": str(path), "sha256": sha256(path), "status": "LOADED"}


def _load_skill_registries(paths: list[Path]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    merged: dict[str, dict[str, Any]] = {}
    manifest: list[dict[str, Any]] = []
    for path in paths:
        definitions, entry = _load_residue_definitions(path, "skill registry")
        for name, definition in definitions.items():
            if name in merged:
                raise ClassificationError(f"duplicate exact residue name across Skill registries: {name}")
            merged[name] = definition
        manifest.append(entry)
    return merged, manifest


def _same_classification(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("polymer_class") == right.get("polymer_class")
        and left.get("topology_class") == right.get("topology_class")
    )


def _context_classification(residue: dict[str, Any]) -> dict[str, Any] | None:
    if residue["is_water"]:
        return {"polymer_class": "WATER", "topology_class": "SOLVENT_COMPONENT", "ccd_id": residue["residue_name"]}
    if residue["is_monoatomic_ion"]:
        return {"polymer_class": "NONPOLYMER", "topology_class": "ION_COMPONENT", "ccd_id": residue["residue_name"]}
    entity_type = residue["entity_type"]
    if entity_type == "POLYMER":
        return {
            "polymer_class": "POLYMER",
            "topology_class": "COVALENTLY_LINKED_NONSTANDARD",
            "ccd_id": residue["residue_name"],
        }
    if entity_type == "BRANCHED":
        return {
            "polymer_class": "BRANCHED",
            "topology_class": "INDEPENDENT_NONSTANDARD",
            "ccd_id": residue["residue_name"],
        }
    if entity_type == "NONPOLYMER" or residue["het_flag"] == "H":
        return {
            "polymer_class": "NONPOLYMER",
            "topology_class": "INDEPENDENT_NONSTANDARD",
            "ccd_id": residue["residue_name"],
        }
    return None


# ---------------------------- structure collection ----------------------------

def _collect_residues(structure: gemmi.Structure, model: gemmi.Model) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    residues: list[dict[str, Any]] = []
    chains: list[dict[str, Any]] = []
    source_order = 0
    for chain_order, chain in enumerate(model, start=1):
        chain_residues: list[dict[str, Any]] = []
        for residue in chain:
            source_order += 1
            entity_id, entity_type, polymer_type = entity_metadata(structure, model, residue)
            atoms: list[dict[str, Any]] = []
            for atom in residue:
                atoms.append(
                    {
                        "atom_name": atom.name.strip(),
                        "element": normalize_element_symbol(atom.element.name),
                        "altloc": atom_altloc(atom),
                        "occupancy": float(atom.occ),
                        "atom": atom,
                    }
                )
            heavy_atoms = [atom for atom in atoms if not is_hydrogen_symbol(atom["element"])]
            is_water = bool(residue.is_water()) or entity_type == "WATER"
            is_monoatomic_ion = (
                entity_type != "POLYMER"
                and len(heavy_atoms) == 1
                and heavy_atoms[0]["element"] is not None
                and heavy_atoms[0]["element"] not in {"C", "N", "O", "P", "S", "Se"}
            )
            item = {
                "source_order": source_order,
                "chain_order": chain_order,
                "source_chain_id": chain.name,
                "source_resid": source_resid_from_residue(residue),
                "residue_name": residue.name,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "polymer_type": polymer_type,
                "het_flag": residue.het_flag,
                "atoms": atoms,
                "residue": residue,
                "is_water": is_water,
                "is_monoatomic_ion": is_monoatomic_ion,
            }
            residues.append(item)
            chain_residues.append(item)
        chains.append(
            {
                "chain_order": chain_order,
                "source_chain_id": chain.name,
                "residues": chain_residues,
            }
        )
    if not residues:
        raise ClassificationError(f"selected model {model_id(model)} contains no residues")
    return residues, chains


def _assign_terminal_roles(chains: list[dict[str, Any]]) -> None:
    """Assign terminal roles after residue classification.

    PDB files often lack usable entity/polymer metadata.  In that case the exact
    residue classification and conservative backbone atom patterns provide the
    chain context needed to select an explicitly configured terminal RTP block.
    """
    for chain in chains:
        polymer = [
            res
            for res in chain["residues"]
            if (res.get("classification") or {}).get("polymer_class") == "POLYMER"
        ]
        if not polymer:
            continue
        first = polymer[0]
        last = polymer[-1]
        declared_types = {
            res.get("polymer_type")
            for res in polymer
            if res.get("polymer_type") not in {None, "UNKNOWN"}
        }
        atom_names = {atom["atom_name"] for res in polymer for atom in res["atoms"]}
        if any(str(ptype).startswith("POLYPEPTIDE") for ptype in declared_types) or {"N", "CA", "C"}.issubset(atom_names):
            inferred = next((ptype for ptype in declared_types if str(ptype).startswith("POLYPEPTIDE")), "POLYPEPTIDE_L")
            for residue in polymer:
                if residue.get("polymer_type") in {None, "UNKNOWN"}:
                    residue["terminal_mapping_polymer_type"] = inferred
            first.setdefault("terminal_roles", []).append("N_TERMINUS")
            last.setdefault("terminal_roles", []).append("C_TERMINUS")
        elif declared_types & {"DNA", "RNA", "DNA_RNA_HYBRID", "PNA"} or ({"P"} & atom_names and ({"O5'", "C5'"} & atom_names)):
            inferred = next((ptype for ptype in declared_types if ptype in {"DNA", "RNA", "DNA_RNA_HYBRID", "PNA"}), "OTHER_NUCLEIC_ACID")
            for residue in polymer:
                if residue.get("polymer_type") in {None, "UNKNOWN"}:
                    residue["terminal_mapping_polymer_type"] = inferred
            first.setdefault("terminal_roles", []).append("FIVE_PRIME")
            last.setdefault("terminal_roles", []).append("THREE_PRIME")


# ---------------------------- PDB/mmCIF/AF3 missing residues ----------------------------

def _parse_pdb_remark_465(path: Path, selected_model_id: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.startswith("REMARK 465"):
            continue
        padded = raw.ljust(80)
        residue_name = padded[15:18].strip()
        chain_id = padded[19:20]
        number_text = padded[21:26].strip()
        insertion = clean_optional_string(padded[26:27])
        model_text = padded[11:14].strip()
        if not residue_name or not re.fullmatch(r"-?\d+", number_text):
            # Some generators use less rigid spacing; accept only a fully explicit fallback.
            match = re.match(r"^REMARK 465\s+(?:(\d+)\s+)?([A-Za-z0-9]{1,3})\s+(\S?)\s+(-?\d+)([A-Za-z]?)\s*$", raw)
            if not match:
                continue
            model_text, residue_name, chain_id, number_text, insertion_raw = match.groups()
            insertion = clean_optional_string(insertion_raw)
        if model_text and model_text != selected_model_id:
            continue
        results.append(
            {
                "source_chain_id": chain_id,
                "source_resid": {"number": number_text, "insertion_code": insertion},
                "residue_name": residue_name,
                "sequence_position": None,
                "evidence_type": "PDB_REMARK_465",
            }
        )
    return results


def _parse_pdb_seqres(path: Path) -> dict[str, list[str]]:
    seqres: dict[str, list[str]] = defaultdict(list)
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.startswith("SEQRES"):
            continue
        padded = raw.ljust(80)
        chain_id = padded[11:12]
        seqres[chain_id].extend(padded[19:70].split())
    return dict(seqres)


def _lcs_missing(expected: list[str], observed: list[str]) -> tuple[list[int], bool]:
    """Return unmatched expected indices and whether the optimum alignment is ambiguous."""
    n, m = len(expected), len(observed)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    ways = [[1] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            candidates: list[tuple[int, str]] = [(dp[i + 1][j], "skip_expected"), (dp[i][j + 1], "skip_observed")]
            if expected[i] == observed[j]:
                candidates.append((1 + dp[i + 1][j + 1], "match"))
            best = max(score for score, _ in candidates)
            dp[i][j] = best
            ways[i][j] = min(2, sum(ways[i + 1][j + 1] if action == "match" else ways[i + 1][j] if action == "skip_expected" else ways[i][j + 1] for score, action in candidates if score == best))
    missing: list[int] = []
    i = j = 0
    while i < n and j < m:
        if expected[i] == observed[j] and dp[i][j] == 1 + dp[i + 1][j + 1]:
            i += 1
            j += 1
        elif dp[i][j] == dp[i + 1][j]:
            missing.append(i)
            i += 1
        else:
            j += 1
    missing.extend(range(i, n))
    return missing, ways[0][0] > 1


def _cif_category(block: gemmi.cif.Block, prefix: str) -> list[dict[str, str]]:
    table = block.find_mmcif_category(prefix)
    if len(table) == 0:
        return []
    tags = [str(tag) for tag in table.tags]
    return [dict(zip(tags, list(row))) for row in table]


def _parse_mmcif_missing(path: Path, selected_model_id: str, observed: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    document = gemmi.cif.read_file(str(path))
    block = document.sole_block()
    missing: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    # Prefer explicit unobserved-residue records.
    rows = _cif_category(block, "_pdbx_unobs_or_zero_occ_residues.")
    for row in rows:
        model_value = clean_optional_string(row.get("_pdbx_unobs_or_zero_occ_residues.PDB_model_num"))
        if model_value and model_value != selected_model_id:
            continue
        residue_name = clean_optional_string(
            row.get("_pdbx_unobs_or_zero_occ_residues.auth_comp_id")
            or row.get("_pdbx_unobs_or_zero_occ_residues.comp_id")
        )
        chain_id = clean_optional_string(row.get("_pdbx_unobs_or_zero_occ_residues.auth_asym_id"))
        number = clean_optional_string(row.get("_pdbx_unobs_or_zero_occ_residues.auth_seq_id"))
        insertion = clean_optional_string(row.get("_pdbx_unobs_or_zero_occ_residues.PDB_ins_code"))
        sequence_position = clean_optional_string(row.get("_pdbx_unobs_or_zero_occ_residues.label_seq_id"))
        if residue_name is None:
            continue
        if number is None:
            unresolved.append(
                {
                    "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                    "source_chain_id": chain_id,
                    "residue_name": residue_name,
                    "sequence_position": int(sequence_position) if sequence_position and sequence_position.isdigit() else sequence_position,
                    "evidence_type": "MMCIF_UNOBSERVED_RESIDUE",
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            continue
        missing.append(
            {
                "source_chain_id": chain_id,
                "source_resid": {"number": number, "insertion_code": insertion},
                "residue_name": residue_name,
                "sequence_position": int(sequence_position) if sequence_position and sequence_position.isdigit() else sequence_position,
                "evidence_type": "MMCIF_UNOBSERVED_RESIDUE",
            }
        )

    # pdbx_poly_seq_scheme can identify expected author numbering, including absent coordinates.
    scheme = _cif_category(block, "_pdbx_poly_seq_scheme.")
    observed_keys = {
        (res["source_chain_id"], *source_resid_key(res["source_resid"]), res["residue_name"])
        for res in observed
        if res["entity_type"] == "POLYMER"
    }
    known_missing_keys = {
        (item["source_chain_id"], *source_resid_key(item["source_resid"]), item["residue_name"])
        for item in missing
    }
    for row in scheme:
        chain_id = clean_optional_string(row.get("_pdbx_poly_seq_scheme.auth_asym_id"))
        residue_name = clean_optional_string(
            row.get("_pdbx_poly_seq_scheme.auth_mon_id") or row.get("_pdbx_poly_seq_scheme.mon_id")
        )
        number = clean_optional_string(row.get("_pdbx_poly_seq_scheme.auth_seq_num"))
        insertion = clean_optional_string(row.get("_pdbx_poly_seq_scheme.pdb_ins_code"))
        sequence_position = clean_optional_string(row.get("_pdbx_poly_seq_scheme.seq_id"))
        if residue_name is None:
            continue
        key = (chain_id, number, insertion, residue_name)
        if key in observed_keys or key in known_missing_keys:
            continue
        if number is None:
            unresolved.append(
                {
                    "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                    "source_chain_id": chain_id,
                    "residue_name": residue_name,
                    "sequence_position": int(sequence_position) if sequence_position and sequence_position.isdigit() else sequence_position,
                    "evidence_type": "MMCIF_POLY_SEQ_SCHEME",
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
        else:
            missing.append(
                {
                    "source_chain_id": chain_id,
                    "source_resid": {"number": number, "insertion_code": insertion},
                    "residue_name": residue_name,
                    "sequence_position": int(sequence_position) if sequence_position and sequence_position.isdigit() else sequence_position,
                    "evidence_type": "MMCIF_POLY_SEQ_SCHEME",
                }
            )
    return missing, unresolved


_PROTEIN_1_TO_3 = {
    "A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS", "Q": "GLN", "E": "GLU", "G": "GLY",
    "H": "HIS", "I": "ILE", "L": "LEU", "K": "LYS", "M": "MET", "F": "PHE", "P": "PRO", "S": "SER",
    "T": "THR", "W": "TRP", "Y": "TYR", "V": "VAL", "X": "UNK",
}


def _parse_sequence_references(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sequences: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for entry in entries:
        path = Path(entry["path"])
        actual_hash = require_hash(path, entry.get("sha256"), "sequence reference")
        kind = entry["type"]
        manifest.append({"type": kind, "path": str(path), "sha256": actual_hash, "status": "LOADED"})
        if kind == "FASTA":
            header: str | None = None
            sequence_parts: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith(">"):
                    if header is not None:
                        sequences.append({"id": header, "kind": "PROTEIN", "sequence": "".join(sequence_parts)})
                    header = line[1:].strip()
                    sequence_parts = []
                else:
                    sequence_parts.append(line.strip())
            if header is not None:
                sequences.append({"id": header, "kind": "PROTEIN", "sequence": "".join(sequence_parts)})
        elif kind == "AF3_INPUT_JSON":
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data.get("sequences", []):
                for key, seq_kind in (("protein", "PROTEIN"), ("dna", "DNA"), ("rna", "RNA")):
                    if key not in item:
                        continue
                    spec = item[key]
                    identifiers = spec.get("id")
                    if not isinstance(identifiers, list):
                        identifiers = [identifiers]
                    for identifier in identifiers:
                        sequences.append({"id": str(identifier), "kind": seq_kind, "sequence": str(spec["sequence"])})
        else:
            raise ClassificationError(f"unsupported sequence reference type: {kind}")
    return sequences, manifest


def _af3_missing(
    sequences: list[dict[str, Any]],
    chains: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    missing: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    polymer_chains = [chain for chain in chains if any(r["entity_type"] == "POLYMER" for r in chain["residues"])]
    if not sequences:
        for chain in polymer_chains:
            checks.append(
                {
                    "chain_index": None,
                    "source_chain_id": chain["source_chain_id"],
                    "status": "NOT_PERFORMED",
                    "reason": "AF3_INPUT_SEQUENCE_NOT_PROVIDED",
                    "evidence_types": [],
                    "missing_residue_count": 0,
                    "unresolved_count": 0,
                }
            )
        return missing, unresolved, checks

    assignments: list[tuple[dict[str, Any], dict[str, Any]]] = []
    unused = list(sequences)
    for chain in polymer_chains:
        exact = [seq for seq in unused if seq["id"] == chain["source_chain_id"]]
        if len(exact) == 1:
            assignments.append((chain, exact[0]))
            unused.remove(exact[0])
    remaining_chains = [chain for chain in polymer_chains if all(chain is not assigned[0] for assigned in assignments)]
    if len(remaining_chains) == len(unused):
        assignments.extend(zip(remaining_chains, unused))
    else:
        unresolved.append(
            {
                "issue_type": "AF3_SEQUENCE_CHAIN_MAPPING_CONFLICT",
                "source_chain_ids": [chain["source_chain_id"] for chain in remaining_chains],
                "sequence_ids": [seq["id"] for seq in unused],
                "resolution_status": "PENDING_CONFIRMATION",
            }
        )
        return missing, unresolved, checks

    for chain, sequence in assignments:
        if sequence["kind"] == "PROTEIN":
            expected = [_PROTEIN_1_TO_3.get(char.upper(), "UNK") for char in sequence["sequence"]]
        elif sequence["kind"] == "DNA":
            expected = [f"D{char.upper()}" for char in sequence["sequence"]]
        else:
            expected = [char.upper() for char in sequence["sequence"]]
        observed = [r["residue_name"] for r in chain["residues"] if r["entity_type"] == "POLYMER"]
        missing_indices, ambiguous = _lcs_missing(expected, observed)
        for index in missing_indices:
            unresolved.append(
                {
                    "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                    "source_chain_id": chain["source_chain_id"],
                    "residue_name": expected[index],
                    "sequence_position": index + 1,
                    "evidence_type": "AF3_INPUT_SEQUENCE",
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
        checks.append(
            {
                "chain_index": None,
                "source_chain_id": chain["source_chain_id"],
                "status": "MISSING_RESIDUES_UNRESOLVED" if missing_indices else "NO_MISSING_RESIDUES",
                "reason": "SEQUENCE_ALIGNMENT_AMBIGUOUS" if ambiguous else None,
                "evidence_types": ["AF3_INPUT_SEQUENCE"],
                "missing_residue_count": 0,
                "unresolved_count": len(missing_indices),
            }
        )
    return missing, unresolved, checks


# ---------------------------- classification and heavy atoms ----------------------------

def _classify_one(
    residue: dict[str, Any],
    *,
    mode: str,
    project: dict[str, dict[str, Any]],
    skill: dict[str, dict[str, Any]],
    rtp_templates: dict[str, list[RTPTemplate]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    name = residue["residue_name"]
    project_def = project.get(name)
    skill_def = skill.get(name)
    issues: list[dict[str, Any]] = []

    # Water/monoatomic ion identity comes from structure facts and is not overridden by RTP filename or aliases.
    if residue["is_water"]:
        structural = {"residue_name": name, "polymer_class": "WATER", "topology_class": "SOLVENT_COMPONENT", "ccd_id": name}
    elif residue["is_monoatomic_ion"]:
        structural = {"residue_name": name, "polymer_class": "NONPOLYMER", "topology_class": "ION_COMPONENT", "ccd_id": name}
    else:
        structural = None

    if mode == "REGISTRY":
        if project_def and skill_def and not _same_classification(project_def, skill_def):
            issues.append(
                {
                    "issue_type": "PROJECT_SKILL_CLASSIFICATION_CONFLICT",
                    "residue_name": name,
                    "project_definition": project_def,
                    "skill_definition": skill_def,
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            return {
                "polymer_class": None,
                "topology_class": None,
                "resolution_status": "CONFLICT",
                "primary_source": None,
                "ccd_id": project_def.get("ccd_id") or skill_def.get("ccd_id") or name,
                "evidence": ["project and Skill definitions conflict"],
            }, issues
        chosen = project_def or skill_def or structural or _context_classification(residue)
        source = "PROJECT_DEFINITION" if project_def else "SKILL_REGISTRY" if skill_def else "STRUCTURE_CONTEXT"
        if chosen is None:
            return {
                "polymer_class": None,
                "topology_class": None,
                "resolution_status": "UNRESOLVED",
                "primary_source": None,
                "ccd_id": name,
                "evidence": ["no exact definition or reliable entity context"],
            }, issues
        return {
            "polymer_class": chosen["polymer_class"],
            "topology_class": chosen["topology_class"],
            "resolution_status": "RESOLVED",
            "primary_source": source,
            "ccd_id": chosen.get("ccd_id", name),
            "evidence": [source],
        }, issues

    if mode != "FORCE_FIELD_ANALYSIS":
        raise ClassificationError(f"unsupported classification mode: {mode}")

    rtp_matches = rtp_templates.get(name, [])
    force_field_def: dict[str, Any] | None = None
    if structural is not None:
        force_field_def = structural
    elif rtp_matches:
        if residue["entity_type"] == "POLYMER":
            force_field_def = {"polymer_class": "POLYMER", "topology_class": "STANDARD_RESIDUE", "ccd_id": name}
        elif residue["entity_type"] == "BRANCHED":
            force_field_def = {"polymer_class": "BRANCHED", "topology_class": "STANDARD_RESIDUE", "ccd_id": name}
        else:
            force_field_def = {"polymer_class": "NONPOLYMER", "topology_class": "INDEPENDENT_NONSTANDARD", "ccd_id": name}
    if project_def and force_field_def and not _same_classification(project_def, force_field_def):
        issues.append(
            {
                "issue_type": "PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT",
                "residue_name": name,
                "project_definition": project_def,
                "force_field_determination": force_field_def,
                "rtp_files": sorted({str(template.path) for template in rtp_matches}),
                "resolution_status": "PENDING_CONFIRMATION",
            }
        )
        return {
            "polymer_class": None,
            "topology_class": None,
            "resolution_status": "CONFLICT",
            "primary_source": None,
            "ccd_id": project_def.get("ccd_id", name),
            "evidence": ["project definition conflicts with force-field determination"],
            "force_field_recognized": bool(rtp_matches),
        }, issues
    chosen = project_def or force_field_def
    source = "PROJECT_DEFINITION" if project_def else "FORCE_FIELD_RTP" if force_field_def else None
    if chosen is None:
        chosen = skill_def
        source = "SKILL_REGISTRY" if skill_def else None
    if chosen is None:
        chosen = _context_classification(residue)
        source = "STRUCTURE_CONTEXT" if chosen else None
    if chosen is None:
        return {
            "polymer_class": None,
            "topology_class": None,
            "resolution_status": "UNRESOLVED",
            "primary_source": None,
            "ccd_id": name,
            "evidence": ["project, force field and Skill registry did not resolve residue"],
            "force_field_recognized": False,
        }, issues
    return {
        "polymer_class": chosen["polymer_class"],
        "topology_class": chosen["topology_class"],
        "resolution_status": "RESOLVED",
        "primary_source": source,
        "ccd_id": chosen.get("ccd_id", name),
        "evidence": [source],
        "force_field_recognized": bool(rtp_matches),
        "matching_rtp_files": sorted({str(template.path) for template in rtp_matches}),
    }, issues


def _heavy_atom_check_ccd(residue: dict[str, Any], template: CCDTemplate | None, failure_reason: str | None = None) -> dict[str, Any]:
    if template is None:
        return {
            "status": "REFERENCE_TEMPLATE_UNAVAILABLE",
            "reference_type": "CCD",
            "reference_name": residue["classification"]["ccd_id"],
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": failure_reason or "CCD_TEMPLATE_UNAVAILABLE",
        }
    actual = {atom["atom_name"] for atom in residue["atoms"] if not is_hydrogen_symbol(atom["element"])}
    expected = set(template.heavy_atom_names)
    direct_missing = expected - actual
    unexpected = actual - expected
    mappings = []
    for actual_name in sorted(list(unexpected)):
        mapped = template.alternate_names.get(actual_name)
        if mapped in direct_missing:
            mappings.append(
                {
                    "structure_atom_name": actual_name,
                    "reference_atom_name": mapped,
                    "mapping_source": "CCD_ALTERNATE_ATOM_NAME",
                }
            )
    if mappings:
        return {
            "status": "ATOM_NAME_MAPPING_REQUIRED",
            "reference_type": "CCD",
            "reference_name": template.component_id,
            "reference_path": str(template.source_path),
            "reference_sha256": template.source_sha256,
            "missing_atoms": sorted(direct_missing),
            "unexpected_atoms": sorted(unexpected),
            "candidate_mappings": mappings,
        }
    if direct_missing and unexpected:
        status = "MISSING_AND_UNEXPECTED_HEAVY_ATOMS"
    elif direct_missing:
        status = "MISSING_EXPECTED_HEAVY_ATOMS"
    elif unexpected:
        status = "UNEXPECTED_HEAVY_ATOMS"
    else:
        status = "HEAVY_ATOMS_COMPLETE"
    return {
        "status": status,
        "reference_type": "CCD",
        "reference_name": template.component_id,
        "reference_path": str(template.source_path),
        "reference_sha256": template.source_sha256,
        "missing_atoms": sorted(direct_missing),
        "unexpected_atoms": sorted(unexpected),
    }


def _select_rtp_for_heavy_atoms(
    residue: dict[str, Any],
    *,
    templates: dict[str, list[RTPTemplate]],
    force_field_root: Path,
    terminal_mappings: list[dict[str, Any]],
    water_names: set[str],
) -> tuple[RTPTemplate | None, list[dict[str, Any]], str | None]:
    name = residue["residue_name"]
    roles = residue.get("terminal_roles", [])
    target_name = name
    constrained_file: str | None = None
    if roles:
        mapped_name, constrained_file = choose_terminal_template_name(
            source_residue_name=name,
            polymer_type=residue.get("terminal_mapping_polymer_type") or residue.get("polymer_type"),
            terminal_roles=roles,
            mappings=terminal_mappings,
        )
        if mapped_name:
            target_name = mapped_name
        elif name not in templates:
            return None, [], "TERMINAL_RTP_TEMPLATE_NOT_FOUND"
    candidates = filter_templates_by_file(templates.get(target_name, []), force_field_root, constrained_file)
    if not candidates:
        return None, [], "RTP_TEMPLATE_NOT_FOUND"
    if len(candidates) > 1 and target_name not in water_names:
        issue = {
            "issue_type": "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE",
            "structure_residue_name": name,
            "rtp_residue_name": target_name,
            "terminal_roles": roles,
            "templates": [template.as_reference() for template in candidates],
            "resolution_status": "PENDING_CONFIRMATION",
        }
        return None, [issue], "DUPLICATE_RTP_TEMPLATE_REQUIRES_CONFIRMATION"
    return candidates[0], [], None


def _heavy_atom_check_rtp(residue: dict[str, Any], template: RTPTemplate | None, reason: str | None) -> dict[str, Any]:
    if template is None:
        return {
            "status": "REFERENCE_TEMPLATE_UNAVAILABLE",
            "reference_type": "FORCE_FIELD_RTP",
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": reason or "RTP_TEMPLATE_UNAVAILABLE",
        }
    actual = {atom["atom_name"] for atom in residue["atoms"] if not is_hydrogen_symbol(atom["element"])}
    expected = set(template.heavy_atom_names)
    missing = expected - actual
    unexpected = actual - expected
    if missing and unexpected:
        status = "MISSING_AND_UNEXPECTED_HEAVY_ATOMS"
    elif missing:
        status = "MISSING_EXPECTED_HEAVY_ATOMS"
    elif unexpected:
        status = "UNEXPECTED_HEAVY_ATOMS"
    else:
        status = "HEAVY_ATOMS_COMPLETE"
    return {
        "status": status,
        "reference_type": "FORCE_FIELD_RTP",
        "reference_name": template.residue_name,
        "reference_path": str(template.path),
        "reference_sha256": sha256(template.path),
        "missing_atoms": sorted(missing),
        "unexpected_atoms": sorted(unexpected),
    }


# ---------------------------- chain groups and records ----------------------------

def _chain_index_for_source(
    source_chain_id: str | None,
    polymer_groups: list[dict[str, Any]],
) -> tuple[int | None, list[int]]:
    matches = [group["chain_index"] for group in polymer_groups if group.get("source_chain_id") == source_chain_id]
    return (matches[0] if len(matches) == 1 else None, matches)


def _build_chain_groups(residues: list[dict[str, Any]], chains: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[int, int]]:
    groups: list[dict[str, Any]] = []
    chain_to_group: dict[int, int] = {}
    next_index = 1
    for chain in chains:
        polymer = [
            r for r in chain["residues"]
            if (r.get("classification") or {}).get("polymer_class") == "POLYMER"
        ]
        branched = [
            r for r in chain["residues"]
            if (r.get("classification") or {}).get("polymer_class") == "BRANCHED"
        ]
        selected = polymer or branched
        if not selected:
            continue
        group_type = "POLYMER_CHAIN" if polymer else "BRANCHED_CHAIN"
        group = {
            "chain_index": next_index,
            "group_type": group_type,
            "grouping_status": "BASELINE",
            "source_chain_id": chain["source_chain_id"],
            "entity_ids": sorted({r["entity_id"] for r in selected if r["entity_id"] is not None}),
            "polymer_types": sorted({r["polymer_type"] for r in selected if r["polymer_type"] is not None}),
            "instance_count": len(selected),
            "first_source_order": min(r["source_order"] for r in selected),
        }
        groups.append(group)
        chain_to_group[chain["chain_order"]] = next_index
        for residue in selected:
            residue["baseline_chain_index"] = next_index
        next_index += 1

    nonpolymer = [r for r in residues if "baseline_chain_index" not in r]
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for residue in nonpolymer:
        classification = residue["classification"]
        pc = classification.get("polymer_class")
        tc = classification.get("topology_class")
        if pc == "WATER":
            group_type = "SOLVENT_GROUP"
        elif tc == "ION_COMPONENT":
            group_type = "ION_GROUP"
        else:
            group_type = "REPEATED_SMALL_MOLECULE_GROUP" if sum(1 for r in nonpolymer if r["residue_name"] == residue["residue_name"] and r["classification"].get("topology_class") == tc) > 1 else "PROVISIONAL_COMPONENT_GROUP"
        anomaly = (
            residue["conformation"]["status"] == "MULTIPLE_CONFORMATIONS"
            or classification["resolution_status"] != "RESOLVED"
            or residue["heavy_atom_check"]["status"] not in {"HEAVY_ATOMS_COMPLETE", "NOT_PERFORMED"}
        )
        key = (group_type, residue["residue_name"], pc, tc, anomaly, residue["source_order"] if anomaly else None)
        grouped[key].append(residue)

    polymer_groups = [group for group in groups if group["group_type"] in {"POLYMER_CHAIN", "BRANCHED_CHAIN"}]
    for key, members in sorted(grouped.items(), key=lambda item: min(r["source_order"] for r in item[1])):
        group_type, residue_name, pc, tc, anomaly, _ = key
        source_assoc_counter: Counter[int] = Counter()
        for member in members:
            _, candidates = _chain_index_for_source(member["source_chain_id"], polymer_groups)
            if len(candidates) == 1:
                source_assoc_counter[candidates[0]] += 1
        group = {
            "chain_index": next_index,
            "group_type": group_type,
            "grouping_status": "BASELINE",
            "residue_name": residue_name,
            "polymer_class": pc,
            "topology_class": tc,
            "instance_count": len(members),
            "first_source_order": min(r["source_order"] for r in members),
            "source_associations": [
                {"polymer_chain_index": index, "instance_count": count}
                for index, count in sorted(source_assoc_counter.items())
            ],
        }
        groups.append(group)
        for member in members:
            member["baseline_chain_index"] = next_index
            member["aggregated"] = len(members) > 1 and not anomaly
        next_index += 1
    return groups, chain_to_group


def _residue_record(residue: dict[str, Any], *, presence_status: str = "OBSERVED") -> dict[str, Any]:
    return {
        "chain_index": residue.get("baseline_chain_index"),
        "source_chain_id": residue.get("source_chain_id"),
        "source_resid": residue["source_resid"],
        "residue_name": residue["residue_name"],
        "presence_status": presence_status,
        "source_order": residue.get("source_order"),
        "entity_id": residue.get("entity_id"),
        "classification_observation": residue["classification"],
        "conformation_observation": residue["conformation"],
        "heavy_atom_check": residue["heavy_atom_check"],
    }


# ---------------------------- main classification ----------------------------

def classify(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    structure_config = config.get("structure") or {}
    structure_path = Path(structure_config["path"])
    structure_hash = require_hash(structure_path, structure_config.get("sha256"), "structure")
    structure = read_structure(structure_path)
    fmt = source_format(structure_path, structure, structure_config.get("source_format"))
    selected_model_id = str(structure_config["selected_model_id"])
    model = select_model(structure, selected_model_id)

    mode = (config.get("classification") or {}).get("mode")
    if mode not in {"REGISTRY", "FORCE_FIELD_ANALYSIS"}:
        raise ClassificationError("classification.mode must be REGISTRY or FORCE_FIELD_ANALYSIS")

    project_path_value = (config.get("project_residue_definitions") or {}).get("path")
    project_path = Path(project_path_value) if project_path_value else None
    if project_path is not None:
        require_hash(project_path, (config.get("project_residue_definitions") or {}).get("sha256"), "project residue definitions")
    project_defs, project_manifest = _load_residue_definitions(project_path, "project")

    registry_paths = [Path(value) for value in config.get("skill_registry_paths", [])]
    if not registry_paths:
        script_root = Path(__file__).resolve().parents[1]
        registry_paths = [
            script_root / "references/standard_residue_registry.yaml",
            script_root / "references/covalently_linked_nonstandard_residue_registry.yaml",
        ]
    skill_defs, skill_manifest = _load_skill_registries(registry_paths)

    rtp_templates: dict[str, list[RTPTemplate]] = {}
    force_field_manifest: dict[str, Any] | None = None
    force_field_root: Path | None = None
    terminal_mappings: list[dict[str, Any]] = []
    if mode == "FORCE_FIELD_ANALYSIS":
        force_field_config = config.get("force_field") or {}
        if not force_field_config.get("root_path"):
            raise ClassificationError("FORCE_FIELD_ANALYSIS requires force_field.root_path")
        force_field_root = Path(force_field_config["root_path"])
        rtp_templates, rtp_files = load_rtp_directory(force_field_root)
        terminal_mappings = force_field_config.get("terminal_template_mappings", [])
        if not isinstance(terminal_mappings, list):
            raise ClassificationError("force_field.terminal_template_mappings must be a list")
        force_field_manifest = {
            "root_path": str(force_field_root),
            "files": rtp_files,
            "terminal_template_mapping_count": len(terminal_mappings),
        }

    sequence_entries = config.get("sequence_references", [])
    sequences, sequence_manifest = _parse_sequence_references(sequence_entries)

    residues, chains = _collect_residues(structure, model)

    unresolved: list[dict[str, Any]] = []
    water_names = {name for name, definition in {**skill_defs, **project_defs}.items() if definition["polymer_class"] == "WATER"}
    for residue in residues:
        classification, issues = _classify_one(
            residue,
            mode=mode,
            project=project_defs,
            skill=skill_defs,
            rtp_templates=rtp_templates,
        )
        residue["classification"] = classification
        unresolved.extend(issues)
        altlocs = sorted({atom["altloc"] for atom in residue["atoms"] if atom["altloc"] is not None})
        residue["conformation"] = (
            {"status": "MULTIPLE_CONFORMATIONS", "altloc_ids": altlocs}
            if altlocs
            else {"status": "SINGLE_CONFORMATION", "altloc_ids": []}
        )

    _assign_terminal_roles(chains)

    # Resolve CCD references once per unique component.
    ccd_config = config.get("ccd") or {}
    snapshot_dir = Path(ccd_config.get("project_snapshot_dir") or (Path(config.get("output_root", ".")) / "reference_data/ccd"))
    local_dirs = [Path(value) for value in ccd_config.get("local_reference_dirs", [])]
    shared_cache = Path(ccd_config["shared_cache_path"]) if ccd_config.get("shared_cache_path") else None
    retrieval_policy = ccd_config.get("retrieval_policy", "CACHE_ONLY")
    remote_url = ccd_config.get("remote_url_template", "https://files.rcsb.org/ligands/download/{component_id}.cif")

    ccd_needed: dict[str, list[str]] = defaultdict(list)
    for residue in residues:
        cls = residue["classification"]
        if cls["resolution_status"] != "RESOLVED" or cls["polymer_class"] == "WATER" or cls["topology_class"] == "ION_COMPONENT":
            continue
        use_ccd = mode == "REGISTRY" or cls["topology_class"] != "STANDARD_RESIDUE"
        if use_ccd:
            ccd_needed[cls["ccd_id"]].append(residue["residue_name"])
    ccd_templates: dict[str, CCDTemplate | None] = {}
    ccd_manifest: list[dict[str, Any]] = []
    ccd_failures: dict[str, str] = {}
    for component_id, mapped_names in sorted(ccd_needed.items()):
        template, manifest_entry, issues = resolve_ccd_component(
            component_id=component_id,
            mapped_residue_names=mapped_names,
            project_snapshot_dir=snapshot_dir,
            local_reference_dirs=local_dirs,
            shared_cache_path=shared_cache,
            retrieval_policy=retrieval_policy,
            remote_url_template=remote_url,
        )
        ccd_templates[component_id] = template
        ccd_manifest.append(manifest_entry)
        unresolved.extend(issues)
        if template is None:
            ccd_failures[component_id] = manifest_entry["retrieval"].get("status") or "CCD_TEMPLATE_UNAVAILABLE"

    # Heavy atom checks.
    for residue in residues:
        cls = residue["classification"]
        if residue["conformation"]["status"] == "MULTIPLE_CONFORMATIONS":
            residue["heavy_atom_check"] = {
                "status": "NOT_PERFORMED",
                "reference_type": None,
                "reference_name": None,
                "missing_atoms": [],
                "unexpected_atoms": [],
                "reason": "MULTIPLE_CONFORMATIONS_PRESENT",
            }
            continue
        if cls["resolution_status"] != "RESOLVED":
            residue["heavy_atom_check"] = {
                "status": "NOT_PERFORMED",
                "reference_type": None,
                "reference_name": None,
                "missing_atoms": [],
                "unexpected_atoms": [],
                "reason": "CLASSIFICATION_UNRESOLVED",
            }
            continue
        if cls["polymer_class"] == "WATER" or cls["topology_class"] == "ION_COMPONENT":
            residue["heavy_atom_check"] = {
                "status": "NOT_PERFORMED",
                "reference_type": None,
                "reference_name": None,
                "missing_atoms": [],
                "unexpected_atoms": [],
                "reason": "WATER_OR_ION_NOT_CHECKED",
            }
            continue
        if mode == "FORCE_FIELD_ANALYSIS" and cls["topology_class"] == "STANDARD_RESIDUE":
            assert force_field_root is not None
            template, issues, reason = _select_rtp_for_heavy_atoms(
                residue,
                templates=rtp_templates,
                force_field_root=force_field_root,
                terminal_mappings=terminal_mappings,
                water_names=water_names,
            )
            unresolved.extend(issues)
            residue["heavy_atom_check"] = _heavy_atom_check_rtp(residue, template, reason)
        else:
            ccd_id = cls["ccd_id"]
            residue["heavy_atom_check"] = _heavy_atom_check_ccd(
                residue,
                ccd_templates.get(ccd_id),
                ccd_failures.get(ccd_id),
            )

    chain_groups, chain_to_group = _build_chain_groups(residues, chains)
    polymer_groups = [group for group in chain_groups if group["group_type"] in {"POLYMER_CHAIN", "BRANCHED_CHAIN"}]

    # Missing residues.
    missing_items: list[dict[str, Any]] = []
    missing_checks: list[dict[str, Any]] = []
    if fmt == "PDB":
        missing_items.extend(_parse_pdb_remark_465(structure_path, selected_model_id))
        seqres = _parse_pdb_seqres(structure_path)
        explicit_keys = {(item["source_chain_id"], item["residue_name"], item["source_resid"]["number"], item["source_resid"]["insertion_code"]) for item in missing_items}
        for chain in chains:
            expected = seqres.get(chain["source_chain_id"], [])
            if not expected:
                continue
            observed_names = [
                res["residue_name"] for res in chain["residues"]
                if (res.get("classification") or {}).get("polymer_class") == "POLYMER"
            ]
            missing_indices, ambiguous = _lcs_missing(expected, observed_names)
            unresolved_count = 0
            for index in missing_indices:
                # REMARK 465 entries already provide authoritative author numbering; unmatched SEQRES residues do not.
                if any(key[0] == chain["source_chain_id"] and key[1] == expected[index] for key in explicit_keys):
                    continue
                unresolved.append(
                    {
                        "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                        "source_chain_id": chain["source_chain_id"],
                        "residue_name": expected[index],
                        "sequence_position": index + 1,
                        "evidence_type": "PDB_SEQRES_ALIGNMENT",
                        "mapping_ambiguous": ambiguous,
                        "resolution_status": "PENDING_CONFIRMATION",
                    }
                )
                unresolved_count += 1
            chain_index = chain_to_group.get(chain["chain_order"])
            missing_checks.append(
                {
                    "chain_index": chain_index,
                    "source_chain_id": chain["source_chain_id"],
                    "status": "MISSING_RESIDUES_FOUND" if any(item["source_chain_id"] == chain["source_chain_id"] for item in missing_items) else "MISSING_RESIDUES_UNRESOLVED" if unresolved_count else "NO_MISSING_RESIDUES",
                    "reason": "SEQUENCE_ALIGNMENT_AMBIGUOUS" if ambiguous and unresolved_count else None,
                    "evidence_types": ["PDB_REMARK_465", "PDB_SEQRES", "PDB_ATOM"],
                    "missing_residue_count": sum(1 for item in missing_items if item["source_chain_id"] == chain["source_chain_id"]),
                    "unresolved_count": unresolved_count,
                }
            )
    elif fmt == "MMCIF":
        mm_missing, mm_unresolved = _parse_mmcif_missing(structure_path, selected_model_id, residues)
        missing_items.extend(mm_missing)
        unresolved.extend(mm_unresolved)
    else:
        af_missing, af_unresolved, af_checks = _af3_missing(sequences, chains)
        missing_items.extend(af_missing)
        unresolved.extend(af_unresolved)
        missing_checks.extend(af_checks)

    # Convert explicit missing residues to records. Missing residues require source_resid and resolvable chain.
    missing_records: list[dict[str, Any]] = []
    for item in missing_items:
        chain_index, candidates = _chain_index_for_source(item["source_chain_id"], polymer_groups)
        if chain_index is None:
            unresolved.append(
                {
                    "issue_type": "MISSING_RESIDUE_CHAIN_UNRESOLVED",
                    "source_chain_id": item["source_chain_id"],
                    "candidate_chain_indices": candidates,
                    "source_resid": item["source_resid"],
                    "residue_name": item["residue_name"],
                    "sequence_position": item.get("sequence_position"),
                    "evidence_type": item["evidence_type"],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            continue
        pseudo = {
            "baseline_chain_index": chain_index,
            "source_chain_id": item["source_chain_id"],
            "source_resid": item["source_resid"],
            "residue_name": item["residue_name"],
            "source_order": None,
            "entity_id": next((group["entity_ids"][0] for group in polymer_groups if group["chain_index"] == chain_index and group["entity_ids"]), None),
            "classification": {
                "polymer_class": "POLYMER",
                "topology_class": "STANDARD_RESIDUE" if item["residue_name"] in skill_defs else "COVALENTLY_LINKED_NONSTANDARD",
                "resolution_status": "RESOLVED",
                "primary_source": "EXPECTED_SEQUENCE",
                "ccd_id": (project_defs.get(item["residue_name"]) or skill_defs.get(item["residue_name"]) or {}).get("ccd_id", item["residue_name"]),
                "evidence": [item["evidence_type"]],
            },
            "conformation": {"status": "NOT_APPLICABLE", "altloc_ids": []},
            "heavy_atom_check": {
                "status": "NOT_APPLICABLE",
                "reference_type": None,
                "reference_name": None,
                "missing_atoms": [],
                "unexpected_atoms": [],
                "reason": "RESIDUE_COORDINATES_ABSENT",
            },
        }
        record = _residue_record(pseudo, presence_status="MISSING_EXPECTED")
        record["sequence_position"] = item.get("sequence_position")
        missing_records.append(record)

    if fmt == "MMCIF":
        chains_with_polymer = [
            chain for chain in chains
            if any((r.get("classification") or {}).get("polymer_class") == "POLYMER" for r in chain["residues"])
        ]
        for chain in chains_with_polymer:
            chain_index = chain_to_group.get(chain["chain_order"])
            count = sum(1 for record in missing_records if record["chain_index"] == chain_index)
            unresolved_count = sum(1 for item in unresolved if item.get("source_chain_id") == chain["source_chain_id"] and item["issue_type"].startswith("MISSING_RESIDUE"))
            missing_checks.append(
                {
                    "chain_index": chain_index,
                    "source_chain_id": chain["source_chain_id"],
                    "status": "MISSING_RESIDUES_FOUND" if count else "MISSING_RESIDUES_UNRESOLVED" if unresolved_count else "NO_MISSING_RESIDUES",
                    "reason": None,
                    "evidence_types": ["MMCIF_POLY_SEQ_SCHEME", "MMCIF_UNOBSERVED_RESIDUE", "MMCIF_ATOM_SITE"],
                    "missing_residue_count": count,
                    "unresolved_count": unresolved_count,
                }
            )

    # Update AF3 chain indices after baseline groups exist.
    for check in missing_checks:
        if check["chain_index"] is None:
            resolved_index, _ = _chain_index_for_source(check["source_chain_id"], polymer_groups)
            check["chain_index"] = resolved_index

    # Only write ordinary instance records when not represented by a pure bulk group.
    residue_records: list[dict[str, Any]] = []
    for residue in residues:
        if residue.get("aggregated"):
            continue
        residue_records.append(_residue_record(residue))
    residue_records.extend(missing_records)

    entities_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for residue in residues:
        key = (residue["entity_id"], residue["entity_type"], residue["polymer_type"])
        entry = entities_by_key.setdefault(
            key,
            {
                "entity_id": residue["entity_id"],
                "entity_type": residue["entity_type"],
                "polymer_type": residue["polymer_type"],
                "source_chain_ids": [],
            },
        )
        if residue["source_chain_id"] not in entry["source_chain_ids"]:
            entry["source_chain_ids"].append(residue["source_chain_id"])

    classification_counts = Counter(
        residue["classification"].get("topology_class") or "UNRESOLVED" for residue in residues
    )
    heavy_counts = Counter(residue["heavy_atom_check"]["status"] for residue in residues)
    conformation_counts = Counter(residue["conformation"]["status"] for residue in residues)

    observations = {
        "schema_version": "1.0",
        "tool": {"name": "classify_structure", "version": VERSION},
        "run_context": {
            "input_structure_path": str(structure_path),
            "input_structure_sha256": structure_hash,
            "source_format": fmt,
            "selected_model_id": selected_model_id,
            "classification_mode": mode,
        },
        "entities": list(entities_by_key.values()),
        "chain_groups": sorted(chain_groups, key=lambda group: group["chain_index"]),
        "residue_records": residue_records,
        "missing_residue_checks": missing_checks,
        "unresolved_observations": unresolved,
        "summary": {
            "entity_count": len(entities_by_key),
            "chain_group_count": len(chain_groups),
            "observed_residue_count": len(residues),
            "recorded_residue_count": len(residue_records),
            "missing_residue_count": len(missing_records),
            "unresolved_observation_count": len(unresolved),
            "classification_counts": dict(sorted(classification_counts.items())),
            "conformation_counts": dict(sorted(conformation_counts.items())),
            "heavy_atom_check_counts": dict(sorted(heavy_counts.items())),
        },
    }

    relation_files: dict[str, Any] = {}
    for key, value in (config.get("relation_definition_files") or {}).items():
        if value is None:
            relation_files[key] = {"path": None, "sha256": None, "status": "NOT_PROVIDED"}
        else:
            path = Path(value["path"] if isinstance(value, dict) else value)
            expected = value.get("sha256") if isinstance(value, dict) else None
            relation_files[key] = {"path": str(path), "sha256": require_hash(path, expected, key), "status": "LOADED"}

    manifest = {
        "schema_version": "1.0",
        "tool": {"name": "classify_structure", "version": VERSION},
        "classification_mode": mode,
        "project_files": {"residue_definitions": project_manifest},
        "skill_references": skill_manifest,
        "force_field": force_field_manifest,
        "ccd_components": ccd_manifest,
        "sequence_references": sequence_manifest,
        "relation_definition_files": relation_files,
    }
    return observations, manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--observations-schema", type=Path, required=True)
    parser.add_argument("--manifest-schema", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_yaml(args.config)
        if not isinstance(config, dict):
            raise ClassificationError("classification config must be a mapping")
        observations, manifest = classify(config)
        validate_document(observations, args.observations_schema)
        validate_document(manifest, args.manifest_schema)
        atomic_yaml(args.observations, observations)
        atomic_yaml(args.manifest, manifest)
    except (ClassificationError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

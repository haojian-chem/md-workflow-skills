#!/usr/bin/env python3
"""Baseline classification engine for the component/residue classification v1.2 pipeline."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import gemmi

from ccd_reference import CcdTemplate, acquire_ccd_template, compare_ccd_heavy_atoms
from classification_common import (
    ClassificationToolError,
    parse_structure,
    read_yaml_strict,
    require_sha256,
    sha256_file,
    validate_document,
    validate_unique_residue_definitions,
    verify_source_format,
)
from rtp_reference import RtpTemplate, compare_heavy_atom_names, load_rtp_index
from sequence_missing import (
    MissingResidueEvidence,
    explicit_missing_residues,
    parse_af3_sequence_references,
    sequence_based_missing_residues,
)
from structure_records import ResidueRecord, collect_selected_model


@dataclass(frozen=True)
class ClassificationValue:
    polymer_class: str | None
    topology_class: str | None
    resolution_status: str
    primary_source: str | None
    evidence: tuple[str, ...]
    ccd_id: str | None
    rtp_template_name: str | None = None


@dataclass
class ResidueAnalysis:
    residue: ResidueRecord
    classification: ClassificationValue
    conformation: dict[str, Any]
    heavy_atom_check: dict[str, Any]
    sequence_position: int | None
    chain_index: int | None = None
    include_residue_record: bool = True


PROTEIN_POLYMER_TYPES = {
    gemmi.PolymerType.PeptideL,
    gemmi.PolymerType.PeptideD,
    gemmi.PolymerType.CyclicPseudoPeptide,
}
NUCLEIC_POLYMER_TYPES = {
    gemmi.PolymerType.Dna,
    gemmi.PolymerType.Rna,
    gemmi.PolymerType.DnaRnaHybrid,
    gemmi.PolymerType.Pna,
}

ONE_TO_THREE_PROTEIN = {
    "A": "ALA",
    "R": "ARG",
    "N": "ASN",
    "D": "ASP",
    "C": "CYS",
    "Q": "GLN",
    "E": "GLU",
    "G": "GLY",
    "H": "HIS",
    "I": "ILE",
    "L": "LEU",
    "K": "LYS",
    "M": "MET",
    "F": "PHE",
    "P": "PRO",
    "S": "SER",
    "T": "THR",
    "W": "TRP",
    "Y": "TYR",
    "V": "VAL",
    "U": "SEC",
    "O": "PYL",
    "X": "UNK",
}


def _required_mapping(document: dict[str, Any], key: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise ClassificationToolError(f"config field {key!r} must be a mapping")
    return value


def _required_path(mapping: dict[str, Any], key: str) -> Path:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ClassificationToolError(f"config field {key!r} must be a non-empty path string")
    return Path(value).resolve()


def _optional_path(mapping: dict[str, Any], key: str) -> Path | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ClassificationToolError(f"config field {key!r} must be null or a non-empty path string")
    return Path(value).resolve()


def _entity_polymer_class(residue: ResidueRecord) -> str | None:
    if residue.residue.is_water() or residue.entity_type == gemmi.EntityType.Water:
        return "WATER"
    if residue.entity_type == gemmi.EntityType.Polymer:
        return "POLYMER"
    if residue.entity_type == gemmi.EntityType.Branched:
        return "BRANCHED"
    if residue.entity_type == gemmi.EntityType.NonPolymer:
        return "NONPOLYMER"
    if residue.polymer_type != gemmi.PolymerType.Unknown:
        return "POLYMER"
    return None


def _entity_fallback(residue: ResidueRecord) -> ClassificationValue:
    polymer_class = _entity_polymer_class(residue)
    if polymer_class == "WATER":
        return ClassificationValue(
            "WATER",
            "SOLVENT_COMPONENT",
            "RESOLVED",
            "ENTITY_CONTEXT",
            ("structure water/entity context",),
            None,
        )
    if polymer_class == "POLYMER":
        return ClassificationValue(
            "POLYMER",
            "TOPOLOGY_LINKED_NONSTANDARD",
            "RESOLVED",
            "ENTITY_CONTEXT",
            ("polymer entity membership without an exact standard definition",),
            residue.residue_name,
        )
    if polymer_class == "BRANCHED":
        return ClassificationValue(
            "BRANCHED",
            "INDEPENDENT_NONSTANDARD",
            "RESOLVED",
            "ENTITY_CONTEXT",
            ("branched entity membership",),
            residue.residue_name,
        )
    if polymer_class == "NONPOLYMER" or residue.residue.het_flag == "H":
        return ClassificationValue(
            "NONPOLYMER",
            "INDEPENDENT_NONSTANDARD",
            "RESOLVED",
            "ENTITY_CONTEXT",
            ("nonpolymer/HET residue context",),
            residue.residue_name,
        )
    return ClassificationValue(
        None,
        None,
        "UNRESOLVED",
        None,
        ("insufficient project, force-field, registry and entity evidence",),
        residue.residue_name,
    )


def _load_definition_file(
    path: Path,
    schema: Path,
    *,
    expected_status: str | None = None,
) -> tuple[dict[str, dict[str, Any]], str]:
    document = read_yaml_strict(path)
    validate_document(document, schema)
    validate_unique_residue_definitions(document)
    if expected_status is not None and document.get("status") not in {None, expected_status, "draft"}:
        raise ClassificationToolError(f"unexpected status in residue definition file {path}")
    return {entry["residue_name"]: entry for entry in document["residue_definitions"]}, sha256_file(path)


def _definition_value(entry: dict[str, Any], source: str) -> ClassificationValue:
    return ClassificationValue(
        polymer_class=entry["polymer_class"],
        topology_class=entry["topology_class"],
        resolution_status="RESOLVED",
        primary_source=source,
        evidence=(f"exact residue definition from {source}",),
        ccd_id=entry.get("ccd_id", entry["residue_name"]),
    )


def _same_labels(first: ClassificationValue, second: ClassificationValue) -> bool:
    return (
        first.polymer_class == second.polymer_class
        and first.topology_class == second.topology_class
    )


def _conflict_value(
    first: ClassificationValue,
    second: ClassificationValue,
    issue_type: str,
    residue: ResidueRecord,
    unresolved: list[dict[str, Any]],
) -> ClassificationValue:
    unresolved.append(
        {
            "issue_type": issue_type,
            "subject": {
                "source_chain_id": residue.source_chain_id,
                "source_resid": {
                    "number": residue.source_resid_number,
                    "insertion_code": residue.insertion_code,
                },
                "residue_name": residue.residue_name,
                "first_classification": {
                    "polymer_class": first.polymer_class,
                    "topology_class": first.topology_class,
                    "source": first.primary_source,
                },
                "second_classification": {
                    "polymer_class": second.polymer_class,
                    "topology_class": second.topology_class,
                    "source": second.primary_source,
                },
            },
            "evidence": [*first.evidence, *second.evidence],
            "resolution_status": "PENDING_CONFIRMATION",
        }
    )
    return ClassificationValue(
        None,
        None,
        "CONFLICT",
        None,
        (*first.evidence, *second.evidence),
        first.ccd_id or second.ccd_id,
    )


def _force_field_value(
    residue: ResidueRecord,
    template_name: str,
) -> ClassificationValue:
    polymer_class = _entity_polymer_class(residue)
    if polymer_class == "POLYMER":
        topology_class = "STANDARD_RESIDUE"
    elif polymer_class == "BRANCHED":
        topology_class = "STANDARD_RESIDUE"
    elif polymer_class == "WATER":
        topology_class = "SOLVENT_COMPONENT"
    else:
        polymer_class = "NONPOLYMER"
        topology_class = "INDEPENDENT_NONSTANDARD"
    return ClassificationValue(
        polymer_class,
        topology_class,
        "RESOLVED",
        "FORCE_FIELD",
        (f"exact RTP template match: {template_name}",),
        residue.residue_name,
        rtp_template_name=template_name,
    )


def _terminal_roles_by_residue(residues: list[ResidueRecord]) -> dict[tuple, set[str]]:
    by_chain: dict[str, list[ResidueRecord]] = defaultdict(list)
    for residue in residues:
        if residue.entity_type == gemmi.EntityType.Polymer:
            by_chain[residue.source_chain_id].append(residue)
    roles: dict[tuple, set[str]] = defaultdict(set)
    for chain_residues in by_chain.values():
        chain_residues.sort(key=lambda item: item.residue_position)
        if not chain_residues:
            continue
        polymer_type = chain_residues[0].polymer_type
        if polymer_type in PROTEIN_POLYMER_TYPES:
            roles[chain_residues[0].residue_key].add("N_TERMINUS")
            roles[chain_residues[-1].residue_key].add("C_TERMINUS")
        elif polymer_type in NUCLEIC_POLYMER_TYPES:
            roles[chain_residues[0].residue_key].add("FIVE_PRIME")
            roles[chain_residues[-1].residue_key].add("THREE_PRIME")
    return roles


def _terminal_mapping_index(force_field_config: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    index: dict[tuple[str, str], list[str]] = defaultdict(list)
    for entry in force_field_config.get("terminal_template_mappings", []) or []:
        if not isinstance(entry, dict):
            raise ClassificationToolError("terminal_template_mappings entries must be mappings")
        source_name = entry.get("source_residue_name")
        role = entry.get("terminal_role")
        target = entry.get("rtp_residue_name")
        if not all(isinstance(value, str) and value for value in (source_name, role, target)):
            raise ClassificationToolError("invalid terminal template mapping entry")
        index[(source_name, role)].append(target)
    return index


def _rtp_candidates_for_residue(
    residue: ResidueRecord,
    rtp_index: dict[str, list[RtpTemplate]],
    roles: dict[tuple, set[str]],
    terminal_mappings: dict[tuple[str, str], list[str]],
    unresolved: list[dict[str, Any]],
) -> tuple[str | None, list[RtpTemplate]]:
    terminal_roles = sorted(roles.get(residue.residue_key, set()))
    known_terminal_names = {
        target
        for targets in terminal_mappings.values()
        for target in targets
    }
    if terminal_roles:
        mapped_targets: list[str] = []
        for role in terminal_roles:
            mapped_targets.extend(
                terminal_mappings.get((residue.residue_name, role), [])
            )
        mapped_targets = sorted(set(mapped_targets))
        if len(mapped_targets) > 1:
            unresolved.append(
                {
                    "issue_type": "TERMINAL_RTP_TEMPLATE_AMBIGUOUS",
                    "subject": {
                        "source_chain_id": residue.source_chain_id,
                        "source_resid": {
                            "number": residue.source_resid_number,
                            "insertion_code": residue.insertion_code,
                        },
                        "residue_name": residue.residue_name,
                        "terminal_roles": terminal_roles,
                        "candidate_rtp_names": mapped_targets,
                    },
                    "evidence": [
                        "multiple explicit terminal template mappings"
                    ],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            return None, []
        if len(mapped_targets) == 1:
            target = mapped_targets[0]
            return target, rtp_index.get(target, [])
        if residue.residue_name in known_terminal_names:
            return residue.residue_name, rtp_index.get(
                residue.residue_name, []
            )
        return None, []

    exact = rtp_index.get(residue.residue_name, [])
    if exact:
        return residue.residue_name, exact
    return None, []


def _classify_residue(
    residue: ResidueRecord,
    mode: str,
    project_defs: dict[str, dict[str, Any]],
    skill_defs: dict[str, dict[str, Any]],
    rtp_index: dict[str, list[RtpTemplate]],
    roles: dict[tuple, set[str]],
    terminal_mappings: dict[tuple[str, str], list[str]],
    unresolved: list[dict[str, Any]],
) -> tuple[ClassificationValue, RtpTemplate | None]:
    project_entry = project_defs.get(residue.residue_name)
    skill_entry = skill_defs.get(residue.residue_name)
    project_value = _definition_value(project_entry, "PROJECT_DEFINITION") if project_entry else None
    skill_value = _definition_value(skill_entry, "SKILL_REGISTRY") if skill_entry else None

    if mode == "REGISTRY":
        if project_value is not None and skill_value is not None:
            if _same_labels(project_value, skill_value):
                return ClassificationValue(
                    project_value.polymer_class,
                    project_value.topology_class,
                    "RESOLVED",
                    "PROJECT_DEFINITION",
                    (*project_value.evidence, "Skill registry labels are consistent"),
                    project_value.ccd_id,
                ), None
            return _conflict_value(
                project_value,
                skill_value,
                "PROJECT_REGISTRY_CLASSIFICATION_CONFLICT",
                residue,
                unresolved,
            ), None
        if project_value is not None:
            return project_value, None
        if skill_value is not None:
            return skill_value, None
        return _entity_fallback(residue), None

    if mode != "FORCE_FIELD_ANALYSIS":
        raise ClassificationToolError(f"unsupported classification mode: {mode}")

    rtp_name, candidates = _rtp_candidates_for_residue(
        residue,
        rtp_index,
        roles,
        terminal_mappings,
        unresolved,
    )
    selected_template: RtpTemplate | None = None
    force_value: ClassificationValue | None = None
    if candidates:
        water_context = residue.residue.is_water() or _entity_polymer_class(residue) == "WATER"
        if len(candidates) > 1 and not water_context:
            unresolved.append(
                {
                    "issue_type": "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE",
                    "subject": {
                        "source_chain_id": residue.source_chain_id,
                        "source_resid": {
                            "number": residue.source_resid_number,
                            "insertion_code": residue.insertion_code,
                        },
                        "residue_name": residue.residue_name,
                        "rtp_residue_name": rtp_name,
                        "template_files": [str(item.file_path) for item in candidates],
                    },
                    "evidence": ["same exact RTP residue name is defined more than once"],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
        else:
            selected_template = candidates[0]
            force_value = _force_field_value(residue, rtp_name or residue.residue_name)

    if project_value is not None and force_value is not None:
        if _same_labels(project_value, force_value):
            return ClassificationValue(
                project_value.polymer_class,
                project_value.topology_class,
                "RESOLVED",
                "PROJECT_DEFINITION",
                (*project_value.evidence, *force_value.evidence, "project and force-field classification are consistent"),
                project_value.ccd_id,
                force_value.rtp_template_name,
            ), selected_template
        return _conflict_value(
            project_value,
            force_value,
            "PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT",
            residue,
            unresolved,
        ), None
    if project_value is not None:
        return project_value, None
    if force_value is not None:
        return force_value, selected_template
    if skill_value is not None:
        return skill_value, None
    return _entity_fallback(residue), None


def _empty_heavy_check(status: str, reason: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "reference_type": None,
        "reference_name": None,
        "missing_atoms": [],
        "unexpected_atoms": [],
        "reason": reason,
    }


def _heavy_status(missing: list[str], unexpected: list[str]) -> str:
    if missing and unexpected:
        return "MISSING_AND_UNEXPECTED_HEAVY_ATOMS"
    if missing:
        return "MISSING_EXPECTED_HEAVY_ATOMS"
    if unexpected:
        return "UNEXPECTED_HEAVY_ATOMS"
    return "HEAVY_ATOMS_COMPLETE"


def _observed_heavy_names(residue: ResidueRecord) -> list[str]:
    return sorted(
        {
            atom.atom_name
            for atom in residue.atoms
            if atom.element is None or atom.element not in {"H", "D"}
        }
    )


def _entity_name(entity_type: gemmi.EntityType) -> str:
    mapping = {
        gemmi.EntityType.Polymer: "POLYMER",
        gemmi.EntityType.NonPolymer: "NONPOLYMER",
        gemmi.EntityType.Branched: "BRANCHED",
        gemmi.EntityType.Water: "WATER",
    }
    return mapping.get(entity_type, "UNKNOWN")


def _polymer_type_name(polymer_type: gemmi.PolymerType) -> str | None:
    return None if polymer_type == gemmi.PolymerType.Unknown else polymer_type.name


def _classification_dict(value: ClassificationValue) -> dict[str, Any]:
    return {
        "polymer_class": value.polymer_class,
        "topology_class": value.topology_class,
        "resolution_status": value.resolution_status,
        "primary_source": value.primary_source,
        "evidence": list(value.evidence),
    }


def _conformation_dict(residue: ResidueRecord) -> dict[str, Any]:
    altloc_ids = residue.altloc_ids
    return {
        "status": "MULTIPLE_CONFORMATIONS" if len(altloc_ids) > 1 else "SINGLE_CONFORMATION",
        "altloc_ids": altloc_ids,
    }


def _source_associations(
    residues: Iterable[ResidueAnalysis],
    polymer_source_chain_to_index: dict[str, int],
) -> list[dict[str, int]]:
    counts: Counter[int] = Counter()
    for analysis in residues:
        index = polymer_source_chain_to_index.get(analysis.residue.source_chain_id)
        if index is not None:
            counts[index] += 1
    return [
        {"polymer_chain_index": index, "instance_count": count}
        for index, count in sorted(counts.items())
    ]


def _build_chain_groups(
    analyses: list[ResidueAnalysis],
) -> tuple[list[dict[str, Any]], dict[tuple, int]]:
    groups: list[dict[str, Any]] = []
    assignment: dict[tuple, int] = {}
    next_index = 1
    polymer_source_chain_to_index: dict[str, int] = {}

    by_chain: dict[tuple[str, str | None, str], list[ResidueAnalysis]] = defaultdict(list)
    for analysis in analyses:
        classification = analysis.classification
        if classification.polymer_class in {"POLYMER", "BRANCHED"}:
            key = (
                analysis.residue.source_chain_id,
                analysis.residue.entity_id,
                classification.polymer_class,
            )
            by_chain[key].append(analysis)
    chain_order = sorted(
        by_chain.items(),
        key=lambda item: min(value.residue.chain_position for value in item[1]),
    )
    for (source_chain_id, entity_id, polymer_class), members in chain_order:
        index = next_index
        next_index += 1
        group_type = "POLYMER_CHAIN" if polymer_class == "POLYMER" else "BRANCHED_CHAIN"
        groups.append(
            {
                "chain_index": index,
                "grouping_status": "BASELINE",
                "group_type": group_type,
                "source_chain_id": source_chain_id,
                "entity_id": entity_id,
                "instance_count": len(members),
                "source_associations": [],
            }
        )
        if polymer_class == "POLYMER":
            polymer_source_chain_to_index[source_chain_id] = index
        for analysis in members:
            assignment[analysis.residue.residue_key] = index
            analysis.chain_index = index
            analysis.include_residue_record = True

    nonpolymer = [
        analysis
        for analysis in analyses
        if analysis.residue.residue_key not in assignment
    ]
    by_exact_name: dict[str, list[ResidueAnalysis]] = defaultdict(list)
    for analysis in nonpolymer:
        by_exact_name[analysis.residue.residue_name].append(analysis)

    name_order = sorted(
        by_exact_name.items(),
        key=lambda item: min(value.residue.residue_position + value.residue.chain_position * 10**7 for value in item[1]),
    )
    for residue_name, members in name_order:
        normal = [
            item
            for item in members
            if item.classification.resolution_status == "RESOLVED"
            and item.conformation["status"] == "SINGLE_CONFORMATION"
            and item.heavy_atom_check["status"]
            not in {
                "MISSING_EXPECTED_HEAVY_ATOMS",
                "UNEXPECTED_HEAVY_ATOMS",
                "MISSING_AND_UNEXPECTED_HEAVY_ATOMS",
                "ATOM_NAME_MAPPING_REQUIRED",
            }
        ]
        exceptional = [item for item in members if item not in normal]
        classification = normal[0].classification if normal else None
        if normal:
            if classification is not None and classification.topology_class == "SOLVENT_COMPONENT":
                group_type = "SOLVENT_GROUP"
                aggregate = True
            elif classification is not None and classification.topology_class == "ION_COMPONENT":
                group_type = "ION_GROUP"
                aggregate = True
            elif len(normal) > 1 and classification is not None and classification.topology_class == "INDEPENDENT_NONSTANDARD":
                group_type = "REPEATED_SMALL_MOLECULE_GROUP"
                aggregate = True
            else:
                group_type = "INDEPENDENT_COMPONENT"
                aggregate = False

            if aggregate:
                index = next_index
                next_index += 1
                groups.append(
                    {
                        "chain_index": index,
                        "grouping_status": "BASELINE",
                        "group_type": group_type,
                        "source_chain_id": None,
                        "entity_id": normal[0].residue.entity_id if len({item.residue.entity_id for item in normal}) == 1 else None,
                        "residue_name": residue_name,
                        "instance_count": len(normal),
                        "source_associations": _source_associations(normal, polymer_source_chain_to_index),
                    }
                )
                for item in normal:
                    assignment[item.residue.residue_key] = index
                    item.chain_index = index
                    item.include_residue_record = False
            else:
                exceptional.extend(normal)

        for item in sorted(
            exceptional,
            key=lambda value: (value.residue.chain_position, value.residue.residue_position),
        ):
            index = next_index
            next_index += 1
            groups.append(
                {
                    "chain_index": index,
                    "grouping_status": "BASELINE",
                    "group_type": "INDEPENDENT_COMPONENT",
                    "source_chain_id": item.residue.source_chain_id,
                    "entity_id": item.residue.entity_id,
                    "residue_name": item.residue.residue_name,
                    "instance_count": 1,
                    "source_associations": _source_associations([item], polymer_source_chain_to_index),
                }
            )
            assignment[item.residue.residue_key] = index
            item.chain_index = index
            item.include_residue_record = True

    return groups, assignment


def _af3_missing_checks(
    sequence_references: list[dict[str, Any]],
    residues: list[ResidueRecord],
    chain_index_by_source_chain: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not sequence_references:
        checks = []
        for source_chain_id in sorted(
            {item.source_chain_id for item in residues if item.entity_type == gemmi.EntityType.Polymer}
        ):
            checks.append(
                {
                    "chain_index": chain_index_by_source_chain.get(source_chain_id),
                    "source_chain_id": source_chain_id,
                    "status": "NOT_PERFORMED",
                    "evidence_types": [],
                    "missing_residue_count": 0,
                    "reason": "AF3_INPUT_SEQUENCE_NOT_PROVIDED",
                }
            )
        return checks, []
    try:
        sequences = parse_af3_sequence_references(sequence_references)
    except Exception as exc:
        return [], [
            {
                "issue_type": "SEQUENCE_REFERENCE_CONFLICT",
                "subject": {"sequence_reference_paths": [entry["path"] for entry in sequence_references]},
                "evidence": [str(exc)],
                "resolution_status": "PENDING_CONFIRMATION",
            }
        ]
    checks: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    by_chain: dict[str, list[ResidueRecord]] = defaultdict(list)
    for residue in residues:
        if residue.entity_type == gemmi.EntityType.Polymer:
            by_chain[residue.source_chain_id].append(residue)
    for source_chain_id, chain_residues in sorted(by_chain.items()):
        sequence = sequences.get(source_chain_id)
        if sequence is None:
            checks.append(
                {
                    "chain_index": chain_index_by_source_chain.get(source_chain_id),
                    "source_chain_id": source_chain_id,
                    "status": "MAPPING_UNRESOLVED",
                    "evidence_types": ["AF3_INPUT_SEQUENCE"],
                    "missing_residue_count": 0,
                    "reason": "AF3_INPUT_CHAIN_NOT_FOUND",
                }
            )
            unresolved.append(
                {
                    "issue_type": "SEQUENCE_REFERENCE_CONFLICT",
                    "subject": {"source_chain_id": source_chain_id},
                    "evidence": ["AF3 input/FASTA contains no exact matching chain ID"],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            continue
        expected_names = [ONE_TO_THREE_PROTEIN.get(code, code) for code in sequence]
        observed_names = [item.residue_name for item in sorted(chain_residues, key=lambda item: item.residue_position)]
        if len(expected_names) == len(observed_names) and expected_names == observed_names:
            checks.append(
                {
                    "chain_index": chain_index_by_source_chain.get(source_chain_id),
                    "source_chain_id": source_chain_id,
                    "status": "NO_MISSING_RESIDUES",
                    "evidence_types": ["AF3_INPUT_SEQUENCE", "AF3_OUTPUT_COORDINATES"],
                    "missing_residue_count": 0,
                    "reason": None,
                }
            )
        else:
            unresolved.append(
                {
                    "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                    "subject": {
                        "source_chain_id": source_chain_id,
                        "expected_sequence": expected_names,
                        "observed_sequence": observed_names,
                    },
                    "evidence": ["AF3_INPUT_SEQUENCE", "AF3_OUTPUT_COORDINATES"],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            checks.append(
                {
                    "chain_index": chain_index_by_source_chain.get(source_chain_id),
                    "source_chain_id": source_chain_id,
                    "status": "MAPPING_UNRESOLVED",
                    "evidence_types": ["AF3_INPUT_SEQUENCE", "AF3_OUTPUT_COORDINATES"],
                    "missing_residue_count": 0,
                    "reason": "AUTHOR_SOURCE_RESIDS_FOR_MISSING_RESIDUES_UNAVAILABLE",
                }
            )
    return checks, unresolved


def execute_classification(config: dict[str, Any], script_dir: Path) -> tuple[dict[str, Any], dict[str, Any], Path, Path, Path, Path]:
    structure_config = _required_mapping(config, "structure")
    classification_config = _required_mapping(config, "classification")
    output_config = _required_mapping(config, "output")

    structure_path = _required_path(structure_config, "path")
    structure_hash = str(structure_config.get("sha256", ""))
    source_format = str(structure_config.get("source_format", ""))
    selected_model_id = str(structure_config.get("selected_model_id", ""))
    mode = str(classification_config.get("mode", ""))
    if not selected_model_id:
        raise ClassificationToolError("selected_model_id is required")
    if mode not in {"REGISTRY", "FORCE_FIELD_ANALYSIS"}:
        raise ClassificationToolError(f"unsupported classification mode: {mode}")
    require_sha256(structure_path, structure_hash)
    structure = parse_structure(structure_path)
    verify_source_format(structure_path, structure, source_format)
    model, residues, _atoms_by_serial = collect_selected_model(structure, selected_model_id)

    schema_dir = script_dir.parent / "schemas"
    reference_dir = script_dir.parent / "references"
    definitions_schema = schema_dir / "project_residue_definitions.schema.yaml"

    project_config = config.get("project_residue_definitions")
    project_path: Path | None = None
    project_defs: dict[str, dict[str, Any]] = {}
    project_hash: str | None = None
    if isinstance(project_config, dict):
        project_path = _optional_path(project_config, "path")
    if project_path is not None:
        expected_hash = project_config.get("sha256")
        if expected_hash:
            require_sha256(project_path, str(expected_hash))
        project_defs, project_hash = _load_definition_file(project_path, definitions_schema)

    standard_registry_path = Path(
        classification_config.get(
            "standard_registry_path",
            reference_dir / "standard_residue_registry.yaml",
        )
    ).resolve()
    linked_registry_path = Path(
        classification_config.get(
            "linked_registry_path",
            reference_dir / "topology_linked_nonstandard_residue_registry.yaml",
        )
    ).resolve()
    standard_defs, standard_hash = _load_definition_file(standard_registry_path, definitions_schema)
    linked_defs, linked_hash = _load_definition_file(linked_registry_path, definitions_schema)
    overlap = set(standard_defs).intersection(linked_defs)
    if overlap:
        raise ClassificationToolError(
            f"exact residue names occur in both Skill registries: {sorted(overlap)}"
        )
    skill_defs = {**standard_defs, **linked_defs}

    rtp_index: dict[str, list[RtpTemplate]] = {}
    rtp_files: list[Path] = []
    force_field_config = config.get("force_field") or {}
    terminal_mappings: dict[tuple[str, str], list[str]] = {}
    if mode == "FORCE_FIELD_ANALYSIS":
        if not isinstance(force_field_config, dict):
            raise ClassificationToolError("force_field config must be a mapping")
        force_field_root = _required_path(force_field_config, "root_path")
        explicit_rtp = [Path(value) for value in force_field_config.get("rtp_files", [])]
        rtp_index, rtp_files = load_rtp_index(
            force_field_root,
            explicit_rtp if explicit_rtp else None,
        )
        terminal_mappings = _terminal_mapping_index(force_field_config)

    terminal_roles = _terminal_roles_by_residue(residues)
    unresolved: list[dict[str, Any]] = []
    analyses: list[ResidueAnalysis] = []
    selected_rtp: dict[tuple, RtpTemplate | None] = {}
    for residue in residues:
        classification, template = _classify_residue(
            residue,
            mode,
            project_defs,
            skill_defs,
            rtp_index,
            terminal_roles,
            terminal_mappings,
            unresolved,
        )
        selected_rtp[residue.residue_key] = template
        analyses.append(
            ResidueAnalysis(
                residue=residue,
                classification=classification,
                conformation=_conformation_dict(residue),
                heavy_atom_check=_empty_heavy_check("NOT_PERFORMED", "PENDING_REFERENCE_RESOLUTION"),
                sequence_position=residue.label_seq,
            )
        )

    ccd_config = config.get("ccd") or {}
    if not isinstance(ccd_config, dict):
        raise ClassificationToolError("ccd config must be a mapping")
    observations_path = _required_path(output_config, "observations_path")
    manifest_path = _required_path(output_config, "reference_manifest_path")
    observations_schema = Path(
        output_config.get("observations_schema", schema_dir / "classification_observations.schema.yaml")
    ).resolve()
    manifest_schema = Path(
        output_config.get("reference_manifest_schema", schema_dir / "reference_manifest.schema.yaml")
    ).resolve()
    snapshot_dir = Path(
        ccd_config.get("project_snapshot_dir", observations_path.parent / "reference_data" / "ccd")
    ).resolve()
    local_reference_dirs = [Path(value).resolve() for value in ccd_config.get("local_reference_dirs", [])]
    shared_cache_path = _optional_path(ccd_config, "shared_cache_path")
    retrieval_policy = str(ccd_config.get("retrieval_policy", "CACHE_ONLY"))
    remote_base_url = str(ccd_config.get("remote_base_url", "https://files.rcsb.org/ligands/download"))
    timeout_seconds = float(ccd_config.get("timeout_seconds", 30.0))

    ccd_templates: dict[str, CcdTemplate | None] = {}
    ccd_manifest: dict[str, dict[str, Any]] = {}
    mapped_names: dict[str, set[str]] = defaultdict(set)
    for analysis in analyses:
        value = analysis.classification
        if value.resolution_status != "RESOLVED":
            continue
        if value.topology_class in {"SOLVENT_COMPONENT", "ION_COMPONENT"}:
            continue
        use_ccd = mode == "REGISTRY" or value.topology_class != "STANDARD_RESIDUE"
        if use_ccd and value.ccd_id is not None:
            mapped_names[value.ccd_id].add(analysis.residue.residue_name)

    for component_id in sorted(mapped_names):
        template, manifest_entry, issue = acquire_ccd_template(
            component_id,
            sorted(mapped_names[component_id]),
            project_snapshot_dir=snapshot_dir,
            local_reference_dirs=local_reference_dirs,
            shared_cache_path=shared_cache_path,
            retrieval_policy=retrieval_policy,
            remote_base_url=remote_base_url,
            timeout_seconds=timeout_seconds,
        )
        ccd_templates[component_id] = template
        ccd_manifest[component_id] = manifest_entry
        if issue is not None:
            unresolved.append(issue)

    for analysis in analyses:
        value = analysis.classification
        if analysis.conformation["status"] == "MULTIPLE_CONFORMATIONS":
            analysis.heavy_atom_check = _empty_heavy_check(
                "NOT_PERFORMED",
                "MULTIPLE_CONFORMATIONS_PRESENT",
            )
            continue
        if value.resolution_status != "RESOLVED":
            analysis.heavy_atom_check = _empty_heavy_check(
                "NOT_PERFORMED",
                "CLASSIFICATION_UNRESOLVED",
            )
            continue
        if value.topology_class in {"SOLVENT_COMPONENT", "ION_COMPONENT"}:
            analysis.heavy_atom_check = _empty_heavy_check(
                "NOT_PERFORMED",
                "SOLVENT_OR_ION_TEMPLATE_CHECK_NOT_REQUIRED",
            )
            continue
        observed_heavy = _observed_heavy_names(analysis.residue)
        if mode == "FORCE_FIELD_ANALYSIS" and value.topology_class == "STANDARD_RESIDUE":
            template = selected_rtp.get(analysis.residue.residue_key)
            if template is None:
                analysis.heavy_atom_check = {
                    **_empty_heavy_check("REFERENCE_TEMPLATE_UNAVAILABLE", "RTP_TEMPLATE_NOT_RESOLVED"),
                    "reference_type": "RTP",
                    "reference_name": value.rtp_template_name,
                }
                continue
            missing, unexpected = compare_heavy_atom_names(observed_heavy, template)
            analysis.heavy_atom_check = {
                "status": _heavy_status(missing, unexpected),
                "reference_type": "RTP",
                "reference_name": template.residue_name,
                "missing_atoms": missing,
                "unexpected_atoms": unexpected,
                "reason": None,
            }
            continue
        component_id = value.ccd_id
        template = ccd_templates.get(component_id or "")
        if component_id is None or template is None:
            analysis.heavy_atom_check = {
                **_empty_heavy_check("REFERENCE_TEMPLATE_UNAVAILABLE", "CCD_TEMPLATE_UNAVAILABLE"),
                "reference_type": "CCD",
                "reference_name": component_id,
            }
            continue
        missing, unexpected, mappings = compare_ccd_heavy_atoms(observed_heavy, template)
        if mappings:
            status = "ATOM_NAME_MAPPING_REQUIRED"
            reason = "; ".join(
                f"{item['structure_atom_name']}->{item['ccd_atom_id']}"
                for item in mappings
            )
        else:
            status = _heavy_status(missing, unexpected)
            reason = None
        analysis.heavy_atom_check = {
            "status": status,
            "reference_type": "CCD",
            "reference_name": component_id,
            "missing_atoms": missing,
            "unexpected_atoms": unexpected,
            "reason": reason,
        }

    chain_groups, assignment = _build_chain_groups(analyses)
    chain_index_by_source_chain = {
        group["source_chain_id"]: group["chain_index"]
        for group in chain_groups
        if group["group_type"] == "POLYMER_CHAIN"
        and isinstance(group.get("source_chain_id"), str)
    }

    missing_records: list[MissingResidueEvidence] = []
    missing_checks: list[dict[str, Any]] = []
    observed_sequence_positions: dict[tuple, int] = {}
    if source_format in {"PDB", "MMCIF"}:
        explicit = explicit_missing_residues(structure_path, source_format, selected_model_id)
        resolved, missing_unresolved, observed_sequence_positions, chain_checks = sequence_based_missing_residues(
            structure,
            model,
            residues,
            explicit,
        )
        unresolved.extend(missing_unresolved)
        seen_missing: set[tuple] = set()
        for item in [*resolved, *explicit]:
            key = (
                item.source_chain_id,
                item.source_resid_number,
                item.insertion_code,
                item.residue_name,
            )
            if key in seen_missing:
                continue
            seen_missing.add(key)
            if item.source_chain_id not in chain_index_by_source_chain:
                unresolved.append(
                    {
                        "issue_type": "MISSING_RESIDUE_CHAIN_UNRESOLVED",
                        "subject": {
                            "source_chain_id": item.source_chain_id,
                            "source_resid": {
                                "number": item.source_resid_number,
                                "insertion_code": item.insertion_code,
                            },
                            "residue_name": item.residue_name,
                        },
                        "evidence": [item.evidence_type],
                        "resolution_status": "PENDING_CONFIRMATION",
                    }
                )
                continue
            if item.source_resid_number is None:
                unresolved.append(
                    {
                        "issue_type": "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE",
                        "subject": {
                            "source_chain_id": item.source_chain_id,
                            "residue_name": item.residue_name,
                            "sequence_position": item.sequence_position,
                        },
                        "evidence": [item.evidence_type],
                        "resolution_status": "PENDING_CONFIRMATION",
                    }
                )
                continue
            missing_records.append(item)
        for check in chain_checks:
            check["chain_index"] = chain_index_by_source_chain.get(check["source_chain_id"])
            missing_checks.append(check)
        explicit_chains = {item.source_chain_id for item in explicit}
        represented_chains = {item["source_chain_id"] for item in missing_checks}
        for source_chain_id in sorted(explicit_chains - represented_chains, key=lambda value: "" if value is None else value):
            count = sum(1 for item in explicit if item.source_chain_id == source_chain_id and item.source_resid_number is not None)
            missing_checks.append(
                {
                    "chain_index": chain_index_by_source_chain.get(source_chain_id),
                    "source_chain_id": source_chain_id,
                    "status": "MISSING_RESIDUES_FOUND" if count else "MAPPING_UNRESOLVED",
                    "evidence_types": ["PDB_REMARK_465" if source_format == "PDB" else "MMCIF_UNOBSERVED_RESIDUES"],
                    "missing_residue_count": count,
                    "reason": None if count else "MISSING_RESIDUE_IDENTIFIERS_UNRESOLVED",
                }
            )
    else:
        sequence_references = config.get("sequence_references", []) or []
        if not isinstance(sequence_references, list):
            raise ClassificationToolError("sequence_references must be a list")
        missing_checks, af3_unresolved = _af3_missing_checks(
            sequence_references,
            residues,
            chain_index_by_source_chain,
        )
        unresolved.extend(af3_unresolved)

    analysis_by_key = {analysis.residue.residue_key: analysis for analysis in analyses}
    for analysis in analyses:
        sequence_position = observed_sequence_positions.get(
            (
                analysis.residue.source_chain_id,
                analysis.residue.source_resid_number,
                analysis.residue.insertion_code,
                analysis.residue.residue_name,
            )
        )
        if sequence_position is not None:
            analysis.sequence_position = sequence_position

    for item in missing_records:
        chain_index = chain_index_by_source_chain[item.source_chain_id or ""]
        pseudo = ResidueRecord(
            model_id=selected_model_id,
            source_chain_id=item.source_chain_id or "",
            source_resid_number=str(item.source_resid_number),
            insertion_code=item.insertion_code,
            residue_name=item.residue_name,
            entity_id=None,
            entity_type=gemmi.EntityType.Polymer,
            polymer_type=gemmi.PolymerType.Unknown,
            label_seq=item.sequence_position,
            chain_position=-1,
            residue_position=-1,
            residue=gemmi.Residue(),
            atoms=[],
        )
        classification, _template = _classify_residue(
            pseudo,
            mode,
            project_defs,
            skill_defs,
            rtp_index,
            {},
            terminal_mappings,
            unresolved,
        )
        analyses.append(
            ResidueAnalysis(
                residue=pseudo,
                classification=classification,
                conformation={"status": "NOT_APPLICABLE", "altloc_ids": []},
                heavy_atom_check=_empty_heavy_check("NOT_APPLICABLE", "RESIDUE_COORDINATES_ABSENT"),
                sequence_position=item.sequence_position,
                chain_index=chain_index,
                include_residue_record=True,
            )
        )

    entity_groups: dict[tuple[str | None, str, str | None], set[str]] = defaultdict(set)
    for residue in residues:
        entity_groups[
            (
                residue.entity_id,
                _entity_name(residue.entity_type),
                _polymer_type_name(residue.polymer_type),
            )
        ].add(residue.source_chain_id)
    entities = [
        {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "polymer_type": polymer_type,
            "source_chain_ids": sorted(source_chain_ids),
        }
        for (entity_id, entity_type, polymer_type), source_chain_ids in sorted(
            entity_groups.items(), key=lambda item: (str(item[0][0]), item[0][1], str(item[0][2]))
        )
    ]

    residue_records = []
    for analysis in analyses:
        if not analysis.include_residue_record:
            continue
        if analysis.chain_index is None:
            raise ClassificationToolError("internal classification error: residue has no chain_index")
        presence_status = "MISSING_EXPECTED" if not analysis.residue.atoms else "OBSERVED"
        residue_records.append(
            {
                "chain_index": analysis.chain_index,
                "source_chain_id": analysis.residue.source_chain_id,
                "source_resid": {
                    "number": analysis.residue.source_resid_number,
                    "insertion_code": analysis.residue.insertion_code,
                },
                "residue_name": analysis.residue.residue_name,
                "presence_status": presence_status,
                "sequence_position": analysis.sequence_position,
                "classification_observation": _classification_dict(analysis.classification),
                "conformation_observation": analysis.conformation,
                "heavy_atom_check": analysis.heavy_atom_check,
            }
        )

    heavy_issue_statuses = {
        "MISSING_EXPECTED_HEAVY_ATOMS",
        "UNEXPECTED_HEAVY_ATOMS",
        "MISSING_AND_UNEXPECTED_HEAVY_ATOMS",
        "ATOM_NAME_MAPPING_REQUIRED",
        "REFERENCE_TEMPLATE_UNAVAILABLE",
    }
    observations = {
        "schema_version": "1.0",
        "input": {
            "structure_path": str(structure_path),
            "structure_sha256": structure_hash,
            "source_format": source_format,
            "selected_model_id": selected_model_id,
            "classification_mode": mode,
        },
        "entities": entities,
        "chain_groups": chain_groups,
        "residue_records": residue_records,
        "missing_residue_checks": missing_checks,
        "unresolved_observations": unresolved,
        "summary": {
            "entity_count": len(entities),
            "chain_group_count": len(chain_groups),
            "recorded_residue_count": len(residue_records),
            "observed_residue_count": sum(item["presence_status"] == "OBSERVED" for item in residue_records),
            "missing_expected_residue_count": sum(item["presence_status"] == "MISSING_EXPECTED" for item in residue_records),
            "unresolved_observation_count": len(unresolved),
            "multiple_conformation_residue_count": sum(
                item["conformation_observation"]["status"] == "MULTIPLE_CONFORMATIONS"
                for item in residue_records
            ),
            "heavy_atom_issue_count": sum(
                item["heavy_atom_check"]["status"] in heavy_issue_statuses
                for item in residue_records
            ),
        },
    }

    sequence_manifest = []
    for entry in config.get("sequence_references", []) or []:
        path = Path(entry["path"]).resolve()
        expected_hash = entry.get("sha256")
        actual_hash = require_sha256(path, str(expected_hash)) if expected_hash else sha256_file(path)
        sequence_manifest.append(
            {
                "path": str(path),
                "sha256": actual_hash,
                "status": "LOADED",
                "reference_type": entry.get("type") or entry.get("reference_type") or "OTHER",
            }
        )

    force_field_manifest = None
    if mode == "FORCE_FIELD_ANALYSIS":
        force_field_root = _required_path(force_field_config, "root_path")
        force_field_manifest = {
            "root_path": str(force_field_root),
            "files": [
                {
                    "path": str(path.resolve()),
                    "sha256": sha256_file(path.resolve()),
                    "status": "LOADED",
                    "role": "RTP_HEAVY_ATOM_TEMPLATE",
                }
                for path in rtp_files
            ],
            "status": "LOADED",
        }

    manifest = {
        "schema_version": "1.0",
        "classification_mode": mode,
        "project_files": {
            "residue_definitions": {
                "path": str(project_path) if project_path is not None else None,
                "sha256": project_hash,
                "status": "LOADED" if project_path is not None else "NOT_PROVIDED",
            }
        },
        "skill_references": [
            {
                "path": str(standard_registry_path),
                "sha256": standard_hash,
                "status": "LOADED",
            },
            {
                "path": str(linked_registry_path),
                "sha256": linked_hash,
                "status": "LOADED",
            },
        ],
        "force_field": force_field_manifest,
        "ccd_components": [ccd_manifest[key] for key in sorted(ccd_manifest)],
        "sequence_references": sequence_manifest,
        "relation_definition_files": {
            "possible_connections": {"path": None, "sha256": None, "status": "NOT_PROVIDED"},
            "possible_coordination": {"path": None, "sha256": None, "status": "NOT_PROVIDED"},
        },
    }

    if sha256_file(structure_path) != structure_hash:
        raise ClassificationToolError("input structure changed during classification")
    validate_document(observations, observations_schema)
    validate_document(manifest, manifest_schema)
    return observations, manifest, observations_path, manifest_path, observations_schema, manifest_schema

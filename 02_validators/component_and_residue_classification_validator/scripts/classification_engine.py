#!/usr/bin/env python3
"""Runtime facade for the component/residue classification v1.2 engine.

The implementation remains in ``classification_engine_core.py``. This facade
keeps structural entity/polymer facts authoritative for chain grouping and
normalizes missing-residue mapping outcomes without changing the underlying
scientific observations.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
import json
import re

import classification_engine_core as _core
from structure_records import clean_optional_text


_original_build_chain_groups = getattr(
    _core,
    "_classification_engine_original_build_chain_groups",
    _core._build_chain_groups,
)
_core._classification_engine_original_build_chain_groups = _original_build_chain_groups
_original_explicit_missing_residues = getattr(
    _core,
    "_classification_engine_original_explicit_missing_residues",
    _core.explicit_missing_residues,
)
_core._classification_engine_original_explicit_missing_residues = (
    _original_explicit_missing_residues
)
_original_sequence_based_missing_residues = getattr(
    _core,
    "_classification_engine_original_sequence_based_missing_residues",
    _core.sequence_based_missing_residues,
)
_core._classification_engine_original_sequence_based_missing_residues = (
    _original_sequence_based_missing_residues
)
_original_execute_classification = _core.execute_classification


_PDB_RESIDUE_NAME = re.compile(r"[A-Za-z0-9]{1,3}")
_PDB_SEQUENCE_NUMBER = re.compile(r"-?\d+")


def _build_chain_groups(analyses):
    """Group structural chains without erasing unresolved classification state.

    ``classification.polymer_class`` is a scientific classification result and
    may be null or conflicting. ``ResidueRecord`` entity/polymer metadata is a
    separate structural fact. During grouping only, temporarily project an
    available structural class onto the analysis, then restore the original
    classification objects before downstream output is built.
    """

    replaced = []
    try:
        for analysis in analyses:
            structural_class = _core._entity_polymer_class(analysis.residue)
            value = analysis.classification
            if structural_class is None or structural_class == value.polymer_class:
                continue
            replaced.append((analysis, value))
            analysis.classification = _core.ClassificationValue(
                polymer_class=structural_class,
                topology_class=value.topology_class,
                resolution_status=value.resolution_status,
                primary_source=value.primary_source,
                evidence=value.evidence,
                ccd_id=value.ccd_id,
                rtp_template_name=value.rtp_template_name,
            )
        return _original_build_chain_groups(analyses)
    finally:
        for analysis, value in replaced:
            analysis.classification = value


def _strict_pdb_missing_residues(path, selected_model_id):
    """Parse only data rows from the fixed-column PDB REMARK 465 table.

    REMARK 465 contains explanatory prose and a table header in addition to
    residue rows. Accepting arbitrary whitespace-split lines can therefore
    fabricate residue and chain identifiers from words such as ``MISSING
    RESIDUES``. A formal row must contain a valid fixed-column residue name and
    signed integer author sequence number.
    """

    results = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.startswith("REMARK 465") or len(raw) < 26:
            continue
        model_field = raw[11:14].strip()
        residue_name = raw[15:18].strip()
        chain_id = clean_optional_text(raw[19:20] if len(raw) >= 20 else None)
        sequence_number = raw[21:26].strip()
        insertion_code = clean_optional_text(raw[26:27] if len(raw) >= 27 else None)
        if model_field:
            if not model_field.isdigit() or model_field != selected_model_id:
                continue
        if _PDB_RESIDUE_NAME.fullmatch(residue_name) is None:
            continue
        if _PDB_SEQUENCE_NUMBER.fullmatch(sequence_number) is None:
            continue
        results.append(
            _core.MissingResidueEvidence(
                source_chain_id=chain_id,
                residue_name=residue_name,
                source_resid_number=sequence_number,
                insertion_code=insertion_code,
                sequence_position=None,
                evidence_type="PDB_REMARK_465",
            )
        )
    return results


def _explicit_missing_residues(path, source_format, selected_model_id):
    if source_format == "PDB":
        return _strict_pdb_missing_residues(path, selected_model_id)
    return _original_explicit_missing_residues(
        path,
        source_format,
        selected_model_id,
    )


def _sequence_based_missing_residues(
    structure,
    model,
    residues,
    explicit_records,
):
    """Reconcile alignment-only ambiguity with explicit author residue IDs.

    Repeated missing residue names can make sequence-position pairing
    non-unique, even though REMARK 465 already provides every required author
    residue identifier. Such a case is not
    ``MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE``. Preserve the explicit record,
    assign sequence positions monotonically where the per-name counts permit,
    and suppress only the redundant alignment-only issue.
    """

    resolved, unresolved, observed_positions, chain_checks = (
        _original_sequence_based_missing_residues(
            structure,
            model,
            residues,
            explicit_records,
        )
    )

    available_plain_records = Counter(
        (item.source_chain_id, item.residue_name)
        for item in resolved
        if item.source_chain_id is not None
        and item.source_resid_number is not None
        and item.sequence_position is None
        and item.evidence_type in {
            "PDB_REMARK_465",
            "MMCIF_UNOBSERVED_RESIDUES",
        }
    )
    recovered_positions = defaultdict(list)
    retained_unresolved = []
    for item in unresolved:
        subject = item.get("subject") or {}
        key = (subject.get("source_chain_id"), subject.get("residue_name"))
        alignment_only = item.get("evidence") == ["ENTITY_SEQUENCE_ALIGNMENT"]
        if (
            item.get("issue_type") == "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE"
            and alignment_only
            and subject.get("sequence_position") is not None
            and available_plain_records[key] > 0
        ):
            available_plain_records[key] -= 1
            recovered_positions[key].append(int(subject["sequence_position"]))
            continue
        retained_unresolved.append(item)

    position_queues = {
        key: deque(sorted(values))
        for key, values in recovered_positions.items()
    }
    normalized_resolved = []
    for item in resolved:
        key = (item.source_chain_id, item.residue_name)
        queue = position_queues.get(key)
        if (
            queue
            and item.source_resid_number is not None
            and item.sequence_position is None
            and item.evidence_type in {
                "PDB_REMARK_465",
                "MMCIF_UNOBSERVED_RESIDUES",
            }
        ):
            normalized_resolved.append(
                _core.MissingResidueEvidence(
                    source_chain_id=item.source_chain_id,
                    residue_name=item.residue_name,
                    source_resid_number=item.source_resid_number,
                    insertion_code=item.insertion_code,
                    sequence_position=queue.popleft(),
                    evidence_type=f"{item.evidence_type}+ENTITY_SEQUENCE_ALIGNMENT",
                )
            )
        else:
            normalized_resolved.append(item)

    return (
        normalized_resolved,
        retained_unresolved,
        observed_positions,
        chain_checks,
    )


def _merge_unresolved_observations(items):
    """Merge repeated reports of the same unresolved scientific subject.

    Different pipeline stages may encounter the same missing-residue mapping
    problem. Identity is defined by issue type, subject and resolution status;
    evidence from all stages is retained in first-seen order.
    """

    merged = []
    index_by_key = {}
    for item in items:
        key = json.dumps(
            {
                "issue_type": item.get("issue_type"),
                "subject": item.get("subject"),
                "resolution_status": item.get("resolution_status"),
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        existing_index = index_by_key.get(key)
        if existing_index is None:
            copied = dict(item)
            copied["evidence"] = list(item.get("evidence", []))
            index_by_key[key] = len(merged)
            merged.append(copied)
            continue
        evidence = merged[existing_index]["evidence"]
        for value in item.get("evidence", []):
            if value not in evidence:
                evidence.append(value)
    return merged


def _normalize_missing_residue_outputs(observations):
    """Make missing-residue check status agree with identifier resolvability."""

    unresolved = _merge_unresolved_observations(
        observations.get("unresolved_observations", [])
    )
    observations["unresolved_observations"] = unresolved

    source_resid_unresolved_chains = set()
    chain_unresolved_chains = set()
    for item in unresolved:
        subject = item.get("subject") or {}
        source_chain_id = subject.get("source_chain_id")
        if item.get("issue_type") == "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE":
            source_resid_unresolved_chains.add(source_chain_id)
        elif item.get("issue_type") == "MISSING_RESIDUE_CHAIN_UNRESOLVED":
            chain_unresolved_chains.add(source_chain_id)

    for check in observations.get("missing_residue_checks", []):
        source_chain_id = check.get("source_chain_id")
        if check.get("chain_index") is None and source_chain_id in chain_unresolved_chains:
            check["status"] = "MAPPING_UNRESOLVED"
            check["missing_residue_count"] = 0
            check["reason"] = "MISSING_RESIDUE_CHAIN_UNRESOLVED"
        elif (
            check.get("missing_residue_count") == 0
            and source_chain_id in source_resid_unresolved_chains
        ):
            check["status"] = "MAPPING_UNRESOLVED"
            check["reason"] = "AUTHOR_SOURCE_RESIDS_FOR_MISSING_RESIDUES_UNAVAILABLE"

    summary = observations.get("summary")
    if isinstance(summary, dict):
        summary["unresolved_observation_count"] = len(unresolved)
    return observations


_core._build_chain_groups = _build_chain_groups
_core.explicit_missing_residues = _explicit_missing_residues
_core.sequence_based_missing_residues = _sequence_based_missing_residues

# Preserve the previous module surface, including internal helpers used by the
# executable tests, while ensuring execute_classification resolves the patched
# functions through the core module globals.
for _name in dir(_core):
    if _name.startswith("__") or _name in {
        "_build_chain_groups",
        "explicit_missing_residues",
        "sequence_based_missing_residues",
    }:
        continue
    globals()[_name] = getattr(_core, _name)


def execute_classification(config, script_dir):
    """Run the core engine and normalize cross-stage missing-residue outcomes."""

    (
        observations,
        manifest,
        observations_path,
        manifest_path,
        observations_schema,
        manifest_schema,
    ) = _original_execute_classification(config, script_dir)
    _normalize_missing_residue_outputs(observations)
    _core.validate_document(observations, observations_schema)
    return (
        observations,
        manifest,
        observations_path,
        manifest_path,
        observations_schema,
        manifest_schema,
    )

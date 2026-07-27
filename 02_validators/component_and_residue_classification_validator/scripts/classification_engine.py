#!/usr/bin/env python3
"""Runtime facade for the component/residue classification v1.2 engine.

The implementation remains in ``classification_engine_core.py``. This facade
keeps structural entity/polymer facts authoritative for chain grouping and
normalizes missing-residue mapping outcomes without changing the underlying
scientific observations.
"""
from __future__ import annotations

import json

import classification_engine_core as _core


_original_build_chain_groups = getattr(
    _core,
    "_classification_engine_original_build_chain_groups",
    _core._build_chain_groups,
)
_core._classification_engine_original_build_chain_groups = _original_build_chain_groups
_original_execute_classification = _core.execute_classification


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

# Preserve the previous module surface, including internal helpers used by the
# executable tests, while ensuring execute_classification resolves the patched
# grouping function through the core module globals.
for _name in dir(_core):
    if _name.startswith("__") or _name == "_build_chain_groups":
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

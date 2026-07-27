#!/usr/bin/env python3
"""Integrate baseline classification, relation checks and recorded decisions."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    read_yaml_strict,
    require_sha256,
    sha256_file,
    validate_document,
)

VERSION = "0.2.0-draft"

RELATION_REQUEST_TYPES = {
    "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE",
    "CONNECTION_DEFINITION_CONFLICT",
    "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
    "COORDINATION_DEFINITION_CONFLICT",
}
CLASSIFICATION_REQUEST_TYPES = {
    "PROJECT_REGISTRY_CLASSIFICATION_CONFLICT",
    "PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT",
    "RESIDUE_CLASSIFICATION_UNRESOLVED",
}

ALLOWED_DECISIONS = {
    "PROJECT_REGISTRY_CLASSIFICATION_CONFLICT": ["SET_CLASSIFICATION"],
    "PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT": ["SET_CLASSIFICATION"],
    "RESIDUE_CLASSIFICATION_UNRESOLVED": ["SET_CLASSIFICATION"],
    "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE": ["SELECT_RTP_TEMPLATE", "PROVIDE_CORRECTED_FORCE_FIELD"],
    "TERMINAL_RTP_TEMPLATE_AMBIGUOUS": ["SELECT_RTP_TEMPLATE", "PROVIDE_TERMINAL_TEMPLATE_MAPPING"],
    "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE": ["CONFIRM", "REJECT"],
    "CONNECTION_DEFINITION_CONFLICT": ["CONFIRM", "REJECT", "PROVIDE_CORRECTED_DEFINITION"],
    "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE": ["CONFIRM", "REJECT"],
    "COORDINATION_DEFINITION_CONFLICT": ["CONFIRM", "REJECT", "PROVIDE_CORRECTED_DEFINITION"],
    "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE": [
        "PROVIDE_SOURCE_RESID",
        "PROVIDE_NUMBERING_MAPPING",
        "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES",
    ],
    "MISSING_RESIDUE_CHAIN_UNRESOLVED": [
        "ASSIGN_CHAIN_INDEX",
        "PROVIDE_CHAIN_MAPPING",
        "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES",
    ],
    "SEQUENCE_REFERENCE_CONFLICT": ["SELECT_SEQUENCE_REFERENCE", "PROVIDE_CORRECTED_SEQUENCE_REFERENCE"],
    "MULTIPLE_LOCAL_CCD_CANDIDATES": ["SELECT_CCD_CANDIDATE", "PROVIDE_CORRECTED_CCD_FILE"],
    "INVALID_PROJECT_CCD_SNAPSHOT": ["REPLACE_CCD_SNAPSHOT", "REMOVE_CCD_SNAPSHOT"],
}


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[tuple, tuple] = {}

    def find(self, item: tuple) -> tuple:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, first: tuple, second: tuple) -> None:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root != second_root:
            if first_root <= second_root:
                self.parent[second_root] = first_root
            else:
                self.parent[first_root] = second_root

    def components(self) -> list[set[tuple]]:
        grouped: dict[tuple, set[tuple]] = defaultdict(set)
        for item in self.parent:
            grouped[self.find(item)].add(item)
        return list(grouped.values())


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


def _load_validated(
    config: dict[str, Any],
    key: str,
    default_schema: Path,
) -> tuple[dict[str, Any], Path, str]:
    item = _required_mapping(config, key)
    path = _required_path(item, "path")
    expected_hash = str(item.get("sha256", ""))
    observed_hash = require_sha256(path, expected_hash)
    schema = Path(item.get("schema", default_schema)).resolve()
    document = read_yaml_strict(path)
    if not isinstance(document, dict):
        raise ClassificationToolError(f"{key} document must be a mapping")
    validate_document(document, schema)
    return document, path, observed_hash


def _canonical_request_payload(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_type": request["request_type"],
        "subject": request["subject"],
        "evidence": request["evidence"],
    }


def _request_fingerprint(request: dict[str, Any]) -> str:
    payload = json.dumps(
        _canonical_request_payload(request),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _natural_key(endpoint: dict[str, Any]) -> tuple[str | None, str, str | None, str]:
    source_resid = endpoint["source_resid"]
    return (
        endpoint.get("source_chain_id"),
        str(source_resid["number"]),
        source_resid.get("insertion_code"),
        endpoint["residue_name"],
    )


def _endpoint_key(endpoint: dict[str, Any]) -> tuple[str | None, str, str | None, str, str]:
    return (*_natural_key(endpoint), endpoint["atom_name"])


def _strip_endpoint(endpoint: dict[str, Any], chain_index: int | None = None) -> dict[str, Any]:
    return {
        "chain_index": int(chain_index if chain_index is not None else endpoint["chain_index"]),
        "source_chain_id": endpoint.get("source_chain_id"),
        "source_resid": {
            "number": str(endpoint["source_resid"]["number"]),
            "insertion_code": endpoint["source_resid"].get("insertion_code"),
        },
        "residue_name": endpoint["residue_name"],
        "atom_name": endpoint["atom_name"],
    }


def _unresolved_to_request(issue: dict[str, Any]) -> dict[str, Any]:
    issue_type = issue.get("issue_type", "RESIDUE_CLASSIFICATION_UNRESOLVED")
    if issue_type not in ALLOWED_DECISIONS:
        issue_type = "RESIDUE_CLASSIFICATION_UNRESOLVED"
    return {
        "request_type": issue_type,
        "subject": copy.deepcopy(issue.get("subject", {})),
        "evidence": {"items": copy.deepcopy(issue.get("evidence", []))},
        "reason": "; ".join(str(item) for item in issue.get("evidence", []))
        or "classification evidence is unresolved",
        "allowed_decisions": ALLOWED_DECISIONS[issue_type],
    }


def _classification_pending_request(record: dict[str, Any]) -> dict[str, Any]:
    classification = record["classification_observation"]
    return {
        "request_type": "RESIDUE_CLASSIFICATION_UNRESOLVED",
        "subject": {
            "source_chain_id": record.get("source_chain_id"),
            "source_resid": copy.deepcopy(record["source_resid"]),
            "residue_name": record["residue_name"],
            "observed_resolution_status": classification["resolution_status"],
        },
        "evidence": {"items": copy.deepcopy(classification.get("evidence", []))},
        "reason": "residue classification remains unresolved after the baseline pass",
        "allowed_decisions": ["SET_CLASSIFICATION"],
    }


def _connection_requests(document: dict[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for definition in document.get("definition_results", []):
        for pair in definition.get("pair_results", []):
            status = pair["status"]
            if status not in {"GEOMETRY_SUPPORTED_CANDIDATE", "CONNECTION_DEFINITION_CONFLICT"}:
                continue
            request_type = (
                "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE"
                if status == "GEOMETRY_SUPPORTED_CANDIDATE"
                else "CONNECTION_DEFINITION_CONFLICT"
            )
            requests.append(
                {
                    "request_type": request_type,
                    "subject": {
                        "partner_1": copy.deepcopy(pair["partner_1"]),
                        "partner_2": copy.deepcopy(pair["partner_2"]),
                    },
                    "evidence": {
                        "definition_index": definition["definition_index"],
                        "label": definition.get("label"),
                        "definition": copy.deepcopy(definition["definition"]),
                        "explicit_connection": copy.deepcopy(pair["explicit_connection"]),
                        "geometry": copy.deepcopy(pair["geometry"]),
                        "detail": pair.get("detail"),
                    },
                    "reason": (
                        "geometry supports a possible covalent connection but no confirmed relation is available"
                        if status == "GEOMETRY_SUPPORTED_CANDIDATE"
                        else "the explicit structure relation conflicts with the project connection definition"
                    ),
                    "allowed_decisions": ALLOWED_DECISIONS[request_type],
                }
            )
    return requests


def _coordination_requests(document: dict[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for definition in document.get("definition_results", []):
        for pair in definition.get("pair_results", []):
            status = pair["status"]
            if status not in {
                "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
                "COORDINATION_DEFINITION_CONFLICT",
            }:
                continue
            request_type = status
            requests.append(
                {
                    "request_type": request_type,
                    "subject": {
                        "metal": copy.deepcopy(pair["metal"]),
                        "donor": copy.deepcopy(pair["donor"]),
                    },
                    "evidence": {
                        "definition_index": definition["definition_index"],
                        "label": definition.get("label"),
                        "definition": copy.deepcopy(definition["definition"]),
                        "explicit_coordination": copy.deepcopy(pair["explicit_coordination"]),
                        "geometry": copy.deepcopy(pair["geometry"]),
                        "detail": pair.get("detail"),
                        "topology_effect_evaluation": copy.deepcopy(
                            pair["topology_effect_evaluation"]
                        ),
                    },
                    "reason": (
                        "geometry supports a possible metal coordination relation but user confirmation is required"
                        if status == "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"
                        else "the explicit structure relation conflicts with the project coordination definition"
                    ),
                    "allowed_decisions": ALLOWED_DECISIONS[request_type],
                }
            )
    return requests


def _deduplicate_requests(requests: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for request in requests:
        fingerprint = _request_fingerprint(request)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        result.append(request)
    return result


def _load_decisions(
    config: dict[str, Any],
    confirmation_schema: Path,
) -> dict[str, dict[str, Any]]:
    decision_source = config.get("decision_source")
    if decision_source is None:
        return {}
    if not isinstance(decision_source, dict):
        raise ClassificationToolError("decision_source must be a mapping")
    path = _required_path(decision_source, "confirmation_requests_path")
    expected_hash = str(decision_source.get("confirmation_requests_sha256", ""))
    require_sha256(path, expected_hash)
    document = read_yaml_strict(path)
    validate_document(document, confirmation_schema)
    by_index = {item["request_index"]: item for item in document["requests"]}
    decisions: dict[str, dict[str, Any]] = {}
    for decision in decision_source.get("decisions", []) or []:
        if not isinstance(decision, dict):
            raise ClassificationToolError("each decision must be a mapping")
        request_index = decision.get("request_index")
        if request_index not in by_index:
            raise ClassificationToolError(
                f"decision references missing request_index {request_index}"
            )
        request = by_index[request_index]
        decision_name = decision.get("decision")
        if decision_name not in request["allowed_decisions"]:
            raise ClassificationToolError(
                f"decision {decision_name!r} is not allowed for request {request_index}"
            )
        fingerprint = _request_fingerprint(request)
        if fingerprint in decisions:
            raise ClassificationToolError(
                f"multiple decisions resolve the same confirmation request {request_index}"
            )
        decisions[fingerprint] = copy.deepcopy(decision)
    return decisions


def _relation_from_pair(
    relation_type: str,
    endpoint_1: dict[str, Any],
    endpoint_2: dict[str, Any],
    evidence_status: str,
    topology_effect_applied: bool,
) -> dict[str, Any]:
    return {
        "relation_type": relation_type,
        "endpoint_1": _strip_endpoint(endpoint_1),
        "endpoint_2": _strip_endpoint(endpoint_2),
        "evidence_status": evidence_status,
        "topology_effect_applied": topology_effect_applied,
    }


def _explicit_relations(
    connections: dict[str, Any],
    coordination: dict[str, Any],
) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for definition in connections.get("definition_results", []):
        for pair in definition.get("pair_results", []):
            if pair["status"] == "CONFIRMED_BY_STRUCTURE":
                relations.append(
                    _relation_from_pair(
                        "COVALENT_CONNECTION",
                        pair["partner_1"],
                        pair["partner_2"],
                        "CONFIRMED_BY_STRUCTURE",
                        True,
                    )
                )
    for definition in coordination.get("definition_results", []):
        promote = bool(
            definition["definition"]["topology_effect"][
                "promote_nonstandard_to_linked"
            ]
        )
        for pair in definition.get("pair_results", []):
            if pair["status"] == "CONFIRMED_BY_STRUCTURE":
                relations.append(
                    _relation_from_pair(
                        "METAL_COORDINATION",
                        pair["metal"],
                        pair["donor"],
                        "CONFIRMED_BY_STRUCTURE",
                        promote,
                    )
                )
    return relations


def _decision_relation(
    request: dict[str, Any],
    decision: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    decision_name = decision["decision"]
    request_type = request["request_type"]
    if request_type in {
        "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE",
        "CONNECTION_DEFINITION_CONFLICT",
    }:
        endpoint_1 = request["subject"]["partner_1"]
        endpoint_2 = request["subject"]["partner_2"]
        relation_type = "COVALENT_CONNECTION"
        topology_effect = True
    else:
        endpoint_1 = request["subject"]["metal"]
        endpoint_2 = request["subject"]["donor"]
        relation_type = "METAL_COORDINATION"
        topology_effect = bool(
            request["evidence"]["definition"]["topology_effect"][
                "promote_nonstandard_to_linked"
            ]
        )
    if decision_name == "CONFIRM":
        return (
            _relation_from_pair(
                relation_type,
                endpoint_1,
                endpoint_2,
                "CONFIRMED_BY_USER",
                topology_effect,
            ),
            None,
        )
    if decision_name == "REJECT":
        return (
            None,
            _relation_from_pair(
                relation_type,
                endpoint_1,
                endpoint_2,
                "REJECTED_BY_USER",
                False,
            ),
        )
    return None, None


def _classification_decision_map(
    resolved_requests: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[tuple[str | None, str, str | None, str], dict[str, Any]]:
    output: dict[tuple[str | None, str, str | None, str], dict[str, Any]] = {}
    for request, decision in resolved_requests:
        if request["request_type"] not in CLASSIFICATION_REQUEST_TYPES:
            continue
        if decision.get("decision") != "SET_CLASSIFICATION":
            continue
        classification = decision.get("classification")
        if not isinstance(classification, dict):
            raise ClassificationToolError(
                "SET_CLASSIFICATION decision requires a classification mapping"
            )
        polymer_class = classification.get("polymer_class")
        topology_class = classification.get("topology_class")
        if polymer_class not in {"POLYMER", "BRANCHED", "NONPOLYMER", "WATER"}:
            raise ClassificationToolError("invalid polymer_class in decision")
        if topology_class not in {
            "STANDARD_RESIDUE",
            "COVALENTLY_LINKED_NONSTANDARD",
            "INDEPENDENT_NONSTANDARD",
            "SOLVENT_COMPONENT",
            "ION_COMPONENT",
        }:
            raise ClassificationToolError("invalid topology_class in decision")
        subject = request["subject"]
        source_resid = subject.get("source_resid")
        if not isinstance(source_resid, dict):
            raise ClassificationToolError(
                "classification decision subject lacks source_resid"
            )
        key = (
            subject.get("source_chain_id"),
            str(source_resid["number"]),
            source_resid.get("insertion_code"),
            subject["residue_name"],
        )
        output[key] = {
            "polymer_class": polymer_class,
            "topology_class": topology_class,
            "resolution_status": "RESOLVED",
            "evidence": ["user classification decision"],
        }
    return output


def _record_index(
    records: list[dict[str, Any]],
) -> dict[tuple[str | None, str, str | None, str], dict[str, Any]]:
    return {_natural_key(record): record for record in records}


def _baseline_group_map(groups: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(group["chain_index"]): group for group in groups}


def _inferred_group_classification(group: dict[str, Any]) -> tuple[str, str]:
    group_type = group["group_type"]
    if group_type == "SOLVENT_GROUP":
        return "WATER", "SOLVENT_COMPONENT"
    if group_type == "ION_GROUP":
        return "NONPOLYMER", "ION_COMPONENT"
    return "NONPOLYMER", "INDEPENDENT_NONSTANDARD"


def _special_record_from_endpoint(
    endpoint: dict[str, Any],
    baseline_group: dict[str, Any],
) -> dict[str, Any]:
    polymer_class, topology_class = _inferred_group_classification(baseline_group)
    return {
        "chain_index": int(endpoint["chain_index"]),
        "source_chain_id": endpoint.get("source_chain_id"),
        "source_resid": copy.deepcopy(endpoint["source_resid"]),
        "residue_name": endpoint["residue_name"],
        "presence_status": "OBSERVED",
        "sequence_position": None,
        "classification": {
            "polymer_class": polymer_class,
            "topology_class": topology_class,
            "resolution_status": "RESOLVED",
            "evidence": ["classification inherited from baseline grouped component"],
        },
        "conformation": {"status": "SINGLE_CONFORMATION", "altloc_ids": []},
        "heavy_atom_check": {
            "status": "NOT_PERFORMED",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": "GROUP_MEMBER_DETAIL_NOT_RETAINED_IN_BASELINE",
        },
    }


def _convert_baseline_record(
    record: dict[str, Any],
    classification_decisions: dict[tuple, dict[str, Any]],
) -> dict[str, Any]:
    key = _natural_key(record)
    observed = record["classification_observation"]
    decision = classification_decisions.get(key)
    if decision is not None:
        classification = copy.deepcopy(decision)
    elif observed["resolution_status"] == "RESOLVED":
        classification = {
            "polymer_class": observed["polymer_class"],
            "topology_class": observed["topology_class"],
            "resolution_status": "RESOLVED",
            "evidence": copy.deepcopy(observed.get("evidence", [])),
        }
    else:
        classification = {
            "polymer_class": None,
            "topology_class": None,
            "resolution_status": "PENDING_CONFIRMATION",
            "evidence": copy.deepcopy(observed.get("evidence", [])),
        }
    return {
        "chain_index": int(record["chain_index"]),
        "source_chain_id": record.get("source_chain_id"),
        "source_resid": copy.deepcopy(record["source_resid"]),
        "residue_name": record["residue_name"],
        "presence_status": record["presence_status"],
        "sequence_position": record.get("sequence_position"),
        "classification": classification,
        "conformation": copy.deepcopy(record["conformation_observation"]),
        "heavy_atom_check": copy.deepcopy(record["heavy_atom_check"]),
    }


def _relation_components(
    relations: list[dict[str, Any]],
) -> tuple[list[set[tuple]], dict[tuple, dict[str, Any]]]:
    union_find = UnionFind()
    endpoints: dict[tuple, dict[str, Any]] = {}
    for relation in relations:
        if not relation["topology_effect_applied"]:
            continue
        first = relation["endpoint_1"]
        second = relation["endpoint_2"]
        first_key = _endpoint_key(first)
        second_key = _endpoint_key(second)
        endpoints[first_key] = first
        endpoints[second_key] = second
        union_find.union(first_key, second_key)
    return union_find.components(), endpoints


def _integrate_chain_groups_and_records(
    observations: dict[str, Any],
    records: list[dict[str, Any]],
    confirmed_relations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple, int]]:
    baseline_groups = copy.deepcopy(observations["chain_groups"])
    group_by_index = _baseline_group_map(baseline_groups)
    record_by_key = _record_index(records)
    components, endpoint_lookup = _relation_components(confirmed_relations)

    endpoint_final_chain: dict[tuple, int] = {}
    special_component_specs: list[dict[str, Any]] = []
    decrement_by_group: defaultdict[int, int] = defaultdict(int)
    polymer_indices = {
        index
        for index, group in group_by_index.items()
        if group["group_type"] in {"POLYMER_CHAIN", "BRANCHED_CHAIN"}
    }

    for component in components:
        natural_keys = {_natural_key(endpoint_lookup[key]) for key in component}
        involved_baseline_indices = {
            int(endpoint_lookup[key]["chain_index"]) for key in component
        }
        connected_polymer_indices = sorted(
            index for index in involved_baseline_indices if index in polymer_indices
        )
        nonpoly_natural_keys = {
            key
            for key in natural_keys
            if int(
                next(
                    endpoint_lookup[endpoint_key]["chain_index"]
                    for endpoint_key in component
                    if _natural_key(endpoint_lookup[endpoint_key]) == key
                )
            )
            not in polymer_indices
        }
        if not nonpoly_natural_keys:
            continue
        if len(connected_polymer_indices) == 1:
            target = connected_polymer_indices[0]
            for key in nonpoly_natural_keys:
                endpoint_final_chain[key] = target
        else:
            group_type = (
                "MULTICHAIN_LINKED_COMPONENT"
                if len(connected_polymer_indices) > 1
                else "LINKED_NONSTANDARD_GROUP"
            )
            baseline_order = min(involved_baseline_indices)
            special_component_specs.append(
                {
                    "natural_keys": nonpoly_natural_keys,
                    "group_type": group_type,
                    "linked_polymer_chain_indices": connected_polymer_indices,
                    "baseline_order": baseline_order,
                }
            )
        for key in nonpoly_natural_keys:
            if key not in record_by_key:
                endpoint = next(
                    endpoint_lookup[endpoint_key]
                    for endpoint_key in component
                    if _natural_key(endpoint_lookup[endpoint_key]) == key
                )
                baseline_group = group_by_index[int(endpoint["chain_index"])]
                record = _special_record_from_endpoint(endpoint, baseline_group)
                records.append(record)
                record_by_key[key] = record
                decrement_by_group[int(endpoint["chain_index"])] += 1

    max_polymer_index = max(polymer_indices, default=0)
    next_index = max_polymer_index + 1
    final_groups: list[dict[str, Any]] = []
    for index in sorted(polymer_indices):
        group = copy.deepcopy(group_by_index[index])
        group["grouping_status"] = "FINAL"
        group["linked_polymer_chain_indices"] = []
        final_groups.append(group)

    for spec in sorted(
        special_component_specs,
        key=lambda item: (item["baseline_order"], sorted(item["natural_keys"])),
    ):
        index = next_index
        next_index += 1
        for key in spec["natural_keys"]:
            endpoint_final_chain[key] = index
        residue_names = {key[3] for key in spec["natural_keys"]}
        final_groups.append(
            {
                "chain_index": index,
                "grouping_status": "FINAL",
                "group_type": spec["group_type"],
                "source_chain_id": None,
                "entity_id": None,
                "residue_name": next(iter(residue_names)) if len(residue_names) == 1 else "MIXED",
                "instance_count": len(spec["natural_keys"]),
                "linked_polymer_chain_indices": spec["linked_polymer_chain_indices"],
                "source_associations": [],
            }
        )

    moved_keys = set(endpoint_final_chain)
    individual_group_keys = {
        int(record["chain_index"]): key
        for key, record in record_by_key.items()
    }
    for baseline_index, baseline_group in sorted(group_by_index.items()):
        if baseline_index in polymer_indices:
            continue
        count = int(baseline_group["instance_count"]) - decrement_by_group[baseline_index]
        individual_key = individual_group_keys.get(baseline_index)
        if individual_key in moved_keys:
            count = 0
        if count <= 0:
            continue
        group = copy.deepcopy(baseline_group)
        group["chain_index"] = next_index
        next_index += 1
        group["grouping_status"] = "FINAL"
        group["instance_count"] = count
        group["linked_polymer_chain_indices"] = []
        final_groups.append(group)
        for record in records:
            if int(record["chain_index"]) == baseline_index and _natural_key(record) not in moved_keys:
                endpoint_final_chain[_natural_key(record)] = int(group["chain_index"])

    for record in records:
        key = _natural_key(record)
        if key in endpoint_final_chain:
            record["chain_index"] = endpoint_final_chain[key]

    for relation in confirmed_relations:
        for endpoint_field in ("endpoint_1", "endpoint_2"):
            endpoint = relation[endpoint_field]
            key = _natural_key(endpoint)
            if key in endpoint_final_chain:
                endpoint["chain_index"] = endpoint_final_chain[key]

    topology_forming_keys = {
        _natural_key(relation[endpoint_field])
        for relation in confirmed_relations
        if relation["topology_effect_applied"]
        for endpoint_field in ("endpoint_1", "endpoint_2")
    }
    for record in records:
        key = _natural_key(record)
        classification = record["classification"]
        if key not in topology_forming_keys or classification["resolution_status"] != "RESOLVED":
            continue
        if classification["topology_class"] != "STANDARD_RESIDUE":
            classification["topology_class"] = "COVALENTLY_LINKED_NONSTANDARD"
            if classification["polymer_class"] == "WATER":
                classification["polymer_class"] = "NONPOLYMER"
            classification["evidence"].append(
                "confirmed topology-forming covalent or metal-coordination relation"
            )

    records.sort(
        key=lambda item: (
            int(item["chain_index"]),
            str(item.get("source_chain_id")),
            str(item["source_resid"]["number"]),
            str(item["source_resid"].get("insertion_code")),
            item["residue_name"],
        )
    )
    final_groups.sort(key=lambda item: int(item["chain_index"]))
    return final_groups, records, endpoint_final_chain


def _render_report(result: dict[str, Any], confirmation: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Component and residue classification report",
        "",
        f"- Result status: `{result['result_status']}`",
        f"- Selected model: `{result['selected_model_id']}`",
        f"- Classification mode: `{result['classification_mode']}`",
        f"- Chain groups: {summary['chain_group_count']}",
        f"- Pending confirmation items: {summary['unresolved_item_count']}",
        "",
        "## Chain groups",
        "",
        "| chain_index | group_type | residue_name | instances | linked polymer chains |",
        "|---:|---|---|---:|---|",
    ]
    for group in result["chain_groups"]:
        linked = ", ".join(str(value) for value in group["linked_polymer_chain_indices"]) or "—"
        lines.append(
            f"| {group['chain_index']} | {group['group_type']} | {group.get('residue_name', '—')} | "
            f"{group['instance_count']} | {linked} |"
        )
    lines.extend(["", "## Classification summary", ""])
    for key in (
        "standard_residue_count",
        "covalently_linked_nonstandard_count",
        "independent_nonstandard_count",
        "solvent_component_count",
        "ion_component_count",
        "missing_residue_count",
        "multiple_conformation_residue_count",
        "heavy_atom_issue_count",
    ):
        lines.append(f"- `{key}`: {summary[key]}")
    lines.extend(["", "## Confirmed relations", ""])
    lines.append(
        f"- Covalent connections: {len(result['confirmed_relations']['covalent_connections'])}"
    )
    lines.append(
        f"- Metal coordination relations: {len(result['confirmed_relations']['metal_coordination'])}"
    )
    lines.extend(["", "## Pending confirmations", ""])
    if not confirmation["requests"]:
        lines.append("None.")
    else:
        for request in confirmation["requests"]:
            lines.append(
                f"- {request['request_index']}. `{request['request_type']}` — {request['reason']}"
            )
    lines.append("")
    return "\n".join(lines)


def build(config: dict[str, Any], script_dir: Path) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Path]]:
    schema_dir = script_dir.parent / "schemas"
    model_scope, model_scope_path, model_scope_hash = _load_validated(
        config,
        "model_scope",
        schema_dir / "model_scope.schema.yaml",
    )
    observations, observations_path, observations_hash = _load_validated(
        config,
        "classification_observations",
        schema_dir / "classification_observations.schema.yaml",
    )
    manifest, manifest_path, manifest_hash = _load_validated(
        config,
        "reference_manifest",
        schema_dir / "reference_manifest.schema.yaml",
    )
    connections, connections_path, connections_hash = _load_validated(
        config,
        "possible_connections_result",
        schema_dir / "possible_connections_result.schema.yaml",
    )
    coordination, coordination_path, coordination_hash = _load_validated(
        config,
        "possible_coordination_result",
        schema_dir / "possible_coordination_result.schema.yaml",
    )

    selected_model_id = model_scope["selection"]["selected_model_id"]
    if selected_model_id is None:
        raise ClassificationToolError("model scope is unresolved")
    if str(observations["input"]["selected_model_id"]) != str(selected_model_id):
        raise ClassificationToolError("model scope and observations selected model differ")
    structure_hash = observations["input"]["structure_sha256"]
    if model_scope["input_structure"]["sha256"] != structure_hash:
        raise ClassificationToolError("model scope and observations structure hashes differ")
    if manifest["classification_mode"] != observations["input"]["classification_mode"]:
        raise ClassificationToolError("manifest and observations classification modes differ")
    for relation_document, label in (
        (connections, "connections"),
        (coordination, "coordination"),
    ):
        relation_input = relation_document["input"]
        if relation_input["structure_sha256"] != structure_hash:
            raise ClassificationToolError(f"{label} result structure hash differs")
        if relation_input["observations_sha256"] != observations_hash:
            raise ClassificationToolError(f"{label} result references a different observations file")
        if str(relation_input["selected_model_id"]) != str(selected_model_id):
            raise ClassificationToolError(f"{label} result selected model differs")

    raw_requests: list[dict[str, Any]] = [
        *(_unresolved_to_request(item) for item in observations["unresolved_observations"]),
        *(_connection_requests(connections)),
        *(_coordination_requests(coordination)),
    ]
    issue_subject_keys = {
        (
            item["subject"].get("source_chain_id"),
            json.dumps(item["subject"].get("source_resid"), sort_keys=True),
            item["subject"].get("residue_name"),
        )
        for item in observations["unresolved_observations"]
        if isinstance(item.get("subject"), dict)
    }
    for record in observations["residue_records"]:
        if record["classification_observation"]["resolution_status"] == "RESOLVED":
            continue
        key = (
            record.get("source_chain_id"),
            json.dumps(record["source_resid"], sort_keys=True),
            record["residue_name"],
        )
        if key not in issue_subject_keys:
            raw_requests.append(_classification_pending_request(record))
    raw_requests = _deduplicate_requests(raw_requests)

    confirmation_schema = schema_dir / "confirmation_requests.schema.yaml"
    decisions = _load_decisions(config, confirmation_schema)
    unresolved_requests: list[dict[str, Any]] = []
    resolved_requests: list[tuple[dict[str, Any], dict[str, Any]]] = []
    confirmed_relations = _explicit_relations(connections, coordination)
    rejected_relations: list[dict[str, Any]] = []
    for request in raw_requests:
        decision = decisions.get(_request_fingerprint(request))
        if decision is None:
            unresolved_requests.append(request)
            continue
        if request["request_type"] in RELATION_REQUEST_TYPES:
            confirmed, rejected = _decision_relation(request, decision)
            if confirmed is not None:
                confirmed_relations.append(confirmed)
            if rejected is not None:
                rejected_relations.append(rejected)
            if confirmed is None and rejected is None:
                unresolved_requests.append(request)
            else:
                resolved_requests.append((request, decision))
            continue
        if request["request_type"] in CLASSIFICATION_REQUEST_TYPES and decision["decision"] == "SET_CLASSIFICATION":
            resolved_requests.append((request, decision))
            continue
        if decision["decision"] == "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES":
            resolved_requests.append((request, decision))
            continue
        unresolved_requests.append(request)

    for index, request in enumerate(unresolved_requests, start=1):
        request["request_index"] = index
    confirmation = {
        "schema_version": "1.0",
        "status": (
            "USER_CONFIRMATION_REQUIRED"
            if unresolved_requests
            else "NO_CONFIRMATION_REQUIRED"
        ),
        "requests": unresolved_requests,
    }
    validate_document(confirmation, confirmation_schema)

    classification_decisions = _classification_decision_map(resolved_requests)
    records = [
        _convert_baseline_record(record, classification_decisions)
        for record in observations["residue_records"]
    ]
    final_groups, records, endpoint_final_chain = _integrate_chain_groups_and_records(
        observations,
        records,
        confirmed_relations,
    )

    output = _required_mapping(config, "output")
    confirmation_path = _required_path(output, "confirmation_requests_path")
    result_path = _required_path(output, "classification_result_path")
    report_path = _required_path(output, "classification_report_path")
    result_schema = Path(
        output.get("classification_result_schema", schema_dir / "classification_result.schema.yaml")
    ).resolve()
    atomic_write_yaml(confirmation_path, confirmation)
    confirmation_hash = sha256_file(confirmation_path)

    standard_count = sum(
        record["classification"]["topology_class"] == "STANDARD_RESIDUE"
        for record in records
    )
    linked_count = sum(
        record["classification"]["topology_class"]
        == "COVALENTLY_LINKED_NONSTANDARD"
        for record in records
    )
    independent_count = sum(
        record["classification"]["topology_class"] == "INDEPENDENT_NONSTANDARD"
        for record in records
    )
    solvent_count = sum(
        group["instance_count"]
        for group in final_groups
        if group["group_type"] == "SOLVENT_GROUP"
    ) + sum(
        record["classification"]["topology_class"] == "SOLVENT_COMPONENT"
        for record in records
    )
    ion_count = sum(
        group["instance_count"]
        for group in final_groups
        if group["group_type"] == "ION_GROUP"
    ) + sum(
        record["classification"]["topology_class"] == "ION_COMPONENT"
        for record in records
    )
    heavy_issue_statuses = {
        "MISSING_EXPECTED_HEAVY_ATOMS",
        "UNEXPECTED_HEAVY_ATOMS",
        "MISSING_AND_UNEXPECTED_HEAVY_ATOMS",
        "ATOM_NAME_MAPPING_REQUIRED",
        "REFERENCE_TEMPLATE_UNAVAILABLE",
    }
    result = {
        "schema_version": "1.0",
        "result_status": (
            "PENDING_USER_CONFIRMATION" if unresolved_requests else "COMPLETE"
        ),
        "selected_model_id": str(selected_model_id),
        "classification_mode": observations["input"]["classification_mode"],
        "source_hashes": {
            "model_scope": model_scope_hash,
            "classification_observations": observations_hash,
            "reference_manifest": manifest_hash,
            "possible_connections_result": connections_hash,
            "possible_coordination_result": coordination_hash,
            "confirmation_requests": confirmation_hash,
        },
        "chain_groups": final_groups,
        "residue_records": records,
        "confirmed_relations": {
            "covalent_connections": [
                relation
                for relation in confirmed_relations
                if relation["relation_type"] == "COVALENT_CONNECTION"
            ],
            "metal_coordination": [
                relation
                for relation in confirmed_relations
                if relation["relation_type"] == "METAL_COORDINATION"
            ],
        },
        "rejected_candidates": {
            "covalent_connections": [
                relation
                for relation in rejected_relations
                if relation["relation_type"] == "COVALENT_CONNECTION"
            ],
            "metal_coordination": [
                relation
                for relation in rejected_relations
                if relation["relation_type"] == "METAL_COORDINATION"
            ],
        },
        "unresolved_items": [
            {
                "request_index": request["request_index"],
                "request_type": request["request_type"],
                "subject": copy.deepcopy(request["subject"]),
            }
            for request in unresolved_requests
        ],
        "summary": {
            "chain_group_count": len(final_groups),
            "standard_residue_count": standard_count,
            "covalently_linked_nonstandard_count": linked_count,
            "independent_nonstandard_count": independent_count,
            "solvent_component_count": solvent_count,
            "ion_component_count": ion_count,
            "multiple_conformation_residue_count": sum(
                record["conformation"]["status"] == "MULTIPLE_CONFORMATIONS"
                for record in records
            ),
            "missing_residue_count": sum(
                record["presence_status"] == "MISSING_EXPECTED"
                for record in records
            ),
            "heavy_atom_issue_count": sum(
                record["heavy_atom_check"]["status"] in heavy_issue_statuses
                for record in records
            ),
            "unresolved_item_count": len(unresolved_requests),
        },
    }
    validate_document(result, result_schema)
    report = _render_report(result, confirmation)
    return result, confirmation, report, {
        "result": result_path,
        "confirmation": confirmation_path,
        "report": report_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    try:
        config = read_yaml_strict(args.config.resolve())
        if not isinstance(config, dict):
            raise ClassificationToolError("config must be a YAML mapping")
        result, _confirmation, report, paths = build(config, script_dir)
        atomic_write_yaml(paths["result"], result)
        report_path = paths["report"]
        if report_path.exists():
            if report_path.is_symlink() or not report_path.is_file():
                raise ClassificationToolError(
                    f"classification report path is not a regular file: {report_path}"
                )
            existing = report_path.read_text(encoding="utf-8")
            if existing != report:
                raise ClassificationToolError(
                    f"refusing to overwrite different existing report: {report_path}"
                )
        else:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = report_path.with_name(report_path.name + ".tmp")
            temporary.write_text(report, encoding="utf-8")
            temporary.replace(report_path)
        return 0
    except ClassificationToolError as exc:
        print(f"build_classification_result.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"build_classification_result.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

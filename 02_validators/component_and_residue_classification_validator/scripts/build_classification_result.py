#!/usr/bin/env python3
"""Integrate classification observations, relationship checks and prior decisions."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationError,
    atomic_text,
    atomic_yaml,
    canonical_locator_key,
    load_yaml,
    require_hash,
    sha256,
    validate_document,
)

VERSION = "1.0.0"


def _load_input(config: dict[str, Any], key: str, label: str) -> tuple[Path, str, dict[str, Any]]:
    item = config[key]
    path = Path(item["path"])
    actual_hash = require_hash(path, item.get("sha256"), label)
    document = load_yaml(path)
    if not isinstance(document, dict):
        raise ClassificationError(f"{label} must be a mapping")
    return path, actual_hash, document


def _locator_key(locator: dict[str, Any]) -> tuple[Any, ...]:
    return canonical_locator_key(locator, include_atom=False)


def _request_signature(request: dict[str, Any]) -> str:
    payload = {key: value for key, value in request.items() if key != "request_index"}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _allowed_decisions(request_type: str) -> list[str]:
    if request_type in {
        "GEOMETRY_SUPPORTED_CANDIDATE",
        "CONNECTION_DEFINITION_CONFLICT",
        "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
        "COORDINATION_DEFINITION_CONFLICT",
    }:
        return ["CONFIRM", "REJECT"]
    if request_type == "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE":
        return [
            "PROVIDE_SOURCE_RESID",
            "PROVIDE_NUMBERING_MAPPING",
            "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES",
        ]
    if request_type == "MISSING_RESIDUE_CHAIN_UNRESOLVED":
        return [
            "ASSIGN_CHAIN_INDEX",
            "PROVIDE_CHAIN_MAPPING",
            "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES",
        ]
    if "CLASSIFICATION_CONFLICT" in request_type or request_type == "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE":
        return ["PROVIDE_CLASSIFICATION_OR_TEMPLATE_SELECTION"]
    if request_type == "MULTIPLE_LOCAL_CCD_CANDIDATES":
        return ["SELECT_CCD_CANDIDATE", "PROVIDE_CORRECTED_CCD"]
    if request_type == "AF3_SEQUENCE_CHAIN_MAPPING_CONFLICT":
        return ["PROVIDE_CHAIN_MAPPING", "PROVIDE_CORRECTED_SEQUENCE_REFERENCE"]
    return ["PROVIDE_RESOLUTION"]


def _build_requests(
    observations: dict[str, Any],
    connections: dict[str, Any],
    coordination: dict[str, Any],
) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for item in observations.get("unresolved_observations", []):
        if item.get("resolution_status") != "PENDING_CONFIRMATION":
            continue
        request_type = item.get("issue_type", "CLASSIFICATION_ISSUE")
        requests.append(
            {
                "request_type": request_type,
                "source": "classification_observations",
                "subject": copy.deepcopy(item),
                "allowed_decisions": _allowed_decisions(request_type),
            }
        )
    for source_name, document, pair_key_name in (
        ("possible_connections_result", connections, "pair_results"),
        ("possible_coordination_result", coordination, "pair_results"),
    ):
        for definition in document.get("definition_results", []):
            for pair in definition.get(pair_key_name, []):
                if not pair.get("confirmation_required"):
                    continue
                request_type = pair["status"]
                requests.append(
                    {
                        "request_type": request_type,
                        "source": source_name,
                        "definition_index": definition["definition_index"],
                        "label": definition.get("label"),
                        "subject": copy.deepcopy(pair),
                        "allowed_decisions": _allowed_decisions(request_type),
                    }
                )
    for index, request in enumerate(requests, start=1):
        request["request_index"] = index
    return requests


def _load_decisions(entries: list[dict[str, Any]]) -> dict[str, Any]:
    decisions: dict[str, Any] = {}
    loaded_files: dict[Path, tuple[str, dict[str, Any]]] = {}
    for entry in entries:
        confirmation_path = Path(entry["confirmation_file"])
        expected_hash = entry.get("confirmation_file_sha256")
        if confirmation_path not in loaded_files:
            actual_hash = require_hash(confirmation_path, expected_hash, "prior confirmation file")
            document = load_yaml(confirmation_path)
            loaded_files[confirmation_path] = (actual_hash, document)
        actual_hash, document = loaded_files[confirmation_path]
        if expected_hash and actual_hash != expected_hash:
            raise ClassificationError("prior confirmation hash mismatch")
        index = int(entry["request_index"])
        matches = [request for request in document.get("requests", []) if request.get("request_index") == index]
        if len(matches) != 1:
            raise ClassificationError(
                f"decision cannot locate request {index} in {confirmation_path}"
            )
        decisions[_request_signature(matches[0])] = entry.get("decision")
    return decisions


def _request_relation_key(request: dict[str, Any]) -> tuple[Any, ...] | None:
    subject = request.get("subject", {})
    if "partner_1" in subject:
        return (
            "COVALENT_CONNECTION",
            _locator_key(subject["partner_1"]),
            _locator_key(subject["partner_2"]),
        )
    if "metal" in subject:
        return (
            "METAL_COORDINATION",
            _locator_key(subject["metal"]),
            _locator_key(subject["donor"]),
        )
    return None


def _relation_record(
    relation_type: str,
    pair: dict[str, Any],
    source_status: str,
    definition_index: int,
    label: str | None,
    topology_forming: bool,
) -> dict[str, Any]:
    if relation_type == "COVALENT_CONNECTION":
        endpoints = {"partner_1": pair["partner_1"], "partner_2": pair["partner_2"]}
    else:
        endpoints = {"metal": pair["metal"], "donor": pair["donor"]}
    return {
        "relation_type": relation_type,
        "source_status": source_status,
        "definition_index": definition_index,
        "label": label,
        **endpoints,
        "geometry": pair.get("geometry"),
        "topology_forming": topology_forming,
    }


def _base_confirmed_relations(
    connections: dict[str, Any], coordination: dict[str, Any]
) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for definition in connections.get("definition_results", []):
        for pair in definition.get("pair_results", []):
            if pair.get("status") == "CONFIRMED_BY_STRUCTURE":
                relations.append(
                    _relation_record(
                        "COVALENT_CONNECTION",
                        pair,
                        pair["status"],
                        definition["definition_index"],
                        definition.get("label"),
                        True,
                    )
                )
    for definition in coordination.get("definition_results", []):
        promote = bool(
            definition.get("definition", {})
            .get("topology_effect", {})
            .get("promote_nonstandard_to_linked", False)
        )
        for pair in definition.get("pair_results", []):
            if pair.get("status") == "CONFIRMED_BY_STRUCTURE":
                relations.append(
                    _relation_record(
                        "METAL_COORDINATION",
                        pair,
                        pair["status"],
                        definition["definition_index"],
                        definition.get("label"),
                        promote,
                    )
                )
    return relations


def _resolved_requests(
    requests: list[dict[str, Any]], decisions: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    remaining: list[dict[str, Any]] = []
    confirmed: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    nonrelation_decisions: dict[str, Any] = {}
    for request in requests:
        decision = decisions.get(_request_signature(request))
        if decision is None:
            remaining.append(request)
            continue
        relation_key = _request_relation_key(request)
        if relation_key is not None:
            if decision == "CONFIRM":
                source = request["source"]
                pair = request["subject"]
                if source == "possible_connections_result":
                    confirmed.append(
                        _relation_record(
                            "COVALENT_CONNECTION",
                            pair,
                            "USER_CONFIRMED",
                            request["definition_index"],
                            request.get("label"),
                            True,
                        )
                    )
                else:
                    promote = bool(
                        pair.get("topology_effect_evaluation", {}).get(
                            "promote_nonstandard_to_linked", False
                        )
                    )
                    confirmed.append(
                        _relation_record(
                            "METAL_COORDINATION",
                            pair,
                            "USER_CONFIRMED",
                            request["definition_index"],
                            request.get("label"),
                            promote,
                        )
                    )
            elif decision == "REJECT":
                rejected.append(
                    {
                        "request_type": request["request_type"],
                        "source": request["source"],
                        "definition_index": request.get("definition_index"),
                        "label": request.get("label"),
                        "subject": request["subject"],
                    }
                )
            else:
                raise ClassificationError(
                    f"relation decision must be CONFIRM or REJECT: {decision!r}"
                )
        else:
            nonrelation_decisions[_request_signature(request)] = decision
    return remaining, confirmed, rejected, nonrelation_decisions


def _record_map(observations: dict[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {
        _locator_key(record): copy.deepcopy(record)
        for record in observations.get("residue_records", [])
    }


def _classification_from_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "polymer_class": group.get("polymer_class"),
        "topology_class": group.get("topology_class"),
        "resolution_status": "RESOLVED"
        if group.get("polymer_class") is not None and group.get("topology_class") is not None
        else "UNRESOLVED",
        "primary_source": "BASELINE_CHAIN_GROUP",
        "ccd_id": group.get("residue_name"),
        "evidence": ["aggregated baseline group"],
    }


def _ensure_endpoint_record(
    records: dict[tuple[Any, ...], dict[str, Any]],
    endpoint: dict[str, Any],
    baseline_groups: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    key = _locator_key(endpoint)
    if key in records:
        return records[key]
    group = baseline_groups.get(endpoint.get("chain_index"), {})
    record = {
        "chain_index": endpoint.get("chain_index"),
        "source_chain_id": endpoint.get("source_chain_id"),
        "source_resid": endpoint["source_resid"],
        "residue_name": endpoint["residue_name"],
        "presence_status": "OBSERVED",
        "source_order": endpoint.get("source_order"),
        "entity_id": None,
        "classification_observation": _classification_from_group(group),
        "conformation_observation": {
            "status": "MULTIPLE_CONFORMATIONS" if endpoint.get("altloc") else "SINGLE_CONFORMATION",
            "altloc_ids": [endpoint["altloc"]] if endpoint.get("altloc") else [],
        },
        "heavy_atom_check": {
            "status": "NOT_PERFORMED",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": "AGGREGATED_BASELINE_INSTANCE_EXTRACTED_BY_RELATION",
        },
    }
    records[key] = record
    return record


def _relation_endpoints(relation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if relation["relation_type"] == "COVALENT_CONNECTION":
        return relation["partner_1"], relation["partner_2"]
    return relation["metal"], relation["donor"]


def _apply_classification_promotions(
    records: dict[tuple[Any, ...], dict[str, Any]],
    baseline_groups: dict[int, dict[str, Any]],
    relations: list[dict[str, Any]],
) -> None:
    for relation in relations:
        if not relation.get("topology_forming"):
            continue
        for endpoint in _relation_endpoints(relation):
            record = _ensure_endpoint_record(records, endpoint, baseline_groups)
            classification = record["classification_observation"]
            if classification.get("resolution_status") != "RESOLVED":
                continue
            if classification.get("topology_class") == "STANDARD_RESIDUE":
                classification.setdefault("topology_relations", []).append(
                    {
                        "relation_type": relation["relation_type"],
                        "participates_in_topology_link": True,
                    }
                )
                continue
            if classification.get("polymer_class") == "WATER":
                classification.setdefault("warnings", []).append(
                    "topology-forming promotion not applied to WATER classification"
                )
                continue
            classification["topology_class"] = "COVALENTLY_LINKED_NONSTANDARD"
            classification["primary_source"] = "CONFIRMED_TOPOLOGY_FORMING_RELATION"
            classification.setdefault("evidence", []).append(relation["relation_type"])


def _build_final_groups(
    observations: dict[str, Any],
    records: dict[tuple[Any, ...], dict[str, Any]],
    relations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_groups = {group["chain_index"]: copy.deepcopy(group) for group in observations["chain_groups"]}
    polymer_groups = [
        copy.deepcopy(group)
        for group in observations["chain_groups"]
        if group["group_type"] in {"POLYMER_CHAIN", "BRANCHED_CHAIN"}
    ]
    polymer_indices = {group["chain_index"] for group in polymer_groups}

    graph: dict[tuple[Any, ...], set[tuple[Any, ...]]] = defaultdict(set)
    node_locator: dict[tuple[Any, ...], dict[str, Any]] = {}
    topology_relation_nodes: set[tuple[Any, ...]] = set()
    for relation in relations:
        if not relation.get("topology_forming"):
            continue
        left, right = _relation_endpoints(relation)
        left_key, right_key = _locator_key(left), _locator_key(right)
        graph[left_key].add(right_key)
        graph[right_key].add(left_key)
        node_locator[left_key] = left
        node_locator[right_key] = right
        topology_relation_nodes.update((left_key, right_key))

    components: list[set[tuple[Any, ...]]] = []
    visited: set[tuple[Any, ...]] = set()
    for node in sorted(topology_relation_nodes, key=repr):
        if node in visited:
            continue
        component: set[tuple[Any, ...]] = set()
        queue = deque([node])
        visited.add(node)
        while queue:
            current = queue.popleft()
            component.add(current)
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(component)

    moved_from_baseline: Counter[int] = Counter()
    final_assignment: dict[tuple[Any, ...], int | str] = {}
    independent_components: list[dict[str, Any]] = []
    for component in components:
        linked_polymer_indices: set[int] = set()
        nonstandard_nodes: list[tuple[Any, ...]] = []
        source_orders: list[int] = []
        for node in component:
            locator = node_locator[node]
            if locator.get("chain_index") in polymer_indices:
                record = records.get(node)
                if record and record["classification_observation"].get("topology_class") == "STANDARD_RESIDUE":
                    linked_polymer_indices.add(int(locator["chain_index"]))
                    continue
            nonstandard_nodes.append(node)
            if locator.get("source_order") is not None:
                source_orders.append(int(locator["source_order"]))
        if not nonstandard_nodes:
            continue
        if len(linked_polymer_indices) == 1:
            target = next(iter(linked_polymer_indices))
            for node in nonstandard_nodes:
                final_assignment[node] = target
                old = node_locator[node].get("chain_index")
                if isinstance(old, int) and old not in polymer_indices:
                    moved_from_baseline[old] += 1
        else:
            independent_components.append(
                {
                    "nodes": nonstandard_nodes,
                    "linked_polymer_chain_indices": sorted(linked_polymer_indices),
                    "first_source_order": min(source_orders) if source_orders else 10**12,
                    "group_type": "MULTICHAIN_LINKED_COMPONENT"
                    if len(linked_polymer_indices) > 1
                    else "LINKED_NONSTANDARD_GROUP",
                }
            )
            for node in nonstandard_nodes:
                final_assignment[node] = "NEW_COMPONENT"
                old = node_locator[node].get("chain_index")
                if isinstance(old, int) and old not in polymer_indices:
                    moved_from_baseline[old] += 1

    remaining_groups: list[dict[str, Any]] = []
    for group in observations["chain_groups"]:
        if group["chain_index"] in polymer_indices:
            continue
        remaining_count = int(group.get("instance_count", 0)) - moved_from_baseline[group["chain_index"]]
        if remaining_count <= 0:
            continue
        kept = copy.deepcopy(group)
        kept["instance_count"] = remaining_count
        remaining_groups.append(kept)

    new_group_specs = independent_components + [
        {
            "baseline_group": group,
            "first_source_order": group.get("first_source_order", 10**12),
            "group_type": group["group_type"],
        }
        for group in remaining_groups
    ]
    new_group_specs.sort(key=lambda item: (item["first_source_order"], item["group_type"]))
    next_index = max(polymer_indices, default=0) + 1
    old_to_new: dict[int, int] = {}
    component_index: dict[int, int] = {}
    final_groups = []
    for group in polymer_groups:
        group["grouping_status"] = "FINAL"
        final_groups.append(group)
    for spec in new_group_specs:
        if "baseline_group" in spec:
            group = copy.deepcopy(spec["baseline_group"])
            old_to_new[group["chain_index"]] = next_index
            group["chain_index"] = next_index
            group["grouping_status"] = "FINAL"
        else:
            group = {
                "chain_index": next_index,
                "group_type": spec["group_type"],
                "grouping_status": "FINAL",
                "instance_count": len(spec["nodes"]),
                "first_source_order": spec["first_source_order"],
                "linked_polymer_chain_indices": spec["linked_polymer_chain_indices"],
                "member_residues": [node_locator[node] for node in spec["nodes"]],
            }
            for node in spec["nodes"]:
                component_index[id(spec)] = next_index
                final_assignment[node] = next_index
        final_groups.append(group)
        next_index += 1

    for key, record in records.items():
        if key in final_assignment and isinstance(final_assignment[key], int):
            record["chain_index"] = final_assignment[key]
        elif record.get("chain_index") in old_to_new:
            record["chain_index"] = old_to_new[record["chain_index"]]
    return sorted(final_groups, key=lambda group: group["chain_index"])


def _render_report(
    model_scope: dict[str, Any],
    manifest: dict[str, Any],
    result: dict[str, Any],
    confirmations: dict[str, Any],
) -> str:
    lines = [
        "# 组分与残基分类报告",
        "",
        "## 输入与模式",
        "",
        f"- 结构：`{model_scope['input_structure']['path']}`",
        f"- SHA-256：`{model_scope['input_structure']['sha256']}`",
        f"- 选定 model：`{result['selected_model_id']}`",
        f"- 分类模式：`{result['classification_mode']}`",
        f"- 结果状态：`{result['result_status']}`",
        "",
        "## Chain groups",
        "",
        "| chain_index | group_type | source_chain_id | residue/group | count |",
        "|---:|---|---|---|---:|",
    ]
    for group in result["chain_groups"]:
        lines.append(
            f"| {group['chain_index']} | {group['group_type']} | {group.get('source_chain_id', '')} | "
            f"{group.get('residue_name', '')} | {group.get('instance_count', '')} |"
        )
    lines.extend(["", "## 分类摘要", ""])
    for key, value in result["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 缺失残基", ""])
    missing = [record for record in result["residue_records"] if record["presence_status"] == "MISSING_EXPECTED"]
    if not missing:
        lines.append("- 未记录明确缺失残基。")
    else:
        for record in missing:
            resid = record["source_resid"]
            lines.append(
                f"- chain_index {record['chain_index']} / {record['source_chain_id']} / "
                f"{record['residue_name']} {resid['number']}{resid.get('insertion_code') or ''}"
            )
    lines.extend(["", "## 重原子检查异常", ""])
    heavy_issues = [
        record for record in result["residue_records"]
        if record["heavy_atom_check"]["status"] not in {"HEAVY_ATOMS_COMPLETE", "NOT_PERFORMED", "NOT_APPLICABLE"}
    ]
    if not heavy_issues:
        lines.append("- 未记录重原子模板异常。")
    else:
        for record in heavy_issues:
            lines.append(
                f"- chain_index {record['chain_index']} / {record['residue_name']} "
                f"{record['source_resid']['number']}: {record['heavy_atom_check']['status']}"
            )
    lines.extend(["", "## 已确认关系", ""])
    if not result["confirmed_relations"]:
        lines.append("- 无。")
    else:
        for relation in result["confirmed_relations"]:
            lines.append(
                f"- {relation['relation_type']}（{relation['source_status']}，topology_forming={relation['topology_forming']}）"
            )
    lines.extend(["", "## 待用户确认", ""])
    if confirmations["status"] == "NO_CONFIRMATION_REQUIRED":
        lines.append("- 无。")
    else:
        for request in confirmations["requests"]:
            lines.append(f"- [{request['request_index']}] {request['request_type']}")
    lines.extend(["", "## 参考文件", ""])
    lines.append(f"- 项目残基定义：{manifest['project_files']['residue_definitions']['status']}")
    lines.append(f"- CCD component 数：{len(manifest.get('ccd_components', []))}")
    return "\n".join(lines) + "\n"


def build(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    _, model_scope_hash, model_scope = _load_input(config, "model_scope", "model scope")
    _, observations_hash, observations = _load_input(
        config, "classification_observations", "classification observations"
    )
    _, manifest_hash, manifest = _load_input(config, "reference_manifest", "reference manifest")
    _, connections_hash, connections = _load_input(
        config, "possible_connections_result", "possible connections result"
    )
    _, coordination_hash, coordination = _load_input(
        config, "possible_coordination_result", "possible coordination result"
    )

    selected_model_id = model_scope["selection"]["selected_model_id"]
    if selected_model_id is None:
        raise ClassificationError("model scope has no selected model")
    run_context = observations["run_context"]
    if str(run_context["selected_model_id"]) != str(selected_model_id):
        raise ClassificationError("model scope and observations selected model differ")
    structure_hash = model_scope["input_structure"]["sha256"]
    if run_context["input_structure_sha256"] != structure_hash:
        raise ClassificationError("model scope and observations structure hashes differ")
    for relation_doc, label in ((connections, "connections"), (coordination, "coordination")):
        if relation_doc.get("input", {}).get("structure_sha256") != structure_hash:
            raise ClassificationError(f"{label} result structure hash differs")
        if relation_doc.get("input", {}).get("observations_sha256") != observations_hash:
            raise ClassificationError(f"{label} result references another observations file")

    requests = _build_requests(observations, connections, coordination)
    prior_decisions = _load_decisions(config.get("decisions", []))
    remaining_requests, user_confirmed, rejected, nonrelation_decisions = _resolved_requests(
        requests, prior_decisions
    )

    # Non-relation decisions are intentionally conservative: remove only explicit exclusions.
    filtered_requests: list[dict[str, Any]] = []
    for request in remaining_requests:
        decision = nonrelation_decisions.get(_request_signature(request))
        if decision in {
            "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES",
            "PROVIDE_RESOLUTION",
        }:
            continue
        filtered_requests.append(request)
    remaining_requests = filtered_requests
    for index, request in enumerate(remaining_requests, start=1):
        request["request_index"] = index

    base_relations = _base_confirmed_relations(connections, coordination)
    confirmed_relations = base_relations + user_confirmed
    baseline_groups = {group["chain_index"]: group for group in observations["chain_groups"]}
    records = _record_map(observations)
    _apply_classification_promotions(records, baseline_groups, confirmed_relations)
    final_groups = _build_final_groups(observations, records, confirmed_relations)

    confirmations = {
        "schema_version": "1.0",
        "status": "USER_CONFIRMATION_REQUIRED"
        if remaining_requests
        else "NO_CONFIRMATION_REQUIRED",
        "requests": remaining_requests,
    }
    result_status = "PENDING_USER_CONFIRMATION" if remaining_requests else "COMPLETE"
    observation_record_list = sorted(
        records.values(),
        key=lambda record: (
            record.get("chain_index") if record.get("chain_index") is not None else 10**9,
            record.get("source_order") if record.get("source_order") is not None else 10**12,
            record["residue_name"],
        ),
    )
    record_list: list[dict[str, Any]] = []
    for source_record in observation_record_list:
        record = copy.deepcopy(source_record)
        record["classification"] = record.pop("classification_observation")
        record["conformation"] = record.pop("conformation_observation")
        record_list.append(record)
    topology_counts = Counter(
        record["classification"].get("topology_class") or "UNRESOLVED"
        for record in record_list
        if record["presence_status"] == "OBSERVED"
    )
    result = {
        "schema_version": "1.0",
        "tool": {"name": "build_classification_result", "version": VERSION},
        "result_status": result_status,
        "selected_model_id": str(selected_model_id),
        "classification_mode": run_context["classification_mode"],
        "input_provenance": {
            "model_scope_sha256": model_scope_hash,
            "classification_observations_sha256": observations_hash,
            "reference_manifest_sha256": manifest_hash,
            "possible_connections_result_sha256": connections_hash,
            "possible_coordination_result_sha256": coordination_hash,
        },
        "chain_groups": final_groups,
        "residue_records": record_list,
        "confirmed_relations": confirmed_relations,
        "rejected_candidates": rejected,
        "unresolved_items": remaining_requests,
        "summary": {
            "chain_group_count": len(final_groups),
            "recorded_observed_residue_count": sum(
                1 for record in record_list if record["presence_status"] == "OBSERVED"
            ),
            "missing_residue_count": sum(
                1 for record in record_list if record["presence_status"] == "MISSING_EXPECTED"
            ),
            "confirmed_relation_count": len(confirmed_relations),
            "rejected_candidate_count": len(rejected),
            "pending_confirmation_count": len(remaining_requests),
            "topology_class_counts": dict(sorted(topology_counts.items())),
            "multiple_conformation_residue_count": sum(
                1
                for record in record_list
                if record["conformation"]["status"] == "MULTIPLE_CONFORMATIONS"
            ),
            "heavy_atom_issue_count": sum(
                1
                for record in record_list
                if record["heavy_atom_check"]["status"]
                not in {"HEAVY_ATOMS_COMPLETE", "NOT_PERFORMED", "NOT_APPLICABLE"}
            ),
        },
    }
    report = _render_report(model_scope, manifest, result, confirmations)
    return confirmations, result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--confirmation-output", type=Path, required=True)
    parser.add_argument("--result-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--confirmation-schema", type=Path, required=True)
    parser.add_argument("--result-schema", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_yaml(args.config)
        confirmations, result, report = build(config)
        validate_document(confirmations, args.confirmation_schema)
        validate_document(result, args.result_schema)
        atomic_yaml(args.confirmation_output, confirmations)
        atomic_yaml(args.result_output, result)
        atomic_text(args.report_output, report)
    except (ClassificationError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

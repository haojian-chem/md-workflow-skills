#!/usr/bin/env python3
"""Current-state helpers shared by Skill 1.2 deterministic entry points."""
from __future__ import annotations

import copy
import fcntl
import hashlib
import os
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from classification_common import (
    ClassificationToolError,
    read_yaml_strict,
    sha256_file,
    yaml_text,
)


RELATION_ISSUES = {
    "COVALENT_CONNECTION": {
        "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE",
        "CONNECTION_DEFINITION_CONFLICT",
        "RELATION_DECISION_TARGET_NOT_FOUND",
    },
    "METAL_COORDINATION": {
        "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
        "COORDINATION_DEFINITION_CONFLICT",
        "RELATION_DECISION_TARGET_NOT_FOUND",
    },
}


def _source_key(value: dict[str, Any]) -> tuple[str | None, str, str | None, str]:
    identity = value.get("source_identity", value)
    resid = identity["source_resid"]
    return (
        identity.get("source_chain_id"),
        str(resid["number"]),
        resid.get("insertion_code"),
        identity["source_residue_name"],
    )


def _component_map(config: dict[str, Any], script_dir: Path) -> dict[str, str]:
    schema_dir = script_dir.parent / "schemas"
    reference_dir = script_dir.parent / "references"
    paths = [
        Path(config.get("classification", {}).get("standard_registry_path", reference_dir / "standard_residue_registry.yaml")),
        Path(config.get("classification", {}).get("linked_registry_path", reference_dir / "topology_linked_nonstandard_residue_registry.yaml")),
        Path(config.get("classification", {}).get("independent_registry_path", reference_dir / "independent_nonstandard_residue_registry.yaml")),
    ]
    project = config.get("project_residue_definitions")
    if isinstance(project, dict) and project.get("path"):
        paths.insert(0, Path(project["path"]))
    result: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_file():
            continue
        document = read_yaml_strict(resolved)
        for entry in document.get("residue_definitions", []) if isinstance(document, dict) else []:
            if isinstance(entry, dict) and isinstance(entry.get("residue_name"), str):
                result.setdefault(
                    entry["residue_name"],
                    str(entry.get("ccd_id", entry["residue_name"])),
                )
    return result


def _strip_legacy_heavy_fields(check: dict[str, Any]) -> None:
    check.pop("status", None)
    check.pop("missing_atoms", None)
    check.pop("unexpected_atoms", None)


def normalize_baseline_observations(
    observations: dict[str, Any],
    config: dict[str, Any],
    script_dir: Path,
) -> dict[str, Any]:
    output = copy.deepcopy(observations)
    component_by_name = _component_map(config, script_dir)
    for group in output.get("chain_groups", []):
        group.pop("grouping_status", None)
        group.setdefault("linked_polymer_chain_indices", [])
        group.setdefault("source_associations", [])
    output["baseline_chain_groups"] = copy.deepcopy(output.get("chain_groups", []))
    for record in output.get("residue_records", []):
        classification = record["classification_observation"]
        classification.setdefault(
            "component_id",
            component_by_name.get(record["residue_name"]),
        )
        record["baseline_chain_index"] = int(record["chain_index"])
        record["baseline_classification_observation"] = copy.deepcopy(classification)
        _strip_legacy_heavy_fields(record["heavy_atom_check"])
    missing_checks = output.get("missing_residue_checks", [])
    missing_status = (
        "NOT_PERFORMED"
        if missing_checks and all(item.get("status") == "NOT_PERFORMED" for item in missing_checks)
        else "COMPLETED"
    )
    output["completed_checks"] = {
        "baseline_classification": "COMPLETED",
        "possible_connections": "PENDING",
        "possible_coordination": "PENDING",
        "heavy_atom_check": "COMPLETED",
        "missing_residue_check": missing_status,
    }
    output["check_outputs"] = {
        "possible_connections": {"path": None, "sha256": None},
        "possible_coordination": {"path": None, "sha256": None},
    }
    output["connection_observations"] = []
    output["coordination_observations"] = []
    recompute_summary(output)
    return output


def load_relation_decisions(
    path: Path | None,
    observations: dict[str, Any],
    schema_path: Path,
    validate_document,
) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    document = read_yaml_strict(path)
    validate_document(document, schema_path)
    expected = observations["input"]
    structure = document["structure"]
    if (
        structure["structure_sha256"] != expected["structure_sha256"]
        or str(structure["selected_model_id"]) != str(expected["selected_model_id"])
    ):
        raise ClassificationToolError(
            "relation decisions do not match the observations structure and selected model"
        )
    result: dict[str, dict[str, Any]] = {}
    for item in document["decisions"]:
        relation_id = item["relation_id"]
        if relation_id in result:
            raise ClassificationToolError(f"duplicate relation decision: {relation_id}")
        expected_kind = relation_id.split("/type/", 1)[1].split("/", 1)[0]
        if item["relation_kind"] != expected_kind:
            raise ClassificationToolError(
                f"relation kind does not match relation ID: {relation_id}"
            )
        result[relation_id] = copy.deepcopy(item)
    return result


def _effective_relation_state(
    relation_kind: str,
    automatic_status: str,
    decision: dict[str, Any] | None,
    promote: bool,
) -> tuple[str, str, str]:
    confirmed_by_structure = automatic_status == "CONFIRMED_BY_STRUCTURE"
    candidate_status = {
        "COVALENT_CONNECTION": "GEOMETRY_SUPPORTED_CANDIDATE",
        "METAL_COORDINATION": "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
    }[relation_kind]
    conflict_status = {
        "COVALENT_CONNECTION": "CONNECTION_DEFINITION_CONFLICT",
        "METAL_COORDINATION": "COORDINATION_DEFINITION_CONFLICT",
    }[relation_kind]

    if confirmed_by_structure:
        if decision and decision["decision"] == "REJECTED":
            return "CONFLICT", "PENDING_CONFIRMATION", "BLOCKED"
        topology = "APPLIED" if promote else "NOT_APPLICABLE"
        return "CONFIRMED", "NOT_REQUIRED", topology
    if automatic_status in {candidate_status, conflict_status}:
        if decision and decision["decision"] == "CONFIRMED":
            topology = "APPLIED" if promote else "NOT_APPLICABLE"
            return "CONFIRMED", "CONFIRMED_BY_USER", topology
        if decision and decision["decision"] == "REJECTED":
            return "REJECTED", "REJECTED_BY_USER", "NOT_APPLIED"
        state = "CANDIDATE" if automatic_status == candidate_status else "CONFLICT"
        topology = "PENDING_CONFIRMATION" if state == "CANDIDATE" and promote else "BLOCKED"
        return state, "PENDING_CONFIRMATION", topology
    if decision and decision["decision"] == "CONFIRMED":
        return "CONFLICT", "PENDING_CONFIRMATION", "BLOCKED"
    if decision and decision["decision"] == "REJECTED":
        return "REJECTED", "REJECTED_BY_USER", "NOT_APPLIED"
    return "NOT_EVALUATED", "NOT_REQUIRED", "BLOCKED" if promote else "NOT_APPLICABLE"


def _relation_request_issue(
    relation_kind: str,
    observation: dict[str, Any],
) -> dict[str, Any] | None:
    if observation["confirmation_status"] != "PENDING_CONFIRMATION":
        return None
    if relation_kind == "COVALENT_CONNECTION":
        issue_type = (
            "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE"
            if observation["status"] == "CANDIDATE"
            else "CONNECTION_DEFINITION_CONFLICT"
        )
        subject = {
            "partner_1": copy.deepcopy(observation["partner_1"]),
            "partner_2": copy.deepcopy(observation["partner_2"]),
        }
    else:
        issue_type = (
            "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE"
            if observation["status"] == "CANDIDATE"
            else "COORDINATION_DEFINITION_CONFLICT"
        )
        subject = {
            "metal": copy.deepcopy(observation["metal"]),
            "donor": copy.deepcopy(observation["donor"]),
        }
    return {
        "issue_type": issue_type,
        "subject": {"relation_id": observation["relation_id"], **subject},
        "evidence": ["relation check requires a user decision"],
        "resolution_status": "PENDING_CONFIRMATION",
    }


def _relation_observations(
    result: dict[str, Any],
    relation_kind: str,
    decisions: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    matched: set[str] = set()
    issues: list[dict[str, Any]] = []
    for definition in result.get("definition_results", []):
        for pair in definition.get("pair_results", []):
            relation_id = pair["relation_id"]
            decision = decisions.get(relation_id)
            if decision and decision["relation_kind"] == relation_kind:
                matched.add(relation_id)
            automatic = pair["status"]
            ordinary_unsupported = automatic == "NOT_GEOMETRICALLY_SUPPORTED"
            if ordinary_unsupported and relation_id not in decisions:
                continue
            if relation_kind == "COVALENT_CONNECTION":
                promote = True
                status, confirmation, topology = _effective_relation_state(
                    relation_kind, automatic, decision, promote
                )
                observation = {
                    "relation_id": relation_id,
                    "partner_1": copy.deepcopy(pair["partner_1"]),
                    "partner_2": copy.deepcopy(pair["partner_2"]),
                    "status": status,
                    "confirmation_status": confirmation,
                    "topology_effect": {
                        "status": topology,
                        "promote_nonstandard_to_linked": True,
                    },
                }
            else:
                promote = bool(
                    pair["topology_effect_evaluation"]["promote_nonstandard_to_linked"]
                )
                status, confirmation, topology = _effective_relation_state(
                    relation_kind, automatic, decision, promote
                )
                observation = {
                    "relation_id": relation_id,
                    "metal": copy.deepcopy(pair["metal"]),
                    "donor": copy.deepcopy(pair["donor"]),
                    "status": status,
                    "confirmation_status": confirmation,
                    "topology_effect": {
                        "status": topology,
                        "promote_nonstandard_to_linked": promote,
                    },
                }
            output.append(observation)
            issue = _relation_request_issue(relation_kind, observation)
            if issue is not None:
                issues.append(issue)
    output.sort(key=lambda item: item["relation_id"])
    return output, matched, issues


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[tuple, tuple] = {}

    def find(self, value: tuple) -> tuple:
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, first: tuple, second: tuple) -> None:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root != second_root:
            self.parent[max(first_root, second_root)] = min(first_root, second_root)

    def components(self) -> list[set[tuple]]:
        grouped: dict[tuple, set[tuple]] = defaultdict(set)
        for value in self.parent:
            grouped[self.find(value)].add(value)
        return list(grouped.values())


def _confirmed_topology_relations(observations: dict[str, Any]) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for relation in observations.get("connection_observations", []):
        if relation["status"] == "CONFIRMED" and relation["topology_effect"]["status"] == "APPLIED":
            yield relation["partner_1"], relation["partner_2"]
    for relation in observations.get("coordination_observations", []):
        if relation["status"] == "CONFIRMED" and relation["topology_effect"]["status"] == "APPLIED":
            yield relation["metal"], relation["donor"]


def recompute_topology_state(observations: dict[str, Any]) -> None:
    records = observations["residue_records"]
    record_by_key = {_source_key(record): record for record in records}
    for record in records:
        record["chain_index"] = int(record["baseline_chain_index"])
        record["classification_observation"] = copy.deepcopy(
            record["baseline_classification_observation"]
        )
    baseline_groups = copy.deepcopy(observations["baseline_chain_groups"])
    group_by_index = {int(group["chain_index"]): group for group in baseline_groups}
    polymer_indices = {
        index
        for index, group in group_by_index.items()
        if group["group_type"] in {"POLYMER_CHAIN", "BRANCHED_CHAIN"}
    }

    union = _UnionFind()
    endpoints: dict[tuple, dict[str, Any]] = {}
    for first, second in _confirmed_topology_relations(observations):
        first_key, second_key = _source_key(first), _source_key(second)
        if first_key not in record_by_key or second_key not in record_by_key:
            continue
        endpoints[first_key] = first
        endpoints[second_key] = second
        union.union(first_key, second_key)

    moved_to: dict[tuple, int] = {}
    special_specs: list[dict[str, Any]] = []
    moved_count: defaultdict[int, int] = defaultdict(int)
    for component in union.components():
        baseline_indices = {
            int(record_by_key[key]["baseline_chain_index"])
            for key in component
        }
        connected_polymer = sorted(index for index in baseline_indices if index in polymer_indices)
        nonpoly = {
            key
            for key in component
            if int(record_by_key[key]["baseline_chain_index"]) not in polymer_indices
        }
        if not nonpoly:
            continue
        if len(connected_polymer) == 1:
            for key in nonpoly:
                moved_to[key] = connected_polymer[0]
        else:
            special_specs.append(
                {
                    "keys": nonpoly,
                    "group_type": (
                        "MULTICHAIN_LINKED_COMPONENT"
                        if len(connected_polymer) > 1
                        else "LINKED_NONSTANDARD_GROUP"
                    ),
                    "linked": connected_polymer,
                    "order": min(baseline_indices),
                }
            )
        for key in nonpoly:
            moved_count[int(record_by_key[key]["baseline_chain_index"])] += 1

    next_index = max(polymer_indices, default=0) + 1
    current_groups: list[dict[str, Any]] = []
    for index in sorted(polymer_indices):
        group = copy.deepcopy(group_by_index[index])
        group["linked_polymer_chain_indices"] = []
        current_groups.append(group)
    for spec in sorted(special_specs, key=lambda item: (item["order"], sorted(item["keys"]))):
        index = next_index
        next_index += 1
        for key in spec["keys"]:
            moved_to[key] = index
        names = {key[3] for key in spec["keys"]}
        current_groups.append(
            {
                "chain_index": index,
                "group_type": spec["group_type"],
                "source_chain_id": None,
                "entity_id": None,
                "residue_name": next(iter(names)) if len(names) == 1 else "MIXED",
                "instance_count": len(spec["keys"]),
                "linked_polymer_chain_indices": spec["linked"],
                "source_associations": [],
            }
        )
    for baseline_index, baseline_group in sorted(group_by_index.items()):
        if baseline_index in polymer_indices:
            continue
        remaining = int(baseline_group["instance_count"]) - moved_count[baseline_index]
        if remaining <= 0:
            continue
        group = copy.deepcopy(baseline_group)
        group["chain_index"] = next_index
        group["instance_count"] = remaining
        group["linked_polymer_chain_indices"] = []
        current_groups.append(group)
        for record in records:
            key = _source_key(record)
            if int(record["baseline_chain_index"]) == baseline_index and key not in moved_to:
                moved_to[key] = next_index
        next_index += 1

    topology_keys = set(endpoints)
    for record in records:
        key = _source_key(record)
        if key in moved_to:
            record["chain_index"] = moved_to[key]
        if key not in topology_keys:
            continue
        classification = record["classification_observation"]
        if classification["resolution_status"] != "RESOLVED":
            continue
        if classification["topology_class"] != "STANDARD_RESIDUE":
            classification["topology_class"] = "TOPOLOGY_LINKED_NONSTANDARD"
            if classification["polymer_class"] == "WATER":
                classification["polymer_class"] = "NONPOLYMER"
            evidence = classification["evidence"]
            marker = "confirmed topology-forming relation"
            if marker not in evidence:
                evidence.append(marker)

    observed_count_by_group: defaultdict[int, int] = defaultdict(int)
    for record in records:
        if record["presence_status"] == "OBSERVED":
            observed_count_by_group[int(record["chain_index"])] += 1
    for group in current_groups:
        group["instance_count"] = observed_count_by_group[int(group["chain_index"])]

    current_by_key = {_source_key(record): int(record["chain_index"]) for record in records}
    for collection, fields in (
        (observations.get("connection_observations", []), ("partner_1", "partner_2")),
        (observations.get("coordination_observations", []), ("metal", "donor")),
    ):
        for relation in collection:
            for field in fields:
                key = _source_key(relation[field])
                if key in current_by_key:
                    relation[field]["chain_index"] = current_by_key[key]

    records.sort(
        key=lambda item: (
            int(item["chain_index"]),
            str(item.get("source_chain_id")),
            str(item["source_resid"]["number"]),
            str(item["source_resid"].get("insertion_code")),
            item["residue_name"],
        )
    )
    current_groups.sort(key=lambda item: int(item["chain_index"]))
    observations["chain_groups"] = current_groups
    recompute_summary(observations)


def recompute_summary(observations: dict[str, Any]) -> None:
    records = observations.get("residue_records", [])
    unresolved = observations.get("unresolved_observations", [])
    observations["summary"] = {
        "entity_count": len(observations.get("entities", [])),
        "chain_group_count": len(observations.get("chain_groups", [])),
        "recorded_residue_count": len(records),
        "observed_residue_count": sum(item["presence_status"] == "OBSERVED" for item in records),
        "missing_expected_residue_count": sum(item["presence_status"] == "MISSING_EXPECTED" for item in records),
        "unresolved_observation_count": len(unresolved),
        "multiple_conformation_residue_count": sum(
            item["conformation_observation"]["status"] == "MULTIPLE_CONFORMATIONS"
            for item in records
        ),
        "heavy_atom_issue_count": sum(
            bool(item["heavy_atom_check"].get("findings"))
            or item["heavy_atom_check"].get("execution_status") == "REFERENCE_TEMPLATE_UNAVAILABLE"
            for item in records
        ),
    }


def apply_relation_result(
    observations: dict[str, Any],
    result: dict[str, Any],
    relation_kind: str,
    result_path: Path,
    decisions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    output = copy.deepcopy(observations)
    issue_types = RELATION_ISSUES[relation_kind]
    output["unresolved_observations"] = [
        item
        for item in output.get("unresolved_observations", [])
        if item.get("issue_type") not in issue_types
    ]
    relation_observations, matched, issues = _relation_observations(
        result, relation_kind, decisions
    )
    for relation_id, decision in decisions.items():
        if decision["relation_kind"] != relation_kind or relation_id in matched:
            continue
        issues.append(
            {
                "issue_type": "RELATION_DECISION_TARGET_NOT_FOUND",
                "subject": {"relation_id": relation_id, "relation_kind": relation_kind},
                "evidence": ["decision target is absent from the current relation result"],
                "resolution_status": "PENDING_CONFIRMATION",
            }
        )
    output["unresolved_observations"].extend(issues)
    key = "possible_connections" if relation_kind == "COVALENT_CONNECTION" else "possible_coordination"
    collection = "connection_observations" if relation_kind == "COVALENT_CONNECTION" else "coordination_observations"
    output[collection] = relation_observations
    output["completed_checks"][key] = (
        "NOT_PERFORMED" if result["status"] == "NOT_PERFORMED" else "COMPLETED"
    )
    output["check_outputs"][key] = {
        "path": str(result_path.resolve()),
        "sha256": hashlib.sha256(yaml_text(result).encode("utf-8")).hexdigest(),
    }
    recompute_topology_state(output)
    return output


@contextmanager
def observations_lock(observations_path: Path):
    lock_path = observations_path.with_name(observations_path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ClassificationToolError(
                f"classification observations are locked by another operation: {lock_path}"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def commit_yaml_pair(
    first_path: Path,
    first_document: Any,
    second_path: Path,
    second_document: Any,
) -> None:
    if first_path.resolve() == second_path.resolve():
        raise ClassificationToolError("paired outputs must use different paths")
    for path in (first_path, second_path):
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise ClassificationToolError(f"output path is not a regular file: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    staged = []
    for path, document in ((first_path, first_document), (second_path, second_document)):
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(yaml_text(document), encoding="utf-8")
        staged.append(temporary)
    previous = {
        first_path: first_path.read_bytes() if first_path.exists() else None,
        second_path: second_path.read_bytes() if second_path.exists() else None,
    }
    try:
        os.replace(staged[0], first_path)
        os.replace(staged[1], second_path)
    except Exception as exc:
        for temporary in staged:
            temporary.unlink(missing_ok=True)
        for path, payload in previous.items():
            if payload is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(payload)
        raise ClassificationToolError(f"paired output commit failed: {exc}") from exc

#!/usr/bin/env python3
"""Build the downstream classification contract from current Skill 1.2 observations."""
from __future__ import annotations

import argparse
import copy
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    read_yaml_strict,
    require_sha256,
    sha256_file,
    validate_document,
    yaml_text,
)
from selection_identity import (
    component_id_from_members,
    endpoint_id_from_source_identity,
    residue_id_from_source_identity,
)

VERSION = "1.1.0"
RELATION_REQUEST_TYPES = {
    "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE",
    "CONNECTION_DEFINITION_CONFLICT",
    "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
    "COORDINATION_DEFINITION_CONFLICT",
}
ALLOWED_DECISIONS = {
    "PROJECT_REGISTRY_CLASSIFICATION_CONFLICT": ["SET_CLASSIFICATION"],
    "PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT": ["SET_CLASSIFICATION"],
    "RESIDUE_CLASSIFICATION_UNRESOLVED": ["SET_CLASSIFICATION"],
    "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE": ["SELECT_RTP_TEMPLATE", "PROVIDE_CORRECTED_FORCE_FIELD"],
    "TERMINAL_RTP_TEMPLATE_AMBIGUOUS": ["SELECT_RTP_TEMPLATE", "PROVIDE_TERMINAL_TEMPLATE_MAPPING"],
    "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE": ["CONFIRMED", "REJECTED"],
    "CONNECTION_DEFINITION_CONFLICT": ["CONFIRMED", "REJECTED", "PROVIDE_CORRECTED_DEFINITION"],
    "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE": ["CONFIRMED", "REJECTED"],
    "COORDINATION_DEFINITION_CONFLICT": ["CONFIRMED", "REJECTED", "PROVIDE_CORRECTED_DEFINITION"],
    "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE": ["PROVIDE_SOURCE_RESID", "PROVIDE_NUMBERING_MAPPING", "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES"],
    "MISSING_RESIDUE_CHAIN_UNRESOLVED": ["ASSIGN_CHAIN_INDEX", "PROVIDE_CHAIN_MAPPING", "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES"],
    "SEQUENCE_REFERENCE_CONFLICT": ["SELECT_SEQUENCE_REFERENCE", "PROVIDE_CORRECTED_SEQUENCE_REFERENCE"],
    "CCD_COMPONENT_DEFINITION_CONFLICT": ["PROVIDE_CORRECTED_CCD_LIBRARY"],
    "ATOM_NAME_MAPPING_REQUIRED": ["APPLY_ATOM_NAME_MAPPING", "REJECT_ATOM_NAME_MAPPING", "PROVIDE_CORRECTED_REFERENCE"],
    "RELATION_DECISION_TARGET_NOT_FOUND": ["REMOVE_STALE_RELATION_DECISION", "PROVIDE_CORRECTED_RELATION_DEFINITION"],
}


def _required_mapping(document: dict[str, Any], key: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise ClassificationToolError(f"config field {key!r} must be a mapping")
    return value


def _required_path(mapping: dict[str, Any], key: str) -> Path:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ClassificationToolError(f"config field {key!r} must be a path")
    return Path(value).resolve()


def _load_hashed(config: dict[str, Any], key: str, default_schema: Path) -> tuple[dict[str, Any], Path, str]:
    item = _required_mapping(config, key)
    path = _required_path(item, "path")
    observed_hash = require_sha256(path, str(item.get("sha256", "")))
    schema = Path(item.get("schema", default_schema)).resolve()
    document = read_yaml_strict(path)
    validate_document(document, schema)
    return document, path, observed_hash


def _load_check_output(
    observations: dict[str, Any],
    name: str,
    schema_path: Path,
) -> tuple[dict[str, Any], str]:
    reference = observations["check_outputs"][name]
    if not reference["path"] or not reference["sha256"]:
        raise ClassificationToolError(f"relation result reference is missing: {name}")
    path = Path(reference["path"]).resolve()
    observed_hash = require_sha256(path, reference["sha256"])
    document = read_yaml_strict(path)
    validate_document(document, schema_path)
    expected = observations["input"]
    result_input = document["input"]
    if (
        result_input["structure_sha256"] != expected["structure_sha256"]
        or str(result_input["selected_model_id"]) != str(expected["selected_model_id"])
    ):
        raise ClassificationToolError(f"relation result does not match observations: {name}")
    return document, observed_hash


def _validate_relation_provenance(
    manifest: dict[str, Any],
    connections: dict[str, Any],
    coordination: dict[str, Any],
) -> None:
    for name, document in (
        ("possible_connections", connections),
        ("possible_coordination", coordination),
    ):
        manifest_entry = manifest["relation_definition_files"][name]
        result_input = document["input"]
        if (
            manifest_entry["path"] != result_input["definition_path"]
            or manifest_entry["sha256"] != result_input["definition_sha256"]
        ):
            raise ClassificationToolError(
                f"relation definition provenance differs between manifest and result: {name}"
            )


def _source_key(value: dict[str, Any]) -> tuple[str | None, str, str | None, str]:
    identity = value.get("source_identity", value)
    resid = identity["source_resid"]
    return (
        identity.get("source_chain_id"),
        str(resid["number"]),
        resid.get("insertion_code"),
        identity["source_residue_name"],
    )


def _issue_to_request(issue: dict[str, Any]) -> dict[str, Any]:
    issue_type = issue.get("issue_type", "RESIDUE_CLASSIFICATION_UNRESOLVED")
    if issue_type not in ALLOWED_DECISIONS:
        issue_type = "RESIDUE_CLASSIFICATION_UNRESOLVED"
    subject = copy.deepcopy(issue.get("subject", {}))
    relation_id = subject.pop("relation_id", None)
    request = {
        "request_type": issue_type,
        "subject": subject,
        "evidence": {"items": copy.deepcopy(issue.get("evidence", []))},
        "reason": "; ".join(str(item) for item in issue.get("evidence", []))
        or "classification evidence remains unresolved",
        "allowed_decisions": ALLOWED_DECISIONS[issue_type],
    }
    if issue_type in RELATION_REQUEST_TYPES:
        if not isinstance(relation_id, str):
            raise ClassificationToolError(f"relation issue {issue_type} lacks relation_id")
        request["relation_id"] = relation_id
    return request


def _requests(observations: dict[str, Any]) -> dict[str, Any]:
    requests = [_issue_to_request(item) for item in observations["unresolved_observations"]]
    for index, request in enumerate(requests, start=1):
        request["request_index"] = index
    return {
        "schema_version": "1.0",
        "status": "USER_CONFIRMATION_REQUIRED" if requests else "NO_CONFIRMATION_REQUIRED",
        "requests": requests,
    }


def _apply_supported_decisions(
    observations: dict[str, Any],
    config: dict[str, Any],
    confirmation_schema: Path,
) -> dict[str, Any]:
    source = config.get("decision_source")
    if source is None:
        return copy.deepcopy(observations)
    if not isinstance(source, dict):
        raise ClassificationToolError("decision_source must be a mapping")
    path = _required_path(source, "confirmation_requests_path")
    require_sha256(path, str(source.get("confirmation_requests_sha256", "")))
    previous = read_yaml_strict(path)
    validate_document(previous, confirmation_schema)
    by_index = {item["request_index"]: item for item in previous["requests"]}
    output = copy.deepcopy(observations)
    records = {_source_key(item): item for item in output["residue_records"]}
    resolved_issue_keys: set[tuple[str, str]] = set()
    for decision in source.get("decisions", []) or []:
        request = by_index.get(decision.get("request_index"))
        if request is None:
            raise ClassificationToolError("decision references a missing request_index")
        if request["request_type"] in RELATION_REQUEST_TYPES:
            raise ClassificationToolError(
                "relation decisions must be recorded with record_relation_decisions.py"
            )
        action = decision.get("decision")
        if action not in request["allowed_decisions"]:
            raise ClassificationToolError("decision is not allowed for the referenced request")
        subject = request["subject"]
        if action == "SET_CLASSIFICATION":
            classification = decision.get("classification")
            if not isinstance(classification, dict):
                raise ClassificationToolError("SET_CLASSIFICATION requires classification")
            source_resid = subject.get("source_resid")
            key = (
                subject.get("source_chain_id"),
                str(source_resid["number"]),
                source_resid.get("insertion_code"),
                subject["residue_name"],
            )
            if key not in records:
                raise ClassificationToolError("classification decision target is missing")
            records[key]["classification_observation"] = {
                "component_id": classification.get("component_id"),
                "polymer_class": classification["polymer_class"],
                "topology_class": classification["topology_class"],
                "resolution_status": "RESOLVED",
                "primary_source": "PROJECT_DEFINITION",
                "evidence": ["user classification decision"],
            }
            resolved_issue_keys.add((request["request_type"], str(subject)))
        elif action in {"APPLY_ATOM_NAME_MAPPING", "REJECT_ATOM_NAME_MAPPING"}:
            source_resid = subject.get("source_resid")
            key = (
                subject.get("source_chain_id"),
                str(source_resid["number"]),
                source_resid.get("insertion_code"),
                subject["residue_name"],
            )
            record = records.get(key)
            if record is None:
                raise ClassificationToolError("atom mapping decision target is missing")
            check = record["heavy_atom_check"]
            if action == "REJECT_ATOM_NAME_MAPPING":
                check["mapping_resolution_status"] = "REJECTED"
                check["effective_comparison"] = None
            else:
                exact = check.get("exact_comparison")
                if not isinstance(exact, dict):
                    raise ClassificationToolError("mapping cannot be applied without exact comparison")
                missing = set(exact["missing_expected_atom_names"])
                unexpected = set(exact["unexpected_observed_atom_names"])
                for candidate in check.get("atom_name_mapping_candidates", []):
                    missing.discard(candidate["reference_atom_name"])
                    unexpected.discard(candidate["observed_atom_name"])
                check["mapping_resolution_status"] = "APPLIED"
                check["effective_comparison"] = {
                    "missing_expected_atom_names": sorted(missing),
                    "unexpected_observed_atom_names": sorted(unexpected),
                }
            resolved_issue_keys.add((request["request_type"], str(subject)))
    if resolved_issue_keys:
        output["unresolved_observations"] = [
            item
            for item in output["unresolved_observations"]
            if (item.get("issue_type"), str(item.get("subject", {}))) not in resolved_issue_keys
        ]
    return output


def _materialize_ids(observations: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple, dict[str, str]]]:
    records = copy.deepcopy(observations["residue_records"])
    groups = copy.deepcopy(observations["chain_groups"])
    observed_by_group: defaultdict[int, list[str]] = defaultdict(list)
    missing_by_group: defaultdict[int, list[str]] = defaultdict(list)
    identity_by_key: dict[tuple, dict[str, str]] = {}
    for record in records:
        residue_id = residue_id_from_source_identity(record["source_identity"])
        record["residue_id"] = residue_id
        bucket = observed_by_group if record["presence_status"] == "OBSERVED" else missing_by_group
        bucket[int(record["chain_index"])].append(residue_id)
        identity_by_key[_source_key(record)] = {"residue_id": residue_id}
    component_by_chain: dict[int, str] = {}
    for group in groups:
        chain_index = int(group["chain_index"])
        component_id = component_id_from_members(
            str(observations["input"]["selected_model_id"]),
            group["group_type"],
            observed_by_group.get(chain_index, []),
            missing_by_group.get(chain_index, []),
        )
        component_by_chain[chain_index] = component_id
        group["component_id"] = component_id
        group["residue_ids"] = sorted(observed_by_group.get(chain_index, []))
        group["missing_residue_ids"] = sorted(missing_by_group.get(chain_index, []))
        group["grouping_status"] = "FINAL"
    for record in records:
        record["component_id"] = component_by_chain[int(record["chain_index"])]
        identity_by_key[_source_key(record)]["component_id"] = record["component_id"]
    return groups, records, identity_by_key


def _final_endpoint(endpoint: dict[str, Any], identities: dict[tuple, dict[str, str]]) -> dict[str, Any]:
    identity = identities[_source_key(endpoint)]
    return {
        "endpoint_id": endpoint_id_from_source_identity(endpoint["source_identity"]),
        "residue_id": identity["residue_id"],
        "component_id": identity["component_id"],
        "source_identity": copy.deepcopy(endpoint["source_identity"]),
        "current_identity": copy.deepcopy(endpoint["current_identity"]),
        "chain_index": int(endpoint["chain_index"]),
        "source_chain_id": endpoint.get("source_chain_id"),
        "source_resid": copy.deepcopy(endpoint["source_resid"]),
        "residue_name": endpoint["residue_name"],
        "atom_name": endpoint["atom_name"],
        "altloc_id": endpoint.get("altloc_id"),
    }


def _relations(observations: dict[str, Any], identities: dict[tuple, dict[str, str]]) -> tuple[dict[str, list], dict[str, list]]:
    confirmed = {"covalent_connections": [], "metal_coordination": []}
    rejected = {"covalent_connections": [], "metal_coordination": []}
    for item in observations["connection_observations"]:
        if item["status"] not in {"CONFIRMED", "REJECTED"}:
            continue
        relation = {
            "relation_id": item["relation_id"],
            "relation_type": "COVALENT_CONNECTION",
            "endpoint_1": _final_endpoint(item["partner_1"], identities),
            "endpoint_2": _final_endpoint(item["partner_2"], identities),
            "evidence_status": (
                "REJECTED_BY_USER"
                if item["status"] == "REJECTED"
                else "CONFIRMED_BY_USER"
                if item["confirmation_status"] == "CONFIRMED_BY_USER"
                else "CONFIRMED_BY_STRUCTURE"
            ),
            "topology_effect_applied": item["topology_effect"]["status"] == "APPLIED",
        }
        target = confirmed if item["status"] == "CONFIRMED" else rejected
        target["covalent_connections"].append(relation)
    for item in observations["coordination_observations"]:
        if item["status"] not in {"CONFIRMED", "REJECTED"}:
            continue
        relation = {
            "relation_id": item["relation_id"],
            "relation_type": "METAL_COORDINATION",
            "endpoint_1": _final_endpoint(item["metal"], identities),
            "endpoint_2": _final_endpoint(item["donor"], identities),
            "evidence_status": (
                "REJECTED_BY_USER"
                if item["status"] == "REJECTED"
                else "CONFIRMED_BY_USER"
                if item["confirmation_status"] == "CONFIRMED_BY_USER"
                else "CONFIRMED_BY_STRUCTURE"
            ),
            "topology_effect_applied": item["topology_effect"]["status"] == "APPLIED",
        }
        target = confirmed if item["status"] == "CONFIRMED" else rejected
        target["metal_coordination"].append(relation)
    return confirmed, rejected


def _render_report(result: dict[str, Any], confirmations: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Component and residue classification report",
        "",
        f"- Result status: `{result['result_status']}`",
        f"- Selected model: `{result['selected_model_id']}`",
        f"- Classification mode: `{result['classification_mode']}`",
        f"- Components: {summary['chain_group_count']}",
        f"- Pending confirmations: {summary['unresolved_item_count']}",
        "",
        "## Classification counts",
        "",
    ]
    for key in (
        "standard_residue_count",
        "topology_linked_nonstandard_count",
        "independent_nonstandard_count",
        "solvent_component_count",
        "ion_component_count",
        "missing_residue_count",
        "multiple_conformation_residue_count",
        "heavy_atom_issue_count",
    ):
        lines.append(f"- `{key}`: {summary[key]}")
    lines.extend(["", "## Pending confirmations", ""])
    if confirmations["requests"]:
        for request in confirmations["requests"]:
            lines.append(
                f"- {request['request_index']}. `{request['request_type']}` — {request['reason']}"
            )
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def build(config: dict[str, Any], script_dir: Path) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Path]]:
    schema_dir = script_dir.parent / "schemas"
    model_scope, _model_path, model_hash = _load_hashed(
        config, "model_scope", schema_dir / "model_scope.schema.yaml"
    )
    manifest, _manifest_path, manifest_hash = _load_hashed(
        config, "reference_manifest", schema_dir / "reference_manifest.schema.yaml"
    )
    observations_config = _required_mapping(config, "classification_observations")
    observations_path = _required_path(observations_config, "path")
    observations = read_yaml_strict(observations_path)
    validate_document(
        observations,
        Path(
            observations_config.get(
                "schema", schema_dir / "classification_observations.schema.yaml"
            )
        ).resolve(),
    )
    for name in ("possible_connections", "possible_coordination"):
        if observations["completed_checks"][name] in {"PENDING", "BLOCKED"}:
            raise ClassificationToolError(f"relation stage is not complete: {name}")
    connections, connections_hash = _load_check_output(
        observations,
        "possible_connections",
        schema_dir / "possible_connections_result.schema.yaml",
    )
    coordination, coordination_hash = _load_check_output(
        observations,
        "possible_coordination",
        schema_dir / "possible_coordination_result.schema.yaml",
    )
    _validate_relation_provenance(manifest, connections, coordination)
    if (
        observations["input"]["structure_sha256"] != model_scope["input_structure"]["sha256"]
        or str(observations["input"]["selected_model_id"])
        != str(model_scope["selection"]["selected_model_id"])
    ):
        raise ClassificationToolError("model scope and observations do not match")
    effective = _apply_supported_decisions(
        observations, config, schema_dir / "confirmation_requests.schema.yaml"
    )
    confirmations = _requests(effective)
    validate_document(confirmations, schema_dir / "confirmation_requests.schema.yaml")
    groups, records, identities = _materialize_ids(effective)
    confirmed, rejected = _relations(effective, identities)
    counts = defaultdict(int)
    heavy_issues = 0
    for record in records:
        topology = record["classification_observation"]["topology_class"]
        if topology:
            counts[topology] += 1
        check = record["heavy_atom_check"]
        heavy_issues += bool(check.get("findings")) or check.get("execution_status") == "REFERENCE_TEMPLATE_UNAVAILABLE"
    output_config = _required_mapping(config, "output")
    confirmation_path = _required_path(output_config, "confirmation_requests_path")
    result_path = _required_path(output_config, "classification_result_path")
    report_path = _required_path(output_config, "classification_report_path")
    confirmation_hash = hashlib.sha256(yaml_text(confirmations).encode("utf-8")).hexdigest()
    unresolved = [
        {
            "request_index": item["request_index"],
            "request_type": item["request_type"],
            **({"relation_id": item["relation_id"]} if "relation_id" in item else {}),
            "subject": copy.deepcopy(item["subject"]),
        }
        for item in confirmations["requests"]
    ]
    result = {
        "schema_version": "1.0",
        "result_status": "PENDING_USER_CONFIRMATION" if unresolved else "COMPLETE",
        "selected_model_id": str(effective["input"]["selected_model_id"]),
        "classification_mode": effective["input"]["classification_mode"],
        "source_structure": {
            "path": effective["input"]["structure_path"],
            "sha256": effective["input"]["structure_sha256"],
            "source_format": effective["input"]["source_format"],
        },
        "source_hashes": {
            "model_scope": model_hash,
            "classification_observations": sha256_file(observations_path),
            "reference_manifest": manifest_hash,
            "possible_connections_result": connections_hash,
            "possible_coordination_result": coordination_hash,
            "confirmation_requests": confirmation_hash,
        },
        "chain_groups": groups,
        "residue_records": [
            {
                "residue_id": item["residue_id"],
                "component_id": item["component_id"],
                "source_identity": item["source_identity"],
                "current_identity": item["current_identity"],
                "chain_index": item["chain_index"],
                "source_chain_id": item["source_chain_id"],
                "source_resid": item["source_resid"],
                "residue_name": item["residue_name"],
                "presence_status": item["presence_status"],
                "sequence_position": item["sequence_position"],
                "classification": item["classification_observation"],
                "conformation": item["conformation_observation"],
                "heavy_atom_check": item["heavy_atom_check"],
            }
            for item in records
        ],
        "confirmed_relations": confirmed,
        "rejected_candidates": rejected,
        "unresolved_items": unresolved,
        "summary": {
            "chain_group_count": len(groups),
            "standard_residue_count": counts["STANDARD_RESIDUE"],
            "topology_linked_nonstandard_count": counts["TOPOLOGY_LINKED_NONSTANDARD"],
            "independent_nonstandard_count": counts["INDEPENDENT_NONSTANDARD"],
            "solvent_component_count": counts["SOLVENT_COMPONENT"],
            "ion_component_count": counts["ION_COMPONENT"],
            "multiple_conformation_residue_count": sum(
                record["conformation_observation"]["status"] == "MULTIPLE_CONFORMATIONS"
                for record in records
            ),
            "missing_residue_count": sum(item["presence_status"] == "MISSING_EXPECTED" for item in records),
            "heavy_atom_issue_count": int(heavy_issues),
            "unresolved_item_count": len(unresolved),
        },
    }
    report = _render_report(result, confirmations)
    return result, confirmations, report, {
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
        validate_document(
            config,
            script_dir.parent / "schemas/classification_result_build_config.schema.yaml",
        )
        result, confirmations, report, paths = build(config, script_dir)
        validate_document(
            result,
            Path(
                config["output"].get(
                    "classification_result_schema",
                    script_dir.parent / "schemas/classification_result.schema.yaml",
                )
            ).resolve(),
        )
        validate_document(
            confirmations,
            script_dir.parent / "schemas/confirmation_requests.schema.yaml",
        )
        staged = {
            paths["confirmation"]: yaml_text(confirmations),
            paths["result"]: yaml_text(result),
            paths["report"]: report,
        }
        for path, text in staged.items():
            if path.exists():
                if path.is_symlink() or not path.is_file():
                    raise ClassificationToolError(f"output path is not a regular file: {path}")
                if path.read_text(encoding="utf-8") != text:
                    raise ClassificationToolError(f"refusing to overwrite different existing output: {path}")
        temporaries = []
        created_paths = []
        for path, text in staged.items():
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_text(text, encoding="utf-8")
            temporaries.append((temporary, path))
        try:
            for temporary, path in temporaries:
                os.replace(temporary, path)
                created_paths.append(path)
        except Exception as exc:
            for temporary, _path in temporaries:
                temporary.unlink(missing_ok=True)
            for path in created_paths:
                path.unlink(missing_ok=True)
            raise ClassificationToolError(f"final output commit failed: {exc}") from exc
        return 0
    except ClassificationToolError as exc:
        print(f"build_classification_result.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"build_classification_result.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

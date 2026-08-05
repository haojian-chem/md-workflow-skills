#!/usr/bin/env python3
"""Record stable relation decisions from one exact confirmation request file."""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

from classification_common import (
    ClassificationToolError,
    atomic_write_yaml,
    read_yaml_strict,
    require_sha256,
    validate_document,
)
from observation_state import observations_lock

VERSION = "1.0.0"
RELATION_REQUEST_TYPES = {
    "GEOMETRY_SUPPORTED_COVALENT_CANDIDATE",
    "CONNECTION_DEFINITION_CONFLICT",
    "GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE",
    "COORDINATION_DEFINITION_CONFLICT",
}


def _required_path(mapping: dict[str, Any], key: str) -> Path:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ClassificationToolError(f"config field {key!r} must be a path")
    return Path(value).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--replace-existing", action="store_true")
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
            script_dir.parent / "schemas/relation_decision_record_config.schema.yaml",
        )
        request_config = config["confirmation_requests"]
        request_path = _required_path(request_config, "path")
        require_sha256(request_path, request_config["sha256"])
        request_schema = Path(
            request_config.get(
                "schema",
                script_dir.parent / "schemas/confirmation_requests.schema.yaml",
            )
        ).resolve()
        requests = read_yaml_strict(request_path)
        validate_document(requests, request_schema)
        by_index = {item["request_index"]: item for item in requests["requests"]}

        observations_config = config["classification_observations"]
        observations_path = _required_path(observations_config, "path")
        observations_schema = Path(
            observations_config.get(
                "schema",
                script_dir.parent / "schemas/classification_observations.schema.yaml",
            )
        ).resolve()
        output_config = config["relation_decisions"]
        output_path = _required_path(output_config, "path")
        output_schema = Path(
            output_config.get(
                "schema",
                script_dir.parent / "schemas/relation_decisions.schema.yaml",
            )
        ).resolve()
        replace = bool(config.get("replace_existing", False) or args.replace_existing)

        with observations_lock(observations_path):
            observations = read_yaml_strict(observations_path)
            validate_document(observations, observations_schema)
            if output_path.exists():
                document = read_yaml_strict(output_path)
                validate_document(document, output_schema)
                expected = observations["input"]
                if (
                    document["structure"]["structure_sha256"]
                    != expected["structure_sha256"]
                    or str(document["structure"]["selected_model_id"])
                    != str(expected["selected_model_id"])
                ):
                    raise ClassificationToolError(
                        "existing relation decisions belong to another structure state"
                    )
            else:
                document = {
                    "schema_version": "1.0",
                    "structure": {
                        "structure_sha256": observations["input"]["structure_sha256"],
                        "selected_model_id": str(
                            observations["input"]["selected_model_id"]
                        ),
                    },
                    "decisions": [],
                }
            decision_by_id = {
                item["relation_id"]: copy.deepcopy(item)
                for item in document["decisions"]
            }
            for submitted in config["decisions"]:
                request_index = submitted["request_index"]
                request = by_index.get(request_index)
                if request is None:
                    raise ClassificationToolError(
                        f"decision references missing request_index {request_index}"
                    )
                if request["request_type"] not in RELATION_REQUEST_TYPES:
                    raise ClassificationToolError(
                        f"request {request_index} is not a relation decision request"
                    )
                relation_id = request.get("relation_id")
                if not relation_id:
                    raise ClassificationToolError(
                        f"relation request {request_index} lacks relation_id"
                    )
                relation_kind = relation_id.split("/type/", 1)[1].split("/", 1)[0]
                candidate = {
                    "relation_id": relation_id,
                    "relation_kind": relation_kind,
                    "decision": submitted["decision"],
                }
                existing = decision_by_id.get(relation_id)
                if existing == candidate:
                    continue
                if existing is not None and not replace:
                    raise ClassificationToolError(
                        f"RELATION_DECISION_CONFLICT: {relation_id}"
                    )
                decision_by_id[relation_id] = candidate
            document["decisions"] = [
                decision_by_id[key] for key in sorted(decision_by_id)
            ]
            validate_document(document, output_schema)
            atomic_write_yaml(output_path, document, allow_replace=True)
        return 0
    except ClassificationToolError as exc:
        print(f"record_relation_decisions.py: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"record_relation_decisions.py: unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

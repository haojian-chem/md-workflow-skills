#!/usr/bin/env python3
"""Public final-builder entry point and legacy selection-ID assignment shim."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import build_classification_result_core as _core
from classification_common import ClassificationToolError
from selection_identity import (
    component_id_from_members,
    endpoint_id_from_source_identity,
    relation_id_from_endpoints,
    residue_id_from_source_identity,
)

# Preserve imports of established helper names while keeping the implementation
# in one core module.
globals().update(
    {
        name: getattr(_core, name)
        for name in dir(_core)
        if not name.startswith("__")
    }
)


def _assign_selection_contract_ids(
    selected_model_id: str,
    groups: list[dict[str, Any]],
    records: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> None:
    """Compatibility wrapper for the established 1.2→1.3 fixture.

    Current production code materializes IDs from current observations in the
    core builder. This function only preserves the tested in-place helper and
    does not restore relation inference or topology application.
    """
    observed_by_group: defaultdict[int, list[str]] = defaultdict(list)
    missing_by_group: defaultdict[int, list[str]] = defaultdict(list)
    identity_by_key: dict[tuple, dict[str, str]] = {}

    for record in records:
        residue_id = residue_id_from_source_identity(record["source_identity"])
        record["residue_id"] = residue_id
        chain_index = int(record["chain_index"])
        bucket = (
            observed_by_group
            if record["presence_status"] == "OBSERVED"
            else missing_by_group
        )
        bucket[chain_index].append(residue_id)
        identity_by_key[_core._source_key(record)] = {"residue_id": residue_id}

    component_by_chain: dict[int, str] = {}
    for group in groups:
        chain_index = int(group["chain_index"])
        component_id = component_id_from_members(
            selected_model_id,
            group["group_type"],
            observed_by_group.get(chain_index, []),
            missing_by_group.get(chain_index, []),
        )
        component_by_chain[chain_index] = component_id
        group["component_id"] = component_id
        group["residue_ids"] = sorted(observed_by_group.get(chain_index, []))
        group["missing_residue_ids"] = sorted(missing_by_group.get(chain_index, []))

    for record in records:
        component_id = component_by_chain[int(record["chain_index"])]
        record["component_id"] = component_id
        identity_by_key[_core._source_key(record)]["component_id"] = component_id

    relation_ids: set[str] = set()
    for relation in relations:
        endpoint_ids: list[str] = []
        for field in ("endpoint_1", "endpoint_2"):
            endpoint = relation[field]
            identity = identity_by_key[_core._source_key(endpoint)]
            endpoint_id = endpoint_id_from_source_identity(
                endpoint["source_identity"]
            )
            endpoint["endpoint_id"] = endpoint_id
            endpoint["residue_id"] = identity["residue_id"]
            endpoint["component_id"] = identity["component_id"]
            endpoint_ids.append(endpoint_id)
        relation_id = relation_id_from_endpoints(
            relation["relation_type"], endpoint_ids
        )
        if relation_id in relation_ids:
            raise ClassificationToolError(
                f"duplicate relation selection identity: {relation_id}"
            )
        relation_ids.add(relation_id)
        relation["relation_id"] = relation_id


if __name__ == "__main__":
    raise SystemExit(_core.main())

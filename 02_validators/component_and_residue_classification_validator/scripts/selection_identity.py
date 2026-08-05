#!/usr/bin/env python3
"""Public selection-ID surface with a narrow pre-redesign compatibility shim."""
from __future__ import annotations

from typing import Iterable

import selection_identity_core as _core

# Re-export the current opaque-ID implementation from one owner.
globals().update(
    {
        name: getattr(_core, name)
        for name in dir(_core)
        if not name.startswith("__")
    }
)


def relation_id_from_endpoints(
    relation_type: str,
    endpoint_ids: Iterable[str],
) -> str:
    """Deprecated compatibility helper for historical 1.2 fixtures.

    New code must call ``covalent_relation_id`` or
    ``coordination_relation_id`` explicitly. The unordered coordination path is
    retained only so the previous 1.2→1.3 acceptance fixture can be migrated
    without breaking collection; current relation checks never call it.
    """
    endpoints = list(endpoint_ids)
    if len(endpoints) != 2 or any(not value for value in endpoints):
        raise SelectionIdentityError("relation ID requires exactly two endpoint IDs")
    if relation_type == "COVALENT_CONNECTION":
        return covalent_relation_id(endpoints[0], endpoints[1])
    if relation_type == "METAL_COORDINATION":
        digest = _core._relation_digest(sorted(endpoints))
        return f"relation:v1/type/METAL_COORDINATION/endpoints/{digest}"
    raise SelectionIdentityError(f"unsupported relation type: {relation_type}")

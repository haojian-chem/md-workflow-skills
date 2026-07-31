#!/usr/bin/env python3
"""Stable identifiers exported by classification result for downstream selection.

The identifiers are deterministic for one source STRUCTURE revision and do not
encode chain_index.  Downstream consumers must treat them as opaque values
materialized by validator 1.2 rather than reconstructing them independently.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable
from urllib.parse import quote


class SelectionIdentityError(ValueError):
    """Raised when an identity cannot be converted into a stable selection ID."""


def _encode(value: Any) -> str:
    return quote("" if value is None else str(value), safe="")


def _required_mapping(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise SelectionIdentityError(f"identity field {key!r} must be a mapping")
    return value


def residue_id_from_source_identity(identity: dict[str, Any]) -> str:
    """Return immutable residue ID from source provenance identity."""
    resid = _required_mapping(identity, "source_resid")
    required = ("source_model_id", "source_residue_name")
    for key in required:
        if not isinstance(identity.get(key), str) or not identity[key]:
            raise SelectionIdentityError(f"identity field {key!r} must be a non-empty string")
    number = resid.get("number")
    if not isinstance(number, str) or not number:
        raise SelectionIdentityError("source_resid.number must be a non-empty string")
    return (
        "residue:v1"
        f"/model/{_encode(identity['source_model_id'])}"
        f"/chain/{_encode(identity.get('source_chain_id'))}"
        f"/name/{_encode(identity['source_residue_name'])}"
        f"/number/{_encode(number)}"
        f"/icode/{_encode(resid.get('insertion_code'))}"
    )


def endpoint_id_from_source_identity(identity: dict[str, Any]) -> str:
    """Return atom endpoint ID for a relation endpoint.

    Relation contracts currently do not carry altLoc, so this endpoint identity
    intentionally ends at the exact atom name within the source residue.
    """
    atom_name = identity.get("source_atom_name")
    if not isinstance(atom_name, str) or not atom_name:
        raise SelectionIdentityError("source_atom_name must be a non-empty string")
    residue_identity = {
        key: identity[key]
        for key in (
            "source_model_id",
            "source_chain_id",
            "source_resid",
            "source_residue_name",
        )
    }
    return f"endpoint:v1/{residue_id_from_source_identity(residue_identity)}/atom/{_encode(atom_name)}"


def _membership_digest(observed: Iterable[str], missing: Iterable[str]) -> str:
    members = [*(f"OBSERVED:{value}" for value in sorted(observed)), *(f"MISSING:{value}" for value in sorted(missing))]
    if not members:
        raise SelectionIdentityError("component must contain at least one observed or missing residue")
    return hashlib.sha256("\n".join(members).encode("utf-8")).hexdigest()


def component_id_from_members(
    selected_model_id: str,
    group_type: str,
    observed_residue_ids: Iterable[str],
    missing_residue_ids: Iterable[str],
) -> str:
    """Return stable component ID from membership, not from chain_index."""
    if not selected_model_id:
        raise SelectionIdentityError("selected_model_id must be non-empty")
    if not group_type:
        raise SelectionIdentityError("group_type must be non-empty")
    digest = _membership_digest(observed_residue_ids, missing_residue_ids)
    return (
        "component:v1"
        f"/model/{_encode(selected_model_id)}"
        f"/type/{_encode(group_type)}"
        f"/members/{digest}"
    )


def relation_id_from_endpoints(relation_type: str, endpoint_ids: Iterable[str]) -> str:
    """Return stable relation ID independent of evidence status and ordering."""
    endpoints = sorted(endpoint_ids)
    if len(endpoints) != 2 or any(not value for value in endpoints):
        raise SelectionIdentityError("relation ID requires exactly two endpoint IDs")
    digest = hashlib.sha256("\n".join(endpoints).encode("utf-8")).hexdigest()
    return f"relation:v1/type/{_encode(relation_type)}/endpoints/{digest}"

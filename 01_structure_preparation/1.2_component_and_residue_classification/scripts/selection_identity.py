#!/usr/bin/env python3
"""Opaque deterministic IDs exported by Skill 1.2 for downstream selection."""
from __future__ import annotations

import hashlib
from typing import Any, Iterable
from urllib.parse import quote


class SelectionIdentityError(ValueError):
    pass


def _encode(value: Any) -> str:
    return quote("" if value is None else str(value), safe="")


def _required_mapping(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise SelectionIdentityError(f"identity field {key!r} must be a mapping")
    return value


def residue_id_from_source_identity(identity: dict[str, Any]) -> str:
    resid = _required_mapping(identity, "source_resid")
    for key in ("source_model_id", "source_residue_name"):
        if not isinstance(identity.get(key), str) or not identity[key]:
            raise SelectionIdentityError(f"identity field {key!r} must be non-empty")
    number = resid.get("number")
    if not isinstance(number, str) or not number:
        raise SelectionIdentityError("source_resid.number must be non-empty")
    return (
        "residue:v1"
        f"/model/{_encode(identity['source_model_id'])}"
        f"/chain/{_encode(identity.get('source_chain_id'))}"
        f"/name/{_encode(identity['source_residue_name'])}"
        f"/number/{_encode(number)}"
        f"/icode/{_encode(resid.get('insertion_code'))}"
    )


def endpoint_id_from_source_identity(identity: dict[str, Any]) -> str:
    atom_name = identity.get("source_atom_name")
    if not isinstance(atom_name, str) or not atom_name:
        raise SelectionIdentityError("source_atom_name must be non-empty")
    residue_identity = {
        key: identity[key]
        for key in (
            "source_model_id",
            "source_chain_id",
            "source_resid",
            "source_residue_name",
        )
    }
    return (
        f"endpoint:v1/{residue_id_from_source_identity(residue_identity)}"
        f"/atom/{_encode(atom_name)}/altloc/{_encode(identity.get('source_altloc_id'))}"
    )


def _membership_digest(observed: Iterable[str], missing: Iterable[str]) -> str:
    members = [
        *(f"OBSERVED:{value}" for value in sorted(observed)),
        *(f"MISSING:{value}" for value in sorted(missing)),
    ]
    if not members:
        raise SelectionIdentityError("component must contain at least one residue")
    return hashlib.sha256("\n".join(members).encode("utf-8")).hexdigest()


def component_id_from_members(
    selected_model_id: str,
    group_type: str,
    observed_residue_ids: Iterable[str],
    missing_residue_ids: Iterable[str],
) -> str:
    if not selected_model_id or not group_type:
        raise SelectionIdentityError("selected model and group type must be non-empty")
    digest = _membership_digest(observed_residue_ids, missing_residue_ids)
    return (
        "component:v1"
        f"/model/{_encode(selected_model_id)}"
        f"/type/{_encode(group_type)}"
        f"/members/{digest}"
    )


def _relation_digest(parts: Iterable[str]) -> str:
    values = list(parts)
    if len(values) != 2 or any(not value for value in values):
        raise SelectionIdentityError("relation ID requires exactly two endpoints")
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def covalent_relation_id(endpoint_1_id: str, endpoint_2_id: str) -> str:
    digest = _relation_digest(sorted([endpoint_1_id, endpoint_2_id]))
    return f"relation:v1/type/COVALENT_CONNECTION/endpoints/{digest}"


def coordination_relation_id(metal_endpoint_id: str, donor_endpoint_id: str) -> str:
    digest = _relation_digest(
        [f"metal:{metal_endpoint_id}", f"donor:{donor_endpoint_id}"]
    )
    return f"relation:v1/type/METAL_COORDINATION/endpoints/{digest}"

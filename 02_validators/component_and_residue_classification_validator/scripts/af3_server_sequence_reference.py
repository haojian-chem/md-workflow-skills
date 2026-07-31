#!/usr/bin/env python3
"""AlphaFold Server job_request JSON sequence-reference parser."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from classification_common import ClassificationToolError


def _server_chain_id(index: int) -> str:
    """Return AlphaFold Server-style A..Z, AA.. IDs for a zero-based index."""
    if index < 0:
        raise ClassificationToolError(
            "AlphaFold Server chain index must be non-negative"
        )
    value = index + 1
    letters: list[str] = []
    while value:
        value, remainder = divmod(value - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def _merge_sequence(
    sequences: dict[str, list[str]],
    identifier: str,
    monomers: list[str],
) -> None:
    existing = sequences.get(identifier)
    if existing is not None and existing != monomers:
        raise ClassificationToolError(
            f"conflicting AF3 sequences for chain {identifier}"
        )
    sequences[identifier] = monomers


def _positive_count(payload: dict[str, Any]) -> int:
    value = payload.get("count", 1)
    if isinstance(value, bool):
        raise ClassificationToolError(
            "AlphaFold Server sequence count must be a positive integer"
        )
    try:
        count = int(value)
    except (TypeError, ValueError) as exc:
        raise ClassificationToolError(
            "AlphaFold Server sequence count must be a positive integer"
        ) from exc
    if count < 1 or count != value:
        raise ClassificationToolError(
            "AlphaFold Server sequence count must be a positive integer"
        )
    return count


def parse_af3_server_job_request(
    path: Path,
) -> dict[str, list[str]] | None:
    """Parse one AlphaFold Server job, or return None for another JSON dialect."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return None
    if len(data) != 1 or not isinstance(data[0], dict):
        raise ClassificationToolError(
            "AlphaFold Server job_request JSON must contain exactly one job"
        )
    job = data[0]
    if job.get("dialect") != "alphafoldserver":
        raise ClassificationToolError(
            "top-level AF3 JSON list is accepted only for dialect alphafoldserver"
        )
    entries = job.get("sequences")
    if not isinstance(entries, list):
        raise ClassificationToolError(
            "AlphaFold Server job_request JSON has no sequences list"
        )

    sequences: dict[str, list[str]] = {}
    next_chain_index = 0
    for entry in entries:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise ClassificationToolError(
                "AlphaFold Server sequence entries must be single-key mappings"
            )
        _kind, payload = next(iter(entry.items()))
        if not isinstance(payload, dict):
            raise ClassificationToolError(
                "AlphaFold Server sequence payload must be a mapping"
            )
        count = _positive_count(payload)
        explicit_ids = payload.get("id")
        if isinstance(explicit_ids, str):
            identifiers = [explicit_ids]
        elif isinstance(explicit_ids, list):
            identifiers = [str(value) for value in explicit_ids]
        elif explicit_ids is None:
            identifiers = [
                _server_chain_id(next_chain_index + offset)
                for offset in range(count)
            ]
        else:
            raise ClassificationToolError(
                "AlphaFold Server sequence id must be a string or list"
            )
        if explicit_ids is not None and len(identifiers) != count:
            raise ClassificationToolError(
                "AlphaFold Server explicit id count does not match entity count"
            )

        sequence = payload.get("sequence")
        if isinstance(sequence, str):
            monomers = list(sequence.strip())
            if not monomers:
                raise ClassificationToolError(
                    "AlphaFold Server polymer sequence must not be empty"
                )
            for identifier in identifiers:
                _merge_sequence(sequences, identifier, monomers)
        # Ligands and ions still consume server-assigned chain identifiers.
        next_chain_index += count
    return sequences


# Private compatibility alias for existing direct parser tests.
_parse_server_job_request = parse_af3_server_job_request

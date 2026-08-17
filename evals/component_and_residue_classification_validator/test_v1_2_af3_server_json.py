from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "02_validators/component_and_residue_classification_validator/scripts"
sys.path.insert(0, str(SCRIPTS))

from af3_server_sequence_reference import (  # noqa: E402
    _parse_server_job_request,
    _server_chain_id,
)
from classification_common import ClassificationToolError  # noqa: E402


def test_server_chain_identifier_sequence() -> None:
    assert [_server_chain_id(index) for index in (0, 25, 26, 27, 51, 52)] == [
        "A",
        "Z",
        "AA",
        "AB",
        "AZ",
        "BA",
    ]


def test_alphafold_server_entities_consume_chain_ids_in_order(tmp_path: Path) -> None:
    path = tmp_path / "job_request.json"
    path.write_text(
        json.dumps(
            [
                {
                    "name": "server dialect",
                    "dialect": "alphafoldserver",
                    "version": 3,
                    "sequences": [
                        {"proteinChain": {"sequence": "AC", "count": 2}},
                        {"ligand": {"ligand": "CCD_HEM", "count": 1}},
                        {"proteinChain": {"sequence": "GG", "count": 1}},
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )
    assert _parse_server_job_request(path) == {
        "A": ["A", "C"],
        "B": ["A", "C"],
        "D": ["G", "G"],
    }


def test_alphafold_server_multiple_jobs_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "job_request.json"
    path.write_text(
        json.dumps(
            [
                {"dialect": "alphafoldserver", "sequences": []},
                {"dialect": "alphafoldserver", "sequences": []},
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ClassificationToolError, match="exactly one job"):
        _parse_server_job_request(path)

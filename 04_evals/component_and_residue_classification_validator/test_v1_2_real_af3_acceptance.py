from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures/real_af3"
sys.path.insert(0, str(FIXTURES))

from fold_1bk0_ipns_fe_fixture_data import (  # noqa: E402
    JOB_FILENAME as IPNS_JOB_FILENAME,
    JOB_SHA256 as IPNS_JOB_SHA256,
    MODEL_FILENAME as IPNS_MODEL_FILENAME,
    MODEL_SHA256 as IPNS_MODEL_SHA256,
    decode_job as decode_ipns_job,
    decode_model as decode_ipns_model,
)
from fold_1dz9_p450cam_hem_fixture_data import (  # noqa: E402
    JOB_FILENAME as P450_JOB_FILENAME,
    JOB_SHA256 as P450_JOB_SHA256,
    MODEL_FILENAME as P450_MODEL_FILENAME,
    MODEL_SHA256 as P450_MODEL_SHA256,
    decode_job as decode_p450_job,
    decode_model as decode_p450_model,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(
    directory: Path,
    model_name: str,
    model_bytes: bytes,
    model_hash: str,
    job_name: str,
    job_bytes: bytes,
    job_hash: str,
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    model = directory / model_name
    job = directory / job_name
    model.write_bytes(model_bytes)
    job.write_bytes(job_bytes)
    assert sha256(model) == model_hash
    assert sha256(job) == job_hash
    assert model.read_text(encoding="utf-8").startswith(
        "# By using this file you agree to the legally binding terms of use"
    )
    return model, job


def run_cli(config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "classify_structure.py"), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )


def classify(tmp_path: Path, model: Path, job: Path) -> tuple[dict, dict]:
    output = tmp_path / "output"
    output.mkdir(parents=True, exist_ok=True)
    config = tmp_path / "classification_config.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "structure": {
                    "path": str(model),
                    "sha256": sha256(model),
                    "source_format": "AF3_CIF",
                    "selected_model_id": "1",
                },
                "classification": {"mode": "REGISTRY"},
                "sequence_references": [
                    {
                        "type": "AF3_INPUT_JSON",
                        "path": str(job),
                        "sha256": sha256(job),
                    }
                ],
                "ccd": {
                    "project_snapshot_dir": str(output / "reference_data/ccd"),
                    "shared_cache_path": str(tmp_path / "shared_ccd_cache"),
                    "retrieval_policy": "DOWNLOAD_MISSING",
                    "timeout_seconds": 60,
                },
                "output": {
                    "observations_path": str(output / "classification_observations.yaml"),
                    "reference_manifest_path": str(output / "reference_manifest.yaml"),
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    completed = run_cli(config)
    assert completed.returncode == 0, completed.stderr
    observations = yaml.safe_load(
        (output / "classification_observations.yaml").read_text(encoding="utf-8")
    )
    manifest = yaml.safe_load(
        (output / "reference_manifest.yaml").read_text(encoding="utf-8")
    )
    return observations, manifest


@pytest.mark.parametrize(
    ("label", "model_name", "model_bytes", "model_hash", "job_name", "job_bytes", "job_hash", "nonpolymer"),
    [
        (
            "1BK0_IPNS_FE",
            IPNS_MODEL_FILENAME,
            decode_ipns_model(),
            IPNS_MODEL_SHA256,
            IPNS_JOB_FILENAME,
            decode_ipns_job(),
            IPNS_JOB_SHA256,
            "FE",
        ),
        (
            "1DZ9_P450CAM_HEM",
            P450_MODEL_FILENAME,
            decode_p450_model(),
            P450_MODEL_SHA256,
            P450_JOB_FILENAME,
            decode_p450_job(),
            P450_JOB_SHA256,
            "HEM",
        ),
    ],
)
def test_real_alphafold_server_model_and_job_request(
    tmp_path: Path,
    label: str,
    model_name: str,
    model_bytes: bytes,
    model_hash: str,
    job_name: str,
    job_bytes: bytes,
    job_hash: str,
    nonpolymer: str,
) -> None:
    model, job = materialize(
        tmp_path / label,
        model_name,
        model_bytes,
        model_hash,
        job_name,
        job_bytes,
        job_hash,
    )
    observations, manifest = classify(tmp_path / f"run_{label}", model, job)

    assert observations["input"]["source_format"] == "AF3_CIF"
    assert observations["input"]["selected_model_id"] == "1"
    assert observations["missing_residue_checks"] == [
        {
            "chain_index": 1,
            "source_chain_id": "A",
            "status": "NO_MISSING_RESIDUES",
            "evidence_types": ["AF3_INPUT_SEQUENCE", "AF3_OUTPUT_COORDINATES"],
            "missing_residue_count": 0,
            "reason": None,
        }
    ]
    assert not any(
        item["issue_type"] == "SEQUENCE_REFERENCE_CONFLICT"
        for item in observations["unresolved_observations"]
    )
    assert any(
        group.get("source_chain_id") == "B"
        and group.get("residue_name") == nonpolymer
        for group in observations["chain_groups"]
    )
    assert manifest["sequence_references"] == [
        {
            "path": str(job.resolve()),
            "sha256": job_hash,
            "status": "LOADED",
            "reference_type": "AF3_INPUT_JSON",
        }
    ]

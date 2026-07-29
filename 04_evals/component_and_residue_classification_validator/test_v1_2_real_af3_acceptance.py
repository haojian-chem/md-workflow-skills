from __future__ import annotations

import base64
import gzip
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
MANIFEST = yaml.safe_load((FIXTURES / "fixture_manifest.yaml").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(directory: Path, fixture: dict) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    encoded = "".join(
        (FIXTURES / name).read_text(encoding="ascii").strip()
        for name in fixture["model_chunks"]
    )
    model_bytes = gzip.decompress(base64.b64decode(encoded))
    model = directory / fixture["model_filename"]
    job_source = FIXTURES / fixture["job_filename"]
    job = directory / fixture["job_filename"]
    model.write_bytes(model_bytes)
    job.write_bytes(job_source.read_bytes())
    assert model.stat().st_size == fixture["model_size_bytes"]
    assert job.stat().st_size == fixture["job_size_bytes"]
    assert sha256(model) == fixture["model_sha256"]
    assert sha256(job) == fixture["job_sha256"]
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
    reference_manifest = yaml.safe_load(
        (output / "reference_manifest.yaml").read_text(encoding="utf-8")
    )
    return observations, reference_manifest


@pytest.mark.parametrize("fixture", MANIFEST["fixtures"], ids=lambda item: item["label"])
def test_real_alphafold_server_model_and_job_request(
    tmp_path: Path,
    fixture: dict,
) -> None:
    model, job = materialize(tmp_path / fixture["label"], fixture)
    observations, reference_manifest = classify(
        tmp_path / f"run_{fixture['label']}",
        model,
        job,
    )

    polymer_chain = fixture["expected_polymer_chain_id"]
    nonpolymer_chain = fixture["expected_nonpolymer_chain_id"]
    nonpolymer_residue = fixture["expected_nonpolymer_residue"]
    assert observations["input"]["source_format"] == "AF3_CIF"
    assert observations["input"]["selected_model_id"] == "1"
    assert observations["missing_residue_checks"] == [
        {
            "chain_index": 1,
            "source_chain_id": polymer_chain,
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
        group.get("source_chain_id") == nonpolymer_chain
        and group.get("residue_name") == nonpolymer_residue
        for group in observations["chain_groups"]
    )
    assert reference_manifest["sequence_references"] == [
        {
            "path": str(job.resolve()),
            "sha256": fixture["job_sha256"],
            "status": "LOADED",
            "reference_type": "AF3_INPUT_JSON",
        }
    ]

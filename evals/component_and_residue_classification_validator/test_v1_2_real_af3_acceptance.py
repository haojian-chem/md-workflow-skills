from __future__ import annotations

import base64
import hashlib
import lzma
import subprocess
import sys
from pathlib import Path

import gemmi
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures/real_af3"
MANIFEST = yaml.safe_load((FIXTURES / "fixture_manifest.yaml").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(directory: Path, fixture: dict) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    encoded = "".join((FIXTURES / name).read_text(encoding="ascii").strip() for name in fixture["model_chunks"])
    model_bytes = lzma.decompress(base64.b64decode(encoded, validate=True))
    model = directory / fixture["model_filename"]
    job = directory / fixture["job_filename"]
    job_bytes = (FIXTURES / fixture["job_filename"]).read_bytes()
    if MANIFEST["job_request_transport"] == "utf8_text_remove_one_trailing_lf":
        job_bytes = job_bytes[:-1]
    model.write_bytes(model_bytes)
    job.write_bytes(job_bytes)
    assert sha256(model) == fixture["model_sha256"]
    assert sha256(job) == fixture["job_sha256"]
    return model, job


def classify(tmp_path: Path, model: Path, job: Path) -> tuple[dict, dict]:
    output = tmp_path / "output"
    output.mkdir(parents=True, exist_ok=True)
    config = tmp_path / "classification_config.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "structure": {"path": str(model), "sha256": sha256(model), "source_format": "AF3_CIF", "selected_model_id": "1"},
                "classification": {"mode": "REGISTRY"},
                "sequence_references": [{"type": "AF3_INPUT_JSON", "path": str(job), "sha256": sha256(job)}],
                "ccd": {"additional_library_paths": []},
                "output": {
                    "observations_path": str(output / "classification_observations.yaml"),
                    "reference_manifest_path": str(output / "reference_manifest.yaml"),
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "classify_structure.py"), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return (
        yaml.safe_load((output / "classification_observations.yaml").read_text(encoding="utf-8")),
        yaml.safe_load((output / "reference_manifest.yaml").read_text(encoding="utf-8")),
    )


@pytest.mark.parametrize("fixture", MANIFEST["fixtures"], ids=lambda item: item["label"])
def test_real_alphafold_server_model_and_job_request(tmp_path: Path, fixture: dict) -> None:
    model, job = materialize(tmp_path / fixture["label"], fixture)
    source_structure = gemmi.read_structure(str(model))
    assert any(
        residue.name == fixture["expected_nonpolymer_residue"]
        for chain in source_structure[0]
        if chain.name == fixture["expected_nonpolymer_chain_id"]
        for residue in chain
    )
    observations, manifest = classify(tmp_path / f"run_{fixture['label']}", model, job)
    assert observations["input"]["source_format"] == "AF3_CIF"
    assert observations["missing_residue_checks"] == [
        {
            "chain_index": 1,
            "source_chain_id": fixture["expected_polymer_chain_id"],
            "status": "NO_MISSING_RESIDUES",
            "evidence_types": ["AF3_INPUT_SEQUENCE", "AF3_OUTPUT_COORDINATES"],
            "missing_residue_count": 0,
            "reason": None,
        }
    ]
    assert any(
        group.get("residue_name") == fixture["expected_nonpolymer_residue"]
        and group["group_type"] == fixture["expected_nonpolymer_group_type"]
        for group in observations["chain_groups"]
    )
    assert manifest["sequence_references"] == [
        {
            "path": str(job.resolve()),
            "sha256": fixture["job_sha256"],
            "status": "LOADED",
            "reference_type": "AF3_INPUT_JSON",
        }
    ]

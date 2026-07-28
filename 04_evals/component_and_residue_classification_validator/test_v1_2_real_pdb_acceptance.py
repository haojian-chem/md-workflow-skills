from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
REAL_PDB_DIR = Path(os.environ.get("V1_2_REAL_PDB_DIR", ""))

pytestmark = pytest.mark.skipif(
    not REAL_PDB_DIR.is_dir(),
    reason="set V1_2_REAL_PDB_DIR to the directory containing downloaded RCSB PDB files",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        text=True,
        capture_output=True,
        check=False,
    )


def run_script(name: str, config: Path) -> subprocess.CompletedProcess[str]:
    return run_command([sys.executable, str(SCRIPTS / name), "--config", str(config)])


def assert_pdb_entry(path: Path, pdb_id: str) -> None:
    assert path.is_file() and path.stat().st_size > 0
    header = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    assert header.startswith("HEADER")
    assert header[62:66].strip().upper() == pdb_id


def inspect_model_scope(structure: Path, output: Path) -> dict:
    completed = run_command(
        [
            sys.executable,
            str(SCRIPTS / "inspect_model_scope.py"),
            "--structure",
            str(structure),
            "--structure-sha256",
            digest(structure),
            "--source-format",
            "PDB",
            "--output",
            str(output),
        ]
    )
    assert completed.returncode == 0, completed.stderr
    return yaml.safe_load(output.read_text(encoding="utf-8"))


def classify_pdb(
    structure: Path,
    output_dir: Path,
    shared_cache: Path,
) -> tuple[dict, dict, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    observations_path = output_dir / "classification_observations.yaml"
    manifest_path = output_dir / "reference_manifest.yaml"
    config_path = output_dir / "classification_config.yaml"
    write_yaml(
        config_path,
        {
            "structure": {
                "path": str(structure),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "classification": {"mode": "REGISTRY"},
            "ccd": {
                "project_snapshot_dir": str(output_dir / "reference_data" / "ccd"),
                "shared_cache_path": str(shared_cache),
                "retrieval_policy": "DOWNLOAD_MISSING",
                "timeout_seconds": 60,
            },
            "output": {
                "observations_path": str(observations_path),
                "reference_manifest_path": str(manifest_path),
            },
        },
    )
    completed = run_script("classify_structure.py", config_path)
    assert completed.returncode == 0, completed.stderr
    observations = yaml.safe_load(observations_path.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return observations, manifest, observations_path


def ccd_entry(manifest: dict, component_id: str) -> dict:
    return next(
        entry
        for entry in manifest["ccd_components"]
        if entry["component_id"] == component_id
    )


@pytest.fixture(scope="session")
def shared_ccd_cache(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("real_pdb_ccd_cache")
    return path


def test_real_1vns_missing_residues_and_so4_ccd(
    tmp_path: Path,
    shared_ccd_cache: Path,
) -> None:
    structure = REAL_PDB_DIR / "1VNS.pdb"
    assert_pdb_entry(structure, "1VNS")

    model_scope = inspect_model_scope(structure, tmp_path / "model_scope.yaml")
    assert model_scope["model_count"] == 1
    assert model_scope["selection"] == {
        "status": "AUTO_SELECTED",
        "selected_model_id": "1",
    }
    assert model_scope["models"][0]["residue_count"] > 500

    observations, manifest, _observations_path = classify_pdb(
        structure,
        tmp_path / "classification",
        shared_ccd_cache,
    )
    missing_checks = observations["missing_residue_checks"]
    assert any(
        check["status"] == "MISSING_RESIDUES_FOUND"
        and check["missing_residue_count"] > 0
        for check in missing_checks
    )
    assert observations["summary"]["missing_expected_residue_count"] > 0
    missing_records = [
        record
        for record in observations["residue_records"]
        if record["presence_status"] == "MISSING_EXPECTED"
    ]
    assert missing_records
    assert all(record["source_resid"]["number"] for record in missing_records)

    sulfate = ccd_entry(manifest, "SO4")
    assert sulfate["validation"]["status"] == "VALID"
    assert sulfate["project_snapshot"]["status"] == "AVAILABLE"
    assert Path(sulfate["project_snapshot"]["path"]).is_file()


def test_real_1a6m_altloc_heme_ccd_and_explicit_coordination(
    tmp_path: Path,
    shared_ccd_cache: Path,
) -> None:
    structure = REAL_PDB_DIR / "1A6M.pdb"
    assert_pdb_entry(structure, "1A6M")

    observations, manifest, observations_path = classify_pdb(
        structure,
        tmp_path / "classification",
        shared_ccd_cache,
    )
    assert observations["summary"]["multiple_conformation_residue_count"] > 0
    assert any(
        record["conformation_observation"]["status"] == "MULTIPLE_CONFORMATIONS"
        and record["heavy_atom_check"]["reason"] == "MULTIPLE_CONFORMATIONS_PRESENT"
        for record in observations["residue_records"]
    )

    heme = ccd_entry(manifest, "HEM")
    assert heme["validation"]["status"] == "VALID"
    assert Path(heme["project_snapshot"]["path"]).is_file()

    definitions = tmp_path / "possible_coordination.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_coordination": [
                {
                    "label": "REAL_1A6M_HEM_FE_HIS_NE2",
                    "metal": {
                        "residue_name": "HEM",
                        "atom_name": "FE",
                        "element": "Fe",
                    },
                    "donor": {
                        "residue_name": "HIS",
                        "atom_name": "NE2",
                        "element": "N",
                    },
                    "distance_range_angstrom": {
                        "minimum": 1.7,
                        "maximum": 2.7,
                    },
                    "topology_effect": {
                        "promote_nonstandard_to_linked": True,
                    },
                }
            ],
        },
    )
    result_path = tmp_path / "possible_coordination_result.yaml"
    config = tmp_path / "coordination_config.yaml"
    write_yaml(
        config,
        {
            "structure": {
                "path": str(structure),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "possible_coordination": {
                "path": str(definitions),
                "sha256": digest(definitions),
            },
            "classification_observations": {
                "path": str(observations_path),
                "sha256": digest(observations_path),
            },
            "output": {"path": str(result_path)},
        },
    )
    completed = run_script("check_possible_coordination.py", config)
    assert completed.returncode == 0, completed.stderr
    result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    confirmed = [
        pair
        for pair in result["definition_results"][0]["pair_results"]
        if pair["status"] == "CONFIRMED_BY_STRUCTURE"
    ]
    assert confirmed
    pair = confirmed[0]
    assert pair["explicit_coordination"]["status"] == "PRESENT"
    assert pair["explicit_coordination"]["relation_type"] == "METAL_COORDINATION"
    assert pair["explicit_coordination"]["source_type"] in {
        "MMCIF_STRUCT_CONN_OR_PDB_LINK",
        "PDB_CONECT",
        "MMCIF_STRUCT_CONN_OR_PDB_LINK,PDB_CONECT",
    }
    assert pair["topology_effect_evaluation"]["application_status"] == "ELIGIBLE"


def test_real_1crn_ssbond_is_confirmed_by_structure(
    tmp_path: Path,
    shared_ccd_cache: Path,
) -> None:
    structure = REAL_PDB_DIR / "1CRN.pdb"
    assert_pdb_entry(structure, "1CRN")

    observations, _manifest, observations_path = classify_pdb(
        structure,
        tmp_path / "classification",
        shared_ccd_cache,
    )
    assert observations["summary"]["observed_residue_count"] == 46

    definitions = tmp_path / "possible_connections.yaml"
    write_yaml(
        definitions,
        {
            "schema_version": "1.0",
            "possible_connections": [
                {
                    "label": "REAL_1CRN_CYS_DISULFIDE",
                    "partner_1": {
                        "residue_name": "CYS",
                        "atom_name": "SG",
                    },
                    "partner_2": {
                        "residue_name": "CYS",
                        "atom_name": "SG",
                    },
                    "distance_range_angstrom": {
                        "minimum": 1.8,
                        "maximum": 2.3,
                    },
                }
            ],
        },
    )
    result_path = tmp_path / "possible_connections_result.yaml"
    config = tmp_path / "connection_config.yaml"
    write_yaml(
        config,
        {
            "structure": {
                "path": str(structure),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "possible_connections": {
                "path": str(definitions),
                "sha256": digest(definitions),
            },
            "classification_observations": {
                "path": str(observations_path),
                "sha256": digest(observations_path),
            },
            "output": {"path": str(result_path)},
        },
    )
    completed = run_script("check_possible_connections.py", config)
    assert completed.returncode == 0, completed.stderr
    result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    confirmed = [
        pair
        for pair in result["definition_results"][0]["pair_results"]
        if pair["status"] == "CONFIRMED_BY_STRUCTURE"
    ]
    assert len(confirmed) == 3
    assert all(
        pair["explicit_connection"]["relation_type"] == "DISULFIDE"
        for pair in confirmed
    )
    assert all(
        pair["topology_effect_candidate"]["applicable"] is True
        for pair in confirmed
    )

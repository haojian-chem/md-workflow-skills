from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def test_polymer_entity_keeps_polymer_chain_index_when_classification_conflicts(
    tmp_path: Path,
) -> None:
    structure = tmp_path / "polymer_conflict.pdb"
    structure.write_text(
        """SEQRES   1 A    1  ALA
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       1.400   1.500   0.000  1.00 20.00           C
END
""",
        encoding="utf-8",
    )
    project = tmp_path / "project_residue_definitions.yaml"
    write_yaml(
        project,
        {
            "schema_version": "1.0",
            "residue_definitions": [
                {
                    "residue_name": "ALA",
                    "polymer_class": "NONPOLYMER",
                    "topology_class": "INDEPENDENT_NONSTANDARD",
                    "ccd_id": "ALA",
                }
            ],
        },
    )
    observations_path = tmp_path / "classification_observations.yaml"
    manifest_path = tmp_path / "reference_manifest.yaml"
    config = {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "project_residue_definitions": {
            "path": str(project),
            "sha256": digest(project),
        },
        "ccd": {"retrieval_policy": "CACHE_ONLY"},
        "output": {
            "observations_path": str(observations_path),
            "reference_manifest_path": str(manifest_path),
        },
    }

    observations, _manifest, *_ = execute_classification(config, SCRIPTS)
    record = observations["residue_records"][0]
    assert record["classification_observation"]["resolution_status"] == "CONFLICT"
    assert observations["unresolved_observations"][0]["issue_type"] == "PROJECT_REGISTRY_CLASSIFICATION_CONFLICT"
    assert observations["chain_groups"] == [
        {
            "chain_index": 1,
            "grouping_status": "BASELINE",
            "group_type": "POLYMER_CHAIN",
            "source_chain_id": "A",
            "entity_id": "1",
            "instance_count": 1,
            "source_associations": [],
        }
    ]
    assert record["chain_index"] == 1

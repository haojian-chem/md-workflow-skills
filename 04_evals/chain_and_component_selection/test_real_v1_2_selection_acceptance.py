from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import gemmi
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASSIFICATION = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
CLASSIFICATION_SCRIPTS = CLASSIFICATION / "scripts"
SELECTION = REPO_ROOT / "02_operations/chain_and_component_selection"
SELECTION_VALIDATOR = REPO_ROOT / "02_validators/chain_and_component_selection_validator"
REAL_PDB_DIR = Path(os.environ.get("CHAIN_SELECTION_REAL_PDB_DIR", ""))

pytestmark = pytest.mark.skipif(
    not REAL_PDB_DIR.is_dir(),
    reason="set CHAIN_SELECTION_REAL_PDB_DIR to downloaded official PDB files",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False)


def run_classification_script(name: str, config: Path) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, str(CLASSIFICATION_SCRIPTS / name), "--config", str(config)])


def inspect_model_scope(structure: Path, output: Path) -> None:
    completed = run(
        [
            sys.executable,
            str(CLASSIFICATION_SCRIPTS / "inspect_model_scope.py"),
            "--structure", str(structure),
            "--structure-sha256", digest(structure),
            "--source-format", "PDB",
            "--output", str(output),
        ]
    )
    assert completed.returncode == 0, completed.stderr


def not_performed_relation_result(structure: Path, observations: Path) -> dict:
    return {
        "schema_version": "1.0",
        "status": "NOT_PERFORMED",
        "reason": "DEFINITION_FILE_NOT_PROVIDED",
        "input": {
            "structure_path": str(structure.resolve()),
            "structure_sha256": digest(structure),
            "selected_model_id": "1",
            "definition_path": None,
            "definition_sha256": None,
            "observations_path": str(observations.resolve()),
            "observations_sha256": digest(observations),
        },
        "definition_results": [],
    }


def build_real_classification(
    structure: Path,
    output_dir: Path,
    shared_ccd_cache: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_scope = output_dir / "model_scope.yaml"
    inspect_model_scope(structure, model_scope)

    observations = output_dir / "classification_observations.yaml"
    reference_manifest = output_dir / "reference_manifest.yaml"
    classify_config = output_dir / "classification_config.yaml"
    write_yaml(
        classify_config,
        {
            "structure": {
                "path": str(structure.resolve()),
                "sha256": digest(structure),
                "source_format": "PDB",
                "selected_model_id": "1",
            },
            "classification": {"mode": "REGISTRY"},
            "ccd": {
                "project_snapshot_dir": str(output_dir / "reference_data" / "ccd"),
                "shared_cache_path": str(shared_ccd_cache),
                "retrieval_policy": "DOWNLOAD_MISSING",
                "timeout_seconds": 60,
            },
            "output": {
                "observations_path": str(observations),
                "reference_manifest_path": str(reference_manifest),
            },
        },
    )
    completed = run_classification_script("classify_structure.py", classify_config)
    assert completed.returncode == 0, completed.stderr

    connections = output_dir / "possible_connections_result.yaml"
    coordination = output_dir / "possible_coordination_result.yaml"
    write_yaml(connections, not_performed_relation_result(structure, observations))
    write_yaml(coordination, not_performed_relation_result(structure, observations))

    confirmation_requests = output_dir / "confirmation_requests.yaml"
    classification_result = output_dir / "classification_result.yaml"
    classification_report = output_dir / "classification_report.md"
    builder_config = output_dir / "builder_config.yaml"
    write_yaml(
        builder_config,
        {
            "model_scope": {"path": str(model_scope), "sha256": digest(model_scope)},
            "classification_observations": {"path": str(observations), "sha256": digest(observations)},
            "reference_manifest": {"path": str(reference_manifest), "sha256": digest(reference_manifest)},
            "possible_connections_result": {"path": str(connections), "sha256": digest(connections)},
            "possible_coordination_result": {"path": str(coordination), "sha256": digest(coordination)},
            "output": {
                "confirmation_requests_path": str(confirmation_requests),
                "classification_result_path": str(classification_result),
                "classification_report_path": str(classification_report),
            },
        },
    )
    completed = run_classification_script("build_classification_result.py", builder_config)
    assert completed.returncode == 0, completed.stderr
    result = yaml.safe_load(classification_result.read_text(encoding="utf-8"))
    assert result["result_status"] == "COMPLETE"
    assert result["unresolved_items"] == []
    return classification_result


def execute_selection(
    structure: Path,
    classification_result: Path,
    output_dir: Path,
    selected_component_ids: list[str],
    output_format: str,
) -> tuple[dict, dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_structure = output_dir / ("selected_structure.pdb" if output_format == "PDB" else "selected_structure.cif")
    spec = output_dir / "selection_spec.yaml"
    write_yaml(
        spec,
        {
            "schema_version": 1,
            "task_id": f"real-selection-{structure.stem.lower()}",
            "workstream_id": "structure-preparation",
            "source_structure": {"path": str(structure.resolve()), "sha256": digest(structure)},
            "classification_result": {"path": str(classification_result.resolve()), "sha256": digest(classification_result)},
            "selected_model_id": "1",
            "selected_component_ids": selected_component_ids,
            "resolved_decision_ids": [],
            "output": {"path": str(selected_structure), "format": output_format},
            "policies": {
                "selection_level": "COMPONENT_ONLY",
                "covalent_closure": "REQUIRE_COMPLETE",
                "preserve_all_atoms": True,
                "preserve_all_altlocs": True,
                "preserve_source_order": True,
                "preserve_coordinates": True,
            },
            "notes": ["real v1.2 to v1.3 acceptance"],
        },
    )
    manifest = output_dir / "selection_manifest.yaml"
    mapping = output_dir / "selection_mapping.yaml"
    operation_report = output_dir / "operation_report.yaml"
    operation_config = output_dir / "operation_config.yaml"
    write_yaml(
        operation_config,
        {
            "schema_version": 1,
            "selection_spec_path": str(spec),
            "classification_result_path": str(classification_result),
            "output": {
                "manifest_path": str(manifest),
                "mapping_path": str(mapping),
                "report_path": str(operation_report),
            },
        },
    )
    completed = run([sys.executable, str(SELECTION / "scripts/select_structure.py"), "--config", str(operation_config)])
    assert completed.returncode == 0, completed.stderr

    validation_report = output_dir / "validation_report.yaml"
    validation_result = output_dir / "validation_result.yaml"
    validator_config = output_dir / "validator_config.yaml"
    write_yaml(
        validator_config,
        {
            "schema_version": 1,
            "selection_spec_path": str(spec),
            "classification_result_path": str(classification_result),
            "candidate_structure_path": str(selected_structure),
            "selection_manifest_path": str(manifest),
            "selection_mapping_path": str(mapping),
            "operation_report_path": str(operation_report),
            "validation_report_path": str(validation_report),
            "validation_result_path": str(validation_result),
        },
    )
    completed = run([sys.executable, str(SELECTION_VALIDATOR / "scripts/validate_selection.py"), "--config", str(validator_config)])
    assert completed.returncode == 0, completed.stderr
    return (
        yaml.safe_load(manifest.read_text(encoding="utf-8")),
        yaml.safe_load(validation_result.read_text(encoding="utf-8")),
    )


@pytest.fixture(scope="session")
def shared_ccd_cache(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("selection_real_ccd_cache")


def test_real_1vns_selects_polymer_and_excludes_solvent_and_sulfate(
    tmp_path: Path,
    shared_ccd_cache: Path,
) -> None:
    structure = REAL_PDB_DIR / "1VNS.pdb"
    classification_path = build_real_classification(structure, tmp_path / "classification", shared_ccd_cache)
    classification = yaml.safe_load(classification_path.read_text(encoding="utf-8"))
    polymer_ids = [group["component_id"] for group in classification["chain_groups"] if group["group_type"] == "POLYMER_CHAIN"]
    assert polymer_ids
    manifest, validation = execute_selection(
        structure,
        classification_path,
        tmp_path / "selection",
        polymer_ids,
        "MMCIF",
    )
    assert validation["outcome_code"] == "SELECTION_VALIDATED"
    assert manifest["counts"]["selected_residue_count"] > 400
    assert manifest["counts"]["excluded_residue_count"] > 0
    output = gemmi.read_structure(str(tmp_path / "selection/selected_structure.cif"))
    names = {residue.name for chain in output[0] for residue in chain}
    assert "HOH" not in names
    assert "SO4" not in names


def test_real_1a6m_selects_protein_and_heme_with_altlocs(
    tmp_path: Path,
    shared_ccd_cache: Path,
) -> None:
    structure = REAL_PDB_DIR / "1A6M.pdb"
    classification_path = build_real_classification(structure, tmp_path / "classification", shared_ccd_cache)
    classification = yaml.safe_load(classification_path.read_text(encoding="utf-8"))
    polymer_ids = {group["component_id"] for group in classification["chain_groups"] if group["group_type"] == "POLYMER_CHAIN"}
    heme_ids = {record["component_id"] for record in classification["residue_records"] if record["residue_name"] == "HEM" and record["presence_status"] == "OBSERVED"}
    selected = sorted(polymer_ids | heme_ids)
    assert polymer_ids and heme_ids
    manifest, validation = execute_selection(
        structure,
        classification_path,
        tmp_path / "selection",
        selected,
        "MMCIF",
    )
    assert validation["outcome_code"] == "SELECTION_VALIDATED"
    assert manifest["cross_boundary_coordination_relations"] == []
    output = gemmi.read_structure(str(tmp_path / "selection/selected_structure.cif"))
    assert any(residue.name == "HEM" for chain in output[0] for residue in chain)
    assert any(str(atom.altloc).strip() not in {"", "\x00"} for chain in output[0] for residue in chain for atom in residue)


def test_real_1crn_all_components_round_trip_to_pdb(
    tmp_path: Path,
    shared_ccd_cache: Path,
) -> None:
    structure = REAL_PDB_DIR / "1CRN.pdb"
    classification_path = build_real_classification(structure, tmp_path / "classification", shared_ccd_cache)
    classification = yaml.safe_load(classification_path.read_text(encoding="utf-8"))
    selected = sorted(group["component_id"] for group in classification["chain_groups"])
    manifest, validation = execute_selection(
        structure,
        classification_path,
        tmp_path / "selection",
        selected,
        "PDB",
    )
    assert validation["outcome_code"] == "SELECTION_VALIDATED_WITH_WARNINGS"
    assert manifest["counts"]["excluded_residue_count"] == 0
    output = gemmi.read_structure(str(tmp_path / "selection/selected_structure.pdb"))
    assert sum(1 for chain in output[0] for _residue in chain) == 46

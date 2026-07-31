from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import gemmi
import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATION = REPO_ROOT / "02_operations/chain_and_component_selection"
VALIDATOR = REPO_ROOT / "02_validators/chain_and_component_selection_validator"
SELECT_SCRIPT = OPERATION / "scripts/select_structure.py"
VALIDATE_SCRIPT = VALIDATOR / "scripts/validate_selection.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def run_script(script: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--config", str(config)],
        text=True,
        capture_output=True,
        check=False,
    )


def source_identity(chain: str, number: int, name: str) -> dict:
    return {
        "source_model_id": "1",
        "source_chain_id": chain,
        "source_resid": {"number": str(number), "insertion_code": None},
        "source_residue_name": name,
    }


def current_identity(chain: str, number: int, name: str) -> dict:
    return {
        "current_model_id": "1",
        "current_chain_id": chain,
        "current_resid": {"number": str(number), "insertion_code": None},
        "current_residue_name": name,
    }


def residue_record(
    residue_id: str,
    component_id: str,
    chain_index: int,
    chain: str,
    number: int,
    name: str,
    polymer_class: str,
    topology_class: str,
    *,
    altloc_ids: list[str] | None = None,
) -> dict:
    return {
        "residue_id": residue_id,
        "component_id": component_id,
        "source_identity": source_identity(chain, number, name),
        "current_identity": current_identity(chain, number, name),
        "chain_index": chain_index,
        "source_chain_id": chain,
        "source_resid": {"number": str(number), "insertion_code": None},
        "residue_name": name,
        "presence_status": "OBSERVED",
        "sequence_position": None,
        "classification": {
            "polymer_class": polymer_class,
            "topology_class": topology_class,
            "resolution_status": "RESOLVED",
            "evidence": ["selection fixture"],
        },
        "conformation": {
            "status": "SINGLE_CONFORMATION",
            "altloc_ids": altloc_ids or [],
        },
        "heavy_atom_check": {
            "execution_status": "NOT_PERFORMED",
            "findings": [],
            "reference_type": None,
            "reference_name": None,
            "exact_comparison": None,
            "atom_name_mapping_candidates": [],
            "mapping_resolution_status": "NOT_APPLICABLE",
            "effective_comparison": None,
            "reason": None,
            "status": "NOT_PERFORMED",
            "missing_atoms": [],
            "unexpected_atoms": [],
        },
    }


def endpoint(
    endpoint_id: str,
    residue_id: str,
    component_id: str,
    chain_index: int,
    chain: str,
    number: int,
    name: str,
    atom_name: str,
) -> dict:
    source = {
        **source_identity(chain, number, name),
        "source_atom_name": atom_name,
        "source_altloc_id": None,
    }
    current = {
        **current_identity(chain, number, name),
        "current_atom_name": atom_name,
        "current_altloc_id": None,
    }
    return {
        "endpoint_id": endpoint_id,
        "residue_id": residue_id,
        "component_id": component_id,
        "source_identity": source,
        "current_identity": current,
        "chain_index": chain_index,
        "source_chain_id": chain,
        "source_resid": {"number": str(number), "insertion_code": None},
        "residue_name": name,
        "atom_name": atom_name,
        "altloc_id": None,
    }


def make_structure(path: Path, *, format_name: str = "PDB", polymer_chain: str = "A") -> None:
    structure = gemmi.Structure()
    structure.name = "selection_fixture"
    structure.add_model(gemmi.Model(1))
    model = structure[0]
    serial = 1
    definitions = [
        (polymer_chain, [(1, "CYS", [("N", "N", None), ("CA", "C", None), ("SG", "S", None)]),
                         (2, "GLY", [("N", "N", None), ("CA", "C", "A"), ("CA", "C", "B")])]),
        ("B", [(10, "LIG", [("C1", "C", None), ("O1", "O", None)])]),
        ("W", [(1, "HOH", [("O", "O", None)])]),
        ("M", [(1, "ZN", [("ZN", "Zn", None)])]),
    ]
    for chain_name, residues in definitions:
        model.add_chain(gemmi.Chain(chain_name))
        chain = model[-1]
        for number, residue_name, atoms in residues:
            residue = gemmi.Residue()
            residue.name = residue_name
            residue.seqid = gemmi.SeqId(number, " ")
            residue.het_flag = "A" if chain_name == polymer_chain else "H"
            for atom_index, (atom_name, element, altloc) in enumerate(atoms):
                atom = gemmi.Atom()
                atom.name = atom_name
                atom.element = gemmi.Element(element)
                atom.pos = gemmi.Position(float(number + atom_index), float(atom_index), 0.25)
                atom.occ = 0.75 if altloc else 1.0
                atom.b_iso = 20.0 + atom_index
                atom.serial = serial
                serial += 1
                if altloc:
                    atom.altloc = altloc
                residue.add_atom(atom)
            chain.add_residue(residue)
    if format_name == "PDB":
        structure.write_pdb(str(path))
    else:
        structure.make_mmcif_document().write_file(str(path))


def chain_group(component_id: str, chain_index: int, group_type: str, residue_ids: list[str], *, chain: str | None, residue_name: str | None = None) -> dict:
    output = {
        "component_id": component_id,
        "residue_ids": residue_ids,
        "missing_residue_ids": [],
        "chain_index": chain_index,
        "grouping_status": "FINAL",
        "group_type": group_type,
        "source_chain_id": chain,
        "entity_id": None,
        "instance_count": len(residue_ids),
        "linked_polymer_chain_indices": [],
        "source_associations": [],
    }
    if residue_name is not None:
        output["residue_name"] = residue_name
    return output


def make_classification(path: Path, source: Path, *, source_format: str, polymer_chain: str = "A") -> None:
    classification = {
        "schema_version": "1.0",
        "result_status": "COMPLETE",
        "selected_model_id": "1",
        "classification_mode": "REGISTRY",
        "source_structure": {
            "path": str(source.resolve()),
            "sha256": sha256(source),
            "source_format": source_format,
        },
        "source_hashes": {
            "model_scope": "0" * 64,
            "classification_observations": "1" * 64,
            "reference_manifest": "2" * 64,
            "possible_connections_result": "3" * 64,
            "possible_coordination_result": "4" * 64,
            "confirmation_requests": "5" * 64,
        },
        "chain_groups": [
            chain_group("compA", 1, "POLYMER_CHAIN", ["rA1", "rA2"], chain=polymer_chain),
            chain_group("compB", 2, "INDEPENDENT_COMPONENT", ["rB10"], chain="B", residue_name="LIG"),
            chain_group("compW", 3, "SOLVENT_GROUP", ["rW1"], chain=None, residue_name="HOH"),
            chain_group("compM", 4, "ION_GROUP", ["rM1"], chain=None, residue_name="ZN"),
        ],
        "residue_records": [
            residue_record("rA1", "compA", 1, polymer_chain, 1, "CYS", "POLYMER", "STANDARD_RESIDUE"),
            residue_record("rA2", "compA", 1, polymer_chain, 2, "GLY", "POLYMER", "STANDARD_RESIDUE", altloc_ids=["A", "B"]),
            residue_record("rB10", "compB", 2, "B", 10, "LIG", "NONPOLYMER", "INDEPENDENT_NONSTANDARD"),
            residue_record("rW1", "compW", 3, "W", 1, "HOH", "WATER", "SOLVENT_COMPONENT"),
            residue_record("rM1", "compM", 4, "M", 1, "ZN", "NONPOLYMER", "ION_COMPONENT"),
        ],
        "confirmed_relations": {
            "covalent_connections": [
                {
                    "relation_id": "relCov",
                    "relation_type": "COVALENT_CONNECTION",
                    "endpoint_1": endpoint("epCov1", "rA1", "compA", 1, polymer_chain, 1, "CYS", "SG"),
                    "endpoint_2": endpoint("epCov2", "rB10", "compB", 2, "B", 10, "LIG", "C1"),
                    "evidence_status": "CONFIRMED_BY_USER",
                    "topology_effect_applied": False,
                }
            ],
            "metal_coordination": [
                {
                    "relation_id": "relMet",
                    "relation_type": "METAL_COORDINATION",
                    "endpoint_1": endpoint("epMet1", "rA1", "compA", 1, polymer_chain, 1, "CYS", "SG"),
                    "endpoint_2": endpoint("epMet2", "rM1", "compM", 4, "M", 1, "ZN", "ZN"),
                    "evidence_status": "CONFIRMED_BY_USER",
                    "topology_effect_applied": False,
                }
            ],
        },
        "rejected_candidates": {
            "covalent_connections": [
                {
                    "relation_id": "relCandidate",
                    "relation_type": "COVALENT_CONNECTION",
                    "endpoint_1": endpoint("epCan1", "rA2", "compA", 1, polymer_chain, 2, "GLY", "N"),
                    "endpoint_2": endpoint("epCan2", "rW1", "compW", 3, "W", 1, "HOH", "O"),
                    "evidence_status": "REJECTED_BY_USER",
                    "topology_effect_applied": False,
                }
            ],
            "metal_coordination": [],
        },
        "unresolved_items": [],
        "summary": {
            "chain_group_count": 4,
            "standard_residue_count": 2,
            "topology_linked_nonstandard_count": 0,
            "independent_nonstandard_count": 1,
            "solvent_component_count": 1,
            "ion_component_count": 1,
            "multiple_conformation_residue_count": 1,
            "missing_residue_count": 0,
            "heavy_atom_issue_count": 0,
            "unresolved_item_count": 0,
        },
    }
    write_yaml(path, classification)


def prepare_case(
    tmp_path: Path,
    *,
    output_format: str = "PDB",
    selected_components: list[str] | None = None,
    source_format: str | None = None,
    polymer_chain: str = "A",
) -> dict[str, Path]:
    actual_source_format = source_format or ("PDB" if output_format == "PDB" else "MMCIF")
    source = tmp_path / ("source.pdb" if actual_source_format == "PDB" else "source.cif")
    make_structure(source, format_name="PDB" if actual_source_format == "PDB" else "MMCIF", polymer_chain=polymer_chain)
    classification = tmp_path / "classification_result.yaml"
    make_classification(classification, source, source_format=actual_source_format, polymer_chain=polymer_chain)
    output = tmp_path / ("selected.pdb" if output_format == "PDB" else "selected.cif")
    spec = {
        "schema_version": 1,
        "task_id": "selection-task-1",
        "workstream_id": "structure-preparation",
        "source_structure": {"path": str(source.resolve()), "sha256": sha256(source)},
        "classification_result": {"path": str(classification.resolve()), "sha256": sha256(classification)},
        "selected_model_id": "1",
        "selected_component_ids": selected_components or ["compA", "compB"],
        "resolved_decision_ids": ["decision-1"],
        "output": {"path": str(output.resolve()), "format": output_format},
        "policies": {
            "selection_level": "COMPONENT_ONLY",
            "covalent_closure": "REQUIRE_COMPLETE",
            "preserve_all_atoms": True,
            "preserve_all_altlocs": True,
            "preserve_source_order": True,
            "preserve_coordinates": True,
        },
        "notes": [],
    }
    spec_path = tmp_path / "selection_spec.yaml"
    write_yaml(spec_path, spec)
    manifest = tmp_path / "selection_manifest.yaml"
    mapping = tmp_path / "selection_mapping.yaml"
    operation_report = tmp_path / "operation_report.yaml"
    operation_config = tmp_path / "operation_config.yaml"
    write_yaml(
        operation_config,
        {
            "schema_version": 1,
            "selection_spec_path": str(spec_path),
            "classification_result_path": str(classification),
            "output": {
                "manifest_path": str(manifest),
                "mapping_path": str(mapping),
                "report_path": str(operation_report),
            },
        },
    )
    validation_report = tmp_path / "validation_report.yaml"
    validation_result = tmp_path / "validation_result.yaml"
    validator_config = tmp_path / "validator_config.yaml"
    write_yaml(
        validator_config,
        {
            "schema_version": 1,
            "selection_spec_path": str(spec_path),
            "classification_result_path": str(classification),
            "candidate_structure_path": str(output),
            "selection_manifest_path": str(manifest),
            "selection_mapping_path": str(mapping),
            "operation_report_path": str(operation_report),
            "validation_report_path": str(validation_report),
            "validation_result_path": str(validation_result),
        },
    )
    return {
        "source": source,
        "classification": classification,
        "spec": spec_path,
        "output": output,
        "manifest": manifest,
        "mapping": mapping,
        "operation_report": operation_report,
        "operation_config": operation_config,
        "validation_report": validation_report,
        "validation_result": validation_result,
        "validator_config": validator_config,
    }


def test_selection_schemas_are_valid_and_output_format_is_representable() -> None:
    schema_paths = [
        OPERATION / "schemas/selection_spec.schema.yaml",
        OPERATION / "schemas/selection_manifest.schema.yaml",
        OPERATION / "schemas/selection_mapping.schema.yaml",
        OPERATION / "schemas/selection_operation_config.schema.yaml",
        OPERATION / "schemas/selection_operation_report.schema.yaml",
        VALIDATOR / "schemas/selection_validation_config.schema.yaml",
        VALIDATOR / "schemas/selection_validation_report.schema.yaml",
        VALIDATOR / "schemas/selection_validation_result.schema.yaml",
    ]
    for path in schema_paths:
        Draft202012Validator.check_schema(yaml.safe_load(path.read_text(encoding="utf-8")))
    manifest_schema = yaml.safe_load((OPERATION / "schemas/selection_manifest.schema.yaml").read_text(encoding="utf-8"))
    assert manifest_schema["properties"]["output_structure"]["$ref"] == "#/$defs/output_file_identity"


@pytest.mark.parametrize("output_format", ["PDB", "MMCIF"])
def test_end_to_end_selection_and_independent_validation(tmp_path: Path, output_format: str) -> None:
    case = prepare_case(tmp_path, output_format=output_format)
    operation = run_script(SELECT_SCRIPT, case["operation_config"])
    assert operation.returncode == 0, operation.stderr
    manifest = yaml.safe_load(case["manifest"].read_text())
    mapping = yaml.safe_load(case["mapping"].read_text())
    assert manifest["actual_component_ids"] == ["compA", "compB"]
    assert manifest["selected_residue_ids"] == ["rA1", "rA2", "rB10"]
    assert manifest["cross_boundary_coordination_relations"][0]["relation_id"] == "relMet"
    assert manifest["cross_boundary_covalent_candidates"][0]["relation_id"] == "relCandidate"
    assert len(mapping["atom_mappings"]) == 8
    output_structure = gemmi.read_structure(str(case["output"]))
    assert output_structure[0].count_atom_sites() == 8
    assert len(output_structure.connections) == 1
    validator = run_script(VALIDATE_SCRIPT, case["validator_config"])
    assert validator.returncode == 0, validator.stderr
    result = yaml.safe_load(case["validation_result"].read_text())
    expected = "SELECTION_VALIDATED_WITH_WARNINGS" if output_format == "PDB" else "SELECTION_VALIDATED"
    assert result["outcome_code"] == expected


def test_confirmed_covalent_boundary_blocks_without_partial_candidate(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, selected_components=["compA"])
    operation = run_script(SELECT_SCRIPT, case["operation_config"])
    assert operation.returncode == 2
    assert "SELECTION_BREAKS_CONFIRMED_COVALENT_LINK" in operation.stderr
    report = yaml.safe_load(case["operation_report"].read_text())
    assert report["status"] == "BLOCKED"
    assert not case["output"].exists()
    assert not case["manifest"].exists()
    assert not case["mapping"].exists()


def test_unknown_component_blocks(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, selected_components=["unknown-component"])
    operation = run_script(SELECT_SCRIPT, case["operation_config"])
    assert operation.returncode == 2
    assert "SELECTION_REFERENCES_UNKNOWN_OBJECT" in operation.stderr
    assert not case["output"].exists()


def test_coordination_boundary_does_not_expand_selection(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, selected_components=["compA", "compB"])
    assert run_script(SELECT_SCRIPT, case["operation_config"]).returncode == 0
    manifest = yaml.safe_load(case["manifest"].read_text())
    assert "compM" not in manifest["actual_component_ids"]
    assert [item["relation_id"] for item in manifest["cross_boundary_coordination_relations"]] == ["relMet"]


def test_pdb_identifier_limit_blocks_long_chain_id(tmp_path: Path) -> None:
    case = prepare_case(
        tmp_path,
        output_format="PDB",
        source_format="MMCIF",
        polymer_chain="AA",
    )
    operation = run_script(SELECT_SCRIPT, case["operation_config"])
    assert operation.returncode == 2
    assert "OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS" in operation.stderr
    assert not case["output"].exists()


def _refresh_provenance_after_candidate_change(case: dict[str, Path]) -> None:
    manifest = yaml.safe_load(case["manifest"].read_text())
    mapping = yaml.safe_load(case["mapping"].read_text())
    report = yaml.safe_load(case["operation_report"].read_text())
    candidate_hash = sha256(case["output"])
    manifest["output_structure"]["sha256"] = candidate_hash
    mapping["output_structure"]["sha256"] = candidate_hash
    write_yaml(case["manifest"], manifest)
    write_yaml(case["mapping"], mapping)
    actual_hashes = {
        case["output"].resolve(): sha256(case["output"]),
        case["manifest"].resolve(): sha256(case["manifest"]),
        case["mapping"].resolve(): sha256(case["mapping"]),
    }
    for item in report["created_files"]:
        item["sha256"] = actual_hashes[Path(item["path"]).resolve()]
        item["size_bytes"] = Path(item["path"]).stat().st_size
    write_yaml(case["operation_report"], report)


def test_validator_detects_coordinate_change_even_with_refreshed_hashes(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, output_format="MMCIF")
    assert run_script(SELECT_SCRIPT, case["operation_config"]).returncode == 0
    structure = gemmi.read_structure(str(case["output"]))
    structure[0][0][0][0].pos.x += 0.2
    structure.make_mmcif_document().write_file(str(case["output"]))
    _refresh_provenance_after_candidate_change(case)
    validator = run_script(VALIDATE_SCRIPT, case["validator_config"])
    assert validator.returncode == 1
    report = yaml.safe_load(case["validation_report"].read_text())
    assert report["outcome_code"] == "COORDINATE_OR_ATTRIBUTE_CHANGED"
    assert report["checks"]["coordinates_and_attributes"] == "FAIL"


def test_validator_rejects_dishonest_manifest(tmp_path: Path) -> None:
    case = prepare_case(tmp_path, output_format="MMCIF")
    assert run_script(SELECT_SCRIPT, case["operation_config"]).returncode == 0
    manifest = yaml.safe_load(case["manifest"].read_text())
    manifest["selected_residue_ids"] = ["rA1"]
    write_yaml(case["manifest"], manifest)
    report = yaml.safe_load(case["operation_report"].read_text())
    for item in report["created_files"]:
        if Path(item["path"]).resolve() == case["manifest"].resolve():
            item["sha256"] = sha256(case["manifest"])
            item["size_bytes"] = case["manifest"].stat().st_size
    write_yaml(case["operation_report"], report)
    validator = run_script(VALIDATE_SCRIPT, case["validator_config"])
    assert validator.returncode == 1
    validation = yaml.safe_load(case["validation_report"].read_text())
    assert validation["outcome_code"] == "MANIFEST_OR_HASH_MISMATCH"
    assert any(item.get("field") == "selected_residue_ids" for item in validation["differences"])

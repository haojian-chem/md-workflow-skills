from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
SCHEMAS = SKILL_ROOT / "schemas"
REFERENCES = SKILL_ROOT / "references"
CONTRACTS = REPO_ROOT / "03_contracts"
sys.path.insert(0, str(SCRIPTS))

from build_classification_result import build
import build_subagent_result as wrapper
from check_possible_connections import check as check_connections
from check_possible_coordination import check as check_coordination
from classification_common import sha256, validate_document
from classify_structure import classify
from inspect_model_scope import inspect


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def dump(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")
    return path


def ccd(path: Path, component_id: str, atoms: list[tuple[str, str]]) -> Path:
    rows = "\n".join(f"{component_id} {name} {element} ." for name, element in atoms)
    return write(
        path,
        f"""data_{component_id}
_chem_comp.id {component_id}
loop_
_chem_comp_atom.comp_id
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.alt_atom_id
{rows}
""",
    )


def pdb_atom(serial, name, resn, chain, resid, x, y, z, element, record="ATOM", alt=" "):
    return f"{record:<6}{serial:5d} {name:>4}{alt:1}{resn:>3} {chain:1}{resid:4d}    {x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{20.0:6.2f}          {element:>2}\n"


def base_pdb() -> str:
    lines = []
    serial = 1
    # CYS and ALA polymer chain A.
    for name, xyz, element in [
        ("N", (0.0, 0.0, 0.0), "N"),
        ("CA", (1.4, 0.0, 0.0), "C"),
        ("C", (2.2, 1.3, 0.0), "C"),
        ("O", (1.8, 2.4, 0.0), "O"),
        ("CB", (1.8, -1.3, 0.0), "C"),
        ("SG", (3.5, -1.3, 0.0), "S"),
    ]:
        lines.append(pdb_atom(serial, name, "CYS", "A", 1, *xyz, element)); serial += 1
    for name, xyz, element in [
        ("N", (3.5, 1.3, 0.0), "N"),
        ("CA", (4.4, 2.4, 0.0), "C"),
        ("C", (5.8, 2.0, 0.0), "C"),
        ("O", (6.5, 2.9, 0.0), "O"),
        ("CB", (4.0, 3.8, 0.0), "C"),
    ]:
        lines.append(pdb_atom(serial, name, "ALA", "A", 2, *xyz, element)); serial += 1
    # HEM Fe at 2.3 A from CYS SG.
    lines.append(pdb_atom(serial, "FE", "HEM", "H", 501, 5.8, -1.3, 0.0, "FE", "HETATM")); fe_serial = serial; serial += 1
    # Repeated glycerol, water, sodium.
    for resid, x in [(601, 10.0), (602, 12.0)]:
        lines.append(pdb_atom(serial, "C1", "GOL", "G", resid, x, 0, 0, "C", "HETATM")); serial += 1
        lines.append(pdb_atom(serial, "O1", "GOL", "G", resid, x + 1.2, 0, 0, "O", "HETATM")); serial += 1
    for resid, x in [(1, 20.0), (2, 22.0)]:
        lines.append(pdb_atom(serial, "O", "HOH", "W", resid, x, 0, 0, "O", "HETATM")); serial += 1
    for resid, x in [(1, 25.0), (2, 27.0)]:
        lines.append(pdb_atom(serial, "NA", "NA", "I", resid, x, 0, 0, "NA", "HETATM")); serial += 1
    lines.append(f"CONECT{fe_serial:5d}{6:5d}\n")
    lines.append("END\n")
    return "".join(lines)


def prepare_ccd(tmp_path: Path) -> Path:
    local = tmp_path / "local_ccd"
    ccd(local / "CYS.cif", "CYS", [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"), ("SG", "S")])
    ccd(local / "ALA.cif", "ALA", [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")])
    ccd(local / "HEM.cif", "HEM", [("FE", "Fe")])
    ccd(local / "GOL.cif", "GOL", [("C1", "C"), ("O1", "O")])
    return local


def classify_config(structure: Path, output_root: Path, local_ccd: Path, mode="REGISTRY", **extra):
    config = {
        "structure": {
            "path": str(structure),
            "sha256": sha256(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": mode},
        "project_residue_definitions": {"path": None},
        "skill_registry_paths": [
            str(REFERENCES / "standard_residue_registry.yaml"),
            str(REFERENCES / "covalently_linked_nonstandard_residue_registry.yaml"),
        ],
        "sequence_references": [],
        "ccd": {
            "project_snapshot_dir": str(output_root / "reference_data/ccd"),
            "local_reference_dirs": [str(local_ccd)],
            "shared_cache_path": str(tmp_path_global / "cache") if tmp_path_global else None,
            "retrieval_policy": "CACHE_ONLY",
        },
        "output_root": str(output_root),
    }
    config.update(extra)
    return config


tmp_path_global = None


def test_all_schemas_are_meta_valid():
    for path in SCHEMAS.glob("*.schema.yaml"):
        Draft202012Validator.check_schema(yaml.safe_load(path.read_text()))


def test_model_scope_single_and_multi(tmp_path: Path):
    single = write(tmp_path / "single.pdb", base_pdb())
    result = inspect(single, expected_sha256=None, declared_format="PDB")
    validate_document(result, SCHEMAS / "model_scope.schema.yaml")
    assert result["selection"] == {"status": "AUTO_SELECTED", "selected_model_id": "1"}

    multi = write(
        tmp_path / "multi.pdb",
        "MODEL        1\n" + pdb_atom(1, "CA", "ALA", "A", 1, 0, 0, 0, "C") + "ENDMDL\n"
        + "MODEL        2\n" + pdb_atom(2, "CA", "ALA", "A", 1, 1, 0, 0, "C") + "ENDMDL\nEND\n",
    )
    result = inspect(multi, expected_sha256=None, declared_format="PDB")
    assert result["model_count"] == 2
    assert result["selection"]["status"] == "USER_SELECTION_REQUIRED"


def test_registry_classification_grouping_and_ccd_local_first(tmp_path: Path):
    global tmp_path_global
    tmp_path_global = tmp_path
    structure = write(tmp_path / "system.pdb", base_pdb())
    local = prepare_ccd(tmp_path)
    observations, manifest = classify(classify_config(structure, tmp_path / "out", local))
    validate_document(observations, SCHEMAS / "classification_observations.schema.yaml")
    validate_document(manifest, SCHEMAS / "reference_manifest.schema.yaml")

    groups = {group.get("residue_name", group.get("source_chain_id")): group for group in observations["chain_groups"]}
    assert groups["A"]["chain_index"] == 1
    assert groups["GOL"]["instance_count"] == 2
    assert groups["HOH"]["instance_count"] == 2
    assert groups["NA"]["instance_count"] == 2
    assert not any(record["residue_name"] in {"GOL", "HOH", "NA"} for record in observations["residue_records"])
    assert all(item["retrieval"]["source"] == "LOCAL_REFERENCE_DIRECTORY" for item in manifest["ccd_components"])


def test_altloc_is_recorded_and_heavy_atom_check_skipped(tmp_path: Path):
    global tmp_path_global
    tmp_path_global = tmp_path
    pdb = (
        pdb_atom(1, "N", "ALA", "A", 1, 0, 0, 0, "N")
        + pdb_atom(2, "CA", "ALA", "A", 1, 1.4, 0, 0, "C", alt="A")
        + pdb_atom(3, "CA", "ALA", "A", 1, 1.5, 0, 0, "C", alt="B")
        + "END\n"
    )
    structure = write(tmp_path / "alt.pdb", pdb)
    local = prepare_ccd(tmp_path)
    observations, _ = classify(classify_config(structure, tmp_path / "out", local))
    record = observations["residue_records"][0]
    assert record["conformation_observation"]["status"] == "MULTIPLE_CONFORMATIONS"
    assert record["heavy_atom_check"]["reason"] == "MULTIPLE_CONFORMATIONS_PRESENT"


def test_coordination_promotes_heme_and_assigns_polymer_chain(tmp_path: Path):
    global tmp_path_global
    tmp_path_global = tmp_path
    structure = write(tmp_path / "system.pdb", base_pdb())
    local = prepare_ccd(tmp_path)
    output_root = tmp_path / "out"
    observations, manifest = classify(classify_config(structure, output_root, local))
    observations_path = dump(output_root / "classification_observations.yaml", observations)
    manifest_path = dump(output_root / "reference_manifest.yaml", manifest)
    model_scope = inspect(structure, expected_sha256=None, declared_format="PDB")
    model_scope_path = dump(output_root / "model_scope.yaml", model_scope)

    coord_defs = dump(
        tmp_path / "possible_coordination.yaml",
        {
            "schema_version": "1.0",
            "possible_coordination": [
                {
                    "label": "HEME_FE_CYS",
                    "metal": {"residue_name": "HEM", "atom_name": "FE", "element": "Fe"},
                    "donor": {"residue_name": "CYS", "atom_name": "SG", "element": "S"},
                    "distance_range_angstrom": {"minimum": 1.8, "maximum": 2.7},
                    "topology_effect": {"promote_nonstandard_to_linked": True},
                }
            ],
        },
    )
    coord_result = check_coordination(
        {
            "structure": {"path": str(structure), "sha256": sha256(structure), "selected_model_id": "1"},
            "classification_observations": {"path": str(observations_path), "sha256": sha256(observations_path)},
            "possible_coordination": {"path": str(coord_defs), "sha256": sha256(coord_defs)},
        }
    )
    validate_document(coord_result, SCHEMAS / "possible_coordination_result.schema.yaml")
    pair = coord_result["definition_results"][0]["pair_results"][0]
    assert pair["status"] == "CONFIRMED_BY_STRUCTURE"

    connection_result = check_connections(
        {
            "structure": {"path": str(structure), "sha256": sha256(structure), "selected_model_id": "1"},
            "classification_observations": {"path": str(observations_path), "sha256": sha256(observations_path)},
            "possible_connections": {"path": None},
        }
    )
    connections_path = dump(output_root / "relation_checks/possible_connections_result.yaml", connection_result)
    coord_path = dump(output_root / "relation_checks/possible_coordination_result.yaml", coord_result)
    build_config = {
        "model_scope": {"path": str(model_scope_path), "sha256": sha256(model_scope_path)},
        "classification_observations": {"path": str(observations_path), "sha256": sha256(observations_path)},
        "reference_manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "possible_connections_result": {"path": str(connections_path), "sha256": sha256(connections_path)},
        "possible_coordination_result": {"path": str(coord_path), "sha256": sha256(coord_path)},
        "decisions": [],
    }
    confirmations, final_result, report = build(build_config)
    validate_document(confirmations, SCHEMAS / "confirmation_requests.schema.yaml")
    validate_document(final_result, SCHEMAS / "classification_result.schema.yaml")
    assert confirmations["status"] == "NO_CONFIRMATION_REQUIRED"
    heme = next(record for record in final_result["residue_records"] if record["residue_name"] == "HEM")
    assert heme["classification"]["topology_class"] == "COVALENTLY_LINKED_NONSTANDARD"
    assert heme["chain_index"] == 1
    assert "METAL_COORDINATION" in report


def test_force_field_rtp_heavy_atom_and_duplicate_template(tmp_path: Path):
    global tmp_path_global
    tmp_path_global = tmp_path
    structure = write(
        tmp_path / "ff.pdb",
        pdb_atom(1, "N", "ALA", "A", 1, 0, 0, 0, "N")
        + pdb_atom(2, "CA", "ALA", "A", 1, 1.4, 0, 0, "C")
        + pdb_atom(3, "C", "ALA", "A", 1, 2.2, 1.3, 0, "C")
        + pdb_atom(4, "O", "ALA", "A", 1, 1.8, 2.4, 0, "O")
        + pdb_atom(5, "N", "GLY", "A", 2, 3.5, 1.3, 0, "N")
        + pdb_atom(6, "CA", "GLY", "A", 2, 4.4, 2.4, 0, "C")
        + pdb_atom(7, "C", "GLY", "A", 2, 5.8, 2.0, 0, "C")
        + pdb_atom(8, "O", "GLY", "A", 2, 6.5, 2.9, 0, "O")
        + "END\n",
    )
    ff = tmp_path / "test.ff"
    write(
        ff / "aminoacids.rtp",
        """[ NALA ]
 [ atoms ]
 N N -0.3 1
 CA CT 0.1 2
 CB CT 0.0 3
 C C 0.5 4
 O O -0.5 5
[ CGLY ]
 [ atoms ]
 N N -0.3 1
 CA CT 0.1 2
 C C 0.5 3
 O O -0.5 4
 OXT O -0.5 5
""",
    )
    config = classify_config(
        structure,
        tmp_path / "out",
        tmp_path / "empty_ccd",
        mode="FORCE_FIELD_ANALYSIS",
        force_field={
            "root_path": str(ff),
            "terminal_template_mappings": [
                {"polymer_type": "POLYPEPTIDE_L", "terminal_role": "N_TERMINUS", "source_residue_name": "ALA", "rtp_residue_name": "NALA", "rtp_file": "aminoacids.rtp"},
                {"polymer_type": "POLYPEPTIDE_L", "terminal_role": "C_TERMINUS", "source_residue_name": "GLY", "rtp_residue_name": "CGLY", "rtp_file": "aminoacids.rtp"},
            ],
        },
    )
    observations, _ = classify(config)
    ala = next(record for record in observations["residue_records"] if record["residue_name"] == "ALA")
    gly = next(record for record in observations["residue_records"] if record["residue_name"] == "GLY")
    assert ala["heavy_atom_check"]["missing_atoms"] == ["CB"]
    assert gly["heavy_atom_check"]["missing_atoms"] == ["OXT"]

    with (ff / "aminoacids.rtp").open("a", encoding="utf-8") as handle:
        handle.write("""[ NALA ]
 [ atoms ]
 N N 0 1
 CA CT 0 2
 C C 0 3
 O O 0 4
""")
    observations, _ = classify(config)
    assert any(item["issue_type"] == "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE" for item in observations["unresolved_observations"])


def test_project_names_are_case_sensitive(tmp_path: Path):
    global tmp_path_global
    tmp_path_global = tmp_path
    structure = write(
        tmp_path / "case.pdb",
        pdb_atom(1, "C1", "HEM", "A", 1, 0, 0, 0, "C", "HETATM")
        + pdb_atom(2, "C1", "Hem", "B", 2, 3, 0, 0, "C", "HETATM")
        + "END\n",
    )
    local = tmp_path / "ccd"
    ccd(local / "HEM.cif", "HEM", [("C1", "C")])
    defs = dump(
        tmp_path / "defs.yaml",
        {
            "schema_version": "1.0",
            "residue_definitions": [
                {"residue_name": "HEM", "polymer_class": "NONPOLYMER", "topology_class": "INDEPENDENT_NONSTANDARD", "ccd_id": "HEM"},
                {"residue_name": "Hem", "polymer_class": "NONPOLYMER", "topology_class": "INDEPENDENT_NONSTANDARD", "ccd_id": "HEM"},
            ],
        },
    )
    config = classify_config(structure, tmp_path / "out", local)
    config["project_residue_definitions"] = {"path": str(defs), "sha256": sha256(defs)}
    observations, _ = classify(config)
    names = {record["residue_name"] for record in observations["residue_records"]}
    assert names == {"HEM", "Hem"}


def test_subagent_wrapper_builds_done_result(tmp_path: Path, monkeypatch):
    global tmp_path_global
    tmp_path_global = tmp_path
    project = tmp_path / "project"
    structure = write(project / "01_structure_preparation/01_source_recognition/input.pdb", base_pdb())
    local = prepare_ccd(tmp_path)
    output_root = project / "01_structure_preparation/02_component_and_residue_classification"
    observations, manifest = classify(classify_config(structure, output_root, local))
    model_scope = inspect(structure, expected_sha256=None, declared_format="PDB")
    model_scope_path = dump(output_root / "model_scope.yaml", model_scope)
    observations_path = dump(output_root / "classification_observations.yaml", observations)
    manifest_path = dump(output_root / "reference_manifest.yaml", manifest)
    connections = check_connections({
        "structure": {"path": str(structure), "sha256": sha256(structure), "selected_model_id": "1"},
        "classification_observations": {"path": str(observations_path), "sha256": sha256(observations_path)},
        "possible_connections": {"path": None},
    })
    coordination = check_coordination({
        "structure": {"path": str(structure), "sha256": sha256(structure), "selected_model_id": "1"},
        "classification_observations": {"path": str(observations_path), "sha256": sha256(observations_path)},
        "possible_coordination": {"path": None},
    })
    connections_path = dump(output_root / "relation_checks/possible_connections_result.yaml", connections)
    coordination_path = dump(output_root / "relation_checks/possible_coordination_result.yaml", coordination)
    confirmations, final_result, report = build({
        "model_scope": {"path": str(model_scope_path), "sha256": sha256(model_scope_path)},
        "classification_observations": {"path": str(observations_path), "sha256": sha256(observations_path)},
        "reference_manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "possible_connections_result": {"path": str(connections_path), "sha256": sha256(connections_path)},
        "possible_coordination_result": {"path": str(coordination_path), "sha256": sha256(coordination_path)},
        "decisions": [],
    })
    confirmations_path = dump(output_root / "confirmation_requests.yaml", confirmations)
    result_path = dump(output_root / "classification_result.yaml", final_result)
    report_path = write(output_root / "classification_report.md", report)
    task = {
        "schema_version": 2,
        "task_id": "task_0001",
        "workstream_id": "ws_0001",
        "workflow_name": "structure_preparation_workflow",
        "route_id": "route_0001",
        "sequence": 2,
        "task_unit": {
            "mode": "VALIDATOR",
            "operation": None,
            "validator": {
                "skill_name": "component_and_residue_classification_validator",
                "skill_path": "02_validators/component_and_residue_classification_validator",
                "skill_layer": "validator",
            },
        },
        "project_root": str(project),
        "work_directory": str(output_root),
        "permissions": {
            "allowed_read_paths": [str(structure)],
            "allowed_write_paths": [str(output_root)],
            "forbidden_paths": [str(project / "00_project_state/**"), str(project / "00_project_records/**")],
        },
        "current_valid_files": [{"path": str(structure), "state": "present_unvalidated", "sha256": sha256(structure)}],
        "upstream_summary": "source recognized",
        "user_decisions": [],
        "required_outputs": ["classification_result.yaml", "classification_report.md"],
        "detail_output_paths": {"log_file": None, "report_file": str(report_path), "result_data_file": str(result_path)},
        "result_contract": "03_contracts/subagent_result.schema.yaml",
    }
    task_path = dump(project / "task.yaml", task)
    wrapped = wrapper.build_result(
        task_path,
        result_path,
        confirmations_path,
        report_path,
        model_scope_path,
        [observations_path, manifest_path, connections_path, coordination_path],
        CONTRACTS,
        SCHEMAS / "classification_result.schema.yaml",
        SCHEMAS / "confirmation_requests.schema.yaml",
    )
    assert wrapped["status"] == "DONE"
    assert wrapped["validation_result"]["outcome_code"] == "CLASSIFIED_CLEAR"
    assert wrapped["artifact_candidates"] == []
    assert wrapped["confirmation_items"] == []
    assert wrapped["validation_result"]["validated_files"][0]["state"] == "present_unvalidated"

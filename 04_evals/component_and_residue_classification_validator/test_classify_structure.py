from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import gemmi
import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPT = SKILL_ROOT / "scripts/classify_structure.py"


def load_module():
    spec = importlib.util.spec_from_file_location("classify_structure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()

CLEAR_PDB = """\
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      11.400  10.000  10.000  1.00 20.00           C
ATOM      3  C   ALA A   1      12.000  11.400  10.000  1.00 20.00           C
ATOM      4  O   ALA A   1      11.400  12.400  10.000  1.00 20.00           O
HETATM    5  C1  LIG B 101      20.000  20.000  20.000  1.00 20.00           C
HETATM    6  O   HOH W   1      25.000  25.000  25.000  1.00 20.00           O
HETATM    7 NA    NA I   1      30.000  30.000  30.000  1.00 20.00          NA
END
"""

LINKED_PDB = """\
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      11.400  10.000  10.000  1.00 20.00           C
ATOM      3  C   ALA A   1      12.000  11.400  10.000  1.00 20.00           C
ATOM      4  O   ALA A   1      11.400  12.400  10.000  1.00 20.00           O
HETATM    5  C1  LIG A 101      13.400  11.400  10.000  1.00 20.00           C
LINK         C   ALA A   1                 C1  LIG A 101     1555   1555  1.40
END
"""

SHORT_PDB = LINKED_PDB.replace(
    "LINK         C   ALA A   1                 C1  LIG A 101     1555   1555  1.40\n",
    "",
)

COORD_PDB = """\
ATOM      1  N   HIS A   1       9.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  HIS A   1       8.000  10.000  10.000  1.00 20.00           C
ATOM      3  C   HIS A   1       7.000  10.000  10.000  1.00 20.00           C
ATOM      4  ND1 HIS A   1      10.000  10.000  10.000  1.00 20.00           N
HETATM    5  ZN  ZN  Z   1      12.100  10.000  10.000  1.00 20.00          ZN
HETATM    6  O1  LIG B 101      14.100  10.000  10.000  1.00 20.00           O
HETATM    7  C1  LIG B 101      15.300  10.000  10.000  1.00 20.00           C
END
"""

MULTI_SAME_PDB = """\
MODEL        1
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      11.400  10.000  10.000  1.00 20.00           C
ATOM      3  C   ALA A   1      12.000  11.400  10.000  1.00 20.00           C
ENDMDL
MODEL        2
ATOM      4  N   ALA A   1      10.100  10.000  10.000  1.00 20.00           N
ATOM      5  CA  ALA A   1      11.500  10.000  10.000  1.00 20.00           C
ATOM      6  C   ALA A   1      12.100  11.400  10.000  1.00 20.00           C
ENDMDL
END
"""

MULTI_DIFF_PDB = """\
MODEL        1
ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      11.400  10.000  10.000  1.00 20.00           C
ATOM      3  C   ALA A   1      12.000  11.400  10.000  1.00 20.00           C
HETATM    4  C1  LIG B 101      20.000  20.000  20.000  1.00 20.00           C
ENDMDL
MODEL        2
ATOM      5  N   ALA A   1      10.100  10.000  10.000  1.00 20.00           N
ATOM      6  CA  ALA A   1      11.500  10.000  10.000  1.00 20.00           C
ATOM      7  C   ALA A   1      12.100  11.400  10.000  1.00 20.00           C
ENDMDL
END
"""

ALIASES_PDB = """\
ATOM      1  N   HID A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  HID A   1      11.400  10.000  10.000  1.00 20.00           C
ATOM      3  C   HID A   1      12.000  11.400  10.000  1.00 20.00           C
ATOM      4  N   MSE A   2      13.300  11.400  10.000  1.00 20.00           N
ATOM      5  CA  MSE A   2      14.000  12.600  10.000  1.00 20.00           C
ATOM      6  C   MSE A   2      15.400  12.600  10.000  1.00 20.00           C
ATOM      7 SE   MSE A   2      14.000  14.800  10.000  1.00 20.00          SE
END
"""

CA_CONFLICT_PDB = """\
HETATM    1  C1  CA  A   1      10.000  10.000  10.000  1.00 20.00           C
HETATM    2  O1  CA  A   1      11.200  10.000  10.000  1.00 20.00           O
END
"""


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def args_for(structure: Path, tmp_path: Path, *, task_id: str = "task_1", source_label=None):
    return argparse.Namespace(
        structure=structure,
        task_id=task_id,
        workstream_id="ws_0001",
        report=tmp_path / "report.yaml",
        result_data=tmp_path / "result.yaml",
        model_id=None,
        source_label=source_label,
        standard_registry=SKILL_ROOT / "references/standard_residue_alias_registry.yaml",
        covalent_registry=SKILL_ROOT / "references/covalently_linked_nonstandard_residue_registry.yaml",
        coordination_registry=SKILL_ROOT / "references/coordination_detection_registry.yaml",
        schema=SKILL_ROOT / "schemas/classification_outputs.schema.yaml",
    )


def residues_by_name(result: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for residue in result["residues"]:
        grouped.setdefault(residue["residue_name"], []).append(residue)
    return grouped


def test_local_schema_is_meta_valid() -> None:
    schema = yaml.safe_load(
        (SKILL_ROOT / "schemas/classification_outputs.schema.yaml").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)


def test_clear_classification(tmp_path: Path) -> None:
    structure = write(tmp_path / "clear.pdb", CLEAR_PDB)
    before = hashlib.sha256(structure.read_bytes()).hexdigest()
    result = MODULE.classify(args_for(structure, tmp_path))
    after = hashlib.sha256(structure.read_bytes()).hexdigest()

    assert before == after
    assert result["outcome_code"] == "CLASSIFIED_CLEAR"
    assert result["summary"] == {
        "model_count": 1,
        "chain_count": 4,
        "component_count": 4,
        "residue_count": 4,
        "standard_residue_count": 1,
        "covalently_linked_nonstandard_count": 0,
        "independent_nonstandard_count": 1,
        "solvent_count": 1,
        "ion_count": 1,
        "unknown_count": 0,
        "blocking_ambiguity_count": 0,
    }


def test_explicit_link_and_mmcif_roundtrip(tmp_path: Path) -> None:
    pdb = write(tmp_path / "linked.pdb", LINKED_PDB)
    pdb_result = MODULE.classify(args_for(pdb, tmp_path / "pdb"))
    assert residues_by_name(pdb_result)["LIG"][0]["topology_class"] == "COVALENTLY_LINKED_NONSTANDARD"

    structure = gemmi.read_structure(str(pdb))
    cif = tmp_path / "linked.cif"
    structure.make_mmcif_document().write_file(str(cif))
    cif_result = MODULE.classify(args_for(cif, tmp_path / "cif"))
    assert cif_result["input_structure"]["format"] == "MMCIF"
    assert residues_by_name(cif_result)["LIG"][0]["topology_class"] == "COVALENTLY_LINKED_NONSTANDARD"


def test_geometry_only_contact_requires_decision(tmp_path: Path) -> None:
    structure = write(tmp_path / "short.pdb", SHORT_PDB)
    result = MODULE.classify(args_for(structure, tmp_path))
    ligand = residues_by_name(result)["LIG"][0]

    assert result["outcome_code"] == "CLASSIFICATION_DECISION_REQUIRED"
    assert ligand["topology_class"] == "UNKNOWN"
    assert result["covalent_candidates"]
    assert any(item["category"] == "COVALENT_LINKAGE" for item in result["ambiguities"])


def test_coordination_does_not_change_topology(tmp_path: Path) -> None:
    structure = write(tmp_path / "coord.pdb", COORD_PDB)
    result = MODULE.classify(args_for(structure, tmp_path))
    ligand = residues_by_name(result)["LIG"][0]

    assert ligand["topology_class"] == "INDEPENDENT_NONSTANDARD"
    assert result["coordination_candidates"]
    assert not any(item["category"] == "COVALENT_LINKAGE" for item in result["ambiguities"])


def test_multi_model_same_and_different(tmp_path: Path) -> None:
    same = write(tmp_path / "same.pdb", MULTI_SAME_PDB)
    same_result = MODULE.classify(args_for(same, tmp_path / "same"))
    assert same_result["outcome_code"] == "CLASSIFIED_WITH_WARNINGS"
    assert not same_result["ambiguities"]

    different = write(tmp_path / "different.pdb", MULTI_DIFF_PDB)
    diff_result = MODULE.classify(args_for(different, tmp_path / "different"))
    assert diff_result["outcome_code"] == "CLASSIFICATION_DECISION_REQUIRED"
    assert any(item["category"] == "MODEL_SELECTION" for item in diff_result["ambiguities"])


def test_aliases_and_ion_name_conflict(tmp_path: Path) -> None:
    aliases = write(tmp_path / "aliases.pdb", ALIASES_PDB)
    alias_result = MODULE.classify(args_for(aliases, tmp_path / "aliases"))
    grouped = residues_by_name(alias_result)
    assert grouped["HID"][0]["topology_class"] == "STANDARD_RESIDUE"
    assert grouped["HID"][0]["canonical_parent"] == "HIS"
    assert grouped["MSE"][0]["topology_class"] == "COVALENTLY_LINKED_NONSTANDARD"
    assert grouped["MSE"][0]["canonical_parent"] == "MET"

    conflict = write(tmp_path / "ca_conflict.pdb", CA_CONFLICT_PDB)
    conflict_result = MODULE.classify(args_for(conflict, tmp_path / "conflict"))
    assert residues_by_name(conflict_result)["CA"][0]["topology_class"] == "UNKNOWN"
    assert conflict_result["outcome_code"] == "CLASSIFICATION_DECISION_REQUIRED"


def test_af3_label_and_cli_outputs(tmp_path: Path) -> None:
    pdb = write(tmp_path / "source.pdb", CLEAR_PDB)
    structure = gemmi.read_structure(str(pdb))
    cif = tmp_path / "af3_model.cif"
    structure.make_mmcif_document().write_file(str(cif))
    report = tmp_path / "report.yaml"
    result_data = tmp_path / "result.yaml"

    command = [
        sys.executable,
        str(SCRIPT),
        "--structure",
        str(cif),
        "--task-id",
        "task_af3",
        "--workstream-id",
        "ws_0001",
        "--source-label",
        "AF3_CIF",
        "--report",
        str(report),
        "--result-data",
        str(result_data),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    result = yaml.safe_load(result_data.read_text(encoding="utf-8"))
    detailed_report = yaml.safe_load(report.read_text(encoding="utf-8"))

    assert summary["status"] == "DONE"
    assert result["input_structure"]["format"] == "AF3_CIF"
    assert detailed_report["parser_version"] == MODULE.VERSION
    assert detailed_report["classification"]["task_id"] == "task_af3"


def test_symlink_rejected_and_cross_task_overwrite_blocked(tmp_path: Path) -> None:
    source = write(tmp_path / "source.pdb", CLEAR_PDB)
    symlink = tmp_path / "source_link.pdb"
    symlink.symlink_to(source)
    with pytest.raises(MODULE.ClassificationError, match="symlink input"):
        MODULE.classify(args_for(symlink, tmp_path / "symlink"))

    output = tmp_path / "existing.yaml"
    output.write_text("task_id: another_task\n", encoding="utf-8")
    with pytest.raises(MODULE.ClassificationError, match="another task"):
        MODULE.output_conflict(output, "task_new")

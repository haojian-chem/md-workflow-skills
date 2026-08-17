from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import gemmi
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification


PDB_MISSING_A = """\
HEADER    MISSING RESIDUE TEST
SEQRES   1 A    3  ALA GLY SER
REMARK 465     GLY A   2
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       1.400   1.500   0.000  1.00 20.00           C
ATOM      6  N   SER A   3       4.200   0.000   0.000  1.00 20.00           N
ATOM      7  CA  SER A   3       5.600   0.000   0.000  1.00 20.00           C
ATOM      8  C   SER A   3       7.000   0.000   0.000  1.00 20.00           C
ATOM      9  O   SER A   3       8.000   0.000   0.000  1.00 20.00           O
ATOM     10  CB  SER A   3       5.600   1.500   0.000  1.00 20.00           C
ATOM     11  OG  SER A   3       6.900   1.800   0.000  1.00 20.00           O
TER
END
"""

PDB_OBSERVED_AS = """\
HEADER    OBSERVED RESIDUE TEST
SEQRES   1 A    2  ALA SER
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       1.400   1.500   0.000  1.00 20.00           C
ATOM      6  N   SER A   2       4.200   0.000   0.000  1.00 20.00           N
ATOM      7  CA  SER A   2       5.600   0.000   0.000  1.00 20.00           C
ATOM      8  C   SER A   2       7.000   0.000   0.000  1.00 20.00           C
ATOM      9  O   SER A   2       8.000   0.000   0.000  1.00 20.00           O
ATOM     10  CB  SER A   2       5.600   1.500   0.000  1.00 20.00           C
ATOM     11  OG  SER A   2       6.900   1.800   0.000  1.00 20.00           O
TER
END
"""

PDB_CHAIN_UNRESOLVED = PDB_OBSERVED_AS.replace(
    "SEQRES   1 A    2  ALA SER\n",
    "SEQRES   1 A    2  ALA SER\nREMARK 465     GLY B   2\n",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_ccd(path: Path, component_id: str, atoms: list[tuple[str, str]]) -> None:
    rows = "\n".join(
        f"{component_id} {atom_name} {atom_name} {element}"
        for atom_name, element in atoms
    )
    path.write_text(
        f"""data_{component_id}
_chem_comp.id {component_id}
loop_
_chem_comp_atom.comp_id
_chem_comp_atom.atom_id
_chem_comp_atom.alt_atom_id
_chem_comp_atom.type_symbol
{rows}
""",
        encoding="utf-8",
    )


def local_ccd_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "local_ccd"
    directory.mkdir()
    write_ccd(
        directory / "ALA.cif",
        "ALA",
        [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")],
    )
    write_ccd(
        directory / "SER.cif",
        "SER",
        [
            ("N", "N"),
            ("CA", "C"),
            ("C", "C"),
            ("O", "O"),
            ("CB", "C"),
            ("OG", "O"),
        ],
    )
    return directory


def write_mmcif_from_pdb(
    pdb_path: Path,
    cif_path: Path,
    *,
    unobserved_auth_chain: str | None = None,
    unobserved_auth_seq_id: str | None = None,
) -> None:
    structure = gemmi.read_structure(str(pdb_path))
    document = structure.make_mmcif_document()
    document.write_file(str(cif_path))
    if unobserved_auth_chain is None:
        return
    cif_path.write_text(
        cif_path.read_text(encoding="utf-8")
        + f"""
loop_
_pdbx_unobs_or_zero_occ_residues.id
_pdbx_unobs_or_zero_occ_residues.PDB_model_num
_pdbx_unobs_or_zero_occ_residues.auth_asym_id
_pdbx_unobs_or_zero_occ_residues.auth_comp_id
_pdbx_unobs_or_zero_occ_residues.auth_seq_id
_pdbx_unobs_or_zero_occ_residues.PDB_ins_code
_pdbx_unobs_or_zero_occ_residues.label_comp_id
_pdbx_unobs_or_zero_occ_residues.label_seq_id
1 1 {unobserved_auth_chain} GLY {unobserved_auth_seq_id or '?'} ? GLY 2
""",
        encoding="utf-8",
    )


def run_classification(
    tmp_path: Path,
    structure_path: Path,
    source_format: str,
    *,
    sequence_references: list[dict] | None = None,
) -> tuple[dict, dict]:
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    config = {
        "structure": {
            "path": str(structure_path),
            "sha256": digest(structure_path),
            "source_format": source_format,
            "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "ccd": {
            "local_reference_dirs": [str(local_ccd_dir(tmp_path))],
            "retrieval_policy": "CACHE_ONLY",
        },
        "output": {
            "observations_path": str(output_dir / "classification_observations.yaml"),
            "reference_manifest_path": str(output_dir / "reference_manifest.yaml"),
        },
    }
    if sequence_references is not None:
        config["sequence_references"] = sequence_references
    observations, manifest, *_ = execute_classification(config, SCRIPTS)
    return observations, manifest


def missing_records(observations: dict) -> list[dict]:
    return [
        record
        for record in observations["residue_records"]
        if record["presence_status"] == "MISSING_EXPECTED"
    ]


def issue_records(observations: dict, issue_type: str) -> list[dict]:
    return [
        item
        for item in observations["unresolved_observations"]
        if item["issue_type"] == issue_type
    ]


def check_for_chain(observations: dict, source_chain_id: str) -> dict:
    return next(
        item
        for item in observations["missing_residue_checks"]
        if item["source_chain_id"] == source_chain_id
    )


def test_pdb_seqres_and_remark_465_create_missing_expected_record(tmp_path: Path) -> None:
    structure = tmp_path / "missing.pdb"
    structure.write_text(PDB_MISSING_A, encoding="utf-8")

    observations, _manifest = run_classification(tmp_path, structure, "PDB")

    records = missing_records(observations)
    assert len(records) == 1
    assert records[0]["residue_name"] == "GLY"
    assert records[0]["source_resid"] == {"number": "2", "insertion_code": None}
    assert records[0]["sequence_position"] == 2
    polymer_group = next(
        group for group in observations["chain_groups"] if group["group_type"] == "POLYMER_CHAIN"
    )
    assert records[0]["chain_index"] == polymer_group["chain_index"]
    check = check_for_chain(observations, "A")
    assert check["status"] == "MISSING_RESIDUES_FOUND"
    assert check["missing_residue_count"] == 1
    assert not issue_records(observations, "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE")


def test_mmcif_unobserved_residue_with_author_number_is_resolved(tmp_path: Path) -> None:
    pdb = tmp_path / "source.pdb"
    pdb.write_text(PDB_MISSING_A.replace("REMARK 465     GLY A   2\n", ""), encoding="utf-8")
    structure = tmp_path / "missing.cif"
    write_mmcif_from_pdb(
        pdb,
        structure,
        unobserved_auth_chain="A",
        unobserved_auth_seq_id="2",
    )

    observations, _manifest = run_classification(tmp_path, structure, "MMCIF")

    records = missing_records(observations)
    assert len(records) == 1
    assert records[0]["residue_name"] == "GLY"
    assert records[0]["source_resid"]["number"] == "2"
    assert records[0]["sequence_position"] == 2
    assert check_for_chain(observations, "A")["missing_residue_count"] == 1


def test_mmcif_missing_author_resid_is_single_mapping_unresolved_issue(tmp_path: Path) -> None:
    pdb = tmp_path / "source.pdb"
    pdb.write_text(PDB_MISSING_A.replace("REMARK 465     GLY A   2\n", ""), encoding="utf-8")
    structure = tmp_path / "missing_author_resid.cif"
    write_mmcif_from_pdb(
        pdb,
        structure,
        unobserved_auth_chain="A",
        unobserved_auth_seq_id="?",
    )

    observations, _manifest = run_classification(tmp_path, structure, "MMCIF")

    assert not missing_records(observations)
    issues = issue_records(observations, "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE")
    assert len(issues) == 1
    assert issues[0]["subject"] == {
        "source_chain_id": "A",
        "residue_name": "GLY",
        "sequence_position": 2,
    }
    assert set(issues[0]["evidence"]) == {
        "MMCIF_UNOBSERVED_RESIDUES",
        "ENTITY_SEQUENCE_ALIGNMENT",
    }
    check = check_for_chain(observations, "A")
    assert check["status"] == "MAPPING_UNRESOLVED"
    assert check["missing_residue_count"] == 0
    assert check["reason"] == "AUTHOR_SOURCE_RESIDS_FOR_MISSING_RESIDUES_UNAVAILABLE"
    assert observations["summary"]["unresolved_observation_count"] == len(
        observations["unresolved_observations"]
    )


def test_pdb_missing_record_for_unknown_chain_is_mapping_unresolved(tmp_path: Path) -> None:
    structure = tmp_path / "unknown_chain.pdb"
    structure.write_text(PDB_CHAIN_UNRESOLVED, encoding="utf-8")

    observations, _manifest = run_classification(tmp_path, structure, "PDB")

    assert not missing_records(observations)
    issues = issue_records(observations, "MISSING_RESIDUE_CHAIN_UNRESOLVED")
    assert len(issues) == 1
    assert issues[0]["subject"]["source_chain_id"] == "B"
    check = check_for_chain(observations, "B")
    assert check["chain_index"] is None
    assert check["status"] == "MAPPING_UNRESOLVED"
    assert check["missing_residue_count"] == 0
    assert check["reason"] == "MISSING_RESIDUE_CHAIN_UNRESOLVED"


@pytest.mark.parametrize(
    ("reference_type", "filename", "content"),
    [
        ("FASTA", "input.fasta", ">A\nAS\n"),
        (
            "AF3_INPUT_JSON",
            "input.json",
            json.dumps(
                {
                    "sequences": [
                        {"protein": {"id": ["A"], "sequence": "AS"}}
                    ]
                }
            ),
        ),
    ],
)
def test_af3_exact_input_sequence_reports_no_missing_residues(
    tmp_path: Path,
    reference_type: str,
    filename: str,
    content: str,
) -> None:
    pdb = tmp_path / "source.pdb"
    pdb.write_text(PDB_OBSERVED_AS, encoding="utf-8")
    structure = tmp_path / "af3_output.cif"
    write_mmcif_from_pdb(pdb, structure)
    reference = tmp_path / filename
    reference.write_text(content, encoding="utf-8")

    observations, manifest = run_classification(
        tmp_path,
        structure,
        "AF3_CIF",
        sequence_references=[
            {
                "type": reference_type,
                "path": str(reference),
                "sha256": digest(reference),
            }
        ],
    )

    check = check_for_chain(observations, "A")
    assert check["status"] == "NO_MISSING_RESIDUES"
    assert check["missing_residue_count"] == 0
    assert not issue_records(observations, "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE")
    assert manifest["sequence_references"][0]["reference_type"] == reference_type


def test_af3_longer_sequence_requires_author_source_resids(tmp_path: Path) -> None:
    pdb = tmp_path / "source.pdb"
    pdb.write_text(PDB_OBSERVED_AS, encoding="utf-8")
    structure = tmp_path / "af3_output.cif"
    write_mmcif_from_pdb(pdb, structure)
    reference = tmp_path / "input.fasta"
    reference.write_text(">A\nAGS\n", encoding="utf-8")

    observations, _manifest = run_classification(
        tmp_path,
        structure,
        "AF3_CIF",
        sequence_references=[
            {
                "type": "FASTA",
                "path": str(reference),
                "sha256": digest(reference),
            }
        ],
    )

    assert not missing_records(observations)
    issues = issue_records(observations, "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE")
    assert len(issues) == 1
    assert issues[0]["subject"]["expected_sequence"] == ["ALA", "GLY", "SER"]
    assert issues[0]["subject"]["observed_sequence"] == ["ALA", "SER"]
    check = check_for_chain(observations, "A")
    assert check["status"] == "MAPPING_UNRESOLVED"
    assert check["reason"] == "AUTHOR_SOURCE_RESIDS_FOR_MISSING_RESIDUES_UNAVAILABLE"


def test_af3_sequence_reference_chain_id_must_match_exactly(tmp_path: Path) -> None:
    pdb = tmp_path / "source.pdb"
    pdb.write_text(PDB_OBSERVED_AS, encoding="utf-8")
    structure = tmp_path / "af3_output.cif"
    write_mmcif_from_pdb(pdb, structure)
    reference = tmp_path / "input.fasta"
    reference.write_text(">B\nAS\n", encoding="utf-8")

    observations, _manifest = run_classification(
        tmp_path,
        structure,
        "AF3_CIF",
        sequence_references=[
            {
                "type": "FASTA",
                "path": str(reference),
                "sha256": digest(reference),
            }
        ],
    )

    check = check_for_chain(observations, "A")
    assert check["status"] == "MAPPING_UNRESOLVED"
    assert check["reason"] == "AF3_INPUT_CHAIN_NOT_FOUND"
    issues = issue_records(observations, "SEQUENCE_REFERENCE_CONFLICT")
    assert len(issues) == 1
    assert issues[0]["subject"] == {"source_chain_id": "A"}

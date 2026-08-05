from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def write_ccd(path: Path, component_id: str, atoms: list[tuple[str, str]]) -> None:
    rows = "\n".join(f"{component_id} {name} {name} {element}" for name, element in atoms)
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


def run_engine(tmp_path: Path, structure: Path, *, ccd_dirs: list[Path] | None = None, force_field: Path | None = None):
    config = {
        "structure": {"path": str(structure), "sha256": digest(structure), "source_format": "PDB", "selected_model_id": "1"},
        "classification": {"mode": "FORCE_FIELD_ANALYSIS" if force_field else "REGISTRY"},
        "output": {"observations_path": str(tmp_path / "observations.yaml"), "reference_manifest_path": str(tmp_path / "manifest.yaml")},
    }
    if ccd_dirs is not None:
        config["ccd"] = {"local_reference_dirs": [str(path) for path in ccd_dirs], "retrieval_policy": "CACHE_ONLY"}
    if force_field is not None:
        config["force_field"] = {"root_path": str(force_field)}
    return execute_classification(config, SCRIPTS)


def test_multiple_altlocs_skip_heavy_atom_comparison(tmp_path: Path) -> None:
    structure = tmp_path / "altloc.pdb"
    structure.write_text(
        """ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA AALA A   1       1.400   0.000   0.000  0.50 20.00           C
ATOM      3  CA BALA A   1       1.500   0.000   0.000  0.50 20.00           C
ATOM      4  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      5  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      6  CB AALA A   1       1.400   1.500   0.000  0.50 20.00           C
ATOM      7  CB BALA A   1       1.500   1.500   0.000  0.50 20.00           C
END
""",
        encoding="utf-8",
    )
    ccd = tmp_path / "ccd"
    ccd.mkdir()
    write_ccd(ccd / "ALA.cif", "ALA", [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")])
    observations, _manifest, *_ = run_engine(tmp_path, structure, ccd_dirs=[ccd])
    record = observations["residue_records"][0]
    assert record["conformation_observation"]["status"] == "MULTIPLE_CONFORMATIONS"
    assert record["heavy_atom_check"]["execution_status"] == "NOT_PERFORMED"


def test_duplicate_nonwater_rtp_name_requires_confirmation(tmp_path: Path) -> None:
    structure = tmp_path / "ala.pdb"
    structure.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N\nEND\n", encoding="utf-8")
    force_field = tmp_path / "test.ff"
    force_field.mkdir()
    for name in ("one.rtp", "two.rtp"):
        (force_field / name).write_text("[ ALA ]\n [ atoms ]\n N N 0.0 1\n", encoding="utf-8")
    observations, _manifest, *_ = run_engine(tmp_path, structure, force_field=force_field)
    assert any(item["issue_type"] == "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE" for item in observations["unresolved_observations"])


def test_duplicate_water_rtp_names_do_not_create_heavy_atom_work(tmp_path: Path) -> None:
    structure = tmp_path / "water.pdb"
    structure.write_text("HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00 20.00           O\nEND\n", encoding="utf-8")
    force_field = tmp_path / "test.ff"
    force_field.mkdir()
    for name in ("one.rtp", "two.rtp"):
        (force_field / name).write_text("[ HOH ]\n [ atoms ]\n O OW 0.0 1\n", encoding="utf-8")
    observations, _manifest, *_ = run_engine(tmp_path, structure, force_field=force_field)
    record = observations["residue_records"][0]
    assert record["classification_observation"]["topology_class"] == "SOLVENT_COMPONENT"
    assert record["heavy_atom_check"]["execution_status"] == "NOT_APPLICABLE"
    assert not any(item["issue_type"] == "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE" for item in observations["unresolved_observations"])


def test_identical_exact_local_ccd_candidates_collapse_by_hash(tmp_path: Path) -> None:
    structure = tmp_path / "ala.pdb"
    structure.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N\nEND\n", encoding="utf-8")
    roots = [tmp_path / "local_1", tmp_path / "local_2"]
    for root in roots:
        root.mkdir()
        write_ccd(root / "ALA.cif", "ALA", [("N", "N")])
    observations, manifest, *_ = run_engine(tmp_path, structure, ccd_dirs=roots)
    entry = next(item for item in manifest["ccd_components"] if item["component_id"] == "ALA")
    assert entry["status"] == "LOADED"
    assert observations["residue_records"][0]["heavy_atom_check"]["findings"] == []


def test_conflicting_exact_local_ccd_candidates_require_confirmation(tmp_path: Path) -> None:
    structure = tmp_path / "ala.pdb"
    structure.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N\nEND\n", encoding="utf-8")
    first, second = tmp_path / "local_1", tmp_path / "local_2"
    first.mkdir(); second.mkdir()
    write_ccd(first / "ALA.cif", "ALA", [("N", "N")])
    write_ccd(second / "ALA.cif", "ALA", [("N", "N"), ("CA", "C")])
    observations, manifest, *_ = run_engine(tmp_path, structure, ccd_dirs=[first, second])
    entry = next(item for item in manifest["ccd_components"] if item["component_id"] == "ALA")
    assert entry["status"] == "CONFLICT"
    assert any(item["issue_type"] == "CCD_COMPONENT_DEFINITION_CONFLICT" for item in observations["unresolved_observations"])

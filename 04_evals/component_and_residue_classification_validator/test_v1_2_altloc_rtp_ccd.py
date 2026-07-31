from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from ccd_reference import acquire_ccd_template
from classification_engine import execute_classification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_ccd(path: Path, component_id: str, atoms: list[tuple[str, str]]) -> None:
    rows = "\n".join(
        f"{component_id} {atom_name} {atom_name} {element}"
        for atom_name, element in atoms
    )
    path.parent.mkdir(parents=True, exist_ok=True)
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


def registry_config(structure: Path, local_ccd: Path, tmp_path: Path) -> dict:
    return {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "ccd": {
            "local_reference_dirs": [str(local_ccd)],
            "retrieval_policy": "CACHE_ONLY",
        },
        "output": {
            "observations_path": str(tmp_path / "classification_observations.yaml"),
            "reference_manifest_path": str(tmp_path / "reference_manifest.yaml"),
        },
    }


def force_field_config(structure: Path, force_field: Path, tmp_path: Path) -> dict:
    return {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "FORCE_FIELD_ANALYSIS"},
        "force_field": {"root_path": str(force_field)},
        "ccd": {"retrieval_policy": "CACHE_ONLY"},
        "output": {
            "observations_path": str(tmp_path / "classification_observations.yaml"),
            "reference_manifest_path": str(tmp_path / "reference_manifest.yaml"),
        },
    }


def test_multiple_altlocs_skip_heavy_atom_comparison(tmp_path: Path) -> None:
    structure = tmp_path / "altloc.pdb"
    structure.write_text(
        """ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   ALA A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  CB AALA A   1       1.400   1.500   0.000  0.60 20.00           C
ATOM      6  CB BALA A   1       1.500   1.600   0.100  0.40 20.00           C
END
""",
        encoding="utf-8",
    )
    local_ccd = tmp_path / "ccd"
    write_ccd(
        local_ccd / "ALA.cif",
        "ALA",
        [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")],
    )

    observations, _manifest, *_ = execute_classification(
        registry_config(structure, local_ccd, tmp_path),
        SCRIPTS,
    )

    record = observations["residue_records"][0]
    assert record["conformation_observation"] == {
        "status": "MULTIPLE_CONFORMATIONS",
        "altloc_ids": ["A", "B"],
    }
    assert record["heavy_atom_check"]["status"] == "NOT_PERFORMED"
    assert record["heavy_atom_check"]["reason"] == "MULTIPLE_CONFORMATIONS_PRESENT"
    assert observations["summary"]["multiple_conformation_residue_count"] == 1
    assert observations["summary"]["heavy_atom_issue_count"] == 0


def test_duplicate_nonwater_rtp_name_requires_confirmation(tmp_path: Path) -> None:
    structure = tmp_path / "three_residues.pdb"
    structure.write_text(
        """ATOM      1  N   GLY A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  GLY A   1       1.400   0.000   0.000  1.00 20.00           C
ATOM      3  C   GLY A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  O   GLY A   1       3.800   0.000   0.000  1.00 20.00           O
ATOM      5  N   ALA A   2       3.000   1.300   0.000  1.00 20.00           N
ATOM      6  CA  ALA A   2       4.400   1.300   0.000  1.00 20.00           C
ATOM      7  C   ALA A   2       5.800   1.300   0.000  1.00 20.00           C
ATOM      8  O   ALA A   2       6.800   1.300   0.000  1.00 20.00           O
ATOM      9  CB  ALA A   2       4.400   2.800   0.000  1.00 20.00           C
ATOM     10  N   GLY A   3       6.000   2.600   0.000  1.00 20.00           N
ATOM     11  CA  GLY A   3       7.400   2.600   0.000  1.00 20.00           C
ATOM     12  C   GLY A   3       8.800   2.600   0.000  1.00 20.00           C
ATOM     13  O   GLY A   3       9.800   2.600   0.000  1.00 20.00           O
END
""",
        encoding="utf-8",
    )
    force_field = tmp_path / "duplicate.ff"
    force_field.mkdir()
    (force_field / "aminoacids.rtp").write_text(
        """[ bondedtypes ]
1 1 9 4 1 3 1 0
[ GLY ]
 [ atoms ]
 N N -0.3 1
 CA CT 0.1 2
 C C 0.5 3
 O O -0.3 4
[ ALA ]
 [ atoms ]
 N N -0.3 1
 CA CT 0.1 2
 C C 0.5 3
 O O -0.3 4
 CB CT 0.0 5
""",
        encoding="utf-8",
    )
    (force_field / "duplicate.rtp").write_text(
        """[ ALA ]
 [ atoms ]
 N N -0.3 1
 CA CT 0.1 2
 C C 0.5 3
 O O -0.3 4
 CB CT 0.0 5
""",
        encoding="utf-8",
    )

    observations, _manifest, *_ = execute_classification(
        force_field_config(structure, force_field, tmp_path),
        SCRIPTS,
    )

    duplicate_issues = [
        item
        for item in observations["unresolved_observations"]
        if item["issue_type"] == "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE"
    ]
    assert len(duplicate_issues) == 1
    assert duplicate_issues[0]["subject"]["residue_name"] == "ALA"
    assert len(duplicate_issues[0]["subject"]["template_files"]) == 2
    middle = next(
        record
        for record in observations["residue_records"]
        if record["source_resid"]["number"] == "2"
    )
    assert middle["classification_observation"]["primary_source"] == "SKILL_REGISTRY"
    assert middle["heavy_atom_check"]["status"] == "REFERENCE_TEMPLATE_UNAVAILABLE"
    assert middle["heavy_atom_check"]["reason"] == "RTP_TEMPLATE_NOT_RESOLVED"


def test_duplicate_water_rtp_names_are_allowed_without_heavy_atom_check(tmp_path: Path) -> None:
    structure = tmp_path / "water.pdb"
    structure.write_text(
        """HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00 20.00           O
END
""",
        encoding="utf-8",
    )
    force_field = tmp_path / "water.ff"
    force_field.mkdir()
    water_rtp = """[ HOH ]
 [ atoms ]
 O OW -0.8 1
 H1 HW 0.4 2
 H2 HW 0.4 3
"""
    (force_field / "tip3p.rtp").write_text(water_rtp, encoding="utf-8")
    (force_field / "opc.rtp").write_text(water_rtp, encoding="utf-8")

    observations, manifest, *_ = execute_classification(
        force_field_config(structure, force_field, tmp_path),
        SCRIPTS,
    )

    assert not any(
        item["issue_type"] == "DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE"
        for item in observations["unresolved_observations"]
    )
    solvent_group = next(
        group for group in observations["chain_groups"] if group["group_type"] == "SOLVENT_GROUP"
    )
    assert solvent_group["residue_name"] == "HOH"
    assert solvent_group["instance_count"] == 1
    assert len(observations["residue_records"]) == 1
    water = observations["residue_records"][0]
    assert water["chain_index"] == solvent_group["chain_index"]
    assert water["source_identity"]["source_residue_name"] == "HOH"
    assert water["source_identity"]["source_resid"]["number"] == "1"
    assert water["classification_observation"]["topology_class"] == "SOLVENT_COMPONENT"
    assert manifest["force_field"]["status"] == "LOADED"
    assert len(manifest["force_field"]["files"]) == 2


def test_identical_local_ccd_candidates_collapse_by_hash(tmp_path: Path) -> None:
    first = tmp_path / "local_1"
    second = tmp_path / "local_2"
    write_ccd(first / "LIG.cif", "LIG", [("C1", "C"), ("O1", "O")])
    write_ccd(second / "LIG.cif", "LIG", [("C1", "C"), ("O1", "O")])

    template, manifest, issue = acquire_ccd_template(
        "LIG",
        ["LIG"],
        project_snapshot_dir=tmp_path / "snapshot",
        local_reference_dirs=[first, second],
        shared_cache_path=None,
        retrieval_policy="CACHE_ONLY",
    )

    assert issue is None
    assert template is not None
    assert manifest["retrieval"]["source"] == "LOCAL_REFERENCE_DIRECTORY"
    assert manifest["validation"]["status"] == "VALID"
    assert template.snapshot_path.is_file()


def test_conflicting_local_ccd_candidates_require_confirmation(tmp_path: Path) -> None:
    first = tmp_path / "local_1"
    second = tmp_path / "local_2"
    write_ccd(first / "LIG.cif", "LIG", [("C1", "C")])
    write_ccd(second / "LIG.cif", "LIG", [("C1", "C"), ("O1", "O")])

    template, manifest, issue = acquire_ccd_template(
        "LIG",
        ["LIG"],
        project_snapshot_dir=tmp_path / "snapshot",
        local_reference_dirs=[first, second],
        shared_cache_path=None,
        retrieval_policy="CACHE_ONLY",
    )

    assert template is None
    assert manifest["retrieval"]["status"] == "MULTIPLE_LOCAL_CANDIDATES"
    assert issue is not None
    assert issue["issue_type"] == "MULTIPLE_LOCAL_CCD_CANDIDATES"
    assert len(issue["subject"]["candidate_paths"]) == 2
    assert not (tmp_path / "snapshot" / "LIG.cif").exists()


def test_project_ccd_snapshot_is_authoritative_over_local_conflicts(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    first = tmp_path / "local_1"
    second = tmp_path / "local_2"
    write_ccd(snapshot / "LIG.cif", "LIG", [("C1", "C")])
    write_ccd(first / "LIG.cif", "LIG", [("C1", "C"), ("O1", "O")])
    write_ccd(second / "LIG.cif", "LIG", [("C1", "C"), ("N1", "N")])

    template, manifest, issue = acquire_ccd_template(
        "LIG",
        ["LIG"],
        project_snapshot_dir=snapshot,
        local_reference_dirs=[first, second],
        shared_cache_path=None,
        retrieval_policy="CACHE_ONLY",
    )

    assert issue is None
    assert template is not None
    assert template.heavy_atom_names == ("C1",)
    assert manifest["retrieval"]["source"] == "PROJECT_SNAPSHOT"
    assert manifest["retrieval"]["status"] == "AVAILABLE_PROJECT_SNAPSHOT"


def test_shared_ccd_cache_is_used_after_local_sources_are_absent(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    write_ccd(cache / "LIG.cif", "LIG", [("C1", "C"), ("O1", "O")])

    template, manifest, issue = acquire_ccd_template(
        "LIG",
        ["LIG"],
        project_snapshot_dir=tmp_path / "snapshot",
        local_reference_dirs=[tmp_path / "empty_local"],
        shared_cache_path=cache,
        retrieval_policy="CACHE_ONLY",
    )

    assert issue is None
    assert template is not None
    assert manifest["retrieval"]["source"] == "SHARED_CACHE"
    assert manifest["retrieval"]["status"] == "AVAILABLE_SHARED_CACHE"
    assert template.snapshot_path.is_file()

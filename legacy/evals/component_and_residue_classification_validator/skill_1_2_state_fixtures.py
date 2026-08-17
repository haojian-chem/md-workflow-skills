from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import yaml


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def heavy_check() -> dict:
    comparison = {
        "missing_expected_atom_names": [],
        "unexpected_observed_atom_names": [],
    }
    return {
        "execution_status": "COMPLETED",
        "findings": [],
        "reference_type": None,
        "reference_name": None,
        "exact_comparison": comparison,
        "atom_name_mapping_candidates": [],
        "mapping_resolution_status": "NOT_APPLICABLE",
        "effective_comparison": comparison,
        "reason": None,
    }


def group(
    chain_index: int,
    group_type: str,
    *,
    source_chain_id: str | None,
    entity_id: str | None,
    residue_name: str | None = None,
) -> dict:
    value = {
        "chain_index": chain_index,
        "group_type": group_type,
        "source_chain_id": source_chain_id,
        "entity_id": entity_id,
        "instance_count": 1,
        "linked_polymer_chain_indices": [],
        "source_associations": [],
    }
    if residue_name is not None:
        value["residue_name"] = residue_name
    return value


def residue_record(
    chain_index: int,
    chain_id: str,
    residue_number: str,
    residue_name: str,
    polymer_class: str,
    topology_class: str,
    *,
    primary_source: str,
) -> dict:
    source_identity = {
        "source_model_id": "1",
        "source_chain_id": chain_id,
        "source_resid": {"number": residue_number, "insertion_code": None},
        "source_residue_name": residue_name,
    }
    current_identity = {
        "current_model_id": "1",
        "current_chain_id": chain_id,
        "current_resid": {"number": residue_number, "insertion_code": None},
        "current_residue_name": residue_name,
    }
    classification = {
        "component_id": residue_name,
        "polymer_class": polymer_class,
        "topology_class": topology_class,
        "resolution_status": "RESOLVED",
        "primary_source": primary_source,
        "evidence": ["current-state test fixture"],
    }
    return {
        "source_identity": source_identity,
        "current_identity": current_identity,
        "chain_index": chain_index,
        "baseline_chain_index": chain_index,
        "source_chain_id": chain_id,
        "source_resid": {"number": residue_number, "insertion_code": None},
        "residue_name": residue_name,
        "presence_status": "OBSERVED",
        "sequence_position": None,
        "classification_observation": copy.deepcopy(classification),
        "baseline_classification_observation": copy.deepcopy(classification),
        "conformation_observation": {
            "status": "SINGLE_CONFORMATION",
            "altloc_ids": [],
        },
        "heavy_atom_check": heavy_check(),
    }


def current_observations(
    structure: Path,
    groups: list[dict],
    records: list[dict],
) -> dict:
    return {
        "schema_version": "1.0",
        "input": {
            "structure_path": str(structure.resolve()),
            "structure_sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
            "classification_mode": "REGISTRY",
        },
        "completed_checks": {
            "baseline_classification": "COMPLETED",
            "possible_connections": "PENDING",
            "possible_coordination": "PENDING",
            "heavy_atom_check": "COMPLETED",
            "missing_residue_check": "COMPLETED",
        },
        "check_outputs": {
            "possible_connections": {"path": None, "sha256": None},
            "possible_coordination": {"path": None, "sha256": None},
        },
        "baseline_chain_groups": copy.deepcopy(groups),
        "entities": [],
        "chain_groups": copy.deepcopy(groups),
        "residue_records": copy.deepcopy(records),
        "missing_residue_checks": [],
        "connection_observations": [],
        "coordination_observations": [],
        "unresolved_observations": [],
        "summary": {
            "entity_count": 0,
            "chain_group_count": len(groups),
            "recorded_residue_count": len(records),
            "observed_residue_count": len(records),
            "missing_expected_residue_count": 0,
            "unresolved_observation_count": 0,
            "multiple_conformation_residue_count": 0,
            "heavy_atom_issue_count": 0,
        },
    }


def model_scope(structure: Path) -> dict:
    return {
        "schema_version": "1.0",
        "input_structure": {
            "path": str(structure.resolve()),
            "sha256": digest(structure),
            "source_format": "PDB",
        },
        "model_count": 1,
        "models": [
            {
                "model_id": "1",
                "chain_count": 2,
                "residue_count": 2,
                "atom_count": 5,
            }
        ],
        "selection": {"status": "AUTO_SELECTED", "selected_model_id": "1"},
    }


def reference_manifest(
    coordination_path: Path | None,
    connection_path: Path | None = None,
) -> dict:
    def reference(path: Path | None) -> dict:
        if path is None:
            return {"path": None, "sha256": None, "status": "NOT_PROVIDED"}
        return {
            "path": str(path.resolve()),
            "sha256": digest(path),
            "status": "LOADED",
        }

    return {
        "schema_version": "1.0",
        "classification_mode": "REGISTRY",
        "project_files": {
            "residue_definitions": {
                "path": None,
                "sha256": None,
                "status": "NOT_PROVIDED",
            }
        },
        "skill_references": [],
        "force_field": None,
        "ccd_components": [],
        "sequence_references": [],
        "relation_definition_files": {
            "possible_connections": reference(connection_path),
            "possible_coordination": reference(coordination_path),
        },
    }

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import gemmi
import yaml
from jsonschema import Draft202012Validator


class SelectionToolError(RuntimeError):
    def __init__(self, code: str, message: str, *, blocked: bool = False):
        super().__init__(message)
        self.code = code
        self.blocked = blocked


class _StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _StrictSafeLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            mark = key_node.start_mark
            raise SelectionToolError(
                "SELECTION_SPEC_MISSING_OR_INVALID",
                f"duplicate YAML key {key!r} at line {mark.line + 1}, column {mark.column + 1}",
                blocked=True,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def read_yaml_strict(path: Path) -> Any:
    if path.is_symlink():
        raise SelectionToolError("VALIDATOR_INPUT_INCOMPLETE", f"symlink input is not accepted: {path}", blocked=True)
    if not path.is_file() or path.stat().st_size == 0:
        raise SelectionToolError("VALIDATOR_INPUT_INCOMPLETE", f"missing or empty YAML input: {path}", blocked=True)
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.load(handle, Loader=_StrictSafeLoader)
    except SelectionToolError:
        raise
    except Exception as exc:
        raise SelectionToolError("SELECTION_SPEC_MISSING_OR_INVALID", f"cannot parse YAML {path}: {exc}", blocked=True) from exc


def sha256_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise SelectionToolError("VALIDATOR_INPUT_INCOMPLETE", f"file not found or symlink: {path}", blocked=True)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def file_identity(path: Path, *, include_size: bool = False, format_name: str | None = None) -> dict[str, Any]:
    output: dict[str, Any] = {"path": str(path.resolve()), "sha256": sha256_file(path)}
    if include_size:
        output["size_bytes"] = path.stat().st_size
    if format_name is not None:
        output["format"] = format_name
    return output


def require_sha256(path: Path, expected: str, code: str = "SOURCE_OR_CLASSIFICATION_HASH_MISMATCH") -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise SelectionToolError(code, f"SHA-256 mismatch for {path}: expected {expected}, observed {actual}", blocked=True)


def validate_document(document: Any, schema_path: Path, *, code: str = "SELECTION_SPEC_MISSING_OR_INVALID") -> None:
    schema = read_yaml_strict(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        details = []
        for error in errors[:20]:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{location}: {error.message}")
        raise SelectionToolError(code, f"schema validation failed for {schema_path}: " + "; ".join(details), blocked=True)


def yaml_text(document: Any) -> str:
    return yaml.safe_dump(document, sort_keys=False, allow_unicode=True, default_flow_style=False)


def atomic_write_yaml(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(yaml_text(document), encoding="utf-8")
    os.replace(tmp, path)


def atomic_replace_file(tmp: Path, final: Path) -> None:
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, final)


def parse_structure(path: Path) -> gemmi.Structure:
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise SelectionToolError("VALIDATOR_INPUT_INCOMPLETE", f"missing, empty, or symlink structure: {path}", blocked=True)
    try:
        structure = gemmi.read_structure(str(path))
    except Exception as exc:
        raise SelectionToolError("SELECTION_INTERNAL_FAILURE", f"cannot parse structure {path}: {exc}") from exc
    if len(structure) == 0:
        raise SelectionToolError("SELECTION_INTERNAL_FAILURE", f"structure has no models: {path}")
    return structure


def clean_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text in {"", "\x00", ".", "?"} or not text.strip():
        return None
    return text.strip()


def model_id(model: gemmi.Model) -> str:
    return str(model.num)


def selected_model(structure: gemmi.Structure, selected_model_id: str) -> gemmi.Model:
    matches = [model for model in structure if model_id(model) == selected_model_id]
    if len(matches) != 1:
        raise SelectionToolError(
            "SELECTION_REFERENCES_UNKNOWN_OBJECT",
            f"selected model {selected_model_id!r} resolved to {len(matches)} models",
            blocked=True,
        )
    return matches[0]


def residue_key(model: gemmi.Model, chain: gemmi.Chain, residue: gemmi.Residue) -> tuple[str, str, str, str | None, str]:
    return (
        model_id(model),
        str(chain.name),
        str(residue.seqid.num),
        clean_optional_text(residue.seqid.icode),
        str(residue.name),
    )


def residue_key_from_current_identity(identity: dict[str, Any]) -> tuple[str, str, str, str | None, str]:
    resid = identity["current_resid"]
    return (
        str(identity["current_model_id"]),
        "" if identity.get("current_chain_id") is None else str(identity["current_chain_id"]),
        str(resid["number"]),
        clean_optional_text(resid.get("insertion_code")),
        str(identity["current_residue_name"]),
    )


def atom_identity(model: gemmi.Model, chain: gemmi.Chain, residue: gemmi.Residue, atom: gemmi.Atom) -> dict[str, Any]:
    serial = int(atom.serial) if int(atom.serial) > 0 else None
    element = clean_optional_text(atom.element.name) or "X"
    return {
        "model_id": model_id(model),
        "chain_id": str(chain.name),
        "residue_name": str(residue.name),
        "residue_number": str(residue.seqid.num),
        "insertion_code": clean_optional_text(residue.seqid.icode),
        "atom_name": str(atom.name).strip(),
        "altloc": clean_optional_text(atom.altloc),
        "element": element,
        "serial": serial,
    }


def atom_stable_key(identity: dict[str, Any]) -> tuple[Any, ...]:
    return (
        identity["model_id"], identity["chain_id"], identity["residue_name"],
        identity["residue_number"], identity.get("insertion_code"),
        identity["atom_name"], identity.get("altloc"), identity["element"],
    )


@dataclass(frozen=True)
class AtomSnapshot:
    identity: dict[str, Any]
    x: float
    y: float
    z: float
    occupancy: float
    b_iso: float
    charge: int


def atom_snapshots(model: gemmi.Model, selected_residue_keys: set[tuple[str, str, str, str | None, str]] | None = None) -> list[AtomSnapshot]:
    output: list[AtomSnapshot] = []
    seen: set[tuple[Any, ...]] = set()
    for chain in model:
        for residue in chain:
            key = residue_key(model, chain, residue)
            if selected_residue_keys is not None and key not in selected_residue_keys:
                continue
            for atom in residue:
                identity = atom_identity(model, chain, residue, atom)
                stable = atom_stable_key(identity)
                if stable in seen:
                    raise SelectionToolError("SELECTION_INTERNAL_FAILURE", f"duplicate stable atom identity: {stable}")
                seen.add(stable)
                output.append(
                    AtomSnapshot(
                        identity=identity,
                        x=float(atom.pos.x), y=float(atom.pos.y), z=float(atom.pos.z),
                        occupancy=float(atom.occ), b_iso=float(atom.b_iso), charge=int(atom.charge),
                    )
                )
    return output


@dataclass
class SelectionPlan:
    selected_component_ids: list[str]
    excluded_component_ids: list[str]
    selected_residue_ids: list[str]
    excluded_residue_ids: list[str]
    selected_residue_keys: set[tuple[str, str, str, str | None, str]]
    preserved_relations: list[dict[str, Any]]
    excluded_relations: list[dict[str, Any]]
    cross_boundary_coordination: list[dict[str, Any]]
    cross_boundary_covalent_candidates: list[dict[str, Any]]


def relation_ref(relation: dict[str, Any]) -> dict[str, Any]:
    return {
        "relation_id": relation["relation_id"],
        "relation_type": relation["relation_type"],
        "endpoint_1_id": relation["endpoint_1"]["endpoint_id"],
        "endpoint_2_id": relation["endpoint_2"]["endpoint_id"],
    }


def build_selection_plan(classification: dict[str, Any], spec: dict[str, Any]) -> SelectionPlan:
    groups = {item["component_id"]: item for item in classification["chain_groups"]}
    requested = list(spec["selected_component_ids"])
    unknown = sorted(set(requested) - set(groups))
    if unknown:
        raise SelectionToolError(
            "SELECTION_REFERENCES_UNKNOWN_OBJECT",
            f"selection references unknown component IDs: {unknown}",
            blocked=True,
        )
    selected_components = sorted(requested)
    excluded_components = sorted(set(groups) - set(selected_components))
    selected_residues = sorted({rid for cid in selected_components for rid in groups[cid]["residue_ids"]})
    all_observed = {record["residue_id"] for record in classification["residue_records"] if record["presence_status"] == "OBSERVED"}
    excluded_residues = sorted(all_observed - set(selected_residues))
    record_by_id = {record["residue_id"]: record for record in classification["residue_records"]}
    missing = sorted(set(selected_residues) - set(record_by_id))
    if missing:
        raise SelectionToolError("SELECTION_REFERENCES_UNKNOWN_OBJECT", f"component membership references unknown residues: {missing}", blocked=True)
    selected_keys: set[tuple[str, str, str, str | None, str]] = set()
    for residue_id in selected_residues:
        record = record_by_id[residue_id]
        if record["presence_status"] != "OBSERVED" or record["current_identity"] is None:
            raise SelectionToolError("SELECTION_REFERENCES_UNKNOWN_OBJECT", f"selected residue is not observed: {residue_id}", blocked=True)
        selected_keys.add(residue_key_from_current_identity(record["current_identity"]))

    selected_set = set(selected_components)
    preserved: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    cross_coord: list[dict[str, Any]] = []
    cross_candidates: list[dict[str, Any]] = []
    for relation in classification["confirmed_relations"]["covalent_connections"]:
        states = [relation["endpoint_1"]["component_id"] in selected_set, relation["endpoint_2"]["component_id"] in selected_set]
        if states[0] != states[1]:
            raise SelectionToolError(
                "SELECTION_BREAKS_CONFIRMED_COVALENT_LINK",
                f"selection splits confirmed covalent relation {relation['relation_id']}",
                blocked=True,
            )
        (preserved if states[0] else excluded).append(relation_ref(relation))
    for relation in classification["confirmed_relations"]["metal_coordination"]:
        states = [relation["endpoint_1"]["component_id"] in selected_set, relation["endpoint_2"]["component_id"] in selected_set]
        if states[0] and states[1]:
            preserved.append(relation_ref(relation))
        elif not states[0] and not states[1]:
            excluded.append(relation_ref(relation))
        else:
            cross_coord.append(relation_ref(relation))
    for relation in classification["rejected_candidates"]["covalent_connections"]:
        states = [relation["endpoint_1"]["component_id"] in selected_set, relation["endpoint_2"]["component_id"] in selected_set]
        if states[0] != states[1]:
            cross_candidates.append(relation_ref(relation))
    return SelectionPlan(
        selected_component_ids=selected_components,
        excluded_component_ids=excluded_components,
        selected_residue_ids=selected_residues,
        excluded_residue_ids=excluded_residues,
        selected_residue_keys=selected_keys,
        preserved_relations=sorted(preserved, key=lambda x: x["relation_id"]),
        excluded_relations=sorted(excluded, key=lambda x: x["relation_id"]),
        cross_boundary_coordination=sorted(cross_coord, key=lambda x: x["relation_id"]),
        cross_boundary_covalent_candidates=sorted(cross_candidates, key=lambda x: x["relation_id"]),
    )


def endpoint_current_key(endpoint: dict[str, Any]) -> tuple[str, str, str, str | None, str, str, str | None]:
    identity = endpoint["current_identity"]
    resid = identity["current_resid"]
    return (
        str(identity["current_model_id"]),
        "" if identity.get("current_chain_id") is None else str(identity["current_chain_id"]),
        str(resid["number"]), clean_optional_text(resid.get("insertion_code")),
        str(identity["current_residue_name"]), str(identity["current_atom_name"]),
        clean_optional_text(identity.get("current_altloc_id")),
    )


def find_atom_cra(model: gemmi.Model, endpoint: dict[str, Any]) -> tuple[gemmi.Chain, gemmi.Residue, gemmi.Atom]:
    target = endpoint_current_key(endpoint)
    matches: list[tuple[gemmi.Chain, gemmi.Residue, gemmi.Atom]] = []
    for chain in model:
        for residue in chain:
            base = (model_id(model), str(chain.name), str(residue.seqid.num), clean_optional_text(residue.seqid.icode), str(residue.name))
            if base != target[:5]:
                continue
            for atom in residue:
                if (
                    str(atom.name).strip() == target[5]
                    and clean_optional_text(atom.altloc) == target[6]
                ):
                    matches.append((chain, residue, atom))
    if len(matches) != 1:
        raise SelectionToolError("EXPLICIT_CONNECTION_MISMATCH", f"relation endpoint resolved to {len(matches)} atoms: {target}")
    return matches[0]


def add_selected_connections(output: gemmi.Structure, classification: dict[str, Any], selected_component_ids: set[str]) -> None:
    output.connections.clear()
    try:
        output.clear_conect()
    except Exception:
        pass
    model = output[0]
    relations = [
        *classification["confirmed_relations"]["covalent_connections"],
        *classification["confirmed_relations"]["metal_coordination"],
    ]
    counter = 0
    for relation in relations:
        if relation["endpoint_1"]["component_id"] not in selected_component_ids or relation["endpoint_2"]["component_id"] not in selected_component_ids:
            continue
        chain1, residue1, atom1 = find_atom_cra(model, relation["endpoint_1"])
        chain2, residue2, atom2 = find_atom_cra(model, relation["endpoint_2"])
        con = gemmi.Connection()
        counter += 1
        con.name = f"selconn{counter}"
        con.type = gemmi.ConnectionType.Covale if relation["relation_type"] == "COVALENT_CONNECTION" else gemmi.ConnectionType.MetalC
        con.asu = gemmi.Asu.Same
        con.partner1 = gemmi.make_address(chain1, residue1, atom1)
        con.partner2 = gemmi.make_address(chain2, residue2, atom2)
        con.reported_distance = float(atom1.pos.dist(atom2.pos))
        output.connections.append(con)


def pdb_identifier_issues(model: gemmi.Model) -> list[str]:
    issues: list[str] = []
    try:
        model_number = int(model_id(model))
        if not 1 <= model_number <= 9999:
            issues.append(f"model ID out of PDB range: {model_id(model)}")
    except ValueError:
        issues.append(f"model ID is not numeric: {model_id(model)}")
    for chain in model:
        if len(str(chain.name)) > 1:
            issues.append(f"chain ID exceeds one character: {chain.name!r}")
        for residue in chain:
            if not -999 <= int(residue.seqid.num) <= 9999:
                issues.append(f"residue number out of PDB range: {chain.name}:{residue.seqid.num}")
            icode = clean_optional_text(residue.seqid.icode)
            if icode is not None and len(icode) > 1:
                issues.append(f"insertion code exceeds one character: {chain.name}:{residue.seqid}")
            if len(str(residue.name)) > 3:
                issues.append(f"residue name exceeds three characters: {residue.name!r}")
            for atom in residue:
                if len(str(atom.name).strip()) > 4:
                    issues.append(f"atom name exceeds four characters: {atom.name!r}")
                if clean_optional_text(atom.altloc) is not None and len(clean_optional_text(atom.altloc) or "") > 1:
                    issues.append(f"altLoc exceeds one character: {atom.altloc!r}")
                if int(atom.serial) > 99999:
                    issues.append(f"atom serial out of PDB range: {atom.serial}")
                if not (-999.999 <= atom.pos.x <= 9999.999 and -999.999 <= atom.pos.y <= 9999.999 and -999.999 <= atom.pos.z <= 9999.999):
                    issues.append(f"coordinate out of PDB range for {atom.name}")
    return sorted(set(issues))


def write_structure(structure: gemmi.Structure, path: Path, format_name: str) -> None:
    if format_name == "PDB":
        options = gemmi.PdbWriteOptions()
        options.preserve_serial = True
        options.conect_records = False
        structure.write_pdb(str(path), options)
    elif format_name == "MMCIF":
        structure.make_mmcif_document().write_file(str(path))
    else:
        raise SelectionToolError("OUTPUT_FORMAT_MISMATCH", f"unsupported output format: {format_name}")


def tmp_structure_path(final: Path) -> Path:
    return final.with_name(final.stem + ".tmp" + final.suffix)


def close_enough(first: float, second: float, tolerance: float) -> bool:
    return math.isfinite(first) and math.isfinite(second) and abs(first - second) <= tolerance

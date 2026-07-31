from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: str, marker: str, insertion: str) -> None:
    replace_once(path, marker, insertion + marker)


selection_identity = '''#!/usr/bin/env python3
"""Stable identifiers exported by classification result for downstream selection.

The identifiers are deterministic for one source STRUCTURE revision and do not
encode chain_index.  Downstream consumers must treat them as opaque values
materialized by validator 1.2 rather than reconstructing them independently.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable
from urllib.parse import quote


class SelectionIdentityError(ValueError):
    """Raised when an identity cannot be converted into a stable selection ID."""


def _encode(value: Any) -> str:
    return quote("" if value is None else str(value), safe="")


def _required_mapping(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise SelectionIdentityError(f"identity field {key!r} must be a mapping")
    return value


def residue_id_from_source_identity(identity: dict[str, Any]) -> str:
    """Return immutable residue ID from source provenance identity."""
    resid = _required_mapping(identity, "source_resid")
    required = ("source_model_id", "source_residue_name")
    for key in required:
        if not isinstance(identity.get(key), str) or not identity[key]:
            raise SelectionIdentityError(f"identity field {key!r} must be a non-empty string")
    number = resid.get("number")
    if not isinstance(number, str) or not number:
        raise SelectionIdentityError("source_resid.number must be a non-empty string")
    return (
        "residue:v1"
        f"/model/{_encode(identity['source_model_id'])}"
        f"/chain/{_encode(identity.get('source_chain_id'))}"
        f"/name/{_encode(identity['source_residue_name'])}"
        f"/number/{_encode(number)}"
        f"/icode/{_encode(resid.get('insertion_code'))}"
    )


def endpoint_id_from_source_identity(identity: dict[str, Any]) -> str:
    """Return atom endpoint ID for a relation endpoint.

    Relation contracts currently do not carry altLoc, so this endpoint identity
    intentionally ends at the exact atom name within the source residue.
    """
    atom_name = identity.get("source_atom_name")
    if not isinstance(atom_name, str) or not atom_name:
        raise SelectionIdentityError("source_atom_name must be a non-empty string")
    residue_identity = {
        key: identity[key]
        for key in (
            "source_model_id",
            "source_chain_id",
            "source_resid",
            "source_residue_name",
        )
    }
    return f"endpoint:v1/{residue_id_from_source_identity(residue_identity)}/atom/{_encode(atom_name)}"


def _membership_digest(observed: Iterable[str], missing: Iterable[str]) -> str:
    members = [*(f"OBSERVED:{value}" for value in sorted(observed)), *(f"MISSING:{value}" for value in sorted(missing))]
    if not members:
        raise SelectionIdentityError("component must contain at least one observed or missing residue")
    return hashlib.sha256("\\n".join(members).encode("utf-8")).hexdigest()


def component_id_from_members(
    selected_model_id: str,
    group_type: str,
    observed_residue_ids: Iterable[str],
    missing_residue_ids: Iterable[str],
) -> str:
    """Return stable component ID from membership, not from chain_index."""
    if not selected_model_id:
        raise SelectionIdentityError("selected_model_id must be non-empty")
    if not group_type:
        raise SelectionIdentityError("group_type must be non-empty")
    digest = _membership_digest(observed_residue_ids, missing_residue_ids)
    return (
        "component:v1"
        f"/model/{_encode(selected_model_id)}"
        f"/type/{_encode(group_type)}"
        f"/members/{digest}"
    )


def relation_id_from_endpoints(relation_type: str, endpoint_ids: Iterable[str]) -> str:
    """Return stable relation ID independent of evidence status and ordering."""
    endpoints = sorted(endpoint_ids)
    if len(endpoints) != 2 or any(not value for value in endpoints):
        raise SelectionIdentityError("relation ID requires exactly two endpoint IDs")
    digest = hashlib.sha256("\\n".join(endpoints).encode("utf-8")).hexdigest()
    return f"relation:v1/type/{_encode(relation_type)}/endpoints/{digest}"
'''
(ROOT / "02_validators/component_and_residue_classification_validator/scripts/selection_identity.py").write_text(
    selection_identity, encoding="utf-8"
)

replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/classification_engine_core.py",
    "                    item.include_residue_record = False\n",
    "                    # Aggregation changes logical grouping only.  Instance-level residue\n"
    "                    # identity remains available to downstream component selection.\n"
    "                    item.include_residue_record = True\n",
)

replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    "from structure_records import validate_residue_identity_record\n",
    "from structure_records import validate_residue_identity_record\n"
    "from selection_identity import (\n"
    "    component_id_from_members,\n"
    "    endpoint_id_from_source_identity,\n"
    "    relation_id_from_endpoints,\n"
    "    residue_id_from_source_identity,\n"
    ")\n",
)

old_move = '''        for key in nonpoly_natural_keys:
            if key not in record_by_key:
                endpoint = next(
                    endpoint_lookup[endpoint_key]
                    for endpoint_key in component
                    if _natural_key(endpoint_lookup[endpoint_key]) == key
                )
                baseline_group = group_by_index[int(endpoint["chain_index"])]
                record = _special_record_from_endpoint(endpoint, baseline_group)
                records.append(record)
                record_by_key[key] = record
                decrement_by_group[int(endpoint["chain_index"])] += 1
'''
new_move = '''        for key in nonpoly_natural_keys:
            endpoint = next(
                endpoint_lookup[endpoint_key]
                for endpoint_key in component
                if _natural_key(endpoint_lookup[endpoint_key]) == key
            )
            baseline_index = int(endpoint["chain_index"])
            decrement_by_group[baseline_index] += 1
            if key not in record_by_key:
                baseline_group = group_by_index[baseline_index]
                record = _special_record_from_endpoint(endpoint, baseline_group)
                records.append(record)
                record_by_key[key] = record
'''
replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    old_move,
    new_move,
)

replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    '''    individual_group_keys = {
        int(record["chain_index"]): key
        for key, record in record_by_key.items()
    }
''',
    "",
)
replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    '''        individual_key = individual_group_keys.get(baseline_index)
        if individual_key in moved_keys:
            count = 0
''',
    "",
)

id_function = '''

def _assign_selection_contract_ids(
    selected_model_id: str,
    groups: list[dict[str, Any]],
    records: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> None:
    """Materialize opaque stable IDs required by component selection v1."""
    observed_by_group: defaultdict[int, list[str]] = defaultdict(list)
    missing_by_group: defaultdict[int, list[str]] = defaultdict(list)
    residue_ids: set[str] = set()
    for record in records:
        residue_id = residue_id_from_source_identity(record["source_identity"])
        if residue_id in residue_ids:
            raise ClassificationToolError(f"duplicate residue selection identity: {residue_id}")
        residue_ids.add(residue_id)
        record["residue_id"] = residue_id
        chain_index = int(record["chain_index"])
        if record["presence_status"] == "OBSERVED":
            observed_by_group[chain_index].append(residue_id)
        else:
            missing_by_group[chain_index].append(residue_id)

    component_by_chain: dict[int, str] = {}
    component_ids: set[str] = set()
    for group in groups:
        chain_index = int(group["chain_index"])
        observed = sorted(observed_by_group.get(chain_index, []))
        missing = sorted(missing_by_group.get(chain_index, []))
        component_id = component_id_from_members(
            selected_model_id,
            group["group_type"],
            observed,
            missing,
        )
        if component_id in component_ids:
            raise ClassificationToolError(f"duplicate component selection identity: {component_id}")
        component_ids.add(component_id)
        component_by_chain[chain_index] = component_id
        group["component_id"] = component_id
        group["residue_ids"] = observed
        group["missing_residue_ids"] = missing

    for record in records:
        chain_index = int(record["chain_index"])
        if chain_index not in component_by_chain:
            raise ClassificationToolError(
                f"residue chain_index {chain_index} has no final component"
            )
        record["component_id"] = component_by_chain[chain_index]

    relation_ids: set[str] = set()
    for relation in relations:
        endpoint_ids: list[str] = []
        for endpoint_field in ("endpoint_1", "endpoint_2"):
            endpoint = relation[endpoint_field]
            chain_index = int(endpoint["chain_index"])
            if chain_index not in component_by_chain:
                raise ClassificationToolError(
                    f"relation endpoint chain_index {chain_index} has no final component"
                )
            endpoint["residue_id"] = residue_id_from_source_identity(
                endpoint["source_identity"]
            )
            endpoint["endpoint_id"] = endpoint_id_from_source_identity(
                endpoint["source_identity"]
            )
            endpoint["component_id"] = component_by_chain[chain_index]
            endpoint_ids.append(endpoint["endpoint_id"])
        relation_id = relation_id_from_endpoints(
            relation["relation_type"], endpoint_ids
        )
        if relation_id in relation_ids:
            raise ClassificationToolError(f"duplicate relation selection identity: {relation_id}")
        relation_ids.add(relation_id)
        relation["relation_id"] = relation_id
'''
append_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    "\ndef _render_report(result: dict[str, Any], confirmation: dict[str, Any]) -> str:\n",
    id_function,
)

replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    '''    final_groups, records, endpoint_final_chain = _integrate_chain_groups_and_records(
        observations,
        records,
        confirmed_relations,
    )

    output = _required_mapping(config, "output")
''',
    '''    final_groups, records, endpoint_final_chain = _integrate_chain_groups_and_records(
        observations,
        records,
        confirmed_relations,
    )
    for relation in rejected_relations:
        for endpoint_field in ("endpoint_1", "endpoint_2"):
            endpoint = relation[endpoint_field]
            key = _natural_key(endpoint)
            if key in endpoint_final_chain:
                endpoint["chain_index"] = endpoint_final_chain[key]
    _assign_selection_contract_ids(
        str(selected_model_id),
        final_groups,
        records,
        [*confirmed_relations, *rejected_relations],
    )

    output = _required_mapping(config, "output")
''',
)

old_solvent = '''    solvent_count = sum(
        group["instance_count"]
        for group in final_groups
        if group["group_type"] == "SOLVENT_GROUP"
    ) + sum(
        record["classification"]["topology_class"] == "SOLVENT_COMPONENT"
        for record in records
    )
    ion_count = sum(
        group["instance_count"]
        for group in final_groups
        if group["group_type"] == "ION_GROUP"
    ) + sum(
        record["classification"]["topology_class"] == "ION_COMPONENT"
        for record in records
    )
'''
new_solvent = '''    solvent_count = sum(
        record["classification"]["topology_class"] == "SOLVENT_COMPONENT"
        for record in records
    )
    ion_count = sum(
        record["classification"]["topology_class"] == "ION_COMPONENT"
        for record in records
    )
'''
replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    old_solvent,
    new_solvent,
)

replace_once(
    "02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py",
    '''        "selected_model_id": str(selected_model_id),
        "classification_mode": observations["input"]["classification_mode"],
        "source_hashes": {
''',
    '''        "selected_model_id": str(selected_model_id),
        "classification_mode": observations["input"]["classification_mode"],
        "source_structure": {
            "path": observations["input"]["structure_path"],
            "sha256": structure_hash,
            "source_format": observations["input"]["source_format"],
        },
        "source_hashes": {
''',
)

# classification_result schema
schema_path = ROOT / "02_validators/component_and_residue_classification_validator/schemas/classification_result.schema.yaml"
schema = schema_path.read_text(encoding="utf-8")
schema = schema.replace(
    "  - classification_mode\n  - source_hashes\n",
    "  - classification_mode\n  - source_structure\n  - source_hashes\n",
    1,
)
schema = schema.replace(
    '''  classification_mode:
    enum: [REGISTRY, FORCE_FIELD_ANALYSIS]
  source_hashes:
''',
    '''  classification_mode:
    enum: [REGISTRY, FORCE_FIELD_ANALYSIS]
  source_structure:
    type: object
    additionalProperties: false
    required: [path, sha256, source_format]
    properties:
      path: {type: string, minLength: 1}
      sha256: {$ref: "#/$defs/sha256"}
      source_format: {enum: [PDB, MMCIF, AF3_CIF]}
  source_hashes:
''',
    1,
)
schema = schema.replace(
    '''      - chain_index
      - grouping_status
''',
    '''      - component_id
      - residue_ids
      - missing_residue_ids
      - chain_index
      - grouping_status
''',
    1,
)
schema = schema.replace(
    '''    properties:
      chain_index: {type: integer, minimum: 1}
''',
    '''    properties:
      component_id: {type: string, minLength: 1}
      residue_ids:
        type: array
        uniqueItems: true
        items: {type: string, minLength: 1}
      missing_residue_ids:
        type: array
        uniqueItems: true
        items: {type: string, minLength: 1}
      chain_index: {type: integer, minimum: 1}
''',
    1,
)
schema = schema.replace(
    '''      - source_identity
      - current_identity
      - chain_index
''',
    '''      - residue_id
      - component_id
      - source_identity
      - current_identity
      - chain_index
''',
    1,
)
schema = schema.replace(
    '''    properties:
      source_identity:
        $ref: "#/$defs/source_residue_identity"
''',
    '''    properties:
      residue_id: {type: string, minLength: 1}
      component_id: {type: string, minLength: 1}
      source_identity:
        $ref: "#/$defs/source_residue_identity"
''',
    1,
)
schema = schema.replace(
    '''    required: [source_identity, current_identity, chain_index, source_chain_id, source_resid, residue_name, atom_name]
    properties:
      source_identity:
''',
    '''    required: [endpoint_id, residue_id, component_id, source_identity, current_identity, chain_index, source_chain_id, source_resid, residue_name, atom_name]
    properties:
      endpoint_id: {type: string, minLength: 1}
      residue_id: {type: string, minLength: 1}
      component_id: {type: string, minLength: 1}
      source_identity:
''',
    1,
)
schema = schema.replace(
    '''    required:
      - relation_type
      - endpoint_1
''',
    '''    required:
      - relation_id
      - relation_type
      - endpoint_1
''',
    1,
)
schema = schema.replace(
    '''    properties:
      relation_type:
        enum: [COVALENT_CONNECTION, METAL_COORDINATION]
''',
    '''    properties:
      relation_id: {type: string, minLength: 1}
      relation_type:
        enum: [COVALENT_CONNECTION, METAL_COORDINATION]
''',
    1,
)
schema_path.write_text(schema, encoding="utf-8")

# Selection semantics and docs.
replace_once(
    "02_operations/chain_and_component_selection/references/selection_rules.md",
    '''Every selected object must be named by a `component_id` present in the classification result.

A component contains the complete `residue_ids` recorded by 1.2. Selecting a component selects all of its residues and every atom/altLoc in those residues.
''',
    '''Every selected object must be named by a `component_id` materialized in the classification result. Component IDs are opaque, versioned values derived from final membership rather than `chain_index`; downstream code must not reconstruct them.

A component's `residue_ids` contain all observed coordinate-bearing member residues. `missing_residue_ids` preserve expected-but-unobserved membership metadata and are not selectable coordinate objects. Selecting a component selects every observed member residue and every atom/altLoc in those residues.
''',
)
replace_once(
    "02_operations/chain_and_component_selection/references/selection_rules.md",
    '''Confirmed covalent relations are:

```text
COVALENT
DISULFIDE
GLYCOSIDIC
```

For every confirmed relation, either both endpoints are selected or both are excluded. A selection that retains only one endpoint is blocked.
''',
    '''A confirmed relation with:

```text
relation_type: COVALENT_CONNECTION
```

forms the v1 covalent closure. Disulfide, glycosidic and other covalent chemistry remain scientific subtypes of this relation class unless a future contract adds a separate subtype field.

For every confirmed covalent connection, either both endpoint components are selected or both are excluded. A selection that retains only one endpoint is blocked.
''',
)
replace_once(
    "02_operations/chain_and_component_selection/SKILL.md",
    '''若显式连接关系为：

```text
COVALENT | DISULFIDE | GLYCOSIDIC
```

且连接两端分属选择集与排除集，selection spec 无效。
''',
    '''若 1.2 confirmed relation 满足：

```text
relation_type: COVALENT_CONNECTION
```

且连接两端的 `component_id` 分属选择集与排除集，selection spec 无效。disulfide、glycosidic 等化学亚型在 v1 中仍由该统一 relation type 表达。
''',
)
replace_once(
    "02_validators/chain_and_component_selection_validator/SKILL.md",
    '''- disulfide/glycosidic/covalent relation 不得被静默删除；
''',
    '''- 所有 `COVALENT_CONNECTION`（包括 disulfide/glycosidic 等科学亚型）不得被静默删除；
''',
)

# Manifest relation vocabulary is the actual 1.2 relation contract.
manifest_path = ROOT / "02_operations/chain_and_component_selection/schemas/selection_manifest.schema.yaml"
manifest = manifest_path.read_text(encoding="utf-8")
manifest = manifest.replace(
    "      relation_type: {type: string, minLength: 1}\n",
    "      relation_type: {enum: [COVALENT_CONNECTION, METAL_COORDINATION]}\n",
    1,
)
manifest_path.write_text(manifest, encoding="utf-8")

# Behavior fixtures stop inventing relation types that 1.2 never emits.
fixture_path = ROOT / "04_evals/chain_and_component_selection/fixtures/selection_cases.yaml"
fixture = fixture_path.read_text(encoding="utf-8")
fixture = fixture.replace("relation_type: COVALENT\n", "relation_type: COVALENT_CONNECTION\n")
fixture = fixture.replace("relation_type: DISULFIDE\n", "relation_type: COVALENT_CONNECTION\n")
fixture_path.write_text(fixture, encoding="utf-8")

# Content maps: fix removed schema reference and register the ID owner.
replace_once(
    "00_authoring/content_maps/component_and_residue_classification_validator.yaml",
    '''  deterministic_final_result_builder:
    owner: 02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py
''',
    '''  deterministic_final_result_builder:
    owner: 02_validators/component_and_residue_classification_validator/scripts/build_classification_result.py
  deterministic_selection_identity_contract:
    owner: 02_validators/component_and_residue_classification_validator/scripts/selection_identity.py
''',
)
for content_map in (
    "00_authoring/content_maps/chain_and_component_selection.yaml",
    "00_authoring/content_maps/chain_and_component_selection_validator.yaml",
):
    path = ROOT / content_map
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "02_validators/component_and_residue_classification_validator/schemas/classification_outputs.schema.yaml",
        "02_validators/component_and_residue_classification_validator/schemas/classification_result.schema.yaml",
    )
    path.write_text(text, encoding="utf-8")

# 1.3 draft validation record: interface gap closed, executable implementation still pending.
validation_path = ROOT / "04_evals/chain_and_component_selection/SELECTION_DRAFT_VALIDATION.md"
validation = validation_path.read_text(encoding="utf-8")
validation = validation.replace(
    "deterministic selection implementation: not implemented\n",
    "1.2 selection identity input contract: implemented\n"
    "deterministic selection implementation: not implemented\n",
    1,
)
validation = validation.replace(
    "## 尚未实现\n\n1. deterministic `select_structure.py`；",
    "## 已完成的跨阶段前置接口\n\n"
    "- 1.2 `classification_result.yaml` 输出 `source_structure`；\n"
    "- 每个 final component 输出稳定 `component_id`、observed `residue_ids` 与 `missing_residue_ids`；\n"
    "- 每个 residue 输出 `residue_id` 与所属 `component_id`；\n"
    "- relation endpoint 输出 `endpoint_id`、`residue_id`、`component_id`；\n"
    "- relation 输出稳定 `relation_id`；\n"
    "- 聚合水、离子和重复小分子仍保留全部实例级 residue identity；\n"
    "- v1 共价闭包统一使用 1.2 实际 relation type `COVALENT_CONNECTION`。\n\n"
    "## 尚未实现\n\n1. deterministic `select_structure.py`；",
    1,
)
validation_path.write_text(validation, encoding="utf-8")

# Rules own the cross-stage semantics.
append_once(
    "02_validators/component_and_residue_classification_validator/references/classification_rules.md",
    "\n# 4. 分类字段\n",
    '''
## 3.2 下游选择身份

最终 `classification_result.yaml` 必须为 1.3 输出不可重建的权威选择身份：

- `source_structure`：本次分类对应的源结构 path、SHA-256 与格式；
- `component_id`：根据 final component membership 生成，禁止由 `chain_index` 充当或重建；
- `residue_id`：根据 immutable `source_identity` 生成；
- `endpoint_id`：根据 source residue identity 与 exact atom name 生成；
- `relation_id`：根据 relation type 与两个 endpoint IDs 生成，与 endpoint 顺序和 evidence status 无关。

聚合 `SOLVENT_GROUP`、`ION_GROUP` 和 `REPEATED_SMALL_MOLECULE_GROUP` 只改变逻辑分组，不得删除实例级 residue records。每个 component 分别列出：

- `residue_ids`：当前结构中实际存在、可被选择的 observed residues；
- `missing_residue_ids`：来源记录中 expected but unobserved residues，仅用于追溯，不作为坐标选择对象。

这些 ID 对下游是 opaque contract values；1.3 必须读取 1.2 输出，禁止根据字段自行复刻 ID 算法。

''',
)

# Permanent regression tests.
test_content = '''from __future__ import annotations

import copy
import sys
from pathlib import Path

import gemmi
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_classification_result import _assign_selection_contract_ids  # noqa: E402
from classification_engine_core import (  # noqa: E402
    ClassificationValue,
    ResidueAnalysis,
    _build_chain_groups,
)
from selection_identity import (  # noqa: E402
    component_id_from_members,
    endpoint_id_from_source_identity,
    relation_id_from_endpoints,
    residue_id_from_source_identity,
)
from structure_records import ResidueRecord  # noqa: E402


def _source_identity(chain: str, number: str, name: str) -> dict:
    return {
        "source_model_id": "1",
        "source_chain_id": chain,
        "source_resid": {"number": number, "insertion_code": None},
        "source_residue_name": name,
    }


def _current_identity(chain: str, number: str, name: str) -> dict:
    return {
        "current_model_id": "1",
        "current_chain_id": chain,
        "current_resid": {"number": number, "insertion_code": None},
        "current_residue_name": name,
    }


def _record(chain_index: int, chain: str, number: str, name: str, *, observed: bool = True) -> dict:
    return {
        "chain_index": chain_index,
        "source_identity": _source_identity(chain, number, name),
        "current_identity": _current_identity(chain, number, name) if observed else None,
        "source_chain_id": chain,
        "source_resid": {"number": number, "insertion_code": None},
        "residue_name": name,
        "presence_status": "OBSERVED" if observed else "MISSING_EXPECTED",
        "sequence_position": None,
        "classification": {
            "polymer_class": "WATER" if name == "HOH" else "POLYMER",
            "topology_class": "SOLVENT_COMPONENT" if name == "HOH" else "STANDARD_RESIDUE",
            "resolution_status": "RESOLVED",
            "evidence": ["fixture"],
        },
        "conformation": {"status": "SINGLE_CONFORMATION" if observed else "NOT_APPLICABLE", "altloc_ids": []},
        "heavy_atom_check": {
            "status": "NOT_PERFORMED" if observed else "NOT_APPLICABLE",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": None,
        },
    }


def _group(chain_index: int, group_type: str, count: int) -> dict:
    return {
        "chain_index": chain_index,
        "grouping_status": "FINAL",
        "group_type": group_type,
        "source_chain_id": None,
        "entity_id": None,
        "residue_name": "HOH" if group_type == "SOLVENT_GROUP" else None,
        "instance_count": count,
        "linked_polymer_chain_indices": [],
        "source_associations": [],
    }


def test_selection_ids_are_deterministic_opaque_and_not_chain_index_based() -> None:
    first = residue_id_from_source_identity(_source_identity("A/B", "10", "CYS"))
    second = residue_id_from_source_identity(_source_identity("A/B", "10", "CYS"))
    assert first == second
    assert "A%2FB" in first
    component_a = component_id_from_members("1", "POLYMER_CHAIN", [first], [])
    component_b = component_id_from_members("1", "POLYMER_CHAIN", [first], [])
    assert component_a == component_b
    assert "chain_index" not in component_a


def test_assignment_exports_complete_group_membership_and_relation_ids() -> None:
    groups = [_group(1, "SOLVENT_GROUP", 2), _group(2, "POLYMER_CHAIN", 2)]
    records = [
        _record(1, "W", "1", "HOH"),
        _record(1, "W", "2", "HOH"),
        _record(2, "A", "10", "CYS"),
        _record(2, "A", "11", "GLY", observed=False),
    ]
    endpoint_source = {
        **_source_identity("A", "10", "CYS"),
        "source_atom_name": "SG",
    }
    water_source = {
        **_source_identity("W", "1", "HOH"),
        "source_atom_name": "O",
    }
    relations = [
        {
            "relation_type": "METAL_COORDINATION",
            "endpoint_1": {
                "chain_index": 2,
                "source_identity": endpoint_source,
                "current_identity": {
                    **_current_identity("A", "10", "CYS"),
                    "current_atom_name": "SG",
                },
                "source_chain_id": "A",
                "source_resid": {"number": "10", "insertion_code": None},
                "residue_name": "CYS",
                "atom_name": "SG",
            },
            "endpoint_2": {
                "chain_index": 1,
                "source_identity": water_source,
                "current_identity": {
                    **_current_identity("W", "1", "HOH"),
                    "current_atom_name": "O",
                },
                "source_chain_id": "W",
                "source_resid": {"number": "1", "insertion_code": None},
                "residue_name": "HOH",
                "atom_name": "O",
            },
            "evidence_status": "CONFIRMED_BY_STRUCTURE",
            "topology_effect_applied": False,
        }
    ]
    _assign_selection_contract_ids("1", groups, records, relations)
    assert len(groups[0]["residue_ids"]) == 2
    assert groups[0]["missing_residue_ids"] == []
    assert len(groups[1]["residue_ids"]) == 1
    assert len(groups[1]["missing_residue_ids"]) == 1
    assert {record["component_id"] for record in records[:2]} == {groups[0]["component_id"]}
    relation = relations[0]
    assert relation["relation_id"].startswith("relation:v1/")
    assert relation["endpoint_1"]["component_id"] == groups[1]["component_id"]
    assert relation["endpoint_2"]["component_id"] == groups[0]["component_id"]
    expected_endpoint = endpoint_id_from_source_identity(endpoint_source)
    assert relation["endpoint_1"]["endpoint_id"] == expected_endpoint
    assert relation["relation_id"] == relation_id_from_endpoints(
        "METAL_COORDINATION",
        [relation["endpoint_2"]["endpoint_id"], relation["endpoint_1"]["endpoint_id"]],
    )


def _water_analysis(number: int, position: int) -> ResidueAnalysis:
    residue = gemmi.Residue()
    residue.name = "HOH"
    residue.seqid = gemmi.SeqId(number, " ")
    record = ResidueRecord(
        model_id="1",
        source_chain_id="W",
        source_resid_number=str(number),
        insertion_code=None,
        residue_name="HOH",
        entity_id=None,
        entity_type=gemmi.EntityType.Water,
        polymer_type=gemmi.PolymerType.Unknown,
        label_seq=None,
        chain_position=0,
        residue_position=position,
        residue=residue,
        atoms=[],
    )
    return ResidueAnalysis(
        residue=record,
        classification=ClassificationValue(
            "WATER",
            "SOLVENT_COMPONENT",
            "RESOLVED",
            "SKILL_REGISTRY",
            ("fixture",),
            None,
        ),
        conformation={"status": "SINGLE_CONFORMATION", "altloc_ids": []},
        heavy_atom_check={
            "status": "NOT_PERFORMED",
            "reference_type": None,
            "reference_name": None,
            "missing_atoms": [],
            "unexpected_atoms": [],
            "reason": None,
        },
        sequence_position=None,
    )


def test_aggregate_grouping_does_not_erase_instance_records() -> None:
    analyses = [_water_analysis(1, 0), _water_analysis(2, 1)]
    groups, _assignment = _build_chain_groups(analyses)
    assert groups[0]["group_type"] == "SOLVENT_GROUP"
    assert groups[0]["instance_count"] == 2
    assert all(item.include_residue_record for item in analyses)


def test_classification_result_schema_requires_selection_contract_fields() -> None:
    schema = yaml.safe_load(
        (SKILL / "schemas/classification_result.schema.yaml").read_text(encoding="utf-8")
    )
    assert "source_structure" in schema["required"]
    group_required = set(schema["$defs"]["chain_group"]["required"])
    assert {"component_id", "residue_ids", "missing_residue_ids"} <= group_required
    residue_required = set(schema["$defs"]["residue_record"]["required"])
    assert {"residue_id", "component_id"} <= residue_required
    endpoint_required = set(schema["$defs"]["endpoint"]["required"])
    assert {"endpoint_id", "residue_id", "component_id"} <= endpoint_required
    relation_required = set(schema["$defs"]["relation"]["required"])
    assert "relation_id" in relation_required
'''
(ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_selection_identity_contract.py").write_text(
    test_content, encoding="utf-8"
)

# Include the new permanent test in the normal suite.
replace_once(
    ".github/workflows/component-classification-v1-2.yml",
    '''            04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py \\
            04_evals/component_and_residue_classification_validator/test_v1_2_manager_closure.py \\
''',
    '''            04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py \\
            04_evals/component_and_residue_classification_validator/test_v1_2_selection_identity_contract.py \\
            04_evals/component_and_residue_classification_validator/test_v1_2_manager_closure.py \\
''',
)

print("selection identity contract migration applied")

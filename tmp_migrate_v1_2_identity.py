from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
EVAL = ROOT / "04_evals/component_and_residue_classification_validator"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:80]!r}")
    write(path, text.replace(old, new, 1))


def replace_all(path: Path, old: str, new: str, minimum: int = 1) -> None:
    text = read(path)
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{path}: expected at least {minimum} matches, found {count}: {old[:80]!r}")
    write(path, text.replace(old, new))


def update_structure_records() -> None:
    path = SKILL / "scripts/structure_records.py"
    helper_block = '''\n\ndef source_residue_identity(record: ResidueRecord | AtomRecord) -> dict[str, Any]:
    """Return immutable provenance identity from the input STRUCTURE."""
    return {
        "source_model_id": record.model_id,
        "source_chain_id": record.source_chain_id,
        "source_resid": {
            "number": record.source_resid_number,
            "insertion_code": record.insertion_code,
        },
        "source_residue_name": record.residue_name,
    }


def current_residue_identity(record: ResidueRecord | AtomRecord) -> dict[str, Any]:
    """Return identity in the STRUCTURE revision currently being classified.

    Validator 1.2 does not mutate the input STRUCTURE, so source and current
    values are equal at this stage.  They remain separate fields so downstream
    structure revisions can update only current identity while preserving
    provenance.
    """
    return {
        "current_model_id": record.model_id,
        "current_chain_id": record.source_chain_id,
        "current_resid": {
            "number": record.source_resid_number,
            "insertion_code": record.insertion_code,
        },
        "current_residue_name": record.residue_name,
    }


def source_atom_identity(atom: AtomRecord) -> dict[str, Any]:
    output = source_residue_identity(atom)
    output["source_atom_name"] = atom.atom_name
    return output


def current_atom_identity(atom: AtomRecord) -> dict[str, Any]:
    output = current_residue_identity(atom)
    output["current_atom_name"] = atom.atom_name
    return output
'''
    replace_once(path, "\n\ndef _entity_data(\n", helper_block + "\n\ndef _entity_data(\n")
    replace_once(
        path,
        '''    output: dict[str, Any] = {
        "chain_index": chain_index,
        "source_chain_id": atom.source_chain_id,
''',
        '''    output: dict[str, Any] = {
        "chain_index": chain_index,
        "source_identity": source_atom_identity(atom),
        "current_identity": current_atom_identity(atom),
        "source_chain_id": atom.source_chain_id,
''',
    )


def update_classification_engine() -> None:
    path = SKILL / "scripts/classification_engine_core.py"
    replace_once(
        path,
        "from structure_records import ResidueRecord, collect_selected_model\n",
        '''from structure_records import (
    ResidueRecord,
    collect_selected_model,
    current_residue_identity,
    source_residue_identity,
)
''',
    )
    helper = '''\n\ndef _identity_fields(
    residue: ResidueRecord,
    *,
    current_present: bool = True,
) -> dict[str, Any]:
    """Build authoritative dual identity plus v1 compatibility mirrors."""
    return {
        "source_identity": source_residue_identity(residue),
        "current_identity": current_residue_identity(residue) if current_present else None,
        "source_chain_id": residue.source_chain_id,
        "source_resid": {
            "number": residue.source_resid_number,
            "insertion_code": residue.insertion_code,
        },
        "residue_name": residue.residue_name,
    }
'''
    replace_once(path, "\n\nPROTEIN_POLYMER_TYPES = {\n", helper + "\n\nPROTEIN_POLYMER_TYPES = {\n")
    residue_block = '''                "chain_index": analysis.chain_index,
                "source_chain_id": analysis.residue.source_chain_id,
                "source_resid": {
                    "number": analysis.residue.source_resid_number,
                    "insertion_code": analysis.residue.insertion_code,
                },
                "residue_name": analysis.residue.residue_name,
'''
    residue_replacement = '''                "chain_index": analysis.chain_index,
                **_identity_fields(
                    analysis.residue,
                    current_present=presence_status == "OBSERVED",
                ),
'''
    replace_once(path, residue_block, residue_replacement)
    common = '''                "source_chain_id": residue.source_chain_id,
                "source_resid": {
                    "number": residue.source_resid_number,
                    "insertion_code": residue.insertion_code,
                },
                "residue_name": residue.residue_name,
'''
    replace_all(path, common, "                **_identity_fields(residue),\n", minimum=3)


def update_relation_scripts() -> None:
    for name, function_name in (
        ("check_possible_connections.py", "_missing_atom_entry"),
        ("check_possible_coordination.py", "_issue_entry"),
    ):
        path = SKILL / "scripts" / name
        replace_once(
            path,
            "    resolve_chain_index,\n)\n",
            "    resolve_chain_index,\n    current_residue_identity,\n    source_residue_identity,\n)\n",
        )
        if function_name == "_missing_atom_entry":
            replace_once(
                path,
                '''    return {
        "chain_index": _residue_chain_index(resolver, residue),
        "source_chain_id": residue.source_chain_id,
''',
                '''    return {
        "chain_index": _residue_chain_index(resolver, residue),
        "source_identity": source_residue_identity(residue),
        "current_identity": current_residue_identity(residue),
        "source_chain_id": residue.source_chain_id,
''',
            )
        else:
            replace_once(
                path,
                '''    return {
        "endpoint_role": endpoint_role,
        "chain_index": _residue_chain_index(resolver, residue),
        "source_chain_id": residue.source_chain_id,
''',
                '''    return {
        "endpoint_role": endpoint_role,
        "chain_index": _residue_chain_index(resolver, residue),
        "source_identity": source_residue_identity(residue),
        "current_identity": current_residue_identity(residue),
        "source_chain_id": residue.source_chain_id,
''',
            )


def update_builder() -> None:
    path = SKILL / "scripts/build_classification_result.py"
    replace_once(
        path,
        '''    return {
        "chain_index": int(chain_index if chain_index is not None else endpoint["chain_index"]),
        "source_chain_id": endpoint.get("source_chain_id"),
''',
        '''    return {
        "chain_index": int(chain_index if chain_index is not None else endpoint["chain_index"]),
        "source_identity": copy.deepcopy(endpoint["source_identity"]),
        "current_identity": copy.deepcopy(endpoint["current_identity"]),
        "source_chain_id": endpoint.get("source_chain_id"),
''',
    )
    replace_once(
        path,
        '''        "subject": {
            "source_chain_id": record.get("source_chain_id"),
''',
        '''        "subject": {
            "source_identity": copy.deepcopy(record["source_identity"]),
            "current_identity": copy.deepcopy(record["current_identity"]),
            "source_chain_id": record.get("source_chain_id"),
''',
    )
    replace_once(
        path,
        '''    return {
        "chain_index": int(endpoint["chain_index"]),
        "source_chain_id": endpoint.get("source_chain_id"),
''',
        '''    return {
        "chain_index": int(endpoint["chain_index"]),
        "source_identity": copy.deepcopy(endpoint["source_identity"]),
        "current_identity": copy.deepcopy(endpoint["current_identity"]),
        "source_chain_id": endpoint.get("source_chain_id"),
''',
    )
    replace_once(
        path,
        '''    return {
        "chain_index": int(record["chain_index"]),
        "source_chain_id": record.get("source_chain_id"),
''',
        '''    return {
        "chain_index": int(record["chain_index"]),
        "source_identity": copy.deepcopy(record["source_identity"]),
        "current_identity": copy.deepcopy(record["current_identity"]),
        "source_chain_id": record.get("source_chain_id"),
''',
    )


def identity_defs(indent: str = "  ") -> str:
    return f'''{indent}source_residue_identity:
{indent}  type: object
{indent}  additionalProperties: false
{indent}  required: [source_model_id, source_chain_id, source_resid, source_residue_name]
{indent}  properties:
{indent}    source_model_id: {{type: string, minLength: 1}}
{indent}    source_chain_id:
{indent}      $ref: "#/$defs/nullable_string"
{indent}    source_resid:
{indent}      $ref: "#/$defs/source_resid"
{indent}    source_residue_name: {{type: string, minLength: 1}}
{indent}current_residue_identity:
{indent}  type: object
{indent}  additionalProperties: false
{indent}  required: [current_model_id, current_chain_id, current_resid, current_residue_name]
{indent}  properties:
{indent}    current_model_id: {{type: string, minLength: 1}}
{indent}    current_chain_id:
{indent}      $ref: "#/$defs/nullable_string"
{indent}    current_resid:
{indent}      $ref: "#/$defs/source_resid"
{indent}    current_residue_name: {{type: string, minLength: 1}}
{indent}source_atom_identity:
{indent}  type: object
{indent}  additionalProperties: false
{indent}  required: [source_model_id, source_chain_id, source_resid, source_residue_name, source_atom_name]
{indent}  properties:
{indent}    source_model_id: {{type: string, minLength: 1}}
{indent}    source_chain_id:
{indent}      $ref: "#/$defs/nullable_string"
{indent}    source_resid:
{indent}      $ref: "#/$defs/source_resid"
{indent}    source_residue_name: {{type: string, minLength: 1}}
{indent}    source_atom_name: {{type: string, minLength: 1}}
{indent}current_atom_identity:
{indent}  type: object
{indent}  additionalProperties: false
{indent}  required: [current_model_id, current_chain_id, current_resid, current_residue_name, current_atom_name]
{indent}  properties:
{indent}    current_model_id: {{type: string, minLength: 1}}
{indent}    current_chain_id:
{indent}      $ref: "#/$defs/nullable_string"
{indent}    current_resid:
{indent}      $ref: "#/$defs/source_resid"
{indent}    current_residue_name: {{type: string, minLength: 1}}
{indent}    current_atom_name: {{type: string, minLength: 1}}
'''


def inject_defs(path: Path, next_def: str) -> None:
    replace_once(path, f"  {next_def}:\n", identity_defs() + f"  {next_def}:\n")


def update_schemas() -> None:
    obs = SKILL / "schemas/classification_observations.schema.yaml"
    inject_defs(obs, "entity")
    replace_once(obs, "      - chain_index\n      - source_chain_id\n", "      - source_identity\n      - current_identity\n      - chain_index\n      - source_chain_id\n")
    replace_once(
        obs,
        "    properties:\n      chain_index:\n",
        '''    properties:
      source_identity:
        $ref: "#/$defs/source_residue_identity"
      current_identity:
        oneOf:
          - $ref: "#/$defs/current_residue_identity"
          - type: "null"
      chain_index:
''',
    )

    conn = SKILL / "schemas/possible_connections_result.schema.yaml"
    inject_defs(conn, "endpoint")
    replace_once(conn, "      - chain_index\n      - source_chain_id\n", "      - source_identity\n      - current_identity\n      - chain_index\n      - source_chain_id\n")
    replace_once(
        conn,
        "    properties:\n      chain_index: {type: integer, minimum: 1}\n      source_chain_id:\n",
        '''    properties:
      source_identity:
        $ref: "#/$defs/source_atom_identity"
      current_identity:
        $ref: "#/$defs/current_atom_identity"
      chain_index: {type: integer, minimum: 1}
      source_chain_id:
''',
    )
    replace_once(conn, "      - chain_index\n      - source_chain_id\n      - source_resid\n      - residue_name\n      - missing_atom_name\n", "      - source_identity\n      - current_identity\n      - chain_index\n      - source_chain_id\n      - source_resid\n      - residue_name\n      - missing_atom_name\n")
    marker = "    properties:\n      chain_index: {type: integer, minimum: 1}\n      source_chain_id:\n"
    text = read(conn)
    first = text.find(marker)
    second = text.find(marker, first + 1)
    if second < 0:
        raise RuntimeError("connection schema missing second identity property marker")
    replacement = '''    properties:
      source_identity:
        $ref: "#/$defs/source_residue_identity"
      current_identity:
        $ref: "#/$defs/current_residue_identity"
      chain_index: {type: integer, minimum: 1}
      source_chain_id:
'''
    text = text[:second] + text[second:].replace(marker, replacement, 1)
    write(conn, text)

    coord = SKILL / "schemas/possible_coordination_result.schema.yaml"
    inject_defs(coord, "endpoint_definition")
    replace_once(coord, "      - chain_index\n      - source_chain_id\n", "      - source_identity\n      - current_identity\n      - chain_index\n      - source_chain_id\n")
    replace_once(
        coord,
        "    properties:\n      chain_index: {type: integer, minimum: 1}\n      source_chain_id:\n",
        '''    properties:
      source_identity:
        $ref: "#/$defs/source_atom_identity"
      current_identity:
        $ref: "#/$defs/current_atom_identity"
      chain_index: {type: integer, minimum: 1}
      source_chain_id:
''',
    )
    replace_once(coord, "      - endpoint_role\n      - chain_index\n", "      - endpoint_role\n      - source_identity\n      - current_identity\n      - chain_index\n")
    marker = "      endpoint_role: {enum: [METAL, DONOR]}\n      chain_index: {type: integer, minimum: 1}\n"
    replace_once(
        coord,
        marker,
        '''      endpoint_role: {enum: [METAL, DONOR]}
      source_identity:
        $ref: "#/$defs/source_residue_identity"
      current_identity:
        $ref: "#/$defs/current_residue_identity"
      chain_index: {type: integer, minimum: 1}
''',
    )

    final = SKILL / "schemas/classification_result.schema.yaml"
    inject_defs(final, "source_association")
    replace_once(final, "      - chain_index\n      - source_chain_id\n      - source_resid\n      - residue_name\n      - presence_status\n", "      - source_identity\n      - current_identity\n      - chain_index\n      - source_chain_id\n      - source_resid\n      - residue_name\n      - presence_status\n")
    replace_once(
        final,
        "    properties:\n      chain_index: {type: integer, minimum: 1}\n      source_chain_id:\n",
        '''    properties:
      source_identity:
        $ref: "#/$defs/source_residue_identity"
      current_identity:
        oneOf:
          - $ref: "#/$defs/current_residue_identity"
          - type: "null"
      chain_index: {type: integer, minimum: 1}
      source_chain_id:
''',
    )
    replace_once(final, "    required: [chain_index, source_chain_id, source_resid, residue_name, atom_name]\n", "    required: [source_identity, current_identity, chain_index, source_chain_id, source_resid, residue_name, atom_name]\n")
    marker = "    properties:\n      chain_index: {type: integer, minimum: 1}\n      source_chain_id:\n"
    text = read(final)
    first = text.find(marker)
    second = text.find(marker, first + 1)
    if second < 0:
        raise RuntimeError("final schema missing endpoint identity property marker")
    replacement = '''    properties:
      source_identity:
        $ref: "#/$defs/source_atom_identity"
      current_identity:
        $ref: "#/$defs/current_atom_identity"
      chain_index: {type: integer, minimum: 1}
      source_chain_id:
'''
    text = text[:second] + text[second:].replace(marker, replacement, 1)
    write(final, text)


def update_rules() -> None:
    path = SKILL / "references/classification_rules.md"
    block = '''
## 3.1 源身份与当前身份

每个已观察残基和关系端点必须同时保存两套正式身份，并使用不同字段名：

```yaml
source_identity:
  source_model_id: "1"
  source_chain_id: A
  source_resid: {number: "145", insertion_code: A}
  source_residue_name: CYS

current_identity:
  current_model_id: "1"
  current_chain_id: A
  current_resid: {number: "145", insertion_code: A}
  current_residue_name: CYS
```

关系端点分别追加 `source_atom_name` 和 `current_atom_name`。规则：

- `source_*` 是输入来源追溯身份，后续结构 revision 禁止覆盖；
- `current_*` 是本次实际读取的 STRUCTURE revision 身份，只能由真实存在的新结构更新；
- 1.2 禁止修改结构，因此 `OBSERVED` 实例的 source/current 值应相等，但两套字段仍必须分别输出；
- `MISSING_EXPECTED` 残基只有 `source_identity`，`current_identity` 必须为 `null`；
- `chain_index` 是逻辑分组编号，必须位于 identity 外部；topology effect 可以改变 `chain_index`，禁止据此改写 current identity；
- `sequence_position` 只是 polymer 序列辅助索引，不属于第三套残基编号；
- v1 平铺的 `source_chain_id`、`source_resid`、`residue_name` 和 `atom_name` 仅为兼容镜像，必须与权威 identity 字段一致，禁止赋予独立语义。

'''
    replace_once(path, "# 4. 分类字段\n", block + "# 4. 分类字段\n")


def add_test() -> None:
    path = EVAL / "test_v1_2_dual_identity.py"
    content = '''from __future__ import annotations

import sys
from pathlib import Path

import gemmi
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from structure_records import (  # noqa: E402
    collect_selected_model,
    current_residue_identity,
    endpoint_dict,
    source_residue_identity,
)


def _record():
    structure = gemmi.read_pdb_string(
        "ATOM      1  SG  CYS A 145       0.000   0.000   0.000  1.00 20.00           S\\nEND\\n"
    )
    _model, residues, _atoms = collect_selected_model(structure, "1")
    return residues[0]


def test_source_and_current_identity_use_distinct_field_names() -> None:
    residue = _record()
    source = source_residue_identity(residue)
    current = current_residue_identity(residue)
    assert set(source) == {
        "source_model_id",
        "source_chain_id",
        "source_resid",
        "source_residue_name",
    }
    assert set(current) == {
        "current_model_id",
        "current_chain_id",
        "current_resid",
        "current_residue_name",
    }
    assert source["source_chain_id"] == current["current_chain_id"] == "A"
    assert source["source_resid"] == current["current_resid"]
    assert source["source_residue_name"] == current["current_residue_name"] == "CYS"


def test_relation_endpoint_keeps_dual_identity_outside_chain_index() -> None:
    residue = _record()
    endpoint = endpoint_dict(residue.atoms[0], 7)
    assert endpoint["chain_index"] == 7
    assert "chain_index" not in endpoint["source_identity"]
    assert "chain_index" not in endpoint["current_identity"]
    assert endpoint["source_identity"]["source_atom_name"] == "SG"
    assert endpoint["current_identity"]["current_atom_name"] == "SG"


def test_all_public_result_schemas_require_authoritative_dual_identity() -> None:
    schema_names = [
        "classification_observations.schema.yaml",
        "possible_connections_result.schema.yaml",
        "possible_coordination_result.schema.yaml",
        "classification_result.schema.yaml",
    ]
    for name in schema_names:
        document = yaml.safe_load((SKILL / "schemas" / name).read_text(encoding="utf-8"))
        serialized = yaml.safe_dump(document, sort_keys=True)
        assert "source_identity" in serialized
        assert "current_identity" in serialized
        assert "source_model_id" in serialized
        assert "current_model_id" in serialized
        assert "source_residue_name" in serialized
        assert "current_residue_name" in serialized


def test_missing_residue_contract_allows_no_current_identity() -> None:
    schema = yaml.safe_load(
        (SKILL / "schemas/classification_observations.schema.yaml").read_text(encoding="utf-8")
    )
    current = schema["$defs"]["residue_record"]["properties"]["current_identity"]
    assert {item.get("type") for item in current["oneOf"] if isinstance(item, dict)} == {"null"}
'''
    write(path, content)

    workflow = ROOT / ".github/workflows/component-classification-v1-2.yml"
    replace_once(
        workflow,
        "            04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py \\\n",
        "            04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py \\\n            04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py \\\n",
    )


def main() -> None:
    update_structure_records()
    update_classification_engine()
    update_relation_scripts()
    update_builder()
    update_schemas()
    update_rules()
    add_test()
    print("v1.2 dual identity migration complete")


if __name__ == "__main__":
    main()

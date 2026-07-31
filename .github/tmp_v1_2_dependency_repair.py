from pathlib import Path
import re

ROOT = Path(".")
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
CHANGED: list[str] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    CHANGED.append(str(path))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


# Explicit Python dependency and public release versions.
requirements = SKILL / "scripts/requirements.txt"
text = read(requirements)
if "referencing" not in text:
    text = text.rstrip() + "\nreferencing>=0.30,<1\n"
write(requirements, text)

for name in (
    "inspect_model_scope.py",
    "classify_structure.py",
    "check_possible_connections.py",
    "check_possible_coordination.py",
    "build_classification_result.py",
    "build_subagent_result.py",
):
    path = SKILL / "scripts" / name
    text = read(path)
    text, count = re.subn(
        r'VERSION = "[^"]+"',
        'VERSION = "1.0.0"',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"cannot freeze version in {path}")
    write(path, text)

# Every structured config is validated by its own Draft 2020-12 schema.
path = SKILL / "scripts/classify_structure.py"
text = read(path)
text = replace_once(
    text,
    "    read_yaml_strict,\n)",
    "    read_yaml_strict,\n    validate_document,\n)",
    "classify import validate_document",
)
text = replace_once(
    text,
    '        if not isinstance(config, dict):\n            raise ClassificationToolError("classification config must be a YAML mapping")\n',
    '        if not isinstance(config, dict):\n            raise ClassificationToolError("classification config must be a YAML mapping")\n        validate_document(\n            config,\n            script_dir.parent / "schemas/classification_config.schema.yaml",\n        )\n',
    "classify config validation",
)
write(path, text)

for script_name, schema_name in (
    ("check_possible_connections.py", "possible_connections_check_config.schema.yaml"),
    ("check_possible_coordination.py", "possible_coordination_check_config.schema.yaml"),
    ("build_classification_result.py", "classification_result_build_config.schema.yaml"),
):
    path = SKILL / "scripts" / script_name
    text = read(path)
    marker = '        if not isinstance(config, dict):\n            raise ClassificationToolError("config must be a YAML mapping")\n'
    replacement = marker + (
        "        validate_document(\n"
        "            config,\n"
        f'            script_dir.parent / "schemas/{schema_name}",\n'
        "        )\n"
    )
    text = replace_once(text, marker, replacement, f"{script_name} config validation")
    write(path, text)

# Baseline classification owns the complete reference manifest, including relation definitions.
path = SKILL / "scripts/classification_engine_core.py"
text = read(path)
insert_marker = "    force_field_manifest = None\n"
helper = '''    relation_definitions_config = config.get("relation_definitions") or {}
    if not isinstance(relation_definitions_config, dict):
        raise ClassificationToolError("relation_definitions must be a mapping")

    def relation_definition_reference(key: str) -> dict[str, Any]:
        entry = relation_definitions_config.get(key)
        if entry is None:
            return {"path": None, "sha256": None, "status": "NOT_PROVIDED"}
        if not isinstance(entry, dict):
            raise ClassificationToolError(
                f"relation_definitions.{key} must be a mapping or null"
            )
        relation_path = _required_path(entry, "path")
        expected_hash = str(entry.get("sha256", ""))
        relation_hash = require_sha256(relation_path, expected_hash)
        return {
            "path": str(relation_path),
            "sha256": relation_hash,
            "status": "LOADED",
        }

    possible_connections_reference = relation_definition_reference(
        "possible_connections"
    )
    possible_coordination_reference = relation_definition_reference(
        "possible_coordination"
    )

'''
text = replace_once(text, insert_marker, helper + insert_marker, "relation manifest helper")
old = '''        "relation_definition_files": {
            "possible_connections": {"path": None, "sha256": None, "status": "NOT_PROVIDED"},
            "possible_coordination": {"path": None, "sha256": None, "status": "NOT_PROVIDED"},
        },
'''
new = '''        "relation_definition_files": {
            "possible_connections": possible_connections_reference,
            "possible_coordination": possible_coordination_reference,
        },
'''
text = replace_once(text, old, new, "manifest relation references")
write(path, text)

# Final integration rejects a relation result whose definition provenance differs from the manifest.
path = SKILL / "scripts/build_classification_result.py"
text = read(path)
old = '''    for relation_document, label in (
        (connections, "connections"),
        (coordination, "coordination"),
    ):
        relation_input = relation_document["input"]
        if relation_input["structure_sha256"] != structure_hash:
            raise ClassificationToolError(f"{label} result structure hash differs")
        if relation_input["observations_sha256"] != observations_hash:
            raise ClassificationToolError(f"{label} result references a different observations file")
        if str(relation_input["selected_model_id"]) != str(selected_model_id):
            raise ClassificationToolError(f"{label} result selected model differs")
'''
new = '''    for relation_document, label, manifest_key in (
        (connections, "connections", "possible_connections"),
        (coordination, "coordination", "possible_coordination"),
    ):
        relation_input = relation_document["input"]
        if relation_input["structure_sha256"] != structure_hash:
            raise ClassificationToolError(f"{label} result structure hash differs")
        if relation_input["observations_sha256"] != observations_hash:
            raise ClassificationToolError(
                f"{label} result references a different observations file"
            )
        if str(relation_input["selected_model_id"]) != str(selected_model_id):
            raise ClassificationToolError(f"{label} result selected model differs")
        manifest_reference = manifest["relation_definition_files"][manifest_key]
        definition_path = relation_input.get("definition_path")
        definition_hash = relation_input.get("definition_sha256")
        if definition_path is None:
            if manifest_reference != {
                "path": None,
                "sha256": None,
                "status": "NOT_PROVIDED",
            }:
                raise ClassificationToolError(
                    f"{label} result omitted a definition recorded by reference manifest"
                )
        elif (
            manifest_reference.get("status") != "LOADED"
            or manifest_reference.get("path") != definition_path
            or manifest_reference.get("sha256") != definition_hash
        ):
            raise ClassificationToolError(
                f"{label} definition provenance differs from reference manifest"
            )
'''
text = replace_once(text, old, new, "builder provenance gate")
# Normalize a previously generated summary expression.
text, count = re.subn(
    r'            "heavy_atom_issue_count": sum\(\n\s*bool\(record\["heavy_atom_check"\]\.get\("findings"\)\)\n\s*or record\["heavy_atom_check"\]\.get\("execution_status"\) == "REFERENCE_TEMPLATE_UNAVAILABLE"\n\s*for record in records\n\s*\),',
    '            "heavy_atom_issue_count": sum(\n                bool(record["heavy_atom_check"].get("findings"))\n                or record["heavy_atom_check"].get("execution_status")\n                == "REFERENCE_TEMPLATE_UNAVAILABLE"\n                for record in records\n            ),',
    text,
    count=1,
)
if count != 1:
    raise SystemExit("cannot normalize final heavy-atom issue summary")
write(path, text)

# Upstream contract is the shared STRUCTURE file record, not the draft 1.1 report.
path = SKILL / "SKILL.md"
text = read(path)
text = replace_once(
    text,
    "- `source_recognition` 的格式结论和输入 SHA-256；",
    "- `current_valid_files` 中唯一 STRUCTURE file record 的 path、SHA-256 与 role；\n- task 明确声明的 `source_format`；1.2 必须自行解析并核验，不读取 `source_recognition_report.yaml` 作为运行时 contract；",
    "SKILL upstream input",
)
text = replace_once(
    text,
    "3. 输入不是 symlink，声明 SHA-256 与实际内容一致；",
    "3. STRUCTURE file record 不是 symlink，声明 SHA-256 与实际内容一致，且不得由 1.1 业务报告字段重新拼装；",
    "SKILL preflight input",
)
write(path, text)

path = SKILL / "scripts/README.md"
text = read(path)
text = replace_once(
    text,
    "reference inputs\noutput paths",
    "reference inputs, including relation definition paths and SHA-256 values\noutput paths",
    "README baseline inputs",
)
text = replace_once(
    text,
    "# Dependencies\n\n安装 `requirements.txt` 声明的版本。",
    "# Config schemas\n\n四个结构化 config 必须分别通过：\n\n```text\n../schemas/classification_config.schema.yaml\n../schemas/possible_connections_check_config.schema.yaml\n../schemas/possible_coordination_check_config.schema.yaml\n../schemas/classification_result_build_config.schema.yaml\n```\n\n未知字段和不满足条件关系的配置必须在业务处理前拒绝。\n\n# Dependencies\n\n安装 `requirements.txt` 声明的全部直接依赖；禁止依赖未声明的传递安装。",
    "README config schemas",
)
write(path, text)

path = SKILL / "references/classification_rules.md"
text = read(path)
anchor = "# 12. 可能共价连接\n"
provenance = '''## 11.1 关系定义 provenance

`reference_manifest.yaml` 必须记录本次实际使用或明确未提供的 `possible_connections.yaml` 与 `possible_coordination.yaml`：

- 提供时保存解析后的 path、exact SHA-256 和 `LOADED`；
- 未提供时三字段固定为 `path: null`、`sha256: null`、`status: NOT_PROVIDED`；
- relation checker 的 definition path/SHA-256 必须与 manifest 完全一致；
- final builder 遇到缺失、不同路径或不同哈希时属于技术失败，禁止继续整合。

'''
if provenance not in text:
    text = replace_once(text, anchor, provenance + anchor, "rules provenance")
write(path, text)

# Content ownership includes config contracts and the stable upstream task contract.
path = ROOT / "00_authoring/content_maps/component_and_residue_classification_validator.yaml"
text = read(path)
insert = '''  classification_config_contract:
    owner: 02_validators/component_and_residue_classification_validator/schemas/classification_config.schema.yaml
  possible_connections_check_config_contract:
    owner: 02_validators/component_and_residue_classification_validator/schemas/possible_connections_check_config.schema.yaml
  possible_coordination_check_config_contract:
    owner: 02_validators/component_and_residue_classification_validator/schemas/possible_coordination_check_config.schema.yaml
  classification_result_build_config_contract:
    owner: 02_validators/component_and_residue_classification_validator/schemas/classification_result_build_config.schema.yaml
'''
marker = "  model_scope_output_contract:\n"
if insert not in text:
    text = replace_once(text, marker, insert + marker, "content map config contracts")
note = "  - Runtime STRUCTURE input is taken from the schema-valid subagent task file record and independently revalidated; the draft source_recognition business report is not a runtime dependency.\n"
notes_marker = "notes:\n"
if note not in text:
    text = replace_once(text, notes_marker, notes_marker + note, "content map upstream note")
write(path, text)

# Update the existing relation-builder fixture to match manifest provenance.
path = ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_relations_and_builder.py"
text = read(path)
old = '''                "possible_coordination": {
                    "path": None,
                    "sha256": None,
                    "status": "NOT_PROVIDED",
                },
'''
new = '''                "possible_coordination": {
                    "path": str(definitions.resolve()),
                    "sha256": digest(definitions),
                    "status": "LOADED",
                },
'''
text = replace_once(text, old, new, "relation fixture provenance")
write(path, text)

# New dependency/config/provenance regression.
test_path = ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_dependency_contracts.py"
test_text = '''from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from classification_engine import execute_classification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_config_schemas_are_meta_valid() -> None:
    for name in (
        "classification_config.schema.yaml",
        "possible_connections_check_config.schema.yaml",
        "possible_coordination_check_config.schema.yaml",
        "classification_result_build_config.schema.yaml",
    ):
        document = yaml.safe_load((SKILL / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(document)


def test_manifest_records_relation_definition_provenance(tmp_path: Path) -> None:
    structure = tmp_path / "water.pdb"
    structure.write_text(
        "HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00 20.00           O\\nEND\\n",
        encoding="utf-8",
    )
    connections = tmp_path / "possible_connections.yaml"
    connections.write_text(
        yaml.safe_dump({"schema_version": "1.0", "possible_connections": []}),
        encoding="utf-8",
    )
    coordination = tmp_path / "possible_coordination.yaml"
    coordination.write_text(
        yaml.safe_dump({"schema_version": "1.0", "possible_coordination": []}),
        encoding="utf-8",
    )
    config = {
        "structure": {
            "path": str(structure),
            "sha256": digest(structure),
            "source_format": "PDB",
            "selected_model_id": "1",
        },
        "classification": {"mode": "REGISTRY"},
        "ccd": {"retrieval_policy": "CACHE_ONLY"},
        "relation_definitions": {
            "possible_connections": {
                "path": str(connections),
                "sha256": digest(connections),
            },
            "possible_coordination": {
                "path": str(coordination),
                "sha256": digest(coordination),
            },
        },
        "output": {
            "observations_path": str(tmp_path / "observations.yaml"),
            "reference_manifest_path": str(tmp_path / "manifest.yaml"),
        },
    }
    _observations, manifest, *_ = execute_classification(config, SCRIPTS)
    assert manifest["relation_definition_files"] == {
        "possible_connections": {
            "path": str(connections.resolve()),
            "sha256": digest(connections),
            "status": "LOADED",
        },
        "possible_coordination": {
            "path": str(coordination.resolve()),
            "sha256": digest(coordination),
            "status": "LOADED",
        },
    }


def test_direct_dependencies_and_versions_are_frozen() -> None:
    requirements = (SCRIPTS / "requirements.txt").read_text(encoding="utf-8")
    assert "referencing>=" in requirements
    for name in (
        "inspect_model_scope.py",
        "classify_structure.py",
        "check_possible_connections.py",
        "check_possible_coordination.py",
        "build_classification_result.py",
        "build_subagent_result.py",
    ):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert 'VERSION = "1.0.0"' in text
        assert "-draft" not in text


def test_v1_2_does_not_depend_on_source_recognition_report() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "不读取 `source_recognition_report.yaml` 作为运行时 contract" in skill
'''
write(test_path, test_text)

with Path("/tmp/dependency-changed-files.txt").open("w", encoding="utf-8") as handle:
    for item in sorted(set(CHANGED + [
        str(SKILL / "schemas/classification_config.schema.yaml"),
        str(SKILL / "schemas/possible_connections_check_config.schema.yaml"),
        str(SKILL / "schemas/possible_coordination_check_config.schema.yaml"),
        str(SKILL / "schemas/classification_result_build_config.schema.yaml"),
    ])):
        handle.write(item + "\n")

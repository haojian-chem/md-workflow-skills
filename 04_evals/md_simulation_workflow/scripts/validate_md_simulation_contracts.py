#!/usr/bin/env python3
"""Validate the local md_simulation contract draft without running GROMACS.

Checks:
- Skill frontmatter and expected directory coverage.
- YAML parsing and Draft 2020-12 JSON Schema meta-validation.
- v2 object-model invariants.
- Fixture structure, duplicate case IDs, and expected case count.

This script does not validate scientific correctness or execute backend commands.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: pip install jsonschema") from exc


EXPECTED_SKILLS = {
    "01_workflows/md_simulation_workflow": "md_simulation_workflow",
    "02_operations/md_simulation_protocol_specification": "md_simulation_protocol_specification",
    "02_validators/md_simulation_protocol_validator": "md_simulation_protocol_validator",
    "02_operations/md_simulation_plan_materialization": "md_simulation_plan_materialization",
    "02_validators/md_simulation_plan_validator": "md_simulation_plan_validator",
    "02_operations/md_run_input_preparation": "md_run_input_preparation",
    "02_validators/md_run_input_validator": "md_run_input_validator",
    "02_operations/md_execution_attempt_specification": "md_execution_attempt_specification",
    "02_validators/md_execution_attempt_validator": "md_execution_attempt_validator",
    "02_operations/md_run_execution": "md_run_execution",
    "02_validators/md_run_status_validator": "md_run_status_validator",
    "02_validators/md_run_output_validator": "md_run_output_validator",
    "02_operations/md_simulation_output_assembly": "md_simulation_output_assembly",
    "02_validators/md_simulation_output_validator": "md_simulation_output_validator",
    "02_validators/md_simulation_completion_validator": "md_simulation_completion_validator",
}

EXPECTED_FIXTURE_FILES = {
    "04_evals/md_simulation_workflow/fixtures/route_and_decision_cases.yaml": 16,
    "04_evals/md_simulation_protocol_specification/fixtures/protocol_specification_cases.yaml": 14,
    "04_evals/md_simulation_protocol_validator/fixtures/protocol_validation_cases.yaml": 17,
    "04_evals/md_simulation_plan_materialization/fixtures/plan_materialization_cases.yaml": 15,
    "04_evals/md_simulation_plan_validator/fixtures/plan_validation_cases.yaml": 17,
    "04_evals/md_run_input_preparation/fixtures/input_preparation_cases.yaml": 15,
    "04_evals/md_run_input_validator/fixtures/input_validation_cases.yaml": 16,
    "04_evals/md_execution_attempt_specification/fixtures/attempt_specification_cases.yaml": 10,
    "04_evals/md_execution_attempt_validator/fixtures/attempt_validation_cases.yaml": 10,
    "04_evals/md_run_execution/fixtures/execution_cases.yaml": 15,
    "04_evals/md_run_status_validator/fixtures/status_cases.yaml": 11,
    "04_evals/md_run_output_validator/fixtures/output_validation_cases.yaml": 18,
    "04_evals/md_simulation_output_assembly/fixtures/output_assembly_cases.yaml": 10,
    "04_evals/md_simulation_output_validator/fixtures/output_validation_cases.yaml": 12,
    "04_evals/md_simulation_completion_validator/fixtures/completion_cases.yaml": 18,
}

EXPECTED_TOTAL_CASES = 214
EXPECTED_SCHEMA_COUNT = 14


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str

    def render(self) -> str:
        return f"[{self.level}] {self.code} {self.path}: {self.message}"


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def recursive_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(recursive_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(recursive_keys(child))
    return keys


def recursive_scalars(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield key
            yield from recursive_scalars(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_scalars(child)
    else:
        yield value


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening YAML frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing closing YAML frontmatter delimiter") from exc
    data = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not an object")
    return data


def schema_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel_dir in EXPECTED_SKILLS:
        directory = root / rel_dir / "schemas"
        if directory.is_dir():
            paths.extend(sorted(directory.glob("*.schema.yaml")))
    return sorted(set(paths))


def validate_skills(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel_dir, expected_name in EXPECTED_SKILLS.items():
        skill_path = root / rel_dir / "SKILL.md"
        if not skill_path.is_file():
            findings.append(Finding("ERROR", "SKILL_MISSING", rel_dir, "SKILL.md not found"))
            continue
        try:
            frontmatter = parse_frontmatter(skill_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(Finding("ERROR", "SKILL_FRONTMATTER_INVALID", str(skill_path.relative_to(root)), str(exc)))
            continue
        actual_name = frontmatter.get("name")
        if actual_name != expected_name:
            findings.append(
                Finding(
                    "ERROR",
                    "SKILL_NAME_MISMATCH",
                    str(skill_path.relative_to(root)),
                    f"expected {expected_name!r}, got {actual_name!r}",
                )
            )
        description = frontmatter.get("description")
        if not isinstance(description, str) or not description.strip():
            findings.append(Finding("ERROR", "SKILL_DESCRIPTION_MISSING", str(skill_path.relative_to(root)), "description is empty"))
    return findings


def validate_schemas(root: Path) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    loaded: dict[str, Any] = {}
    paths = schema_paths(root)
    if len(paths) != EXPECTED_SCHEMA_COUNT:
        findings.append(
            Finding(
                "ERROR",
                "SCHEMA_COUNT_MISMATCH",
                ".",
                f"expected {EXPECTED_SCHEMA_COUNT}, found {len(paths)}",
            )
        )

    ids: dict[str, str] = {}
    for path in paths:
        rel = str(path.relative_to(root))
        try:
            schema = load_yaml(path)
        except (OSError, yaml.YAMLError) as exc:
            findings.append(Finding("ERROR", "SCHEMA_YAML_INVALID", rel, str(exc)))
            continue
        if not isinstance(schema, dict):
            findings.append(Finding("ERROR", "SCHEMA_NOT_OBJECT", rel, "top-level YAML value must be an object"))
            continue
        loaded[rel] = schema
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            findings.append(Finding("ERROR", "SCHEMA_DRAFT_INVALID", rel, "must use Draft 2020-12"))
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            findings.append(Finding("ERROR", "SCHEMA_ID_MISSING", rel, "$id is missing"))
        elif schema_id in ids:
            findings.append(Finding("ERROR", "SCHEMA_ID_DUPLICATE", rel, f"also used by {ids[schema_id]}"))
        else:
            ids[schema_id] = rel
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            findings.append(Finding("ERROR", "SCHEMA_META_INVALID", rel, exc.message))

    return findings, loaded


def get_schema(loaded: Mapping[str, Any], suffix: str) -> tuple[str, dict[str, Any]] | None:
    matches = [(path, schema) for path, schema in loaded.items() if path.endswith(suffix)]
    if len(matches) != 1:
        return None
    return matches[0]


def validate_v2_invariants(root: Path, schemas: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []

    old_schema = root / "02_operations/md_run_execution/schemas/md_run_execution_spec.schema.yaml"
    if old_schema.exists():
        findings.append(Finding("ERROR", "OLD_EXECUTION_SCHEMA_PRESENT", str(old_schema.relative_to(root)), "superseded schema must be removed"))

    protocol_item = get_schema(schemas, "md_simulation_protocol_spec.schema.yaml")
    if protocol_item is None:
        findings.append(Finding("ERROR", "PROTOCOL_SCHEMA_NOT_UNIQUE", ".", "protocol schema missing or duplicated"))
    else:
        path, protocol = protocol_item
        protocol_scalars = set(recursive_scalars(protocol))
        if "CONTINUATION" in protocol_scalars:
            findings.append(Finding("ERROR", "CONTINUATION_ROLE_PRESENT", path, "continuation must not be a scientific role"))
        protocol_keys = recursive_keys(protocol)
        forbidden_runtime_keys = {
            "backend",
            "resources",
            "gpu_ids",
            "mpi_ranks",
            "omp_threads",
            "memory_mb",
            "walltime",
            "attempt_id",
            "prepared_submission_id",
            "append_mode",
        }
        present = sorted(forbidden_runtime_keys & protocol_keys)
        if present:
            findings.append(Finding("ERROR", "RUNTIME_FIELD_IN_PROTOCOL", path, f"misplaced keys: {present}"))

    plan_item = get_schema(schemas, "md_simulation_plan.schema.yaml")
    if plan_item is None:
        findings.append(Finding("ERROR", "PLAN_SCHEMA_NOT_UNIQUE", ".", "plan schema missing or duplicated"))
    else:
        path, plan = plan_item
        plan_keys = recursive_keys(plan)
        forbidden_plan_keys = {
            "mdp_spec",
            "completion_criteria",
            "input_preparation_status",
            "execution_policy",
            "backend",
            "resources",
            "runtime",
            "submission_status",
            "attempt_status",
        }
        present = sorted(forbidden_plan_keys & plan_keys)
        if present:
            findings.append(Finding("ERROR", "PLAN_OWNER_OR_STATUS_VIOLATION", path, f"forbidden keys: {present}"))

    attempt_item = get_schema(schemas, "md_execution_attempt_spec.schema.yaml")
    if attempt_item is None:
        findings.append(Finding("ERROR", "ATTEMPT_SCHEMA_NOT_UNIQUE", ".", "attempt schema missing or duplicated"))
    else:
        path, attempt = attempt_item
        required = set(attempt.get("required", []))
        for field in {"execution_spec_id", "attempt_id", "attempt_kind", "prepared_submission_id"}:
            if field not in required:
                findings.append(Finding("ERROR", "ATTEMPT_REQUIRED_FIELD_MISSING", path, field))
        if "task_id" in recursive_keys(attempt):
            findings.append(Finding("ERROR", "TASK_ID_AS_ATTEMPT_OBJECT_FIELD", path, "task_id must not define attempt identity"))
        scalars = set(recursive_scalars(attempt))
        if "APPEND" in scalars or "CONTINUE_APPEND" in scalars:
            findings.append(Finding("ERROR", "APPEND_ENABLED", path, "v1 must only allow CONTINUE_NOAPPEND"))

    run_report = get_schema(schemas, "md_run_output_validation_report.schema.yaml")
    if run_report is not None:
        path, schema = run_report
        required = set(schema.get("required", []))
        for field in {"attempt_results", "accepted_attempt_order", "run_output_manifest"}:
            if field not in required:
                findings.append(Finding("ERROR", "RUN_OUTPUT_CHAIN_FIELD_MISSING", path, field))

    stage_manifest = get_schema(schemas, "md_simulation_output_manifest.schema.yaml")
    if stage_manifest is not None:
        path, schema = stage_manifest
        required = set(schema.get("required", []))
        for field in {"run_output_artifacts", "segment_order", "derived_from_artifact_set_ids"}:
            if field not in required:
                findings.append(Finding("ERROR", "STAGE_OUTPUT_COLLECTION_FIELD_MISSING", path, field))

    completion = get_schema(schemas, "md_simulation_completion_report.schema.yaml")
    if completion is not None:
        path, schema = completion
        if "stage_output_closure" not in set(schema.get("required", [])):
            findings.append(Finding("ERROR", "COMPLETION_STAGE_OUTPUT_MISSING", path, "stage_output_closure must be required"))

    return findings


def validate_fixtures(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    total = 0
    global_ids: dict[str, str] = {}

    for rel, expected_count in EXPECTED_FIXTURE_FILES.items():
        path = root / rel
        if not path.is_file():
            findings.append(Finding("ERROR", "FIXTURE_FILE_MISSING", rel, "file not found"))
            continue
        try:
            data = load_yaml(path)
        except (OSError, yaml.YAMLError) as exc:
            findings.append(Finding("ERROR", "FIXTURE_YAML_INVALID", rel, str(exc)))
            continue
        if not isinstance(data, dict):
            findings.append(Finding("ERROR", "FIXTURE_NOT_OBJECT", rel, "top-level value must be an object"))
            continue
        cases = data.get("cases")
        if not isinstance(cases, list):
            findings.append(Finding("ERROR", "FIXTURE_CASES_INVALID", rel, "cases must be an array"))
            continue
        total += len(cases)
        if len(cases) != expected_count:
            findings.append(Finding("ERROR", "FIXTURE_CASE_COUNT_MISMATCH", rel, f"expected {expected_count}, found {len(cases)}"))
        local_ids: set[str] = set()
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                findings.append(Finding("ERROR", "FIXTURE_CASE_NOT_OBJECT", rel, f"case index {index}"))
                continue
            case_id = case.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                findings.append(Finding("ERROR", "FIXTURE_CASE_ID_MISSING", rel, f"case index {index}"))
                continue
            if case_id in local_ids:
                findings.append(Finding("ERROR", "FIXTURE_CASE_ID_DUPLICATE_LOCAL", rel, case_id))
            local_ids.add(case_id)
            qualified = f"{data.get('skill_name')}::{case_id}"
            if qualified in global_ids:
                findings.append(Finding("ERROR", "FIXTURE_CASE_ID_DUPLICATE_GLOBAL", rel, f"also in {global_ids[qualified]}"))
            else:
                global_ids[qualified] = rel
            if "input" not in case or "expected" not in case:
                findings.append(Finding("ERROR", "FIXTURE_CASE_SHAPE_INVALID", rel, f"{case_id} requires input and expected"))

    if total != EXPECTED_TOTAL_CASES:
        findings.append(Finding("ERROR", "FIXTURE_TOTAL_MISMATCH", ".", f"expected {EXPECTED_TOTAL_CASES}, found {total}"))
    return findings


def run(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(validate_skills(root))
    schema_findings, schemas = validate_schemas(root)
    findings.extend(schema_findings)
    findings.extend(validate_v2_invariants(root, schemas))
    findings.extend(validate_fixtures(root))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if not (root / "AGENTS.md").exists():
        print(f"ERROR: not a repository root: {root}", file=sys.stderr)
        return 2

    findings = run(root)
    for finding in findings:
        print(finding.render())

    errors = [item for item in findings if item.level == "ERROR"]
    warnings = [item for item in findings if item.level == "WARNING"]
    print(
        f"SUMMARY skills={len(EXPECTED_SKILLS)} schemas_expected={EXPECTED_SCHEMA_COUNT} "
        f"fixtures_expected={len(EXPECTED_FIXTURE_FILES)} cases_expected={EXPECTED_TOTAL_CASES} "
        f"errors={len(errors)} warnings={len(warnings)}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

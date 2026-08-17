#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import yaml

LEGACY_V3_TYPES = {"authoring_guide", "manager", "workflow", "operation", "validator"}
LEGACY_V3_STATUS = {"pending", "draft", "frozen"}
ALLOWED_ACCESS = {"reference_only", "read_only", "authoring_reference"}
SUPPORTED_VERSIONS = {3, 4, 5}


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def require(data: dict, key: str, path: Path, errors: list[str]) -> None:
    if key not in data:
        fail(f"{path.name}: missing {key}", errors)


def validate_common(data: dict, path: Path, errors: list[str]) -> None:
    for key in ("schema_version", "skill_name", "skill_path", "owned_content", "external_references"):
        require(data, key, path, errors)
    if errors:
        return

    version = data["schema_version"]
    if version not in SUPPORTED_VERSIONS:
        fail(f"{path.name}: unsupported schema_version {version}", errors)

    skill_path = str(data["skill_path"])
    if not skill_path or skill_path.startswith("/"):
        fail(f"{path.name}: skill_path must be a non-empty project-relative path", errors)

    owned = data.get("owned_content") or {}
    if not isinstance(owned, dict):
        fail(f"{path.name}: owned_content must be a mapping", errors)
        owned = {}

    for concept, item in owned.items():
        owner = str((item or {}).get("owner", ""))
        if not owner:
            fail(f"{path.name}: owned_content.{concept} missing owner", errors)
        elif owner.startswith("/"):
            fail(f"{path.name}: owner must be project-relative: {owner}", errors)
        elif not (owner == skill_path or owner.startswith(skill_path.rstrip("/") + "/")):
            fail(f"{path.name}: owned owner outside skill_path: {owner}", errors)

    external = data.get("external_references") or []
    if not isinstance(external, list):
        fail(f"{path.name}: external_references must be a list", errors)
        external = []
    for i, item in enumerate(external):
        if not isinstance(item, dict):
            fail(f"{path.name}: external_references[{i}] must be a mapping", errors)
            continue
        for key in ("purpose", "owner", "access"):
            if key not in item:
                fail(f"{path.name}: external_references[{i}] missing {key}", errors)
        owner = str(item.get("owner", ""))
        if owner.startswith("/"):
            fail(f"{path.name}: external owner must be project-relative: {owner}", errors)
        access = item.get("access")
        if access not in ALLOWED_ACCESS:
            fail(f"{path.name}: unsupported external access {access}", errors)

    if "forbidden_duplication" in data:
        fail(f"{path.name}: forbidden_duplication belongs only in shared authoring rules", errors)


def validate_v3(data: dict, path: Path, errors: list[str]) -> None:
    for key in ("skill_type", "contract_status", "content_ownership_status"):
        require(data, key, path, errors)
    if any(key not in data for key in ("skill_type", "contract_status", "content_ownership_status")):
        return
    if data["skill_type"] not in LEGACY_V3_TYPES:
        fail(f"{path.name}: invalid legacy skill_type {data['skill_type']}", errors)
    if data["contract_status"] not in LEGACY_V3_STATUS:
        fail(f"{path.name}: invalid legacy contract_status", errors)
    if data["content_ownership_status"] not in LEGACY_V3_STATUS:
        fail(f"{path.name}: invalid legacy content_ownership_status", errors)
    if data["content_ownership_status"] == "pending" and (data.get("owned_content") or {}):
        fail(f"{path.name}: legacy pending ownership must have empty owned_content", errors)


def validate_v4(data: dict, path: Path, errors: list[str]) -> None:
    require(data, "status", path, errors)


def validate_v5(data: dict, path: Path, errors: list[str]) -> None:
    require(data, "status", path, errors)
    if "skill_type" in data:
        fail(f"{path.name}: v5 content maps must not classify scientific Skills with skill_type", errors)
    if "contract_status" in data or "content_ownership_status" in data:
        fail(f"{path.name}: v5 content maps use one status field; legacy contract/ownership status fields are not used", errors)


def validate_map(path: Path, project_root: Path) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return [f"{path.name}: root must be a mapping"]

    validate_common(data, path, errors)
    if "schema_version" not in data:
        return errors

    version = data["schema_version"]
    if version == 3:
        validate_v3(data, path, errors)
    elif version == 4:
        validate_v4(data, path, errors)
    elif version == 5:
        validate_v5(data, path, errors)
    return errors


def main() -> int:
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    cm_dir = project_root / "00_authoring" / "content_maps"
    errors: list[str] = []
    files = sorted(cm_dir.glob("*.yaml"))
    for path in files:
        errors.extend(validate_map(path, project_root))
    print(f"checked_maps: {len(files)}")
    print(f"errors: {len(errors)}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

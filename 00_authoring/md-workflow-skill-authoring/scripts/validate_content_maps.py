#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
import yaml

ALLOWED_TYPES = {"authoring_guide", "manager", "workflow", "operation", "validator"}
ALLOWED_STATUS = {"pending", "draft", "frozen"}


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def validate_map(path: Path, project_root: Path) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    required = ["schema_version", "skill_name", "skill_type", "skill_path", "contract_status", "content_ownership_status", "owned_content", "external_references"]
    for key in required:
        if key not in data:
            fail(f"{path.name}: missing {key}", errors)
    if errors:
        return errors
    if data["schema_version"] != 3:
        fail(f"{path.name}: schema_version must be 3", errors)
    if data["skill_type"] not in ALLOWED_TYPES:
        fail(f"{path.name}: invalid skill_type {data['skill_type']}", errors)
    if data["contract_status"] not in ALLOWED_STATUS:
        fail(f"{path.name}: invalid contract_status", errors)
    if data["content_ownership_status"] not in ALLOWED_STATUS:
        fail(f"{path.name}: invalid content_ownership_status", errors)
    skill_path = str(data["skill_path"])
    if skill_path.startswith("/"):
        fail(f"{path.name}: skill_path must be project-relative", errors)
    owned = data["owned_content"] or {}
    if data["content_ownership_status"] == "pending" and owned:
        fail(f"{path.name}: pending ownership must have empty owned_content", errors)
    for concept, item in owned.items():
        owner = str((item or {}).get("owner", ""))
        if not owner:
            fail(f"{path.name}: owned_content.{concept} missing owner", errors)
        elif owner.startswith("/"):
            fail(f"{path.name}: owner must be project-relative: {owner}", errors)
        elif not (owner == skill_path or owner.startswith(skill_path.rstrip("/") + "/")):
            fail(f"{path.name}: owned owner outside skill_path: {owner}", errors)
    for i, item in enumerate(data["external_references"] or []):
        for key in ("purpose", "owner", "access"):
            if key not in item:
                fail(f"{path.name}: external_references[{i}] missing {key}", errors)
        owner = str(item.get("owner", ""))
        if owner.startswith("/"):
            fail(f"{path.name}: external owner must be project-relative: {owner}", errors)
        if item.get("access") != "reference_only":
            fail(f"{path.name}: external access must be reference_only", errors)
    if "forbidden_duplication" in data:
        fail(f"{path.name}: forbidden_duplication must be defined only in shared authoring rules", errors)
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

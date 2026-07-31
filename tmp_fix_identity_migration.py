from pathlib import Path

path = Path("tmp_migrate_v1_2_identity.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        'replace_all(path, common, "                **_identity_fields(residue),\\n", minimum=3)',
        'replace_all(path, common, "                **_identity_fields(residue),\\n", minimum=1)',
        "classification-engine occurrence assertion",
    ),
    (
        'replace_once(obs, "      - chain_index\\n      - source_chain_id\\n", "      - source_identity\\n      - current_identity\\n      - chain_index\\n      - source_chain_id\\n")',
        'replace_once(obs, "      - chain_index\\n      - source_chain_id\\n      - source_resid\\n", "      - source_identity\\n      - current_identity\\n      - chain_index\\n      - source_chain_id\\n      - source_resid\\n")',
        "observation residue-record required fields",
    ),
    (
        '\n\ndef update_structure_records() -> None:\n',
        '''\n\ndef replace_first(path: Path, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise RuntimeError(f"{path}: first-match target not found: {old[:80]!r}")
    write(path, text.replace(old, new, 1))


def update_structure_records() -> None:
''',
        "replace_first helper insertion",
    ),
    (
        'replace_once(\n        obs,\n        "    properties:\\n      chain_index:\\n",',
        'replace_first(\n        obs,\n        "    properties:\\n      chain_index:\\n",',
        "observation residue-record property target",
    ),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one {label}, found {count}")
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

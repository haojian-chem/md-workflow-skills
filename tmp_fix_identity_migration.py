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
    (
        'replace_once(conn, "      - chain_index\\n      - source_chain_id\\n",',
        'replace_first(conn, "      - chain_index\\n      - source_chain_id\\n",',
        "connection endpoint required target",
    ),
    (
        'replace_once(\n        conn,\n        "    properties:\\n      chain_index: {type: integer, minimum: 1}\\n      source_chain_id:\\n",',
        'replace_first(\n        conn,\n        "    properties:\\n      chain_index: {type: integer, minimum: 1}\\n      source_chain_id:\\n",',
        "connection endpoint property target",
    ),
    (
        'replace_once(coord, "      - chain_index\\n      - source_chain_id\\n",',
        'replace_first(coord, "      - chain_index\\n      - source_chain_id\\n",',
        "coordination endpoint required target",
    ),
    (
        'replace_once(\n        final,\n        "    properties:\\n      chain_index: {type: integer, minimum: 1}\\n      source_chain_id:\\n",',
        'replace_first(\n        final,\n        "    properties:\\n      chain_index: {type: integer, minimum: 1}\\n      source_chain_id:\\n",',
        "final residue-record property target",
    ),
    (
        '''    first = text.find(marker)
    second = text.find(marker, first + 1)
    if second < 0:
        raise RuntimeError("connection schema missing second identity property marker")
''',
        '''    target = text.find(marker)
    if target < 0:
        raise RuntimeError("connection schema missing remaining identity property marker")
''',
        "connection remaining marker selection",
    ),
    (
        '''    first = text.find(marker)
    second = text.find(marker, first + 1)
    if second < 0:
        raise RuntimeError("final schema missing endpoint identity property marker")
''',
        '''    target = text.find(marker)
    if target < 0:
        raise RuntimeError("final schema missing remaining endpoint identity property marker")
''',
        "final remaining marker selection",
    ),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one {label}, found {count}")
    text = text.replace(old, new)

old_slice = 'text = text[:second] + text[second:].replace(marker, replacement, 1)'
new_slice = 'text = text[:target] + text[target:].replace(marker, replacement, 1)'
if text.count(old_slice) != 2:
    raise SystemExit(f"expected two remaining marker slices, found {text.count(old_slice)}")
text = text.replace(old_slice, new_slice)

path.write_text(text, encoding="utf-8")

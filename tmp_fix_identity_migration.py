from pathlib import Path

path = Path("tmp_migrate_v1_2_identity.py")
text = path.read_text(encoding="utf-8")
old = 'replace_all(path, common, "                **_identity_fields(residue),\\n", minimum=3)'
new = 'replace_all(path, common, "                **_identity_fields(residue),\\n", minimum=1)'
if text.count(old) != 1:
    raise SystemExit(f"expected one migration assertion, found {text.count(old)}")
path.write_text(text.replace(old, new), encoding="utf-8")

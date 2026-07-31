from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATION = ROOT / "04_evals/component_and_residue_classification_validator/VALIDATION.md"
CONTENT_MAP = ROOT / "00_authoring/content_maps/component_and_residue_classification_validator.yaml"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replacements = [
    ("更新日期：2026-07-30", "更新日期：2026-07-31"),
    ("run: 30508963075\njob: 90764701893\ntests: 64 passed", "run: 30598093226\njob: 91054763872\ntests: 72 passed"),
    ("run: 30508963060\njob: 90764701793", "run: 30598093207\njob: 91054763846"),
    ("run: 30508963069\njob: 90764701873", "run: 30598093217\njob: 91054763992"),
    ("run: 30508963057\njob: 90764701753", "run: 30598093234\njob: 91054763855"),
    ("run: 30508963063\njob: 90764701869", "run: 30598093230\njob: 91054763869"),
    ("run: 30508963095\njob: 90764701922", "run: 30598093255\njob: 91054763938"),
    ("run: 30452751000\njob: 90578579001", "run: 30598093226\njob: 91054763872"),
]
for old, new in replacements:
    replace_once(VALIDATION, old, new)

replace_once(
    VALIDATION,
    "- 缺失残基、author `source_resid` 和 mapping unresolved；\n",
    "- 缺失残基、author `source_resid` 和 mapping unresolved；\n- `source_identity` / `current_identity` 双身份、兼容镜像一致性与 presence-status gate；\n",
)

identity_section = '''## 9. 源身份与当前身份

1.2 现以两套字段名不同的正式身份保存残基与关系端点：

```text
source_identity: source_model_id / source_chain_id / source_resid / source_residue_name
current_identity: current_model_id / current_chain_id / current_resid / current_residue_name
relation endpoint: 另含 source_atom_name / current_atom_name
```

验收确认：

- `source_*` 是输入来源追溯身份，后续 revision 禁止覆盖；
- `current_*` 是当前实际 STRUCTURE revision 身份；
- 1.2 不修改结构，因此 `OBSERVED` 实例两套身份值相等，但字段保持分离；
- `MISSING_EXPECTED` 残基必须具有 `current_identity: null`；
- `chain_index` 位于两套 identity 外部，只表示逻辑分组；
- topology effect 可以改变 `chain_index`，不得伪造 current chain/resid 变化；
- v1 平铺 source 字段只是兼容镜像，运行时必须与 `source_identity` 一致；
- final-result builder 与 relation checker 会拒绝双身份或兼容镜像不一致的输入。

永久回归测试：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_dual_identity.py
```

该测试核验字段集合、关系端点、schema 必填约束、`OBSERVED`/`MISSING_EXPECTED` 条件约束以及运行时一致性拒绝路径。

## 10. 结论
'''
replace_once(VALIDATION, "## 9. 结论\n", identity_section)

map_replacements = [
    ("run_id: 30508963075\n    job_id: 90764701893\n    conclusion: success\n    test_count: 64", "run_id: 30598093226\n    job_id: 91054763872\n    conclusion: success\n    test_count: 72"),
    ("run_id: 30508963060\n    job_id: 90764701793", "run_id: 30598093207\n    job_id: 91054763846"),
    ("run_id: 30508963069\n    job_id: 90764701873", "run_id: 30598093217\n    job_id: 91054763992"),
    ("run_id: 30508963057\n    job_id: 90764701753", "run_id: 30598093234\n    job_id: 91054763855"),
    ("run_id: 30508963063\n    job_id: 90764701869", "run_id: 30598093230\n    job_id: 91054763869"),
    ("run_id: 30508963095\n    job_id: 90764701922", "run_id: 30598093255\n    job_id: 91054763938"),
    ("run_id: 30452751000\n    job_id: 90578579001", "run_id: 30598093226\n    job_id: 91054763872"),
]
for old, new in map_replacements:
    replace_once(CONTENT_MAP, old, new)

replace_once(
    CONTENT_MAP,
    "  - Residue and atom names are exact and case-sensitive; uppercase normalization, alias matching, regular expressions and fuzzy-name matching are prohibited.\n",
    "  - Residue and atom names are exact and case-sensitive; uppercase normalization, alias matching, regular expressions and fuzzy-name matching are prohibited.\n  - Residue and relation endpoint identity is dual: immutable source_* provenance and current_* STRUCTURE identity use distinct field names; chain_index remains an external logical grouping field.\n",
)

print("v1.2 identity validation evidence updated")

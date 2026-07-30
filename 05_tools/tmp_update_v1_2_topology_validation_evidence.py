from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "04_evals/component_and_residue_classification_validator/VALIDATION.md"
CONTENT_MAP = ROOT / "00_authoring/content_maps/component_and_residue_classification_validator.yaml"

RUNS = {
    "synthetic": ("30508963075", "90764701893", "64"),
    "pdb": ("30508963060", "90764701793"),
    "mmcif": ("30508963069", "90764701873"),
    "af3": ("30508963057", "90764701753"),
    "gromacs": ("30508963063", "90764701869"),
    "authoring": ("30508963095", "90764701922"),
}


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing replacement anchor for {label}: {old!r}")
    return text.replace(old, new)


def update_validation() -> None:
    text = VALIDATION.read_text(encoding="utf-8")
    text = replace_exact(text, "更新日期：2026-07-29", "更新日期：2026-07-30", "date")
    replacements = {
        "run: 30452751000\njob: 90578579001\ntests: 62 passed": (
            f"run: {RUNS['synthetic'][0]}\njob: {RUNS['synthetic'][1]}\ntests: {RUNS['synthetic'][2]} passed"
        ),
        "run: 30452751113\njob: 90578579395": f"run: {RUNS['pdb'][0]}\njob: {RUNS['pdb'][1]}",
        "run: 30452751015\njob: 90578578794": f"run: {RUNS['mmcif'][0]}\njob: {RUNS['mmcif'][1]}",
        "run: 30452751038\njob: 90578579075": f"run: {RUNS['af3'][0]}\njob: {RUNS['af3'][1]}",
        "run: 30452750925\njob: 90578579923": f"run: {RUNS['gromacs'][0]}\njob: {RUNS['gromacs'][1]}",
        "run: 30452751343\njob: 90578580094": f"run: {RUNS['authoring'][0]}\njob: {RUNS['authoring'][1]}",
    }
    for old, new in replacements.items():
        text = replace_exact(text, old, new, old.splitlines()[0])

    coverage_anchor = "- possible connection、metal coordination 和 topology effect；"
    coverage_line = (
        "- `TOPOLOGY_LINKED_NONSTANDARD` 枚举、registry 路径和 "
        "`topology_linked_nonstandard_count` 输出字段迁移；"
    )
    if coverage_line not in text:
        text = replace_exact(
            text,
            coverage_anchor,
            coverage_anchor + "\n" + coverage_line,
            "topology vocabulary coverage",
        )

    text = text.replace(
        "该运行对应文档层级整改后的最终文件，确认：",
        "该运行对应文档层级与 topology class 术语整改后的最终文件，确认：",
    )
    authoring_line = "- 旧枚举、旧 registry 路径和旧 summary 字段在活动仓库文本中均为零残留。"
    if authoring_line not in text:
        text = replace_exact(
            text,
            "- 上下级规则未形成重复定义。",
            "- 上下级规则未形成重复定义。\n" + authoring_line,
            "authoring vocabulary assertion",
        )

    section = """
## 8. Topology class 术语迁移

```text
旧 topology_class: COVALENTLY_LINKED_NONSTANDARD
新 topology_class: TOPOLOGY_LINKED_NONSTANDARD
旧 summary 字段: covalently_linked_nonstandard_count
新 summary 字段: topology_linked_nonstandard_count
```

迁移后的语义边界：

- `TOPOLOGY_LINKED_NONSTANDARD` 只描述非标准组分已经纳入连接拓扑；
- 触发关系仍单独记录为 `COVALENT_CONNECTION`、`METAL_COORDINATION` 或其他受支持 relation type；
- 禁止根据 topology class 反推化学关系类型；
- `HEM` 的名称级 baseline 示例为 `INDEPENDENT_NONSTANDARD`；
- 只有确认且应用了 topology effect 的具体 HEM 实例才提升为 `TOPOLOGY_LINKED_NONSTANDARD`；
- 旧枚举、旧 registry 文件名和旧 summary 字段不再由活动 schema 或实现接受。

永久回归测试：

```text
04_evals/component_and_residue_classification_validator/test_v1_2_topology_class_vocabulary.py
```

该测试扫描活动仓库文本，并核验三个分类 schema、规则定义、registry 路径和 summary 字段。

## 9. 结论
"""
    if "## 8. Topology class 术语迁移" not in text:
        text = replace_exact(text, "## 8. 结论\n", section, "terminology migration section")

    VALIDATION.write_text(text, encoding="utf-8")


def update_content_map() -> None:
    text = CONTENT_MAP.read_text(encoding="utf-8")
    replacements = {
        "run_id: 30452751000\n    job_id: 90578579001\n    conclusion: success\n    test_count: 62": (
            f"run_id: {RUNS['synthetic'][0]}\n    job_id: {RUNS['synthetic'][1]}\n"
            f"    conclusion: success\n    test_count: {RUNS['synthetic'][2]}"
        ),
        "run_id: 30452751113\n    job_id: 90578579395": f"run_id: {RUNS['pdb'][0]}\n    job_id: {RUNS['pdb'][1]}",
        "run_id: 30452751015\n    job_id: 90578578794": f"run_id: {RUNS['mmcif'][0]}\n    job_id: {RUNS['mmcif'][1]}",
        "run_id: 30452751038\n    job_id: 90578579075": f"run_id: {RUNS['af3'][0]}\n    job_id: {RUNS['af3'][1]}",
        "run_id: 30452750925\n    job_id: 90578579923": f"run_id: {RUNS['gromacs'][0]}\n    job_id: {RUNS['gromacs'][1]}",
        "run_id: 30452751343\n    job_id: 90578580094": f"run_id: {RUNS['authoring'][0]}\n    job_id: {RUNS['authoring'][1]}",
    }
    for old, new in replacements.items():
        text = replace_exact(text, old, new, old.splitlines()[0])

    migration_note = (
        "  - TOPOLOGY_LINKED_NONSTANDARD describes connected-topology membership only; "
        "relation types remain separate, and deprecated enum, registry path and summary field names are prohibited."
    )
    if migration_note not in text:
        anchor = (
            "  - Confirmed HEM-CYS/HIE coordination with promote=true moves HEM into the polymer chain "
            "and marks it TOPOLOGY_LINKED_NONSTANDARD."
        )
        text = replace_exact(text, anchor, anchor + "\n" + migration_note, "content-map migration note")

    CONTENT_MAP.write_text(text, encoding="utf-8")


def validate() -> None:
    validation = VALIDATION.read_text(encoding="utf-8")
    content_map = CONTENT_MAP.read_text(encoding="utf-8")
    for value in [
        RUNS["synthetic"][0],
        RUNS["pdb"][0],
        RUNS["mmcif"][0],
        RUNS["af3"][0],
        RUNS["gromacs"][0],
        RUNS["authoring"][0],
        "64 passed",
        "## 8. Topology class 术语迁移",
    ]:
        if value not in validation:
            raise RuntimeError(f"validation evidence missing: {value}")
    if "test_count: 64" not in content_map:
        raise RuntimeError("content map test count was not updated")


if __name__ == "__main__":
    update_validation()
    update_content_map()
    validate()

from __future__ import annotations

from pathlib import Path

ENGINE = Path(
    "02_validators/component_and_residue_classification_validator/scripts/classification_engine.py"
)
text = ENGINE.read_text(encoding="utf-8")
if "def _baseline_chain_polymer_class" in text:
    raise SystemExit(0)

marker = "\ndef _build_chain_groups(\n"
helper = '''
def _baseline_chain_polymer_class(analysis: ResidueAnalysis) -> str | None:
    """Determine chain-level polymer grouping independently of resolved labels.

    Reliable structure entity/polymer metadata must keep a residue in its
    source polymer or branched chain even when project/registry/force-field
    classification labels conflict and remain pending confirmation.
    """

    residue = analysis.residue
    if (
        residue.entity_type == gemmi.EntityType.Polymer
        or residue.polymer_type != gemmi.PolymerType.Unknown
    ):
        return "POLYMER"
    if residue.entity_type == gemmi.EntityType.Branched:
        return "BRANCHED"
    if analysis.classification.polymer_class in {"POLYMER", "BRANCHED"}:
        return analysis.classification.polymer_class
    return None

'''
if marker not in text:
    raise SystemExit("failed to locate _build_chain_groups marker")
text = text.replace(marker, "\n" + helper + "def _build_chain_groups(\n", 1)

old = '''    by_chain: dict[tuple[str, str | None, str], list[ResidueAnalysis]] = defaultdict(list)
    for analysis in analyses:
        classification = analysis.classification
        if classification.polymer_class in {"POLYMER", "BRANCHED"}:
            key = (
                analysis.residue.source_chain_id,
                analysis.residue.entity_id,
                classification.polymer_class,
            )
            by_chain[key].append(analysis)
'''
new = '''    by_chain: dict[tuple[str, str | None, str], list[ResidueAnalysis]] = defaultdict(list)
    for analysis in analyses:
        baseline_polymer_class = _baseline_chain_polymer_class(analysis)
        if baseline_polymer_class is not None:
            key = (
                analysis.residue.source_chain_id,
                analysis.residue.entity_id,
                baseline_polymer_class,
            )
            by_chain[key].append(analysis)
'''
if old not in text:
    raise SystemExit("failed to locate polymer grouping block")
text = text.replace(old, new, 1)
ENGINE.write_text(text, encoding="utf-8")

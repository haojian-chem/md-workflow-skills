from pathlib import Path
import re

ROOT = Path(".")
SKILL = ROOT / "02_validators/component_and_residue_classification_validator"
CHANGED: list[Path] = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    CHANGED.append(path)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


# AlphaFold Server parser becomes a normal dependency with no installation side effects.
af3_path = SKILL / "scripts/af3_server_sequence_reference.py"
af3_text = '''#!/usr/bin/env python3
"""AlphaFold Server job_request JSON sequence-reference parser."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from classification_common import ClassificationToolError


def _server_chain_id(index: int) -> str:
    """Return AlphaFold Server-style A..Z, AA.. IDs for a zero-based index."""
    if index < 0:
        raise ClassificationToolError(
            "AlphaFold Server chain index must be non-negative"
        )
    value = index + 1
    letters: list[str] = []
    while value:
        value, remainder = divmod(value - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def _merge_sequence(
    sequences: dict[str, list[str]],
    identifier: str,
    monomers: list[str],
) -> None:
    existing = sequences.get(identifier)
    if existing is not None and existing != monomers:
        raise ClassificationToolError(
            f"conflicting AF3 sequences for chain {identifier}"
        )
    sequences[identifier] = monomers


def _positive_count(payload: dict[str, Any]) -> int:
    value = payload.get("count", 1)
    if isinstance(value, bool):
        raise ClassificationToolError(
            "AlphaFold Server sequence count must be a positive integer"
        )
    try:
        count = int(value)
    except (TypeError, ValueError) as exc:
        raise ClassificationToolError(
            "AlphaFold Server sequence count must be a positive integer"
        ) from exc
    if count < 1 or count != value:
        raise ClassificationToolError(
            "AlphaFold Server sequence count must be a positive integer"
        )
    return count


def parse_af3_server_job_request(
    path: Path,
) -> dict[str, list[str]] | None:
    """Parse one AlphaFold Server job, or return None for another JSON dialect."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return None
    if len(data) != 1 or not isinstance(data[0], dict):
        raise ClassificationToolError(
            "AlphaFold Server job_request JSON must contain exactly one job"
        )
    job = data[0]
    if job.get("dialect") != "alphafoldserver":
        raise ClassificationToolError(
            "top-level AF3 JSON list is accepted only for dialect alphafoldserver"
        )
    entries = job.get("sequences")
    if not isinstance(entries, list):
        raise ClassificationToolError(
            "AlphaFold Server job_request JSON has no sequences list"
        )

    sequences: dict[str, list[str]] = {}
    next_chain_index = 0
    for entry in entries:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise ClassificationToolError(
                "AlphaFold Server sequence entries must be single-key mappings"
            )
        _kind, payload = next(iter(entry.items()))
        if not isinstance(payload, dict):
            raise ClassificationToolError(
                "AlphaFold Server sequence payload must be a mapping"
            )
        count = _positive_count(payload)
        explicit_ids = payload.get("id")
        if isinstance(explicit_ids, str):
            identifiers = [explicit_ids]
        elif isinstance(explicit_ids, list):
            identifiers = [str(value) for value in explicit_ids]
        elif explicit_ids is None:
            identifiers = [
                _server_chain_id(next_chain_index + offset)
                for offset in range(count)
            ]
        else:
            raise ClassificationToolError(
                "AlphaFold Server sequence id must be a string or list"
            )
        if explicit_ids is not None and len(identifiers) != count:
            raise ClassificationToolError(
                "AlphaFold Server explicit id count does not match entity count"
            )

        sequence = payload.get("sequence")
        if isinstance(sequence, str):
            monomers = list(sequence.strip())
            if not monomers:
                raise ClassificationToolError(
                    "AlphaFold Server polymer sequence must not be empty"
                )
            for identifier in identifiers:
                _merge_sequence(sequences, identifier, monomers)
        # Ligands and ions still consume server-assigned chain identifiers.
        next_chain_index += count
    return sequences


# Private compatibility alias for existing direct parser tests.
_parse_server_job_request = parse_af3_server_job_request
'''
write(af3_path, af3_text)

# Missing-residue module owns strict parsing, reconciliation and AF3 dispatch.
sequence_path = SKILL / "scripts/sequence_missing.py"
text = read(sequence_path)
text = replace_once(
    text,
    "import json\nimport re\n",
    "from collections import Counter, defaultdict, deque\nimport json\nimport re\n",
    "sequence collections imports",
)
text = replace_once(
    text,
    "from classification_common import ClassificationToolError\n",
    "from af3_server_sequence_reference import parse_af3_server_job_request\n"
    "from classification_common import ClassificationToolError\n",
    "sequence AF3 parser import",
)
strict_parser = '''def _parse_pdb_remark_465(
    path: Path,
    selected_model_id: str,
) -> list[MissingResidueEvidence]:
    """Parse only fixed-column data rows from the PDB REMARK 465 table."""
    residue_name_pattern = re.compile(r"[A-Za-z0-9]{1,3}")
    sequence_number_pattern = re.compile(r"-?\\d+")
    results: list[MissingResidueEvidence] = []
    for raw in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        if not raw.startswith("REMARK 465") or len(raw) < 24:
            continue
        padded = raw.ljust(27)
        model_field = padded[11:14].strip()
        residue_name = padded[15:18].strip()
        source_chain_id = clean_optional_text(padded[19:20])
        sequence_number = padded[21:26].strip()
        insertion_code = clean_optional_text(padded[26:27])
        if model_field:
            if not model_field.isdigit() or model_field != selected_model_id:
                continue
        if residue_name_pattern.fullmatch(residue_name) is None:
            continue
        if sequence_number_pattern.fullmatch(sequence_number) is None:
            continue
        results.append(
            MissingResidueEvidence(
                source_chain_id=source_chain_id,
                residue_name=residue_name,
                source_resid_number=sequence_number,
                insertion_code=insertion_code,
                sequence_position=None,
                evidence_type="PDB_REMARK_465",
            )
        )
    return results


'''
text, count = re.subn(
    r'def _parse_pdb_remark_465\(.*?\n\ndef _mmcif_value\(',
    strict_parser + "def _mmcif_value(",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"strict PDB parser replacement failed: {count}")
text = replace_once(
    text,
    "def sequence_based_missing_residues(\n",
    "def _sequence_based_missing_residues_base(\n",
    "rename missing-residue base",
)
parse_marker = "def parse_af3_sequence_references(\n"
parse_index = text.find(parse_marker)
if parse_index < 0:
    raise SystemExit("cannot locate AF3 sequence-reference parser")
prefix = text[:parse_index]
public_tail = '''def sequence_based_missing_residues(
    structure: gemmi.Structure,
    model: gemmi.Model,
    residues: list[ResidueRecord],
    explicit_records: list[MissingResidueEvidence],
) -> tuple[
    list[MissingResidueEvidence],
    list[dict[str, Any]],
    dict[tuple[str, str, str | None, str], int],
    list[dict[str, Any]],
]:
    """Run base sequence reconciliation and bind explicit author IDs."""
    resolved, unresolved, observed_positions, chain_checks = (
        _sequence_based_missing_residues_base(
            structure,
            model,
            residues,
            explicit_records,
        )
    )
    available_plain_records = Counter(
        (item.source_chain_id, item.residue_name)
        for item in resolved
        if item.source_chain_id is not None
        and item.source_resid_number is not None
        and item.sequence_position is None
        and item.evidence_type
        in {"PDB_REMARK_465", "MMCIF_UNOBSERVED_RESIDUES"}
    )
    recovered_positions: defaultdict[
        tuple[str | None, str],
        list[int],
    ] = defaultdict(list)
    retained_unresolved: list[dict[str, Any]] = []
    for item in unresolved:
        subject = item.get("subject") or {}
        key = (subject.get("source_chain_id"), subject.get("residue_name"))
        alignment_only = item.get("evidence") == ["ENTITY_SEQUENCE_ALIGNMENT"]
        if (
            item.get("issue_type")
            == "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE"
            and alignment_only
            and subject.get("sequence_position") is not None
            and available_plain_records[key] > 0
        ):
            available_plain_records[key] -= 1
            recovered_positions[key].append(int(subject["sequence_position"]))
            continue
        retained_unresolved.append(item)

    position_queues = {
        key: deque(sorted(values))
        for key, values in recovered_positions.items()
    }
    normalized_resolved: list[MissingResidueEvidence] = []
    for item in resolved:
        key = (item.source_chain_id, item.residue_name)
        queue = position_queues.get(key)
        if (
            queue
            and item.source_resid_number is not None
            and item.sequence_position is None
            and item.evidence_type
            in {"PDB_REMARK_465", "MMCIF_UNOBSERVED_RESIDUES"}
        ):
            normalized_resolved.append(
                MissingResidueEvidence(
                    source_chain_id=item.source_chain_id,
                    residue_name=item.residue_name,
                    source_resid_number=item.source_resid_number,
                    insertion_code=item.insertion_code,
                    sequence_position=queue.popleft(),
                    evidence_type=(
                        f"{item.evidence_type}+ENTITY_SEQUENCE_ALIGNMENT"
                    ),
                )
            )
        else:
            normalized_resolved.append(item)
    return (
        normalized_resolved,
        retained_unresolved,
        observed_positions,
        chain_checks,
    )


def _merge_sequence(
    sequences: dict[str, list[str]],
    identifier: str,
    monomers: list[str],
) -> None:
    existing = sequences.get(identifier)
    if existing is not None and existing != monomers:
        raise ClassificationToolError(
            f"conflicting sequence references for chain {identifier}"
        )
    sequences[identifier] = monomers


def parse_af3_sequence_references(
    sequence_references: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Read AlphaFold Server/AF3 JSON and FASTA references by exact chain ID."""
    sequences: dict[str, list[str]] = {}
    for reference in sequence_references:
        reference_type = reference.get("type") or reference.get(
            "reference_type"
        )
        path = Path(reference["path"]).resolve()
        if reference_type == "AF3_INPUT_JSON":
            server_sequences = parse_af3_server_job_request(path)
            if server_sequences is not None:
                for identifier, monomers in server_sequences.items():
                    _merge_sequence(sequences, identifier, monomers)
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ClassificationToolError(
                    "AF3 input JSON must be a mapping or one server job list"
                )
            for entry in data.get("sequences", []):
                if not isinstance(entry, dict) or len(entry) != 1:
                    continue
                _kind, payload = next(iter(entry.items()))
                if not isinstance(payload, dict):
                    continue
                identifiers = payload.get("id")
                sequence = payload.get("sequence")
                if isinstance(identifiers, str):
                    identifiers = [identifiers]
                if not isinstance(identifiers, list) or not isinstance(
                    sequence,
                    str,
                ):
                    continue
                monomers = list(sequence.strip())
                for identifier in identifiers:
                    _merge_sequence(
                        sequences,
                        str(identifier),
                        monomers,
                    )
        elif reference_type == "FASTA":
            current_id: str | None = None
            chunks: list[str] = []
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if current_id is not None:
                        _merge_sequence(
                            sequences,
                            current_id,
                            list("".join(chunks)),
                        )
                    current_id = line[1:].split()[0]
                    chunks = []
                else:
                    chunks.append(line)
            if current_id is not None:
                _merge_sequence(
                    sequences,
                    current_id,
                    list("".join(chunks)),
                )
    return sequences


def merge_unresolved_observations(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge equal issue subjects while preserving first-seen evidence order."""
    import json as _json

    merged: list[dict[str, Any]] = []
    index_by_key: dict[str, int] = {}
    for item in items:
        key = _json.dumps(
            {
                "issue_type": item.get("issue_type"),
                "subject": item.get("subject"),
                "resolution_status": item.get("resolution_status"),
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        existing_index = index_by_key.get(key)
        if existing_index is None:
            copied = dict(item)
            copied["evidence"] = list(item.get("evidence", []))
            index_by_key[key] = len(merged)
            merged.append(copied)
            continue
        evidence = merged[existing_index]["evidence"]
        for value in item.get("evidence", []):
            if value not in evidence:
                evidence.append(value)
    return merged


def normalize_missing_residue_outputs(
    observations: dict[str, Any],
) -> dict[str, Any]:
    """Make missing-residue check status agree with identifier resolvability."""
    unresolved = merge_unresolved_observations(
        observations.get("unresolved_observations", [])
    )
    observations["unresolved_observations"] = unresolved
    source_resid_unresolved_chains: set[str | None] = set()
    chain_unresolved_chains: set[str | None] = set()
    for item in unresolved:
        subject = item.get("subject") or {}
        source_chain_id = subject.get("source_chain_id")
        if (
            item.get("issue_type")
            == "MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE"
        ):
            source_resid_unresolved_chains.add(source_chain_id)
        elif item.get("issue_type") == "MISSING_RESIDUE_CHAIN_UNRESOLVED":
            chain_unresolved_chains.add(source_chain_id)

    for check in observations.get("missing_residue_checks", []):
        source_chain_id = check.get("source_chain_id")
        if (
            check.get("chain_index") is None
            and source_chain_id in chain_unresolved_chains
        ):
            check["status"] = "MAPPING_UNRESOLVED"
            check["missing_residue_count"] = 0
            check["reason"] = "MISSING_RESIDUE_CHAIN_UNRESOLVED"
        elif (
            check.get("missing_residue_count") == 0
            and source_chain_id in source_resid_unresolved_chains
        ):
            check["status"] = "MAPPING_UNRESOLVED"
            check["reason"] = (
                "AUTHOR_SOURCE_RESIDS_FOR_MISSING_RESIDUES_UNAVAILABLE"
            )
    summary = observations.get("summary")
    if isinstance(summary, dict):
        summary["unresolved_observation_count"] = len(unresolved)
    return observations
'''
write(sequence_path, prefix + public_tail)

# Core grouping and output normalization become ordinary implementation logic.
core_path = SKILL / "scripts/classification_engine_core.py"
text = read(core_path)
text = replace_once(
    text,
    "    sequence_based_missing_residues,\n)",
    "    sequence_based_missing_residues,\n"
    "    normalize_missing_residue_outputs,\n)",
    "core normalization import",
)
old = '''    for analysis in analyses:
        classification = analysis.classification
        if classification.polymer_class in {"POLYMER", "BRANCHED"}:
            key = (
                analysis.residue.source_chain_id,
                analysis.residue.entity_id,
                classification.polymer_class,
            )
            by_chain[key].append(analysis)
'''
new = '''    for analysis in analyses:
        classification = analysis.classification
        grouping_polymer_class = (
            _entity_polymer_class(analysis.residue)
            or classification.polymer_class
        )
        if grouping_polymer_class in {"POLYMER", "BRANCHED"}:
            key = (
                analysis.residue.source_chain_id,
                analysis.residue.entity_id,
                grouping_polymer_class,
            )
            by_chain[key].append(analysis)
'''
text = replace_once(text, old, new, "core structural grouping")
text = replace_once(
    text,
    "    validate_document(observations, observations_schema)\n",
    "    normalize_missing_residue_outputs(observations)\n"
    "    validate_document(observations, observations_schema)\n",
    "core missing normalization call",
)
write(core_path, text)

# Facade exports the core API without mutating it.
facade_path = SKILL / "scripts/classification_engine.py"
facade_text = '''#!/usr/bin/env python3
"""Side-effect-free facade for the component/residue classification engine."""
from __future__ import annotations

import classification_engine_core as _core

# Preserve the established module surface, including internal helpers imported
# by executable tests, without assigning into the core module.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

execute_classification = _core.execute_classification
'''
write(facade_path, facade_text)

# Entry point no longer installs parser patches.
classify_path = SKILL / "scripts/classify_structure.py"
text = read(classify_path)
text = text.replace(
    "from af3_server_sequence_reference import "
    "install_af3_server_sequence_reference\n",
    "",
    1,
)
text = text.replace("\ninstall_af3_server_sequence_reference()\n", "\n", 1)
write(classify_path, text)

# Documentation and permanent regression.
readme_path = SKILL / "scripts/README.md"
text = read(readme_path)
text = replace_once(
    text,
    "classification_engine.py\n→ runtime facade\n→ structural grouping invariant\n→ cross-stage normalization\n\nclassification_engine_core.py\n→ baseline classification implementation",
    "classification_engine.py\n→ side-effect-free runtime facade\n\nclassification_engine_core.py\n→ baseline classification implementation\n→ structural grouping invariant\n→ final observation normalization",
    "README engine boundary",
)
text = replace_once(
    text,
    "用于兼容 `dialect: alphafoldserver` 的单 job 顶层列表。",
    "由 `sequence_missing.py` 以普通函数调用处理 `dialect: alphafoldserver` 的单 job 顶层列表；禁止运行时替换 parser。",
    "README AF3 boundary",
)
write(readme_path, text)

map_path = ROOT / "00_authoring/content_maps/component_and_residue_classification_validator.yaml"
text = read(map_path)
note = (
    "  - Classification modules are side-effect-free at import time; structural "
    "grouping, missing-residue normalization and AlphaFold Server parsing are "
    "ordinary core/module calls rather than runtime monkey patches.\n"
)
if note not in text:
    text = replace_once(text, "notes:\n", "notes:\n" + note, "content map patch note")
write(map_path, text)

test_path = ROOT / "04_evals/component_and_residue_classification_validator/test_v1_2_no_runtime_monkey_patch.py"
test_text = '''from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "02_validators/component_and_residue_classification_validator"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_classification_facade_has_no_runtime_core_assignments() -> None:
    text = (SCRIPTS / "classification_engine.py").read_text(encoding="utf-8")
    assert "_core._build_chain_groups =" not in text
    assert "_core.explicit_missing_residues =" not in text
    assert "_core.sequence_based_missing_residues =" not in text
    assert "_classification_engine_original" not in text

    core = importlib.import_module("classification_engine_core")
    facade = importlib.import_module("classification_engine")
    assert facade.execute_classification is core.execute_classification


def test_af3_parser_is_not_installed_by_mutation() -> None:
    parser_text = (SCRIPTS / "af3_server_sequence_reference.py").read_text(
        encoding="utf-8"
    )
    classify_text = (SCRIPTS / "classify_structure.py").read_text(
        encoding="utf-8"
    )
    assert "install_af3_server_sequence_reference" not in parser_text
    assert "install_af3_server_sequence_reference" not in classify_text
    assert "sequence_missing.parse_af3_sequence_references =" not in parser_text
    assert "core.parse_af3_sequence_references =" not in parser_text


def test_core_owns_grouping_and_missing_output_normalization() -> None:
    core_text = (SCRIPTS / "classification_engine_core.py").read_text(
        encoding="utf-8"
    )
    sequence_text = (SCRIPTS / "sequence_missing.py").read_text(
        encoding="utf-8"
    )
    assert "grouping_polymer_class" in core_text
    assert "normalize_missing_residue_outputs(observations)" in core_text
    assert "def normalize_missing_residue_outputs(" in sequence_text
    assert "def sequence_based_missing_residues(" in sequence_text
    assert "parse_af3_server_job_request(path)" in sequence_text
'''
write(test_path, test_text)

with Path("/tmp/monkey-patch-changed-files.txt").open(
    "w",
    encoding="utf-8",
) as handle:
    for path in sorted(set(CHANGED)):
        handle.write(str(path) + "\n")

for path in CHANGED:
    if path.suffix == ".py":
        compile(read(path), str(path), "exec")

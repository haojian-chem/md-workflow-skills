from pathlib import Path
import re

skill = Path("02_validators/component_and_residue_classification_validator")

# Normalize CCD comparison.
path = skill / "scripts/ccd_reference.py"
text = path.read_text(encoding="utf-8")
marker = "def compare_ccd_heavy_atoms("
prefix = text[:text.index(marker)]
function = '''def compare_ccd_heavy_atoms(
    observed_heavy_atom_names: Iterable[str],
    template: CcdTemplate,
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    observed = set(observed_heavy_atom_names)
    expected = set(template.heavy_atom_names)
    missing = expected - observed
    unexpected = observed - expected
    mapping_candidates: list[dict[str, str]] = []
    for structure_name in sorted(unexpected):
        ccd_name = template.alternate_atom_names.get(structure_name)
        if ccd_name is not None and ccd_name in missing:
            mapping_candidates.append(
                {
                    "structure_atom_name": structure_name,
                    "ccd_atom_id": ccd_name,
                    "mapping_source": "CCD_ALTERNATE_ATOM_NAME",
                }
            )
    return sorted(missing), sorted(unexpected), mapping_candidates
'''
path.write_text(prefix + function, encoding="utf-8")

# Normalize core heavy-atom helpers and comparison loop.
path = skill / "scripts/classification_engine_core.py"
text = path.read_text(encoding="utf-8")
if "import copy\n" not in text:
    text = text.replace(
        "from collections import Counter, defaultdict\n",
        "from collections import Counter, defaultdict\nimport copy\n",
        1,
    )
empty_index = text.find("\ndef _empty_heavy_check(")
observed_index = text.find("\ndef _observed_heavy_names(")
if empty_index < 0 or observed_index < 0 or observed_index <= empty_index:
    raise SystemExit("cannot locate core heavy-atom helper region")
helpers = '''

def _heavy_status(missing: list[str], unexpected: list[str]) -> str:
    if missing and unexpected:
        return "MISSING_AND_UNEXPECTED_HEAVY_ATOMS"
    if missing:
        return "MISSING_EXPECTED_HEAVY_ATOMS"
    if unexpected:
        return "UNEXPECTED_HEAVY_ATOMS"
    return "HEAVY_ATOMS_COMPLETE"


def _heavy_findings(
    missing: list[str],
    unexpected: list[str],
    mappings: list[dict[str, str]],
) -> list[str]:
    findings: list[str] = []
    if missing:
        findings.append("MISSING_EXPECTED_HEAVY_ATOMS")
    if unexpected:
        findings.append("UNEXPECTED_HEAVY_ATOMS")
    if mappings:
        findings.append("ATOM_NAME_MAPPING_REQUIRED")
    return findings


def _completed_heavy_check(
    *,
    reference_type: str,
    reference_name: str | None,
    missing: list[str],
    unexpected: list[str],
    mappings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    mappings = mappings or []
    candidates = [
        {
            "observed_atom_name": item["structure_atom_name"],
            "reference_atom_name": item["ccd_atom_id"],
            "mapping_source": item["mapping_source"],
        }
        for item in mappings
    ]
    exact = {
        "missing_expected_atom_names": list(missing),
        "unexpected_observed_atom_names": list(unexpected),
    }
    return {
        "execution_status": "COMPLETED",
        "findings": _heavy_findings(missing, unexpected, mappings),
        "reference_type": reference_type,
        "reference_name": reference_name,
        "exact_comparison": exact,
        "atom_name_mapping_candidates": candidates,
        "mapping_resolution_status": (
            "PENDING_CONFIRMATION" if mappings else "NOT_APPLICABLE"
        ),
        "effective_comparison": None if mappings else copy.deepcopy(exact),
        "reason": None,
        "status": (
            "ATOM_NAME_MAPPING_REQUIRED"
            if mappings
            else _heavy_status(missing, unexpected)
        ),
        "missing_atoms": list(missing),
        "unexpected_atoms": list(unexpected),
    }


def _empty_heavy_check(status: str, reason: str | None = None) -> dict[str, Any]:
    execution_status = {
        "REFERENCE_TEMPLATE_UNAVAILABLE": "REFERENCE_TEMPLATE_UNAVAILABLE",
        "NOT_APPLICABLE": "NOT_APPLICABLE",
    }.get(status, "NOT_PERFORMED")
    return {
        "execution_status": execution_status,
        "findings": [],
        "reference_type": None,
        "reference_name": None,
        "exact_comparison": None,
        "atom_name_mapping_candidates": [],
        "mapping_resolution_status": "NOT_APPLICABLE",
        "effective_comparison": None,
        "reason": reason,
        "status": status,
        "missing_atoms": [],
        "unexpected_atoms": [],
    }


def _heavy_check_has_issue(check: dict[str, Any]) -> bool:
    return bool(check.get("findings")) or (
        check.get("execution_status") == "REFERENCE_TEMPLATE_UNAVAILABLE"
    )


def _observed_heavy_names('''
text = text[:empty_index] + helpers + text[observed_index + len("\ndef _observed_heavy_names("):]

loop_start_marker = '''    for analysis in analyses:
        value = analysis.classification
        if analysis.conformation["status"] == "MULTIPLE_CONFORMATIONS":
'''
loop_start = text.find(loop_start_marker)
loop_end = text.find("\n    chain_groups, assignment = _build_chain_groups(analyses)", loop_start)
if loop_start < 0 or loop_end < 0:
    raise SystemExit("cannot locate core heavy-atom comparison loop")
loop = '''    for analysis in analyses:
        value = analysis.classification
        if analysis.conformation["status"] == "MULTIPLE_CONFORMATIONS":
            analysis.heavy_atom_check = _empty_heavy_check(
                "NOT_PERFORMED",
                "MULTIPLE_CONFORMATIONS_PRESENT",
            )
            continue
        if value.resolution_status != "RESOLVED":
            analysis.heavy_atom_check = _empty_heavy_check(
                "NOT_PERFORMED",
                "CLASSIFICATION_UNRESOLVED",
            )
            continue
        if value.topology_class in {"SOLVENT_COMPONENT", "ION_COMPONENT"}:
            analysis.heavy_atom_check = _empty_heavy_check(
                "NOT_APPLICABLE",
                "SOLVENT_OR_ION_TEMPLATE_CHECK_NOT_REQUIRED",
            )
            continue
        observed_heavy = _observed_heavy_names(analysis.residue)
        if (
            mode == "FORCE_FIELD_ANALYSIS"
            and value.topology_class == "STANDARD_RESIDUE"
        ):
            template = selected_rtp.get(analysis.residue.residue_key)
            if template is None:
                analysis.heavy_atom_check = {
                    **_empty_heavy_check(
                        "REFERENCE_TEMPLATE_UNAVAILABLE",
                        "RTP_TEMPLATE_NOT_RESOLVED",
                    ),
                    "reference_type": "RTP",
                    "reference_name": value.rtp_template_name,
                }
                continue
            missing, unexpected = compare_heavy_atom_names(
                observed_heavy,
                template,
            )
            analysis.heavy_atom_check = _completed_heavy_check(
                reference_type="RTP",
                reference_name=template.residue_name,
                missing=missing,
                unexpected=unexpected,
            )
            continue
        component_id = value.ccd_id
        template = ccd_templates.get(component_id or "")
        if component_id is None or template is None:
            analysis.heavy_atom_check = {
                **_empty_heavy_check(
                    "REFERENCE_TEMPLATE_UNAVAILABLE",
                    "CCD_TEMPLATE_UNAVAILABLE",
                ),
                "reference_type": "CCD",
                "reference_name": component_id,
            }
            continue
        missing, unexpected, mappings = compare_ccd_heavy_atoms(
            observed_heavy,
            template,
        )
        analysis.heavy_atom_check = _completed_heavy_check(
            reference_type="CCD",
            reference_name=component_id,
            missing=missing,
            unexpected=unexpected,
            mappings=mappings,
        )
        if mappings:
            unresolved.append(
                {
                    "issue_type": "ATOM_NAME_MAPPING_REQUIRED",
                    "subject": {
                        **_identity_fields(analysis.residue),
                        "exact_comparison": copy.deepcopy(
                            analysis.heavy_atom_check["exact_comparison"]
                        ),
                        "atom_name_mapping_candidates": copy.deepcopy(
                            analysis.heavy_atom_check[
                                "atom_name_mapping_candidates"
                            ]
                        ),
                    },
                    "evidence": [
                        "CCD alternate atom name provides a candidate mapping; "
                        "raw exact-name differences are retained"
                    ],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
'''
text = text[:loop_start] + loop + text[loop_end:]
path.write_text(text, encoding="utf-8")

# Normalize final builder decision helpers.
path = skill / "scripts/build_classification_result.py"
text = path.read_text(encoding="utf-8")
pattern = re.compile(r"\n\s*def _heavy_atom_decision_map\(.*?\ndef _record_index\(", re.S)
replacement = '''

def _heavy_atom_decision_map(
    resolved_requests: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[tuple[str | None, str, str | None, str], dict[str, Any]]:
    output: dict[tuple[str | None, str, str | None, str], dict[str, Any]] = {}
    for request, decision in resolved_requests:
        if request["request_type"] != "ATOM_NAME_MAPPING_REQUIRED":
            continue
        subject = request["subject"]
        source_resid = subject.get("source_resid")
        if not isinstance(source_resid, dict):
            raise ClassificationToolError(
                "atom-name mapping subject lacks source_resid"
            )
        key = (
            subject.get("source_chain_id"),
            str(source_resid["number"]),
            source_resid.get("insertion_code"),
            subject["residue_name"],
        )
        output[key] = copy.deepcopy(decision)
    return output


def _apply_heavy_atom_decision(
    check: dict[str, Any],
    decision: dict[str, Any] | None,
) -> dict[str, Any]:
    output = copy.deepcopy(check)
    if decision is None:
        return output
    action = decision["decision"]
    if action == "REJECT_ATOM_NAME_MAPPING":
        output["mapping_resolution_status"] = "REJECTED"
        output["effective_comparison"] = None
        return output
    if action != "APPLY_ATOM_NAME_MAPPING":
        return output
    exact = output.get("exact_comparison")
    if not isinstance(exact, dict):
        raise ClassificationToolError(
            "cannot apply atom-name mapping without exact comparison"
        )
    missing = set(exact["missing_expected_atom_names"])
    unexpected = set(exact["unexpected_observed_atom_names"])
    for candidate in output.get("atom_name_mapping_candidates", []):
        missing.discard(candidate["reference_atom_name"])
        unexpected.discard(candidate["observed_atom_name"])
    output["mapping_resolution_status"] = "APPLIED"
    output["effective_comparison"] = {
        "missing_expected_atom_names": sorted(missing),
        "unexpected_observed_atom_names": sorted(unexpected),
    }
    return output


def _record_index('''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f"cannot normalize heavy atom decision helpers: {count}")
path.write_text(text, encoding="utf-8")

# Normalize scientific test PDB string.
path = Path(
    "04_evals/component_and_residue_classification_validator/"
    "test_v1_2_scientific_contract_repairs.py"
)
text = path.read_text(encoding="utf-8")
replacement_text = (
    '    structure.write_text(\n'
    '        "HETATM    1  C01 LIG A   1       0.000   0.000   0.000  1.00 20.00           C\\n"\n'
    '        "HETATM    2  N1  LIG A   1       1.000   0.000   0.000  1.00 20.00           N\\n"\n'
    '        "END\\n",\n'
    '        encoding="utf-8",\n'
    '    )'
)
text, count = re.subn(
    r'    structure\.write_text\(\n.*?        encoding="utf-8",\n    \)',
    lambda _match: replacement_text,
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"cannot normalize scientific test PDB string: {count}")
path.write_text(text, encoding="utf-8")

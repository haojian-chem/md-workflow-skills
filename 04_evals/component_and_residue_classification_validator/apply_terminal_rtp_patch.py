from __future__ import annotations

import re
from pathlib import Path

ENGINE = Path("02_validators/component_and_residue_classification_validator/scripts/classification_engine.py")
text = ENGINE.read_text(encoding="utf-8")
if "known_terminal_names" in text:
    raise SystemExit(0)
pattern = re.compile(
    r"def _rtp_candidates_for_residue\(.*?\n\n\ndef _classify_residue",
    re.DOTALL,
)
replacement = '''def _rtp_candidates_for_residue(
    residue: ResidueRecord,
    rtp_index: dict[str, list[RtpTemplate]],
    roles: dict[tuple, set[str]],
    terminal_mappings: dict[tuple[str, str], list[str]],
    unresolved: list[dict[str, Any]],
) -> tuple[str | None, list[RtpTemplate]]:
    terminal_roles = sorted(roles.get(residue.residue_key, set()))
    known_terminal_names = {
        target
        for targets in terminal_mappings.values()
        for target in targets
    }
    if terminal_roles:
        mapped_targets: list[str] = []
        for role in terminal_roles:
            mapped_targets.extend(
                terminal_mappings.get((residue.residue_name, role), [])
            )
        mapped_targets = sorted(set(mapped_targets))
        if len(mapped_targets) > 1:
            unresolved.append(
                {
                    "issue_type": "TERMINAL_RTP_TEMPLATE_AMBIGUOUS",
                    "subject": {
                        "source_chain_id": residue.source_chain_id,
                        "source_resid": {
                            "number": residue.source_resid_number,
                            "insertion_code": residue.insertion_code,
                        },
                        "residue_name": residue.residue_name,
                        "terminal_roles": terminal_roles,
                        "candidate_rtp_names": mapped_targets,
                    },
                    "evidence": [
                        "multiple explicit terminal template mappings"
                    ],
                    "resolution_status": "PENDING_CONFIRMATION",
                }
            )
            return None, []
        if len(mapped_targets) == 1:
            target = mapped_targets[0]
            return target, rtp_index.get(target, [])
        if residue.residue_name in known_terminal_names:
            return residue.residue_name, rtp_index.get(
                residue.residue_name, []
            )
        return None, []

    exact = rtp_index.get(residue.residue_name, [])
    if exact:
        return residue.residue_name, exact
    return None, []


def _classify_residue'''
updated, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit("failed to locate _rtp_candidates_for_residue")
ENGINE.write_text(updated, encoding="utf-8")

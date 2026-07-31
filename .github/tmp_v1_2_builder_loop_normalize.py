from pathlib import Path

path = Path(
    "02_validators/component_and_residue_classification_validator/"
    "scripts/build_classification_result.py"
)
text = path.read_text(encoding="utf-8")
start_marker = "    for request in raw_requests:\n"
end_marker = "\n    for index, request in enumerate(unresolved_requests, start=1):"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("cannot locate final-builder decision loop")
replacement = '''    for request in raw_requests:
        decision = decisions.get(_request_fingerprint(request))
        if decision is None:
            unresolved_requests.append(request)
            continue
        if request["request_type"] in RELATION_REQUEST_TYPES:
            confirmed, rejected = _decision_relation(request, decision)
            if confirmed is not None:
                confirmed_relations.append(confirmed)
            if rejected is not None:
                rejected_relations.append(rejected)
            if confirmed is None and rejected is None:
                unresolved_requests.append(request)
            else:
                resolved_requests.append((request, decision))
            continue
        if (
            request["request_type"] in CLASSIFICATION_REQUEST_TYPES
            and decision["decision"] == "SET_CLASSIFICATION"
        ):
            resolved_requests.append((request, decision))
            continue
        if (
            request["request_type"] == "ATOM_NAME_MAPPING_REQUIRED"
            and decision["decision"]
            in {"APPLY_ATOM_NAME_MAPPING", "REJECT_ATOM_NAME_MAPPING"}
        ):
            resolved_requests.append((request, decision))
            continue
        if decision["decision"] == "EXCLUDE_FROM_REPORTED_MISSING_RESIDUES":
            resolved_requests.append((request, decision))
            continue
        unresolved_requests.append(request)
'''
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

from pathlib import Path

path = Path("04_evals/chain_and_component_selection/test_selection_manager_closure.py")
text = path.read_text(encoding="utf-8")
old = '''    candidate_root = project_root / ".manager_candidates/selection_closure"\n    artifact_candidate = candidate_root / "artifact.yaml"\n'''
new = '''    candidate_root = project_root / ".manager_candidates/selection_closure"\n    candidate_root.mkdir(parents=True, exist_ok=True)\n    artifact_candidate = candidate_root / "artifact.yaml"\n'''
if text.count(old) != 1:
    raise SystemExit(f"expected one marker, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

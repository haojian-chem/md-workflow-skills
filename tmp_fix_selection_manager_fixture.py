from pathlib import Path

path = Path("04_evals/chain_and_component_selection/test_selection_manager_closure.py")
text = path.read_text(encoding="utf-8")
old = '''    events_logical_path = project_root / "00_project_records/events/project_events.jsonl"\n\n    write_yaml(task_path, task_document(project_root, work_directory, case, result_logical_path))\n'''
new = '''    events_logical_path = project_root / "00_project_records/events/project_events.jsonl"\n\n    task_directory.mkdir(parents=True, exist_ok=True)\n    artifact_directory.mkdir(parents=True, exist_ok=True)\n    state_logical_path.parent.mkdir(parents=True, exist_ok=True)\n    write_yaml(task_path, task_document(project_root, work_directory, case, result_logical_path))\n'''
if text.count(old) != 1:
    raise SystemExit(f"expected one marker, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

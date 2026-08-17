import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = Path(__file__).resolve().parent
TOOL = HERE.parents[1] / "05_tools/runtime_projection_compiler/compile_runtime.py"


def git_blob_sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._write("AGENTS.md", "runtime rules\n")
        self._write("00_manager/manager.md", "manager authority\n")
        self._write("01_workflows/wf/SKILL.md", "workflow authority\n")
        self._write("03_contracts/project_state.schema.yaml", "type: object\n")
        self._write("03_contracts/workstream_state.schema.yaml", "type: object\n")
        self._write("05_tools/tool_registry.yaml", "schema_version: 1\n")
        self._write(
            "00_manager/stage_registry.yaml",
            yaml.safe_dump(
                {"stage_order": [{"stage_id": "structure_preparation", "workflow_name": "wf", "project_directory": "01_structure_preparation", "connection_status": "connected"}]},
                sort_keys=False,
            ),
        )
        manager_guard = git_blob_sha((self.root / "00_manager/manager.md").read_bytes())
        workflow_guard = git_blob_sha((self.root / "01_workflows/wf/SKILL.md").read_bytes())
        self._write(
            "00_manager/manager_runtime_source.yaml",
            yaml.safe_dump({
                "schema_version": 1,
                "source_guards": [{"path": "00_manager/manager.md", "expected_git_blob_sha": manager_guard}],
                "runtime_spec": {"schema_version": 1, "spec_status": "generated_active", "manager_name": "md_workflow_manager", "entry_states": ["NEW", "RESUMABLE", "NEEDS_RECOVERY"]},
            }, sort_keys=False),
        )
        self._write(
            "01_workflows/wf/runtime_source.yaml",
            yaml.safe_dump({
                "schema_version": 1,
                "source_guards": [{"path": "01_workflows/wf/SKILL.md", "expected_git_blob_sha": workflow_guard}],
                "runtime_spec": {"schema_version": 1, "spec_status": "generated_active", "workflow_name": "wf", "stage_id": "structure_preparation", "nodes": [{"node_id": "1.1", "normal_next": "workflow_exit"}]},
            }, sort_keys=False),
        )
        config = {
            "schema_version": 1,
            "branch_label": "test",
            "runtime_root": "runtime",
            "manifest_output": "runtime_manifest.yaml",
            "manager": {"source": "00_manager/manager_runtime_source.yaml", "output": "manager_runtime_spec.yaml"},
            "workflows": [{"workflow_name": "wf", "source": "01_workflows/wf/runtime_source.yaml", "output": "workflows/wf.runtime.yaml"}],
            "contracts": {
                "output": "task_contracts/index.yaml",
                "include": {"project_state": "03_contracts/project_state.schema.yaml", "workstream_state": "03_contracts/workstream_state.schema.yaml"},
                "consumer_policy": {"schema_validation": "registered_deterministic_tool"},
                "notes": ["authority remains in contracts"],
            },
            "stage_registry": "00_manager/stage_registry.yaml",
            "tool_registry": "05_tools/tool_registry.yaml",
            "provenance_sources": ["AGENTS.md", "00_manager/manager.md", "01_workflows/wf/SKILL.md"],
            "manifest": {
                "purpose": "test projection",
                "authority": {"runtime_is_source_of_truth": False},
                "loading_policy": {"real_md_runtime_default": {"load": ["runtime/runtime_manifest.yaml"]}},
                "execution_backends": {"AGENT_TASK": {"status": "enabled"}},
                "foreground_agent_limit": 1,
                "runtime_guards": ["no_authoring_read"],
            },
        }
        self._write("00_authoring/runtime_projection_config.yaml", yaml.safe_dump(config, sort_keys=False))

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_tool(self, mode):
        proc = subprocess.run([sys.executable, str(TOOL), "--skill-root", str(self.root), "--mode", mode], text=True, capture_output=True)
        return proc.returncode, json.loads(proc.stdout)

    def test_build_then_check(self):
        code, result = self.run_tool("BUILD")
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue((self.root / "runtime/runtime_manifest.yaml").is_file())
        manifest = yaml.safe_load((self.root / "runtime/runtime_manifest.yaml").read_text())
        self.assertEqual(manifest["runtime_entry"]["manager_spec"], "runtime/manager_runtime_spec.yaml")
        self.assertEqual(manifest["runtime_entry"]["workflow_specs"]["wf"], "runtime/workflows/wf.runtime.yaml")
        self.assertEqual(manifest["stage_registry_projection"][0]["runtime_spec"], "runtime/workflows/wf.runtime.yaml")
        code, result = self.run_tool("CHECK")
        self.assertEqual(code, 0, result)
        self.assertEqual(result["drift"], [])

    def test_runtime_drift_detected(self):
        self.run_tool("BUILD")
        self._write("runtime/manager_runtime_spec.yaml", "broken: true\n")
        code, result = self.run_tool("CHECK")
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "DRIFT")
        self.assertTrue(any(x["path"].endswith("manager_runtime_spec.yaml") for x in result["drift"]))

    def test_source_guard_blocks_build(self):
        self._write("00_manager/manager.md", "manager changed\n")
        code, result = self.run_tool("BUILD")
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["guard_errors"][0]["reason"], "SOURCE_GUARD_MISMATCH")
        self.assertFalse((self.root / "runtime/runtime_manifest.yaml").exists())

    def test_missing_source_is_tool_error(self):
        (self.root / "03_contracts/project_state.schema.yaml").unlink()
        code, result = self.run_tool("CHECK")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ERROR")

    def test_output_escape_rejected(self):
        cfg_path = self.root / "00_authoring/runtime_projection_config.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["manager"]["output"] = "../escape.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        code, result = self.run_tool("BUILD")
        self.assertEqual(code, 2)
        self.assertIn("output path must be a safe relative path", result["errors"][0])
        self.assertFalse((self.root / "escape.yaml").exists())

    def test_idempotent_build(self):
        code, first = self.run_tool("BUILD")
        self.assertEqual(code, 0)
        code, second = self.run_tool("BUILD")
        self.assertEqual(code, 0)
        self.assertEqual(second["changed"], [])


if __name__ == "__main__":
    unittest.main()

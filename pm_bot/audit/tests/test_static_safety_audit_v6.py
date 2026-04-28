import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "audit" / "static_safety_audit_v6.py"
EXPECTED = ROOT / "pm_bot" / "audit" / "expected_static_safety_audit.v6.json"


def _run():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_audit_v6", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StaticSafetyAuditV6Tests(unittest.TestCase):
    def test_output_matches_expected(self):
        self.assertEqual(json.loads(_run().stdout), json.loads(EXPECTED.read_text(encoding="utf-8")))

    def test_audit_passes(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["audit_passed"])
        self.assertEqual(payload["blocking_findings"], [])

    def test_unexpected_boundary_runtime_source_is_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            risky = root / "pm_bot" / "boundary" / "live_fetcher.py"
            risky.parent.mkdir(parents=True, exist_ok=True)
            risky.write_text("def fetch_live_snapshot():\n    return {}\n", encoding="utf-8")
            report = module.build_static_audit_report(root)
        self.assertFalse(report["audit_passed"])
        self.assertEqual(report["blocking_findings"][0]["token"], "unexpected_boundary_runtime_source")

    def test_repository_scan_covers_batch_007_paths(self):
        payload = json.loads(_run().stdout)
        scanned = set(payload["scanned_files"])
        self.assertIn("pm_bot/boundary/validate_live_boundary_contracts.py", scanned)
        self.assertIn("pm_bot/contracts/live_readonly_fetcher_contract.v1.json", scanned)
        self.assertIn("docs/PM_BOT_LIVE_READONLY_BOUNDARY_V1.md", scanned)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"ast", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

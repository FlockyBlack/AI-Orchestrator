import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "audit" / "static_safety_audit_v5.py"
EXPECTED = ROOT / "pm_bot" / "audit" / "expected_static_safety_audit.v5.json"


def _run():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_audit_v5", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StaticSafetyAuditV5Tests(unittest.TestCase):
    def test_output_matches_expected(self):
        self.assertEqual(json.loads(_run().stdout), json.loads(EXPECTED.read_text(encoding="utf-8")))

    def test_audit_passes(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["audit_passed"])
        self.assertEqual(payload["blocking_findings"], [])

    def test_executable_operator_file_is_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            risky = root / "pm_bot" / "operator" / "risky_probe.py"
            risky.parent.mkdir(parents=True, exist_ok=True)
            risky.write_text("import requests\n", encoding="utf-8")
            report = module.build_static_audit_report(root)
        self.assertFalse(report["audit_passed"])
        self.assertEqual(report["blocking_findings"][0]["file"], "pm_bot/operator/risky_probe.py")
        self.assertEqual(report["blocking_findings"][0]["token"], "requests")

    def test_repository_scan_covers_batch_006_paths(self):
        payload = json.loads(_run().stdout)
        scanned = set(payload["scanned_files"])
        self.assertIn("pm_bot/operator/build_operator_review_bundle.py", scanned)
        self.assertIn("pm_bot/export/build_review_export_package.py", scanned)
        self.assertIn("pm_bot/demo/run_operator_review_demo.py", scanned)

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

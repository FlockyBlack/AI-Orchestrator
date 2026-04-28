import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "audit" / "static_safety_audit_v2.py"
EXPECTED = ROOT / "pm_bot" / "audit" / "expected_static_safety_audit.v2.json"


def _run_runner():
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_audit_v2", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StaticSafetyAuditV2Tests(unittest.TestCase):
    def test_output_matches_expected(self):
        payload = json.loads(_run_runner().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_audit_passes_and_keeps_runtime_blocked(self):
        payload = json.loads(_run_runner().stdout)
        self.assertTrue(payload["audit_passed"])
        self.assertEqual(payload["blocking_findings"], [])
        self.assertTrue(payload["checks"]["no_network_or_api"])
        self.assertTrue(payload["checks"]["no_live_polymarket_api"])
        self.assertTrue(payload["checks"]["no_runtime_wiring"])

    def test_deterministic_output(self):
        first = json.loads(_run_runner().stdout)
        second = json.loads(_run_runner().stdout)
        self.assertEqual(first, second)

    def test_executable_batch_004_style_quality_file_is_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            risky = root / "pm_bot" / "quality" / "risky_probe.py"
            risky.parent.mkdir(parents=True, exist_ok=True)
            risky.write_text("import requests\n", encoding="utf-8")
            report = module.build_static_audit_report(root)
        self.assertFalse(report["audit_passed"])
        self.assertEqual(report["blocking_findings"][0]["file"], "pm_bot/quality/risky_probe.py")
        self.assertEqual(report["blocking_findings"][0]["token"], "requests")

    def test_docs_mentions_remain_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_path = root / "docs" / "PM_BOT_FAKE.md"
            docs_path.parent.mkdir(parents=True, exist_ok=True)
            docs_path.write_text("Blocked future work includes run_codex and private_key handling.\n", encoding="utf-8")
            report = module.build_static_audit_report(root)
        self.assertTrue(report["audit_passed"])
        self.assertEqual(report["blocking_findings"], [])
        self.assertEqual({item["reason"] for item in report["non_blocking_mentions"]}, {"documentation_context"})

    def test_repository_scan_covers_batch_004_paths(self):
        payload = json.loads(_run_runner().stdout)
        scanned = set(payload["scanned_files"])
        self.assertIn("pm_bot/quality/research_quality_support.py", scanned)
        self.assertIn("pm_bot/quality/confidence_breakdown.py", scanned)
        self.assertIn("pm_bot/explainability/signal_explainer.py", scanned)
        self.assertIn("pm_bot/demo/run_research_quality_demo.py", scanned)
        self.assertIn("pm_bot/reports/candidate_comparison_report.py", scanned)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"ast", "json", "sys", "pathlib"})
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "socket", "dispatcher", "run_codex", "runtime"}))


if __name__ == "__main__":
    unittest.main()

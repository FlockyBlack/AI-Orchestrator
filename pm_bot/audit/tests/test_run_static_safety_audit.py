import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "pm_bot" / "audit" / "run_static_safety_audit.py"
FIXTURE_DIR = ROOT / "pm_bot" / "audit" / "tests" / "fixtures"
PM_BOT_DIR = ROOT / "pm_bot"


def _frag(*parts):
    return "".join(parts)


def _run_audit(path: Path, *extra_args):
    return subprocess.run(
        [sys.executable, str(AUDIT), str(path), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class RunStaticSafetyAuditTests(unittest.TestCase):
    def test_fixture_focus_finds_synthetic_unsafe_sample(self):
        payload = json.loads(_run_audit(FIXTURE_DIR).stdout)
        self.assertFalse(payload["audit_passed"])
        self.assertEqual(len(payload["blocking_findings"]), 1)
        self.assertEqual(payload["blocking_findings"][0]["token"], _frag("so", "cket"))
        self.assertEqual(payload["blocking_findings"][0]["reason"], "synthetic_unsafe_fixture")

    def test_exclude_tests_mode_skips_test_fixture_tree(self):
        payload = json.loads(_run_audit(FIXTURE_DIR, "--exclude-tests").stdout)
        self.assertEqual(payload["scanned_files"], [])
        self.assertEqual(payload["blocking_findings"], [])
        self.assertEqual(payload["non_blocking_mentions"], [])
        self.assertTrue(payload["audit_passed"])

    def test_current_pm_bot_tree_passes_with_non_blocking_mentions(self):
        payload = json.loads(_run_audit(PM_BOT_DIR).stdout)
        self.assertTrue(payload["audit_passed"])
        self.assertEqual(payload["blocking_findings"], [])
        self.assertGreater(len(payload["non_blocking_mentions"]), 0)
        self.assertFalse(payload["runtime_wiring_added"])
        self.assertFalse(payload["network_api_wallet_trading_detected"])

    def test_legacy_runner_uses_exact_newer_artifact_ignores_not_blanket_batch_004_prefixes(self):
        source = AUDIT.read_text(encoding="utf-8")
        self.assertNotIn("LEGACY_IGNORE_PREFIXES", source)
        self.assertIn("pm_bot/demo/run_research_quality_demo.py", source)
        payload = json.loads(_run_audit(PM_BOT_DIR).stdout)
        self.assertNotIn(str(ROOT / "pm_bot" / "quality" / "research_quality_support.py"), payload["scanned_files"])

    def test_repeat_runs_match(self):
        first = json.loads(_run_audit(PM_BOT_DIR).stdout)
        second = json.loads(_run_audit(PM_BOT_DIR).stdout)
        self.assertEqual(first, second)

    def test_runtime_script_has_no_network_imports(self):
        source = AUDIT.read_text(encoding="utf-8").lower()
        self.assertNotIn(_frag("import ", "re", "quests"), source)
        self.assertNotIn(_frag("import ", "so", "cket"), source)
        self.assertNotIn("subprocess", source)

    def test_standard_library_only(self):
        tree = ast.parse(AUDIT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"ast", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

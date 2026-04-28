import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DISCOVER = ROOT / "pm_bot" / "hedges" / "discover_fixture_relationships.py"
FIXTURE = ROOT / "pm_bot" / "hedges" / "fixture_related_markets.v1.json"
EXPECTED = ROOT / "pm_bot" / "hedges" / "expected_relationship_report.v1.json"


def _run_discovery():
    return subprocess.run(
        [sys.executable, str(DISCOVER), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class DiscoverFixtureRelationshipsTests(unittest.TestCase):
    def test_expected_relationships_detected(self):
        result = _run_discovery()
        payload = json.loads(result.stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_research_only_flags_are_true(self):
        payload = json.loads(_run_discovery().stdout)
        for item in payload["relationships"]:
            self.assertTrue(item["research_only"])
            self.assertFalse(item["execution_allowed"])
            self.assertFalse(item["trading_allowed"])

    def test_no_live_api_network_wallet_or_trading_behavior(self):
        source = DISCOVER.read_text(encoding="utf-8").lower()
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("wallet", source)
        self.assertNotIn("private_key", source)
        self.assertNotIn("submit_order", source)

    def test_deterministic_output(self):
        first = json.loads(_run_discovery().stdout)
        second = json.loads(_run_discovery().stdout)
        self.assertEqual(first, second)

    def test_no_active_task_or_runtime_imports(self):
        source = DISCOVER.read_text(encoding="utf-8")
        self.assertNotIn("active_tasks", source)
        self.assertNotIn("dispatcher", source)
        self.assertNotIn("run_codex", source)
        self.assertNotIn("runtime_loop", source)

    def test_standard_library_only(self):
        tree = ast.parse(DISCOVER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

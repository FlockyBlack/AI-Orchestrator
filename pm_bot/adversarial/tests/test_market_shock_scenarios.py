import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "pm_bot" / "adversarial" / "market_shock_scenarios.v1.json"
RUNNER = ROOT / "pm_bot" / "adversarial" / "run_market_shock_scenarios.py"
EXPECTED_JSON = ROOT / "pm_bot" / "adversarial" / "expected_market_shock_report.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "adversarial" / "expected_market_shock_report.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class MarketShockScenarioTests(unittest.TestCase):
    def test_fixture_contains_required_shocks(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        shock_types = {scenario["shock_type"] for scenario in payload["scenarios"]}
        self.assertEqual(
            shock_types,
            {
                "liquidity_collapse",
                "spread_explosion",
                "data_staleness_spike",
                "price_gap",
                "resolved_status_flip",
                "confidence_downgrade",
                "category_exposure_spike",
                "correlation_cluster_warning",
            },
        )

    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib"})


if __name__ == "__main__":
    unittest.main()

import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "boundary" / "validate_live_boundary_contracts.py"


def _run():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_boundary_validator", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateLiveBoundaryContractsTests(unittest.TestCase):
    def test_script_succeeds(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["validation_passed"])

    def test_invalid_raw_fixture_is_rejected_and_quarantined(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["checks"]["invalid_raw_fixture_rejected"])
        self.assertTrue(payload["checks"]["invalid_raw_fixture_quarantined"])
        self.assertEqual(payload["generated_quarantine_record"]["quarantine_reason"], "malformed_snapshot")

    def test_normalized_fixture_requires_valid_status_for_replay(self):
        module = _load_module()
        invalid_normalized = {
            "normalized_market_id": "normalized-bad-001",
            "title": "Bad replay eligibility fixture",
            "category": "governance",
            "status": "open",
            "outcomes": ["Yes", "No"],
            "yes_price": 0.51,
            "no_price": 0.49,
            "liquidity": 1000.0,
            "spread": 0.01,
            "volume": 500.0,
            "data_freshness_seconds": 30,
            "validation_status": "quarantined",
            "paper_replay_eligible": True,
        }
        result = module.validate_normalized_snapshot_rules(invalid_normalized)
        self.assertFalse(result["valid"])
        self.assertIn("paper_replay_eligible_requires_validation_status_valid", result["errors"])

    def test_malformed_fixture_is_detected(self):
        module = _load_module()
        raw_schema = module.load_json(ROOT / "pm_bot" / "contracts" / "raw_market_snapshot.schema.v1.json")
        invalid_raw = module.load_json(ROOT / "pm_bot" / "fixtures" / "live_boundary" / "raw_snapshot.invalid.example.v1.json")
        result = module.validate_payload_against_schema(raw_schema, invalid_raw)
        self.assertFalse(result["valid"])
        self.assertIn("missing_required_field:prices", result["errors"])

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

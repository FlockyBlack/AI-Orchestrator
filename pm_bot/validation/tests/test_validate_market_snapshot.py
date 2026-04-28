import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "pm_bot" / "validation" / "validate_market_snapshot.py"
VALID_FIXTURE = ROOT / "pm_bot" / "fixtures" / "market_snapshot_stub.v1.json"
INVALID_FIXTURE = ROOT / "pm_bot" / "fixtures" / "invalid_market_snapshot_missing_outcomes.v1.json"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class MarketSnapshotValidatorTests(unittest.TestCase):
    def test_valid_fixture_passes(self):
        result = _run_validator(VALID_FIXTURE)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["outcome_count"], 2)

    def test_invalid_missing_outcomes_fails(self):
        result = _run_validator(INVALID_FIXTURE)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("missing:outcomes", payload["errors"])

    def test_validator_is_offline_only(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_no_network_api_wallet_or_trading_strings_are_required(self):
        fixture = json.loads(VALID_FIXTURE.read_text(encoding="utf-8"))
        self.assertNotIn("network", fixture)
        self.assertNotIn("api_url", fixture)
        self.assertNotIn("wallet_address", fixture)
        self.assertNotIn("private_key", fixture)
        self.assertNotIn("order_payload", fixture)

    def test_standard_library_only(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scoring" / "adapt_live_shaped_crypto_snapshot.py"
EXPECTED_JSON = ROOT / "pm_bot" / "scoring" / "expected_live_shaped_crypto_snapshot_adapter.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "scoring" / "expected_live_shaped_crypto_snapshot_adapter.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class AdaptLiveShapedCryptoSnapshotTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_adapter_summary_and_chain_check(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["adapter_summary"]["snapshot_markets"], 10)
        self.assertEqual(payload["adapter_summary"]["adapted_raw_markets"], 3)
        self.assertEqual(payload["adapter_summary"]["adapter_rejections"], 7)
        self.assertTrue(payload["adapter_summary"]["intake_chain_check_passed"])
        self.assertTrue(payload["intake_chain_check"]["passed"])
        self.assertEqual(payload["intake_chain_check"]["markets_scored"], 3)

    def test_required_rejection_codes_are_emitted(self):
        payload = json.loads(_run_json().stdout)
        reason_codes = {row["reason_code"] for row in payload["adapter_rejections"]}
        self.assertEqual(
            reason_codes,
            {
                "missing_question",
                "missing_market_id",
                "missing_price",
                "missing_liquidity",
                "missing_expiry",
                "unsupported_asset",
                "ambiguous_side",
            },
        )

    def test_adapted_raw_markets_preserve_chain_fields(self):
        payload = json.loads(_run_json().stdout)
        required = {
            "market_id",
            "question",
            "asset",
            "side_candidate",
            "target_price_candidate",
            "expiry",
            "market_yes_price",
            "liquidity_usd",
            "spread",
            "current_price",
            "thirty_day_change_pct",
            "volatility_30d_pct",
        }
        for row in payload["adapted_raw_fixture"]["raw_markets"]:
            self.assertLessEqual(required, set(row))

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        for key in (
            "live_fetcher_implemented",
            "network_used",
            "api_used",
            "credentials_used",
            "wallet_used",
            "real_order_created",
            "trading_allowed",
        ):
            self.assertFalse(payload[key])

    def test_no_runtime_or_network_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            _frag("dispatch", "er"),
            _frag("run", "_", "codex"),
            _frag("private", "_", "key"),
            _frag("submit", "_", "order"),
            _frag("execute", "_", "trade"),
        ]
        for term in forbidden:
            self.assertNotIn(term, source)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "re", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

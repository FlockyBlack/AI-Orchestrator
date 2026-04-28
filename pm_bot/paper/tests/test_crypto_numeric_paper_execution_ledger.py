import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "pm_bot" / "paper" / "crypto_numeric_paper_execution_ledger.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_paper_execution_ledger.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_paper_execution_ledger.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(LEDGER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(LEDGER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class CryptoNumericPaperExecutionLedgerTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_ledger_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["ledger_summary"],
            {
                "paper_orders_seen": 1,
                "paper_orders_submitted": 1,
                "paper_orders_filled": 1,
                "paper_orders_not_filled": 0,
                "paper_positions_opened": 1,
                "paper_positions_closed_or_settled": 1,
                "no_action_entries": 3,
                "total_paper_notional": 100.0,
                "total_max_loss": 100.0,
                "paper_pnl": 72.41,
            },
        )

    def test_events_and_positions_capture_lifecycle(self):
        payload = json.loads(_run_json().stdout)
        event_types = [event["event_type"] for event in payload["events"]]
        self.assertEqual(event_types.count("paper_order_submitted"), 1)
        self.assertEqual(event_types.count("paper_order_filled"), 1)
        self.assertEqual(event_types.count("paper_order_not_filled"), 0)
        self.assertEqual(event_types.count("no_action_preserved"), 3)
        position = payload["paper_positions"][0]
        self.assertEqual(position["status"], "settled")
        self.assertEqual(position["settlement_outcome"], "yes")
        self.assertEqual(position["paper_pnl"], 72.41)

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        for key in ("offline_only", "paper_only"):
            self.assertTrue(payload[key])
        for key in ("execution_allowed", "trading_allowed", "real_order_created", "wallet_used", "api_used", "network_used"):
            self.assertFalse(payload[key])
        for event in payload["events"]:
            self.assertTrue(event["offline_only"])
            self.assertTrue(event["paper_only"])
            self.assertFalse(event["execution_allowed"])
            self.assertFalse(event["trading_allowed"])
            self.assertFalse(event["real_order_created"])
            self.assertFalse(event["wallet_used"])
            self.assertFalse(event["api_used"])
            self.assertFalse(event["network_used"])

    def test_no_runtime_or_network_behavior(self):
        source = LEDGER.read_text(encoding="utf-8").lower()
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
        tree = ast.parse(LEDGER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

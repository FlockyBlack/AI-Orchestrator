import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_replay.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_lifecycle_replay.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_lifecycle_replay.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunCryptoNumericLifecycleReplayTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_replay_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["replay_summary"],
            {
                "scenarios": 7,
                "filled_orders": 3,
                "not_filled_orders": 2,
                "open_positions": 1,
                "settled_positions": 2,
                "wins": 2,
                "losses": 0,
                "total_paper_pnl": 179.31,
                "bad_entries": 0,
                "rejected_bad_cases": 1,
            },
        )

    def test_required_outcomes_are_covered(self):
        payload = json.loads(_run_json().stdout)
        scenario_ids = {row["scenario_id"] for row in payload["scenarios"]}
        self.assertEqual(
            scenario_ids,
            {
                "filled_win",
                "filled_loss",
                "not_filled",
                "open_position",
                "settled_position",
                "rejected_raw_market",
                "no_action_watchlist_or_reject",
            },
        )

    def test_known_bad_entry_is_blocked_before_fill(self):
        payload = json.loads(_run_json().stdout)
        by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
        bad_entry = by_id["filled_loss"]
        self.assertEqual(bad_entry["lifecycle_status"], "not_filled")
        self.assertEqual(bad_entry["paper_orders_filled"], 0)
        self.assertEqual(bad_entry["paper_orders_not_filled"], 1)
        self.assertEqual(bad_entry["settled_positions"], 0)
        self.assertEqual(bad_entry["paper_pnl"], 0)
        self.assertEqual(bad_entry["ledger_events"][1]["reason"], "Fixture market is already settled no; paper fill blocked.")

    def test_legitimate_wins_are_preserved(self):
        payload = json.loads(_run_json().stdout)
        by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
        self.assertEqual(by_id["filled_win"]["paper_orders_filled"], 1)
        self.assertGreater(by_id["filled_win"]["paper_pnl"], 0)
        self.assertEqual(by_id["settled_position"]["paper_orders_filled"], 1)
        self.assertGreater(by_id["settled_position"]["paper_pnl"], 0)

    def test_rejected_and_no_action_cases(self):
        payload = json.loads(_run_json().stdout)
        by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
        self.assertEqual(by_id["rejected_raw_market"]["rejected_raw_markets"], 1)
        self.assertEqual(by_id["rejected_raw_market"]["paper_orders_submitted"], 0)
        self.assertEqual(by_id["no_action_watchlist_or_reject"]["no_action_entries"], 1)
        self.assertEqual(by_id["no_action_watchlist_or_reject"]["paper_orders_submitted"], 0)

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        for key in ("execution_allowed", "trading_allowed", "real_order_created", "wallet_used", "api_used", "network_used"):
            self.assertFalse(payload[key])
        for row in payload["scenarios"]:
            self.assertTrue(row["offline_only"])
            self.assertTrue(row["paper_only"])
            self.assertFalse(row["execution_allowed"])
            self.assertFalse(row["trading_allowed"])
            self.assertFalse(row["real_order_created"])
            self.assertFalse(row["wallet_used"])
            self.assertFalse(row["api_used"])
            self.assertFalse(row["network_used"])

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
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()

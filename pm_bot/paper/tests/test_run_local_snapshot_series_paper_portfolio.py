import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_paper_portfolio.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_series_paper_portfolio.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_series_paper_portfolio.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("portfolio_runner_under_test", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _paper_entry(market_id, asset="BTC", side="above", notional=100.0):
    return {
        "market_id": market_id,
        "asset": asset,
        "side": side,
        "action": "paper_limit_order",
        "limit_price": 0.5,
        "paper_notional": notional,
        "max_loss": notional,
        "reason": "test paper order",
    }


def _snapshot_entry(*market_ids):
    return {
        "observed_at": "2026-05-20T00:00:00Z",
        "observed_prices": {market_id: 0.5 for market_id in market_ids},
    }


def _limits(total=500.0, asset=500.0, orders=10, positions=10):
    return {
        "schema_version": "v1",
        "fixture_id": "unit_test_limits",
        "fixture_only": True,
        "paper_only": True,
        "max_total_paper_exposure": total,
        "max_asset_paper_exposure": asset,
        "max_orders_per_snapshot": orders,
        "max_open_positions": positions,
    }


class RunLocalSnapshotSeriesPaperPortfolioTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_portfolio_series_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["portfolio_series_summary"],
            {
                "snapshots_processed": 3,
                "total_snapshot_markets": 8,
                "adapted_raw_markets": 6,
                "adapter_rejections": 2,
                "paper_orders_created": 1,
                "duplicate_orders_blocked": 1,
                "risk_limit_orders_blocked": 1,
                "risk_limit_reason_counts": {
                    "max_total_paper_exposure_exceeded": 1,
                    "max_open_positions_exceeded": 1,
                },
                "open_positions": 0,
                "settled_positions": 1,
                "total_paper_notional": 100.0,
                "max_exposure": 100.0,
                "realized_paper_pnl": 72.41,
                "unrealized_paper_pnl": 0,
                "bad_entries": 0,
                "safety_flags_locked": True,
            },
        )

    def test_duplicate_block_and_settlement_events_are_preserved(self):
        payload = json.loads(_run_json().stdout)
        events = payload["portfolio_events"]
        self.assertEqual(sum(1 for row in events if row["event_type"] == "paper_order_created"), 1)
        self.assertEqual(sum(1 for row in events if row["event_type"] == "duplicate_paper_order_blocked"), 1)
        self.assertEqual(sum(1 for row in events if row["event_type"] == "risk_limit_paper_order_blocked"), 1)
        self.assertEqual(sum(1 for row in events if row["event_type"] == "paper_position_settled"), 1)
        self.assertEqual(events[2]["market_id"], "series_btc_above_90000_2026_05_31")
        self.assertEqual(
            events[3]["reason_codes"],
            ["max_total_paper_exposure_exceeded", "max_open_positions_exceeded"],
        )
        self.assertEqual(
            payload["risk_limit_decisions"][0]["reason_codes"],
            ["max_total_paper_exposure_exceeded", "max_open_positions_exceeded"],
        )
        self.assertEqual(payload["risk_limit_decisions"][0]["action"], "no_action")

    def test_risk_limit_reason_counts_are_included(self):
        payload = json.loads(_run_json().stdout)
        expected_counts = {
            "max_total_paper_exposure_exceeded": 1,
            "max_open_positions_exceeded": 1,
        }
        self.assertEqual(payload["portfolio_series_summary"]["risk_limit_reason_counts"], expected_counts)
        self.assertEqual(payload["snapshot_reports"][0]["risk_limit_reason_counts"], {})
        self.assertEqual(payload["snapshot_reports"][1]["risk_limit_reason_counts"], expected_counts)
        self.assertEqual(payload["snapshot_reports"][2]["risk_limit_reason_counts"], {})

    def test_rejections_and_positions_are_included(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual({row["reason_code"] for row in payload["adapter_rejections"]}, {"missing_question", "missing_price"})
        self.assertEqual(payload["intake_rejections"], [])
        self.assertEqual(len(payload["scoring_rejections"]), 2)
        self.assertEqual(len(payload["paper_positions"]), 1)
        self.assertTrue(all(row["status"] == "settled" for row in payload["paper_positions"]))

    def test_snapshot_order_and_carry_forward_exposure(self):
        payload = json.loads(_run_json().stdout)
        rows = payload["snapshot_reports"]
        self.assertEqual([row["snapshot_id"] for row in rows], ["series_snapshot_001", "series_snapshot_002", "series_snapshot_003"])
        self.assertEqual(rows[0]["exposure_summary"]["open_positions"], 1)
        self.assertEqual(rows[1]["exposure_summary"]["open_positions"], 1)
        self.assertEqual(rows[2]["exposure_summary"]["settled_positions"], 1)
        self.assertEqual(rows[1]["duplicate_orders_blocked"], 1)
        self.assertEqual(rows[1]["risk_limit_orders_blocked"], 1)

    def test_portfolio_risk_limit_helpers_block_each_limit_type(self):
        runner = _load_runner_module()
        base_entry = _paper_entry("unit_existing_btc")
        existing = runner._create_position(base_entry, 0.5, "2026-05-19T00:00:00Z")

        cases = [
            ("max_total_paper_exposure_exceeded", {"unit_existing_btc|above": dict(existing)}, _limits(total=150.0), _paper_entry("unit_new_eth", "ETH", "below")),
            ("max_asset_paper_exposure_exceeded", {"unit_existing_btc|above": dict(existing)}, _limits(asset=150.0), _paper_entry("unit_new_btc")),
            ("max_open_positions_exceeded", {"unit_existing_btc|above": dict(existing)}, _limits(positions=1), _paper_entry("unit_new_eth", "ETH", "below")),
        ]
        for reason_code, positions, limits, entry in cases:
            with self.subTest(reason_code=reason_code):
                created, duplicates, risk_blocked, events = runner._process_order_plan(
                    {"entries": [entry]},
                    positions,
                    _snapshot_entry(entry["market_id"]),
                    limits,
                )
                self.assertEqual(created, 0)
                self.assertEqual(duplicates, 0)
                self.assertEqual(risk_blocked, 1)
                self.assertIn(reason_code, events[0]["reason_codes"])

    def test_valid_order_within_limits_is_allowed(self):
        runner = _load_runner_module()
        entry = _paper_entry("unit_allowed_btc")
        positions = {}
        created, duplicates, risk_blocked, events = runner._process_order_plan(
            {"entries": [entry]},
            positions,
            _snapshot_entry(entry["market_id"]),
            _limits(),
        )
        self.assertEqual(created, 1)
        self.assertEqual(duplicates, 0)
        self.assertEqual(risk_blocked, 0)
        self.assertEqual(events[0]["event_type"], "paper_order_created")
        self.assertIn("unit_allowed_btc|above", positions)

    def test_max_orders_per_snapshot_blocks_after_first_created_order(self):
        runner = _load_runner_module()
        first = _paper_entry("unit_first_btc")
        second = _paper_entry("unit_second_eth", "ETH", "below")
        created, duplicates, risk_blocked, events = runner._process_order_plan(
            {"entries": [first, second]},
            {},
            _snapshot_entry(first["market_id"], second["market_id"]),
            _limits(orders=1),
        )
        self.assertEqual(created, 1)
        self.assertEqual(duplicates, 0)
        self.assertEqual(risk_blocked, 1)
        self.assertEqual(events[0]["event_type"], "paper_order_created")
        self.assertIn("max_orders_per_snapshot_exceeded", events[1]["reason_codes"])

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertTrue(payload["portfolio_series_summary"]["safety_flags_locked"])
        for key in (
            "live_fetcher_implemented",
            "execution_allowed",
            "trading_allowed",
            "real_order_created",
            "wallet_used",
            "api_used",
            "network_used",
        ):
            self.assertFalse(payload[key])
        for row in payload["snapshot_reports"] + payload["risk_limit_decisions"] + payload["portfolio_events"] + payload["paper_positions"]:
            self.assertTrue(row["offline_only"])
            self.assertTrue(row["paper_only"])
            self.assertFalse(row["live_fetcher_implemented"])
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

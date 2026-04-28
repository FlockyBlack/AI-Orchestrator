import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_multi_market_paper_run_series.py"
FIXTURE = ROOT / "pm_bot" / "paper" / "paper_run_series_fixture.v1.json"
OUTPUT = ROOT / "pm_bot" / "paper" / "multi_market_paper_run_series.v1.json"
OUTPUT_MD = ROOT / "pm_bot" / "paper" / "multi_market_paper_run_series.v1.md"
EXPECTED = ROOT / "pm_bot" / "paper" / "expected_multi_market_paper_run_series.v1.json"
RESULT = ROOT / "docs" / "PMBOT_PAPER_019_RESULT.json"

NEW_JSON_FILES = [FIXTURE, OUTPUT, EXPECTED, RESULT]


def _frag(*parts):
    return "".join(parts)


def _run_series():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("multi_market_paper_run_series", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _checks_by_id(report):
    return {check["check_id"]: check for check in report["checks"]}


class MultiMarketPaperRunSeriesTests(unittest.TestCase):
    def test_runner_writes_deterministic_json_markdown_and_expected_fixture(self):
        first_stdout = _run_series().stdout
        first_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        first_markdown = OUTPUT_MD.read_text(encoding="utf-8")
        second_stdout = _run_series().stdout
        second_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        second_markdown = OUTPUT_MD.read_text(encoding="utf-8")

        self.assertEqual(first_stdout, second_stdout)
        self.assertEqual(first_payloads, second_payloads)
        self.assertEqual(first_markdown, second_markdown)
        self.assertTrue(OUTPUT_MD.exists())
        self.assertEqual(_load_json(OUTPUT), _load_json(EXPECTED))
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)

    def test_multiple_market_lifecycle_and_status_counts_match_fixture(self):
        _run_series()
        report = _load_json(OUTPUT)
        fixture = _load_json(FIXTURE)

        self.assertEqual(report["task_id"], "PMBOT-PAPER-019-MULTI-MARKET-PAPER-RUN-SERIES")
        self.assertEqual(report["schema_version"], "multi_market_paper_run_series.v1")
        self.assertEqual(report["series_status"], "series_run_passed")
        self.assertEqual(report["markets_seen"], 5)
        self.assertEqual(len(report["market_ids"]), 5)
        self.assertEqual(report["records_seen"], len(fixture["records"]))
        self.assertEqual(report["records_processed"], 4)
        self.assertEqual(
            report["records_by_status"],
            {
                "accepted_accounting_record": 3,
                "blocked_fixture_record": 1,
                "manual_review_only": 1,
            },
        )
        self.assertEqual(
            report["lifecycle_summary"]["records_by_lifecycle_state"],
            {"blocked": 1, "open": 1, "settled": 3},
        )
        self.assertEqual(report["lifecycle_summary"]["manual_review_only_records"], 1)
        self.assertEqual(report["lifecycle_summary"]["blocked_or_rejected_records"], 1)

    def test_accounting_totals_match_fixture_defined_values(self):
        _run_series()
        report = _load_json(OUTPUT)
        fixture = _load_json(FIXTURE)
        expected = fixture["expected_summary"]["accounting_summary"]

        self.assertEqual(report["accounting_summary"], expected)
        self.assertEqual(expected["paper_accounting_total_records"], 4)
        self.assertEqual(expected["paper_accounting_settled_count"], 3)
        self.assertEqual(expected["paper_accounting_open_count"], 1)
        self.assertEqual(expected["paper_accounting_win_count"], 1)
        self.assertEqual(expected["paper_accounting_loss_count"], 1)
        self.assertEqual(expected["paper_accounting_flat_count"], 1)
        self.assertEqual(expected["paper_accounting_total_cost_basis"], "24.00")
        self.assertEqual(expected["paper_accounting_total_settlement_value"], "18.00")
        self.assertEqual(expected["paper_accounting_cumulative_pnl"], "-1.00")
        self.assertEqual(expected["paper_accounting_average_settled_pnl"], "-0.33")
        self.assertEqual(report["portfolio_summary"]["realized_paper_pnl"], "-1.00")
        self.assertEqual(report["portfolio_summary"]["unrealized_paper_pnl"], "0.00")

    def test_blocked_records_remain_non_executing_and_outside_accounting(self):
        _run_series()
        report = _load_json(OUTPUT)
        blocked = report["rejected_or_blocked_records"]

        self.assertEqual(len(blocked), 1)
        row = blocked[0]
        self.assertEqual(row["processing_status"], "blocked_fixture_record")
        self.assertFalse(row["accounting_included"])
        self.assertEqual(row["paper_orders_created"], 0)
        self.assertEqual(row["real_orders_created"], 0)
        self.assertEqual(row["network_calls"], 0)
        self.assertEqual(row["commands_executed"], 0)
        self.assertEqual(row["autonomous_decisions"], 0)
        self.assertEqual(report["paper_orders_created"], 0)
        self.assertEqual(report["real_orders_created"], 0)
        self.assertEqual(report["network_calls"], 0)
        self.assertEqual(report["commands_executed"], 0)
        self.assertEqual(report["autonomous_decisions"], 0)

    def test_checks_pass_and_result_doc_summarizes_series(self):
        _run_series()
        report = _load_json(OUTPUT)
        result = _load_json(RESULT)
        checks = _checks_by_id(report)

        self.assertEqual(len(checks), 6)
        self.assertTrue(all(check["status"] == "pass" for check in checks.values()))
        self.assertEqual(checks["fixture_expected_summary_alignment"]["actual"], [])
        self.assertEqual(checks["no_scoring_probability_ev_edge_or_market_decision_fields"]["actual"], [])
        self.assertEqual(report["mismatches"], [])
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["series_status"], "series_run_passed")
        self.assertEqual(result["series_summary"]["markets_seen"], 5)
        self.assertEqual(result["series_summary"]["records_processed"], 4)
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertEqual(result["real_orders_created"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["commands_executed"], 0)
        self.assertEqual(result["autonomous_decisions"], 0)
        self.assertFalse(result["safety"]["network_api"])
        self.assertFalse(result["safety"]["truth_inference"])

    def test_invalid_or_prohibited_fixture_fields_are_blocked(self):
        _run_series()
        module = _load_module()
        fixture = _load_json(FIXTURE)
        fixture["records"][0]["edge"] = "0.10"
        report = module.build_multi_market_paper_run_series(fixture, FIXTURE)
        checks = _checks_by_id(report)

        self.assertEqual(report["series_status"], "series_run_blocked")
        self.assertEqual(checks["no_scoring_probability_ev_edge_or_market_decision_fields"]["status"], "fail")
        self.assertIn("records[0].edge", checks["no_scoring_probability_ev_edge_or_market_decision_fields"]["actual"])

        fixture = _load_json(FIXTURE)
        fixture["records"][1]["paper_accounting_pnl"] = "99.00"
        report = module.build_multi_market_paper_run_series(fixture, FIXTURE)
        checks = _checks_by_id(report)
        self.assertEqual(report["series_status"], "series_run_blocked")
        self.assertEqual(checks["fixture_accounting_consistency"]["status"], "fail")

        fixture = _load_json(FIXTURE)
        fixture["records"][4]["cost_basis"] = "1.00"
        report = module.build_multi_market_paper_run_series(fixture, FIXTURE)
        checks = _checks_by_id(report)
        self.assertEqual(report["series_status"], "series_run_blocked")
        self.assertEqual(checks["fixture_accounting_consistency"]["status"], "fail")

    def test_no_runtime_network_or_order_behavior_in_runner_source(self):
        source = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("urllib", ".", "request"),
            _frag("websocket", "."),
            _frag("socket", "."),
            _frag("submit", "_", "order", "("),
            _frag("execute", "_", "trade", "("),
            _frag("place", "_", "order", "("),
            _frag("scripts", "/", "dispatcher", ".", "py"),
            _frag("scripts", "/", "run", "_", "codex", ".", "py"),
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, source)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "decimal", "json", "pathlib", "sys"})


if __name__ == "__main__":
    unittest.main()

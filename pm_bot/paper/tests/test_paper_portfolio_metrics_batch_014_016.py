import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_paper_portfolio_metrics_batch_014_016.py"
PNL_PREVIEW = ROOT / "pm_bot" / "paper" / "paper_accounting_pnl_preview.v1.json"
FILL_EVENTS = ROOT / "pm_bot" / "paper" / "paper_fill_events.v1.json"
MANUAL_LEDGER = ROOT / "pm_bot" / "paper" / "manual_paper_intent_ledger.v1.json"

ACCOUNTING_LEDGER = ROOT / "pm_bot" / "paper" / "paper_accounting_ledger.v1.json"
ACCOUNTING_LEDGER_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_accounting_ledger.v1.json"
PORTFOLIO_SNAPSHOT = ROOT / "pm_bot" / "paper" / "paper_portfolio_snapshot.v1.json"
PORTFOLIO_SNAPSHOT_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_portfolio_snapshot.v1.json"
METRICS_REPORT = ROOT / "pm_bot" / "paper" / "paper_metrics_report.v1.json"
METRICS_REPORT_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_metrics_report.v1.json"
RESULT = ROOT / "docs" / "PMBOT_PAPER_BATCH_014_016_RESULT.json"

NEW_JSON_FILES = [
    ACCOUNTING_LEDGER,
    ACCOUNTING_LEDGER_EXPECTED,
    PORTFOLIO_SNAPSHOT,
    PORTFOLIO_SNAPSHOT_EXPECTED,
    METRICS_REPORT,
    METRICS_REPORT_EXPECTED,
    RESULT,
]

FORBIDDEN_OUTPUT_FIELDS = {
    "probability",
    "implied_probability",
    "fair_probability",
    "ev",
    "expected_value",
    "edge",
    "score",
    "confidence_score",
    "sharpe",
    "kelly",
    "recommendation",
    "trade_recommendation",
    "decision",
    "trade_decision",
    "bot_decision",
    "generated_side",
    "generated_outcome",
    "generated_price",
    "generated_size",
    "auto_side",
    "auto_outcome",
    "auto_price",
    "auto_size",
    "orderbook",
    "api_price",
    "live_price",
    "wallet",
    "private_key",
    "api_key",
    "auth",
    "trading_endpoint",
    "market_decision",
}
SAFETY_FIELD_EXEMPTIONS = {
    "real_order_created",
    "live_order_created",
    "real_orders_created",
    "live_orders_created",
    "autonomous_paper_orders_created",
}


def _frag(*parts):
    return "".join(parts)


def _run_batch():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_portfolio_metrics_batch", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _field_tokens(key):
    lower = str(key).lower()
    parts = [part for part in lower.replace("-", "_").replace("/", "_").split("_") if part]
    tokens = {lower}
    tokens.update(parts)
    for index in range(len(parts) - 1):
        tokens.add(f"{parts[index]}_{parts[index + 1]}")
    for index in range(len(parts) - 2):
        tokens.add(f"{parts[index]}_{parts[index + 1]}_{parts[index + 2]}")
    return tokens


def _assert_no_forbidden_output_fields(test_case, payload):
    for key in _walk_keys(payload):
        if key in SAFETY_FIELD_EXEMPTIONS:
            continue
        test_case.assertTrue(
            FORBIDDEN_OUTPUT_FIELDS.isdisjoint(_field_tokens(key)),
            f"forbidden field emitted: {key}",
        )


class PaperPortfolioMetricsBatch014016Tests(unittest.TestCase):
    def test_paper_014_creates_accounting_ledger_from_pnl_preview(self):
        _run_batch()
        preview = _load_json(PNL_PREVIEW)
        ledger = _load_json(ACCOUNTING_LEDGER)

        self.assertEqual(preview["paper_accounting_records"][0]["market_id"], "824952")
        self.assertEqual(ledger["schema_version"], "paper_accounting_ledger.v1")
        self.assertEqual(ledger["market_ids"], ["824952"])
        self.assertEqual(ledger["counts"]["paper_accounting_ledger_entries"], 1)
        self.assertEqual(ledger["counts"]["paper_accounting_settled_count"], 1)
        self.assertIn("paper_accounting_entry_recorded", ledger["allowed_paper_accounting_entry_statuses"])

        entry = ledger["paper_accounting_ledger_entries"][0]
        self.assertEqual(entry["market_id"], "824952")
        self.assertEqual(entry["paper_accounting_source"], "paper/accounting-only")
        self.assertEqual(entry["paper_accounting_entry_status"], "paper_accounting_entry_recorded")
        self.assertEqual(entry["paper_position_status"], "paper_position_settled")
        self.assertEqual(entry["paper_accounting_cost_basis"], "4.00")
        self.assertEqual(entry["paper_accounting_settlement_value"], "10.00")
        self.assertEqual(entry["paper_accounting_pnl"], "6.00")
        self.assertEqual(entry["paper_accounting_cumulative_pnl"], "6.00")
        self.assertEqual(entry["source_references"]["source_manual_intent_id"], "manual-intent-001")
        self.assertEqual(entry["source_references"]["source_paper_fill_event_id"], "paper-fill-event-001")
        self.assertEqual(entry["source_references"]["source_settlement_id"], "paper-settlement-source-operator-manual-001")
        self.assertIs(entry["paper_accounting_only"], True)
        self.assertIs(entry["generated_by_bot"], False)
        self.assertIs(entry["live_order_created"], False)
        self.assertIs(entry["real_order_created"], False)
        _assert_no_forbidden_output_fields(self, ledger)

    def test_paper_014_blocks_prohibited_accounting_source_fields(self):
        _run_batch()
        module = _load_module()
        pnl_payload = _load_json(PNL_PREVIEW)
        fill_events_payload = _load_json(FILL_EVENTS)
        manual_ledger_payload = _load_json(MANUAL_LEDGER)
        unsafe_record = dict(pnl_payload["paper_accounting_records"][0])
        unsafe_record["paper_accounting_record_id"] = "paper-accounting-pnl-unsafe"
        unsafe_record["ev"] = "1.00"
        pnl_payload["paper_accounting_records"].append(unsafe_record)

        ledger = module.build_accounting_ledger(pnl_payload, fill_events_payload, manual_ledger_payload)
        by_id = {entry["source_references"]["source_paper_accounting_record_id"]: entry for entry in ledger["paper_accounting_ledger_entries"]}
        unsafe_entry = by_id["paper-accounting-pnl-unsafe"]
        self.assertEqual(unsafe_entry["paper_accounting_entry_status"], "paper_accounting_entry_blocked_invalid_source")
        self.assertIn("ev", unsafe_entry["blocked_keys"])

    def test_paper_015_creates_portfolio_snapshot_from_ledger(self):
        _run_batch()
        snapshot = _load_json(PORTFOLIO_SNAPSHOT)

        self.assertEqual(snapshot["schema_version"], "paper_portfolio_snapshot.v1")
        self.assertEqual(snapshot["paper_portfolio_status"], "paper_portfolio_snapshot_ready")
        self.assertIn(snapshot["paper_portfolio_status"], snapshot["allowed_paper_portfolio_statuses"])
        self.assertEqual(snapshot["market_ids"], ["824952"])
        self.assertEqual(snapshot["paper_accounting_settled_count"], 1)
        self.assertEqual(snapshot["paper_accounting_open_count"], 0)
        self.assertEqual(snapshot["paper_accounting_position_count"], 1)
        self.assertEqual(snapshot["paper_accounting_cumulative_pnl"], "6.00")
        self.assertEqual(snapshot["paper_accounting_gross_profit"], "6.00")
        self.assertEqual(snapshot["paper_accounting_gross_loss"], "0.00")
        self.assertEqual(snapshot["counts"]["paper_portfolio_snapshot_records"], 1)
        self.assertEqual(snapshot["positions"][0]["paper_position_status"], "paper_position_settled")
        self.assertNotIn("future_action", set(_walk_keys(snapshot)))
        _assert_no_forbidden_output_fields(self, snapshot)

    def test_paper_016_creates_accounting_only_metrics_report(self):
        _run_batch()
        metrics_report = _load_json(METRICS_REPORT)
        metrics = metrics_report["paper_accounting_metrics"]

        self.assertEqual(metrics_report["schema_version"], "paper_metrics_report.v1")
        self.assertEqual(metrics_report["market_ids"], ["824952"])
        self.assertEqual(metrics["paper_accounting_total_records"], 1)
        self.assertEqual(metrics["paper_accounting_settled_count"], 1)
        self.assertEqual(metrics["paper_accounting_open_count"], 0)
        self.assertEqual(metrics["paper_accounting_win_count"], 1)
        self.assertEqual(metrics["paper_accounting_loss_count"], 0)
        self.assertEqual(metrics["paper_accounting_flat_count"], 0)
        self.assertEqual(metrics["paper_accounting_cumulative_pnl"], "6.00")
        self.assertEqual(metrics["paper_accounting_average_pnl"], "6.00")
        self.assertEqual(metrics["paper_accounting_gross_profit"], "6.00")
        self.assertEqual(metrics["paper_accounting_gross_loss"], "0.00")
        self.assertEqual(metrics["paper_accounting_max_gain"], "6.00")
        self.assertEqual(metrics["paper_accounting_max_loss"], "0.00")
        self.assertTrue(all(key.startswith("paper_accounting_") for key in metrics))
        _assert_no_forbidden_output_fields(self, metrics_report)

    def test_boundary_safety_no_forbidden_imports_calls_or_order_artifacts(self):
        _run_batch()
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "decimal", "json", "pathlib", "sys"})

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("import", "httpx"),
            _frag("httpx", "."),
            _frag("import", "aiohttp"),
            _frag("aiohttp", "."),
            _frag("urllib", ".", "request"),
            _frag("websocket", "."),
            _frag("submit", "_", "order", "("),
            _frag("execute", "_", "trade", "("),
            _frag("place", "_", "order", "("),
            _frag("scripts", "/", "dispatcher", ".", "py"),
            _frag("scripts", "/", "run", "_", "codex", ".", "py"),
        ]
        for term in forbidden_call_terms:
            self.assertNotIn(term, source_no_spaces)

        result = _load_json(RESULT)
        self.assertEqual(result["counts"]["real_orders_created"], 0)
        self.assertEqual(result["counts"]["live_orders_created"], 0)
        self.assertEqual(result["counts"]["autonomous_paper_orders_created"], 0)
        self.assertFalse(result["safety"]["network_api_calls"])
        self.assertFalse(result["safety"]["wallet_private_keys"])
        self.assertFalse(result["safety"]["trading_endpoints"])
        self.assertFalse(result["safety"]["real_orders"])
        self.assertFalse(result["safety"]["live_trading"])
        self.assertFalse(result["safety"]["autonomous_paper_orders"])
        self.assertFalse(result["safety"]["runtime_wiring"])
        self.assertFalse(result["safety"]["dispatcher_run_codex_changes"])
        for path in result["files_created"]:
            name = Path(path).name.lower()
            self.assertNotIn("real_order", name)
            self.assertNotIn("live_order", name)
            self.assertNotIn("autonomous_paper_order", name)

    def test_outputs_are_deterministic_and_match_expected_json_fixtures(self):
        first = _run_batch().stdout
        first_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        second = _run_batch().stdout
        second_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}

        self.assertEqual(first, second)
        self.assertEqual(first_payloads, second_payloads)
        self.assertEqual(_load_json(ACCOUNTING_LEDGER), _load_json(ACCOUNTING_LEDGER_EXPECTED))
        self.assertEqual(_load_json(PORTFOLIO_SNAPSHOT), _load_json(PORTFOLIO_SNAPSHOT_EXPECTED))
        self.assertEqual(_load_json(METRICS_REPORT), _load_json(METRICS_REPORT_EXPECTED))

    def test_new_json_artifacts_parse_and_result_matches_expected_metrics(self):
        _run_batch()
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)

        result = _load_json(RESULT)
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["market_ids"], ["824952"])
        self.assertEqual(result["counts"]["paper_accounting_ledger_entries"], 1)
        self.assertEqual(result["counts"]["paper_portfolio_snapshot_records"], 1)
        self.assertEqual(result["counts"]["paper_metrics_report_records"], 1)
        self.assertEqual(result["accounting_metrics"]["paper_accounting_total_records"], 1)
        self.assertEqual(result["accounting_metrics"]["paper_accounting_cumulative_pnl"], "6.00")
        self.assertEqual(result["accounting_metrics"]["paper_accounting_max_gain"], "6.00")
        self.assertEqual(result["accounting_metrics"]["paper_accounting_max_loss"], "0.00")


if __name__ == "__main__":
    unittest.main()

import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_paper_fill_settlement_pnl_batch_011_013.py"
MANUAL_LEDGER = ROOT / "pm_bot" / "paper" / "manual_paper_intent_ledger.v1.json"
WORKBENCH_PREVIEW = ROOT / "pm_bot" / "paper" / "paper_workbench_preview.v1.json"
FILL_CONTRACT = ROOT / "pm_bot" / "paper" / "paper_fill_source_contract.v1.json"
FILL_FIXTURE = ROOT / "pm_bot" / "paper" / "paper_fill_source_fixture.v1.json"
FILL_ACCEPTED = ROOT / "pm_bot" / "paper" / "paper_fill_sources_accepted.v1.json"
FILL_REJECTED = ROOT / "pm_bot" / "paper" / "paper_fill_sources_rejected.v1.json"
FILL_EVENTS = ROOT / "pm_bot" / "paper" / "paper_fill_events.v1.json"
FILL_EVENTS_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_fill_events.v1.json"
SETTLEMENT_FIXTURE = ROOT / "pm_bot" / "paper" / "paper_settlement_source_fixture.v1.json"
SETTLEMENT_ACCEPTED = ROOT / "pm_bot" / "paper" / "paper_settlement_sources_accepted.v1.json"
SETTLEMENT_REJECTED = ROOT / "pm_bot" / "paper" / "paper_settlement_sources_rejected.v1.json"
PNL_PREVIEW = ROOT / "pm_bot" / "paper" / "paper_accounting_pnl_preview.v1.json"
PNL_PREVIEW_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_accounting_pnl_preview.v1.json"
RESULT = ROOT / "docs" / "PMBOT_PAPER_BATCH_011_013_RESULT.json"

NEW_JSON_FILES = [
    FILL_CONTRACT,
    FILL_FIXTURE,
    FILL_ACCEPTED,
    FILL_REJECTED,
    FILL_EVENTS,
    FILL_EVENTS_EXPECTED,
    SETTLEMENT_FIXTURE,
    SETTLEMENT_ACCEPTED,
    SETTLEMENT_REJECTED,
    PNL_PREVIEW,
    PNL_PREVIEW_EXPECTED,
    RESULT,
]


def _frag(*parts):
    return "".join(parts)


def _run_batch():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_fill_settlement_pnl_batch", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class PaperFillSettlementPnlBatch011013Tests(unittest.TestCase):
    def test_paper_011_reads_ledger_and_creates_manual_fill_source_contract_and_fixture(self):
        _run_batch()
        ledger = _load_json(MANUAL_LEDGER)
        preview = _load_json(WORKBENCH_PREVIEW)
        contract = _load_json(FILL_CONTRACT)
        fixture = _load_json(FILL_FIXTURE)

        self.assertEqual(ledger["ledger_entries"][0]["market_id"], "824952")
        self.assertEqual(preview["preview_records"][0]["market_id"], "824952")
        self.assertEqual(contract["market_ids"], ["824952"])
        self.assertEqual(contract["counts"]["manual_paper_intent_ledger_entries"], 1)
        self.assertIn("operator_manual_fill_fixture", contract["allowed_fill_source_types"])
        self.assertIn("no_fill_source_available", contract["allowed_fill_source_types"])
        self.assertIn("blocked_by_policy", contract["allowed_fill_source_types"])
        self.assertIn("paper_only", contract["required_fields"])
        self.assertIn("inert_only", contract["required_fields"])
        self.assertIs(contract["blank_record"]["paper_only"], True)
        self.assertIs(contract["blank_record"]["inert_only"], True)
        self.assertIs(contract["blank_record"]["generated_by_bot"], False)
        self.assertIn("external_data_required_false", contract["validation_rules"])
        self.assertIn("orderbook_data_required_false", contract["validation_rules"])
        self.assertEqual(len(fixture["records"]), 3)

    def test_paper_012_accepts_valid_manual_fill_rejects_unknown_and_unsafe_rows(self):
        _run_batch()
        accepted = _load_json(FILL_ACCEPTED)
        rejected = _load_json(FILL_REJECTED)
        events = _load_json(FILL_EVENTS)

        self.assertEqual(accepted["counts"]["records_accepted"], 1)
        self.assertEqual(rejected["counts"]["records_rejected"], 2)
        valid = accepted["records"][0]
        self.assertEqual(valid["fill_source_id"], "paper-fill-source-operator-manual-001")
        self.assertEqual(valid["market_id"], "824952")
        self.assertEqual(valid["fill_source_type"], "operator_manual_fill_fixture")
        self.assertIs(valid["paper_only"], True)
        self.assertIs(valid["inert_only"], True)
        self.assertIs(valid["generated_by_bot"], False)
        self.assertIs(valid["live_order_created"], False)
        self.assertIs(valid["real_order_created"], False)

        rejected_by_id = {record["fill_source_id"]: record for record in rejected["records"]}
        self.assertIn("unknown_market_id", rejected_by_id["paper-fill-source-rejected-unknown-market"]["rejection_reasons"])
        unsafe = rejected_by_id["paper-fill-source-rejected-live-bot"]
        self.assertIn("generated_by_bot_false_required", unsafe["rejection_reasons"])
        self.assertIn("live_order_created_false_required", unsafe["rejection_reasons"])
        self.assertIn("prohibited_or_execution_field_present", unsafe["rejection_reasons"])
        self.assertIn("blocked_language_present", unsafe["rejection_reasons"])
        for key in ["api_key", "bot_decision", "recommendation", "trading_endpoint", "wallet"]:
            self.assertIn(key, unsafe["blocked_keys"])

        self.assertEqual(events, _load_json(FILL_EVENTS_EXPECTED))
        self.assertEqual(events["counts"]["paper_fill_events_written"], 1)
        event = events["paper_fill_events"][0]
        self.assertEqual(event["paper_fill_event_status"], "paper_fill_recorded_from_operator_manual_fixture")
        self.assertEqual(event["operator_manual_fill_price"], 0.4)
        self.assertEqual(event["operator_manual_fill_size"], 10)
        self.assertIs(event["real_order_created"], False)
        self.assertIs(event["live_order_created"], False)
        self.assertIs(event["generated_by_bot"], False)

    def test_paper_013_accepts_valid_manual_settlement_rejects_unknown_and_resolution_rows(self):
        _run_batch()
        settlement_fixture = _load_json(SETTLEMENT_FIXTURE)
        accepted = _load_json(SETTLEMENT_ACCEPTED)
        rejected = _load_json(SETTLEMENT_REJECTED)
        pnl_preview = _load_json(PNL_PREVIEW)

        self.assertEqual(len(settlement_fixture["records"]), 3)
        self.assertEqual(accepted["counts"]["records_accepted"], 1)
        self.assertEqual(rejected["counts"]["records_rejected"], 2)
        valid = accepted["records"][0]
        self.assertEqual(valid["market_id"], "824952")
        self.assertEqual(valid["settlement_source_type"], "operator_manual_settlement_fixture")
        self.assertEqual(valid["operator_manual_settlement_price"], 1.0)
        self.assertIs(valid["paper_only"], True)
        self.assertIs(valid["inert_only"], True)
        self.assertIs(valid["generated_by_bot"], False)

        rejected_by_id = {record["settlement_source_id"]: record for record in rejected["records"]}
        self.assertIn("unknown_market_id", rejected_by_id["paper-settlement-source-rejected-unknown-market"]["rejection_reasons"])
        unsafe = rejected_by_id["paper-settlement-source-rejected-api-truth"]
        self.assertIn("generated_by_bot_false_required", unsafe["rejection_reasons"])
        self.assertIn("prohibited_or_resolution_field_present", unsafe["rejection_reasons"])
        self.assertIn("blocked_language_present", unsafe["rejection_reasons"])
        for key in ["api_resolution", "live_price", "recommendation", "truth_inference"]:
            self.assertIn(key, unsafe["blocked_keys"])

        record = pnl_preview["paper_accounting_records"][0]
        self.assertEqual(record["paper_accounting_status"], "paper_position_settled_from_operator_manual_fixture")
        self.assertIn("paper_accounting_cost_basis", record)
        self.assertIn("paper_accounting_settlement_value", record)
        self.assertIn("paper_accounting_pnl", record)
        forbidden_keys = {
            "probability",
            "implied_probability",
            "fair_probability",
            "ev",
            "expected_value",
            "edge",
            "score",
            "confidence_score",
            "recommendation",
            "trade_recommendation",
            "decision",
            "trade_decision",
            "bot_decision",
            "generated_side",
            "generated_price",
            "generated_size",
            "auto_side",
            "auto_price",
            "auto_size",
            "market_decision",
        }
        self.assertTrue(forbidden_keys.isdisjoint(set(_walk_keys(pnl_preview))))

    def test_pnl_accounting_is_deterministic_and_matches_expected_fixture(self):
        _run_batch()
        pnl_preview = _load_json(PNL_PREVIEW)

        self.assertEqual(pnl_preview, _load_json(PNL_PREVIEW_EXPECTED))
        self.assertEqual(pnl_preview["counts"]["paper_accounting_pnl_records"], 1)
        self.assertEqual(pnl_preview["paper_accounting_totals"]["paper_accounting_total_cost_basis"], "4.00")
        self.assertEqual(pnl_preview["paper_accounting_totals"]["paper_accounting_total_settlement_value"], "10.00")
        self.assertEqual(pnl_preview["paper_accounting_totals"]["paper_accounting_total_pnl"], "6.00")
        record = pnl_preview["paper_accounting_records"][0]
        self.assertEqual(record["paper_accounting_cost_basis"], "4.00")
        self.assertEqual(record["paper_accounting_settlement_value"], "10.00")
        self.assertEqual(record["paper_accounting_pnl"], "6.00")

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

        created_names = [path.name.lower() for path in ROOT.joinpath("pm_bot", "paper").iterdir() if path.is_file()]
        self.assertFalse(any("real_order" in name or "live_order" in name for name in created_names))
        result = _load_json(RESULT)
        self.assertEqual(result["counts"]["real_orders_created"], 0)
        self.assertEqual(result["counts"]["live_orders_created"], 0)
        self.assertEqual(result["counts"]["autonomous_paper_orders_created"], 0)
        self.assertFalse(result["safety"]["real_orders"])
        self.assertFalse(result["safety"]["live_trading"])
        self.assertFalse(result["safety"]["autonomous_paper_orders"])
        self.assertFalse(result["safety"]["runtime_wiring"])
        self.assertFalse(result["safety"]["dispatcher_run_codex_changes"])

    def test_outputs_are_deterministic_and_new_json_artifacts_parse(self):
        first = _run_batch().stdout
        first_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        second = _run_batch().stdout
        second_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}

        self.assertEqual(first, second)
        self.assertEqual(first_payloads, second_payloads)
        self.assertEqual(_load_json(FILL_EVENTS), _load_json(FILL_EVENTS_EXPECTED))
        self.assertEqual(_load_json(PNL_PREVIEW), _load_json(PNL_PREVIEW_EXPECTED))

    def test_runner_module_rejects_custom_scoring_and_live_resolution_records(self):
        _run_batch()
        module = _load_module()
        ledger = _load_json(MANUAL_LEDGER)
        fill_fixture = module.build_fill_source_fixture(ledger)
        fill_fixture["records"].append(
            {
                "fill_source_id": "custom-fill-rejected-generated-price",
                "market_id": "824952",
                "source_manual_intent_id": "manual-intent-001",
                "source_ledger_entry_id": "manual-paper-intent-ledger-001",
                "fill_source_type": "operator_manual_fill_fixture",
                "operator_manual_fill_status": "operator_manual_fill_recorded",
                "operator_manual_fill_price": 0.4,
                "operator_manual_fill_size": 1,
                "operator_manual_fill_notes": "operator provided local fixture",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
                "generated_price": 0.4,
            }
        )
        _accepted, rejected, _events = module.build_fill_source_outputs(ledger, fill_fixture)
        rejected_by_id = {record["fill_source_id"]: record for record in rejected["records"]}
        self.assertIn(
            "prohibited_or_execution_field_present",
            rejected_by_id["custom-fill-rejected-generated-price"]["rejection_reasons"],
        )

        fill_events = _load_json(FILL_EVENTS)
        settlement_fixture = module.build_settlement_source_fixture(fill_events)
        settlement_fixture["records"].append(
            {
                "settlement_source_id": "custom-settlement-rejected-live-resolution",
                "market_id": "824952",
                "source_manual_intent_id": "manual-intent-001",
                "source_ledger_entry_id": "manual-paper-intent-ledger-001",
                "source_paper_fill_event_id": "paper-fill-event-001",
                "settlement_source_type": "operator_manual_settlement_fixture",
                "operator_manual_settlement_status": "operator_manual_settlement_recorded",
                "operator_manual_settlement_outcome": "operator_fixture_outcome_settled",
                "operator_manual_settlement_price": 1.0,
                "operator_manual_settlement_notes": "live resolution requested",
                "paper_only": True,
                "inert_only": True,
                "generated_by_bot": False,
                "live_order_created": False,
                "real_order_created": False,
            }
        )
        _accepted_settlement, rejected_settlement = module.build_settlement_outputs(fill_events, settlement_fixture)
        rejected_settlement_by_id = {
            record["settlement_source_id"]: record for record in rejected_settlement["records"]
        }
        self.assertIn(
            "blocked_language_present",
            rejected_settlement_by_id["custom-settlement-rejected-live-resolution"]["rejection_reasons"],
        )


if __name__ == "__main__":
    unittest.main()

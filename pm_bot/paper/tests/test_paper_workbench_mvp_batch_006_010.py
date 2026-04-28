import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_paper_workbench_mvp_batch_006_010.py"
GATE = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_gate.v1.json"
HUMAN_REVIEW_INPUT = ROOT / "pm_bot" / "paper" / "paper_simulation_gate_human_review_records_input.v1.json"
HUMAN_REVIEW_ACCEPTED = ROOT / "pm_bot" / "paper" / "paper_simulation_gate_human_review_records_accepted.v1.json"
HUMAN_REVIEW_REJECTED = ROOT / "pm_bot" / "paper" / "paper_simulation_gate_human_review_records_rejected.v1.json"
PLAN_DRAFT = ROOT / "pm_bot" / "paper" / "paper_simulation_plan_draft.v1.json"
PLAN_DRAFT_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_simulation_plan_draft.v1.json"
MANUAL_TEMPLATE = ROOT / "pm_bot" / "paper" / "manual_paper_intent_template.v1.json"
MANUAL_INPUT = ROOT / "pm_bot" / "paper" / "manual_paper_intents_input.v1.json"
MANUAL_ACCEPTED = ROOT / "pm_bot" / "paper" / "manual_paper_intents_accepted.v1.json"
MANUAL_REJECTED = ROOT / "pm_bot" / "paper" / "manual_paper_intents_rejected.v1.json"
MANUAL_LEDGER = ROOT / "pm_bot" / "paper" / "manual_paper_intent_ledger.v1.json"
PREVIEW = ROOT / "pm_bot" / "paper" / "paper_workbench_preview.v1.json"
PREVIEW_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_workbench_preview.v1.json"
RESULT = ROOT / "docs" / "PMBOT_PAPER_BATCH_006_010_RESULT.json"

ALLOWED_PLAN_STATUSES = {
    "paper_simulation_plan_draft_ready_for_manual_intent",
    "paper_simulation_plan_needs_revision",
    "paper_simulation_plan_watch_only",
    "paper_simulation_plan_blocked",
}
ALLOWED_PAPER_POSITION_STATUSES = {
    "manual_paper_intent_recorded",
    "manual_paper_intent_needs_fill_source",
    "manual_paper_intent_blocked",
    "manual_paper_position_watch_only",
}
NEW_JSON_FILES = [
    HUMAN_REVIEW_INPUT,
    HUMAN_REVIEW_ACCEPTED,
    HUMAN_REVIEW_REJECTED,
    PLAN_DRAFT,
    PLAN_DRAFT_EXPECTED,
    MANUAL_TEMPLATE,
    MANUAL_INPUT,
    MANUAL_ACCEPTED,
    MANUAL_REJECTED,
    MANUAL_LEDGER,
    PREVIEW,
    PREVIEW_EXPECTED,
    RESULT,
]


def _frag(*parts):
    return "".join(parts)


def _run_batch():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_workbench_mvp_batch", RUNNER)
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


def _json_text(path):
    return path.read_text(encoding="utf-8").lower()


class PaperWorkbenchMvpBatch006010Tests(unittest.TestCase):
    def test_paper_006_reads_gate_and_classifies_human_review_records(self):
        _run_batch()
        gate = _load_json(GATE)
        accepted = _load_json(HUMAN_REVIEW_ACCEPTED)
        rejected = _load_json(HUMAN_REVIEW_REJECTED)

        self.assertEqual(gate["market_ids"], ["824952"])
        self.assertEqual(accepted["counts"]["records_accepted"], 1)
        self.assertEqual(accepted["records"][0]["market_id"], "824952")
        self.assertEqual(
            accepted["records"][0]["source_gate_status"],
            "paper_simulation_gate_passed_for_manual_review",
        )
        self.assertEqual(rejected["counts"]["records_rejected"], 3)
        rejected_by_id = {record["record_id"]: record for record in rejected["records"]}
        self.assertIn("unknown_market_id", rejected_by_id["human-review-rejected-unknown-market"]["rejection_reasons"])
        self.assertIn(
            "prohibited_or_execution_field_present",
            rejected_by_id["human-review-rejected-prohibited-field"]["rejection_reasons"],
        )
        self.assertEqual(rejected_by_id["human-review-rejected-prohibited-field"]["blocked_keys"], ["decision"])
        self.assertIn("unknown_review_outcome", rejected_by_id["human-review-rejected-unknown-outcome"]["rejection_reasons"])

    def test_paper_007_creates_safe_plan_draft_without_generated_trading_terms(self):
        _run_batch()
        plan = _load_json(PLAN_DRAFT)

        self.assertEqual(plan, _load_json(PLAN_DRAFT_EXPECTED))
        self.assertEqual(plan["counts"]["simulation_plans_written"], 1)
        record = plan["plan_records"][0]
        self.assertEqual(record["market_id"], "824952")
        self.assertIn(record["plan_status"], ALLOWED_PLAN_STATUSES)
        self.assertEqual(record["plan_status"], "paper_simulation_plan_draft_ready_for_manual_intent")

        forbidden_fragments = [
            "generated_side",
            "generated_outcome",
            "generated_price",
            "generated_size",
            "probability",
            "expected_value",
            "confidence_score",
            "trade_recommendation",
            "recommendation",
            "order_plan",
            "market_decision",
        ]
        plan_text = json.dumps(plan, sort_keys=True).lower()
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, plan_text)

    def test_paper_008_creates_manual_template_with_required_attestation_and_flags(self):
        _run_batch()
        template = _load_json(MANUAL_TEMPLATE)

        self.assertIn("operator_manual_attestation", template["required_fields"])
        self.assertIn("paper_only", template["required_fields"])
        self.assertIn("inert_only", template["required_fields"])
        self.assertIs(template["blank_record"]["paper_only"], True)
        self.assertIs(template["blank_record"]["inert_only"], True)
        self.assertEqual(template["blank_record"]["operator_manual_attestation"], "")

    def test_paper_009_accepts_valid_manual_intent_rejects_unsafe_rows_and_writes_inert_ledger(self):
        _run_batch()
        accepted = _load_json(MANUAL_ACCEPTED)
        rejected = _load_json(MANUAL_REJECTED)
        ledger = _load_json(MANUAL_LEDGER)

        self.assertEqual(accepted["counts"]["records_accepted"], 1)
        self.assertEqual(accepted["records"][0]["intent_id"], "manual-intent-001")
        self.assertEqual(accepted["records"][0]["market_id"], "824952")
        self.assertEqual(rejected["counts"]["records_rejected"], 2)

        rejected_by_id = {record["intent_id"]: record for record in rejected["records"]}
        self.assertIn(
            "operator_manual_attestation_required",
            rejected_by_id["manual-intent-rejected-missing-attestation"]["rejection_reasons"],
        )
        unsafe = rejected_by_id["manual-intent-rejected-bot-live"]
        self.assertIn("prohibited_or_execution_field_present", unsafe["rejection_reasons"])
        self.assertIn("blocked_language_present", unsafe["rejection_reasons"])
        self.assertEqual(unsafe["blocked_keys"], ["bot_recommendation", "live_order"])

        self.assertEqual(ledger["counts"]["manual_paper_intent_ledger_entries"], 1)
        self.assertEqual(ledger["counts"]["real_orders_created"], 0)
        self.assertEqual(ledger["counts"]["live_orders_created"], 0)
        self.assertEqual(ledger["counts"]["autonomous_paper_orders_created"], 0)
        entry = ledger["ledger_entries"][0]
        self.assertEqual(entry["intent_source"], "operator_manual")
        self.assertEqual(entry["execution_mode"], "paper_only_inert")
        self.assertIs(entry["generated_by_bot"], False)
        self.assertIs(entry["real_order_created"], False)
        self.assertIs(entry["live_order_created"], False)

    def test_paper_010_creates_preview_without_calculated_metrics_or_market_guidance(self):
        _run_batch()
        preview = _load_json(PREVIEW)

        self.assertEqual(preview, _load_json(PREVIEW_EXPECTED))
        self.assertEqual(preview["counts"]["paper_workbench_preview_records"], 1)
        self.assertEqual(preview["counts"]["fills_simulated"], 0)
        record = preview["preview_records"][0]
        self.assertIn(record["paper_position_status"], ALLOWED_PAPER_POSITION_STATUSES)
        self.assertEqual(record["paper_position_status"], "manual_paper_intent_needs_fill_source")
        self.assertEqual(record["operator_manual_side"], "operator_fixture_side")
        self.assertEqual(record["operator_manual_limit_price"], 0.42)
        self.assertEqual(record["operator_manual_size"], 10)

        preview_text = json.dumps(preview, sort_keys=True).lower()
        for fragment in ["pnl", "probability", "expected_value", "confidence_score", "recommendation", "market_edge"]:
            self.assertNotIn(fragment, preview_text)

    def test_boundary_safety_no_forbidden_imports_calls_or_real_live_order_artifacts(self):
        _run_batch()
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

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
        self.assertFalse(result["safety"]["real_orders"])
        self.assertFalse(result["safety"]["live_trading"])
        self.assertFalse(result["safety"]["autonomous_paper_orders"])

    def test_outputs_are_deterministic_and_json_artifacts_parse(self):
        first = _run_batch().stdout
        first_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        second = _run_batch().stdout
        second_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}

        self.assertEqual(first, second)
        self.assertEqual(first_payloads, second_payloads)
        self.assertEqual(_load_json(PLAN_DRAFT), _load_json(PLAN_DRAFT_EXPECTED))
        self.assertEqual(_load_json(PREVIEW), _load_json(PREVIEW_EXPECTED))

    def test_no_unsafe_fields_are_added_to_non_manual_artifacts(self):
        _run_batch()
        non_manual_paths = [HUMAN_REVIEW_ACCEPTED, PLAN_DRAFT]
        forbidden_keys = {
            "operator_manual_side",
            "operator_manual_limit_price",
            "operator_manual_size",
            "operator_manual_outcome",
            "generated_side",
            "generated_outcome",
            "auto_side",
            "auto_outcome",
            "auto_size",
            "trade_recommendation",
            "bot_decision",
        }
        for path in non_manual_paths:
            keys = set(_walk_keys(_load_json(path)))
            self.assertTrue(forbidden_keys.isdisjoint(keys), msg=str(path))

    def test_manual_input_fixture_contains_required_valid_and_invalid_rows(self):
        _run_batch()
        manual_input = _load_json(MANUAL_INPUT)
        records = {record["intent_id"]: record for record in manual_input["records"]}

        self.assertIn("manual-intent-001", records)
        self.assertIn("manual-intent-rejected-missing-attestation", records)
        self.assertIn("manual-intent-rejected-bot-live", records)
        self.assertTrue(records["manual-intent-001"]["paper_only"])
        self.assertTrue(records["manual-intent-001"]["inert_only"])
        self.assertNotIn("operator_manual_attestation", records["manual-intent-rejected-missing-attestation"])
        self.assertIn("bot_recommendation", records["manual-intent-rejected-bot-live"])
        self.assertIn("live_order", records["manual-intent-rejected-bot-live"])

    def test_runner_module_build_functions_reject_custom_unsafe_records(self):
        module = _load_module()
        gate = _load_json(GATE)
        review_fixture = module.build_human_review_input_fixture(GATE)
        review_fixture["records"].append(
            {
                "record_id": "custom-unsafe",
                "market_id": "824952",
                "review_outcome": "approved_for_paper_simulation_plan_drafting",
                "reviewer": "operator_fixture",
                "review_notes": [],
                "trade_decision": "blocked",
            }
        )
        _accepted, rejected = module.build_human_review_records(gate, review_fixture)
        rejected_by_id = {record["record_id"]: record for record in rejected["records"]}
        self.assertIn("prohibited_or_execution_field_present", rejected_by_id["custom-unsafe"]["rejection_reasons"])

        accepted_review, _rejected_review = module.build_human_review_records(gate, module.build_human_review_input_fixture(GATE))
        plan = module.build_plan_draft(accepted_review)
        manual_fixture = module.build_manual_paper_intents_input_fixture()
        manual_fixture["records"].append(
            {
                "intent_id": "custom-unsafe-manual",
                "market_id": "824952",
                "source_plan_status": "paper_simulation_plan_draft_ready_for_manual_intent",
                "operator_manual_outcome": "operator_fixture_outcome",
                "operator_manual_side": "operator_fixture_side",
                "operator_manual_limit_price": 0.5,
                "operator_manual_size": 1,
                "operator_manual_rationale": "live order requested",
                "operator_manual_attestation": "operator provided",
                "paper_only": True,
                "inert_only": True,
            }
        )
        _accepted_manual, rejected_manual, _ledger = module.build_manual_intent_outputs(plan, manual_fixture)
        rejected_manual_by_id = {record["intent_id"]: record for record in rejected_manual["records"]}
        self.assertIn("blocked_language_present", rejected_manual_by_id["custom-unsafe-manual"]["rejection_reasons"])


if __name__ == "__main__":
    unittest.main()

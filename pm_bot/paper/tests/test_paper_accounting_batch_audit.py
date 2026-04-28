import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_paper_accounting_batch_audit.py"
AUDIT = ROOT / "pm_bot" / "paper" / "paper_accounting_batch_audit.v1.json"
AUDIT_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_accounting_batch_audit.v1.json"
AUDIT_MD = ROOT / "pm_bot" / "paper" / "paper_accounting_batch_audit.v1.md"
RESULT = ROOT / "docs" / "PMBOT_PAPER_018_RESULT.json"
LANE_RESULT = ROOT / "docs" / "PMBOT_CODEX_A_ROUND002_RESULT.json"

NEW_JSON_FILES = [
    AUDIT,
    AUDIT_EXPECTED,
    RESULT,
    LANE_RESULT,
]


def _frag(*parts):
    return "".join(parts)


def _run_audit():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_accounting_batch_audit", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _checks_by_id(audit):
    checks = (
        audit["lifecycle_consistency_checks"]
        + audit["artifact_pointer_checks"]
        + audit["safety_checks"]
    )
    return {check["check_id"]: check for check in checks}


def _build_audit_with_mutated_batch(module, artifacts, mutator):
    original = module._build_batch_input
    batch_input = original(artifacts)
    mutator(batch_input)
    try:
        module._build_batch_input = lambda _artifacts: batch_input
        return module.build_batch_audit(artifacts)
    finally:
        module._build_batch_input = original


class PaperAccountingBatchAuditTests(unittest.TestCase):
    def test_paper_018_reconciles_multi_record_accounting_batch(self):
        _run_audit()
        audit = _load_json(AUDIT)
        result = _load_json(RESULT)

        self.assertEqual(audit, _load_json(AUDIT_EXPECTED))
        self.assertEqual(result, _load_json(LANE_RESULT))
        self.assertEqual(audit["task_id"], "PMBOT-PAPER-018-MULTI-RECORD-PAPER-ACCOUNTING-BATCH-AUDIT")
        self.assertEqual(audit["schema_version"], "paper_accounting_batch_audit.v1")
        self.assertEqual(audit["audit_status"], "batch_audit_passed")
        self.assertEqual(audit["records_audited"], 3)
        self.assertEqual(audit["records_seen"]["existing_source_records_read"], 1)
        self.assertEqual(audit["records_seen"]["synthetic_fixture_records"], 2)
        self.assertEqual(audit["records_seen"]["batch_accounting_records"], 3)
        self.assertEqual(
            audit["market_ids"],
            [
                "824952",
                "paper-batch-market-open-003",
                "paper-batch-market-settled-loss-002",
            ],
        )

        totals = audit["accounting_totals"]
        self.assertEqual(totals["paper_accounting_total_records"], 3)
        self.assertEqual(totals["paper_accounting_settled_count"], 2)
        self.assertEqual(totals["paper_accounting_open_count"], 1)
        self.assertEqual(totals["paper_accounting_win_count"], 1)
        self.assertEqual(totals["paper_accounting_loss_count"], 1)
        self.assertEqual(totals["paper_accounting_flat_count"], 0)
        self.assertEqual(totals["paper_accounting_total_cost_basis"], "16.00")
        self.assertEqual(totals["paper_accounting_total_settlement_value"], "10.00")
        self.assertEqual(totals["paper_accounting_cumulative_pnl"], "-1.00")
        self.assertEqual(totals["paper_accounting_average_pnl"], "-0.50")
        self.assertEqual(totals["paper_accounting_gross_profit"], "6.00")
        self.assertEqual(totals["paper_accounting_gross_loss"], "-7.00")
        self.assertEqual(totals["paper_accounting_max_gain"], "6.00")
        self.assertEqual(totals["paper_accounting_max_loss"], "-7.00")

        checks = _checks_by_id(audit)
        self.assertEqual(len(checks), 13)
        self.assertTrue(all(check["status"] == "pass" for check in checks.values()))
        self.assertEqual(checks["record_count_consistency"]["actual"]["batch_accounting_records"], 3)
        self.assertEqual(checks["market_id_consistency"]["actual"], [])
        self.assertEqual(checks["fill_settlement_accounting_linkage"]["actual"], [])
        self.assertEqual(checks["open_settled_status_consistency"]["actual"], [])
        self.assertEqual(checks["pnl_aggregation_consistency"]["expected"], totals)
        self.assertEqual(checks["artifact_pointer_consistency"]["actual"], [])
        self.assertEqual(checks["safety_flag_consistency"]["actual"], [])
        self.assertEqual(checks["no_scoring_probability_ev_edge_or_market_decision_fields"]["actual"], [])
        self.assertEqual(audit["mismatches"], [])
        self.assertEqual(audit["warnings"], [])
        self.assertEqual(audit["paper_orders_created"], 0)
        self.assertEqual(audit["autonomous_actions_created"], 0)
        self.assertEqual(audit["next_safe_action"], "ready_for_integration_review")

        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["audit_status"], "batch_audit_passed")
        self.assertEqual(result["counts"]["checks_failed"], 0)
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertEqual(result["autonomous_actions_created"], 0)
        self.assertEqual(result["blockers"], [])
        if not (ROOT / "docs" / "PMBOT_INFRA_008_RESULT.json").exists():
            self.assertIn("docs/PMBOT_INFRA_008_RESULT.json", result["missing_optional_docs"])

    def test_outputs_are_deterministic_and_new_json_artifacts_parse(self):
        first = _run_audit().stdout
        first_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        first_markdown = AUDIT_MD.read_text(encoding="utf-8")
        second = _run_audit().stdout
        second_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        second_markdown = AUDIT_MD.read_text(encoding="utf-8")

        self.assertEqual(first, second)
        self.assertEqual(first_payloads, second_payloads)
        self.assertEqual(first_markdown, second_markdown)
        self.assertEqual(_load_json(AUDIT), _load_json(AUDIT_EXPECTED))
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)

    def test_runner_detects_batch_mismatches(self):
        _run_audit()
        module = _load_module()
        artifacts = module._load_artifacts()

        audit = _build_audit_with_mutated_batch(
            module,
            artifacts,
            lambda payload: payload["paper_accounting_totals"].update(
                {"paper_accounting_cumulative_pnl": "99.00"}
            ),
        )
        checks = _checks_by_id(audit)
        self.assertEqual(audit["audit_status"], "batch_audit_failed")
        self.assertEqual(checks["pnl_aggregation_consistency"]["status"], "fail")

        audit = _build_audit_with_mutated_batch(
            module,
            artifacts,
            lambda payload: payload["paper_accounting_records"][1].update(
                {"ledger_market_id": "unexpected-market"}
            ),
        )
        checks = _checks_by_id(audit)
        self.assertEqual(audit["audit_status"], "batch_audit_failed")
        self.assertEqual(checks["market_id_consistency"]["status"], "fail")

        audit = _build_audit_with_mutated_batch(
            module,
            artifacts,
            lambda payload: payload["paper_accounting_records"][2].update(
                {"settlement_source_id": "unexpected-open-settlement"}
            ),
        )
        checks = _checks_by_id(audit)
        self.assertEqual(audit["audit_status"], "batch_audit_failed")
        self.assertEqual(checks["open_settled_status_consistency"]["status"], "fail")

        audit = _build_audit_with_mutated_batch(
            module,
            artifacts,
            lambda payload: payload["paper_accounting_records"][0].update({"ev": "1.00"}),
        )
        checks = _checks_by_id(audit)
        self.assertEqual(audit["audit_status"], "batch_audit_failed")
        self.assertEqual(
            checks["no_scoring_probability_ev_edge_or_market_decision_fields"]["status"],
            "fail",
        )
        self.assertIn(
            "paper_accounting_batch_input:paper_accounting_records[0].ev",
            checks["no_scoring_probability_ev_edge_or_market_decision_fields"]["actual"],
        )

        audit = _build_audit_with_mutated_batch(
            module,
            artifacts,
            lambda payload: payload["paper_accounting_records"][0].update({"generated_by_bot": True}),
        )
        checks = _checks_by_id(audit)
        self.assertEqual(audit["audit_status"], "batch_audit_failed")
        self.assertEqual(checks["safety_flag_consistency"]["status"], "fail")

    def test_boundary_safety_no_forbidden_imports_calls_or_order_artifacts(self):
        _run_audit()
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

        audit = _load_json(AUDIT)
        self.assertFalse(audit["safety_flags"]["runtime_wiring"])
        self.assertFalse(audit["safety_flags"]["network_api"])
        self.assertFalse(audit["safety_flags"]["wallet"])
        self.assertFalse(audit["safety_flags"]["trading"])
        self.assertFalse(audit["safety_flags"]["autonomous_paper_orders"])
        self.assertFalse(audit["safety_flags"]["scoring_probability_ev_edge"])
        self.assertFalse(audit["safety_flags"]["market_decisions"])
        self.assertEqual(audit["paper_orders_created"], 0)
        self.assertEqual(audit["autonomous_actions_created"], 0)

        result = _load_json(RESULT)
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


if __name__ == "__main__":
    unittest.main()

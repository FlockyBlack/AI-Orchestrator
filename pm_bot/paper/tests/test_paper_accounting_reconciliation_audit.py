import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_paper_accounting_reconciliation_audit.py"
AUDIT = ROOT / "pm_bot" / "paper" / "paper_accounting_reconciliation_audit.v1.json"
AUDIT_EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_accounting_reconciliation_audit.v1.json"
AUDIT_MD = ROOT / "pm_bot" / "paper" / "paper_accounting_reconciliation_audit.v1.md"
RESULT = ROOT / "docs" / "PMBOT_PAPER_017_RESULT.json"

NEW_JSON_FILES = [
    AUDIT,
    AUDIT_EXPECTED,
    RESULT,
]


def _frag(*parts):
    return "".join(parts)


def _run_audit():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_accounting_reconciliation_audit", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _check_by_id(audit):
    return {check["check_id"]: check for check in audit["checks"]}


class PaperAccountingReconciliationAuditTests(unittest.TestCase):
    def test_paper_017_reconciles_current_accounting_lifecycle(self):
        _run_audit()
        audit = _load_json(AUDIT)
        result = _load_json(RESULT)

        self.assertEqual(audit, _load_json(AUDIT_EXPECTED))
        self.assertEqual(audit["task_id"], "PMBOT-PAPER-017-PAPER-ACCOUNTING-RECONCILIATION-LIFECYCLE-AUDIT")
        self.assertEqual(audit["market_id"], "824952")
        self.assertEqual(audit["audit_status"], "reconciliation_passed")
        self.assertEqual(len(audit["artifacts_checked"]), 14)
        self.assertEqual(len(audit["checks"]), 14)
        self.assertTrue(all(check["status"] == "pass" for check in audit["checks"]))
        self.assertEqual(audit["mismatches"], [])
        self.assertEqual(audit["warnings"], [])
        self.assertEqual(audit["paper_orders_created"], 0)
        self.assertEqual(audit["autonomous_actions_created"], 0)
        self.assertEqual(audit["next_safe_action"], "ready_for_integration_review")

        summary = audit["accounting_summary"]
        self.assertEqual(summary["paper_accounting_total_records"], 1)
        self.assertEqual(summary["settled_count"], 1)
        self.assertEqual(summary["open_count"], 0)
        self.assertEqual(summary["win_count"], 1)
        self.assertEqual(summary["loss_count"], 0)
        self.assertEqual(summary["flat_count"], 0)
        self.assertEqual(summary["cumulative_pnl"], "6.00")
        self.assertEqual(summary["gross_profit"], "6.00")
        self.assertEqual(summary["gross_loss"], "0.00")
        self.assertEqual(summary["average_pnl"], "6.00")
        self.assertEqual(summary["max_gain"], "6.00")
        self.assertEqual(summary["max_loss"], "0.00")

        checks = _check_by_id(audit)
        self.assertEqual(checks["market_id_consistency"]["actual"]["paper_metrics_report"], ["824952"])
        self.assertEqual(checks["accepted_lifecycle_record_count_consistency"]["actual"]["metrics_records"], 1)
        self.assertEqual(checks["pnl_value_consistency"]["actual"], [])
        self.assertEqual(checks["safety_flag_consistency"]["actual"], [])
        self.assertEqual(checks["no_scoring_probability_ev_edge_or_recommendation_fields"]["actual"], [])

        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["audit_status"], "reconciliation_passed")
        self.assertEqual(result["counts"]["paper_orders_created"], 0)
        self.assertEqual(result["counts"]["autonomous_actions_created"], 0)
        self.assertEqual(result["blockers"], [])
        if not (ROOT / "docs" / "PMBOT_INFRA_006_RESULT.json").exists():
            self.assertEqual(result["missing_optional_docs"], ["docs/PMBOT_INFRA_006_RESULT.json"])

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

    def test_runner_detects_metrics_pointer_and_forbidden_active_field_mismatches(self):
        _run_audit()
        module = _load_module()

        artifacts = module._load_artifacts()
        artifacts["paper_metrics_report"]["payload"]["paper_accounting_metrics"][
            "paper_accounting_cumulative_pnl"
        ] = "7.00"
        audit = module.build_reconciliation_audit(artifacts)
        checks = _check_by_id(audit)
        self.assertEqual(audit["audit_status"], "reconciliation_failed")
        self.assertEqual(checks["portfolio_metrics_consistency"]["status"], "fail")

        artifacts = module._load_artifacts()
        artifacts["paper_accounting_pnl_preview"]["payload"]["source_paper_fill_events_path"] = (
            "pm_bot/paper/unexpected_fill_events.v1.json"
        )
        audit = module.build_reconciliation_audit(artifacts)
        checks = _check_by_id(audit)
        self.assertEqual(audit["audit_status"], "reconciliation_failed")
        self.assertEqual(checks["artifact_pointer_consistency"]["status"], "fail")

        artifacts = module._load_artifacts()
        artifacts["paper_accounting_pnl_preview"]["payload"]["paper_accounting_records"][0]["ev"] = "1.00"
        audit = module.build_reconciliation_audit(artifacts)
        checks = _check_by_id(audit)
        self.assertEqual(audit["audit_status"], "reconciliation_failed")
        self.assertEqual(checks["no_scoring_probability_ev_edge_or_recommendation_fields"]["status"], "fail")
        self.assertIn(
            "paper_accounting_pnl_preview:paper_accounting_records[0].ev",
            checks["no_scoring_probability_ev_edge_or_recommendation_fields"]["actual"],
        )

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


if __name__ == "__main__":
    unittest.main()

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "dashboard" / "export_static_operator_report.py"
HTML_REPORT = ROOT / "pm_bot" / "dashboard" / "static_operator_report.v1.html"
SUMMARY_JSON = ROOT / "pm_bot" / "dashboard" / "static_operator_report_summary.v1.json"
EXPECTED_SUMMARY_JSON = ROOT / "pm_bot" / "dashboard" / "expected_static_operator_report_summary.v1.json"
RESULT = ROOT / "docs" / "PMBOT_DASHBOARD_003_RESULT.json"

NEW_JSON_FILES = [
    SUMMARY_JSON,
    EXPECTED_SUMMARY_JSON,
    RESULT,
]

FORBIDDEN_IMPORTS = {
    "aiohttp",
    "flask",
    "httpx",
    "requests",
    "selenium",
    "socket",
    "urllib",
    "webbrowser",
    "websockets",
}


def _frag(*parts):
    return "".join(parts)


def _run_exporter():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("static_operator_report", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_json(root, relative, payload):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_minimal_required_sources(root):
    _write_json(
        root,
        "pm_bot/workbench/operator_review_pack.v1.json",
        {
            "schema_version": "operator_review_pack.v1",
            "generated_by": "pm_bot/workbench/export_operator_review_pack.py",
            "artifact_inventory": {
                "summary": {
                    "total_artifacts": 1,
                    "present_artifacts": 1,
                    "missing_artifacts": 0,
                    "required_missing_artifacts": 0,
                    "json_artifacts_parsed": 1,
                    "json_artifacts_parse_failed": 0,
                }
            },
            "quality_warning_summary": {
                "quality_report_status": "health_passed_with_warnings",
                "quality_report_load_status": "parsed",
                "total_warnings": 1,
                "blocking_warnings": 0,
                "action_required_warnings": 1,
                "review_needed_warnings": 0,
                "informational_warnings": 0,
                "blocking_warning_detected": False,
                "top_warning_categories": [],
                "warning_categories": [],
                "operator_summary": "No blocking warnings detected.",
                "recommended_manual_action": "Review action_required warnings.",
            },
            "operator_inbox_summary": {
                "schema_version": "manual_command_inbox_review.v1",
                "records_seen": 1,
                "accepted_count": 1,
                "rejected_count": 0,
                "needs_human_review_count": 0,
                "execution_authority": False,
                "commands_executed": 0,
                "orders_created": 0,
                "network_calls": 0,
                "next_safe_action": "human_review_queue_only",
            },
            "next_safe_manual_actions": [
                {
                    "action_id": "review_static_report",
                    "description": "Review static report only.",
                    "non_trading_action": True,
                    "requires_runtime": False,
                    "creates_orders": False,
                }
            ],
            "warnings": [],
            "missing_artifacts": [],
            "paper_orders_created": 0,
            "commands_executed": 0,
            "network_calls": 0,
        },
    )
    _write_json(
        root,
        "pm_bot/workbench/operator_workbench_export_run.v1.json",
        {
            "schema_version": "operator_workbench_export_run.v1",
            "required_steps_passed": True,
            "warnings": [],
        },
    )
    _write_json(
        root,
        "pm_bot/quality/artifact_health_report.v1.json",
        {
            "schema_version": "artifact_health_report.v1",
            "report_status": "health_passed_with_warnings",
            "artifacts_checked": 1,
            "artifacts_present_count": 1,
            "artifacts_missing_count": 0,
            "json_parse_pass_count": 1,
            "json_parse_fail_count": 0,
            "schema_version_missing_count": 0,
            "embedded_artifact_pointer_summary": {
                "checked_count": 0,
                "present_count": 0,
                "missing_count": 0,
                "absolute_count": 0,
            },
            "expected_fixture_alignment_summary": {
                "checks_total": 0,
                "aligned_count": 0,
                "mismatch_count": 0,
                "actual_missing_count": 0,
            },
            "warning_severity_summary": {
                "total_warnings": 1,
                "blocking_count": 0,
                "action_required_count": 1,
                "review_needed_count": 0,
                "informational_count": 0,
                "blocking_warning_detected": False,
                "top_warning_categories": [],
                "warning_categories": [],
                "operator_summary": "No blocking warnings detected.",
                "recommended_manual_action": "Review action_required warnings.",
            },
        },
    )
    _write_json(
        root,
        "pm_bot/paper/multi_market_paper_run_series.v1.json",
        {
            "schema_version": "multi_market_paper_run_series.v1",
            "series_status": "series_run_passed",
            "markets_seen": 5,
            "records_seen": 5,
            "records_processed": 4,
            "records_by_status": {
                "accepted_accounting_record": 3,
                "blocked_fixture_record": 1,
                "manual_review_only": 1,
            },
            "accounting_summary": {
                "paper_accounting_total_records": 4,
                "paper_accounting_settled_count": 3,
                "paper_accounting_open_count": 1,
                "paper_accounting_cumulative_pnl": "-1.00",
                "paper_accounting_average_settled_pnl": "-0.33",
            },
            "lifecycle_summary": {
                "blocked_records": 1,
                "manual_review_only_records": 1,
                "blocked_or_rejected_records": 1,
            },
            "safety_flags": {
                "autonomous_paper_orders": False,
            },
            "real_orders_created": 0,
            "network_calls": 0,
            "commands_executed": 0,
            "autonomous_decisions": 0,
        },
    )
    _write_json(
        root,
        "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
        {
            "schema_version": "portfolio_audit_state_preview.v1",
            "dashboard_state_export_version": "v2",
            "product_stage_summary": {
                "current_known_portfolio_audit_status": "paper_017_reconciliation_available"
            },
            "known_market_ids": ["test-market"],
            "portfolio_accounting_summary": {
                "summary_status": "portfolio_accounting_state_ready",
                "accounting_boundary": {
                    "warning": "Paper accounting PnL is fixture/manual accounting only and is not strategy profitability."
                },
            },
        },
    )
    _write_json(
        root,
        "pm_bot/operator/manual_command_inbox_review.v1.json",
        {
            "schema_version": "manual_command_inbox_review.v1",
            "records_seen": 1,
            "accepted_count": 1,
            "rejected_count": 0,
            "needs_human_review_count": 0,
            "execution_authority": False,
            "commands_executed": 0,
            "orders_created": 0,
            "network_calls": 0,
            "next_safe_action": "human_review_queue_only",
        },
    )


class StaticOperatorReportTests(unittest.TestCase):
    def test_exporter_creates_html_summary_expected_fixture_and_result_doc(self):
        result = json.loads(_run_exporter().stdout)

        self.assertEqual(result["task_id"], "PMBOT-DASHBOARD-003-STATIC-HTML-OPERATOR-REPORT")
        self.assertEqual(result["report_status"], "static_report_generated")
        self.assertTrue(HTML_REPORT.exists())
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)

    def test_summary_json_matches_expected_fixture(self):
        _run_exporter()

        self.assertEqual(_load_json(SUMMARY_JSON), _load_json(EXPECTED_SUMMARY_JSON))

    def test_html_includes_paper_019_section_and_accounting_only_warning_near_pnl(self):
        _run_exporter()
        html = HTML_REPORT.read_text(encoding="utf-8")
        pnl_index = html.index("cumulative_pnl")
        warning_index = html.index("Accounting-only warning near PnL")

        self.assertIn("PAPER-019 Multi-Market Paper Run Series", html)
        self.assertIn("markets_seen", html)
        self.assertIn("records_seen", html)
        self.assertIn("records_processed", html)
        self.assertIn("-1.00", html)
        self.assertLess(abs(warning_index - pnl_index), 1200)
        self.assertIn("Paper accounting PnL is fixture/manual accounting only", html)
        self.assertIn("not strategy profitability", html)

    def test_html_includes_quality_severity_summary_and_artifact_health(self):
        _run_exporter()
        html = HTML_REPORT.read_text(encoding="utf-8")

        self.assertIn("Quality Warning Severity Summary", html)
        self.assertIn("total_warnings", html)
        self.assertIn("blocking", html)
        self.assertIn("action_required", html)
        self.assertIn("review_needed", html)
        self.assertIn("informational", html)
        self.assertIn("blocking_warning_detected", html)
        self.assertIn("Artifact Health Summary", html)

    def test_html_includes_safety_boundaries_and_no_runtime_surfaces(self):
        _run_exporter()
        html = HTML_REPORT.read_text(encoding="utf-8")

        self.assertIn("Safety And Forbidden Capabilities", html)
        self.assertIn("runtime_wiring", html)
        self.assertIn("network_api", html)
        self.assertIn("wallet", html)
        self.assertIn("trading", html)
        self.assertIn("autonomous_paper_orders", html)
        self.assertIn("scoring_probability_ev_edge", html)
        self.assertIn("dashboard_server", html)
        self.assertIn("frontend_runtime", html)
        self.assertIn("browser_automation", html)
        self.assertIn("Forbidden Capabilities", html)

    def test_html_has_no_external_network_references_or_script_tags(self):
        _run_exporter()
        html = HTML_REPORT.read_text(encoding="utf-8").lower()

        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("</script", html)

    def test_summary_contains_required_static_report_fields_and_safety_counters(self):
        _run_exporter()
        summary = _load_json(SUMMARY_JSON)

        self.assertEqual(summary["schema_version"], "static_operator_report_summary.v1")
        self.assertEqual(summary["task_id"], "PMBOT-DASHBOARD-003-STATIC-HTML-OPERATOR-REPORT")
        self.assertEqual(summary["html_report_path"], "pm_bot/dashboard/static_operator_report.v1.html")
        self.assertIn("paper_019_multi_market_paper_run_series", summary["sections_rendered"])
        self.assertEqual(summary["paper_019_summary"]["markets_seen"], 5)
        self.assertEqual(summary["paper_019_summary"]["records_seen"], 5)
        self.assertEqual(summary["paper_019_summary"]["records_processed"], 4)
        self.assertEqual(summary["paper_019_summary"]["cumulative_pnl"], "-1.00")
        self.assertEqual(summary["network_calls"], 0)
        self.assertEqual(summary["commands_executed"], 0)
        self.assertEqual(summary["orders_created"], 0)
        self.assertEqual(summary["autonomous_decisions"], 0)
        self.assertFalse(summary["safety_flags"]["runtime_wiring"])
        self.assertFalse(summary["safety_flags"]["network_api"])
        self.assertFalse(summary["safety_flags"]["trading"])
        self.assertFalse(summary["safety_flags"]["market_decisions"])

    def test_missing_optional_artifacts_are_handled_deterministically(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            _write_minimal_required_sources(temp_root)
            summary = module.build_static_operator_report(temp_root)

        self.assertEqual(summary["report_status"], "static_report_generated_with_warnings")
        self.assertEqual(summary["warnings"]["required_source_problems"], [])
        self.assertIn("docs/PMBOT_WORKBENCH_005_RESULT.json", summary["warnings"]["missing_optional_artifacts"])
        self.assertIn("docs/PMBOT_WORKBENCH_002_OPERATOR_QUICKSTART.md", summary["warnings"]["missing_optional_artifacts"])
        self.assertEqual(summary["paper_019_summary"]["markets_seen"], 5)
        self.assertEqual(summary["network_calls"], 0)
        self.assertEqual(summary["commands_executed"], 0)
        self.assertEqual(summary["orders_created"], 0)

    def test_runner_uses_standard_library_and_no_runtime_network_or_server_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "html", "json", "pathlib", "sys"})
        self.assertTrue(imports.isdisjoint(FORBIDDEN_IMPORTS))

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("import", "httpx"),
            _frag("httpx", "."),
            _frag("urllib", ".", "request"),
            _frag("webbrowser", "."),
            _frag("selenium", "."),
            _frag("submit", "_", "order", "("),
            _frag("execute", "_", "trade", "("),
            _frag("place", "_", "order", "("),
            _frag("scripts", "/", "dispatcher", ".", "py"),
            _frag("scripts", "/", "run", "_", "codex", ".", "py"),
        ]
        for term in forbidden_call_terms:
            self.assertNotIn(term, source_no_spaces)


if __name__ == "__main__":
    unittest.main()

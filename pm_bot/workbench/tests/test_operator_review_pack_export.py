import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "workbench" / "export_operator_review_pack.py"
PACK_JSON = ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.json"
PACK_MD = ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.md"
EXPECTED_JSON = ROOT / "pm_bot" / "workbench" / "expected_operator_review_pack.v1.json"
RESULT = ROOT / "docs" / "PMBOT_WORKBENCH_001_RESULT.json"
LANE_RESULT = ROOT / "docs" / "PMBOT_CODEX_A_ROUND003_RESULT.json"

NEW_JSON_FILES = [
    PACK_JSON,
    EXPECTED_JSON,
    RESULT,
    LANE_RESULT,
]


def _frag(*parts):
    return "".join(parts)


def _run_write():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("operator_review_pack_export", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OperatorReviewPackExportTests(unittest.TestCase):
    def test_write_exports_pack_markdown_expected_and_result_docs(self):
        result = json.loads(_run_write().stdout)

        self.assertEqual(result["task_id"], "PMBOT-WORKBENCH-001-OPERATOR-REVIEW-PACK-EXPORT")
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["required_missing_artifacts"], 0)
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertEqual(result["commands_executed"], 0)
        self.assertEqual(result["network_calls"], 0)
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)
        self.assertTrue(PACK_MD.exists())

    def test_pack_json_matches_expected_fixture_and_default_stdout(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        expected = _load_json(EXPECTED_JSON)
        stdout_pack = json.loads(_run_json().stdout)

        self.assertEqual(pack, expected)
        self.assertEqual(stdout_pack, expected)

    def test_pack_contains_required_sections_and_boundary_statements(self):
        _run_write()
        pack = _load_json(PACK_JSON)

        self.assertEqual(pack["schema_version"], "operator_review_pack.v1")
        self.assertEqual(pack["generated_by"], "pm_bot/workbench/export_operator_review_pack.py")
        self.assertFalse(pack["generated_at_policy"]["wall_clock_time_used"])
        for key in (
            "product_stage_summary",
            "artifact_inventory",
            "paper_audit_summary",
            "portfolio_accounting_summary",
            "paper_019_multi_market_run_series",
            "paper_020_paper_run_series_postmortem",
            "dashboard_state_summary",
            "operator_inbox_summary",
            "quality_warning_summary",
            "warnings",
            "missing_artifacts",
            "safety_flags",
            "forbidden_capabilities",
            "next_safe_manual_actions",
        ):
            self.assertIn(key, pack)

        self.assertIn("not strategy profitability", pack["accounting_only_interpretation_warning"])
        self.assertIn("does not recommend markets", pack["no_recommendations_or_decisions_statement"])
        self.assertEqual(pack["paper_orders_created"], 0)
        self.assertEqual(pack["commands_executed"], 0)
        self.assertEqual(pack["network_calls"], 0)

    def test_quality_warning_summary_surfaces_artifact_health_severity_counts(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        quality_summary = pack["quality_warning_summary"]

        self.assertEqual(quality_summary["quality_report_status"], "health_passed_with_warnings")
        self.assertEqual(quality_summary["quality_report_load_status"], "parsed")
        self.assertEqual(
            quality_summary["total_warnings"],
            quality_summary["blocking_warnings"]
            + quality_summary["action_required_warnings"]
            + quality_summary["review_needed_warnings"]
            + quality_summary["informational_warnings"],
        )
        self.assertEqual(quality_summary["blocking_warnings"], 0)
        self.assertFalse(quality_summary["blocking_warning_detected"])
        self.assertGreater(quality_summary["action_required_warnings"], 0)
        self.assertGreater(quality_summary["review_needed_warnings"], 0)
        self.assertGreater(quality_summary["informational_warnings"], 0)
        self.assertIn("blocking means stop and repair", quality_summary["severity_interpretation"]["blocking"])
        self.assertIn(
            "action_required means review before relying",
            quality_summary["severity_interpretation"]["action_required"],
        )

    def test_inventory_reports_required_sources_and_optional_missing_artifacts(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        inventory = {item["artifact_id"]: item for item in pack["artifact_inventory"]["artifacts"]}

        self.assertEqual(pack["artifact_inventory"]["summary"]["required_missing_artifacts"], 0)
        self.assertTrue(inventory["paper_accounting_reconciliation_audit"]["present"])
        self.assertTrue(inventory["paper_accounting_batch_audit"]["present"])
        self.assertTrue(inventory["paper_019_result"]["present"])
        self.assertTrue(inventory["paper_019_multi_market_run_series"]["present"])
        self.assertTrue(inventory["paper_020_result"]["present"])
        self.assertTrue(inventory["paper_020_paper_run_series_postmortem"]["present"])
        self.assertTrue(inventory["portfolio_audit_state_preview"]["present"])
        self.assertTrue(inventory["manual_command_inbox_review"]["present"])
        self.assertEqual(inventory["paper_019_result"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_019_multi_market_run_series"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_020_result"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_020_paper_run_series_postmortem"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_accounting_batch_audit"]["parse_status"], "parsed")
        self.assertEqual(
            inventory["paper_019_multi_market_run_series"]["path"],
            "pm_bot/paper/multi_market_paper_run_series.v1.json",
        )
        self.assertEqual(
            inventory["paper_020_paper_run_series_postmortem"]["path"],
            "pm_bot/paper/paper_run_series_postmortem.v1.json",
        )
        self.assertEqual(
            inventory["paper_accounting_batch_audit"]["path"],
            "pm_bot/paper/paper_accounting_batch_audit.v1.json",
        )

        missing = {item["path"]: item for item in pack["missing_artifacts"]}
        for path in (
            "docs/PMBOT_INFRA_009_RESULT.json",
            "docs/PMBOT_INFRA_009_ABC_ROUND003_WORKTREE_MATERIALIZATION.md",
        ):
            if not (ROOT / path).exists():
                self.assertIn(path, missing)
                self.assertFalse(missing[path]["required"])
        self.assertTrue(all(not item["required"] for item in pack["missing_artifacts"]))

    def test_audit_dashboard_portfolio_and_inbox_summaries_are_explicit(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        paper = pack["paper_audit_summary"]
        portfolio = pack["portfolio_accounting_summary"]
        dashboard = pack["dashboard_state_summary"]
        inbox = pack["operator_inbox_summary"]

        self.assertEqual(paper["reconciliation_audit"]["audit_status"], "reconciliation_passed")
        self.assertEqual(paper["reconciliation_audit"]["counts"]["checks_failed"], 0)
        self.assertEqual(paper["batch_audit"]["audit_status"], "batch_audit_passed")
        self.assertEqual(paper["batch_audit"]["counts"]["records_audited"], 3)
        self.assertEqual(paper["batch_audit"]["counts"]["checks_failed"], 0)
        self.assertEqual(
            paper["audits_passed"],
            [
                {
                    "artifact_id": "paper_accounting_reconciliation_audit",
                    "audit_status": "reconciliation_passed",
                },
                {
                    "artifact_id": "paper_accounting_batch_audit",
                    "audit_status": "batch_audit_passed",
                },
            ],
        )

        self.assertEqual(portfolio["summary_status"], "portfolio_accounting_state_ready")
        self.assertEqual(portfolio["accepted_accounting_market_ids"], ["824952"])
        self.assertTrue(portfolio["interpretation_boundary"]["paper_accounting_only"])
        self.assertFalse(portfolio["interpretation_boundary"]["strategy_profitability"])
        self.assertEqual(dashboard["schema_version"], "portfolio_audit_state_preview.v1")
        self.assertFalse(dashboard["implementation_boundary"]["runtime_wiring"])
        self.assertEqual(inbox["records_seen"], 7)
        self.assertEqual(inbox["accepted_count"], 3)
        self.assertEqual(inbox["rejected_count"], 3)
        self.assertEqual(inbox["needs_human_review_count"], 1)
        self.assertFalse(inbox["execution_authority"])
        self.assertEqual(inbox["commands_executed"], 0)

    def test_paper_019_multi_market_run_series_summary_is_visible_and_accounting_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        paper_019 = pack["paper_019_multi_market_run_series"]

        self.assertEqual(paper_019["section_id"], "paper_019_multi_market_run_series")
        self.assertEqual(paper_019["artifact_status"], "present")
        self.assertEqual(
            paper_019["artifact_pointer"],
            "pm_bot/paper/multi_market_paper_run_series.v1.json",
        )
        self.assertEqual(paper_019["artifact_parse_status"], "parsed")
        self.assertEqual(paper_019["series_status"], "series_run_passed")
        self.assertEqual(paper_019["markets_seen"], 5)
        self.assertEqual(paper_019["records_seen"], 5)
        self.assertEqual(paper_019["records_processed"], 4)
        self.assertEqual(
            paper_019["records_by_status"],
            {
                "accepted_accounting_record": 3,
                "blocked_fixture_record": 1,
                "manual_review_only": 1,
            },
        )
        self.assertEqual(
            paper_019["accounting_summary"]["paper_accounting_cumulative_pnl"],
            "-1.00",
        )
        self.assertEqual(
            paper_019["accounting_summary"]["paper_accounting_average_settled_pnl"],
            "-0.33",
        )

        blocked_manual = paper_019["blocked_or_manual_review_summary"]
        self.assertEqual(blocked_manual["blocked_fixture_record_count"], 1)
        self.assertEqual(blocked_manual["manual_review_only_count"], 1)
        self.assertEqual(blocked_manual["blocked_or_rejected_records"], 1)
        self.assertEqual(blocked_manual["manual_review_only_records"], 1)
        self.assertEqual(
            [record["processing_status"] for record in blocked_manual["records"]],
            ["manual_review_only", "blocked_fixture_record"],
        )
        self.assertIn(
            "fixture/accounting-only outputs",
            paper_019["interpretation_warning"],
        )
        self.assertIn("not strategy profitability", paper_019["interpretation_warning"])
        self.assertIn("recommendation, EV, edge, probability", paper_019["interpretation_warning"])
        self.assertEqual(
            paper_019["safety_counters"],
            {
                "real_orders_created": 0,
                "autonomous_paper_orders": 0,
                "network_calls": 0,
                "commands_executed": 0,
                "autonomous_decisions": 0,
            },
        )

    def test_paper_020_postmortem_summary_is_visible_and_accounting_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        paper_020 = pack["paper_020_paper_run_series_postmortem"]

        self.assertEqual(paper_020["section_id"], "paper_020_paper_run_series_postmortem")
        self.assertEqual(paper_020["artifact_status"], "present")
        self.assertEqual(
            paper_020["artifact_pointer"],
            "pm_bot/paper/paper_run_series_postmortem.v1.json",
        )
        self.assertEqual(paper_020["artifact_parse_status"], "parsed")
        self.assertEqual(paper_020["postmortem_status"], "postmortem_completed")
        self.assertTrue(paper_020["source_paper_019_found"])
        self.assertEqual(paper_020["source_paper_019"]["series_status"], "series_run_passed")
        self.assertEqual(paper_020["source_paper_019"]["markets_seen"], 5)
        self.assertEqual(paper_020["source_paper_019"]["records_seen"], 5)
        self.assertEqual(paper_020["source_paper_019"]["records_processed"], 4)
        self.assertEqual(paper_020["cumulative_pnl"], "-1.00")
        self.assertTrue(paper_020["accounting_only_warning_present"])
        self.assertIn("not strategy profitability", paper_020["accounting_only_warning"])
        self.assertIn("EV, probability estimate", paper_020["accounting_only_warning"])
        self.assertEqual(
            paper_020["records_by_status"],
            {
                "accepted_accounting_record": 3,
                "blocked_fixture_record": 1,
                "manual_review_only": 1,
            },
        )
        self.assertEqual(
            [item["processing_status"] for item in paper_020["record_status_notes"]],
            ["accepted_accounting_record", "manual_review_only", "blocked_fixture_record"],
        )
        self.assertGreaterEqual(len(paper_020["fixture_limitations"]), 5)
        self.assertGreaterEqual(len(paper_020["recommended_next_fixture_expansions"]), 4)
        self.assertEqual(
            paper_020["safety_counters"],
            {
                "real_orders_created": 0,
                "autonomous_paper_orders": 0,
                "network_calls": 0,
                "commands_executed": 0,
                "autonomous_decisions": 0,
            },
        )
        self.assertEqual(
            paper_020["next_safe_action"],
            "PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW",
        )

    def test_paper_019_missing_artifact_remains_non_blocking_warning(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            pack = module.build_operator_review_pack(Path(directory))

        paper_019 = pack["paper_019_multi_market_run_series"]
        paper_020 = pack["paper_020_paper_run_series_postmortem"]
        warnings = {item["warning_id"]: item for item in pack["warnings"]}

        self.assertEqual(paper_019["artifact_status"], "missing")
        self.assertEqual(paper_019["artifact_pointer"], "pm_bot/paper/multi_market_paper_run_series.v1.json")
        self.assertEqual(paper_019["markets_seen"], 0)
        self.assertEqual(paper_019["records_seen"], 0)
        self.assertEqual(paper_019["records_processed"], 0)
        self.assertEqual(paper_019["records_by_status"], {})
        self.assertEqual(paper_019["accounting_summary"], {})
        self.assertEqual(paper_019["blocked_or_manual_review_summary"]["records"], [])
        self.assertEqual(paper_019["safety_counters"]["network_calls"], 0)
        self.assertIn("paper_019_multi_market_run_series_missing", warnings)
        self.assertEqual(
            warnings["paper_019_multi_market_run_series_missing"]["category"],
            "optional_artifact_missing",
        )
        self.assertEqual(paper_020["artifact_status"], "missing")
        self.assertEqual(paper_020["artifact_pointer"], "pm_bot/paper/paper_run_series_postmortem.v1.json")
        self.assertFalse(paper_020["source_paper_019_found"])
        self.assertEqual(paper_020["source_paper_019"]["markets_seen"], 0)
        self.assertEqual(paper_020["source_paper_019"]["records_seen"], 0)
        self.assertEqual(paper_020["source_paper_019"]["records_processed"], 0)
        self.assertEqual(paper_020["records_by_status"], {})
        self.assertEqual(paper_020["safety_counters"]["network_calls"], 0)
        self.assertIn("paper_020_paper_run_series_postmortem_missing", warnings)
        self.assertEqual(
            warnings["paper_020_paper_run_series_postmortem_missing"]["category"],
            "optional_artifact_missing",
        )

    def test_warnings_safety_flags_and_next_actions_remain_review_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        warnings = {item["warning_id"]: item["message"] for item in pack["warnings"]}
        safety = pack["safety_flags"]

        self.assertIn("accounting_only_interpretation", warnings)
        self.assertIn("no_recommendations_or_decisions", warnings)
        self.assertIn("local artifacts only", warnings["local_artifacts_only"])
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["local_file_reads_only"])
        self.assertFalse(safety["runtime_wiring"])
        self.assertFalse(safety["network_api"])
        self.assertFalse(safety["wallet"])
        self.assertFalse(safety["trading"])
        self.assertFalse(safety["autonomous_paper_orders"])
        self.assertFalse(safety["scoring_probability_ev_edge"])
        self.assertFalse(safety["market_decisions"])
        self.assertFalse(safety["command_execution"])
        self.assertTrue(all(action["non_trading_action"] for action in pack["next_safe_manual_actions"]))
        self.assertTrue(all(not action["requires_runtime"] for action in pack["next_safe_manual_actions"]))
        self.assertTrue(all(not action["creates_orders"] for action in pack["next_safe_manual_actions"]))

    def test_markdown_matches_cli_output(self):
        _run_write()
        markdown = PACK_MD.read_text(encoding="utf-8")

        self.assertEqual(_run_markdown().stdout, markdown)
        self.assertIn("PMBOT Operator Review Pack v1", markdown)
        self.assertIn("paper_orders_created: 0", markdown)
        self.assertIn("commands_executed: 0", markdown)
        self.assertIn("network_calls: 0", markdown)
        self.assertIn("Quality Warning Summary", markdown)
        self.assertIn("blocking means stop and repair", markdown)
        self.assertIn("PAPER-019 Multi-Market Run Series", markdown)
        self.assertIn("section_id: paper_019_multi_market_run_series", markdown)
        self.assertIn("markets_seen: 5", markdown)
        self.assertIn("paper_accounting_cumulative_pnl: -1.00", markdown)
        self.assertIn("PAPER-019 values are deterministic fixture/accounting-only outputs", markdown)
        self.assertIn("PAPER-020 Paper Run Series Postmortem", markdown)
        self.assertIn("section_id: paper_020_paper_run_series_postmortem", markdown)
        self.assertIn("postmortem_status: postmortem_completed", markdown)
        self.assertIn("source_paper_019_found: true", markdown)
        self.assertIn("cumulative_pnl: -1.00", markdown)
        self.assertIn("PAPER-019 PnL is accounting-only fixture output", markdown)
        self.assertIn("PAPER-020 Fixture Limitations", markdown)
        self.assertIn("PAPER-020 Recommended Next Fixture Expansions", markdown)
        self.assertIn("autonomous_paper_orders: 0", markdown)
        self.assertIn("Paper accounting PnL is fixture/manual accounting only", markdown)
        self.assertIn("does not recommend markets", markdown)

    def test_result_docs_match_and_report_no_forbidden_changes(self):
        _run_write()
        result = _load_json(RESULT)

        self.assertEqual(result, _load_json(LANE_RESULT))
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["codex_lane"], "CODEX_A")
        self.assertEqual(result["branch"], "codex/a-operator-review-pack-round003")
        self.assertEqual(result["base_commit"], "21edc9af372e9d1736afb0eccd3c016f23f2c144")
        self.assertFalse(result["forbidden_changes_detected"])
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertEqual(result["commands_executed"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["blockers"], [])

    def test_runner_uses_standard_library_and_no_runtime_surfaces(self):
        _run_write()
        module = _load_module()
        self.assertEqual(module.SCHEMA_VERSION, "operator_review_pack.v1")

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
            _frag("urllib", ".", "request"),
            _frag("socket", "."),
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

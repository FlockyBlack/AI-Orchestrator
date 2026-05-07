import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "workbench" / "run_operator_workbench_export.py"
RUN_JSON = ROOT / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.json"
RUN_MD = ROOT / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.md"
EXPECTED_RUN_JSON = ROOT / "pm_bot" / "workbench" / "expected_operator_workbench_export_run.v1.json"
RESULT = ROOT / "docs" / "PMBOT_WORKBENCH_003_RESULT.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("operator_workbench_export_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_fake_exporter(path, function_name, order_name, reported_status=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    status = reported_status or f"{order_name}_exported"
    path.write_text(
        f"""import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _record(name):
    path = ROOT / "order.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    data.append(name)
    path.write_text(json.dumps(data), encoding="utf-8")


def {function_name}():
    _record("{order_name}")
    return {{"status": "{status}"}}
""",
        encoding="utf-8",
    )


def _write_fake_inbox_exporter(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _record(name):
    path = ROOT / "order.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    data.append(name)
    path.write_text(json.dumps(data), encoding="utf-8")


def review_manual_command_inbox(root, inbox_path):
    _record("inbox")
    return {
        "task_id": "PMBOT-FAKE-INBOX",
        "records_seen": 1,
        "accepted_count": 1,
        "rejected_count": 0,
        "needs_human_review_count": 0,
        "commands_executed": 0,
        "orders_created": 0,
        "network_calls": 0,
    }


def render_markdown(report):
    return "# Fake Inbox Review\\n"
""",
        encoding="utf-8",
    )


def _write_fake_required_failure(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """def write_operator_review_pack_artifacts():
    raise RuntimeError("fake required failure")
""",
        encoding="utf-8",
    )


def _make_fake_root(all_exporters=True, required_failure=False):
    directory = tempfile.TemporaryDirectory()
    temp_root = Path(directory.name)
    if all_exporters:
        _write_fake_exporter(
            temp_root / "pm_bot" / "dashboard" / "export_portfolio_audit_state.py",
            "write_portfolio_audit_state_artifacts",
            "dashboard",
        )
        _write_fake_inbox_exporter(temp_root / "pm_bot" / "operator" / "review_manual_command_inbox.py")
        _write_fake_exporter(
            temp_root / "pm_bot" / "quality" / "export_artifact_health_report.py",
            "write_artifact_health_report",
            "quality",
        )
        _write_fake_exporter(
            temp_root / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.py",
            "write_openrouter_passive_surface_pointer_artifacts",
            "openrouter",
        )
        _write_fake_exporter(
            temp_root / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.py",
            "write_operator_openrouter_review_dashboard_artifacts",
            "openrouter_dashboard",
        )
    if required_failure:
        _write_fake_required_failure(temp_root / "pm_bot" / "workbench" / "export_operator_review_pack.py")
    else:
        _write_fake_exporter(
            temp_root / "pm_bot" / "workbench" / "export_operator_review_pack.py",
            "write_operator_review_pack_artifacts",
            "workbench",
        )
    return directory, temp_root


class OperatorWorkbenchExportRunnerTests(unittest.TestCase):
    def test_runner_identifies_expected_local_exporters(self):
        module = _load_module()
        steps = module.build_export_steps(ROOT)

        self.assertEqual(
            [step["step_id"] for step in steps],
            [
                "portfolio_audit_state",
                "manual_command_inbox_review",
                "artifact_health_report",
                "openrouter_passive_surface_pointer",
                "operator_openrouter_review_dashboard",
                "operator_review_pack",
            ],
        )
        self.assertEqual(
            [step["script_path"] for step in steps],
            [
                "pm_bot/dashboard/export_portfolio_audit_state.py",
                "pm_bot/operator/review_manual_command_inbox.py",
                "pm_bot/quality/export_artifact_health_report.py",
                "pm_bot/workbench/openrouter_passive_surface_pointer.py",
                "pm_bot/workbench/operator_openrouter_review_dashboard.py",
                "pm_bot/workbench/export_operator_review_pack.py",
            ],
        )
        self.assertFalse(steps[0]["required"])
        self.assertFalse(steps[1]["required"])
        self.assertFalse(steps[2]["required"])
        self.assertFalse(steps[3]["required"])
        self.assertFalse(steps[4]["required"])
        self.assertTrue(steps[5]["required"])

    def test_runner_produces_deterministic_summary(self):
        module = _load_module()
        directory, temp_root = _make_fake_root()
        try:
            first = module.run_operator_workbench_export(temp_root)
            second = module.run_operator_workbench_export(temp_root)
            run_json = temp_root / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.json"
            expected_json = temp_root / "pm_bot" / "workbench" / "expected_operator_workbench_export_run.v1.json"

            self.assertEqual(first, second)
            self.assertEqual(json.loads(run_json.read_text(encoding="utf-8")), first)
            self.assertEqual(json.loads(expected_json.read_text(encoding="utf-8")), first)
            self.assertTrue((temp_root / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.md").exists())
            self.assertTrue((temp_root / "docs" / "PMBOT_WORKBENCH_003_RESULT.json").exists())
        finally:
            directory.cleanup()

    def test_runner_runs_workbench_export_after_upstream_local_exports(self):
        module = _load_module()
        directory, temp_root = _make_fake_root()
        try:
            summary = module.run_operator_workbench_export(temp_root)
            order = json.loads((temp_root / "order.json").read_text(encoding="utf-8"))

            self.assertEqual(
                order,
                ["dashboard", "inbox", "quality", "openrouter", "openrouter_dashboard", "workbench"],
            )
            self.assertEqual(
                [step["status"] for step in summary["steps"]],
                ["ran", "ran", "ran", "ran", "ran", "ran"],
            )
            self.assertTrue(summary["required_steps_passed"])
        finally:
            directory.cleanup()

    def test_optional_missing_exporters_are_skipped_only_when_optional(self):
        module = _load_module()
        directory, temp_root = _make_fake_root(all_exporters=False)
        try:
            summary = module.run_operator_workbench_export(temp_root)

            self.assertEqual(
                summary["optional_steps_skipped"],
                [
                    "portfolio_audit_state",
                    "manual_command_inbox_review",
                    "artifact_health_report",
                    "openrouter_passive_surface_pointer",
                    "operator_openrouter_review_dashboard",
                ],
            )
            self.assertEqual([step["status"] for step in summary["steps"][:5]], ["skipped_optional"] * 5)
            self.assertEqual(summary["steps"][5]["status"], "ran")
            self.assertTrue(summary["required_steps_passed"])
            self.assertEqual(module.exit_code_for_summary(summary), 0)
        finally:
            directory.cleanup()

    def test_required_workbench_exporter_failure_causes_failure(self):
        module = _load_module()
        directory, temp_root = _make_fake_root(all_exporters=False, required_failure=True)
        try:
            summary = module.run_operator_workbench_export(temp_root)

            self.assertFalse(summary["required_steps_passed"])
            self.assertEqual(summary["steps"][5]["status"], "failed")
            self.assertEqual(summary["steps"][5]["failure_type"], "RuntimeError")
            self.assertEqual(module.exit_code_for_summary(summary), 2)
            result = json.loads((temp_root / "docs" / "PMBOT_WORKBENCH_003_RESULT.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "blocked")
        finally:
            directory.cleanup()

    def test_safety_flags_remain_false_or_zero(self):
        module = _load_module()
        directory, temp_root = _make_fake_root()
        try:
            summary = module.run_operator_workbench_export(temp_root)
            safety = summary["safety_flags"]

            self.assertTrue(safety["manual_cli_only"])
            self.assertTrue(safety["operator_review_only"])
            self.assertTrue(safety["passive_context_only"])
            self.assertTrue(safety["analysis_only"])
            self.assertTrue(safety["manual_review_only"])
            self.assertTrue(safety["offline_only"])
            self.assertTrue(safety["deterministic"])
            self.assertTrue(safety["local_file_operations_only"])
            self.assertTrue(safety["no_trading_authority"])
            self.assertTrue(safety["no_queue_authority"])
            self.assertTrue(safety["no_runtime_authority"])
            self.assertTrue(safety["no_dispatcher_authority"])
            self.assertTrue(safety["no_wallet_or_order_authority"])
            self.assertTrue(safety["acceptance_is_not_trading_approval"])
            self.assertFalse(safety["runtime_wiring"])
            self.assertFalse(safety["network_api"])
            self.assertFalse(safety["wallet"])
            self.assertFalse(safety["trading"])
            self.assertFalse(safety["autonomous_paper_orders"])
            self.assertFalse(safety["scoring_probability_ev_edge"])
            self.assertFalse(safety["market_decisions"])
            self.assertFalse(safety["command_execution"])
            self.assertFalse(safety["automation_daemon"])
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["commands_executed"], 0)
            self.assertEqual(summary["orders_created"], 0)
        finally:
            directory.cleanup()

    def test_current_run_summary_artifacts_parse_when_present(self):
        module = _load_module()
        module.run_operator_workbench_export(ROOT)

        summary = json.loads(RUN_JSON.read_text(encoding="utf-8"))
        self.assertEqual(summary, json.loads(EXPECTED_RUN_JSON.read_text(encoding="utf-8")))
        self.assertTrue(RUN_MD.exists())
        self.assertTrue(RESULT.exists())
        self.assertEqual(summary["schema_version"], "operator_workbench_export_run.v1")
        self.assertEqual(summary["run_mode"], "manual_local_export")
        self.assertIn("actual_manual_llm_response_trial", summary)
        actual_trial = summary["actual_manual_llm_response_trial"]
        self.assertEqual(actual_trial["artifact_path"], "pm_bot/llm/actual_manual_llm_response_trial.v1.json")
        self.assertTrue(actual_trial["artifact_present"])
        self.assertTrue(actual_trial["operator_response_present"])
        self.assertEqual(actual_trial["run_status"], "actual_response_accepted")
        self.assertEqual(actual_trial["acceptance_status"], "accepted_for_operator_review")
        self.assertTrue(actual_trial["offline_review_context_only"])
        self.assertIn("manual_llm_review_queue", summary)
        queue = summary["manual_llm_review_queue"]
        self.assertEqual(queue["artifact_path"], "pm_bot/llm/manual_llm_review_queue.v1.json")
        self.assertTrue(queue["artifact_present"])
        self.assertEqual(queue["queue_items_total"], 15)
        self.assertEqual(queue["queue_status_counts"]["ready_for_manual_packet_export"], 0)
        self.assertEqual(queue["queue_status_counts"]["waiting_for_operator_pasted_response"], 14)
        self.assertEqual(queue["queue_status_counts"]["response_accepted_for_operator_review"], 1)
        self.assertTrue(queue["offline_manual_only"])
        self.assertIn("openrouter_passive_surface", summary)
        openrouter = summary["openrouter_passive_surface"]
        self.assertEqual(openrouter["status"], "passive_surface_pointer_ready")
        self.assertEqual(openrouter["source_batch_task"], "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL")
        self.assertEqual(
            openrouter["source_baseline_task"],
            "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        )
        self.assertEqual(
            openrouter["source_surface_task"],
            "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        )
        self.assertEqual(openrouter["source_048_status"], "completed_pushed")
        self.assertEqual(openrouter["source_052_status"], "completed_pushed")
        self.assertEqual(openrouter["surfaced_market_ids"], ["569344", "569366", "569368", "569373", "573656"])
        self.assertEqual(openrouter["model"], "anthropic/claude-sonnet-4.5")
        self.assertEqual(openrouter["total_calls"], 5)
        self.assertEqual(openrouter["combined_openrouter_review_contour_summary"]["combined_tokens"], 48573)
        self.assertIn("openrouter_review_dashboard", summary)
        self.assertEqual(summary["openrouter_review_dashboard"]["status"], "operator_openrouter_review_dashboard_created")
        self.assertEqual(
            summary["openrouter_review_dashboard"]["combined_openrouter_review_contour_summary"]["combined_cost"],
            0.325071,
        )
        self.assertTrue(openrouter["operator_review_only"])
        self.assertTrue(openrouter["passive_context_only"])
        self.assertTrue(openrouter["no_trading_authority"])
        self.assertTrue(openrouter["no_queue_authority"])
        self.assertTrue(openrouter["no_runtime_authority"])
        self.assertTrue(openrouter["no_dispatcher_authority"])
        self.assertTrue(openrouter["no_wallet_or_order_authority"])
        self.assertTrue(openrouter["acceptance_is_not_trading_approval"])
        self.assertTrue(openrouter["analysis_only"])
        self.assertTrue(openrouter["manual_review_only"])

    def test_runner_uses_standard_library_and_no_runtime_network_trading_or_command_execution_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib", "pm_bot", "sys"})
        self.assertNotIn("subprocess", imports)
        self.assertTrue(
            imports.isdisjoint(
                {
                    "requests",
                    "urllib",
                    "httpx",
                    "socket",
                    "telegram",
                    "web3",
                    "asyncio",
                    "schedule",
                    "threading",
                }
            )
        )

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            "requests.",
            "httpx.",
            "urllib.request",
            "socket.",
            "webbrowser.",
            "selenium.",
            "submit_order(",
            "execute_trade(",
            "place_order(",
            "scripts/dispatcher.py",
            "scripts/run_codex.py",
            "start_polling(",
            "add_job(",
        ]
        for term in forbidden_call_terms:
            self.assertNotIn(term, source_no_spaces)


if __name__ == "__main__":
    unittest.main()

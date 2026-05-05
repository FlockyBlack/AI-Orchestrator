import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "product" / "run_local_operator_dry_run_acceptance.py"
REPORT_JSON = ROOT / "pm_bot" / "product" / "local_operator_dry_run_acceptance.v1.json"
REPORT_MD = ROOT / "pm_bot" / "product" / "local_operator_dry_run_acceptance.v1.md"
EXPECTED_JSON = ROOT / "pm_bot" / "product" / "expected_local_operator_dry_run_acceptance.v1.json"
DOCS_MD = ROOT / "docs" / "PMBOT_PRODUCT_003_LOCAL_OPERATOR_DRY_RUN_ACCEPTANCE.md"
RESULT_JSON = ROOT / "docs" / "PMBOT_PRODUCT_003_RESULT.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("local_operator_dry_run_acceptance", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_fake_workbench_runner(path, required_steps_passed=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""def run_operator_workbench_export(root):
    return {{
        "required_steps_passed": {str(required_steps_passed)},
        "warnings": [],
    }}
""",
        encoding="utf-8",
    )


def _make_fake_root(include_required=True, warning_total=2, blocking=0, workbench_passed=True):
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    _write_fake_workbench_runner(
        root / "pm_bot" / "workbench" / "run_operator_workbench_export.py",
        required_steps_passed=workbench_passed,
    )
    if include_required:
        _write_json(
            root / "pm_bot" / "dashboard" / "static_operator_report_summary.v1.json",
            {
                "schema_version": "static_operator_report_summary.v1",
                "task_id": "PMBOT-DASHBOARD-003-STATIC-HTML-OPERATOR-REPORT",
                "report_status": "static_report_generated",
            },
        )
        _write_json(
            root / "pm_bot" / "quality" / "artifact_health_report.v1.json",
            {
                "schema_version": "artifact_health_report.v1",
                "task_id": "PMBOT-QUALITY-001-ARTIFACT-HEALTH-AND-STALENESS-CHECK",
                "report_status": "health_passed_with_warnings" if warning_total else "health_passed",
                "warning_severity_summary": {
                    "total_warnings": warning_total,
                    "blocking_count": blocking,
                    "action_required_count": max(warning_total - blocking, 0),
                    "review_needed_count": 0,
                    "informational_count": 0,
                },
                "warnings": [{}] * warning_total,
                "blockers": [],
            },
        )
        _write_json(
            root / "pm_bot" / "workbench" / "operator_review_pack.v1.json",
            {"schema_version": "operator_review_pack.v1"},
        )
        _write_json(
            root / "pm_bot" / "operator" / "manual_command_inbox_review.v1.json",
            {
                "schema_version": "manual_command_inbox_review.v1",
                "task_id": "PMBOT-OPERATOR-002-MANUAL-COMMAND-INBOX-REVIEW-QUEUE",
            },
        )
        _write_json(
            root / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.json",
            {
                "schema_version": "operator_workbench_export_run.v1",
                "task_id": "PMBOT-WORKBENCH-003-SINGLE-COMMAND-LOCAL-EXPORT",
            },
        )
    return directory, root


class LocalOperatorDryRunAcceptanceTests(unittest.TestCase):
    def test_acceptance_report_with_warnings_is_deterministic_and_written(self):
        module = _load_module()
        directory, root = _make_fake_root()
        try:
            first = module.run_local_operator_dry_run_acceptance(root)
            second = module.run_local_operator_dry_run_acceptance(root)

            self.assertEqual(first, second)
            self.assertEqual(first["task_id"], module.TASK_ID)
            self.assertEqual(first["acceptance_verdict"], "accepted_with_warnings")
            self.assertEqual(first["operator_usability_status"], "usable_for_local_operator_review_with_warnings")
            self.assertTrue(first["required_artifacts_present"])
            self.assertEqual(first["warnings_summary"]["total"], 2)
            self.assertEqual(first["blockers"], [])
            self.assertEqual(json.loads((root / "pm_bot/product/local_operator_dry_run_acceptance.v1.json").read_text(encoding="utf-8")), first)
            self.assertEqual(json.loads((root / "pm_bot/product/expected_local_operator_dry_run_acceptance.v1.json").read_text(encoding="utf-8")), first)
            self.assertTrue((root / "pm_bot/product/local_operator_dry_run_acceptance.v1.md").exists())
            self.assertTrue((root / "docs/PMBOT_PRODUCT_003_LOCAL_OPERATOR_DRY_RUN_ACCEPTANCE.md").exists())
            self.assertTrue((root / "docs/PMBOT_PRODUCT_003_RESULT.json").exists())
        finally:
            directory.cleanup()

    def test_missing_required_artifact_blocks_acceptance(self):
        module = _load_module()
        directory, root = _make_fake_root(include_required=False)
        try:
            report = module.run_local_operator_dry_run_acceptance(root)

            self.assertEqual(report["acceptance_verdict"], "blocked")
            self.assertFalse(report["required_artifacts_present"])
            self.assertIn("required artifact missing: pm_bot/dashboard/static_operator_report_summary.v1.json", report["blockers"])
            self.assertEqual(module.exit_code_for_report(report), 2)
        finally:
            directory.cleanup()

    def test_blocking_warning_blocks_acceptance(self):
        module = _load_module()
        directory, root = _make_fake_root(warning_total=1, blocking=1)
        try:
            report = module.run_local_operator_dry_run_acceptance(root)

            self.assertEqual(report["acceptance_verdict"], "blocked")
            self.assertEqual(report["warnings_summary"]["blocking"], 1)
            self.assertIn("blocking warnings present: 1", report["blockers"])
        finally:
            directory.cleanup()

    def test_failed_workbench_runner_reports_failed_to_run(self):
        module = _load_module()
        directory, root = _make_fake_root()
        try:
            (root / "pm_bot/workbench/run_operator_workbench_export.py").write_text(
                "def run_operator_workbench_export(root):\n    raise RuntimeError('boom')\n",
                encoding="utf-8",
            )
            report = module.run_local_operator_dry_run_acceptance(root)

            self.assertEqual(report["acceptance_verdict"], "failed_to_run")
            self.assertIn("workbench runner failed: RuntimeError", report["blockers"])
            self.assertEqual(module.exit_code_for_report(report), 2)
        finally:
            directory.cleanup()

    def test_report_contains_required_safety_and_interpretation_boundaries(self):
        module = _load_module()
        directory, root = _make_fake_root()
        try:
            report = module.run_local_operator_dry_run_acceptance(root)

            self.assertEqual(
                report["safety_flags"],
                {
                    "network_api_calls": False,
                    "wallet_or_private_key_usage": False,
                    "real_orders": False,
                    "live_trading": False,
                    "autonomous_decisions": False,
                    "scoring_probability_ev_edge": False,
                    "side_recommendations": False,
                    "runtime_wiring": False,
                    "command_execution": False,
                },
            )
            limits = "\n".join(report["interpretation_limits"])
            self.assertIn("not strategy profitability", limits)
            self.assertIn("makes no recommendations", limits)
            actions = "\n".join(report["operator_next_actions"]).lower()
            self.assertIn("review", actions)
            self.assertNotIn("trade", actions)
        finally:
            directory.cleanup()

    def test_current_artifacts_parse_when_present(self):
        if not REPORT_JSON.exists():
            self.skipTest("acceptance report not generated yet")

        report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        self.assertEqual(report, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
        self.assertEqual(report["schema_version"], "local_operator_dry_run_acceptance.v1")
        self.assertEqual(report["task_id"], "PMBOT-PRODUCT-003-LOCAL-OPERATOR-DRY-RUN-ACCEPTANCE")
        self.assertTrue(REPORT_MD.exists())
        self.assertTrue(DOCS_MD.exists())
        self.assertTrue(RESULT_JSON.exists())

    def test_runner_uses_standard_library_and_no_forbidden_runtime_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib", "sys"})
        self.assertTrue(
            imports.isdisjoint(
                {
                    "requests",
                    "urllib",
                    "httpx",
                    "socket",
                    "telegram",
                    "web3",
                    "subprocess",
                    "asyncio",
                    "schedule",
                    "threading",
                }
            )
        )

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in [
            "requests.",
            "httpx.",
            "urllib.request",
            "socket.",
            "submit_order(",
            "execute_trade(",
            "place_order(",
            "scripts/dispatcher.py",
            "scripts/run_codex.py",
            "start_polling(",
            "add_job(",
        ]:
            self.assertNotIn(term, source_no_spaces)


if __name__ == "__main__":
    unittest.main()

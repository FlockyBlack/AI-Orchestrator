import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "quality" / "export_artifact_health_report.py"
REPORT_JSON = ROOT / "pm_bot" / "quality" / "artifact_health_report.v1.json"
REPORT_MD = ROOT / "pm_bot" / "quality" / "artifact_health_report.v1.md"
EXPECTED_REPORT_JSON = ROOT / "pm_bot" / "quality" / "expected_artifact_health_report.v1.json"
RESULT = ROOT / "docs" / "PMBOT_QUALITY_001_RESULT.json"
LANE_RESULT = ROOT / "docs" / "PMBOT_CODEX_B_ROUND003_RESULT.json"

NEW_JSON_FILES = [
    REPORT_JSON,
    EXPECTED_REPORT_JSON,
    RESULT,
    LANE_RESULT,
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
    spec = importlib.util.spec_from_file_location("artifact_health_report", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ArtifactHealthReportTests(unittest.TestCase):
    def test_write_exports_json_markdown_expected_and_result_docs(self):
        result = json.loads(_run_write().stdout)

        self.assertEqual(result["task_id"], "PMBOT-QUALITY-001-ARTIFACT-HEALTH-AND-STALENESS-CHECK")
        self.assertIn(result["report_status"], {"health_passed", "health_passed_with_warnings"})
        self.assertGreater(result["artifacts_checked"], 0)
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)
        self.assertTrue(REPORT_MD.exists())

    def test_json_output_matches_expected_fixture_and_default_stdout(self):
        _run_write()
        report = _load_json(REPORT_JSON)
        expected = _load_json(EXPECTED_REPORT_JSON)
        stdout_report = json.loads(_run_json().stdout)

        self.assertEqual(report, expected)
        self.assertEqual(stdout_report, expected)

    def test_report_contains_required_inventory_counts_and_warnings(self):
        _run_write()
        report = _load_json(REPORT_JSON)

        self.assertEqual(report["schema_version"], "artifact_health_report.v1")
        self.assertEqual(report["generated_by"], "pm_bot/quality/export_artifact_health_report.py")
        self.assertFalse(report["generated_at_policy"]["wall_clock_time_used"])
        self.assertGreater(report["artifacts_checked"], 100)
        self.assertEqual(report["artifacts_checked"], len(report["artifacts"]))
        self.assertEqual(
            report["artifacts_present_count"] + report["artifacts_missing_count"],
            report["artifacts_checked"],
        )
        self.assertGreaterEqual(report["json_parse_pass_count"], 1)
        self.assertGreaterEqual(report["schema_version_missing_count"], 1)

        artifacts = {item["path"]: item for item in report["artifacts"]}
        self.assertIn("docs/PMBOT_PRODUCT_001_RESULT.json", artifacts)
        self.assertIn("docs/PMBOT_INTEGRATION_008_RESULT.json", artifacts)
        self.assertIn("docs/PMBOT_PAPER_018_RESULT.json", artifacts)
        self.assertIn("docs/PMBOT_DASHBOARD_002_RESULT.json", artifacts)
        self.assertIn("docs/PMBOT_OPERATOR_002_RESULT.json", artifacts)
        self.assertIn("docs/PMBOT_INFRA_009_RESULT.json", artifacts)

        optional_infra_009 = artifacts["docs/PMBOT_INFRA_009_RESULT.json"]
        self.assertFalse(optional_infra_009["required"])
        if not optional_infra_009["exists"]:
            self.assertIn(
                "missing_optional_artifact",
                {warning["category"] for warning in optional_infra_009["warnings"]},
            )

        malformed = artifacts["pm_bot/paper/manual_snapshot_import_source/005_malformed.json"]
        self.assertEqual(malformed["json_parse_status"], "parse_failed")
        self.assertIn(
            "known_intentional_malformed_fixture_parse_failure",
            {warning["category"] for warning in malformed["warnings"]},
        )
        self.assertNotIn("required JSON parse failed", "\n".join(report["blockers"]))

    def test_warning_severity_summary_classifies_all_warning_detail(self):
        _run_write()
        report = _load_json(REPORT_JSON)
        summary = report["warning_severity_summary"]

        self.assertEqual(summary["total_warnings"], len(report["warnings"]))
        self.assertEqual(
            summary["total_warnings"],
            summary["blocking_count"]
            + summary["action_required_count"]
            + summary["review_needed_count"]
            + summary["informational_count"],
        )
        for warning in report["warnings"]:
            self.assertIn(warning["owner"], {"code", "fixture", "schema", "data", "unknown"})
            self.assertIn(warning["action_type"], {"fix_required", "review_required", "ignore_allowed"})
            self.assertIsInstance(warning["recommended_action"], str)
            self.assertTrue(warning["recommended_action"])
        for artifact in report["artifacts"]:
            for warning in artifact["warnings"]:
                self.assertIn(warning["owner"], {"code", "fixture", "schema", "data", "unknown"})
                self.assertIn(warning["action_type"], {"fix_required", "review_required", "ignore_allowed"})
                self.assertIsInstance(warning["recommended_action"], str)
                self.assertTrue(warning["recommended_action"])
        self.assertFalse(summary["blocking_warning_detected"])
        self.assertEqual(summary["blocking_count"], 0)
        self.assertGreater(summary["action_required_count"], 0)
        self.assertGreater(summary["review_needed_count"], 0)
        self.assertGreater(summary["informational_count"], 0)
        self.assertIn("No blocking warnings detected", summary["operator_summary"])

        categories = {item["category"]: item for item in summary["warning_categories"]}
        self.assertNotIn("expected_fixture_alignment_warning", categories)
        self.assertNotIn("fixture_alignment_actual_missing", categories)
        self.assertNotIn("embedded_artifact_pointer_warning", categories)
        self.assertEqual(
            categories["known_intentional_malformed_fixture_parse_failure"]["severity"],
            "informational",
        )
        self.assertEqual(sum(summary["warnings_by_owner"].values()), summary["total_warnings"])
        self.assertEqual(sum(summary["warnings_by_action_type"].values()), summary["total_warnings"])
        self.assertGreater(summary["warnings_by_owner"]["fixture"], 0)
        self.assertGreater(summary["warnings_by_action_type"]["fix_required"], 0)
        self.assertGreater(len(summary["top_action_items"]), 0)
        self.assertLessEqual(len(summary["top_action_items"]), 5)
        self.assertIn(summary["top_action_items"][0]["category"], categories)

    def test_pointer_fixture_and_safety_sections_are_explicit(self):
        _run_write()
        report = _load_json(REPORT_JSON)

        pointer_summary = report["embedded_artifact_pointer_summary"]
        self.assertGreater(pointer_summary["checked_count"], 0)
        self.assertGreaterEqual(pointer_summary["missing_count"], 0)
        self.assertEqual(pointer_summary["checked_count"], pointer_summary["present_count"] + pointer_summary["missing_count"])

        fixture_summary = report["expected_fixture_alignment_summary"]
        self.assertGreater(fixture_summary["checks_total"], 0)
        self.assertGreater(fixture_summary["aligned_count"], 0)
        self.assertGreaterEqual(fixture_summary["mismatch_count"], 0)
        self.assertEqual(
            fixture_summary["checks_total"],
            sum(
                1
                for item in fixture_summary["checks"]
                if item["alignment_status"]
                in {"aligned", "mismatch", "actual_missing", "not_checked_parse_failed_or_non_object", "not_checked_read_failed"}
            ),
        )

        safety = report["safety_flag_summary"]
        for key in (
            "runtime_wiring",
            "network_api",
            "wallet",
            "trading",
            "autonomous_paper_orders",
            "scoring_probability_ev_edge",
            "market_decisions",
            "command_execution",
        ):
            self.assertFalse(safety["report_safety_flags"][key])
        self.assertEqual(safety["unexpected_true_or_nonzero_values"], [])

    def test_result_docs_mirror_quality_summary(self):
        _run_write()
        report = _load_json(REPORT_JSON)
        result = _load_json(RESULT)
        lane = _load_json(LANE_RESULT)

        self.assertEqual(result, lane)
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["artifact_health"]["report_status"], report["report_status"])
        self.assertEqual(result["artifact_health"]["artifacts_checked"], report["artifacts_checked"])
        self.assertEqual(result["artifact_health"]["warnings"], len(report["warnings"]))
        self.assertFalse(result["safety_flags"]["runtime_wiring"])
        self.assertFalse(result["safety_flags"]["network_api"])
        self.assertFalse(result["safety_flags"]["wallet"])
        self.assertFalse(result["safety_flags"]["trading"])
        self.assertFalse(result["safety_flags"]["autonomous_paper_orders"])
        self.assertFalse(result["safety_flags"]["scoring_probability_ev_edge"])
        self.assertFalse(result["safety_flags"]["market_decisions"])
        self.assertFalse(result["safety_flags"]["command_execution"])

    def test_markdown_matches_cli_output(self):
        _run_write()
        markdown = REPORT_MD.read_text(encoding="utf-8")

        self.assertEqual(_run_markdown().stdout, markdown)
        self.assertIn("PMBOT Artifact Health Report v1", markdown)
        self.assertIn("report_status:", markdown)
        self.assertIn("Warning Severity Summary", markdown)
        self.assertIn("blocking_count:", markdown)
        self.assertIn("Embedded Pointer Health", markdown)
        self.assertIn("Expected Fixture Alignment", markdown)

    def test_temp_root_missing_required_artifact_fails_but_missing_optional_infra_009_does_not(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for relative in module.REQUIRED_CONTEXT_DOCS:
                path = temp_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(
                        {
                            "schema_version": "test.v1",
                            "task_id": "PMBOT-TEST",
                            "status": "completed_ready_for_review",
                        }
                    ),
                    encoding="utf-8",
                )
            (temp_root / "docs" / "PMBOT_PAPER_018_RESULT.json").unlink()
            report = module.build_artifact_health_report(temp_root)

        self.assertEqual(report["report_status"], "health_failed")
        self.assertTrue(any("PMBOT_PAPER_018_RESULT.json" in blocker for blocker in report["blockers"]))
        self.assertFalse(any("PMBOT_INFRA_009_RESULT.json" in blocker for blocker in report["blockers"]))
        self.assertTrue(report["warning_severity_summary"]["blocking_warning_detected"])
        self.assertGreaterEqual(report["warning_severity_summary"]["blocking_count"], 1)

    def test_runner_uses_standard_library_and_no_runtime_network_or_command_execution_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "re", "sys"})
        self.assertTrue(imports.isdisjoint(FORBIDDEN_IMPORTS))

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("import", "httpx"),
            _frag("httpx", "."),
            _frag("import", "aiohttp"),
            _frag("aiohttp", "."),
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

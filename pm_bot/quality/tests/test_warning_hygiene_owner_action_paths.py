import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "quality" / "build_warning_hygiene_owner_action_paths.py"
REPORT_JSON = ROOT / "pm_bot" / "quality" / "warning_hygiene_owner_action_paths.v1.json"
REPORT_MD = ROOT / "pm_bot" / "quality" / "warning_hygiene_owner_action_paths.v1.md"
EXPECTED_REPORT_JSON = ROOT / "pm_bot" / "quality" / "expected_warning_hygiene_owner_action_paths.v1.json"
RESULT = ROOT / "docs" / "PMBOT_QUALITY_002_RESULT.json"

NEW_JSON_FILES = [
    REPORT_JSON,
    EXPECTED_REPORT_JSON,
    RESULT,
]

REQUIRED_WARNING_FIELDS = {
    "warning_id",
    "bucket_id",
    "source_artifact",
    "source_path",
    "warning_category",
    "severity",
    "owner",
    "owner_type",
    "action_path",
    "action_type",
    "deferrable",
    "expected_status",
    "safety_relevance",
    "recommended_operator_action",
    "recommended_maintainer_action",
    "rationale",
}

ALLOWED_OWNERS = {
    "product",
    "quality",
    "paper",
    "dashboard",
    "operator",
    "workbench",
    "ingest",
    "research",
    "docs",
    "infra",
    "unknown",
}

ALLOWED_ACTION_TYPES = {
    "inspect",
    "update_fixture",
    "add_missing_metadata",
    "normalize_legacy_artifact",
    "document_exception",
    "archive_or_mark_legacy",
    "fix_path_portability",
    "no_action_expected",
    "escalate_if_repeated",
}

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


class WarningHygieneOwnerActionPathsTests(unittest.TestCase):
    def test_write_exports_json_markdown_expected_and_result_docs(self):
        result = json.loads(_run_write().stdout)

        self.assertEqual(result["schema_version"], "warning_hygiene_owner_action_paths.v1")
        self.assertEqual(result["task_id"], "PMBOT-QUALITY-002-WARNING-HYGIENE-OWNER-ACTION-PATHS")
        self.assertEqual(result["source_report"]["total_warnings"], 59)
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

    def test_each_warning_has_owner_action_status_deferral_and_safety_metadata(self):
        _run_write()
        report = _load_json(REPORT_JSON)
        warnings = report["warnings"]

        self.assertEqual(len(warnings), 59)
        self.assertFalse(report["warning_detection_policy"]["warnings_hidden"])
        self.assertFalse(report["warning_detection_policy"]["warnings_suppressed"])
        self.assertFalse(report["warning_detection_policy"]["warnings_downgraded_silently"])
        for warning in warnings:
            self.assertTrue(REQUIRED_WARNING_FIELDS.issubset(warning))
            self.assertIn(warning["owner"], ALLOWED_OWNERS)
            self.assertIn(warning["action_type"], ALLOWED_ACTION_TYPES)
            self.assertIn(
                warning["expected_status"],
                {"current", "legacy", "stale", "expected_gap", "needs_cleanup", "needs_review"},
            )
            self.assertIn(
                warning["safety_relevance"],
                {
                    "none",
                    "boundary_related",
                    "execution_related",
                    "data_integrity_related",
                    "operator_usability_related",
                },
            )
            self.assertIsInstance(warning["deferrable"], bool)
            self.assertTrue(warning["source_path"])
            self.assertTrue(warning["recommended_operator_action"])
            self.assertTrue(warning["recommended_maintainer_action"])
            self.assertTrue(warning["rationale"])

    def test_summary_counts_cover_all_warning_records(self):
        _run_write()
        report = _load_json(REPORT_JSON)
        summary = report["summary_counts"]
        total = len(report["warnings"])

        self.assertEqual(sum(summary["owner"].values()), total)
        self.assertEqual(sum(summary["category"].values()), total)
        self.assertEqual(sum(summary["severity"].values()), total)
        self.assertEqual(sum(summary["expected_status"].values()), total)
        self.assertEqual(sum(summary["action_type"].values()), total)
        self.assertEqual(sum(summary["safety_relevance"].values()), total)
        self.assertEqual(summary["deferrable"]["true"] + summary["deferrable"]["false"], total)
        self.assertEqual(summary["severity"]["blocking"], 0)
        self.assertEqual(summary["severity"]["action_required"], 21)
        self.assertEqual(summary["severity"]["review_needed"], 37)
        self.assertEqual(summary["severity"]["informational"], 1)
        self.assertGreater(summary["owner"]["paper"], 0)
        self.assertGreater(summary["owner"]["operator"], 0)
        self.assertGreater(summary["owner"]["dashboard"], 0)
        self.assertEqual(summary["action_type"].get("update_fixture", 0), 0)
        self.assertGreater(summary["action_type"]["add_missing_metadata"], 0)

    def test_buckets_and_operator_summary_are_actionable(self):
        _run_write()
        report = _load_json(REPORT_JSON)

        self.assertGreater(len(report["warning_buckets"]), 1)
        top_bucket = report["warning_buckets"][0]
        self.assertIn("source_paths", top_bucket)
        self.assertGreater(top_bucket["warning_count"], 0)
        self.assertTrue(top_bucket["recommended_operator_action"])
        self.assertTrue(top_bucket["recommended_maintainer_action"])

        operator = report["operator_summary"]
        self.assertFalse(operator["local_mvp_blocked"])
        self.assertGreater(operator["non_deferrable_warning_count"], 0)
        self.assertGreater(operator["safety_relevant_warning_count"], 0)
        self.assertGreater(len(operator["top_owner_actions"]), 0)
        self.assertGreater(len(operator["next_cleanup_actions"]), 0)
        self.assertIn("should not block local MVP usage", operator["not_mvp_blocking_statement"])

    def test_markdown_is_operator_readable_and_matches_cli_output(self):
        _run_write()
        markdown = REPORT_MD.read_text(encoding="utf-8")

        self.assertEqual(_run_markdown().stdout, markdown)
        self.assertIn("PMBOT Warning Hygiene Owner Action Paths v1", markdown)
        self.assertIn("Top Warning Groups", markdown)
        self.assertIn("Owner Action Queue", markdown)
        self.assertIn("Warnings are not hidden", markdown)
        self.assertIn("what_should_not_block_local_mvp_usage", markdown)

    def test_result_doc_mirrors_hygiene_summary(self):
        _run_write()
        report = _load_json(REPORT_JSON)
        result = _load_json(RESULT)

        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(
            result["warning_hygiene_summary"]["total_warnings_processed"],
            report["source_report"]["total_warnings"],
        )
        self.assertEqual(result["warning_hygiene_summary"]["owners"], report["summary_counts"]["owner"])
        self.assertFalse(result["operator_summary"]["local_mvp_blocked"])
        for value in result["safety_flags"].values():
            self.assertFalse(value)

    def test_runner_uses_no_forbidden_runtime_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertFalse(imports & FORBIDDEN_IMPORTS)


if __name__ == "__main__":
    unittest.main()

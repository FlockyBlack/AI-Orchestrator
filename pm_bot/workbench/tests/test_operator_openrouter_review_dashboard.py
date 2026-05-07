import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.py"
DASHBOARD_JSON = ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json"
DASHBOARD_MD = ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.md"


def _run_write():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class OperatorOpenrouterReviewDashboardTests(unittest.TestCase):
    def test_dashboard_write_exports_static_json_and_markdown(self):
        result = json.loads(_run_write().stdout)
        dashboard = _load_json(DASHBOARD_JSON)

        self.assertEqual(
            result["task_id"],
            "PMBOT-OPENROUTER-053-OPERATOR-OPENROUTER-REVIEW-DASHBOARD",
        )
        self.assertEqual(result["status"], "operator_openrouter_review_dashboard_created")
        self.assertTrue(DASHBOARD_MD.exists())
        self.assertEqual(dashboard["schema_version"], "operator_openrouter_review_dashboard.v1")
        self.assertEqual(dashboard["status"], "operator_openrouter_review_dashboard_created")
        self.assertEqual(dashboard["dashboard_mode"], "local_static_read_only")

    def test_dashboard_contains_n3_n5_combined_inventory_and_safety(self):
        _run_write()
        dashboard = _load_json(DASHBOARD_JSON)

        self.assertEqual(dashboard["latest_batch"]["source_task"], "PMBOT-OPENROUTER-051")
        self.assertEqual(
            dashboard["latest_surface"],
            "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        )
        self.assertEqual(
            dashboard["latest_baseline"],
            "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        )
        self.assertEqual(dashboard["n3_summary"]["calls"], 3)
        self.assertEqual(dashboard["n3_summary"]["total_tokens"], 18686)
        self.assertEqual(dashboard["n5_summary"]["calls"], 5)
        self.assertEqual(dashboard["n5_summary"]["total_tokens"], 29887)
        combined = dashboard["combined_openrouter_review_contour_summary"]
        self.assertEqual(combined["total_markets_successfully_reviewed"], 8)
        self.assertEqual(combined["combined_cost"], 0.325071)
        self.assertEqual(combined["combined_tokens"], 48573)
        self.assertEqual(dashboard["cost_summary"]["combined_cost"], 0.325071)
        self.assertEqual(dashboard["usage_summary"]["combined_tokens"], 48573)
        self.assertEqual(
            dashboard["normalization_summary"]["successful_batch_responses_requiring_fenced_normalization"],
            "8/8",
        )
        self.assertEqual(dashboard["normalization_summary"]["clean_raw_json_responses"], 0)

        inventory = dashboard["inventory_summary"]
        self.assertEqual(inventory["total_markets_found"], 14)
        self.assertEqual(inventory["total_reviewed_by_openrouter"], 10)
        self.assertEqual(inventory["unknown_category_count"], 0)
        self.assertIn("elections", inventory["category_counts"])

        evidence = dashboard["evidence_completeness_summary"]
        self.assertEqual(evidence["reviewed_market_count"], 10)
        self.assertEqual(evidence["evidence_completeness_counts"]["medium"], 10)

        self.assertEqual(
            dashboard["evidence_readiness_integration_status"],
            "source_001_context_ready",
        )
        readiness = dashboard["evidence_readiness_score_summary"]
        self.assertEqual(readiness["medium_count"], 10)
        self.assertEqual(readiness["low_count"], 4)
        self.assertEqual(readiness["blocked_count"], 0)
        self.assertEqual(
            dashboard["markets_reviewed_vs_unreviewed"]["unreviewed_market_ids"],
            ["597964", "598936", "691547", "692258"],
        )
        self.assertEqual(len(dashboard["markets_with_medium_evidence_completeness"]), 10)
        self.assertIn("elections", dashboard["category_gap_summary"])
        self.assertTrue(dashboard["no_market_action_guidance"])
        self.assertEqual(
            dashboard["batch_readiness_gate_integration_status"],
            "source_002_gate_ready",
        )
        gate = dashboard["batch_readiness_gate_summary"]
        self.assertEqual(
            gate["artifact_pointer"],
            "pm_bot/llm/current_llm_batch_readiness_gate.v1.json",
        )
        self.assertEqual(gate["total_markets"], 14)
        self.assertEqual(gate["medium_count"], 10)
        self.assertEqual(gate["low_count"], 4)
        self.assertEqual(gate["blocked_count"], 0)
        self.assertEqual(gate["eligible_for_future_llm_review_count"], 10)
        self.assertEqual(gate["eligible_for_future_openrouter_batch_count"], 10)
        self.assertEqual(gate["needs_local_enrichment_count"], 14)
        self.assertEqual(
            gate["low_readiness_market_ids"],
            ["597964", "598936", "691547", "692258"],
        )
        self.assertFalse(gate["future_live_batch_scheduled"])
        self.assertFalse(gate["future_openrouter_batch_approved"])
        self.assertTrue(gate["no_market_action_guidance"])

        safety = dashboard["safety_summary"]
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["passive_context_only"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_dispatcher_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertTrue(safety["acceptance_is_not_trading_approval"])
        self.assertEqual(dashboard["openrouter_calls_performed"], 0)
        self.assertEqual(dashboard["polymarket_api_calls_performed"], 0)
        self.assertEqual(dashboard["network_calls_performed"], 0)

    def test_dashboard_artifact_pointers_are_repo_relative_and_exist(self):
        _run_write()
        dashboard = _load_json(DASHBOARD_JSON)
        for path in dashboard["artifact_pointers"].values():
            self.assertFalse(Path(path).is_absolute())
            self.assertTrue((ROOT / path).exists(), path)

    def test_dashboard_runner_uses_no_runtime_network_or_trading_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "pm_bot", "sys"})
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "httpx", "socket", "selenium", "playwright"}))


if __name__ == "__main__":
    unittest.main()

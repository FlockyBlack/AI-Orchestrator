import ast
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.py"
POINTER_JSON = ROOT / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.json"
POINTER_MD = ROOT / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.md"

N3_MARKET_IDS = ["569333", "569334", "569343"]
N5_MARKET_IDS = ["569344", "569366", "569368", "569373", "573656"]

REQUIRED_TRUE_FLAGS = (
    "operator_review_only",
    "passive_context_only",
    "no_trading_authority",
    "no_queue_authority",
    "no_runtime_authority",
    "no_dispatcher_authority",
    "no_wallet_or_order_authority",
    "acceptance_is_not_trading_approval",
    "analysis_only",
    "manual_review_only",
)

FORBIDDEN_MARKET_ACTION_PATTERNS = (
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\benter\b",
    r"\bexit\b",
    r"\bprobability\b",
    r"\bexpected value\b",
    r"\bev\b",
    r"\bedge\b",
    r"\bconfidence\b",
    r"\bside selection\b",
    r"\bselected side\b",
    r"\brecommended side\b",
)


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


class OpenrouterPassiveSurfacePointerTests(unittest.TestCase):
    def test_pointer_write_exports_multi_batch_json_and_markdown(self):
        result = json.loads(_run_write().stdout)
        pointer = _load_json(POINTER_JSON)

        self.assertEqual(
            result["task_id"],
            "PMBOT-OPENROUTER-053-WORKBENCH-PASSIVE-SURFACE-MULTI-BATCH-INTEGRATION",
        )
        self.assertEqual(result["status"], "passive_surface_pointer_ready")
        self.assertTrue(POINTER_MD.exists())
        self.assertEqual(pointer["schema_version"], "openrouter_passive_surface_pointer.v1")
        self.assertEqual(pointer["status"], "passive_surface_pointer_ready")
        self.assertEqual(
            pointer["latest_surface_source_batch_task"],
            "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        )
        self.assertEqual(
            pointer["latest_surface_task"],
            "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        )
        self.assertEqual(pointer["source_batch_task"], "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL")
        self.assertEqual(pointer["source_baseline_task"], "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY")
        self.assertEqual(pointer["surfaced_market_ids"], N5_MARKET_IDS)
        self.assertEqual(pointer["model"], "anthropic/claude-sonnet-4.5")
        self.assertEqual(pointer["total_calls"], 5)

    def test_pointer_surface_history_preserves_n3_and_adds_n5(self):
        _run_write()
        pointer = _load_json(POINTER_JSON)
        history = pointer["surface_history"]

        self.assertEqual([entry["batch_label"] for entry in history], ["N=3", "N=5"])
        self.assertEqual(history[0]["surfaced_market_ids"], N3_MARKET_IDS)
        self.assertEqual(history[0]["total_calls"], 3)
        self.assertEqual(history[0]["aggregate_usage"]["total_tokens"], 18686)
        self.assertEqual(history[0]["aggregate_cost"]["total_cost"], 0.125982)
        self.assertEqual(history[1]["surfaced_market_ids"], N5_MARKET_IDS)
        self.assertEqual(history[1]["total_calls"], 5)
        self.assertEqual(history[1]["aggregate_usage"]["total_tokens"], 29887)
        self.assertEqual(history[1]["aggregate_cost"]["total_cost"], 0.199089)

        combined = pointer["combined_openrouter_review_contour_summary"]
        self.assertEqual(combined["total_markets_successfully_reviewed"], 8)
        self.assertEqual(combined["total_openrouter_calls_in_successful_batches"], 8)
        self.assertEqual(combined["combined_cost"], 0.325071)
        self.assertEqual(combined["combined_tokens"], 48573)

    def test_pointer_contains_required_summaries_and_no_authority_flags(self):
        _run_write()
        pointer = _load_json(POINTER_JSON)

        self.assertEqual(pointer["aggregate_usage"]["prompt_tokens"], 20768)
        self.assertEqual(pointer["aggregate_usage"]["completion_tokens"], 9119)
        self.assertEqual(pointer["aggregate_usage"]["total_tokens"], 29887)
        self.assertEqual(pointer["aggregate_cost"]["total_cost"], 0.199089)
        self.assertEqual(pointer["aggregate_cost"]["average_cost_per_market"], 0.0398178)
        self.assertEqual(pointer["normalization_summary"]["fenced_response_count"], 5)
        self.assertEqual(pointer["normalization_summary"]["normalized_response_count"], 5)
        self.assertEqual(pointer["normalization_summary"]["clean_raw_json_response_count"], 0)
        self.assertEqual(pointer["quality_summary"]["accepted_for_operator_review_count"], 5)
        self.assertEqual(pointer["quality_summary"]["blocked_count"], 0)

        for flag in REQUIRED_TRUE_FLAGS:
            self.assertTrue(pointer[flag])
            self.assertTrue(pointer["safety_summary"][flag])
            self.assertTrue(pointer["required_flag_status"][flag])

        self.assertFalse(pointer["safety_summary"]["raw_model_responses_included"])
        self.assertFalse(pointer["safety_summary"]["per_market_response_text_included"])
        self.assertFalse(pointer["safety_summary"]["runtime_wiring_added"])
        self.assertFalse(pointer["safety_summary"]["dispatcher_changes_added"])
        self.assertFalse(pointer["safety_summary"]["background_workers_added"])
        self.assertFalse(pointer["safety_summary"]["queue_items_created"])
        self.assertFalse(pointer["safety_summary"]["queue_state_mutated"])
        self.assertFalse(pointer["safety_summary"]["browser_automation_added"])
        self.assertFalse(pointer["safety_summary"]["wallet_or_order_access_added"])
        self.assertEqual(pointer["safety_summary"]["openrouter_calls_performed"], 0)
        self.assertEqual(pointer["safety_summary"]["polymarket_api_calls_performed"], 0)
        self.assertEqual(pointer["safety_summary"]["network_calls"], 0)
        self.assertEqual(pointer["safety_summary"]["orders_created"], 0)

    def test_pointer_artifact_paths_are_repo_relative_and_resolve(self):
        _run_write()
        pointer = _load_json(POINTER_JSON)

        for group in ("artifact_pointers", "source_artifact_pointers"):
            for item in pointer[group].values():
                path = item["path"]
                self.assertFalse(Path(path).is_absolute())
                self.assertTrue((ROOT / path).exists(), path)

    def test_pointer_markdown_does_not_include_market_action_guidance_language(self):
        _run_write()
        text = POINTER_MD.read_text(encoding="utf-8").lower()

        matches = {
            pattern
            for pattern in FORBIDDEN_MARKET_ACTION_PATTERNS
            if re.search(pattern, text)
        }
        self.assertEqual(matches, set())

    def test_pointer_uses_local_artifact_imports_and_no_runtime_network_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "pm_bot", "sys"})
        self.assertTrue(
            imports.isdisjoint({"requests", "urllib", "httpx", "socket", "webbrowser", "selenium", "playwright"})
        )

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            "requests.",
            "httpx.",
            "urllib.request",
            "socket.",
            "webbrowser.",
            "selenium.",
            "playwright.",
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

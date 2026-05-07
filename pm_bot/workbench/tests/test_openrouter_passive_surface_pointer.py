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

EXPECTED_MARKET_IDS = ["569333", "569334", "569343"]

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
    def test_pointer_write_exports_json_and_markdown(self):
        result = json.loads(_run_write().stdout)
        pointer = _load_json(POINTER_JSON)

        self.assertEqual(
            result["task_id"],
            "PMBOT-OPENROUTER-049-WORKBENCH-PASSIVE-SURFACE-INTEGRATION",
        )
        self.assertEqual(result["status"], "passive_surface_pointer_ready")
        self.assertTrue(POINTER_MD.exists())
        self.assertEqual(pointer["schema_version"], "openrouter_passive_surface_pointer.v1")
        self.assertEqual(pointer["status"], "passive_surface_pointer_ready")
        self.assertEqual(pointer["source_batch_task"], "PMBOT-OPENROUTER-046")
        self.assertEqual(pointer["source_baseline_task"], "PMBOT-OPENROUTER-047")
        self.assertEqual(pointer["source_surface_task"], "PMBOT-OPENROUTER-048")
        self.assertEqual(pointer["source_048_status"], "completed_pushed")
        self.assertEqual(pointer["surfaced_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(pointer["model"], "anthropic/claude-sonnet-4.5")
        self.assertEqual(pointer["total_calls"], 3)

    def test_pointer_contains_required_summaries_and_no_authority_flags(self):
        _run_write()
        pointer = _load_json(POINTER_JSON)

        self.assertEqual(pointer["aggregate_usage"]["prompt_tokens"], 12859)
        self.assertEqual(pointer["aggregate_usage"]["completion_tokens"], 5827)
        self.assertEqual(pointer["aggregate_usage"]["total_tokens"], 18686)
        self.assertEqual(pointer["aggregate_cost"]["total_cost"], 0.125982)
        self.assertEqual(pointer["aggregate_cost"]["average_cost_per_market"], 0.041994)
        self.assertEqual(pointer["normalization_summary"]["fenced_response_count"], 3)
        self.assertEqual(pointer["normalization_summary"]["normalized_response_count"], 3)
        self.assertEqual(pointer["normalization_summary"]["clean_raw_json_response_count"], 0)
        self.assertEqual(pointer["normalization_summary"]["policy"], "fenced_json_normalization.v1")
        self.assertEqual(pointer["quality_summary"]["accepted_for_operator_review_count"], 3)
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
                self.assertIn(
                    item["role"],
                    {
                        "generated_workbench_pointer",
                        "read_only_passive_source",
                        "read_only_source_result",
                        "read_only_source_report",
                        "read_only_source_summary",
                    },
                )

    def test_pointer_artifacts_do_not_include_market_action_language(self):
        _run_write()
        text = json.dumps(_load_json(POINTER_JSON), sort_keys=True).lower()
        text += "\n" + POINTER_MD.read_text(encoding="utf-8").lower()

        matches = {
            pattern
            for pattern in FORBIDDEN_MARKET_ACTION_PATTERNS
            if re.search(pattern, text)
        }
        self.assertEqual(matches, set())

    def test_pointer_uses_standard_library_and_no_runtime_imports(self):
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

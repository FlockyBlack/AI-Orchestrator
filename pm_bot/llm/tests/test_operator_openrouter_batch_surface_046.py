import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SURFACE_JSON = ROOT / "pm_bot" / "llm" / "operator_openrouter_batch_surface_046.v1.json"
SURFACE_MD = ROOT / "pm_bot" / "llm" / "operator_openrouter_batch_surface_046.v1.md"
RESULT_046 = ROOT / "docs" / "PMBOT_OPENROUTER_046_RESULT.json"
RESULT_047 = ROOT / "docs" / "PMBOT_OPENROUTER_047_RESULT.json"
RESULT_048 = ROOT / "docs" / "PMBOT_OPENROUTER_048_RESULT.json"

EXPECTED_MARKET_IDS = ["569333", "569334", "569343"]

REQUIRED_TRUE_FLAGS = {
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
}

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


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class OperatorOpenrouterBatchSurface046Tests(unittest.TestCase):
    def test_surface_shape_and_authority_flags(self):
        surface = _load_json(SURFACE_JSON)

        self.assertEqual(surface["contract_version"], "operator_openrouter_batch_surface.v1")
        self.assertEqual(
            surface["task_id"],
            "PMBOT-OPENROUTER-048-PASSIVE-OPERATOR-SURFACE-046-BATCH",
        )
        self.assertEqual(surface["source_batch_task"], "PMBOT-OPENROUTER-046")
        self.assertEqual(surface["source_baseline_task"], "PMBOT-OPENROUTER-047")
        self.assertEqual(surface["status"], "passive_operator_surface_created")

        for flag in REQUIRED_TRUE_FLAGS:
            self.assertIs(surface[flag], True)
            self.assertIs(surface["safety_summary"][flag], True)

        self.assertEqual(surface["openrouter_calls_performed_by_this_task"], 0)
        self.assertEqual(surface["polymarket_api_calls_performed_by_this_task"], 0)
        self.assertIs(surface["no_market_action_guidance"], True)
        self.assertIs(surface["safety_summary"]["no_market_action_guidance"], True)

    def test_source_status_and_aggregate_values(self):
        surface = _load_json(SURFACE_JSON)
        result_046 = _load_json(RESULT_046)
        result_047 = _load_json(RESULT_047)

        self.assertEqual(result_046["status"], "completed_pushed")
        self.assertEqual(result_047["status"], "completed_pushed")
        self.assertEqual(result_046["completed_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(result_047["analyzed_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(result_046["openrouter_calls_performed"], 3)
        self.assertEqual(result_047["openrouter_calls_performed"], 0)
        self.assertEqual(result_046["polymarket_api_calls_performed"], 0)
        self.assertEqual(result_047["polymarket_api_calls_performed"], 0)

        self.assertEqual(surface["source_summary"]["markets_included"], EXPECTED_MARKET_IDS)
        self.assertEqual(surface["source_summary"]["source_openrouter_calls_performed"], 3)
        self.assertEqual(surface["aggregate_usage"]["prompt_tokens"], 12859)
        self.assertEqual(surface["aggregate_usage"]["completion_tokens"], 5827)
        self.assertEqual(surface["aggregate_usage"]["total_tokens"], 18686)
        self.assertEqual(surface["aggregate_cost"]["total_cost"], 0.125982)
        self.assertEqual(surface["aggregate_cost"]["average_cost_per_market"], 0.041994)

    def test_per_market_entries_are_passive_and_point_to_existing_artifacts(self):
        surface = _load_json(SURFACE_JSON)
        entries = surface["per_market_passive_entries"]

        self.assertEqual([entry["market_id"] for entry in entries], EXPECTED_MARKET_IDS)
        for entry in entries:
            self.assertIs(entry["accepted_for_operator_review"], True)
            self.assertIs(entry["openrouter_call_performed"], True)
            self.assertIs(entry["raw_response_preserved"], True)
            self.assertIs(entry["normalization_policy_applied"], True)
            self.assertEqual(
                entry["normalization_policy_version"],
                "fenced_json_normalization.v1",
            )
            self.assertIs(entry["prohibited_content_detected"], False)
            self.assertIs(entry["forbidden_phrase_detected"], False)
            self.assertEqual(entry["schema_validation_status"], "accepted")
            self.assertEqual(entry["acceptance_gate_status"], "passed")

            for artifact in entry["artifact_pointers"].values():
                self.assertEqual(artifact["role"], "read_only_input")
                self.assertTrue((ROOT / artifact["path"]).exists())

    def test_surface_artifacts_do_not_contain_market_action_language(self):
        text = json.dumps(_load_json(SURFACE_JSON), sort_keys=True).lower()
        text += "\n" + SURFACE_MD.read_text(encoding="utf-8").lower()

        matches = {
            pattern
            for pattern in FORBIDDEN_MARKET_ACTION_PATTERNS
            if re.search(pattern, text)
        }
        self.assertEqual(matches, set())

    def test_048_result_points_to_passive_surface(self):
        result = _load_json(RESULT_048)

        self.assertEqual(
            result["task_id"],
            "PMBOT-OPENROUTER-048-PASSIVE-OPERATOR-SURFACE-046-BATCH",
        )
        self.assertEqual(result["status"], "completed_pushed")
        self.assertEqual(result["openrouter_calls_performed"], 0)
        self.assertEqual(result["polymarket_api_calls_performed"], 0)
        self.assertEqual(result["source_046_status"], "completed_pushed")
        self.assertEqual(result["source_047_status"], "completed_pushed")
        self.assertIs(result["passive_operator_surface_created"], True)
        self.assertEqual(result["surfaced_market_ids"], EXPECTED_MARKET_IDS)
        self.assertIn(
            "pm_bot/llm/operator_openrouter_batch_surface_046.v1.json",
            result["surface_artifact_paths"],
        )


if __name__ == "__main__":
    unittest.main()

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SURFACE_JSON = ROOT / "pm_bot" / "llm" / "operator_openrouter_batch_surface_051.v1.json"
SURFACE_MD = ROOT / "pm_bot" / "llm" / "operator_openrouter_batch_surface_051.v1.md"
RESULT_051 = ROOT / "docs" / "PMBOT_OPENROUTER_051_RESULT.json"
RESULT_052 = ROOT / "docs" / "PMBOT_OPENROUTER_052_RESULT.json"

EXPECTED_MARKET_IDS = ["569344", "569366", "569368", "569373", "573656"]

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
    "no_market_action_guidance",
    "no_probability_ev_edge_confidence_side_selection",
    "no_buy_sell_hold_enter_exit",
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


class OperatorOpenrouterBatchSurface051Tests(unittest.TestCase):
    def test_surface_shape_and_authority_flags(self):
        surface = _load_json(SURFACE_JSON)

        self.assertEqual(surface["surface_version"], "operator_openrouter_batch_surface.v1")
        self.assertEqual(surface["contract_version"], "operator_openrouter_batch_surface.v1")
        self.assertEqual(
            surface["task_id"],
            "PMBOT-OPENROUTER-053-N5-SURFACE-WORKBENCH-INVENTORY-UX-AND-CONTOUR-AUDIT",
        )
        self.assertEqual(
            surface["source_protocol_task"],
            "PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL",
        )
        self.assertEqual(
            surface["source_batch_task"],
            "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        )
        self.assertEqual(
            surface["source_baseline_task"],
            "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        )
        self.assertEqual(surface["status"], "passive_operator_surface_created")

        for flag in REQUIRED_TRUE_FLAGS:
            self.assertIs(surface[flag], True)
            self.assertIs(surface["safety_summary"][flag], True)

        self.assertEqual(surface["openrouter_calls_performed_by_this_task"], 0)
        self.assertEqual(surface["polymarket_api_calls_performed_by_this_task"], 0)

    def test_source_status_and_aggregate_values(self):
        surface = _load_json(SURFACE_JSON)
        result_051 = _load_json(RESULT_051)
        result_052 = _load_json(RESULT_052)

        self.assertEqual(result_051["status"], "completed_pushed")
        self.assertEqual(result_052["status"], "completed_pushed")
        self.assertEqual(result_051["completed_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(result_052["analyzed_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(surface["surfaced_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(surface["accepted_for_operator_review_count"], 5)
        self.assertEqual(surface["blocked_count"], 0)
        self.assertEqual(surface["total_openrouter_calls_performed"], 5)
        self.assertEqual(surface["aggregate_usage"]["prompt_tokens"], 20768)
        self.assertEqual(surface["aggregate_usage"]["completion_tokens"], 9119)
        self.assertEqual(surface["aggregate_usage"]["total_tokens"], 29887)
        self.assertEqual(surface["aggregate_usage"]["average_tokens_per_market"], 5977.4)
        self.assertEqual(surface["aggregate_cost"]["total_cost"], 0.199089)
        self.assertEqual(surface["aggregate_cost"]["average_cost_per_market"], 0.0398178)
        self.assertEqual(surface["aggregate_cost"]["max_total_cost_allowed"], 0.35)
        self.assertIs(surface["aggregate_cost"]["cost_cap_exceeded"], False)

    def test_normalization_quality_and_estimated_vs_actual(self):
        surface = _load_json(SURFACE_JSON)

        self.assertEqual(surface["normalization"]["policy"], "fenced_json_normalization.v1")
        self.assertEqual(surface["normalization"]["fenced_response_count"], 5)
        self.assertEqual(surface["normalization"]["normalized_response_count"], 5)
        self.assertEqual(surface["normalization"]["clean_raw_json_response_count"], 0)
        self.assertIs(surface["normalization"]["raw_response_preserved"], True)
        self.assertIs(surface["normalization"]["semantic_repair_allowed"], False)
        self.assertEqual(surface["quality"]["schema_validation_accepted_count"], 5)
        self.assertEqual(surface["quality"]["acceptance_gate_passed_count"], 5)
        self.assertEqual(surface["quality"]["prohibited_content_detected_count"], 0)
        self.assertEqual(surface["quality"]["forbidden_phrase_detected_count"], 0)
        self.assertIs(surface["quality"]["baseline_suitable_for_future_controlled_expansion"], True)
        self.assertEqual(surface["estimated_vs_actual"]["estimated_total_tokens"], 31143.333335)
        self.assertEqual(surface["estimated_vs_actual"]["actual_total_tokens"], 29887)
        self.assertEqual(surface["estimated_vs_actual"]["token_delta_actual_minus_estimate"], -1256.333335)
        self.assertEqual(surface["estimated_vs_actual"]["estimated_total_cost"], 0.20997)
        self.assertEqual(surface["estimated_vs_actual"]["actual_total_cost"], 0.199089)
        self.assertEqual(surface["estimated_vs_actual"]["cost_delta_actual_minus_estimate"], -0.010881)

    def test_per_market_entries_are_passive_and_point_to_existing_artifacts(self):
        surface = _load_json(SURFACE_JSON)
        entries = surface["per_market_passive_entries"]

        self.assertEqual([entry["market_id"] for entry in entries], EXPECTED_MARKET_IDS)
        for entry in entries:
            self.assertIs(entry["accepted_for_operator_review"], True)
            self.assertIs(entry["openrouter_call_performed"], True)
            self.assertIs(entry["raw_response_preserved"], True)
            self.assertIs(entry["semantic_repair_allowed"], False)
            self.assertIs(entry["normalization_policy_applied"], True)
            self.assertEqual(entry["normalization_policy_version"], "fenced_json_normalization.v1")
            self.assertIs(entry["raw_response_was_markdown_fenced"], True)
            self.assertIs(entry["prohibited_content_detected"], False)
            self.assertIs(entry["forbidden_phrase_detected"], False)
            self.assertIs(entry["schema_validation_passed"], True)
            self.assertIs(entry["acceptance_gate_passed"], True)
            self.assertGreater(entry["usage_summary"]["total_tokens"], 0)
            self.assertGreater(entry["cost_summary"]["cost"], 0)
            self.assertTrue(entry["sanitized_operator_note"])
            self.assertIs(entry["no_market_action_guidance"], True)

            for artifact in entry["artifact_pointers"].values():
                self.assertEqual(artifact["role"], "read_only_input")
                self.assertFalse(Path(artifact["path"]).is_absolute())
                self.assertTrue((ROOT / artifact["path"]).exists(), artifact["path"])

    def test_surface_markdown_does_not_contain_market_action_guidance_language(self):
        text = SURFACE_MD.read_text(encoding="utf-8").lower()
        matches = {
            pattern
            for pattern in FORBIDDEN_MARKET_ACTION_PATTERNS
            if re.search(pattern, text)
        }
        self.assertEqual(matches, set())


if __name__ == "__main__":
    unittest.main()

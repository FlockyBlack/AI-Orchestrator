import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SURFACE_JSON = ROOT / "pm_bot" / "llm" / "operator_live_review_surface_563650.v1.json"
SURFACE_MD = ROOT / "pm_bot" / "llm" / "operator_live_review_surface_563650.v1.md"

EXPECTED_SOURCE_TASK_ID = "PMBOT-OPENROUTER-028-FIRST-ONE-MARKET-LIVE-CALL-WITH-SAFE-USER-ENV-IMPORT"
EXPECTED_SESSION_ID = "pmbot_openrouter_028_first_live_call_with_safe_user_env_import"
EXPECTED_MODEL = "anthropic/claude-sonnet-4.5"

REQUIRED_SOURCE_ARTIFACTS = {
    "result_json": "docs/PMBOT_OPENROUTER_028_RESULT.json",
    "content_json": (
        "pm_bot/llm/openrouter_test_artifacts/"
        "pmbot_openrouter_028_first_live_call_with_safe_user_env_import/"
        "openrouter_sonnet_563650_content.json"
    ),
    "validation_json": (
        "pm_bot/llm/openrouter_test_artifacts/"
        "pmbot_openrouter_028_first_live_call_with_safe_user_env_import/"
        "openrouter_sonnet_563650_validation.json"
    ),
    "summary_json": (
        "pm_bot/llm/openrouter_test_artifacts/"
        "pmbot_openrouter_028_first_live_call_with_safe_user_env_import/"
        "openrouter_test_summary_563650.json"
    ),
}

REQUIRED_TRUE_FLAGS = {
    "operator_review_only",
    "no_trading_authority",
    "no_runtime_authority",
    "no_queue_mutation",
    "no_recommendations",
}

REQUIRED_SAFETY_TRUE_FLAGS = {
    "passive_context_only",
    "offline_artifact_surface_only",
    "no_openrouter_call_needed",
    "no_api_key_needed",
    "no_network_needed",
    "no_polymarket_api_call_needed",
    "no_wallet_or_private_key_access",
    "no_orders",
    "no_trading",
    "no_runtime_wiring",
    "no_dispatcher_changes",
    "no_background_workers",
    "no_browser_automation",
}

REQUIRED_EXCLUSION_FALSE_FLAGS = {
    "runtime_wiring_changed",
    "dispatcher_changed",
    "queue_mutated",
    "background_worker_added",
    "dashboard_or_status_exporter_updated",
}

FORBIDDEN_FIELD_NAMES = {
    "probability",
    "probabilities",
    "expected_value",
    "ev",
    "edge",
    "confidence",
    "confidence_score",
    "side",
    "side_selection",
    "selected_side",
    "recommended_side",
    "recommendation",
    "recommendations",
    "buy",
    "sell",
    "hold",
    "enter",
    "exit",
}
ALLOWED_SAFETY_FIELD_NAMES = {"no_recommendations"}


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _walk_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            yield from _walk_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _walk_keys(item)


class OperatorLiveReviewSurfaceTests(unittest.TestCase):
    def test_surface_shape_and_required_flags(self):
        surface = _load_json(SURFACE_JSON)

        self.assertEqual(surface["contract_version"], "operator_live_review_surface.v1")
        self.assertEqual(
            surface["task_id"],
            "PMBOT-OPENROUTER-029-LIVE-RESPONSE-OPERATOR-REVIEW-SURFACING",
        )
        self.assertEqual(surface["source_task_id"], EXPECTED_SOURCE_TASK_ID)
        self.assertEqual(surface["market_id"], "563650")
        self.assertEqual(surface["session_id"], EXPECTED_SESSION_ID)
        self.assertEqual(surface["model"], EXPECTED_MODEL)
        self.assertEqual(surface["status"], "accepted_for_operator_review")

        for flag in REQUIRED_TRUE_FLAGS:
            self.assertIs(surface[flag], True)
            self.assertIs(surface["authority_flags"][flag], True)

        for flag in REQUIRED_SAFETY_TRUE_FLAGS:
            self.assertIs(surface["safety_flags"][flag], True)

        for flag in REQUIRED_EXCLUSION_FALSE_FLAGS:
            self.assertIs(surface["explicit_exclusions"][flag], False)

    def test_source_artifacts_are_read_only_inputs_and_consistent_with_028_result(self):
        surface = _load_json(SURFACE_JSON)
        result_028 = _load_json(ROOT / REQUIRED_SOURCE_ARTIFACTS["result_json"])

        for artifact_id, expected_path in REQUIRED_SOURCE_ARTIFACTS.items():
            artifact = surface["source_artifacts"][artifact_id]
            self.assertEqual(artifact["path"], expected_path)
            self.assertEqual(artifact["role"], "read_only_input")
        self.assertTrue((ROOT / REQUIRED_SOURCE_ARTIFACTS["result_json"]).exists())

        source_validation = surface["source_validation"]
        self.assertEqual(result_028["market_id"], "563650")
        self.assertEqual(result_028["session_id"], EXPECTED_SESSION_ID)
        self.assertEqual(result_028["model"], EXPECTED_MODEL)
        self.assertIs(result_028["live_call"]["performed"], True)
        self.assertEqual(result_028["live_call"]["openrouter_calls_count"], 1)
        self.assertIs(result_028["validation"]["accepted_for_operator_review"], True)
        self.assertIs(result_028["validation"]["prohibited_trading_content_detected"], False)
        self.assertIs(result_028["safety"]["api_key_leaked"], False)

        self.assertIs(source_validation["market_id_consistent"], True)
        self.assertIs(source_validation["session_id_consistent"], True)
        self.assertIs(source_validation["model_consistent"], True)
        self.assertIs(source_validation["live_call_performed"], True)
        self.assertIs(source_validation["openrouter_calls_count_is_one"], True)
        self.assertIs(source_validation["raw_response_validator_passed"], True)
        self.assertEqual(source_validation["validation_status"], "accepted")
        self.assertIs(source_validation["validation_valid"], True)
        self.assertEqual(source_validation["summary_status"], "completed")
        self.assertIs(source_validation["summary_sonnet_valid"], True)
        self.assertIs(source_validation["accepted_for_operator_review"], True)
        self.assertIs(source_validation["prohibited_trading_content_detected"], False)
        self.assertIs(source_validation["api_key_leaked"], False)

    def test_no_decision_or_scoring_fields_are_introduced(self):
        surface = _load_json(SURFACE_JSON)
        forbidden_keys = {
            key
            for key in _walk_keys(surface)
            if key in FORBIDDEN_FIELD_NAMES and key not in ALLOWED_SAFETY_FIELD_NAMES
        }
        self.assertEqual(forbidden_keys, set())

    def test_markdown_surfaces_same_boundaries(self):
        markdown = SURFACE_MD.read_text(encoding="utf-8")

        for expected in (
            "source_task_id: PMBOT-OPENROUTER-028-FIRST-ONE-MARKET-LIVE-CALL-WITH-SAFE-USER-ENV-IMPORT",
            "market_id: 563650",
            "model: anthropic/claude-sonnet-4.5",
            "status: accepted_for_operator_review",
            "operator_review_only: true",
            "no_trading_authority: true",
            "no_runtime_authority: true",
            "no_queue_mutation: true",
            "no_recommendations: true",
            "no_openrouter_call_needed: true",
            "no_api_key_needed: true",
            "no_network_needed: true",
            "no_runtime_wiring: true",
            "dispatcher_changed: false",
            "queue_mutated: false",
        ):
            self.assertIn(expected, markdown)


if __name__ == "__main__":
    unittest.main()

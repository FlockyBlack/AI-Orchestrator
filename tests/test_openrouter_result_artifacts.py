import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_result(name: str) -> dict:
    path = ROOT / "docs" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_openrouter_037_status_is_reconciled_before_retry_artifacts():
    result_037 = _load_result("PMBOT_OPENROUTER_037_RESULT.json")
    result_038 = _load_result("PMBOT_OPENROUTER_038_RESULT.json")
    result_039 = _load_result("PMBOT_OPENROUTER_039_RESULT.json")

    assert result_037["status"] == "completed_pushed"
    assert result_037["commit_hash"] == "5dbc94872527194cb139d1159990062616079e50"
    assert result_037["pushed"] is True
    assert result_037["openrouter_calls_performed"] == 0

    assert result_038["status"] == "blocked_precheck_failed"
    assert result_038["total_openrouter_calls_performed"] == 0
    assert (
        result_038["fail_fast_reason"]
        == "precheck_failed:037_result_status_expected_completed_pushed_actual_completed_local_checks_passed_pending_commit_push"
    )

    assert result_039["source_037_status_before"] == "completed_local_checks_passed_pending_commit_push"
    assert result_039["source_037_status_after"] == "completed_pushed"
    assert result_039["source_037_reconciled"] is True
    assert result_039["source_038_preserved_as_blocked"] is True
    assert result_039["source_038_openrouter_calls_performed"] == 0


def test_openrouter_041_records_fenced_json_normalization_policy():
    result_040 = _load_result("PMBOT_OPENROUTER_040_RESULT.json")
    result_041 = _load_result("PMBOT_OPENROUTER_041_RESULT.json")

    assert result_040["status"] == "blocked_markdown_fence_detected"
    assert result_040["total_openrouter_calls_performed"] == 1
    assert result_040["fail_fast_reason"] == "markdown_fence_detected:569333"

    assert result_041["task_id"] == "PMBOT-OPENROUTER-041-FENCED-JSON-NORMALIZATION-POLICY"
    assert result_041["status"] == "completed_pushed"
    assert result_041["openrouter_calls_performed"] == 0
    assert result_041["polymarket_api_calls_performed"] == 0
    assert result_041["source_040_status"] == "blocked_markdown_fence_detected"
    assert result_041["source_040_fail_fast_reason"] == "markdown_fence_detected:569333"
    assert result_041["fenced_json_normalization_policy_added"] is True
    assert result_041["normalization_policy_version"] == "fenced_json_normalization.v1"
    assert result_041["semantic_repair_allowed"] is False
    assert result_041["raw_response_preserved"] is True
    assert result_041["raw_strict_json_parse_remains_strict"] is True
    assert result_041["secret_scan_passed"] is True
    assert result_041["safety_summary"]["openrouter_calls_performed"] == 0
    assert result_041["safety_summary"]["polymarket_api_calls_performed"] == 0


def test_openrouter_042_records_prohibited_content_block_inputs():
    result_042 = _load_result("PMBOT_OPENROUTER_042_RESULT.json")

    assert result_042["status"] == "blocked_prohibited_content_detected"
    assert result_042["fail_fast_reason"] == "prohibited_content_detected:569334"
    assert result_042["total_openrouter_calls_performed"] == 2
    assert result_042["attempted_market_ids"] == ["569333", "569334"]
    assert result_042["completed_market_ids"] == ["569333"]
    assert result_042["skipped_market_ids"] == ["569343"]
    safety = result_042["safety_boundary_summary"]
    assert safety["no_polymarket_api_calls"] is True
    assert safety["no_wallet_orders_trading"] is True
    assert safety["no_runtime_dispatcher_background_browser_queue_changes"] is True
    assert safety["api_key_value_printed"] is False
    assert safety["api_key_value_written"] is False
    assert safety["api_key_leaked"] is False


def test_openrouter_043_records_local_only_prohibited_content_diagnostic():
    result_043 = _load_result("PMBOT_OPENROUTER_043_RESULT.json")

    assert result_043["task_id"] == "PMBOT-OPENROUTER-043-ANALYZE-042-PROHIBITED-CONTENT-BLOCK"
    assert result_043["status"] == "completed_pushed"
    assert result_043["openrouter_calls_performed"] == 0
    assert result_043["polymarket_api_calls_performed"] == 0
    assert result_043["source_042_status"] == "blocked_prohibited_content_detected"
    assert result_043["source_042_fail_fast_reason"] == "prohibited_content_detected:569334"
    assert result_043["analyzed_market_id"] == "569334"
    assert result_043["diagnostic_classification"] == "false_positive_validator_rule"
    assert result_043["prohibited_content_true_positive"] is False
    assert result_043["prohibited_content_false_positive"] is True
    assert result_043["prohibited_content_uncertain"] is False
    assert result_043["validator_reporting_improved"] is True
    assert result_043["prompt_hardening_performed"] is True
    assert result_043["secret_scan_passed"] is True
    assert result_043["safety_summary"]["openrouter_calls_performed"] == 0
    assert result_043["safety_summary"]["polymarket_api_calls_performed"] == 0

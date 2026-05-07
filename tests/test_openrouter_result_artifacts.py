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

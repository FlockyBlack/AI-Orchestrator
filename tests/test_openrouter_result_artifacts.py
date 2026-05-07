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

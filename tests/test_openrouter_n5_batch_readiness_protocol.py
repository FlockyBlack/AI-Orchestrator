import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_openrouter_050_result_records_protocol_only_n5_readiness():
    result = _load_json("docs/PMBOT_OPENROUTER_050_RESULT.json")

    assert result["task_id"] == "PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL"
    assert result["status"] == "completed_pushed"
    assert result["head_before"] == "1a98e6be63c76380acfc3b86f66f26b51ae898f8"
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["source_046_status"] == "completed_pushed"
    assert result["source_047_status"] == "completed_pushed"
    assert result["source_048_status"] == "completed_pushed"
    assert result["source_049_status"] == "completed_pushed"
    assert result["n5_protocol_created"] is True
    assert result["n5_live_batch_approved"] is False
    assert result["proposed_future_task_id"] == "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL"
    assert result["candidate_selection_status"] == "ready"
    assert result["proposed_market_ids"] == ["569344", "569366", "569368", "569373", "573656"]
    assert result["max_openrouter_calls_allowed_future"] == 5
    assert result["no_retries_future"] is True
    assert result["fail_fast_future"] is True
    assert result["max_total_cost_allowed"] == 0.35
    assert result["normalization_policy_version"] == "fenced_json_normalization.v1"
    assert result["raw_response_preserved_required"] is True
    assert result["semantic_repair_allowed"] is False
    assert result["secret_scan_passed"] is True


def test_openrouter_n5_protocol_structure_and_safety_boundaries():
    protocol = _load_json("pm_bot/llm/openrouter_n5_batch_readiness_protocol.v1.json")

    assert protocol["protocol_version"] == "openrouter_n5_batch_readiness_protocol.v1"
    assert protocol["protocol_only"] is True
    assert protocol["live_calls_approved"] is False
    assert protocol["future_task_id"] == "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL"
    assert protocol["source_successful_batch_task"] == "PMBOT-OPENROUTER-046"
    assert protocol["source_baseline_task"] == "PMBOT-OPENROUTER-047"
    assert protocol["source_surface_task"] == "PMBOT-OPENROUTER-048"
    assert protocol["source_workbench_task"] == "PMBOT-OPENROUTER-049"
    assert protocol["model"] == "anthropic/claude-sonnet-4.5"
    assert protocol["max_openrouter_calls_allowed"] == 5
    assert protocol["no_retries"] is True
    assert protocol["fail_fast"] is True

    if protocol["candidate_selection_status"] == "ready":
        assert len(protocol["proposed_market_ids"]) == 5
        assert protocol["proposed_market_ids"] == ["569344", "569366", "569368", "569373", "573656"]

    assert protocol["cost_cap"]["max_total_cost_allowed_usd"] == 0.35
    assert protocol["normalization_policy"]["version"] == "fenced_json_normalization.v1"
    assert protocol["normalization_policy"]["raw_response_preserved"] is True
    assert protocol["normalization_policy"]["semantic_repair_allowed"] is False

    safety = protocol["safety_boundaries"]
    for flag in (
        "no_trading_authority",
        "no_queue_authority",
        "no_runtime_authority",
        "no_dispatcher_authority",
        "no_wallet_or_order_authority",
        "no_orders",
        "no_trading",
        "no_runtime_wiring",
        "no_dispatcher_changes",
        "no_background_workers",
        "no_browser_automation",
        "no_queue_mutation",
        "no_polymarket_api_calls",
        "no_openrouter_calls_in_050",
        "no_api_key_value_read_or_written",
    ):
        assert safety[flag] is True

    assert any("missing local packet or prompt artifact" in item for item in protocol["fail_fast_conditions"])
    assert any("missing aggregate usage or cost artifact" in item for item in protocol["fail_fast_conditions"])
    assert protocol["expected_artifacts"]["future_session_dir"].endswith(
        "pmbot_openrouter_051_controlled_n5_batch_live_call"
    )
    assert "python -m compileall pm_bot" in protocol["required_validation_commands"]

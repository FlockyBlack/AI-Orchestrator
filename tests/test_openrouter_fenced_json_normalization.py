import json
from pathlib import Path

from pm_bot.llm import run_openrouter_prompt_test as harness


ROOT = Path(__file__).resolve().parents[1]


def _artifact_path(display_path):
    path = Path(display_path)
    return path if path.is_absolute() else ROOT / path


def _structured_critic_payload():
    return {
        "contract_version": harness.CRITIC_CONTRACT_VERSION,
        "json_validity": {
            "candidate_parses_json": True,
            "candidate_top_level_object": True,
        },
        "schema_review": {
            "status": "pass",
            "missing_required_fields": [],
            "type_issues": [],
        },
        "safety_boundary_review": {
            "has_trading_recommendation": False,
            "has_side_selection": False,
            "has_probability_estimate": False,
            "has_ev_or_edge_or_scoring": False,
            "has_order_instruction": False,
            "has_wallet_or_credential_instruction": False,
            "has_market_decision": False,
            "has_runtime_or_dispatcher_instruction": False,
            "has_external_data_claim": False,
        },
        "operator_readiness": {
            "ready_for_operator_review": True,
            "ready_for_resolution": False,
            "ready_for_trading_action": False,
        },
        "issues": [],
        "verdict": "pass",
    }


def test_clean_raw_json_object_is_accepted_without_normalization():
    validation, parsed = harness.validate_raw_json_content('{"notes":["operator review only"]}')

    assert validation["valid"] is True
    assert validation["raw_response_was_markdown_fenced"] is False
    assert validation["raw_strict_json_parse_passed"] is True
    assert validation["normalized_from_markdown_fence"] is False
    assert validation["normalization_policy_applied"] is False
    assert parsed == {"notes": ["operator review only"]}


def test_json_fenced_object_with_only_whitespace_is_normalized_and_accepted():
    raw = '\n  ```json\n{"notes":["operator review only"]}\n```\n'

    validation, parsed = harness.validate_raw_json_content(raw)

    assert validation["valid"] is True
    assert validation["raw_response_was_markdown_fenced"] is True
    assert validation["raw_strict_json_parse_passed"] is False
    assert validation["normalized_from_markdown_fence"] is True
    assert validation["normalized_json_parse_passed"] is True
    assert validation["normalized_content_used"] is True
    assert validation["normalization_policy_version"] == harness.NORMALIZATION_POLICY_VERSION
    assert parsed == {"notes": ["operator review only"]}


def test_unlabeled_fenced_object_is_normalized_and_accepted():
    validation, parsed = harness.validate_raw_json_content('```\n{"notes":["operator review only"]}\n```')

    assert validation["valid"] is True
    assert validation["normalization"]["fence_language"] is None
    assert validation["normalized_from_markdown_fence"] is True
    assert parsed == {"notes": ["operator review only"]}


def test_fenced_json_with_prose_before_is_rejected():
    validation, parsed = harness.validate_raw_json_content('Here is JSON:\n```json\n{"ok": true}\n```')

    assert validation["valid"] is False
    assert validation["normalization_policy_applied"] is True
    assert validation["normalized_from_markdown_fence"] is False
    assert any(error["code"] == "markdown_fence_present" for error in validation["errors"])
    assert parsed is None


def test_fenced_json_with_prose_after_is_rejected():
    validation, parsed = harness.validate_raw_json_content('```json\n{"ok": true}\n```\nDone.')

    assert validation["valid"] is False
    assert validation["normalization_policy_applied"] is True
    assert validation["normalized_from_markdown_fence"] is False
    assert any(error["code"] == "markdown_fence_present" for error in validation["errors"])
    assert parsed is None


def test_multiple_fenced_blocks_are_rejected():
    raw = '```json\n{"a": 1}\n```\n```json\n{"b": 2}\n```'

    validation, parsed = harness.validate_raw_json_content(raw)

    assert validation["valid"] is False
    assert validation["normalized_from_markdown_fence"] is False
    assert any(error["code"] == "multiple_markdown_fences_present" for error in validation["errors"])
    assert parsed is None


def test_fenced_json_array_is_rejected_where_object_is_required():
    validation, parsed = harness.validate_raw_json_content('```json\n[{"ok": true}]\n```')

    assert validation["valid"] is False
    assert validation["normalized_from_markdown_fence"] is False
    assert validation["normalized_json_parse_passed"] is False
    assert any(error["code"] == "json_top_level_not_object" for error in validation["errors"])
    assert parsed == [{"ok": True}]


def test_fenced_malformed_json_is_rejected():
    validation, parsed = harness.validate_raw_json_content('```json\n{"ok": true\n```')

    assert validation["valid"] is False
    assert validation["normalized_from_markdown_fence"] is False
    assert validation["normalized_json_parse_passed"] is False
    assert any(error["code"] == "normalized_json_parse_failed" for error in validation["errors"])
    assert parsed is None


def test_non_json_markdown_content_is_rejected():
    validation, parsed = harness.validate_raw_json_content("# Review\n\n- operator review only")

    assert validation["valid"] is False
    assert validation["raw_response_was_markdown_fenced"] is False
    assert validation["normalization_policy_applied"] is False
    assert any(error["code"] == "json_parse_failed" for error in validation["errors"])
    assert parsed is None


def test_normalized_fenced_json_still_fails_prohibited_trading_language():
    raw = '```json\n{"notes":["Buy YES"]}\n```'

    validation, parsed = harness.validate_raw_json_content(raw)

    assert validation["valid"] is False
    assert validation["normalized_from_markdown_fence"] is True
    assert validation["checks"]["forbidden_language_absent"] is False
    assert any(error["code"].startswith("forbidden_phrase:") for error in validation["errors"])
    diagnostic = validation["prohibited_content_diagnostics"][0]
    assert diagnostic["gate_id"] == "raw_or_normalized_json"
    assert diagnostic["detector_rule_id"] == "forbidden_phrase:buy"
    assert diagnostic["violation_category"] == "market_action_keyword"
    assert diagnostic["diagnostic_status"] == "ambiguous_needs_operator_review"
    assert diagnostic["checked_content_source"] == "normalized_content"
    assert "[redacted:safety-term]" in diagnostic["safe_redacted_snippet"]
    assert parsed == {"notes": ["Buy YES"]}


def test_normalized_fenced_json_still_fails_probability_ev_edge_confidence_and_side_content():
    payload = {
        "notes": [
            "Probability is 62%.",
            "EV is positive.",
            "There is an edge.",
            "Confidence is high.",
            "Select the YES side.",
        ]
    }
    raw = "```json\n" + json.dumps(payload) + "\n```"

    validation, parsed = harness.validate_raw_json_content(raw)

    assert validation["valid"] is False
    assert validation["normalized_from_markdown_fence"] is True
    assert validation["checks"]["forbidden_language_absent"] is False
    codes = {error["code"] for error in validation["errors"]}
    assert "forbidden_phrase:probability_value" in codes
    assert "forbidden_phrase:ev" in codes
    assert "forbidden_phrase:edge" in codes
    assert "forbidden_phrase:confidence" in codes
    assert "forbidden_phrase:choose_side" in codes
    assert parsed == payload


def test_result_artifacts_preserve_raw_vs_normalized_flags(tmp_path):
    def fake_api_caller(model, system_prompt, user_content, api_key):
        if model == harness.DEFAULT_SONNET_MODEL:
            return {
                "id": "fake-sonnet-response",
                "model": model,
                "provider": "unit-test-provider",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                "choices": [
                    {
                        "message": {
                            "content": '```json\n{"contract_version":"unit_test","notes":["operator review only"]}\n```'
                        }
                    }
                ],
            }
        return {
            "id": "fake-critic-response",
            "model": model,
            "provider": "unit-test-provider",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [{"message": {"content": json.dumps(_structured_critic_payload())}}],
        }

    code, summary = harness.run_harness(
        ["--market-id", "563650", "--out-dir", str(tmp_path)],
        env={"OPENROUTER_API_KEY": "unit-test-openrouter-key"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 0
    assert summary["status"] == "completed"
    assert summary["fenced_json_normalization_policy_enabled"] is True
    assert summary["normalization_policy_version"] == harness.NORMALIZATION_POLICY_VERSION
    assert summary["semantic_repair_allowed"] is False
    assert summary["sonnet_raw_markdown_fence_detected"] is True
    assert summary["sonnet_raw_strict_json_parse_passed"] is False
    assert summary["sonnet_normalized_json_parse_passed"] is True
    assert summary["sonnet_normalized_content_used"] is True

    sonnet_paths = summary["artifact_paths"]["sonnet"]
    validation = json.loads(_artifact_path(sonnet_paths["validation"]).read_text(encoding="utf-8"))
    raw = json.loads(_artifact_path(sonnet_paths["raw"]).read_text(encoding="utf-8"))

    for artifact in (validation, raw):
        assert artifact["raw_response_was_markdown_fenced"] is True
        assert artifact["raw_strict_json_parse_passed"] is False
        assert artifact["normalized_json_parse_passed"] is True
        assert artifact["normalization_policy_applied"] is True
        assert artifact["normalization_policy_version"] == harness.NORMALIZATION_POLICY_VERSION
        assert artifact["normalized_content_used"] is True
    assert raw["raw_content"].startswith("```json")

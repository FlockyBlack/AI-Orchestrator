import json
from pathlib import Path

import pytest

from pm_bot.llm import run_openrouter_prompt_test as harness


ROOT = Path(__file__).resolve().parents[1]


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


def _artifact_path(display_path):
    path = Path(display_path)
    return path if path.is_absolute() else ROOT / path


def test_prompt_selection_by_market_id_563650():
    selection = harness.select_prompt(market_id="563650", root=ROOT)

    assert selection["market_id"] == "563650"
    assert selection["prompt_path"] == ROOT / "pm_bot" / "llm" / "manual_packet_batch" / "563650_prompt.v1.md"
    assert selection["packet_path"] == ROOT / "pm_bot" / "llm" / "manual_packet_batch" / "563650_packet.v1.json"


def test_default_prompt_selection_ignores_legacy_prompt():
    legacy = ROOT / "pm_bot" / "llm" / "real_local_market_llm_trial_prompt.v1.md"
    assert legacy.exists()

    selection = harness.select_prompt(root=ROOT)

    assert selection["prompt_path"] != legacy
    assert selection["prompt_path"].parent == ROOT / "pm_bot" / "llm" / "manual_packet_batch"
    assert selection["prompt_path"].name.endswith("_prompt.v1.md")


def _assert_strict_json_prompt_contract(text):
    for fragment in (
        "Return exactly one raw JSON object.",
        "Do not wrap the JSON in Markdown.",
        "Do not use ```json fences",
        "Do not include prose before or after the JSON",
        "Any Markdown fencing makes the response invalid.",
    ):
        assert fragment in text


def test_openrouter_system_prompts_contain_no_markdown_fence_contract():
    for prompt in (harness.SONNET_SYSTEM_PROMPT, harness.CRITIC_SYSTEM_PROMPT):
        _assert_strict_json_prompt_contract(prompt)
        assert "first character must be {" in prompt
        assert "last character must be }" in prompt
        assert "operator-review readiness only, never trading approval" in prompt


def test_selected_live_prompt_contains_no_markdown_fence_contract():
    prompt = (ROOT / "pm_bot" / "llm" / "manual_packet_batch" / "569333_prompt.v1.md").read_text(
        encoding="utf-8"
    )

    _assert_strict_json_prompt_contract(prompt)
    assert "The first character must be `{` and the last character must be `}`." in prompt
    assert "Acceptance is operator-review readiness only, never trading approval." in prompt


def test_raw_json_validation_passes_valid_object():
    validation, parsed = harness.validate_raw_json_content(
        '{"contract_version":"unit_test","notes":["operator review only"]}'
    )

    assert validation["valid"] is True
    assert validation["status"] == "accepted"
    assert parsed["contract_version"] == "unit_test"


def test_raw_json_validation_rejects_markdown_fenced_json_by_default():
    validation, parsed = harness.validate_raw_json_content('```json\n{"ok": true}\n```')

    assert validation["valid"] is False
    assert validation["recovery"]["applied"] is False
    assert validation["checks"]["raw_starts_with_object"] is False
    assert validation["checks"]["raw_ends_with_object"] is False
    assert validation["checks"]["raw_no_markdown_fences"] is False
    assert any(error["code"] == "markdown_fence_present" for error in validation["errors"])
    assert not any(warning["code"] == "markdown_fence_recovered" for warning in validation["warnings"])
    assert parsed is None


def test_raw_json_validation_recovers_markdown_fenced_json_when_allowed():
    validation, parsed = harness.validate_raw_json_content(
        '```json\n{"ok": true}\n```',
        allow_local_json_fence_repair=True,
    )

    assert validation["valid"] is True
    assert validation["recovery"]["applied"] is True
    assert validation["recovery"]["method"] == "single_json_markdown_fence"
    assert validation["checks"]["raw_no_markdown_fences"] is False
    assert any(warning["code"] == "markdown_fence_recovered" for warning in validation["warnings"])
    assert parsed == {"ok": True}


def test_raw_json_validation_recovers_unlabeled_markdown_fenced_json_when_allowed():
    validation, parsed = harness.validate_raw_json_content(
        '```\n{"ok": true}\n```',
        allow_local_json_fence_repair=True,
    )

    assert validation["valid"] is True
    assert validation["recovery"]["applied"] is True
    assert validation["recovery"]["method"] == "single_json_markdown_fence"
    assert validation["recovery"]["fence_language"] is None
    assert parsed == {"ok": True}


def test_raw_json_validation_fail_on_repair_rejects_recovered_json():
    validation, parsed = harness.validate_raw_json_content(
        '```json\n{"ok": true}\n```',
        allow_local_json_fence_repair=True,
        fail_on_repair=True,
    )

    assert validation["valid"] is False
    assert validation["recovery"]["applied"] is True
    assert any(error["code"] == "markdown_fence_recovered_fail_on_repair" for error in validation["errors"])
    assert parsed == {"ok": True}


def test_raw_json_validation_rejects_prose_wrapped_markdown_fence():
    validation, _parsed = harness.validate_raw_json_content(
        'Here is JSON:\n```json\n{"ok": true}\n```',
        allow_local_json_fence_repair=True,
    )

    assert validation["valid"] is False
    assert validation["recovery"]["applied"] is False
    assert any(error["code"] == "markdown_fence_present" for error in validation["errors"])


def test_raw_json_validation_rejects_non_json_markdown_fence():
    validation, _parsed = harness.validate_raw_json_content(
        '```python\n{"ok": true}\n```',
        allow_local_json_fence_repair=True,
    )

    assert validation["valid"] is False
    assert validation["recovery"]["applied"] is False
    assert any(error["code"] == "markdown_fence_present" for error in validation["errors"])


def test_raw_json_validation_allows_benign_edge_cases_phrase():
    validation, parsed = harness.validate_raw_json_content(
        '{"notes":["How should edge cases be handled during manual review?"]}'
    )

    assert validation["valid"] is True
    assert parsed["notes"] == ["How should edge cases be handled during manual review?"]


def test_raw_json_validation_still_rejects_trading_edge_phrase():
    validation, _parsed = harness.validate_raw_json_content('{"notes":["This market has an edge."]}')

    assert validation["valid"] is False
    assert any(error["code"] == "forbidden_phrase:edge" for error in validation["errors"])


@pytest.mark.parametrize(
    "phrase",
    [
        "No side selection, outcome estimate, EV, edge, trade execution, wallet, or order instructions are present.",
        "No EV, edge, wallet, or order instructions are present.",
        "No trading recommendations detected.",
        "No side selection detected.",
        "No wallet instructions detected.",
        "No order instructions detected.",
        "The candidate avoids market-decision language.",
        "The artifact is not ready for market-resolution analysis.",
        "It is not suitable for resolution, market decisioning, or automated workflow progression.",
        "not actionable",
        "do_not_trade",
        "not_actionable",
        "ready_for_resolution_or_action: false",
        "The text does not select Yes/No or imply an outcome.",
        "Does not select Yes or No.",
        "No Yes/No side is selected.",
        "No Yes or No outcome is selected.",
        "No side is selected.",
        "No side selection detected.",
        "Does not choose a side.",
        "No outcome side is chosen.",
        "The candidate does not imply an outcome.",
        "No outcome estimate is provided.",
    ],
)
def test_raw_json_validation_allows_negative_safety_attestations(phrase):
    payload = {"safety_boundary_compliance": {"review_notes": [phrase]}}
    validation, parsed = harness.validate_raw_json_content(json.dumps(payload))

    assert validation["valid"] is True
    assert validation["checks"]["forbidden_language_absent"] is True
    assert parsed == payload


@pytest.mark.parametrize(
    "phrase",
    [
        "I recommend buying YES",
        "Buy YES",
        "Sell NO",
        "Select the YES side",
        "The recommended side is YES",
        "EV is positive",
        "There is an edge",
        "This has value scoring",
        "Place an order",
        "Use wallet credentials",
        "Enter the position",
        "Exit the position",
        "This market decision is to buy",
        "Probability is 62%",
        "Outcome estimate is YES likely",
        "No reason not to buy YES",
        "No downside to selecting YES",
        "No reason not to select Yes",
        "No downside to choosing Yes",
        "No issue selecting No",
        "Do not avoid choosing Yes",
        "Not selecting No would be wrong",
        "Does not select Yes or No, choose Yes",
        "No problem using wallet credentials",
        "No issue placing an order",
        "No need to avoid trading",
    ],
)
def test_raw_json_validation_rejects_market_action_and_bypass_language(phrase):
    payload = {"notes": [phrase]}
    validation, parsed = harness.validate_raw_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["forbidden_language_absent"] is False
    assert any(error["code"].startswith("forbidden_phrase:") for error in validation["errors"])
    assert parsed == payload


@pytest.mark.parametrize(
    "phrase",
    [
        "Select Yes",
        "Select No",
        "Choose Yes",
        "Choose No",
        "The selected side is Yes",
        "The selected side is No",
        "YES is the side",
        "NO is the side",
        "Outcome is Yes",
        "Outcome is No",
        "I would choose Yes",
        "I would choose No",
        "The market should resolve Yes",
        "The market should resolve No",
        "Likely Yes",
        "Likely No",
    ],
)
def test_raw_json_validation_rejects_yes_no_side_selection_language(phrase):
    payload = {"notes": [phrase]}
    validation, parsed = harness.validate_raw_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["forbidden_language_absent"] is False
    assert any(error["code"].startswith("forbidden_phrase:") for error in validation["errors"])
    assert parsed == payload


def test_sanitized_old_free_text_critic_fixture_is_regression_rejected_without_network():
    fixture_path = (
        ROOT
        / "tests"
        / "fixtures"
        / "openrouter_prompt_test"
        / "old_free_text_critic_response.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    validation, parsed = harness.validate_critic_json_content(
        fixture["critic_text"],
        allow_local_json_fence_repair=True,
    )

    assert validation["valid"] is False
    assert validation["checks"]["critic_schema_valid"] is False
    assert any(error["code"] == "critic_schema_missing_field" for error in validation["errors"])
    assert parsed == fixture["expected_parsed_content"]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "overall_assessment": (
                "Minor edits are recommended to remove a temporal inconsistency and reduce "
                "forecasting-adjacent wording."
            )
        },
        {"notes": ["Recommended JSON edits"]},
        {"recommended_candidate_json_edits": [{"field": "risk_notes", "edit": "Remove relative timing."}]},
        {"notes": ["candidate JSON edits are recommended"]},
        {"suggested_fix": "Use source-neutral wording."},
        {"notes": ["schema correction is recommended"]},
        {"notes": ["operator review is recommended"]},
        {"notes": ["manual source review is recommended"]},
        {"notes": ["for definitional validation only, not probability estimation"]},
    ],
)
def test_raw_json_validation_allows_safe_edit_review_recommendation_language(payload):
    validation, parsed = harness.validate_raw_json_content(json.dumps(payload))

    assert validation["valid"] is True
    assert validation["checks"]["forbidden_language_absent"] is True
    assert parsed == payload


@pytest.mark.parametrize(
    "phrase",
    [
        "I recommend buying YES",
        "recommend selling",
        "trading recommendation",
        "market recommendation",
        "recommended side",
        "recommended outcome",
        "recommended trade",
        "recommended position",
        "recommended entry",
        "recommended exit",
        "recommend placing an order",
        "recommend a market decision",
    ],
)
def test_raw_json_validation_rejects_trading_recommendation_language(phrase):
    payload = {"notes": [phrase]}
    validation, parsed = harness.validate_raw_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["forbidden_language_absent"] is False
    assert any(error["code"].startswith("forbidden_phrase:") for error in validation["errors"])
    assert parsed == payload


def test_raw_json_validation_fails_array_non_object_json():
    validation, _parsed = harness.validate_raw_json_content('[{"ok": true}]')

    assert validation["valid"] is False
    assert any(error["code"] == "json_top_level_not_object" for error in validation["errors"])


def test_structured_critic_valid_object_passes():
    payload = _structured_critic_payload()

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is True
    assert validation["status"] == "accepted"
    assert validation["checks"]["critic_schema_valid"] is True
    assert validation["checks"]["critic_safety_booleans_passed"] is True
    assert validation["checks"]["critic_verdict"] == "pass"
    assert parsed == payload


@pytest.mark.parametrize("field", list(harness.CRITIC_SAFETY_FIELDS))
def test_structured_critic_safety_boolean_true_fails(field):
    payload = _structured_critic_payload()
    payload["safety_boundary_review"][field] = True

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["critic_schema_valid"] is True
    assert validation["checks"]["critic_safety_booleans_passed"] is False
    assert any(error["code"] == f"critic_safety_boundary_true:{field}" for error in validation["errors"])
    assert parsed == payload


def test_structured_critic_ready_for_trading_action_true_fails():
    payload = _structured_critic_payload()
    payload["operator_readiness"]["ready_for_trading_action"] = True

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["critic_schema_valid"] is True
    assert validation["checks"]["ready_for_trading_action_false"] is False
    assert any(error["code"] == "critic_ready_for_trading_action_true" for error in validation["errors"])
    assert parsed == payload


def test_structured_critic_acceptance_is_operator_review_only_not_trading_approval():
    payload = _structured_critic_payload()

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is True
    assert parsed["operator_readiness"]["ready_for_operator_review"] is True
    assert parsed["operator_readiness"]["ready_for_resolution"] is False
    assert parsed["operator_readiness"]["ready_for_trading_action"] is False


def test_structured_critic_missing_required_fields_fails():
    payload = _structured_critic_payload()
    del payload["safety_boundary_review"]["has_side_selection"]

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["critic_schema_valid"] is False
    assert any(
        error["code"] == "critic_schema_missing_field"
        and error["path"] == "safety_boundary_review.has_side_selection"
        for error in validation["errors"]
    )
    assert parsed == payload


def test_structured_critic_invalid_verdict_fails():
    payload = _structured_critic_payload()
    payload["verdict"] = "maybe"

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["critic_schema_valid"] is False
    assert any(error["code"] == "critic_schema_invalid_enum" and error["path"] == "verdict" for error in validation["errors"])
    assert parsed == payload


def test_structured_critic_does_not_require_free_text_negative_safety_notes():
    payload = _structured_critic_payload()
    payload["issues"] = [
        {
            "severity": "low",
            "category": "operator_readiness",
            "field": "operator_readiness.ready_for_resolution",
            "message_code": "manual_review_only_not_ready_for_resolution",
        }
    ]
    payload["schema_review"]["status"] = "pass_with_notes"
    payload["verdict"] = "pass_with_notes"

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is True
    assert validation["checks"]["critic_schema_valid"] is True
    assert validation["checks"]["critic_safety_booleans_passed"] is True
    assert parsed == payload


def test_structured_critic_rejects_explicit_forbidden_instruction_text():
    payload = _structured_critic_payload()
    payload["issues"] = [
        {
            "severity": "high",
            "category": "safety",
            "field": "I recommend buying YES",
            "message_code": "detected_violation",
        }
    ]

    validation, parsed = harness.validate_critic_json_content(json.dumps(payload))

    assert validation["valid"] is False
    assert validation["checks"]["critic_schema_valid"] is True
    assert validation["checks"]["critic_explicit_forbidden_instruction_absent"] is False
    assert any(error["code"].startswith("critic_forbidden_instruction:") for error in validation["errors"])
    assert parsed == payload


def test_structured_critic_json_fence_repair_behavior_still_works():
    payload = _structured_critic_payload()
    raw = "```json\n" + json.dumps(payload) + "\n```"

    strict_validation, _strict_parsed = harness.validate_critic_json_content(raw)
    repaired_validation, repaired_parsed = harness.validate_critic_json_content(
        raw,
        allow_local_json_fence_repair=True,
    )

    assert strict_validation["valid"] is False
    assert any(error["code"] == "markdown_fence_present" for error in strict_validation["errors"])
    assert repaired_validation["valid"] is True
    assert repaired_validation["recovery"]["applied"] is True
    assert repaired_parsed == payload


def test_artifact_serialization_does_not_include_fake_api_key(tmp_path):
    fake_key = "sk-fake-openrouter-key-123456789"
    artifact = {
        "api_key": fake_key,
        "nested": {
            "authorization": f"Bearer {fake_key}",
            "safe": "operator review only",
        },
    }
    path = tmp_path / "artifact.json"

    harness._write_json(path, artifact, known_secrets=(fake_key,))

    text = path.read_text(encoding="utf-8")
    assert fake_key not in text
    payload = json.loads(text)
    assert payload["api_key"] == "[redacted]"
    assert payload["nested"]["authorization"] == "[redacted]"


def test_dry_run_does_not_require_openrouter_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    code, summary = harness.run_harness(
        ["--dry-run", "--market-id", "563650", "--out-dir", str(tmp_path)],
        env={},
        root=ROOT,
    )

    assert code == 0
    assert summary["status"] == "dry_run_ready"
    assert summary["sonnet_called"] is False
    assert summary["artifact_paths"]["summary"].endswith("openrouter_test_summary_563650.json")


def test_critic_skipped_when_sonnet_invalid(tmp_path):
    calls = []

    def fake_api_caller(model, system_prompt, user_content, api_key):
        calls.append(model)
        return {
            "id": "fake-sonnet-response",
            "model": model,
            "provider": "unit-test-provider",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [{"message": {"content": '[{"not":"an object"}]'}}],
        }

    code, summary = harness.run_harness(
        ["--market-id", "563650", "--out-dir", str(tmp_path)],
        env={"OPENROUTER_API_KEY": "sk-fake-openrouter-key-123456789"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 1
    assert calls == [harness.DEFAULT_SONNET_MODEL]
    assert summary["status"] == "sonnet_validation_failed"
    assert summary["sonnet_called"] is True
    assert summary["sonnet_valid"] is False
    assert summary["critic_called"] is False


def test_fenced_sonnet_json_is_strict_failure_by_default_and_skips_critic(tmp_path):
    calls = []

    def fake_api_caller(model, system_prompt, user_content, api_key):
        calls.append(model)
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

    code, summary = harness.run_harness(
        ["--market-id", "563650", "--out-dir", str(tmp_path)],
        env={"OPENROUTER_API_KEY": "sk-fake-openrouter-key-123456789"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 1
    assert calls == [harness.DEFAULT_SONNET_MODEL]
    assert summary["status"] == "sonnet_validation_failed"
    assert summary["sonnet_valid"] is False
    assert summary["sonnet_json_recovered"] is False
    assert summary["critic_called"] is False

    sonnet_paths = summary["artifact_paths"]["sonnet"]
    sonnet_content = json.loads(_artifact_path(sonnet_paths["content"]).read_text(encoding="utf-8"))
    sonnet_validation = json.loads(_artifact_path(sonnet_paths["validation"]).read_text(encoding="utf-8"))
    sonnet_raw = json.loads(_artifact_path(sonnet_paths["raw"]).read_text(encoding="utf-8"))

    assert sonnet_content["status"] == "not_valid_json_object"
    assert sonnet_content["raw_content"].startswith("```json")
    assert sonnet_validation["recovery"]["applied"] is False
    assert any(error["code"] == "markdown_fence_present" for error in sonnet_validation["errors"])
    assert sonnet_raw["raw_content"].startswith("```json")


def test_fenced_sonnet_json_is_recovered_before_critic(tmp_path):
    calls = []

    def fake_api_caller(model, system_prompt, user_content, api_key):
        calls.append({"model": model, "user_content": user_content})
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
            "choices": [
                {
                    "message": {
                        "content": json.dumps(_structured_critic_payload())
                    }
                }
            ],
        }

    code, summary = harness.run_harness(
        ["--market-id", "563650", "--out-dir", str(tmp_path), "--allow-local-json-fence-repair"],
        env={"OPENROUTER_API_KEY": "sk-fake-openrouter-key-123456789"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 0
    assert [call["model"] for call in calls] == [harness.DEFAULT_SONNET_MODEL, harness.DEFAULT_CRITIC_MODEL]
    assert summary["status"] == "completed"
    assert summary["sonnet_valid"] is True
    assert summary["sonnet_json_recovered"] is True
    assert summary["critic_called"] is True
    assert summary["critic_valid"] is True
    assert summary["critic_schema_valid"] is True
    assert summary["critic_safety_booleans_passed"] is True
    assert summary["critic_verdict"] == "pass"
    assert "```" not in calls[1]["user_content"]

    sonnet_paths = summary["artifact_paths"]["sonnet"]
    sonnet_content = json.loads(_artifact_path(sonnet_paths["content"]).read_text(encoding="utf-8"))
    sonnet_validation = json.loads(_artifact_path(sonnet_paths["validation"]).read_text(encoding="utf-8"))
    sonnet_raw = json.loads(_artifact_path(sonnet_paths["raw"]).read_text(encoding="utf-8"))

    assert sonnet_content["contract_version"] == "unit_test"
    assert sonnet_validation["recovery"]["applied"] is True
    assert sonnet_raw["raw_content"].startswith("```json")


def test_critic_content_artifact_wraps_valid_structured_json_object(tmp_path):
    calls = []

    def fake_api_caller(model, system_prompt, user_content, api_key):
        calls.append(model)
        if model == harness.DEFAULT_SONNET_MODEL:
            return {
                "id": "fake-sonnet-response",
                "model": model,
                "provider": "unit-test-provider",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                "choices": [
                    {
                        "message": {
                            "content": '{"contract_version":"unit_test","notes":["operator review only"]}'
                        }
                    }
                ],
            }
        critic_payload = _structured_critic_payload()
        critic_payload["schema_review"]["status"] = "pass_with_notes"
        critic_payload["issues"] = [
            {
                "severity": "low",
                "category": "schema",
                "field": "notes",
                "message_code": "source_neutral_wording_preferred",
            }
        ]
        critic_payload["verdict"] = "pass_with_notes"
        return {
            "id": "fake-critic-response",
            "model": model,
            "provider": "unit-test-provider",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [
                {
                    "message": {
                        "content": json.dumps(critic_payload)
                    }
                }
            ],
        }

    code, summary = harness.run_harness(
        ["--market-id", "563650", "--out-dir", str(tmp_path)],
        env={"OPENROUTER_API_KEY": "sk-fake-openrouter-key-123456789"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 0
    assert calls == [harness.DEFAULT_SONNET_MODEL, harness.DEFAULT_CRITIC_MODEL]
    assert summary["status"] == "completed"
    assert summary["critic_valid"] is True
    assert summary["critic_schema_valid"] is True
    assert summary["critic_safety_booleans_passed"] is True
    assert summary["critic_verdict"] == "pass_with_notes"

    critic_paths = summary["artifact_paths"]["critic"]
    critic_content = json.loads(_artifact_path(critic_paths["content"]).read_text(encoding="utf-8"))
    critic_validation = json.loads(_artifact_path(critic_paths["validation"]).read_text(encoding="utf-8"))

    assert critic_validation["checks"]["parses_json"] is True
    assert critic_validation["checks"]["critic_schema_valid"] is True
    assert critic_validation["valid"] is True
    assert critic_content["content_status"] == "accepted"
    assert critic_content["status"] == "accepted"
    assert critic_content["parsed_content"]["issues"][0]["field"] == "notes"
    assert critic_content["parsed_content"]["verdict"] == "pass_with_notes"


def test_critic_content_artifact_marks_parsed_rejected_json_without_non_json_status(tmp_path):
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
                            "content": '{"contract_version":"unit_test","notes":["operator review only"]}'
                        }
                    }
                ],
            }
        critic_payload = _structured_critic_payload()
        critic_payload["safety_boundary_review"]["has_trading_recommendation"] = True
        critic_payload["issues"] = [
            {
                "severity": "high",
                "category": "safety",
                "field": "safety_boundary_review.has_trading_recommendation",
                "message_code": "safety_boundary_violation_detected",
            }
        ]
        critic_payload["verdict"] = "fail"
        return {
            "id": "fake-critic-response",
            "model": model,
            "provider": "unit-test-provider",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [
                {
                    "message": {
                        "content": json.dumps(critic_payload)
                    }
                }
            ],
        }

    code, summary = harness.run_harness(
        ["--market-id", "563650", "--out-dir", str(tmp_path)],
        env={"OPENROUTER_API_KEY": "sk-fake-openrouter-key-123456789"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 1
    assert summary["status"] == "critic_validation_failed"
    assert summary["critic_valid"] is False
    assert summary["critic_schema_valid"] is True
    assert summary["critic_safety_booleans_passed"] is False
    assert summary["critic_verdict"] == "fail"

    critic_paths = summary["artifact_paths"]["critic"]
    critic_content = json.loads(_artifact_path(critic_paths["content"]).read_text(encoding="utf-8"))
    critic_validation = json.loads(_artifact_path(critic_paths["validation"]).read_text(encoding="utf-8"))

    assert critic_validation["checks"]["parses_json"] is True
    assert critic_validation["checks"]["top_level_object"] is True
    assert critic_validation["checks"]["critic_schema_valid"] is True
    assert critic_content["content_status"] == "rejected"
    assert critic_content["status"] == "rejected"
    assert critic_content["parsed_content"]["safety_boundary_review"]["has_trading_recommendation"] is True
    assert critic_content["status"] != "not_valid_json_object"


def test_fenced_sonnet_json_fail_on_repair_stops_before_critic(tmp_path):
    calls = []

    def fake_api_caller(model, system_prompt, user_content, api_key):
        calls.append(model)
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

    code, summary = harness.run_harness(
        [
            "--market-id",
            "563650",
            "--out-dir",
            str(tmp_path),
            "--allow-local-json-fence-repair",
            "--fail-on-repair",
        ],
        env={"OPENROUTER_API_KEY": "sk-fake-openrouter-key-123456789"},
        api_caller=fake_api_caller,
        root=ROOT,
    )

    assert code == 1
    assert calls == [harness.DEFAULT_SONNET_MODEL]
    assert summary["status"] == "sonnet_validation_failed"
    assert summary["sonnet_valid"] is False
    assert summary["sonnet_json_recovered"] is True
    assert summary["critic_called"] is False

    sonnet_paths = summary["artifact_paths"]["sonnet"]
    sonnet_validation = json.loads(_artifact_path(sonnet_paths["validation"]).read_text(encoding="utf-8"))

    assert sonnet_validation["recovery"]["applied"] is True
    assert any(error["code"] == "markdown_fence_recovered_fail_on_repair" for error in sonnet_validation["errors"])

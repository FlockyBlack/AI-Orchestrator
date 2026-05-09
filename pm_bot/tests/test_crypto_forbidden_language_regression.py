from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_014_CRYPTO_FORBIDDEN_LANGUAGE_REGRESSION_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_forbidden_language_regression.valid.json")
TASK_ID = "PMBOT-CRYPTO-LIVE-014-CRYPTO-FORBIDDEN-LANGUAGE-REGRESSION-LOCAL-ONLY"
CONTRACT_ID = "pmbot-crypto-forbidden-language-regression"
CONTRACT_VERSION = "pmbot_crypto_forbidden_language_regression.v1"
REGRESSION_ID = "pmbot-crypto-forbidden-language-regression-001"
REGRESSION_NAME = "pmbot-crypto-forbidden-language-regression"
RUN_MODE = "local_static_crypto_forbidden_language_regression"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")

EXPECTED_EXCLUDED_PREFIXES = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)
EXPECTED_CATEGORY_TOKENS = {
    "trade_action_terms": ("buy", "sell", "hold", "enter", "exit"),
    "forecast_metric_terms": ("forecast", "probability", "confidence", "edge", "ev", "odds", "score", "scoring"),
    "selection_terms": ("pick", "selection", "recommendation", "recommendations", "side"),
    "exposure_terms": ("stake", "wager"),
    "crypto_position_terms": ("long", "short", "leverage"),
}
EXPECTED_SAMPLE_IDS = (
    "crypto_forbidden_language_regression_001.clean_operator_review_reference",
    "crypto_forbidden_language_regression_001.clean_crypto_readiness_reference",
    "crypto_forbidden_language_regression_001.trade_action_terms",
    "crypto_forbidden_language_regression_001.forecast_metric_terms",
    "crypto_forbidden_language_regression_001.selection_terms",
    "crypto_forbidden_language_regression_001.exposure_terms",
    "crypto_forbidden_language_regression_001.crypto_position_terms",
    "crypto_forbidden_language_regression_001.mixed_crypto_terms",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "crypto_forbidden_language_regression_fixture",
    "crypto_forbidden_language_regression_document",
    "crypto_forbidden_language_regression_contract_test",
    "base_forbidden_language_regression_suite_fixture",
    "base_forbidden_language_regression_suite_document",
    "crypto_ci_safe_validation_subset_fixture",
    "crypto_ci_safe_validation_subset_document",
    "queue_template_validation_test",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "crypto_data_refresh_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "forbidden_language_samples_are_literal_tokens_only": True,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_output_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "paperlive_execution_allowed": False,
    "regression_artifact_runtime_input_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "supervised_live_transition_allowed": False,
    "threshold_comparison_output_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_crypto_forbidden_language_regression_fixture_has_expected_contract() -> None:
    regression = _load_regression()

    assert tuple(regression.keys()) == tuple(sorted(regression.keys()))
    assert regression["task_id"] == TASK_ID
    assert regression["regression_id"] == REGRESSION_ID
    assert regression["regression_name"] == REGRESSION_NAME
    assert regression["contract_id"] == CONTRACT_ID
    assert regression["contract_version"] == CONTRACT_VERSION
    assert regression["run_mode"] == RUN_MODE
    assert regression["created_at"] == "2026-05-09T05:00:00Z"
    assert regression["local_only"] is True
    assert regression["operator_review_required"] is True
    assert regression["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert regression["errors"] == []
    assert regression["warnings"] == []


def test_forbidden_language_categories_are_fixed_literal_token_sets() -> None:
    regression = _load_regression()

    assert tuple(category["category_id"] for category in regression["forbidden_language_categories"]) == tuple(
        EXPECTED_CATEGORY_TOKENS
    )
    for category in regression["forbidden_language_categories"]:
        assert tuple(category.keys()) == ("category_id", "detection_tokens", "operator_review_status", "review_label")
        assert tuple(category["detection_tokens"]) == EXPECTED_CATEGORY_TOKENS[category["category_id"]]
        assert category["operator_review_status"] == OPERATOR_REVIEW_STATUS


def test_regression_samples_are_static_literal_token_or_clean_samples() -> None:
    regression = _load_regression()

    assert tuple(sample["sample_id"] for sample in regression["regression_samples"]) == EXPECTED_SAMPLE_IDS
    for sample in regression["regression_samples"]:
        assert tuple(sample.keys()) == (
            "expected_categories",
            "expected_result",
            "operator_review_status",
            "sample_id",
            "sample_kind",
            "sample_text",
        )
        assert sample["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert sample["sample_kind"] in {"clean_local_review_sample", "literal_token_detection_only"}
        if sample["sample_kind"] == "clean_local_review_sample":
            assert sample["expected_categories"] == []
            assert sample["expected_result"] == "clear_for_operator_review"
            assert sample["sample_text"].startswith("Clean local-review sample:")
        else:
            assert sample["expected_categories"]
            assert sample["expected_result"] == "flag_for_operator_review"
            assert sample["sample_text"].startswith("Literal crypto safety-token sample:")


def test_regression_sample_detection_is_deterministic() -> None:
    regression = _load_regression()

    for sample in regression["regression_samples"]:
        assert _detected_categories(sample["sample_text"], regression) == sample["expected_categories"]


def test_literal_samples_do_not_form_operator_instructions() -> None:
    regression = _load_regression()
    forbidden_instruction_phrases = (
        "best pick",
        "buy no",
        "buy yes",
        "enter position",
        "exit position",
        "go long",
        "go short",
        "place order",
        "recommended side",
        "sell no",
        "sell yes",
        "should buy",
        "should sell",
        "stake amount",
        "take position",
        "use leverage",
        "wager amount",
    )

    for sample in regression["regression_samples"]:
        normalized = sample["sample_text"].lower()
        assert not any(phrase in normalized for phrase in forbidden_instruction_phrases)


def test_source_artifacts_are_allowed_existing_local_references() -> None:
    regression = _load_regression()

    assert tuple(regression["allowed_path_prefixes"]) == ALLOWED_LOCAL_PREFIXES
    assert tuple(item["artifact_id"] for item in regression["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for item in regression["source_artifacts"]:
        assert tuple(item.keys()) == (
            "artifact_id",
            "artifact_role",
            "artifact_type",
            "local_reference",
            "operator_review_status",
            "source_task_id",
        )
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert item["source_task_id"]
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    regression = _load_regression()

    assert regression["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]
    assert [record["command_label"] for record in regression["validation_command_records"]] == regression[
        "required_validation_commands"
    ]
    for record in regression["validation_command_records"]:
        assert tuple(record.keys()) == ("command_label", "local_reference", "operator_review_status", "status")
        assert record["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert record["status"] == "not_run_static_record"
        _assert_allowed_existing_local_reference(record["local_reference"])


def test_excluded_prefixes_match_sensitive_and_execution_boundaries() -> None:
    regression = _load_regression()

    assert tuple(regression["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES


def test_safety_boundaries_are_closed_for_crypto_forbidden_language_regression() -> None:
    regression = _load_regression()

    assert regression["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert regression["safety_boundaries"]["forbidden_language_samples_are_literal_tokens_only"] is True
    assert regression["safety_boundaries"]["local_fixtures_only"] is True
    assert regression["safety_boundaries"]["local_static_samples_only"] is True
    assert regression["safety_boundaries"]["operator_review_required"] is True
    assert regression["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in regression["safety_boundaries"].items() if key.endswith("_allowed"))


def test_summary_counts_match_crypto_forbidden_language_regression_content() -> None:
    regression = _load_regression()

    assert regression["summary_counts"] == {
        "allowed_path_prefixes": len(regression["allowed_path_prefixes"]),
        "clear_samples": sum(
            1 for sample in regression["regression_samples"] if sample["expected_result"] == "clear_for_operator_review"
        ),
        "errors": len(regression["errors"]),
        "excluded_path_prefixes": len(regression["excluded_path_prefixes"]),
        "flagged_samples": sum(
            1 for sample in regression["regression_samples"] if sample["expected_result"] == "flag_for_operator_review"
        ),
        "forbidden_language_categories": len(regression["forbidden_language_categories"]),
        "regression_samples": len(regression["regression_samples"]),
        "required_validation_commands": len(regression["required_validation_commands"]),
        "source_artifacts": len(regression["source_artifacts"]),
        "validation_command_records": len(regression["validation_command_records"]),
        "warnings": len(regression["warnings"]),
    }


def test_documentation_registers_crypto_forbidden_language_regression_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Regression: `{REGRESSION_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "Literal-token samples only; no operator instruction samples." in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This regression is not execution approval and is not runtime input." in document


def _load_regression() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(ALLOWED_LOCAL_PREFIXES)
    assert Path(local_reference).exists()


def _detected_categories(sample_text: str, regression: dict) -> list[str]:
    tokens = _tokenize(sample_text)
    detected: list[str] = []
    for category in regression["forbidden_language_categories"]:
        if tokens & set(category["detection_tokens"]):
            detected.append(category["category_id"])
    return detected


def _tokenize(value: str) -> set[str]:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    return {token for token in normalized.split("_") if token}

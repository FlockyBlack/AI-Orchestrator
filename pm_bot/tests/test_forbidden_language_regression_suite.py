from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("docs/PMBOT_SAFETY_005_FORBIDDEN_LANGUAGE_REGRESSION_SUITE_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/safety/forbidden_language_regression_suite.valid.json")
TASK_ID = "PMBOT-SAFETY-005-FORBIDDEN-LANGUAGE-REGRESSION-SUITE-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_forbidden_language_regression_suite.v1"
RUN_MODE = "local_static_forbidden_language_regression_suite"
SUITE_ID = "pmbot_forbidden_language_regression_suite_001"
SUITE_NAME = "pmbot-forbidden-language-regression-suite"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_ALLOWED_PREFIXES = (
    "docs/",
    "pm_bot/tests/",
    "tests/",
)
EXPECTED_CATEGORY_TOKENS = {
    "trade_action_terms": ("buy", "sell", "hold", "enter", "exit"),
    "forecast_metric_terms": ("forecast", "probability", "confidence", "edge", "ev", "odds", "score", "scoring"),
    "selection_terms": ("pick", "selection", "recommendation", "recommendations", "side"),
    "exposure_terms": ("stake", "wager"),
}
EXPECTED_SAMPLE_IDS = (
    "forbidden_language_regression_suite_001.clean_operator_review_reference",
    "forbidden_language_regression_suite_001.trade_action_terms_lowercase",
    "forbidden_language_regression_suite_001.trade_action_terms_case_and_punctuation",
    "forbidden_language_regression_suite_001.forecast_metric_terms",
    "forbidden_language_regression_suite_001.selection_terms",
    "forbidden_language_regression_suite_001.exposure_terms",
    "forbidden_language_regression_suite_001.mixed_terms",
    "forbidden_language_regression_suite_001.clean_boundary_reference",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "forbidden_action_scan_doc",
    "sensitive_path_exclusion_audit_doc",
    "forbidden_action_scan_fixture",
    "queue_template_safety_contract",
    "forbidden_language_regression_suite_fixture",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "forbidden_language_samples_are_literal_tokens_only": True,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_output_allowed": False,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_forbidden_language_regression_suite_fixture_has_expected_contract() -> None:
    suite = _load_suite()

    assert tuple(suite.keys()) == tuple(sorted(suite.keys()))
    assert suite["task_id"] == TASK_ID
    assert suite["suite_id"] == SUITE_ID
    assert suite["suite_name"] == SUITE_NAME
    assert suite["contract_version"] == CONTRACT_VERSION
    assert suite["run_mode"] == RUN_MODE
    assert suite["created_at"] == "2026-05-09T03:00:00Z"
    assert suite["local_only"] is True
    assert suite["operator_review_required"] is True
    assert suite["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert suite["errors"] == []
    assert suite["warnings"] == []


def test_forbidden_language_categories_are_fixed_literal_token_sets() -> None:
    suite = _load_suite()

    assert tuple(category["category_id"] for category in suite["forbidden_language_categories"]) == tuple(
        EXPECTED_CATEGORY_TOKENS
    )
    for category in suite["forbidden_language_categories"]:
        assert set(category) == {
            "category_id",
            "detection_tokens",
            "operator_review_status",
            "review_label",
        }
        assert tuple(category["detection_tokens"]) == EXPECTED_CATEGORY_TOKENS[category["category_id"]]
        assert category["operator_review_status"] == OPERATOR_REVIEW_STATUS


def test_regression_samples_are_static_literal_token_or_clean_samples() -> None:
    suite = _load_suite()

    assert tuple(sample["sample_id"] for sample in suite["regression_samples"]) == EXPECTED_SAMPLE_IDS
    for sample in suite["regression_samples"]:
        assert set(sample) == {
            "expected_categories",
            "expected_result",
            "operator_review_status",
            "sample_id",
            "sample_kind",
            "sample_text",
        }
        assert sample["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert sample["sample_kind"] in {"clean_local_review_sample", "literal_token_detection_only"}
        if sample["sample_kind"] == "clean_local_review_sample":
            assert sample["expected_categories"] == []
            assert sample["expected_result"] == "clear_for_operator_review"
            assert sample["sample_text"].startswith("Clean local-review sample:")
        else:
            assert sample["expected_categories"]
            assert sample["expected_result"] == "flag_for_operator_review"
            assert sample["sample_text"].startswith("Literal safety-token sample:")


def test_regression_sample_detection_is_deterministic() -> None:
    suite = _load_suite()

    for sample in suite["regression_samples"]:
        assert _detected_categories(sample["sample_text"], suite) == sample["expected_categories"]


def test_literal_samples_do_not_form_operator_instructions() -> None:
    suite = _load_suite()
    forbidden_instruction_phrases = (
        "best pick",
        "buy no",
        "buy yes",
        "enter position",
        "exit position",
        "place order",
        "recommended side",
        "sell no",
        "sell yes",
        "should buy",
        "should sell",
        "stake amount",
        "take position",
        "wager amount",
    )

    for sample in suite["regression_samples"]:
        normalized = sample["sample_text"].lower()
        assert not any(phrase in normalized for phrase in forbidden_instruction_phrases)


def test_source_artifacts_are_allowed_existing_local_references() -> None:
    suite = _load_suite()

    assert tuple(suite["allowed_path_prefixes"]) == EXPECTED_ALLOWED_PREFIXES
    assert tuple(item["artifact_id"] for item in suite["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for item in suite["source_artifacts"]:
        assert set(item) == {"artifact_id", "local_reference", "operator_review_status"}
        assert item["operator_review_status"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(item["local_reference"])


def test_safety_boundaries_close_forbidden_language_suite_surfaces() -> None:
    suite = _load_suite()

    assert suite["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert suite["safety_boundaries"]["forbidden_language_samples_are_literal_tokens_only"] is True
    assert suite["safety_boundaries"]["local_static_samples_only"] is True
    assert suite["safety_boundaries"]["operator_review_required"] is True
    assert suite["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in suite["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    suite = _load_suite()

    assert suite["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_forbidden_language_regression_suite_content() -> None:
    suite = _load_suite()

    assert suite["summary_counts"] == {
        "allowed_path_prefixes": len(suite["allowed_path_prefixes"]),
        "clear_samples": sum(
            1 for sample in suite["regression_samples"] if sample["expected_result"] == "clear_for_operator_review"
        ),
        "errors": len(suite["errors"]),
        "flagged_samples": sum(
            1 for sample in suite["regression_samples"] if sample["expected_result"] == "flag_for_operator_review"
        ),
        "forbidden_language_categories": len(suite["forbidden_language_categories"]),
        "regression_samples": len(suite["regression_samples"]),
        "required_validation_commands": len(suite["required_validation_commands"]),
        "source_artifacts": len(suite["source_artifacts"]),
        "warnings": len(suite["warnings"]),
    }


def test_documentation_registers_forbidden_language_suite_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Suite: `{SUITE_NAME}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "Literal-token samples only; no operator instruction samples." in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This suite is not execution approval and is not runtime input." in document


def _load_suite() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(EXPECTED_ALLOWED_PREFIXES)
    assert Path(local_reference).exists()


def _detected_categories(sample_text: str, suite: dict) -> list[str]:
    tokens = _tokenize(sample_text)
    detected: list[str] = []
    for category in suite["forbidden_language_categories"]:
        if tokens & set(category["detection_tokens"]):
            detected.append(category["category_id"])
    return detected


def _tokenize(value: str) -> set[str]:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    return {token for token in normalized.split("_") if token}

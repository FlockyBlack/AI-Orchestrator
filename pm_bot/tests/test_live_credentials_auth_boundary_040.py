from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.btc_market_analysis_order_intent import evaluate_btc_analysis_to_order_intent
from pm_bot.trading_core.live_canary_readiness import btc_market_readiness_blocker_categories
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
    summarize_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_credentials_auth_boundary import (
    DECISION_AUTH_BOUNDARY_REVIEW_READY,
    DECISION_AUTHENTICATED_ENDPOINTS_STILL_DISABLED,
    DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED,
    DECISION_MISSING_REQUIRED_CREDENTIALS,
    DECISION_ORDER_SUBMISSION_STILL_DISABLED,
    DECISION_SECRET_POLICY_VIOLATION,
    DECISION_SIGNING_STILL_DISABLED,
    REDACTED_CONFIGURED,
    REDACTED_MISSING,
    UI_REDACTION_WARNING,
    FakeLiveCredentialProvider,
    build_default_live_credentials_boundary_config,
    evaluate_live_auth_boundary_for_tiny_canary,
    evaluate_live_credentials_status,
    summarize_live_credentials_status,
    validate_live_credentials_boundary_config,
)
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    PolymarketBTCReadOnlyConnector,
    build_default_btc_fixture_market_payload,
    build_default_btc_read_only_config,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    DECISION_ALLOW_DRY_RUN,
    RiskLimitOrderIntent,
    build_default_risk_limit_policy,
    build_default_risk_limit_state,
    evaluate_risk_limits_for_order_intent,
)
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_live_credentials_config,
    validate_secret_boundary_result_artifact,
    validate_static_secret_boundary,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
FAKE_SECRET_VALUES = {
    "POLYMARKET_PRIVATE_KEY": "fake_private_material_never_output_040",
    "POLYMARKET_FUNDER_ADDRESS": "fake_funder_address_never_output_040",
    "POLYMARKET_CLOB_API_KEY": "fake_clob_key_never_output_040",
    "POLYMARKET_CLOB_SECRET": "fake_clob_secret_never_output_040",
    "POLYMARKET_CLOB_PASSPHRASE": "fake_clob_passphrase_never_output_040",
    "POLYMARKET_CHAIN_ID": "fake_chain_id_never_output_040",
    "POLYMARKET_NETWORK": "fake_network_never_output_040",
}
REQUESTED_BLOCKER_CATEGORIES = {
    "live_credentials_boundary_review_only",
    "live_credentials_not_operator_verified_for_live",
    "authenticated_endpoints_still_disabled",
    "signing_still_disabled",
    "order_submission_still_disabled",
    "live_wallet_funding_not_verified",
    "real_order_adapter_not_enabled",
}


def _config(*, live_mode: bool = False) -> dict[str, Any]:
    return build_default_live_credentials_boundary_config(
        live_mode_explicitly_requested=live_mode,
        generated_at=GENERATED_AT,
    )


def _present_provider(config: Mapping[str, Any]) -> FakeLiveCredentialProvider:
    values = {
        row["env_var_name"]: FAKE_SECRET_VALUES[row["env_var_name"]]
        for row in config["credential_requirements"]
    }
    return FakeLiveCredentialProvider(values)


def _btc_snapshot() -> dict[str, Any]:
    config = build_default_btc_read_only_config(generated_at=GENERATED_AT)
    result = PolymarketBTCReadOnlyConnector(config).build_snapshot_from_fixture_payload(
        build_default_btc_fixture_market_payload(observed_at=GENERATED_AT),
        current_time=GENERATED_AT,
    )
    return dict(result["snapshot"])


def _dry_run_intent() -> dict[str, Any]:
    return RiskLimitOrderIntent(
        intent_id="risk-auth-boundary-test-intent",
        market_id="btc-one-market-demo-market",
        market_slug="btc-one-market-demo",
        market_tag="BTC",
        market_category="bitcoin",
        side_label="track_primary_outcome",
        notional_usd=1.0,
        quantity=1.0,
        limit_price=1.0,
        intent_source="live_credentials_auth_boundary_040_test",
        created_at=GENERATED_AT,
        dry_run_only=True,
        operator_intent_reference="operator-intent:review-only",
        readiness_evidence_reference="readiness-evidence:review-only",
        audit_replay_reference="audit-replay:review-only",
    ).to_dict()


def _assert_no_fake_secret_values(value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, sort_keys=True)
    for fake_secret in FAKE_SECRET_VALUES.values():
        assert fake_secret not in serialized


def test_default_config_builds_deterministically_and_validates_symbolic_names() -> None:
    first = _config()
    second = _config()

    assert first == second
    assert first["required_credentials_count"] == 7
    assert validate_live_credentials_boundary_config(first, generated_at=GENERATED_AT)["valid"] is True
    assert validate_secret_boundary_live_credentials_config(first, generated_at=GENERATED_AT)["valid"] is True
    assert [row["env_var_name"] for row in first["credential_requirements"]] == [
        "POLYMARKET_PRIVATE_KEY",
        "POLYMARKET_FUNDER_ADDRESS",
        "POLYMARKET_CLOB_API_KEY",
        "POLYMARKET_CLOB_SECRET",
        "POLYMARKET_CLOB_PASSPHRASE",
        "POLYMARKET_CHAIN_ID",
        "POLYMARKET_NETWORK",
    ]
    assert first["allow_environment_provider"] is False
    assert first["authenticated_endpoints_enabled"] is False
    assert first["order_submission_enabled"] is False
    assert first["cryptographic_signing_enabled"] is False
    assert first["wallet_signing_enabled"] is False


def test_fake_provider_missing_present_partial_and_unsafe_values_are_redacted() -> None:
    config = _config(live_mode=True)
    missing_report = evaluate_live_credentials_status(config, FakeLiveCredentialProvider(), generated_at=GENERATED_AT)
    present_report = evaluate_live_credentials_status(config, _present_provider(config), generated_at=GENERATED_AT)
    partial_report = evaluate_live_credentials_status(
        config,
        FakeLiveCredentialProvider({"POLYMARKET_NETWORK": "fake_network_never_output_040"}),
        generated_at=GENERATED_AT,
    )
    unsafe_report = evaluate_live_credentials_status(
        config,
        FakeLiveCredentialProvider({"POLYMARKET_PRIVATE_KEY": "0x" + "a" * 64}),
        generated_at=GENERATED_AT,
    )

    assert missing_report["missing_credentials_count"] == config["required_credentials_count"]
    assert {row["redacted_preview"] for row in missing_report["credential_statuses"]} == {REDACTED_MISSING}
    assert present_report["live_credentials_configured"] is True
    assert present_report["missing_requirements"] == []
    assert {row["redacted_preview"] for row in present_report["credential_statuses"]} == {REDACTED_CONFIGURED}
    assert partial_report["missing_requirements"] == [
        row["requirement_id"]
        for row in config["credential_requirements"]
        if row["env_var_name"] != "POLYMARKET_NETWORK"
    ]
    assert unsafe_report["policy_violation_count"] == 1
    _assert_no_fake_secret_values(present_report)
    _assert_no_fake_secret_values(json.loads(json.dumps(present_report, sort_keys=True)))


def test_auth_boundary_review_ready_remains_non_executable_with_all_fake_credentials() -> None:
    config = _config(live_mode=True)
    decision = evaluate_live_auth_boundary_for_tiny_canary(
        config,
        _present_provider(config),
        generated_at=GENERATED_AT,
    )

    assert decision["decision_status"] == DECISION_AUTH_BOUNDARY_REVIEW_READY
    assert decision["live_credentials_configured"] is True
    assert decision["live_auth_ready_for_future_tiny_canary_review"] is True
    assert DECISION_AUTHENTICATED_ENDPOINTS_STILL_DISABLED in decision["boundary_statuses"]
    assert DECISION_SIGNING_STILL_DISABLED in decision["boundary_statuses"]
    assert DECISION_ORDER_SUBMISSION_STILL_DISABLED in decision["boundary_statuses"]
    assert decision["authenticated_endpoints_enabled"] is False
    assert decision["order_submission_enabled"] is False
    assert decision["cryptographic_signing_enabled"] is False
    assert decision["wallet_signing_enabled"] is False
    assert decision["allowed_for_live"] is False
    assert decision["canary_executable_now"] is False
    assert decision["live_execution_approved"] is False
    assert decision["real_execution_available"] is False
    assert decision["live_connector_enabled"] is False
    _assert_no_fake_secret_values(decision)


def test_auth_boundary_missing_live_mode_and_secret_policy_statuses_are_deterministic() -> None:
    config = _config()
    first = evaluate_live_auth_boundary_for_tiny_canary(config, _present_provider(config), generated_at=GENERATED_AT)
    second = evaluate_live_auth_boundary_for_tiny_canary(config, _present_provider(config), generated_at=GENERATED_AT)
    unsafe = evaluate_live_auth_boundary_for_tiny_canary(
        config,
        FakeLiveCredentialProvider({"POLYMARKET_PRIVATE_KEY": "Bearer unsafe-token"}),
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert first["decision_status"] == DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED
    assert unsafe["decision_status"] == DECISION_SECRET_POLICY_VIOLATION
    assert DECISION_MISSING_REQUIRED_CREDENTIALS in evaluate_live_auth_boundary_for_tiny_canary(
        _config(live_mode=True),
        FakeLiveCredentialProvider(),
        generated_at=GENERATED_AT,
    )["boundary_statuses"]


def test_risk_control_consumes_auth_boundary_but_allows_dry_run_only() -> None:
    config = _config(live_mode=True)
    decision = evaluate_live_auth_boundary_for_tiny_canary(
        config,
        _present_provider(config),
        generated_at=GENERATED_AT,
    )
    summary = summarize_live_credentials_status(decision, generated_at=GENERATED_AT)
    state = build_default_risk_limit_state(
        live_credentials_boundary_status=summary["live_credentials_boundary_status"],
        live_credentials_configured=summary["live_credentials_configured"],
        live_mode_explicitly_requested=summary["live_mode_explicitly_requested"],
        live_auth_ready_for_future_tiny_canary_review=summary[
            "live_auth_ready_for_future_tiny_canary_review"
        ],
        generated_at=GENERATED_AT,
    )
    risk_decision = evaluate_risk_limits_for_order_intent(
        _dry_run_intent(),
        state=state,
        policy=build_default_risk_limit_policy(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )

    assert risk_decision["decision_status"] == DECISION_ALLOW_DRY_RUN
    assert risk_decision["allowed_for_dry_run"] is True
    assert risk_decision["allowed_for_live"] is False
    assert DECISION_AUTHENTICATED_ENDPOINTS_STILL_DISABLED in risk_decision["live_block_reasons"]
    assert DECISION_SIGNING_STILL_DISABLED in risk_decision["live_block_reasons"]
    assert DECISION_ORDER_SUBMISSION_STILL_DISABLED in risk_decision["live_block_reasons"]


def test_btc_dry_run_order_intent_remains_dry_run_only_with_auth_boundary() -> None:
    config = _config(live_mode=True)
    auth_decision = evaluate_live_auth_boundary_for_tiny_canary(
        config,
        _present_provider(config),
        generated_at=GENERATED_AT,
    )
    result = evaluate_btc_analysis_to_order_intent(
        _btc_snapshot(),
        live_auth_boundary_decision=auth_decision,
        generated_at=GENERATED_AT,
    )

    assert result["dry_run_only"] is True
    assert result["order_intent_is_not_order_submission"] is True
    assert result["risk_decision_summary"]["risk_decision_status"] == DECISION_ALLOW_DRY_RUN
    assert result["summary"]["allowed_for_dry_run"] is True
    assert result["summary"]["allowed_for_live"] is False
    assert result["summary"]["live_credentials_boundary_status"] == DECISION_AUTH_BOUNDARY_REVIEW_READY
    assert result["allowed_for_live"] is False
    assert result["canary_executable_now"] is False


def test_ui_panel_surfaces_redacted_auth_section_without_execution_actions() -> None:
    summary = summarize_live_credentials_status(
        evaluate_live_auth_boundary_for_tiny_canary(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )
    blocker_matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=blocker_matrix,
        live_credentials_auth_boundary=summary,
        generated_at=GENERATED_AT,
    )
    panel = build_operator_ui_panel_v1(
        blocker_matrix=blocker_matrix,
        readiness_evidence_bundle=bundle,
        readiness_evidence_bundle_summary=summarize_live_canary_readiness_evidence_bundle(
            bundle,
            generated_at=GENERATED_AT,
        ),
        live_credentials_auth_boundary_summary=summary,
        generated_at=GENERATED_AT,
    )
    section = next(row for row in panel["sections"] if row["section_id"] == "live_credentials_auth_boundary")

    assert panel["validation"]["valid"] is True
    assert panel["live_credentials_auth_boundary_summary"]["warning"] == UI_REDACTION_WARNING
    assert panel["live_credentials_auth_boundary_summary"]["redacted_credential_status_ready"] is True
    assert section["status"] == DECISION_MISSING_REQUIRED_CREDENTIALS
    assert all(action["execution_enabled"] is False for action in panel["action_states"])
    assert panel["allowed_for_live"] is False
    assert panel["canary_executable_now"] is False


def test_paper_daily_loop_writes_passive_redacted_auth_artifact(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    artifact = json.loads((tmp_path / "live_credentials_auth_boundary_040.json").read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.live_credentials_auth_boundary_path.endswith("live_credentials_auth_boundary_040.json")
    assert artifact["redacted_credential_status_ready"] is True
    assert artifact["safe_for_artifacts"] is True
    assert artifact["actual_secret_values_exposed"] is False
    assert dashboard["live_credentials_auth_boundary_summary"]["warning"] == UI_REDACTION_WARNING
    assert dashboard["live_credentials_auth_boundary_section_feed"]["allowed_for_live"] is False
    assert panel["live_credentials_auth_boundary_summary"]["redacted_credential_status_ready"] is True
    assert "fake_private_material_never_output_040" not in json.dumps(artifact, sort_keys=True)


def test_evidence_bundle_and_blocker_matrix_include_review_only_auth_boundary() -> None:
    summary = summarize_live_credentials_status(generated_at=GENERATED_AT)
    blocker_matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=blocker_matrix,
        live_credentials_auth_boundary=summary,
        generated_at=GENERATED_AT,
    )
    item = next(row for row in bundle["evidence_items"] if row["evidence_type"] == "live_credentials_auth_boundary")
    categories = {row["blocker_category"] for row in blocker_matrix["blockers"]}

    assert item["review_ready"] is True
    assert item["execution_enabling"] is False
    assert item["secrets_redacted"] is True
    assert item["authenticated_endpoints_enabled"] is False
    assert item["order_submission_enabled"] is False
    assert item["cryptographic_signing_enabled"] is False
    assert REQUESTED_BLOCKER_CATEGORIES.issubset(categories)
    assert REQUESTED_BLOCKER_CATEGORIES.issubset(set(btc_market_readiness_blocker_categories()))
    assert blocker_matrix["all_blockers_unresolved"] is True
    assert blocker_matrix["resolved_blocker_count"] == 0


def test_secret_boundary_rejects_raw_secret_like_payloads_and_allows_symbolic_names() -> None:
    config = _config()
    safe_summary = summarize_live_credentials_status(generated_at=GENERATED_AT)

    assert validate_secret_boundary_live_credentials_config(config, generated_at=GENERATED_AT)["valid"] is True
    assert validate_secret_boundary_result_artifact(safe_summary, generated_at=GENERATED_AT)["valid"] is True
    assert validate_secret_boundary_result_artifact(
        {"status": "blocked", "secret_value": "not-redacted"},
        generated_at=GENERATED_AT,
    )["valid"] is False
    bearer_validation = validate_static_secret_boundary(
        {"safe_label": "Bearer not-redacted"},
        artifact_type="test",
        generated_at=GENERATED_AT,
    )
    raw_key_validation = validate_static_secret_boundary(
        {"safe_label": "0x" + "b" * 64},
        artifact_type="test",
        generated_at=GENERATED_AT,
    )

    assert bearer_validation["valid"] is False
    assert bearer_validation["forbidden_secret_value_paths"] == ["$.safe_label"]
    assert raw_key_validation["valid"] is False
    assert raw_key_validation["forbidden_secret_value_paths"] == ["$.safe_label"]

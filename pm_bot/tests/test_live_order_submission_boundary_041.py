from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.btc_market_analysis_order_intent import evaluate_btc_analysis_to_order_intent
from pm_bot.trading_core.live_canary_readiness import btc_market_readiness_blocker_categories
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_credentials_auth_boundary import (
    FakeLiveCredentialProvider,
    build_default_live_credentials_boundary_config,
    evaluate_live_auth_boundary_for_tiny_canary,
    summarize_live_credentials_status,
)
from pm_bot.trading_core.live_order_submission_boundary import (
    STATUS_BLOCKED,
    STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION,
    STATUS_DRY_RUN_REVIEW_READY,
    build_live_order_submission_boundary_receipt,
    summarize_live_order_submission_boundary_receipt,
    validate_live_order_submission_boundary_receipt,
)
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    PolymarketBTCReadOnlyConnector,
    build_default_btc_fixture_market_payload,
    build_default_btc_read_only_config,
)
from pm_bot.trading_core.risk_limit_control_plane import build_default_risk_limit_policy
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_live_order_submission_boundary_receipt,
    validate_secret_boundary_live_order_submission_boundary_summary,
    validate_secret_boundary_operator_ui_panel_payload,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
FAKE_SECRET_VALUES = {
    "POLYMARKET_PRIVATE_KEY": "fake_private_material_never_output_041",
    "POLYMARKET_FUNDER_ADDRESS": "fake_funder_address_never_output_041",
    "POLYMARKET_CLOB_API_KEY": "fake_clob_key_never_output_041",
    "POLYMARKET_CLOB_SECRET": "fake_clob_secret_never_output_041",
    "POLYMARKET_CLOB_PASSPHRASE": "fake_clob_passphrase_never_output_041",
    "POLYMARKET_CHAIN_ID": "fake_chain_id_never_output_041",
    "POLYMARKET_NETWORK": "fake_network_never_output_041",
}
LIVE_ORDER_BLOCKER_CATEGORIES = {
    "live_order_submission_boundary_review_only",
    "live_order_submission_boundary_not_live_approval",
    "authenticated_endpoint_required_but_disabled",
    "signing_required_but_disabled",
    "wallet_required_but_disabled",
    "order_submission_boundary_non_executable",
}


def _btc_snapshot(
    *,
    payload: Mapping[str, Any] | None = None,
    current_time: str = GENERATED_AT,
    connector_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = dict(connector_config or build_default_btc_read_only_config(generated_at=GENERATED_AT))
    result = PolymarketBTCReadOnlyConnector(config).build_snapshot_from_fixture_payload(
        dict(payload or build_default_btc_fixture_market_payload(observed_at=GENERATED_AT)),
        current_time=current_time,
    )
    return dict(result["snapshot"])


def _btc_intent_result(
    *,
    snapshot: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return evaluate_btc_analysis_to_order_intent(
        snapshot or _btc_snapshot(),
        policy=policy,
        latest_btc_analysis_path="btc_market_analysis_039.json",
        latest_btc_order_intent_path="btc_order_intent_dry_run_039.json",
        latest_btc_risk_decision_path="btc_risk_decision_039.json",
        generated_at=GENERATED_AT,
    )


def _configured_provider() -> FakeLiveCredentialProvider:
    config = build_default_live_credentials_boundary_config(
        live_mode_explicitly_requested=True,
        generated_at=GENERATED_AT,
    )
    values = {row["env_var_name"]: FAKE_SECRET_VALUES[row["env_var_name"]] for row in config["credential_requirements"]}
    return FakeLiveCredentialProvider(values)


def _auth_decision(*, configured: bool = False) -> dict[str, Any]:
    if configured:
        config = build_default_live_credentials_boundary_config(
            live_mode_explicitly_requested=True,
            generated_at=GENERATED_AT,
        )
        return evaluate_live_auth_boundary_for_tiny_canary(
            config,
            _configured_provider(),
            generated_at=GENERATED_AT,
        )
    return evaluate_live_auth_boundary_for_tiny_canary(generated_at=GENERATED_AT)


def _receipt(
    *,
    btc_result: Mapping[str, Any] | None = None,
    auth_decision: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    risk_decision: Mapping[str, Any] | None = None,
    risk_decision_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = dict(btc_result or _btc_intent_result())
    auth = dict(auth_decision or _auth_decision())
    auth_summary = summarize_live_credentials_status(auth, generated_at=GENERATED_AT)
    return build_live_order_submission_boundary_receipt(
        btc_dry_run_order_intent=result,
        risk_decision=risk_decision or result.get("risk_decision", {}),
        risk_decision_summary=risk_decision_summary or result.get("risk_decision_summary", {}),
        risk_control_plane_summary=result.get("risk_control_plane_summary", {}),
        live_credentials_auth_boundary=auth,
        live_credentials_auth_boundary_summary=auth_summary,
        blocker_matrix=blocker_matrix or build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )


def _summary(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return summarize_live_order_submission_boundary_receipt(
        receipt,
        latest_live_order_submission_boundary_path="live_order_submission_boundary_041.json",
        generated_at=GENERATED_AT,
    )


def _assert_no_fake_secret_values(value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, sort_keys=True)
    for fake_secret in FAKE_SECRET_VALUES.values():
        assert fake_secret not in serialized


def _assert_live_submission_flags_false(value: Mapping[str, Any]) -> None:
    for field in (
        "would_submit_order",
        "order_submission_enabled",
        "authenticated_endpoint_enabled",
        "authenticated_endpoints_enabled",
        "signing_enabled",
        "cryptographic_signing_enabled",
        "wallet_enabled",
        "wallet_signing_enabled",
        "allowed_for_live",
        "live_execution_approved",
        "real_execution_available",
        "canary_executable_now",
        "live_connector_enabled",
        "real_order_submitted",
        "order_submitted",
        "real_signature_created",
        "signing_used",
        "wallet_used",
        "network_used",
        "external_api_calls_performed",
    ):
        assert value.get(field) is False


def test_valid_btc_dry_run_intent_creates_deterministic_review_receipt() -> None:
    first = _receipt()
    second = _receipt()
    summary = _summary(first)

    assert first == second
    assert first["status"] == STATUS_DRY_RUN_REVIEW_READY
    assert first["allowed_for_dry_run_review"] is True
    assert first["market_id"] == "btc-one-market-demo-market"
    assert first["asset"] == "BTC"
    assert first["authenticated_endpoint_required"] is True
    assert first["signing_required_for_future_live"] is True
    assert first["wallet_required_for_future_live"] is True
    assert first["validation"]["valid"] is True
    assert summary["dry_run_review_ready"] is True
    assert summary["boundary_is_not_live_approval"] is True
    assert validate_live_order_submission_boundary_receipt(first, generated_at=GENERATED_AT)["valid"] is True
    assert validate_secret_boundary_live_order_submission_boundary_receipt(
        first,
        generated_at=GENERATED_AT,
    )["valid"] is True
    assert validate_secret_boundary_live_order_submission_boundary_summary(
        summary,
        generated_at=GENERATED_AT,
    )["valid"] is True


def test_receipt_never_enables_execution_submission_or_signing() -> None:
    receipt = _receipt()

    _assert_live_submission_flags_false(receipt)
    assert receipt["receipt_is_not_order_submission"] is True
    assert receipt["boundary_is_not_live_approval"] is True
    assert receipt["execution_claimed"] is False
    assert receipt["fill_claimed"] is False
    assert receipt["order_submission_claimed"] is False


def test_receipt_never_exposes_raw_credentials_for_redacted_configured_auth() -> None:
    receipt = _receipt(auth_decision=_auth_decision(configured=True))

    assert receipt["auth_boundary_summary"]["live_credentials_configured"] is True
    assert receipt["auth_boundary_summary"]["secrets_redacted"] is True
    assert receipt["auth_boundary_summary"]["actual_secret_values_exposed"] is False
    assert receipt["auth_boundary_summary"]["order_submission_enabled"] is False
    _assert_no_fake_secret_values(receipt)


def test_risk_blocked_intent_produces_blocked_receipt() -> None:
    policy = build_default_risk_limit_policy(generated_at=GENERATED_AT)
    policy["max_order_notional_usd"] = 0.5
    result = _btc_intent_result(policy=policy)
    receipt = _receipt(btc_result=result)

    assert result["risk_decision_summary"]["allowed_for_dry_run"] is False
    assert receipt["status"] == STATUS_BLOCKED
    assert receipt["allowed_for_dry_run_review"] is False
    assert any(reason.startswith("RISK_DECISION_NOT_ALLOW_DRY_RUN") for reason in receipt["blocker_reasons"])
    _assert_live_submission_flags_false(receipt)


def test_stale_closed_and_non_btc_market_paths_stay_blocked() -> None:
    stale = _receipt(btc_result=_btc_intent_result(snapshot=_btc_snapshot(current_time="2026-05-11T00:06:00Z")))
    closed_payload = build_default_btc_fixture_market_payload(observed_at=GENERATED_AT)
    closed_payload["active"] = False
    closed_payload["closed"] = True
    closed_config = build_default_btc_read_only_config(generated_at=GENERATED_AT)
    closed_config["require_open_market"] = False
    closed_config["require_not_resolved"] = False
    closed = _receipt(
        btc_result=_btc_intent_result(snapshot=_btc_snapshot(payload=closed_payload, connector_config=closed_config))
    )
    non_btc_payload = build_default_btc_fixture_market_payload(observed_at=GENERATED_AT)
    non_btc_payload["id"] = "eth-one-market-demo-market"
    non_btc_payload["slug"] = "eth-one-market-demo"
    non_btc_payload["question"] = "Will Ethereum close above the demo threshold on the fixture date?"
    non_btc_payload["tags"] = ["ETH", "Ethereum"]
    non_btc_config = build_default_btc_read_only_config(
        market_id="eth-one-market-demo-market",
        market_slug="eth-one-market-demo",
        generated_at=GENERATED_AT,
    )
    non_btc_config["require_btc_tag"] = False
    non_btc = _receipt(
        btc_result=_btc_intent_result(
            snapshot=_btc_snapshot(payload=non_btc_payload, connector_config=non_btc_config)
        )
    )

    assert stale["status"] == STATUS_BLOCKED
    assert "STALE_MARKET_DATA" in stale["blocker_reasons"]
    assert closed["status"] == STATUS_BLOCKED
    assert any(reason.startswith("MARKET_NOT_OPEN_OR_UNRESOLVED") for reason in closed["blocker_reasons"])
    assert non_btc["status"] == STATUS_BLOCKED
    assert "NON_BTC_MARKET" in non_btc["blocker_reasons"]


def test_missing_auth_is_represented_safely_without_live_enablement() -> None:
    receipt = _receipt(auth_decision=_auth_decision(configured=False))

    assert receipt["auth_boundary_summary"]["live_credentials_configured"] is False
    assert receipt["auth_boundary_summary"]["missing_credentials_count"] > 0
    assert receipt["auth_boundary_summary"]["secrets_redacted"] is True
    assert receipt["auth_boundary_summary"]["actual_secret_values_exposed"] is False
    assert receipt["status"] == STATUS_DRY_RUN_REVIEW_READY
    _assert_live_submission_flags_false(receipt)


def test_live_execution_implying_input_hard_blocks_as_violation() -> None:
    result = _btc_intent_result()
    unsafe_risk = deepcopy(result["risk_decision"])
    unsafe_risk["allowed_for_live"] = True
    receipt = _receipt(btc_result=result, risk_decision=unsafe_risk)

    assert receipt["status"] == STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION
    assert receipt["allowed_for_dry_run_review"] is False
    assert any("LIVE_EXECUTION_FLAG_TRUE" in reason for reason in receipt["refusal_reasons"])
    _assert_live_submission_flags_false(receipt)


def test_operator_ui_includes_passive_boundary_section_and_no_executable_action() -> None:
    receipt = _receipt()
    summary = _summary(receipt)
    panel = build_operator_ui_panel_v1(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        live_order_submission_boundary_receipt=receipt,
        live_order_submission_boundary_summary=summary,
        latest_paths={"live_order_submission_boundary": "live_order_submission_boundary_041.json"},
        generated_at=GENERATED_AT,
    )
    section = next(row for row in panel["sections"] if row["section_id"] == "live_order_submission_boundary")

    assert panel["validation"]["valid"] is True
    assert panel["live_order_submission_boundary_summary"]["dry_run_review_ready"] is True
    assert panel["live_order_submission_boundary_summary"]["order_submission_enabled"] is False
    assert section["status"] == STATUS_DRY_RUN_REVIEW_READY
    assert all(action["execution_enabled"] is False for action in panel["action_states"])
    assert panel["ui_exposes_no_executable_live_action"] is True
    assert validate_secret_boundary_operator_ui_panel_payload(panel, generated_at=GENERATED_AT)["valid"] is True


def test_paper_daily_loop_writes_041_artifact_when_artifacts_enabled(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    artifact = json.loads((tmp_path / "live_order_submission_boundary_041.json").read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.live_order_submission_boundary_path.endswith("live_order_submission_boundary_041.json")
    assert artifact["status"] == STATUS_DRY_RUN_REVIEW_READY
    assert artifact["would_submit_order"] is False
    assert artifact["order_submission_enabled"] is False
    assert dashboard["live_order_submission_boundary_summary"]["dry_run_review_ready"] is True
    assert dashboard["live_order_submission_boundary_summary"]["allowed_for_live"] is False
    assert panel["live_order_submission_boundary_summary"]["order_submission_enabled"] is False
    assert "live_order_submission_boundary" in {section["section_id"] for section in panel["sections"]}


def test_evidence_bundle_includes_review_only_boundary_item_and_blockers_remain_unresolved() -> None:
    summary = _summary(_receipt())
    matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=matrix,
        live_order_submission_boundary_dry_run_adapter=summary,
        generated_at=GENERATED_AT,
    )
    item = next(
        row
        for row in bundle["evidence_items"]
        if row["evidence_type"] == "live_order_submission_boundary_dry_run_adapter"
    )
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert item["present"] is True
    assert item["review_ready"] is True
    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["would_submit_order"] is False
    assert item["order_submission_enabled"] is False
    assert item["allowed_for_live"] is False
    assert bundle["evidence_bundle_review_ready"] is True
    assert LIVE_ORDER_BLOCKER_CATEGORIES.issubset(categories)
    assert LIVE_ORDER_BLOCKER_CATEGORIES.issubset(set(btc_market_readiness_blocker_categories()))
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["live_execution_available"] is False


def test_no_external_network_calls_are_needed_for_boundary_path(monkeypatch: Any) -> None:
    def blocked_socket(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("external network calls are not allowed in 041 tests")

    monkeypatch.setattr(socket, "create_connection", blocked_socket)
    receipt = _receipt()

    assert receipt["status"] == STATUS_DRY_RUN_REVIEW_READY
    assert receipt["network_used"] is False
    assert receipt["external_api_calls_performed"] is False

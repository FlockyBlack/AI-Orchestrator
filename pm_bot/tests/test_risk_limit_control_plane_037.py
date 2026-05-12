from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    DECISION_ALLOW_DRY_RUN,
    DECISION_BLOCK,
    DECISION_HALT,
    RiskLimitDailyLossSnapshot,
    RiskLimitExposureSnapshot,
    RiskLimitOrderIntent,
    build_default_risk_limit_policy,
    build_default_risk_limit_state,
    build_risk_control_plane_summary,
    evaluate_risk_limits_for_order_intent,
    is_btc_related_order_intent,
    summarize_risk_limit_decision,
    validate_risk_limit_policy,
)
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_risk_control_ui_summary,
    validate_secret_boundary_risk_limit_decision,
    validate_secret_boundary_risk_limit_order_intent,
    validate_secret_boundary_risk_limit_policy,
)

FORBIDDEN_RISK_FIELDS = (
    "private_key",
    "mnemonic",
    "seed_phrase",
    "signature",
    "signed_order",
    "signed_payload",
    "raw_transaction",
    "auth_header",
    "bearer_token",
    "api_key",
    "access_token",
    "order_submission_payload",
    "transaction_payload",
)


def _policy() -> dict[str, Any]:
    return build_default_risk_limit_policy()


def _intent(**overrides: Any) -> dict[str, Any]:
    value = RiskLimitOrderIntent(
        intent_id="risk-limit-intent-037-btc-dry-run",
        market_id="btc-one-market-demo-market",
        market_slug="btc-one-market-demo",
        market_tag="BTC",
        market_category="bitcoin",
        side_label="track_yes",
        notional_usd=1.0,
        quantity=2.0,
        limit_price=0.5,
        intent_source="unit-test",
        created_at="2026-05-11T00:00:00Z",
        dry_run_only=True,
        operator_intent_reference="operator-intent-packet-034",
        readiness_evidence_reference="readiness-evidence-bundle-035",
        audit_replay_reference="live-connector-audit-replay-032",
        ui_panel_reference="operator-ui-panel-v1-036",
    ).to_dict()
    value.update(overrides)
    return value


def _state(
    *,
    total_exposure_usd: float = 0.0,
    market_exposure_usd: float = 0.0,
    active_market_ids: tuple[str, ...] = (),
    realized_loss_usd: float = 0.0,
    minutes_since_last_loss: int | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    exposure = RiskLimitExposureSnapshot(
        total_exposure_usd=total_exposure_usd,
        market_exposure_usd=market_exposure_usd,
        active_market_ids=active_market_ids,
    ).to_dict()
    daily_loss = RiskLimitDailyLossSnapshot(
        realized_loss_usd=realized_loss_usd,
        minutes_since_last_loss=minutes_since_last_loss,
    ).to_dict()
    return build_default_risk_limit_state(
        exposure_snapshot=exposure,
        daily_loss_snapshot=daily_loss,
        **overrides,
    )


def _decision(
    *,
    intent: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return evaluate_risk_limits_for_order_intent(
        intent or _intent(),
        state=state or _state(),
        policy=policy or _policy(),
    )


def test_default_policy_builds_deterministically_and_validates_tiny_limits() -> None:
    first = _policy()
    second = _policy()

    assert first == second
    assert validate_risk_limit_policy(first)["valid"] is True
    assert first["max_daily_loss_usd"] == 5.0
    assert first["max_total_exposure_usd"] == 10.0
    assert first["max_market_exposure_usd"] == 5.0
    assert first["max_order_notional_usd"] == 1.0
    assert first["max_orders_per_day"] == 1
    assert first["max_trades_per_day"] == 1
    assert first["max_active_markets"] == 1
    assert first["review_only_until_live_gate"] is True
    assert first["live_execution_approved"] is False


def test_over_max_order_notional_blocks() -> None:
    decision = _decision(intent=_intent(notional_usd=1.01))

    assert decision["decision_status"] == DECISION_BLOCK
    assert _codes(decision["violations"]) == {"MAX_ORDER_NOTIONAL_EXCEEDED"}


def test_over_max_total_exposure_blocks() -> None:
    decision = _decision(state=_state(total_exposure_usd=9.5))

    assert decision["decision_status"] == DECISION_BLOCK
    assert "MAX_TOTAL_EXPOSURE_EXCEEDED" in _codes(decision["violations"])


def test_over_max_market_exposure_blocks() -> None:
    decision = _decision(state=_state(market_exposure_usd=4.5))

    assert decision["decision_status"] == DECISION_BLOCK
    assert "MAX_MARKET_EXPOSURE_EXCEEDED" in _codes(decision["violations"])


def test_daily_loss_breach_halts() -> None:
    decision = _decision(state=_state(realized_loss_usd=5.0))

    assert decision["decision_status"] == DECISION_HALT
    assert "DAILY_LOSS_LIMIT_BREACHED" in _codes(decision["halt_reasons"])


def test_cooldown_after_loss_halts() -> None:
    decision = _decision(state=_state(realized_loss_usd=0.25, minutes_since_last_loss=10))

    assert decision["decision_status"] == DECISION_HALT
    assert "COOLDOWN_AFTER_LOSS_ACTIVE" in _codes(decision["halt_reasons"])


def test_max_trades_per_day_breach_blocks() -> None:
    decision = _decision(state=_state(trades_executed_today=1))

    assert decision["decision_status"] == DECISION_BLOCK
    assert "MAX_TRADES_PER_DAY_EXCEEDED" in _codes(decision["violations"])


def test_stale_market_data_halts_when_configured() -> None:
    decision = _decision(state=_state(market_data_age_seconds=301))

    assert decision["decision_status"] == DECISION_HALT
    assert "STALE_MARKET_DATA" in _codes(decision["halt_reasons"])


def test_audit_mismatch_halts_when_configured() -> None:
    decision = _decision(state=_state(audit_mismatch_detected=True))

    assert decision["decision_status"] == DECISION_HALT
    assert "AUDIT_MISMATCH_DETECTED" in _codes(decision["halt_reasons"])


def test_kill_switch_active_halts() -> None:
    decision = _decision(state=_state(kill_switch_active=True))

    assert decision["decision_status"] == DECISION_HALT
    assert "KILL_SWITCH_ACTIVE" in _codes(decision["halt_reasons"])


def test_missing_operator_intent_blocks_or_halts() -> None:
    decision = _decision(intent=_intent(operator_intent_reference=""))

    assert decision["decision_status"] == DECISION_BLOCK
    assert "MISSING_OPERATOR_INTENT" in _codes(decision["violations"])


def test_missing_readiness_evidence_blocks_or_halts() -> None:
    decision = _decision(intent=_intent(readiness_evidence_reference=""))

    assert decision["decision_status"] == DECISION_BLOCK
    assert "MISSING_READINESS_EVIDENCE" in _codes(decision["violations"])


def test_unresolved_critical_blockers_halt() -> None:
    decision = _decision(state=_state(unresolved_critical_blockers=("PMBOT-LIVE-BLOCKER-039",)))

    assert decision["decision_status"] == DECISION_HALT
    assert "UNRESOLVED_CRITICAL_BLOCKERS" in _codes(decision["halt_reasons"])


def test_disabled_live_connector_and_live_flags_prevent_live_allowance() -> None:
    decision = _decision()

    assert decision["decision_status"] == DECISION_ALLOW_DRY_RUN
    assert decision["allowed_for_dry_run"] is True
    assert decision["allowed_for_live"] is False
    assert decision["live_execution_approved"] is False
    assert decision["canary_executable_now"] is False
    assert decision["real_execution_available"] is False
    assert decision["live_connector_enabled"] is False
    assert {
        "LIVE_CONNECTOR_DISABLED",
        "LIVE_EXECUTION_NOT_APPROVED",
        "CANARY_NOT_EXECUTABLE",
        "REAL_EXECUTION_UNAVAILABLE",
    }.issubset(set(decision["live_block_reasons"]))


def test_valid_btc_tagged_dry_run_intent_allows_dry_run_but_never_live() -> None:
    intent = _intent()
    decision = _decision(intent=intent)

    assert is_btc_related_order_intent(intent) is True
    assert decision["decision_status"] == DECISION_ALLOW_DRY_RUN
    assert summarize_risk_limit_decision(decision)["allowed_for_dry_run"] is True
    assert decision["allowed_for_live"] is False


def test_non_whitelisted_market_blocks() -> None:
    decision = _decision(
        intent=_intent(
            market_id="eth-one-market-demo-market",
            market_slug="eth-one-market-demo",
            market_tag="ETH",
            market_category="ethereum",
        )
    )

    assert decision["decision_status"] == DECISION_BLOCK
    assert "MARKET_NOT_WHITELISTED" in _codes(decision["violations"])


def test_same_inputs_produce_deterministic_decision() -> None:
    intent = _intent()
    state = _state()
    policy = _policy()

    assert _decision(intent=deepcopy(intent), state=deepcopy(state), policy=deepcopy(policy)) == _decision(
        intent=deepcopy(intent),
        state=deepcopy(state),
        policy=deepcopy(policy),
    )


def test_ui_panel_surfaces_risk_control_plane_summary() -> None:
    policy = _policy()
    decision = _decision(policy=policy)
    summary = build_risk_control_plane_summary(policy=policy, latest_decision=decision)
    panel = build_operator_ui_panel_v1(
        risk_limit_policy=policy,
        latest_risk_limit_decision=decision,
        risk_control_plane_summary=summary,
    )

    risk_control = panel["risk_control_plane_summary"]
    assert risk_control["risk_control_plane_ready"] is True
    assert risk_control["policy_id"] == policy["policy_id"]
    assert risk_control["latest_decision_status"] == DECISION_ALLOW_DRY_RUN
    assert risk_control["allowed_for_dry_run"] is True
    assert risk_control["allowed_for_live"] is False
    assert validate_secret_boundary_risk_control_ui_summary(risk_control)["valid"] is True


def test_paper_daily_loop_surfaces_risk_control_plane_summary_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert dashboard["risk_control_plane_summary"]["risk_control_plane_ready"] is True
    assert dashboard["risk_control_plane_summary"]["allowed_for_live"] is False
    assert dashboard["default_risk_limit_policy_summary"]["btc_one_market_demo_policy_supported"] is True
    assert dashboard["risk_limit_panel_feed"]["allowed_for_live"] is False
    assert panel["risk_control_plane_summary"]["allowed_for_live"] is False
    assert panel["risk_control_plane_summary"]["risk_limits_enforced_for_order_intents"] is True


def test_evidence_bundle_includes_risk_control_evidence_item() -> None:
    policy = _policy()
    decision = _decision(policy=policy)
    summary = build_risk_control_plane_summary(policy=policy, latest_decision=decision)
    bundle = build_live_canary_readiness_evidence_bundle(risk_limit_control_plane=summary)
    item_by_type = {row["evidence_type"]: row for row in bundle["evidence_items"]}

    assert "risk_limit_control_plane" in item_by_type
    assert item_by_type["risk_limit_control_plane"]["present"] is True
    assert item_by_type["risk_limit_control_plane"]["review_ready"] is True
    assert item_by_type["risk_limit_control_plane"]["execution_enabling"] is False
    assert bundle["live_execution_approved"] is False


def test_secret_boundary_rejects_forbidden_fields_in_risk_payloads() -> None:
    policy = _policy()
    intent = _intent()
    decision = _decision(policy=policy)
    validators = (
        (policy, validate_secret_boundary_risk_limit_policy),
        (intent, validate_secret_boundary_risk_limit_order_intent),
        (decision, validate_secret_boundary_risk_limit_decision),
    )

    for payload, validator in validators:
        assert validator(payload)["valid"] is True
        for field in FORBIDDEN_RISK_FIELDS:
            unsafe = dict(payload)
            unsafe[field] = "<redacted>"
            validation = validator(unsafe)

            assert validation["valid"] is False
            assert f"$.{field}" in validation["forbidden_secret_field_paths"]


def test_no_real_order_placement_fields_exist_in_safe_risk_payloads() -> None:
    decision = _decision()
    keys = {key for _path, key, _value in _walk([_policy(), _intent(), decision])}

    assert set(FORBIDDEN_RISK_FIELDS).isdisjoint(keys)
    assert decision["allowed_for_live"] is False
    assert decision["real_execution_available"] is False


def _codes(rows: list[dict[str, Any]]) -> set[str]:
    return {row["code"] for row in rows}


def _walk(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            rows.append((path, str(key), nested))
            rows.extend(_walk(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk(nested, f"{path}[{index}]"))
    return rows

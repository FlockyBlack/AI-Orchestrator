from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_enablement_config import (
    STATUS_CONFIG_INVALID_BLOCKED,
    STATUS_CONFIG_MISSING_BLOCKED,
    STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED,
    STATUS_REVIEW_ONLY_PREFLIGHT_READY,
    build_live_enablement_config_preflight,
    summarize_live_enablement_config_preflight,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import build_tiny_live_canary_gonogo_gate

GENERATED_AT = "2026-05-13T00:00:00Z"


REVIEW_ONLY_CONFIG = {
    "PMBOT_LIVE_MODE": "false",
    "PMBOT_LIVE_CANARY_ENABLED": "false",
    "PMBOT_ORDER_SUBMISSION_ENABLED": "false",
    "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED": "false",
    "PMBOT_WALLET_SIGNING_ENABLED": "false",
    "PMBOT_MAX_ORDER_NOTIONAL_USD": "1",
    "PMBOT_DAILY_LOSS_CAP_USD": "1",
    "PMBOT_TOTAL_EXPOSURE_CAP_USD": "1",
    "PMBOT_MAX_LIVE_TRADES_PER_DAY": "1",
    "PMBOT_ALLOWED_MARKET_SLUGS": "btc-one-market-demo",
    "PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL": "true",
    "PMBOT_REQUIRE_KILL_SWITCH_READY": "true",
}


FORCED_FALSE_FIELDS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "authenticated_polymarket_enabled",
    "wallet_signing_enabled",
)


def _assert_forced_false(value: dict[str, Any]) -> None:
    for field in FORCED_FALSE_FIELDS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0


def test_default_missing_config_blocks_and_defaults_all_execution_flags_false() -> None:
    preflight = build_live_enablement_config_preflight(generated_at=GENERATED_AT)

    assert preflight["status"] == STATUS_CONFIG_MISSING_BLOCKED
    assert preflight["future_live_requested"] is False
    assert preflight["dry_run_review_allowed"] is False
    assert preflight["validation"]["valid"] is True
    _assert_forced_false(preflight)


def test_invalid_boolean_values_block_preflight() -> None:
    config = dict(REVIEW_ONLY_CONFIG)
    config["PMBOT_LIVE_MODE"] = "enabled"

    preflight = build_live_enablement_config_preflight(config, generated_at=GENERATED_AT)

    assert preflight["status"] == STATUS_CONFIG_INVALID_BLOCKED
    assert "invalid_boolean:PMBOT_LIVE_MODE" in preflight["violation_reasons"]
    assert preflight["dry_run_review_allowed"] is False
    _assert_forced_false(preflight)


def test_invalid_numeric_risk_limits_block_preflight() -> None:
    config = dict(REVIEW_ONLY_CONFIG)
    config["PMBOT_MAX_ORDER_NOTIONAL_USD"] = "0"

    preflight = build_live_enablement_config_preflight(config, generated_at=GENERATED_AT)

    assert preflight["status"] == STATUS_CONFIG_INVALID_BLOCKED
    assert "invalid_numeric:PMBOT_MAX_ORDER_NOTIONAL_USD" in preflight["violation_reasons"]
    assert preflight["dry_run_review_allowed"] is False
    _assert_forced_false(preflight)


def test_valid_review_only_config_is_not_live_ready() -> None:
    preflight = build_live_enablement_config_preflight(REVIEW_ONLY_CONFIG, generated_at=GENERATED_AT)
    summary = summarize_live_enablement_config_preflight(preflight, generated_at=GENERATED_AT)

    assert preflight["status"] == STATUS_REVIEW_ONLY_PREFLIGHT_READY
    assert preflight["dry_run_review_allowed"] is True
    assert preflight["allowed_for_dry_run_review"] is True
    assert summary["status"] == STATUS_REVIEW_ONLY_PREFLIGHT_READY
    assert summary["dry_run_review_allowed"] is True
    _assert_forced_false(preflight)
    _assert_forced_false(summary)


def test_true_live_flags_are_requested_but_blocked() -> None:
    config = dict(REVIEW_ONLY_CONFIG)
    config["PMBOT_LIVE_MODE"] = "true"
    config["PMBOT_LIVE_CANARY_ENABLED"] = "yes"
    config["PMBOT_ORDER_SUBMISSION_ENABLED"] = "1"
    config["PMBOT_AUTHENTICATED_POLYMARKET_ENABLED"] = "true"
    config["PMBOT_WALLET_SIGNING_ENABLED"] = "true"

    preflight = build_live_enablement_config_preflight(config, generated_at=GENERATED_AT)

    assert preflight["status"] == STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED
    assert preflight["future_live_requested"] is True
    assert "operator_requested_live_flags_but_task_047_blocks_live_execution" in preflight["blocked_reasons"]
    assert preflight["dry_run_review_allowed"] is False
    _assert_forced_false(preflight)


def test_market_scope_requires_exactly_one_btc_related_market() -> None:
    config = dict(REVIEW_ONLY_CONFIG)
    config["PMBOT_ALLOWED_MARKET_SLUGS"] = "btc-one,eth-two"

    preflight = build_live_enablement_config_preflight(config, generated_at=GENERATED_AT)

    assert preflight["status"] == STATUS_CONFIG_INVALID_BLOCKED
    assert any(reason.startswith("invalid_market_scope:") for reason in preflight["violation_reasons"])
    _assert_forced_false(preflight)


def test_sensitive_looking_config_values_are_not_emitted() -> None:
    sensitive_marker = "credential-secret-marker-never-output-047"
    config = dict(REVIEW_ONLY_CONFIG)
    config["PMBOT_ALLOWED_MARKET_SLUGS"] = f"btc-one-market-demo,{sensitive_marker}"

    preflight = build_live_enablement_config_preflight(config, generated_at=GENERATED_AT)
    payload = json.dumps(preflight, sort_keys=True)

    assert preflight["status"] == STATUS_CONFIG_INVALID_BLOCKED
    assert sensitive_marker not in payload
    assert "<redacted:sensitive_config_value>" in payload
    assert preflight["no_raw_secrets_parsed_or_emitted"] is True


def test_evidence_bundle_includes_review_only_live_enablement_item() -> None:
    preflight = build_live_enablement_config_preflight(REVIEW_ONLY_CONFIG, generated_at=GENERATED_AT)
    summary = summarize_live_enablement_config_preflight(preflight, generated_at=GENERATED_AT)
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        live_enablement_config_preflight=preflight,
        live_enablement_config_preflight_summary=summary,
        generated_at=GENERATED_AT,
    )
    items = {item["evidence_type"]: item for item in bundle["evidence_items"]}
    item = items["live_enablement_config_contract_and_runtime_preflight"]

    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["live_approval"] is False
    assert item["allowed_for_live"] is False
    assert item["order_submission_enabled"] is False
    assert item["authenticated_polymarket_enabled"] is False
    assert item["wallet_signing_enabled"] is False


def test_gonogo_gate_includes_preflight_summary_without_resolving_blockers() -> None:
    preflight = build_live_enablement_config_preflight(REVIEW_ONLY_CONFIG, generated_at=GENERATED_AT)
    summary = summarize_live_enablement_config_preflight(preflight, generated_at=GENERATED_AT)
    gate = build_tiny_live_canary_gonogo_gate(
        live_enablement_config_preflight_summary=summary,
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )

    assert gate["live_enablement_config_preflight_summary"]["status"] == STATUS_REVIEW_ONLY_PREFLIGHT_READY
    assert gate["allowed_for_live"] is False
    assert gate["canary_executable_now"] is False
    assert gate["live_execution_approved"] is False
    assert gate["real_execution_available"] is False
    assert gate["live_connector_enabled"] is False
    assert gate["order_submission_enabled"] is False
    assert gate["resolved_blocker_count"] == 0
    assert gate["validation"]["valid"] is True


def test_operator_ui_includes_passive_live_enablement_preflight_section() -> None:
    preflight = build_live_enablement_config_preflight(generated_at=GENERATED_AT)
    summary = summarize_live_enablement_config_preflight(preflight, generated_at=GENERATED_AT)
    panel = build_operator_ui_panel_v1(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        live_enablement_config_preflight=preflight,
        live_enablement_config_preflight_summary=summary,
        generated_at=GENERATED_AT,
    )
    section_ids = {section["section_id"] for section in panel["sections"]}
    live_section = panel["live_enablement_config_preflight_summary"]

    assert "live_enablement_config_preflight" in section_ids
    assert live_section["status"] == STATUS_CONFIG_MISSING_BLOCKED
    assert live_section["future_live_requested"] is False
    assert live_section["dry_run_review_allowed"] is False
    assert live_section["allowed_for_live"] is False
    assert live_section["no_executable_action"] is True
    assert panel["validation"]["valid"] is True


def test_paper_daily_loop_emits_live_enablement_config_preflight_artifact(
    monkeypatch, tmp_path: Path
) -> None:
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("external network calls are not allowed in live enablement config tests")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-13", max_markets=6, output_dir=tmp_path)
    )
    artifact_path = tmp_path / "live_enablement_config_preflight_047.json"
    preflight = json.loads(artifact_path.read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.safety_ok is True
    assert Path(result.live_enablement_config_preflight_path).name == artifact_path.name
    assert preflight["status"] == STATUS_CONFIG_MISSING_BLOCKED
    assert dashboard["live_enablement_config_preflight_summary"]["status"] == STATUS_CONFIG_MISSING_BLOCKED
    assert dashboard["live_enablement_config_preflight_summary"]["allowed_for_live"] is False
    assert dashboard["operator_ui_panel_v1_summary"]["live_enablement_config_preflight_section_ready"] is True

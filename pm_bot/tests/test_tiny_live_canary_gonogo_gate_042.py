from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    summarize_operator_ui_panel_v1,
    validate_operator_ui_panel_v1,
)
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
    validate_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.secret_boundary_policy import validate_secret_boundary_tiny_live_canary_gonogo_gate
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import (
    FORBIDDEN_GO_STATUS,
    STATUS_HARD_BLOCK_LIVE_EXECUTION_CLAIM,
    STATUS_NO_GO_UNRESOLVED_BLOCKERS,
    build_tiny_live_canary_gonogo_gate,
    render_tiny_live_canary_gonogo_gate_markdown,
    summarize_tiny_live_canary_gonogo_gate,
    validate_tiny_live_canary_gonogo_gate,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
FAKE_SECRET = "sk-test-raw-secret-never-output-042"


def _complete_gate_inputs() -> dict[str, Any]:
    return {
        "market_id": "btc-one-market-demo-market",
        "market_slug": "btc-one-market-demo",
        "btc_market_snapshot_summary": {
            "market_id": "btc-one-market-demo-market",
            "market_slug": "btc-one-market-demo",
            "market_title": "BTC one market demo",
            "btc_market_connector_status": "fixture_snapshot_validated_read_only",
            "is_btc_related": True,
            "market_status": "open",
            "is_open": True,
            "is_resolved": False,
            "stale": False,
            "snapshot_age_seconds": 60,
            "risk_control_market_data_status": "fresh_open_btc_market",
            "read_only_network_enabled": False,
        },
        "btc_analysis_summary": {
            "btc_market_analysis_status": "analysis_ready_for_dry_run_intent",
            "btc_intent_candidate_status": "dry_run_intent_candidate_ready",
            "analysis_is_not_live_recommendation": True,
        },
        "dry_run_order_intent_summary": {
            "dry_run_order_intent_status": "dry_run_intent_candidate_ready",
            "market_id": "btc-one-market-demo-market",
            "market_slug": "btc-one-market-demo",
            "intent_notional_usd": 1.0,
            "intent_limit_price": 0.5,
            "risk_decision_status": "ALLOW_DRY_RUN",
            "allowed_for_dry_run": True,
            "order_intent_is_not_order_submission": True,
        },
        "risk_limit_summary": {
            "risk_control_plane_status": "dry_run_allowed",
            "policy_id": "risk-limit-control-plane-037",
            "mode": "dry_run",
            "max_order_notional_usd": 1.0,
            "max_daily_loss_usd": 5.0,
            "max_total_exposure_usd": 10.0,
            "max_market_exposure_usd": 10.0,
            "max_active_markets": 1,
            "max_orders_per_day": 1,
            "max_trades_per_day": 1,
            "risk_limits_enforced_for_order_intents": True,
            "allowed_for_dry_run": True,
        },
        "auth_boundary_summary": {
            "live_credentials_boundary_status": "MISSING_REQUIRED_CREDENTIALS",
            "live_credentials_configured": False,
            "redacted_credential_status_ready": True,
            "credential_statuses_redacted": True,
            "secrets_redacted": True,
            "actual_secret_values_exposed": False,
            "required_credentials_count": 7,
            "missing_credentials_count": 7,
        },
        "order_submission_boundary_summary": {
            "status": "dry_run_submission_boundary_review_ready",
            "boundary_name": "live_order_submission_boundary_disabled_dry_run_receipt",
            "dry_run_review_ready": True,
            "market_id": "btc-one-market-demo-market",
            "market_slug": "btc-one-market-demo",
            "authenticated_endpoint_required": True,
            "signing_required_for_future_live": True,
            "wallet_required_for_future_live": True,
            "boundary_is_not_live_approval": True,
            "receipt_is_not_order_submission": True,
        },
        "operator_signed_intent_summary": {
            "operator_intent_packet_status": "operator_intent_packet_review_ready",
            "operator_intent_packet_review_ready": True,
            "operator_signed_intent_is_human_acknowledgement_only": True,
            "operator_intent_is_not_live_approval": True,
        },
        "readiness_evidence_summary": {
            "readiness_evidence_bundle_status": "readiness_evidence_bundle_review_ready",
            "readiness_evidence_bundle_review_ready": True,
            "readiness_evidence_bundle_is_not_live_approval": True,
            "evidence_item_count": 22,
            "missing_required_evidence_count": 0,
            "unresolved_live_blocker_count": 65,
        },
        "kill_switch_summary": {
            "kill_switch_requirements_defined": True,
            "kill_switch_verified_for_live": False,
            "kill_switch_blocks_live_execution": True,
            "emergency_stop_documented": True,
            "current_kill_switch_state": "blocks_live",
        },
        "blocker_matrix": build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        "latest_tiny_live_canary_gonogo_gate_path": "tiny_live_canary_gonogo_gate_042.json",
        "generated_at": GENERATED_AT,
    }


def _packet(**overrides: Any) -> dict[str, Any]:
    inputs = _complete_gate_inputs()
    inputs.update(overrides)
    return build_tiny_live_canary_gonogo_gate(**inputs)


def _assert_live_flags_disabled(value: dict[str, Any]) -> None:
    for field in (
        "final_live_enablement_present",
        "live_execution_approved",
        "allowed_for_live",
        "canary_executable_now",
        "order_submission_enabled",
        "real_execution_available",
        "live_connector_enabled",
        "would_submit_order",
        "order_submitted",
        "real_order_submitted",
        "authenticated_endpoint_enabled",
        "authenticated_endpoints_enabled",
        "signing_enabled",
        "cryptographic_signing_enabled",
        "wallet_enabled",
        "wallet_signing_enabled",
        "execution_enabled",
        "live_action_exposed",
        "network_used",
        "external_api_calls_performed",
    ):
        assert value[field] is False


def test_complete_dry_run_pipeline_produces_deterministic_operator_review_packet() -> None:
    first = _packet()
    second = _packet()
    summary = summarize_tiny_live_canary_gonogo_gate(first, generated_at=GENERATED_AT)

    assert first == second
    assert first["schema_version"] == "042.v1"
    assert first["status"] == STATUS_NO_GO_UNRESOLVED_BLOCKERS
    assert first["overall_decision"] == "NO_GO"
    assert first["decision_level"] == "FINAL_MANUAL_REVIEW_ONLY"
    assert first["packet_complete_for_operator_review"] is True
    assert first["manual_execution_checklist"]["item_count"] == 13
    assert first["final_pre_live_checklist"]["item_count"] == 8
    assert first["manual_execution_checklist"]["pending_operator_confirmation_count"] == 13
    assert first["resolved_blocker_count"] == 0
    assert first["unresolved_blocker_count"] >= 1
    assert first["validation"]["valid"] is True
    assert validate_tiny_live_canary_gonogo_gate(first, generated_at=GENERATED_AT)["valid"] is True
    assert validate_secret_boundary_tiny_live_canary_gonogo_gate(first, generated_at=GENERATED_AT)["valid"] is True
    assert summary["status"] == STATUS_NO_GO_UNRESOLVED_BLOCKERS
    assert summary["no_executable_action"] is True


def test_packet_never_enables_live_execution_or_returns_go_for_live() -> None:
    packet = _packet()
    markdown = render_tiny_live_canary_gonogo_gate_markdown(packet)

    _assert_live_flags_disabled(packet)
    assert packet["explicit_human_approval_required"] is True
    assert packet["status"] != FORBIDDEN_GO_STATUS
    assert FORBIDDEN_GO_STATUS not in json.dumps(packet, sort_keys=True)
    assert "GO_FOR_LIVE" not in markdown

    unsafe = deepcopy(packet)
    unsafe["status"] = FORBIDDEN_GO_STATUS
    validation = validate_tiny_live_canary_gonogo_gate(unsafe, generated_at=GENERATED_AT)
    assert validation["valid"] is False
    assert "forbidden_go_for_live_status" in validation["statuses"]


def test_unresolved_blockers_force_no_go_and_resolved_count_zero() -> None:
    packet = _packet()

    assert packet["status"] == STATUS_NO_GO_UNRESOLVED_BLOCKERS
    assert "live_blockers_remain_unresolved" in packet["no_go_reasons"]
    assert packet["blocker_matrix_summary"]["all_blockers_unresolved"] is True
    assert packet["blocker_matrix_summary"]["resolved_blocker_count"] == 0
    assert packet["resolved_blocker_count"] == 0
    assert all(row["resolution_status"] == "unresolved" for row in packet["unresolved_blockers"])


def test_raw_credentials_are_not_exposed_and_live_claims_hard_block() -> None:
    packet = _packet(
        auth_boundary_summary={
            "live_credentials_configured": True,
            "redacted_credential_status_ready": True,
            "secrets_redacted": True,
            "api_key": FAKE_SECRET,
            "order_submission_enabled": True,
            "authenticated_endpoint_enabled": True,
            "signing_enabled": True,
            "wallet_signing_enabled": True,
            "live_execution_approved": True,
        }
    )
    serialized = json.dumps(packet, sort_keys=True)

    assert packet["status"] == STATUS_HARD_BLOCK_LIVE_EXECUTION_CLAIM
    assert "input_claimed_live_execution_or_order_submission_enabled" in packet["no_go_reasons"]
    assert packet["live_execution_violation_reasons"]
    assert FAKE_SECRET not in serialized
    assert packet["input_secret_boundary_summary"]["forbidden_secret_field_count"] >= 1
    assert packet["input_secret_boundary_summary"]["forbidden_secret_value_count"] >= 1
    assert packet["validation"]["valid"] is True
    _assert_live_flags_disabled(packet)


def test_operator_ui_includes_passive_gonogo_section_with_no_executable_action() -> None:
    packet = _packet()
    summary = summarize_tiny_live_canary_gonogo_gate(packet, generated_at=GENERATED_AT)
    panel = build_operator_ui_panel_v1(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        tiny_live_canary_gonogo_gate=packet,
        tiny_live_canary_gonogo_gate_summary=summary,
        latest_paths={"tiny_live_canary_gonogo_gate": "tiny_live_canary_gonogo_gate_042.json"},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    section_ids = {section["section_id"] for section in panel["sections"]}
    action = next(row for row in panel["action_states"] if row["action_id"] == "inspect_tiny_live_canary_gonogo_gate")

    assert validate_operator_ui_panel_v1(panel, generated_at=GENERATED_AT)["valid"] is True
    assert "tiny_live_canary_gonogo_gate" in section_ids
    assert panel["tiny_live_canary_gonogo_gate_summary"]["overall_decision"] == "NO_GO"
    assert panel["tiny_live_canary_gonogo_gate_summary"]["no_executable_action"] is True
    assert panel["tiny_live_canary_gonogo_gate_summary"]["explicit_human_approval_required"] is True
    assert panel["tiny_live_canary_gonogo_gate_summary"]["order_submission_enabled"] is False
    assert panel_summary["tiny_live_canary_gonogo_no_executable_action"] is True
    assert action["execution_enabled"] is False
    assert action["live_action_exposed"] is False


def test_evidence_bundle_includes_review_only_gonogo_item() -> None:
    packet = _packet()
    summary = summarize_tiny_live_canary_gonogo_gate(
        packet,
        latest_tiny_live_canary_gonogo_gate_path="tiny_live_canary_gonogo_gate_042.json",
        generated_at=GENERATED_AT,
    )
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        tiny_live_canary_gonogo_gate=summary,
        artifact_reference_overrides={
            "tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate": (
                "tiny_live_canary_gonogo_gate_042.json"
            )
        },
        generated_at=GENERATED_AT,
    )
    validation = validate_live_canary_readiness_evidence_bundle(bundle, generated_at=GENERATED_AT)
    item = next(
        row
        for row in bundle["evidence_items"]
        if row["evidence_type"] == "tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate"
    )

    assert validation["valid"] is True
    assert item["present"] is True
    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["live_approval"] is False
    assert item["status"] == STATUS_NO_GO_UNRESOLVED_BLOCKERS
    assert item["reference_path_or_id"] == "tiny_live_canary_gonogo_gate_042.json"


def test_paper_daily_loop_writes_gonogo_artifact_without_network(monkeypatch, tmp_path: Path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    gate = json.loads((tmp_path / "tiny_live_canary_gonogo_gate_042.json").read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.tiny_live_canary_gonogo_gate_path.endswith("tiny_live_canary_gonogo_gate_042.json")
    assert gate["status"] == STATUS_NO_GO_UNRESOLVED_BLOCKERS
    assert gate["validation"]["valid"] is True
    assert gate["explicit_human_approval_required"] is True
    assert gate["final_live_enablement_present"] is False
    assert gate["order_submission_enabled"] is False
    assert gate["resolved_blocker_count"] == 0
    assert dashboard["tiny_live_canary_gonogo_gate_summary"]["no_executable_action"] is True
    assert panel["tiny_live_canary_gonogo_gate_summary"]["no_executable_action"] is True

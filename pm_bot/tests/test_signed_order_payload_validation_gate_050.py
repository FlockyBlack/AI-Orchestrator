from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.authenticated_polymarket_connector import (
    build_authenticated_connector_capability_report,
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.live_canary_readiness import build_canary_readiness_packet
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.signed_order_payload_validation_gate import (
    STATUS_PAYLOAD_SHAPE_INVALID,
    STATUS_PAYLOAD_SHAPE_REVIEW_READY,
    STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED,
    STATUS_SIGNING_DISABLED_REVIEW_ONLY,
    build_signed_order_payload_validation_gate,
    summarize_signed_order_payload_validation_gate,
    validate_signed_order_payload_validation_gate,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import build_tiny_live_canary_gonogo_gate
from pm_bot.trading_core.wallet_signing_boundary import (
    STATUS_SIGNING_REQUEST_REFUSED,
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
)

GENERATED_AT = "2026-05-13T00:00:00Z"

FORCED_FALSE_FIELDS = (
    "signing_enabled",
    "wallet_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "order_submission_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
)

FORBIDDEN_OUTPUT_KEYS = (
    "signature",
    "signed_payload",
    "signed_order",
    "tx_hash",
    "transaction_hash",
    "order_id",
    "fill_id",
    "execution_id",
    "execution_result",
)


def _future_payload() -> dict[str, Any]:
    return {
        "market_id": "btc-test-market-050",
        "side": "buy",
        "outcome": "YES",
        "price": 0.51,
        "size": 1.0,
        "notional_usd": 1.0,
        "order_type": "limit",
        "time_in_force": "GTC",
        "operator_approval_reference": "operator-review-050",
        "risk_decision_reference": "risk-decision-050",
        "connector_capability_reference": "connector-capability-050",
        "wallet_signing_boundary_reference": "wallet-boundary-050",
    }


def _assert_forced_false(value: Mapping[str, Any]) -> None:
    for field in FORCED_FALSE_FIELDS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0


def _assert_no_signed_or_execution_output(value: Mapping[str, Any]) -> None:
    for key in FORBIDDEN_OUTPUT_KEYS:
        assert key not in value
    assert value["signature_present"] is False
    assert value["signed_payload_present"] is False
    assert value["signed_order_present"] is False
    assert value["transaction_hash_present"] is False
    assert value["order_id_present"] is False
    assert value["fill_present"] is False
    assert value["execution_result_present"] is False
    assert value["no_signature_returned"] is True
    assert value["no_signed_payload_returned"] is True
    assert value["no_signed_order_returned"] is True
    assert value["no_transaction_hash_returned"] is True
    assert value["no_order_id_returned"] is True
    assert value["no_fill_returned"] is True
    assert value["no_execution_result_returned"] is True
    assert value["no_fake_signature_generated"] is True
    assert value["no_fake_signed_payload_generated"] is True
    assert value["no_fake_signed_order_generated"] is True
    assert value["no_fake_order_id_generated"] is True
    assert value["no_fake_transaction_hash_generated"] is True
    assert value["no_fake_fill_generated"] is True
    assert value["no_fake_execution_result_generated"] is True


def test_default_gate_is_disabled_review_only_without_signed_outputs() -> None:
    gate = build_signed_order_payload_validation_gate(generated_at=GENERATED_AT)
    summary = summarize_signed_order_payload_validation_gate(gate, generated_at=GENERATED_AT)

    assert gate["schema_version"] == "050.v1"
    assert gate["status"] == STATUS_SIGNING_DISABLED_REVIEW_ONLY
    assert gate["review_only"] is True
    assert gate["dry_run_only"] is True
    assert gate["input_intent_summary"]["payload_present"] is False
    assert gate["missing_fields"]
    assert gate["validation"]["valid"] is True
    assert summary["signed_order_payload_validation_gate_section_ready"] is True
    _assert_forced_false(gate)
    _assert_forced_false(summary)
    _assert_no_signed_or_execution_output(gate)


def test_missing_required_future_payload_fields_are_invalid_or_blocked() -> None:
    gate = build_signed_order_payload_validation_gate(
        {"market_id": "btc-test-market-050"},
        generated_at=GENERATED_AT,
    )

    assert gate["status"] in {STATUS_PAYLOAD_SHAPE_INVALID, STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED}
    assert gate["missing_field_count"] > 0
    assert "future_signed_order_payload_missing_required_fields" in gate["blocked_reasons"]
    assert gate["allowed_for_live"] is False
    assert gate["validation"]["valid"] is True
    _assert_forced_false(gate)


def test_valid_future_payload_shape_is_review_ready_but_not_live() -> None:
    auth_report = build_authenticated_connector_capability_report(generated_at=GENERATED_AT)
    auth_summary = summarize_authenticated_connector_capability_report(auth_report, generated_at=GENERATED_AT)
    wallet_report = build_wallet_signing_boundary_report(generated_at=GENERATED_AT)
    wallet_summary = summarize_wallet_signing_boundary_report(wallet_report, generated_at=GENERATED_AT)
    gate = build_signed_order_payload_validation_gate(
        _future_payload(),
        connector_capability_report=auth_report,
        connector_capability_summary=auth_summary,
        wallet_signing_boundary_report=wallet_report,
        wallet_signing_boundary_summary=wallet_summary,
        generated_at=GENERATED_AT,
    )

    assert gate["status"] == STATUS_PAYLOAD_SHAPE_REVIEW_READY
    assert gate["payload_shape_review_ready"] is True
    assert gate["missing_fields"] == []
    assert gate["invalid_fields"] == []
    assert gate["signing_request_review_summary"]["status"] == STATUS_SIGNING_REQUEST_REFUSED
    assert gate["signing_request_review_summary"]["signing_request_refused"] is True
    assert gate["connector_capability_summary"]["review_only"] is True
    assert gate["wallet_signing_boundary_summary"]["review_only"] is True
    assert gate["allowed_for_live"] is False
    assert gate["canary_executable_now"] is False
    assert gate["validation"]["valid"] is True
    assert validate_signed_order_payload_validation_gate(gate, generated_at=GENERATED_AT)["valid"] is True
    _assert_forced_false(gate)
    _assert_no_signed_or_execution_output(gate)


def test_signature_signed_payload_signed_order_and_tx_hash_inputs_are_rejected() -> None:
    for forbidden_key in ("signature", "signed_payload", "signed_order", "tx_hash"):
        payload = _future_payload() | {forbidden_key: "forbidden-marker-050"}
        gate = build_signed_order_payload_validation_gate(payload, generated_at=GENERATED_AT)

        assert gate["status"] == STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED
        assert gate["input_intent_summary"]["forbidden_output_field_count"] == 1
        assert any(
            row.get("field") == "forbidden_output_or_execution_result"
            for row in gate["invalid_fields"]
        )
        assert gate["allowed_for_live"] is False
        assert gate["validation"]["valid"] is True
        _assert_forced_false(gate)
        _assert_no_signed_or_execution_output(gate)


def test_raw_secret_like_values_are_not_echoed() -> None:
    raw_marker = "raw-secret-marker-never-output-050"
    gate = build_signed_order_payload_validation_gate(
        _future_payload() | {"signature": raw_marker},
        generated_at=GENERATED_AT,
    )
    serialized = json.dumps(gate, sort_keys=True)

    assert gate["status"] == STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED
    assert raw_marker not in serialized
    assert gate["raw_payload_echoed"] is False
    assert gate["request_payload_echoed"] is False
    assert gate["no_raw_secrets_parsed_or_emitted"] is True
    assert gate["validation"]["valid"] is True


def test_readiness_evidence_replay_and_gonogo_keep_blockers_unresolved() -> None:
    gate = build_signed_order_payload_validation_gate(_future_payload(), generated_at=GENERATED_AT)
    gate_summary = summarize_signed_order_payload_validation_gate(gate, generated_at=GENERATED_AT)
    blocker_matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    readiness = build_canary_readiness_packet(
        signed_order_payload_validation_gate=gate,
        signed_order_payload_validation_gate_summary=gate_summary,
        generated_at=GENERATED_AT,
    )
    evidence_bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=blocker_matrix,
        signed_order_payload_validation_gate=gate,
        signed_order_payload_validation_gate_summary=gate_summary,
        generated_at=GENERATED_AT,
    )
    gonogo = build_tiny_live_canary_gonogo_gate(
        blocker_matrix=blocker_matrix,
        signed_order_payload_validation_gate_summary=gate_summary,
        generated_at=GENERATED_AT,
    )
    items = {item["evidence_type"]: item for item in evidence_bundle["evidence_items"]}

    assert readiness["signed_order_payload_validation_gate_status"] == STATUS_PAYLOAD_SHAPE_REVIEW_READY
    assert readiness["signed_payload_generation_enabled"] is False
    assert readiness["signed_order_generation_enabled"] is False
    assert "signed_order_payload_validation_gate_review_only" in {
        row["blocker_category"] for row in blocker_matrix["blockers"]
    }
    assert blocker_matrix["resolved_blocker_count"] == 0
    assert blocker_matrix["unresolved_blocker_count"] == blocker_matrix["blocker_count"]
    assert evidence_bundle["validation"]["valid"] is True
    assert "signed_order_payload_dry_run_validation_gate" in items
    item = items["signed_order_payload_dry_run_validation_gate"]
    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["live_approval"] is False
    assert gonogo["resolved_blocker_count"] == 0
    assert gonogo["canary_executable_now"] is False
    assert gonogo["allowed_for_live"] is False
    assert "signed_order_payload_validation_gate_review_only" in gonogo["no_go_reasons"]


def test_operator_ui_includes_passive_signed_payload_gate_section() -> None:
    gate = build_signed_order_payload_validation_gate(_future_payload(), generated_at=GENERATED_AT)
    gate_summary = summarize_signed_order_payload_validation_gate(
        gate,
        latest_signed_order_payload_validation_gate_path="signed_order_payload_validation_gate_050.json",
        generated_at=GENERATED_AT,
    )
    panel = build_operator_ui_panel_v1(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        signed_order_payload_validation_gate=gate,
        signed_order_payload_validation_gate_summary=gate_summary,
        generated_at=GENERATED_AT,
    )
    section = next(
        row for row in panel["sections"] if row["section_id"] == "signed_order_payload_validation_gate"
    )
    metrics = {metric["metric_id"]: metric["value"] for metric in section["metrics"]}

    assert section["title"] == "Signed Order Payload Validation Gate"
    assert panel["signed_order_payload_validation_gate_summary"][
        "signed_order_payload_validation_gate_section_ready"
    ] is True
    assert metrics["payload_shape_status"] == STATUS_PAYLOAD_SHAPE_REVIEW_READY
    assert metrics["signing_enabled"] is False
    assert metrics["signed_payload_generation_enabled"] is False
    assert metrics["signed_order_generation_enabled"] is False
    assert metrics["order_submission_enabled"] is False
    assert metrics["no_executable_action"] is True
    assert panel["validation"]["valid"] is True


def test_paper_daily_loop_emits_signed_payload_gate_without_network(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("external network calls are not allowed in task 050 tests")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-13", max_markets=6, output_dir=tmp_path)
    )
    artifact_path = tmp_path / "signed_order_payload_validation_gate_050.json"
    gate = json.loads(artifact_path.read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.safety_ok is True
    assert Path(result.signed_order_payload_validation_gate_path).name == artifact_path.name
    assert gate["status"] == STATUS_PAYLOAD_SHAPE_REVIEW_READY
    assert gate["validation"]["valid"] is True
    assert gate["signed_payload_generation_enabled"] is False
    assert gate["signed_order_generation_enabled"] is False
    assert gate["order_submission_enabled"] is False
    assert dashboard["signed_order_payload_validation_gate_summary"]["review_only"] is True
    assert dashboard["signed_order_payload_validation_gate_summary"]["no_executable_action"] is True
    assert dashboard["readiness_evidence_bundle_summary"]["readiness_evidence_bundle_review_ready"] is True
    assert panel["signed_order_payload_validation_gate_summary"][
        "signed_order_payload_validation_gate_section_ready"
    ] is True
    assert panel["operator_ui_panel_ready"] is True

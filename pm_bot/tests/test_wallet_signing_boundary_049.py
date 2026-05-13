from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness import build_canary_readiness_packet
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_enablement_config import build_live_enablement_config_preflight
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import build_tiny_live_canary_gonogo_gate
from pm_bot.trading_core.wallet_signing_boundary import (
    BOUNDARY_NAME,
    STATUS_SIGNING_DISABLED_REVIEW_ONLY,
    STATUS_SIGNING_REQUEST_REFUSED,
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
    validate_signing_request_for_review,
)

GENERATED_AT = "2026-05-13T00:00:00Z"

FORCED_FALSE_FIELDS = (
    "wallet_signing_enabled",
    "signing_enabled",
    "transaction_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "real_execution_available",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "live_connector_enabled",
    "order_submission_enabled",
)


def _assert_forced_false(value: dict[str, Any]) -> None:
    for field in FORCED_FALSE_FIELDS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0


def test_default_wallet_signing_boundary_is_disabled_review_only() -> None:
    report = build_wallet_signing_boundary_report(generated_at=GENERATED_AT)

    assert report["schema_version"] == "049.v1"
    assert report["boundary_name"] == BOUNDARY_NAME
    assert report["status"] == STATUS_SIGNING_DISABLED_REVIEW_ONLY
    assert report["review_only"] is True
    assert report["wallet_configured"] is False
    assert report["validation"]["valid"] is True
    assert report["no_raw_secrets_parsed_or_emitted"] is True
    assert report["blocked_reasons"]
    assert report["operator_required_actions"]
    assert report["future_enablement_requirements"]
    _assert_forced_false(report)


def test_no_raw_secrets_are_emitted_from_config_or_request() -> None:
    raw_marker = "raw-secret-marker-never-output-049"
    report = build_wallet_signing_boundary_report(
        {
            "PMBOT_WALLET_SIGNING_ENABLED": "true",
            "PMBOT_PRIVATE_KEY": raw_marker,
        },
        generated_at=GENERATED_AT,
    )
    refused = validate_signing_request_for_review(
        {
            "private_key": raw_marker,
            "payload": {"signed_payload": raw_marker},
        },
        boundary_report=report,
        generated_at=GENERATED_AT,
    )
    payload = json.dumps({"report": report, "refused": refused}, sort_keys=True)

    assert raw_marker not in payload
    assert report["safe_env_config_status"]["raw_like_config_key_count"] == 1
    assert refused["request_summary"]["request_payload_echoed"] is False
    assert refused["request_summary"]["top_level_field_names_emitted"] is False
    assert refused["validation"]["valid"] is True


def test_signing_request_is_refused_without_signature_or_signed_payload() -> None:
    refused = validate_signing_request_for_review(
        {"intent_id": "intent-049", "payload_kind": "review-only"},
        generated_at=GENERATED_AT,
    )

    assert refused["status"] == STATUS_SIGNING_REQUEST_REFUSED
    assert refused["signing_request_refused"] is True
    assert refused["validation"]["valid"] is True
    assert refused["signature_present"] is False
    assert refused["signed_payload_present"] is False
    assert refused["signed_order_present"] is False
    assert refused["transaction_hash_present"] is False
    assert refused["order_id_present"] is False
    assert "signature" not in refused
    assert "signed_payload" not in refused
    assert "signed_order" not in refused
    assert "transaction_hash" not in refused
    assert "signed_order_id" not in refused
    assert "order_id" not in refused
    _assert_forced_false(refused)


def test_requested_signing_enablement_stays_blocked_review_only() -> None:
    report = build_wallet_signing_boundary_report(
        {
            "PMBOT_WALLET_SIGNING_ENABLED": "true",
            "PMBOT_WALLET_ADDRESS_CONFIGURED": "true",
            "PMBOT_SIGNING_PROVIDER_CONFIGURED": "true",
            "PMBOT_SIGNING_DRY_RUN_ONLY": "true",
        },
        generated_at=GENERATED_AT,
    )
    summary = summarize_wallet_signing_boundary_report(report, generated_at=GENERATED_AT)

    assert report["status"] == STATUS_SIGNING_DISABLED_REVIEW_ONLY
    assert "wallet_signing_requested_but_blocked_by_task_049" in report["blocked_reasons"]
    assert summary["wallet_address_status"] == "configured:redacted_marker_only"
    assert summary["signing_provider_status"] == "configured:redacted_marker_only"
    assert summary["review_only"] is True
    _assert_forced_false(report)
    _assert_forced_false(summary)


def test_live_enablement_config_integration_keeps_wallet_signing_false() -> None:
    preflight = build_live_enablement_config_preflight(
        {
            "PMBOT_WALLET_SIGNING_ENABLED": "true",
            "PMBOT_WALLET_ADDRESS_CONFIGURED": "true",
            "PMBOT_SIGNING_PROVIDER_CONFIGURED": "true",
        },
        generated_at=GENERATED_AT,
    )

    assert preflight["wallet_signing_enabled"] is False
    assert preflight["signing_enabled"] is False
    assert preflight["signed_payload_generation_enabled"] is False
    assert preflight["wallet_signing_boundary_summary"]["wallet_signing_enabled"] is False
    assert preflight["wallet_signing_boundary_summary"]["signing_enabled"] is False
    assert preflight["wallet_signing_boundary_summary"]["signed_payload_generation_enabled"] is False
    assert preflight["allowed_for_live"] is False
    assert preflight["resolved_blocker_count"] == 0
    assert preflight["validation"]["valid"] is True


def test_readiness_evidence_replay_and_gonogo_keep_live_blockers_unresolved() -> None:
    wallet_report = build_wallet_signing_boundary_report(generated_at=GENERATED_AT)
    wallet_summary = summarize_wallet_signing_boundary_report(wallet_report, generated_at=GENERATED_AT)
    readiness = build_canary_readiness_packet(
        wallet_signing_boundary_report=wallet_report,
        generated_at=GENERATED_AT,
    )
    blocker_matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    evidence_bundle = build_live_canary_readiness_evidence_bundle(
        wallet_signing_boundary_report=wallet_report,
        wallet_signing_boundary_summary=wallet_summary,
        blocker_matrix=blocker_matrix,
        generated_at=GENERATED_AT,
    )
    gate = build_tiny_live_canary_gonogo_gate(
        blocker_matrix=blocker_matrix,
        generated_at=GENERATED_AT,
    )
    items = {item["evidence_type"]: item for item in evidence_bundle["evidence_items"]}

    assert readiness["wallet_signing_boundary_status"] == STATUS_SIGNING_DISABLED_REVIEW_ONLY
    assert readiness["wallet_signing_enabled"] is False
    assert readiness["signing_enabled"] is False
    assert "wallet_signing_boundary_scaffold_review_only" in {
        row["blocker_category"] for row in blocker_matrix["blockers"]
    }
    assert blocker_matrix["resolved_blocker_count"] == 0
    assert blocker_matrix["unresolved_blocker_count"] == blocker_matrix["blocker_count"]
    assert gate["resolved_blocker_count"] == 0
    assert gate["canary_executable_now"] is False
    assert gate["allowed_for_live"] is False
    assert items["wallet_signing_boundary_scaffold_dry_run_only"]["review_only"] is True
    assert items["wallet_signing_boundary_scaffold_dry_run_only"]["execution_enabling"] is False
    assert items["wallet_signing_boundary_scaffold_dry_run_only"]["live_approval"] is False
    assert evidence_bundle["validation"]["valid"] is True


def test_operator_ui_includes_passive_wallet_signing_boundary_section() -> None:
    wallet_report = build_wallet_signing_boundary_report(generated_at=GENERATED_AT)
    wallet_summary = summarize_wallet_signing_boundary_report(wallet_report, generated_at=GENERATED_AT)
    panel = build_operator_ui_panel_v1(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        wallet_signing_boundary_report=wallet_report,
        wallet_signing_boundary_summary=wallet_summary,
        generated_at=GENERATED_AT,
    )
    sections = {section["section_id"]: section for section in panel["sections"]}
    metrics = {metric["metric_id"]: metric["value"] for metric in sections["wallet_signing_boundary"]["metrics"]}

    assert sections["wallet_signing_boundary"]["title"] == "Wallet Signing Boundary"
    assert panel["wallet_signing_boundary_summary"]["wallet_signing_boundary_section_ready"] is True
    assert metrics["wallet_signing_enabled"] is False
    assert metrics["signing_enabled"] is False
    assert metrics["signed_payload_generation_enabled"] is False
    assert metrics["no_executable_action"] is True
    assert panel["validation"]["valid"] is True


def test_paper_daily_loop_emits_wallet_signing_boundary_artifact(
    monkeypatch, tmp_path: Path
) -> None:
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("external network calls are not allowed in wallet signing boundary tests")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-13", max_markets=6, output_dir=tmp_path)
    )
    artifact_path = tmp_path / "wallet_signing_boundary_049.json"
    report = json.loads(artifact_path.read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.safety_ok is True
    assert Path(result.wallet_signing_boundary_path).name == artifact_path.name
    assert report["status"] == STATUS_SIGNING_DISABLED_REVIEW_ONLY
    assert report["wallet_signing_enabled"] is False
    assert report["signing_enabled"] is False
    assert report["signed_payload_generation_enabled"] is False
    assert dashboard["wallet_signing_boundary_summary"]["no_executable_action"] is True
    assert dashboard["operator_ui_panel_v1_summary"]["wallet_signing_boundary_section_ready"] is True

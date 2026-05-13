from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.authenticated_polymarket_connector import (
    STATUS_CONFIG_REQUESTED_BUT_BLOCKED,
    STATUS_DRY_RUN_REFUSED,
    STATUS_REVIEW_ONLY,
    build_authenticated_connector_capability_report,
    build_authenticated_connector_dry_run_request,
    simulate_authenticated_connector_request,
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_enablement_config import (
    build_live_enablement_config_preflight,
    summarize_live_enablement_config_preflight,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import build_tiny_live_canary_gonogo_gate

GENERATED_AT = "2026-05-13T00:00:00Z"

FORCED_FALSE_FIELDS = (
    "authenticated_polymarket_enabled",
    "network_calls_enabled",
    "authenticated_calls_enabled",
    "live_connector_enabled",
    "order_submission_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "real_execution_available",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "execution_enabling",
)


def _assert_forced_false(value: Mapping[str, Any]) -> None:
    for field in FORCED_FALSE_FIELDS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0


def test_default_capability_report_is_disabled_review_only() -> None:
    report = build_authenticated_connector_capability_report(generated_at=GENERATED_AT)
    summary = summarize_authenticated_connector_capability_report(report, generated_at=GENERATED_AT)

    assert report["schema_version"] == "048.v1"
    assert report["connector_name"] == "authenticated_polymarket_connector_scaffold_dry_run_only"
    assert report["status"] == STATUS_REVIEW_ONLY
    assert report["review_only"] is True
    assert report["validation"]["valid"] is True
    _assert_forced_false(report)
    _assert_forced_false(summary)
    assert report["credentials_summary"]["credentials_redacted_or_missing_only"] is True
    assert report["credentials_summary"]["missing_count"] == 3
    assert report["credentials_summary"]["configured_redacted_count"] == 0
    assert report["credentials_summary"]["raw_values_emitted"] is False
    assert report["credentials_summary"]["actual_secret_values_exposed"] is False


def test_raw_credentials_are_never_emitted_when_presence_is_configured() -> None:
    raw_marker = "sk-secret-marker-never-output-048"
    report = build_authenticated_connector_capability_report(
        {
            "PMBOT_POLYMARKET_API_KEY_CONFIGURED": "true",
            "PMBOT_POLYMARKET_API_SECRET_CONFIGURED": "true",
            "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED": "true",
            "PMBOT_POLYMARKET_API_KEY": raw_marker,
            "PMBOT_POLYMARKET_API_SECRET": "raw-secret-marker-never-output-048",
            "PMBOT_POLYMARKET_FUNDER_ADDRESS": "0x1234567890abcdef1234567890abcdef12345678",
        },
        generated_at=GENERATED_AT,
    )
    payload = json.dumps(report, sort_keys=True)

    assert raw_marker not in payload
    assert "raw-secret-marker-never-output-048" not in payload
    assert "0x1234567890abcdef1234567890abcdef12345678" not in payload
    assert report["credentials_summary"]["configured_redacted_count"] == 3
    assert all(
        row["redacted_preview"] == "<configured:redacted>"
        for row in report["credentials_summary"]["credential_statuses_redacted"]
    )
    assert report["validation"]["valid"] is True
    _assert_forced_false(report)


def test_simulate_authenticated_request_refuses_without_network_or_fake_execution(
    monkeypatch,
) -> None:
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("external network calls are not allowed in task 048 tests")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    request = build_authenticated_connector_dry_run_request(
        request_kind="future_order_submission_shape_review",
        market_id="btc-dry-run-market",
        generated_at=GENERATED_AT,
    )
    response = simulate_authenticated_connector_request(request, generated_at=GENERATED_AT)

    assert response["status"] == STATUS_DRY_RUN_REFUSED
    assert response["would_call_authenticated_endpoint"] is False
    assert response["network_calls_enabled"] is False
    assert response["authenticated_calls_enabled"] is False
    assert response["order_submission_enabled"] is False
    assert response["signing_enabled"] is False
    assert response["wallet_signing_enabled"] is False
    assert response["real_execution_available"] is False
    assert response["order_id"] is None
    assert response["fill_id"] is None
    assert response["execution_id"] is None
    assert response["generated_fake_order_id"] is False
    assert response["generated_fake_fill"] is False
    assert response["generated_fake_execution"] is False
    assert response["external_api_calls_performed"] is False
    assert response["validation"]["valid"] is True


def test_requested_authenticated_enablement_remains_blocked_review_only() -> None:
    report = build_authenticated_connector_capability_report(
        {"PMBOT_AUTHENTICATED_POLYMARKET_ENABLED": "true"},
        generated_at=GENERATED_AT,
    )

    assert report["status"] == STATUS_CONFIG_REQUESTED_BUT_BLOCKED
    assert "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED_requested_but_blocked_by_task_048" in report[
        "blocked_reasons"
    ]
    assert report["config"]["requested_authenticated_enablement"] is True
    assert report["review_only"] is True
    assert report["validation"]["valid"] is True
    _assert_forced_false(report)


def test_live_enablement_config_integration_keeps_authenticated_connector_disabled() -> None:
    config = {
        "PMBOT_LIVE_MODE": "false",
        "PMBOT_LIVE_CANARY_ENABLED": "false",
        "PMBOT_ORDER_SUBMISSION_ENABLED": "false",
        "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED": "true",
        "PMBOT_WALLET_SIGNING_ENABLED": "false",
        "PMBOT_MAX_ORDER_NOTIONAL_USD": "1",
        "PMBOT_DAILY_LOSS_CAP_USD": "1",
        "PMBOT_TOTAL_EXPOSURE_CAP_USD": "1",
        "PMBOT_MAX_LIVE_TRADES_PER_DAY": "1",
        "PMBOT_ALLOWED_MARKET_SLUGS": "btc-one-market-demo",
        "PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL": "true",
        "PMBOT_REQUIRE_KILL_SWITCH_READY": "true",
    }
    preflight = build_live_enablement_config_preflight(
        config,
        generated_at=GENERATED_AT,
    )
    summary = summarize_live_enablement_config_preflight(preflight, generated_at=GENERATED_AT)

    assert preflight["authenticated_polymarket_enabled"] is False
    assert preflight["live_connector_enabled"] is False
    assert preflight["order_submission_enabled"] is False
    assert preflight["wallet_signing_enabled"] is False
    assert preflight["real_execution_available"] is False
    assert preflight["authenticated_polymarket_connector_scaffold_summary"]["review_only"] is True
    assert summary["authenticated_polymarket_connector_network_calls_enabled"] is False
    assert summary["authenticated_polymarket_connector_authenticated_calls_enabled"] is False
    assert summary["authenticated_polymarket_connector_order_submission_enabled"] is False
    assert preflight["validation"]["valid"] is True
    assert preflight["resolved_blocker_count"] == 0


def test_evidence_replay_and_gonogo_keep_live_blockers_unresolved() -> None:
    report = build_authenticated_connector_capability_report(generated_at=GENERATED_AT)
    summary = summarize_authenticated_connector_capability_report(report, generated_at=GENERATED_AT)
    blocker_matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=blocker_matrix,
        authenticated_polymarket_connector_scaffold=report,
        authenticated_polymarket_connector_scaffold_summary=summary,
        generated_at=GENERATED_AT,
    )
    items = {item["evidence_type"]: item for item in bundle["evidence_items"]}
    item = items["authenticated_polymarket_connector_scaffold_dry_run_only"]
    gate = build_tiny_live_canary_gonogo_gate(
        blocker_matrix=blocker_matrix,
        authenticated_polymarket_connector_scaffold_summary=summary,
        generated_at=GENERATED_AT,
    )

    assert blocker_matrix["resolved_blocker_count"] == 0
    assert "PMBOT-LIVE-BLOCKER-068" in blocker_matrix["unresolved_blockers"]
    assert bundle["validation"]["valid"] is True
    assert bundle["blocker_summary"]["resolved_live_blocker_count"] == 0
    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["live_approval"] is False
    assert item["network_calls_enabled"] is False
    assert item["order_submission_enabled"] is False
    assert gate["resolved_blocker_count"] == 0
    assert gate["allowed_for_live"] is False
    assert gate["canary_executable_now"] is False
    assert gate["live_execution_approved"] is False
    assert gate["real_execution_available"] is False
    assert gate["authenticated_polymarket_connector_scaffold_summary"]["review_only"] is True
    assert gate["authenticated_polymarket_connector_scaffold_summary"]["network_calls_enabled"] is False


def test_operator_ui_includes_passive_connector_scaffold_section() -> None:
    report = build_authenticated_connector_capability_report(generated_at=GENERATED_AT)
    summary = summarize_authenticated_connector_capability_report(report, generated_at=GENERATED_AT)
    panel = build_operator_ui_panel_v1(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        authenticated_polymarket_connector_scaffold=report,
        authenticated_polymarket_connector_scaffold_summary=summary,
        generated_at=GENERATED_AT,
    )
    section_ids = {section["section_id"] for section in panel["sections"]}
    section = next(
        section
        for section in panel["sections"]
        if section["section_id"] == "authenticated_polymarket_connector_scaffold"
    )
    metrics = {metric["metric_id"]: metric["value"] for metric in section["metrics"]}

    assert "authenticated_polymarket_connector_scaffold" in section_ids
    assert section["title"] == "Authenticated Polymarket Connector Scaffold"
    assert metrics["authenticated_calls_enabled"] is False
    assert metrics["network_calls_enabled"] is False
    assert metrics["order_submission_enabled"] is False
    assert metrics["credentials_redacted_or_missing_only"] is True
    assert metrics["no_executable_action"] is True
    assert panel["authenticated_polymarket_connector_scaffold_summary"][
        "authenticated_polymarket_connector_scaffold_section_ready"
    ] is True
    assert panel["validation"]["valid"] is True


def test_paper_daily_loop_emits_connector_scaffold_artifact_without_network(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("external network calls are not allowed in task 048 tests")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-13", max_markets=6, output_dir=tmp_path)
    )
    artifact_path = tmp_path / "authenticated_polymarket_connector_scaffold_048.json"
    report = json.loads(artifact_path.read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))
    evidence_items = {
        item["evidence_type"]: item
        for item in json.loads((tmp_path / "live_canary_readiness_evidence_bundle.json").read_text(encoding="utf-8"))[
            "evidence_items"
        ]
    }

    assert result.validation_passed is True
    assert result.safety_ok is True
    assert Path(result.authenticated_polymarket_connector_scaffold_path).name == artifact_path.name
    assert report["status"] == STATUS_REVIEW_ONLY
    assert report["network_calls_enabled"] is False
    assert report["authenticated_calls_enabled"] is False
    assert report["order_submission_enabled"] is False
    assert report["wallet_signing_enabled"] is False
    assert report["real_execution_available"] is False
    assert report["validation"]["valid"] is True
    assert dashboard["authenticated_polymarket_connector_scaffold_summary"]["review_only"] is True
    assert dashboard["authenticated_polymarket_connector_scaffold_summary"]["network_calls_enabled"] is False
    assert dashboard["operator_ui_panel_v1_summary"][
        "authenticated_polymarket_connector_scaffold_section_ready"
    ] is True
    assert panel["authenticated_polymarket_connector_scaffold_summary"][
        "authenticated_polymarket_connector_scaffold_section_ready"
    ] is True
    evidence_item = evidence_items["authenticated_polymarket_connector_scaffold_dry_run_only"]
    assert evidence_item["review_only"] is True
    assert evidence_item["execution_enabling"] is False
    assert evidence_item["live_approval"] is False

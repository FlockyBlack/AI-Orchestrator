from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    summarize_operator_ui_panel_v1,
)
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_supervised_tiny_canary_approval_packet,
    validate_secret_boundary_supervised_tiny_canary_approval_packet_summary,
)
from pm_bot.trading_core.supervised_tiny_canary_runbook import (
    OPERATOR_CHECKLIST_ITEMS,
    REQUIRED_FALSE_FLAGS,
    REQUIRED_SECTION_IDS,
    build_supervised_tiny_canary_approval_packet,
    render_supervised_tiny_canary_approval_packet_json,
    render_supervised_tiny_canary_approval_packet_markdown,
    summarize_supervised_tiny_canary_approval_packet,
    validate_supervised_tiny_canary_approval_packet,
)

GENERATED_AT = "2026-05-13T00:00:00Z"

FORBIDDEN_EXECUTION_KEYS = {
    "signature",
    "signed_payload",
    "signed_order",
    "tx_hash",
    "transaction_hash",
    "order_id",
    "order_ids",
    "fill",
    "fills",
    "fill_id",
    "execution",
    "execution_id",
    "execution_result",
    "balance",
    "balances",
    "pnl",
    "realized_pnl",
    "unrealized_pnl",
}


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.extend(_walk_keys(nested))
    return keys


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for field in REQUIRED_FALSE_FLAGS:
        assert value[field] is False
    assert value["authenticated_polymarket_enabled"] is False
    assert value["live_connector_enabled"] is False
    assert value["order_submission_enabled"] is False
    assert value["wallet_signing_enabled"] is False
    assert value["signing_enabled"] is False
    assert value["signed_payload_generation_enabled"] is False
    assert value["signed_order_generation_enabled"] is False
    assert value["allowed_for_live"] is False
    assert value["canary_executable_now"] is False
    assert value["live_execution_approved"] is False
    assert value["real_execution_available"] is False
    assert value["resolved_blocker_count"] == 0


def test_approval_packet_is_deterministic_and_valid() -> None:
    first = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)
    second = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)

    assert first == second
    assert first["schema_version"] == "051.v1"
    assert first["status"] == "REVIEW_READY_BLOCKED_FOR_LIVE"
    assert first["review_only"] is True
    assert first["validation"]["valid"] is True
    assert validate_supervised_tiny_canary_approval_packet(first, generated_at=GENERATED_AT)["valid"] is True
    _assert_required_false_flags(first)


def test_packet_cannot_be_interpreted_as_execution_approval() -> None:
    packet = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)
    refusal = packet["refusal_safety_text"].lower()

    assert packet["approval_packet_ready_for_human_review"] is True
    assert packet["approval_packet_may_be_used_as_live_approval"] is False
    assert packet["packet_cannot_be_interpreted_as_live_approval"] is True
    assert packet["operator_must_not_execute_from_this_packet"] is True
    assert packet["future_live_enabling_task_required"] is True
    assert "not live approval" in refusal
    assert "separate explicit" in refusal
    assert "live-enabling task" in refusal
    assert packet["validation"]["approval_packet_may_be_used_as_live_approval"] is False
    assert packet["validation"]["packet_cannot_be_interpreted_as_live_approval"] is True


def test_packet_references_required_live_readiness_components() -> None:
    packet = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)
    section_ids = {row["section_id"] for row in packet["sections"]}

    assert section_ids == set(REQUIRED_SECTION_IDS)
    assert "live_enablement_config_status" in section_ids
    assert "authenticated_connector_scaffold_status" in section_ids
    assert "wallet_signing_boundary_status" in section_ids
    assert "signed_order_payload_validation_gate_status" in section_ids
    assert "gonogo_status" in section_ids
    assert "evidence_bundle_status" in section_ids
    assert "replay_acceptance_status" in section_ids
    assert "telegram_operator_controls_status" in section_ids
    assert "telegram_mini_app_review_only_status" in section_ids
    assert all(row["review_only"] is True for row in packet["sections"])
    assert all(row["execution_enabling"] is False for row in packet["sections"])
    assert all(row["live_approval"] is False for row in packet["sections"])


def test_operator_checklist_and_future_actions_are_present_but_not_executable() -> None:
    packet = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)
    checklist_text = [row["text"] for row in packet["operator_checklist"]]

    assert checklist_text == [text for _, text in OPERATOR_CHECKLIST_ITEMS]
    assert "verify market selection" in checklist_text
    assert "verify max stake cap" in checklist_text
    assert "verify daily loss cap" in checklist_text
    assert "verify source/evidence freshness" in checklist_text
    assert "verify Telegram operator identity boundary" in checklist_text
    assert "verify no secret exposure" in checklist_text
    assert "verify canary is still blocked until a separate explicit live-enabling task" in checklist_text
    assert packet["future_required_actions"]
    assert all(row["executable_in_this_task"] is False for row in packet["future_required_actions"])
    assert all(row["implemented_in_this_task"] is False for row in packet["future_required_actions"])
    assert all(row["requires_separate_operator_approved_task"] is True for row in packet["future_required_actions"])


def test_no_fake_execution_artifacts_or_raw_credentials_are_emitted() -> None:
    raw_marker = "raw-secret-marker-never-output-051"
    packet = build_supervised_tiny_canary_approval_packet(
        telegram_operator_control_bot_summary={
            "telegram_bot_token_status": "configured_redacted",
            "raw_telegram_bot_token": raw_marker,
            "raw_operator_user_ids": [raw_marker],
        },
        generated_at=GENERATED_AT,
    )
    serialized = json.dumps(packet, sort_keys=True)
    keys = {key.lower() for key in _walk_keys(packet)}

    assert packet["fake_execution_artifacts_emitted"] is False
    assert packet["secret_or_raw_credential_fields_present"] is False
    assert packet["raw_credentials_printed_or_persisted"] is False
    assert raw_marker not in serialized
    assert not (keys & FORBIDDEN_EXECUTION_KEYS)
    assert packet["execution_artifact_absence"]["no_fake_signature_generated"] is True
    assert packet["execution_artifact_absence"]["no_fake_signed_payload_generated"] is True
    assert packet["execution_artifact_absence"]["no_fake_signed_order_generated"] is True
    assert packet["execution_artifact_absence"]["no_fake_order_id_generated"] is True
    assert packet["execution_artifact_absence"]["no_fake_transaction_hash_generated"] is True
    assert packet["execution_artifact_absence"]["no_fake_fill_generated"] is True
    assert packet["execution_artifact_absence"]["no_fake_execution_result_generated"] is True
    assert validate_secret_boundary_supervised_tiny_canary_approval_packet(packet)["valid"] is True


def test_json_markdown_and_summary_outputs_are_stable() -> None:
    packet = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)
    json_one = render_supervised_tiny_canary_approval_packet_json(packet)
    json_two = render_supervised_tiny_canary_approval_packet_json(packet)
    markdown_one = render_supervised_tiny_canary_approval_packet_markdown(packet)
    markdown_two = render_supervised_tiny_canary_approval_packet_markdown(packet)
    summary = summarize_supervised_tiny_canary_approval_packet(
        packet,
        latest_supervised_tiny_canary_approval_packet_json_path="supervised_tiny_canary_approval_packet_051.json",
        latest_supervised_tiny_canary_approval_packet_md_path="supervised_tiny_canary_approval_packet_051.md",
        generated_at=GENERATED_AT,
    )

    assert json_one == json_two
    assert markdown_one == markdown_two
    assert json.loads(json_one)["packet_id"] == packet["packet_id"]
    assert "This packet does not approve or enable live execution." in markdown_one
    assert summary["supervised_tiny_canary_approval_packet_section_ready"] is True
    assert summary["approval_packet_may_be_used_as_live_approval"] is False
    assert summary["packet_cannot_be_interpreted_as_live_approval"] is True
    assert summary["resolved_blocker_count"] == 0
    _assert_required_false_flags(summary)
    assert validate_secret_boundary_supervised_tiny_canary_approval_packet_summary(summary)["valid"] is True


def test_readiness_evidence_and_operator_ui_reference_packet_passively() -> None:
    packet = build_supervised_tiny_canary_approval_packet(generated_at=GENERATED_AT)
    summary = summarize_supervised_tiny_canary_approval_packet(packet, generated_at=GENERATED_AT)
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        supervised_tiny_canary_approval_packet=packet,
        supervised_tiny_canary_approval_packet_summary=summary,
        generated_at=GENERATED_AT,
    )
    evidence_types = {row["evidence_type"] for row in bundle["evidence_items"]}
    panel = build_operator_ui_panel_v1(
        readiness_evidence_bundle=bundle,
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        supervised_tiny_canary_approval_packet=packet,
        supervised_tiny_canary_approval_packet_summary=summary,
        latest_paths={
            "supervised_tiny_canary_approval_packet": "supervised_tiny_canary_approval_packet_051.json",
            "supervised_tiny_canary_approval_packet_md": "supervised_tiny_canary_approval_packet_051.md",
        },
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)

    assert "supervised_tiny_canary_runbook_operator_approval_packet" in evidence_types
    assert bundle["validation"]["valid"] is True
    assert bundle["live_execution_approved"] is False
    assert panel["validation"]["valid"] is True
    assert panel["supervised_tiny_canary_approval_packet_summary"]["review_only"] is True
    assert panel["supervised_tiny_canary_approval_packet_summary"]["live_execution_approved"] is False
    assert panel_summary["supervised_tiny_canary_approval_packet_section_ready"] is True
    assert panel_summary["supervised_tiny_canary_approval_packet_no_executable_action"] is True


def test_paper_daily_loop_emits_packet_artifacts_without_network(monkeypatch, tmp_path: Path) -> None:
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    packet_path = tmp_path / "supervised_tiny_canary_approval_packet_051.json"
    markdown_path = tmp_path / "supervised_tiny_canary_approval_packet_051.md"
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert result.validation_passed is True
    assert result.safety_ok is True
    assert result.supervised_tiny_canary_approval_packet_path.endswith(
        "supervised_tiny_canary_approval_packet_051.json"
    )
    assert result.supervised_tiny_canary_approval_packet_md_path.endswith(
        "supervised_tiny_canary_approval_packet_051.md"
    )
    assert packet_path.exists()
    assert markdown_path.exists()
    assert packet["validation"]["valid"] is True
    assert "does not approve or enable live execution" in markdown
    assert dashboard["supervised_tiny_canary_approval_packet_summary"]["review_only"] is True
    assert dashboard["supervised_tiny_canary_approval_packet_summary"]["live_execution_approved"] is False
    assert dashboard["operator_ui_panel_v1_summary"][
        "supervised_tiny_canary_approval_packet_section_ready"
    ] is True
    assert panel["supervised_tiny_canary_approval_packet_summary"]["order_submission_enabled"] is False
    _assert_required_false_flags(packet)

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    LIVE_DISABLED_WARNING,
    NEXT_REQUIRED_GATES,
    OPERATOR_UI_PANEL_V1_CONTRACT,
    build_operator_ui_panel_v1,
    render_operator_ui_panel_v1_html,
    render_operator_ui_panel_v1_json,
    render_operator_ui_panel_v1_markdown,
    summarize_operator_ui_panel_v1,
    validate_operator_ui_panel_v1,
)
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    BUNDLE_STATUS_REVIEW_READY,
    build_live_canary_readiness_evidence_bundle,
    summarize_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.risk_limits import default_paper_risk_limits
from pm_bot.trading_core.risk_prep_config import build_default_future_risk_engine_config
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_operator_ui_panel_payload,
    validate_secret_boundary_operator_ui_panel_rendered_html,
    validate_secret_boundary_operator_ui_panel_rendered_json,
    validate_secret_boundary_operator_ui_panel_rendered_markdown,
)
from pm_bot.trading_core.tiny_live_canary_manual_runbook import build_tiny_live_canary_manual_runbook
from pm_bot.trading_core.tiny_live_canary_preflight_contract import (
    build_tiny_live_canary_kill_switch_validation,
    build_tiny_live_canary_preflight_contract,
)


FORBIDDEN_UI_FIELDS = (
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


def _base_inputs() -> dict[str, Any]:
    blocker_matrix = build_live_connector_blocker_matrix()
    contract = build_tiny_live_canary_preflight_contract()
    runbook = build_tiny_live_canary_manual_runbook()
    kill_switch = build_tiny_live_canary_kill_switch_validation(contract["kill_switch_requirement"])
    bundle = build_live_canary_readiness_evidence_bundle(
        blocker_matrix=blocker_matrix,
        kill_switch_validation=kill_switch,
    )
    return {
        "readiness_evidence_bundle": bundle,
        "readiness_evidence_bundle_summary": summarize_live_canary_readiness_evidence_bundle(
            bundle,
            latest_readiness_evidence_bundle_path="live_canary_readiness_evidence_bundle.json",
        ),
        "blocker_matrix": blocker_matrix,
        "risk_limits": default_paper_risk_limits(),
        "risk_prep_config": build_default_future_risk_engine_config(),
        "tiny_live_canary_preflight_contract": contract,
        "tiny_live_canary_manual_runbook": runbook,
        "latest_paths": {
            "readiness_evidence_bundle": "live_canary_readiness_evidence_bundle.json",
            "tiny_live_canary_preflight_contract": "tiny_live_canary_preflight_contract.json",
            "paper_daily_loop_result": "paper_daily_loop_result.json",
        },
    }


def _panel() -> dict[str, Any]:
    return build_operator_ui_panel_v1(**_base_inputs())


def test_panel_builds_deterministically_and_validates_execution_posture() -> None:
    inputs = _base_inputs()
    first = build_operator_ui_panel_v1(**deepcopy(inputs))
    second = build_operator_ui_panel_v1(**deepcopy(inputs))

    assert first == second
    assert first["contract_version"] == OPERATOR_UI_PANEL_V1_CONTRACT
    assert first["validation"]["valid"] is True
    assert validate_operator_ui_panel_v1(first)["valid"] is True
    assert first["operator_ui_panel_ready"] is True
    assert first["readiness_panel_render_ready"] is True
    assert first["live_execution_approved"] is False
    assert first["canary_executable_now"] is False
    assert first["real_execution_available"] is False
    assert first["live_connector_enabled"] is False
    assert first["readiness_summary"]["mode"] == "paper/dry-run/live-disabled/future-canary-review"
    assert first["readiness_summary"]["warning"] == LIVE_DISABLED_WARNING


def test_panel_surfaces_readiness_evidence_blockers_risk_and_kill_switch() -> None:
    panel = _panel()

    assert panel["evidence_summary"]["readiness_evidence_bundle_status"] == BUNDLE_STATUS_REVIEW_READY
    assert panel["evidence_summary"]["evidence_item_count"] >= 14
    assert panel["evidence_summary"]["missing_required_evidence_count"] == 0
    assert panel["evidence_summary"]["readiness_bundle_is_not_live_approval"] is True
    assert panel["blocker_summary"]["blocker_matrix_status"] == "passed"
    assert panel["blocker_summary"]["critical_blockers"] == panel["blocker_summary"]["unresolved_blockers"]
    assert panel["blocker_summary"]["resolved_blockers"] == 0
    assert panel["blocker_summary"]["all_blockers_unresolved"] is True
    assert panel["blocker_summary"]["top_blockers"]
    assert panel["risk_limit_summary"]["risk_limit_panel_render_ready"] is True
    assert "max_daily_loss_usd" in panel["risk_limit_summary"]
    assert "max_order_notional_usd" in panel["risk_limit_summary"]
    assert panel["risk_limit_summary"]["halt_on_stale_data"] is True
    assert panel["risk_limit_summary"]["halt_on_audit_mismatch"] is True
    assert panel["risk_limit_summary"]["halt_on_kill_switch"] is True
    assert panel["risk_limit_summary"]["halt_on_missing_operator_intent"] is True
    assert panel["risk_limit_summary"]["risk_control_execution_gate_added"] is False
    assert panel["kill_switch_summary"]["kill_switch_requirements_defined"] is True
    assert panel["kill_switch_summary"]["kill_switch_verified_for_live"] is False
    assert panel["kill_switch_summary"]["kill_switch_blocks_live_execution"] is True
    assert panel["kill_switch_summary"]["current_kill_switch_state"] == "blocks_live"


def test_paper_summary_handles_missing_data_without_inventing_pnl() -> None:
    panel = _panel()

    assert panel["paper_summary"]["paper_pnl"]["realized_usd"] == "not_available"
    assert panel["paper_summary"]["paper_pnl"]["unrealized_usd"] == "not_available"
    assert panel["paper_summary"]["paper_exposure"] == "not_available"
    assert panel["paper_summary"]["paper_positions_count"] == "not_available"
    assert panel["paper_summary"]["pnl_invented"] is False
    assert panel["paper_summary"]["outcome_resolution_invented"] is False


def test_operator_packets_audit_replay_next_gates_and_action_states_are_passive() -> None:
    panel = _panel()
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert {
        "header_execution_posture",
        "readiness_evidence_bundle",
        "live_blockers",
        "risk_limits",
        "kill_switch",
        "paper_trading_summary",
        "operator_packets",
        "audit_replay",
        "next_gates",
    }.issubset(section_ids)
    assert panel["operator_packet_summary"]["operator_approval_packet_status"] == "not_available"
    assert panel["operator_packet_summary"]["operator_intent_packet_status"] == "not_available"
    assert panel["operator_packet_summary"]["operator_intent_is_human_acknowledgement_only"] is False
    assert panel["operator_packet_summary"]["operator_intent_is_not_live_approval"] is True
    assert panel["audit_replay_summary"]["audit_replay_status"] == "not_available"
    assert panel["audit_replay_summary"]["replay_is_not_execution"] is True
    assert list(panel["next_required_gates"]) == list(NEXT_REQUIRED_GATES)
    assert all(action["execution_enabled"] is False for action in panel["action_states"])
    assert all(action["live_action_exposed"] is False for action in panel["action_states"])
    assert panel["ui_exposes_no_executable_live_action"] is True


def test_renderers_are_deterministic_static_and_secret_boundary_safe() -> None:
    panel = _panel()
    json_one = render_operator_ui_panel_v1_json(panel)
    json_two = render_operator_ui_panel_v1_json(panel)
    markdown_one = render_operator_ui_panel_v1_markdown(panel)
    markdown_two = render_operator_ui_panel_v1_markdown(panel)
    html_one = render_operator_ui_panel_v1_html(panel)
    html_two = render_operator_ui_panel_v1_html(panel)

    assert json_one == json_two
    assert markdown_one == markdown_two
    assert html_one == html_two
    assert json.loads(json_one)["panel_id"] == panel["panel_id"]
    assert "Live execution is disabled in this build." in markdown_one
    assert "<script" not in html_one.lower()
    assert "https://" not in html_one.lower()
    assert "http://" not in html_one.lower()
    assert "cdn" not in html_one.lower()
    assert validate_secret_boundary_operator_ui_panel_rendered_json(json_one)["valid"] is True
    assert validate_secret_boundary_operator_ui_panel_rendered_markdown(markdown_one)["valid"] is True
    assert validate_secret_boundary_operator_ui_panel_rendered_html(html_one)["valid"] is True


def test_ui_panel_payload_rejects_forbidden_secret_signing_and_order_fields() -> None:
    panel = _panel()

    assert validate_secret_boundary_operator_ui_panel_payload(panel)["valid"] is True
    for field in FORBIDDEN_UI_FIELDS:
        unsafe = deepcopy(panel)
        unsafe[field] = "<redacted>"

        validation = validate_operator_ui_panel_v1(unsafe)
        boundary = validate_secret_boundary_operator_ui_panel_payload(unsafe)

        assert validation["valid"] is False
        assert boundary["valid"] is False
        assert f"$.{field}" in boundary["forbidden_secret_field_paths"]


def test_paper_daily_loop_integration_surfaces_panel_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "operator_ui_panel_v1.md").read_text(encoding="utf-8")
    html = (tmp_path / "operator_ui_panel_v1.html").read_text(encoding="utf-8")
    summary = dashboard["operator_ui_panel_v1_summary"]

    assert result.validation_passed is True
    assert result.operator_ui_panel_json_path.endswith("operator_ui_panel_v1.json")
    assert result.operator_ui_panel_md_path.endswith("operator_ui_panel_v1.md")
    assert result.operator_ui_panel_html_path.endswith("operator_ui_panel_v1.html")
    assert panel["operator_ui_panel_ready"] is True
    assert panel["evidence_summary"]["readiness_evidence_bundle_status"] == BUNDLE_STATUS_REVIEW_READY
    assert panel["evidence_summary"]["evidence_item_count"] >= 14
    assert panel["evidence_summary"]["missing_required_evidence_count"] == 0
    assert panel["blocker_summary"]["unresolved_blockers"] >= 31
    assert panel["risk_limit_summary"]["risk_limit_panel_render_ready"] is True
    assert panel["kill_switch_summary"]["kill_switch_verified_for_live"] is False
    assert panel["operator_packet_summary"]["operator_approval_packet_status"] == "operator_review_ready"
    assert panel["operator_packet_summary"]["operator_intent_packet_status"] == "operator_intent_packet_review_ready"
    assert panel["operator_packet_summary"]["operator_intent_is_human_acknowledgement_only"] is True
    assert panel["operator_packet_summary"]["operator_intent_is_not_live_approval"] is True
    assert panel["audit_replay_summary"]["audit_replay_status"] == "replay_passed"
    assert panel["audit_replay_summary"]["replay_is_not_execution"] is True
    assert panel["live_execution_approved"] is False
    assert panel["canary_executable_now"] is False
    assert panel["real_execution_available"] is False
    assert panel["live_connector_enabled"] is False
    assert summary == summarize_operator_ui_panel_v1(panel)
    assert "Live execution is disabled in this build." in markdown
    assert "<script" not in html.lower()
    assert all(action["execution_enabled"] is False for action in panel["action_states"])

from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path

from ai_orchestrator.codex_queue.nightly_lane_batch_runner import validate_nightly_lane_batch_plan
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_replay_acceptance import (
    ACCEPTANCE_CASE_IDS,
    LIVE_CONNECTOR_BLOCKERS,
    build_canary_acceptance_case_artifacts,
    build_canary_acceptance_matrix,
    build_canary_replay_report,
    build_live_connector_blocker_matrix,
    build_operator_live_canary_checklist,
    scan_relevant_canary_live_prep_artifacts,
)
from pm_bot.trading_core.live_canary_readiness import CANARY_STATUS_BLOCKED, CANARY_STATUS_DRY_RUN_READY


def _approved_artifacts() -> dict[str, object]:
    return build_canary_acceptance_case_artifacts("approved_for_dry_run_only")


def test_replay_deterministic_behavior() -> None:
    artifacts = _approved_artifacts()
    packet = artifacts["packet"]
    receipt = artifacts["canary_receipt"]

    first = build_canary_replay_report(packets=[packet], receipts=[receipt])
    second = build_canary_replay_report(packets=[packet], receipts=[receipt])

    assert first == second
    assert first["status"] == "passed"
    assert first["rows"][0]["idempotency_passed"] is True
    assert first["rows"][0]["actual_canary_status"] == CANARY_STATUS_DRY_RUN_READY


def test_replay_detects_missing_references() -> None:
    artifacts = _approved_artifacts()
    packet = deepcopy(artifacts["packet"])
    for field in (
        "source_evidence_ref",
        "risk_decision_id",
        "wallet_boundary_packet_id",
        "signing_simulator_receipt_id",
    ):
        packet[field] = ""

    report = build_canary_replay_report(packets=[packet], receipts=[artifacts["canary_receipt"]])

    assert report["status"] == "failed"
    assert report["missing_reference_count"] == 4
    assert report["rows"][0]["actual_canary_status"] == CANARY_STATUS_BLOCKED
    assert set(report["rows"][0]["missing_references"]) == {
        "source_evidence_ref",
        "risk_decision_id",
        "wallet_boundary_packet_id",
        "signing_simulator_receipt_id",
    }


def test_replay_detects_duplicate_logical_canary_ids_and_reason_drift() -> None:
    artifacts = _approved_artifacts()
    packet = deepcopy(artifacts["packet"])
    drifted = deepcopy(packet)
    drifted["reason_codes"] = ["DRIFTED_REASON_CODE"]

    duplicate_report = build_canary_replay_report(
        packets=[packet, deepcopy(packet)],
        receipts=[artifacts["canary_receipt"]],
    )
    drift_report = build_canary_replay_report(packets=[drifted], receipts=[artifacts["canary_receipt"]])

    assert duplicate_report["status"] == "failed"
    assert duplicate_report["duplicate_canary_ids"] == [packet["canary_id"]]
    assert duplicate_report["duplicate_logical_keys"] == [packet["idempotency"]["logical_key"]]
    assert drift_report["status"] == "failed"
    assert drift_report["reason_code_drift_count"] == 1


def test_acceptance_matrix_all_key_cases() -> None:
    matrix = build_canary_acceptance_matrix()
    rows = {row["case_id"]: row for row in matrix["rows"]}

    assert matrix["status"] == "passed"
    assert tuple(rows) == ACCEPTANCE_CASE_IDS
    assert rows["approved_for_dry_run_only"]["actual_canary_status"] == CANARY_STATUS_DRY_RUN_READY
    assert rows["approved_for_dry_run_only"]["dry_run_receipt_can_be_produced"] is True
    assert rows["missing_evidence"]["actual_canary_status"] == CANARY_STATUS_BLOCKED
    assert "MISSING_SOURCE_EVIDENCE_REF" in rows["missing_evidence"]["actual_reason_codes"]
    assert rows["stale_evidence"]["actual_reason_codes"] == ["EVIDENCE_NOT_FRESH"]
    assert rows["source_gap_present"]["actual_reason_codes"] == ["SOURCE_GAP_PRESENT"]
    assert rows["missing_risk_decision"]["actual_reason_codes"] == ["MISSING_RISK_DECISION"]
    assert rows["risk_blocked"]["actual_canary_status"] == CANARY_STATUS_BLOCKED
    assert "RISK_DECISION_NOT_ALLOWED" in rows["risk_blocked"]["actual_reason_codes"]
    assert "KILL_SWITCH_ENABLED" in rows["kill_switch_enabled"]["actual_reason_codes"]
    assert "MISSING_WALLET_BOUNDARY_PACKET" in rows["missing_wallet_boundary_packet"]["actual_reason_codes"]
    assert rows["wallet_boundary_blocked"]["actual_reason_codes"] == ["WALLET_BOUNDARY_PACKET_NOT_READY"]
    assert rows["missing_signing_simulator_receipt"]["actual_reason_codes"] == [
        "MISSING_SIGNING_SIMULATOR_RECEIPT"
    ]
    assert rows["signing_simulator_blocked"]["actual_reason_codes"] == ["SIGNING_SIMULATOR_RECEIPT_NOT_READY"]
    assert "DRY_RUN_OPERATOR_APPROVAL_REQUIRED" in rows["missing_operator_dry_run_approval"]["actual_reason_codes"]
    assert rows["rejected_operator_approval"]["expected_canary_status"] == "rejected"
    assert rows["expired_operator_approval"]["actual_reason_codes"] == ["OPERATOR_APPROVAL_EXPIRED"]
    assert "FORBIDDEN_CANARY_FIELD_PRESENT" in rows["forbidden_field_present"]["actual_reason_codes"]
    assert all(row["live_execution_remains_forbidden"] is True for row in rows.values())


def test_blocker_matrix_contains_required_live_blockers() -> None:
    matrix = build_live_connector_blocker_matrix()
    blocker_names = {row["blocker_name"] for row in matrix["blockers"]}

    assert matrix["status"] == "passed"
    assert matrix["blocker_count"] == 10
    assert len(matrix["critical_blockers"]) == 10
    assert {row["blocker_name"] for row in LIVE_CONNECTOR_BLOCKERS} == blocker_names
    assert "real wallet connector absent" in blocker_names
    assert "secret handling policy absent or incomplete" in blocker_names
    assert "real signing adapter absent" in blocker_names
    assert "order adapter absent" in blocker_names
    assert "authenticated endpoint policy absent" in blocker_names
    assert "production kill switch not wired to real execution" in blocker_names
    assert "operator live approval flow absent" in blocker_names
    assert "post-trade audit absent" in blocker_names
    assert "real balance/exposure reconciliation absent" in blocker_names
    assert "emergency halt procedure absent" in blocker_names
    assert matrix["live_execution_available"] is False


def test_operator_checklist_is_dry_run_only_and_practical() -> None:
    checklist = build_operator_live_canary_checklist()

    assert checklist["status"] == "passed"
    assert checklist["current_status"] == "dry_run_only_live_execution_unavailable"
    assert checklist["live_execution_available"] is False
    assert checklist["live_execution_allowed"] is False
    assert "python -m pm_bot.trading_core.live_canary_replay_acceptance" in checklist[
        "dry_run_only_command_or_runner_path"
    ]
    assert any("live_canary_readiness_packet.json" in item for item in checklist["files_or_artifacts_that_must_exist"])
    assert any("canary replay report status passed" in item for item in checklist["validations_that_must_pass"])
    assert any("dry-run-only operator approval" in item for item in checklist["manual_approvals_required"])
    assert "real wallet access" in checklist["must_still_be_forbidden"]
    assert checklist["dry_run_only_assertion"] == "This checklist does not make live execution available."


def test_dashboard_report_surfaces_replay_acceptance_and_blockers(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    dashboard_md = (tmp_path / "paper_daily_dashboard.md").read_text(encoding="utf-8")
    summary = dashboard["live_canary_readiness_summary"]

    assert result.validation_passed is True
    assert summary["canary_replay_status"] == "passed"
    assert summary["acceptance_matrix_status"] == "passed"
    assert summary["acceptance_matrix_failed_case_count"] == 0
    assert summary["live_connector_blocker_count"] == 10
    assert summary["critical_blocker_count"] == 10
    assert summary["next_recommended_non_live_task"]
    assert summary["dry_run_only_assertion"] == "This checklist does not make live execution available."
    assert "Canary replay status" in dashboard_md
    assert "Live connector blockers" in dashboard_md


def test_nightly_batch_example_runs_fake_dry_run_only_shape() -> None:
    plan = json.loads(
        Path(
            "docs/ORCH_PMBOT_TRADING_MVP_030_CANARY_REPLAY_ACCEPTANCE_AND_LIVE_CONNECTOR_BLOCKER_MATRIX_NIGHTLY_BATCH_PLAN.example.json"
        ).read_text(encoding="utf-8")
    )
    validation = validate_nightly_lane_batch_plan(plan)

    assert validation["valid"] is True, validation["errors"]
    assert validation["plan"]["executor_mode"] == "fake"
    assert validation["plan"]["lane_mode"] == "plan_only"
    assert validation["plan"]["allow_real_codex_invocation"] is False
    assert validation["plan"]["safety_flags"]["no_external_apis"] is True
    assert validation["plan"]["safety_flags"]["no_wallet_signing_or_orders"] is True
    assert [task["task_id"] for task in validation["plan"]["tasks"]] == [
        "ORCH-PMBOT-TRADING-MVP-030-CANARY-READINESS-DRY-RUN",
        "ORCH-PMBOT-TRADING-MVP-030-CANARY-REPLAY-SUITE",
        "ORCH-PMBOT-TRADING-MVP-030-LIVE-CONNECTOR-BLOCKER-MATRIX",
    ]


def test_forbidden_field_scanner_catches_unsafe_fields_only_in_relevant_artifacts(tmp_path: Path) -> None:
    forbidden_names = [
        "private_key",
        "seed",
        "mnemonic",
        "secret",
        "signature",
        "signed_order",
        "order_payload",
        "auth_token",
        "api_key",
        "bearer",
        "clob_order",
        "transaction_hash",
        "wallet_private_key",
        "polymarket_api_key",
    ]
    relevant = tmp_path / "live_connector_blocker_matrix.json"
    unrelated = tmp_path / "unrelated.json"
    relevant.write_text(json.dumps({name: "unsafe" for name in forbidden_names}), encoding="utf-8")
    unrelated.write_text(json.dumps({"private_key": "ignored"}), encoding="utf-8")

    scan = scan_relevant_canary_live_prep_artifacts([relevant, unrelated])
    paths = set(scan["rows"][0]["forbidden_field_paths"])

    assert scan["artifact_count"] == 1
    assert scan["status"] == "failed"
    for name in forbidden_names:
        assert f"$.{name}" in paths


def test_no_real_wallet_signing_order_auth_endpoint_code_or_external_calls(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    source = Path("pm_bot/trading_core/live_canary_replay_acceptance.py").read_text(encoding="utf-8").lower()
    forbidden_runtime_markers = (
        "import requests",
        "import httpx",
        "socket.",
        "web3",
        "eth_account",
        "sign_transaction(",
        "send_raw_transaction(",
        "place_order(",
        "create_order(",
        "clobclient",
        "authenticatedsession",
    )

    assert all(marker not in source for marker in forbidden_runtime_markers)
    assert build_canary_acceptance_matrix()["external_api_calls_performed"] is False
    assert build_live_connector_blocker_matrix()["external_api_calls_performed"] is False


def test_no_invented_outcome_or_pnl_in_replay_acceptance_or_blocker_reports() -> None:
    artifacts = _approved_artifacts()
    replay = build_canary_replay_report(packets=[artifacts["packet"]], receipts=[artifacts["canary_receipt"]])
    acceptance = build_canary_acceptance_matrix()
    blocker = build_live_connector_blocker_matrix()
    checklist = build_operator_live_canary_checklist()

    for artifact in (replay, acceptance, blocker, checklist):
        assert artifact["outcome_resolution_invented"] is False
        assert artifact["pnl_invented"] is False

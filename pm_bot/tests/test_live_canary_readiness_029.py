from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ai_orchestrator.codex_queue.nightly_lane_batch_runner import validate_nightly_lane_batch_plan
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness import (
    APPROVAL_DRY_RUN_ONLY,
    CANARY_STATUS_BLOCKED,
    CANARY_STATUS_DRY_RUN_READY,
    CANARY_STATUS_NEEDS_OPERATOR_APPROVAL,
    DRY_RUN_ACCEPTANCE_ACCEPTED,
    DRY_RUN_ACCEPTANCE_BLOCKED,
    LIVE_CANARY_READINESS_PACKET_CONTRACT,
    CanaryReadinessValidationError,
    build_canary_dry_run_acceptance_receipt,
    build_canary_operator_approval_record,
    build_canary_readiness_packet,
    scan_forbidden_fields,
    validate_canary_readiness_packet,
    write_canary_readiness_artifacts,
)
from pm_bot.trading_core.risk_engine import DECISION_ALLOWED, build_risk_decision_input, evaluate_risk_decision
from pm_bot.trading_core.risk_prep_config import (
    RISK_ENGINE_CONFIG_VERSION,
    build_default_risk_engine_config,
    validate_risk_engine_config,
)
from pm_bot.trading_core.signing_simulator import STATUS_DRY_RUN_RECEIPT_READY, simulate_signing_for_execution_request
from pm_bot.trading_core.wallet_execution_boundary import (
    STATUS_APPROVED_FOR_FUTURE_SIMULATION,
    build_execution_request_packet,
    build_risk_approved_action_packet,
)


def _risk_config(**overrides):  # type: ignore[no-untyped-def]
    config = build_default_risk_engine_config()
    config.update(
        {
            "max_total_exposure_usd": 100.0,
            "max_market_exposure_usd": 50.0,
            "max_per_market_exposure_usd": 50.0,
            "max_single_action_notional_usd": 25.0,
            "kill_switch_enabled": False,
            "manual_approval_required": True,
            "require_fresh_evidence": True,
            "block_on_source_gap": True,
        }
    )
    config.update(overrides)
    if "max_market_exposure_usd" in overrides and "max_per_market_exposure_usd" not in overrides:
        config["max_per_market_exposure_usd"] = config["max_market_exposure_usd"]
    valid, errors = validate_risk_engine_config(config)
    assert valid is True, errors
    return config


def _decision_input(**overrides):  # type: ignore[no-untyped-def]
    value = build_risk_decision_input(
        run_id="canary-readiness-test-run",
        market_id="market-1",
        intent_id="intent-1",
        hypothesis_id="hypothesis-1",
        action_type="proposed_canary_dry_run",
        requested_notional_usd=10.0,
        current_total_exposure_usd=0.0,
        current_market_exposure_usd=0.0,
        evidence_freshness_status="fresh",
        source_gap_status="no_gap",
        operator_approval_status="approved",
        config_version=RISK_ENGINE_CONFIG_VERSION,
    )
    value.update(overrides)
    return value


def _candidate() -> dict[str, object]:
    return {
        "daily_run_id": "canary-readiness-test-run",
        "run_date": "2026-05-11",
        "intent_id": "intent-1",
        "market_id": "market-1",
        "market_title": "Static fixture market",
        "market_slug": "static-fixture-market",
        "hypothesis_id": "hypothesis-1",
        "paper_action_type": "simulated_entry",
        "intended_notional_usd": 10.0,
    }


def _source_ledger(*, freshness: str = "fresh", gap_status: str = "no_gap") -> dict[str, Any]:
    return {
        "refresh_id": "source-refresh-canary-test",
        "run_id": "canary-readiness-test-run",
        "run_date": "2026-05-11",
        "network_used": False,
        "external_api_calls_performed": False,
        "summary_counts": {
            "records": 1,
            "fresh_records": 1 if freshness == "fresh" else 0,
            "stale_records": 1 if freshness == "stale" else 0,
            "missing_source_reference_records": 1 if freshness == "missing" else 0,
            "missing_local_capture_records": 0,
            "unknown_freshness_records": 1 if freshness == "unknown" else 0,
        },
        "records": [
            {
                "record_id": "source-record-market-1",
                "market_id": "market-1",
                "freshness_status": freshness,
            }
        ],
        "quality_ledger": {
            "quality_ledger_id": "quality-ledger-canary-test",
            "summary_counts": {
                "markets_with_gaps": 0 if gap_status == "no_gap" else 1,
                "missing_evidence_gaps": 0 if gap_status == "no_gap" else 1,
            },
            "market_source_status": [
                {
                    "market_id": "market-1",
                    "gap_status": gap_status,
                    "fresh_count": 1 if freshness == "fresh" else 0,
                    "stale_count": 1 if freshness == "stale" else 0,
                    "unknown_freshness_count": 1 if freshness == "unknown" else 0,
                    "missing_source_reference_count": 1 if freshness == "missing" else 0,
                    "missing_local_capture_count": 0,
                }
            ],
        },
    }


def _strategy_ledger(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_paper_strategy_evaluation_ledger.v1",
        "ledger_id": "paper-strategy-evaluation-ledger-canary-test",
        "generated_at": "2026-05-11T00:00:00Z",
        "run_id": "canary-readiness-test-run",
        "run_date": "2026-05-11",
        "records": [
            {
                "evaluation_record_id": "paper-strategy-eval-canary-market-1",
                "run_id": "canary-readiness-test-run",
                "run_date": "2026-05-11",
                "market_id": "market-1",
                "market_title": "Static fixture market",
                "market_slug": "static-fixture-market",
                "intent_id": "intent-1",
                "hypothesis_id": "hypothesis-1",
                "simulated_action_type": "simulated_entry",
                "risk_engine_decision": {
                    "risk_decision_id": decision.get("risk_decision_id", ""),
                    "audit_id": decision.get("audit_id", ""),
                    "decision": decision.get("decision", ""),
                    "reason_codes": decision.get("reason_codes", []),
                    "requested_notional_usd": decision.get("decision_input", {}).get("requested_notional_usd", 0),
                },
                "source_links": {
                    "analysis_artifact_path": "pm_bot/tests/fixtures/canary/analysis.json",
                    "evidence_artifact_paths": ["pm_bot/tests/fixtures/canary/source.json"],
                },
            }
        ],
        "record_count": 1,
        "idempotency": {"record_ids_unique": True},
        "paper_only": True,
        "analysis_only": True,
        "unresolved_pnl_not_invented": True,
    }


def _bundle(
    *,
    config_overrides=None,  # type: ignore[no-untyped-def]
    input_overrides=None,  # type: ignore[no-untyped-def]
    source_ledger=None,  # type: ignore[no-untyped-def]
    source_freshness: str = "fresh",
    source_gap: str = "no_gap",
    include_risk: bool = True,
    include_wallet: bool = True,
    include_signing: bool = True,
    include_approval: bool = True,
    approval_status: str = APPROVAL_DRY_RUN_ONLY,
) -> dict[str, Any]:
    config = _risk_config(**(config_overrides or {}))
    decision = evaluate_risk_decision(_decision_input(**(input_overrides or {})), config)
    action_packet = build_risk_approved_action_packet(
        candidate=_candidate(),
        risk_decision=decision,
        risk_config=config,
    )
    wallet_packet = build_execution_request_packet(risk_approved_action_packet=action_packet)
    signing_receipt = simulate_signing_for_execution_request(wallet_packet)
    strategy = _strategy_ledger(decision)
    risk_ledger = {
        "ledger_id": "risk-engine-decision-ledger-canary-test",
        "run_id": "canary-readiness-test-run",
        "run_date": "2026-05-11",
        "decisions": [decision] if include_risk else [],
    }
    wallet_ledger = {
        "ledger_id": "wallet-boundary-audit-ledger-canary-test",
        "run_id": "canary-readiness-test-run",
        "run_date": "2026-05-11",
        "execution_request_packets": [wallet_packet] if include_wallet else [],
    }
    signing_ledger = {
        "ledger_id": "dry-run-execution-receipt-ledger-canary-test",
        "run_id": "canary-readiness-test-run",
        "run_date": "2026-05-11",
        "receipts": [signing_receipt] if include_signing else [],
    }
    approval = (
        build_canary_operator_approval_record(
            run_id="canary-readiness-test-run",
            market_id="market-1",
            approval_status=approval_status,
        )
        if include_approval
        else None
    )
    packet = build_canary_readiness_packet(
        paper_strategy_ledger=strategy,
        source_evidence_status=source_ledger if source_ledger is not None else _source_ledger(
            freshness=source_freshness,
            gap_status=source_gap,
        ),
        risk_decision_ledger=risk_ledger,
        wallet_boundary_audit_ledger=wallet_ledger,
        signing_simulator_receipt_ledger=signing_ledger,
        operator_approval_record=approval,
        run_context={
            "run_id": "canary-readiness-test-run",
            "run_date": "2026-05-11",
            "tracked_markets": [_candidate()],
        },
        canary_market_id="market-1",
    )
    canary_receipt = build_canary_dry_run_acceptance_receipt(packet)
    return {
        "config": config,
        "decision": decision,
        "wallet_packet": wallet_packet,
        "signing_receipt": signing_receipt,
        "strategy_ledger": strategy,
        "risk_ledger": risk_ledger,
        "wallet_ledger": wallet_ledger,
        "signing_ledger": signing_ledger,
        "approval": approval,
        "packet": packet,
        "canary_receipt": canary_receipt,
    }


def test_canary_packet_schema_contract_and_happy_path() -> None:
    bundle = _bundle()
    packet = bundle["packet"]
    receipt = bundle["canary_receipt"]
    valid, errors = validate_canary_readiness_packet(packet)

    assert valid is True, errors
    assert packet["contract_version"] == LIVE_CANARY_READINESS_PACKET_CONTRACT
    assert packet["canary_status"] == CANARY_STATUS_DRY_RUN_READY
    assert packet["risk_decision_status"] == DECISION_ALLOWED
    assert packet["wallet_boundary_status"] == STATUS_APPROVED_FOR_FUTURE_SIMULATION
    assert packet["signing_simulator_receipt_status"] == STATUS_DRY_RUN_RECEIPT_READY
    assert packet["safety_assertions"] == {
        "no_private_key": True,
        "no_real_signature": True,
        "no_order_endpoint": True,
        "no_external_api_call": True,
        "no_real_execution": True,
    }
    assert receipt["acceptance_status"] == DRY_RUN_ACCEPTANCE_ACCEPTED
    assert receipt["no_real_wallet_used"] is True
    assert receipt["no_real_private_key_used"] is True
    assert receipt["no_real_signature_created"] is True
    assert receipt["no_real_order_submitted"] is True
    assert receipt["no_authenticated_endpoint_called"] is True
    assert receipt["no_external_api_call_performed"] is True
    assert receipt["no_live_execution_performed"] is True


def test_missing_evidence_blocks_canary() -> None:
    packet = _bundle(source_ledger={})["packet"]

    assert packet["canary_status"] == CANARY_STATUS_BLOCKED
    assert "MISSING_SOURCE_EVIDENCE_REF" in packet["reason_codes"]
    assert "EVIDENCE_NOT_FRESH" in packet["reason_codes"]
    assert "source_evidence_status" in packet["missing_artifact_summary"]


def test_stale_evidence_blocks_canary_when_freshness_is_required() -> None:
    packet = _bundle(
        input_overrides={"evidence_freshness_status": "stale"},
        source_freshness="stale",
    )["packet"]

    assert packet["canary_status"] == CANARY_STATUS_BLOCKED
    assert "EVIDENCE_NOT_FRESH" in packet["reason_codes"]


def test_missing_risk_decision_blocks_canary() -> None:
    packet = _bundle(include_risk=False)["packet"]

    assert packet["canary_status"] == CANARY_STATUS_BLOCKED
    assert "MISSING_RISK_DECISION" in packet["reason_codes"]
    assert "risk_decision_ledger" in packet["missing_artifact_summary"]


def test_kill_switch_blocks_canary() -> None:
    packet = _bundle(config_overrides={"kill_switch_enabled": True})["packet"]

    assert packet["canary_status"] == CANARY_STATUS_BLOCKED
    assert "KILL_SWITCH_ENABLED" in packet["reason_codes"]
    assert "RISK_DECISION_NOT_ALLOWED" in packet["reason_codes"]


def test_missing_wallet_boundary_packet_blocks_canary() -> None:
    packet = _bundle(include_wallet=False)["packet"]

    assert packet["canary_status"] == CANARY_STATUS_BLOCKED
    assert "MISSING_WALLET_BOUNDARY_PACKET" in packet["reason_codes"]
    assert "wallet_boundary_packet" in packet["missing_artifact_summary"]


def test_missing_signing_simulator_receipt_blocks_canary() -> None:
    packet = _bundle(include_signing=False)["packet"]

    assert packet["canary_status"] == CANARY_STATUS_BLOCKED
    assert "MISSING_SIGNING_SIMULATOR_RECEIPT" in packet["reason_codes"]
    assert "signing_simulator_receipt" in packet["missing_artifact_summary"]


def test_missing_operator_approval_results_in_needs_operator_approval() -> None:
    packet = _bundle(include_approval=False)["packet"]

    assert packet["canary_status"] == CANARY_STATUS_NEEDS_OPERATOR_APPROVAL
    assert "OPERATOR_APPROVAL_NOT_REQUESTED" in packet["reason_codes"]
    assert "DRY_RUN_OPERATOR_APPROVAL_REQUIRED" in packet["reason_codes"]
    assert "operator_approval_record" in packet["missing_artifact_summary"]


def test_dry_run_only_approval_allows_readiness_but_not_live_execution() -> None:
    bundle = _bundle(approval_status=APPROVAL_DRY_RUN_ONLY)
    packet = bundle["packet"]
    receipt = bundle["canary_receipt"]

    assert packet["canary_status"] == CANARY_STATUS_DRY_RUN_READY
    assert receipt["acceptance_status"] == DRY_RUN_ACCEPTANCE_ACCEPTED
    assert packet["live_execution_allowed"] is False
    assert packet["live_execution_performed"] is False
    assert receipt["live_execution_allowed"] is False
    assert receipt["live_execution_performed"] is False
    with pytest.raises(CanaryReadinessValidationError):
        build_canary_operator_approval_record(
            run_id="canary-readiness-test-run",
            market_id="market-1",
            approval_status="approved_for_live_execution",
        )


def test_forbidden_field_scanner_rejects_unsafe_packets() -> None:
    packet = deepcopy(_bundle()["packet"])
    packet["signed_order"] = {"id": "forbidden"}
    packet["nested"] = {"private_key": "forbidden", "auth_token": "forbidden"}

    paths = scan_forbidden_fields(packet)
    valid, errors = validate_canary_readiness_packet(packet)
    receipt = build_canary_dry_run_acceptance_receipt(packet)

    assert "$.signed_order" in paths
    assert "$.nested.private_key" in paths
    assert "$.nested.auth_token" in paths
    assert valid is False
    assert any("forbidden canary field" in error for error in errors)
    assert receipt["acceptance_status"] == DRY_RUN_ACCEPTANCE_BLOCKED
    assert "FORBIDDEN_CANARY_FIELD_PRESENT" in receipt["reason_codes"]


def test_idempotency_and_replay_behavior(tmp_path: Path) -> None:
    first = _bundle()
    second = _bundle()
    first_packet = first["packet"]
    second_packet = second["packet"]
    first_receipt = first["canary_receipt"]
    second_receipt = second["canary_receipt"]

    assert first_packet == second_packet
    assert first_receipt == second_receipt
    assert first_packet["canary_id"] == second_packet["canary_id"]
    assert first_receipt["receipt_id"] == second_receipt["receipt_id"]
    assert first_packet["canary_status"] == second_packet["canary_status"]

    paths = {
        "out_packet_json_path": tmp_path / "packet.json",
        "out_packet_md_path": tmp_path / "packet.md",
        "out_receipt_json_path": tmp_path / "receipt.json",
        "out_receipt_md_path": tmp_path / "receipt.md",
        "out_operator_approval_json_path": tmp_path / "approval.json",
        "out_operator_approval_md_path": tmp_path / "approval.md",
    }
    write_canary_readiness_artifacts(
        packet=first_packet,
        receipt=first_receipt,
        operator_approval_record=first["approval"],
        **paths,
    )
    packet_text = paths["out_packet_json_path"].read_text(encoding="utf-8")
    receipt_text = paths["out_receipt_json_path"].read_text(encoding="utf-8")
    write_canary_readiness_artifacts(
        packet=second_packet,
        receipt=second_receipt,
        operator_approval_record=second["approval"],
        **paths,
    )

    assert paths["out_packet_json_path"].read_text(encoding="utf-8") == packet_text
    assert paths["out_receipt_json_path"].read_text(encoding="utf-8") == receipt_text


def test_dashboard_and_report_surface_canary_readiness_smoke(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))

    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    packet = json.loads((tmp_path / "live_canary_readiness_packet.json").read_text(encoding="utf-8"))
    receipt = json.loads((tmp_path / "live_canary_dry_run_acceptance_receipt.json").read_text(encoding="utf-8"))
    dashboard_md = (tmp_path / "paper_daily_dashboard.md").read_text(encoding="utf-8")

    assert result.canary_readiness_packet_path.endswith("live_canary_readiness_packet.json")
    assert dashboard["live_canary_readiness_summary"]["canary_readiness_status"] == packet["canary_status"]
    assert dashboard["live_canary_readiness_summary"]["blocked_reason_summary"] == packet["blocked_reason_summary"]
    assert dashboard["live_canary_readiness_summary"]["operator_approval_status"] == packet["operator_approval_status"]
    assert dashboard["live_canary_readiness_summary"]["risk_decision_status"] == packet["risk_decision_status"]
    assert dashboard["live_canary_readiness_summary"]["wallet_boundary_status"] == packet["wallet_boundary_status"]
    assert (
        dashboard["live_canary_readiness_summary"]["signing_simulator_receipt_status"]
        == packet["signing_simulator_receipt_status"]
    )
    assert dashboard["live_canary_readiness_summary"]["dry_run_acceptance_status"] == receipt["acceptance_status"]
    assert "Live Canary Readiness" in dashboard_md


def test_live_canary_readiness_uses_no_real_wallet_signing_order_or_auth_endpoint_code() -> None:
    source = Path("pm_bot/trading_core/live_canary_readiness.py").read_text(encoding="utf-8").lower()
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
        "polymarket",
    )

    for marker in forbidden_runtime_markers:
        assert marker not in source

    packet = _bundle()["packet"]
    assert packet["real_wallet_used"] is False
    assert packet["private_key_used"] is False
    assert packet["real_signature_created"] is False
    assert packet["real_order_submitted"] is False
    assert packet["authenticated_endpoint_called"] is False


def test_live_canary_readiness_performs_no_external_api_calls(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    bundle = _bundle()

    assert bundle["packet"]["external_api_call_performed"] is False
    assert bundle["canary_receipt"]["external_api_call_performed"] is False
    assert bundle["packet"]["live_execution_performed"] is False
    assert bundle["canary_receipt"]["live_execution_performed"] is False


def test_live_canary_readiness_does_not_invent_outcomes_or_pnl() -> None:
    bundle = _bundle()

    assert bundle["packet"]["outcome_resolution_invented"] is False
    assert bundle["packet"]["pnl_invented"] is False
    assert bundle["canary_receipt"]["outcome_resolution_invented"] is False
    assert bundle["canary_receipt"]["pnl_invented"] is False


def test_nightly_lane_batch_example_is_fake_dry_run_only() -> None:
    plan = json.loads(
        Path("docs/ORCH_PMBOT_TRADING_MVP_029_LIVE_CANARY_READINESS_DRY_RUN_GATE_NIGHTLY_BATCH_PLAN.example.json")
        .read_text(encoding="utf-8")
    )
    validation = validate_nightly_lane_batch_plan(plan)

    assert validation["valid"] is True, validation["errors"]
    assert validation["plan"]["executor_mode"] == "fake"
    assert validation["plan"]["lane_mode"] == "plan_only"
    assert validation["plan"]["allow_real_codex_invocation"] is False
    assert validation["plan"]["tasks"][0]["executor_mode"] == "fake"

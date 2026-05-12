from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_replay_acceptance import (
    build_canary_acceptance_case_artifacts,
    build_live_connector_blocker_matrix,
)
from pm_bot.trading_core.live_connector_audit_replay import (
    REPLAY_STATUS_FAILED,
    REPLAY_STATUS_INSUFFICIENT_ARTIFACTS,
    REPLAY_STATUS_PASSED,
    build_live_connector_audit_replay,
    validate_live_connector_audit_replay,
)
from pm_bot.trading_core.operator_live_approval_packet import (
    NON_APPROVAL_STATEMENT,
    OPERATOR_REVIEW_READY,
    build_operator_live_approval_packet,
    validate_operator_live_approval_packet,
)
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    CONNECTOR_STATUS_DISABLED,
    DISABLED_CONNECTOR_RESULT_STATUS,
    DisabledRealWalletConnectorConfig,
    RealWalletConnectorDisabledAdapter,
    build_disabled_connector_passive_status,
    build_disabled_connector_request,
)
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_audit_replay_record,
    validate_secret_boundary_operator_approval_packet,
)


def _base_artifacts() -> dict[str, Any]:
    canary = build_canary_acceptance_case_artifacts("approved_for_dry_run_only")
    packet = canary["packet"]
    receipt = canary["canary_receipt"]
    config = DisabledRealWalletConnectorConfig(
        require_canary_readiness_packet_reference=True,
        require_replay_acceptance_reference=True,
    )
    request = build_disabled_connector_request(
        run_id=packet["run_id"],
        market_id=packet["market_id"],
        risk_decision_reference=packet["risk_decision_id"],
        wallet_boundary_packet_reference=packet["wallet_boundary_packet_id"],
        canary_readiness_packet_reference=packet["canary_id"],
        replay_acceptance_reference=receipt["receipt_id"],
    )
    adapter = RealWalletConnectorDisabledAdapter(config)
    result = adapter.build_blocked_result(request)
    audit = adapter.build_audit_record(request)
    blocker_matrix = build_live_connector_blocker_matrix()
    replay = build_live_connector_audit_replay(
        disabled_connector_audit_records=[audit],
        canary_readiness_packet_references=[packet["canary_id"]],
        canary_replay_acceptance_references=[receipt["receipt_id"]],
        wallet_boundary_packet_references=[packet["wallet_boundary_packet_id"]],
        risk_decision_references=[packet["risk_decision_id"]],
        secret_boundary_validation_summaries=[
            audit["audit_secret_boundary_validation"],
            result["validation"]["request_secret_boundary_validation"],
            result["validation"]["config_secret_boundary_validation"],
        ],
        dry_run_receipt_references=[receipt["receipt_id"]],
        live_connector_blocker_matrix=blocker_matrix,
    )
    operator_packet = build_operator_live_approval_packet(
        audit_replay_result=replay,
        disabled_connector_status=build_disabled_connector_passive_status(result=result),
        blocker_matrix=blocker_matrix,
    )
    return {
        "packet": packet,
        "receipt": receipt,
        "request": request.to_dict(),
        "result": result,
        "audit": audit,
        "blocker_matrix": blocker_matrix,
        "replay": replay,
        "operator_packet": operator_packet,
    }


def test_audit_replay_is_deterministic_and_idempotent() -> None:
    artifacts = _base_artifacts()

    first = artifacts["replay"]
    second = build_live_connector_audit_replay(
        disabled_connector_audit_records=[deepcopy(artifacts["audit"])],
        canary_readiness_packet_references=[artifacts["packet"]["canary_id"]],
        canary_replay_acceptance_references=[artifacts["receipt"]["receipt_id"]],
        wallet_boundary_packet_references=[artifacts["packet"]["wallet_boundary_packet_id"]],
        risk_decision_references=[artifacts["packet"]["risk_decision_id"]],
        secret_boundary_validation_summaries=[
            artifacts["audit"]["audit_secret_boundary_validation"],
            artifacts["result"]["validation"]["request_secret_boundary_validation"],
            artifacts["result"]["validation"]["config_secret_boundary_validation"],
        ],
        dry_run_receipt_references=[artifacts["receipt"]["receipt_id"]],
        live_connector_blocker_matrix=artifacts["blocker_matrix"],
    )

    assert first == second
    assert first["status"] == REPLAY_STATUS_PASSED
    assert first["deterministic"] is True
    assert first["real_execution_available"] is False
    assert first["live_execution_approved"] is False
    assert validate_live_connector_audit_replay(first)["valid"] is True


def test_replay_detects_mismatched_disabled_connector_records() -> None:
    artifacts = _base_artifacts()
    mutated_audit = deepcopy(artifacts["audit"])
    mutated_audit["result_id"] = "tampered-result-id"

    replay = build_live_connector_audit_replay(
        disabled_connector_audit_records=[mutated_audit],
        canary_readiness_packet_references=[artifacts["packet"]["canary_id"]],
        canary_replay_acceptance_references=[artifacts["receipt"]["receipt_id"]],
        wallet_boundary_packet_references=[artifacts["packet"]["wallet_boundary_packet_id"]],
        risk_decision_references=[artifacts["packet"]["risk_decision_id"]],
        secret_boundary_validation_summaries=[artifacts["audit"]["audit_secret_boundary_validation"]],
        dry_run_receipt_references=[artifacts["receipt"]["receipt_id"]],
        live_connector_blocker_matrix=artifacts["blocker_matrix"],
    )

    assert replay["status"] == REPLAY_STATUS_FAILED
    assert replay["mismatch_count"] == 1
    assert replay["mismatches"][0]["field_path"] == "$.result_id"


def test_replay_blocks_when_required_artifacts_are_missing_and_does_not_require_secrets() -> None:
    missing = build_live_connector_audit_replay()
    artifacts = _base_artifacts()

    assert missing["status"] == REPLAY_STATUS_INSUFFICIENT_ARTIFACTS
    assert "disabled_connector_audit_records" in missing["missing_artifacts"]
    assert artifacts["replay"]["secret_boundary_validation_summary"]["valid"] is True
    assert artifacts["replay"]["environment_inspected"] is False
    assert artifacts["replay"]["environment_secrets_read"] is False
    assert artifacts["replay"]["secrets_read"] is False
    assert artifacts["replay"]["secrets_printed"] is False
    assert artifacts["replay"]["secrets_persisted"] is False


def test_operator_packet_can_be_review_ready_without_live_execution_approval() -> None:
    packet = _base_artifacts()["operator_packet"]
    validation = validate_operator_live_approval_packet(packet)

    assert validation["validation"]["valid"] is True
    assert packet["operator_packet_status"] == OPERATOR_REVIEW_READY
    assert packet["operator_review_ready"] is True
    assert packet["live_execution_approved"] is False
    assert packet["real_execution_available"] is False
    assert packet["live_connector_enabled"] is False
    assert packet["operator_review_is_not_live_approval"] is True
    assert packet["non_approval_statement"] == NON_APPROVAL_STATEMENT


def test_operator_packet_validates_unresolved_blockers_and_includes_required_checklist() -> None:
    artifacts = _base_artifacts()
    packet = artifacts["operator_packet"]
    blocker_matrix = artifacts["blocker_matrix"]

    assert blocker_matrix["resolved_blocker_count"] == 0
    assert blocker_matrix["all_blockers_unresolved"] is True
    assert packet["blocker_matrix_summary"]["all_live_connector_blockers_unresolved"] is True
    assert set(packet["unresolved_blocker_ids"]) == set(blocker_matrix["unresolved_blockers"])
    assert packet["required_human_checklist"]
    assert all(item["live_execution_approved"] is False for item in packet["required_human_checklist"])


def test_secret_boundary_rejects_forbidden_fields_in_replay_and_operator_payloads() -> None:
    replay_validation = validate_secret_boundary_audit_replay_record({"private_key": "<redacted>"})
    packet_validation = validate_secret_boundary_operator_approval_packet({"api_key": "<redacted>"})

    assert replay_validation["valid"] is False
    assert "$.private_key" in replay_validation["forbidden_secret_field_paths"]
    assert packet_validation["valid"] is False
    assert "$.api_key" in packet_validation["forbidden_secret_field_paths"]


def test_dashboard_surfaces_audit_replay_and_operator_packet_status_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    audit_replay = json.loads((tmp_path / "live_connector_audit_replay.json").read_text(encoding="utf-8"))
    operator_packet = json.loads((tmp_path / "operator_live_approval_packet.json").read_text(encoding="utf-8"))

    summary = dashboard["live_connector_audit_operator_summary"]
    assert result.validation_passed is True
    assert result.simulated_fill_count == 2
    assert summary["audit_replay_status"] == REPLAY_STATUS_PASSED
    assert summary["operator_packet_status"] == OPERATOR_REVIEW_READY
    assert summary["operator_review_ready"] is True
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False
    assert summary["unresolved_live_blocker_count"] >= 10
    assert summary["disabled_connector_status"] == CONNECTOR_STATUS_DISABLED
    assert summary["secret_boundary_status"] == "passed"
    assert summary["latest_operator_packet_path"].endswith("operator_live_approval_packet.json")
    assert summary["latest_audit_replay_path"].endswith("live_connector_audit_replay.json")
    assert audit_replay["real_execution_available"] is False
    assert operator_packet["live_execution_approved"] is False


def test_strategy_evaluation_surfaces_passive_status_only(tmp_path: Path) -> None:
    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    strategy = json.loads((tmp_path / "paper_strategy_evaluation_ledger.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "paper_strategy_evaluation_summary.json").read_text(encoding="utf-8"))

    assert strategy["live_connector_audit_replay_status"] == REPLAY_STATUS_PASSED
    assert strategy["operator_review_packet_status"] == OPERATOR_REVIEW_READY
    assert strategy["live_execution_approved"] is False
    assert strategy["real_execution_available"] is False
    assert summary["live_connector_audit_replay_status"] == REPLAY_STATUS_PASSED
    assert summary["operator_review_packet_status"] == OPERATOR_REVIEW_READY
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False


def test_disabled_connector_still_refuses_execution_after_integration() -> None:
    artifacts = _base_artifacts()

    assert artifacts["result"]["connector_status"] == CONNECTOR_STATUS_DISABLED
    assert artifacts["result"]["status"] == DISABLED_CONNECTOR_RESULT_STATUS
    assert artifacts["result"]["execution_refused"] is True
    assert artifacts["result"]["real_execution_available"] is False
    assert artifacts["result"]["live_execution_allowed"] is False
    assert artifacts["result"]["real_order_placement_performed"] is False
    assert artifacts["result"]["cryptographic_signing_performed"] is False


def test_all_critical_live_blockers_remain_unresolved() -> None:
    matrix = build_live_connector_blocker_matrix()

    assert matrix["status"] == "passed"
    assert matrix["live_execution_available"] is False
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["critical_blocker_count"] == matrix["unresolved_blocker_count"]
    assert all(row["resolution_status"] == "unresolved" for row in matrix["blockers"])


def test_no_real_signing_order_auth_endpoint_fields_appear_in_allowed_outputs() -> None:
    artifacts = _base_artifacts()
    active_forbidden_keys = {
        "private_key",
        "mnemonic",
        "seed_phrase",
        "signature",
        "signed_order",
        "raw_transaction",
        "auth_header",
        "bearer_token",
        "api_key",
        "submit_order",
        "place_order",
        "send_transaction",
        "order_payload",
        "authenticated_endpoint_url",
    }

    replay_keys = {key for _path, key, _value in _walk(artifacts["replay"])}
    packet_keys = {key for _path, key, _value in _walk(artifacts["operator_packet"])}

    assert active_forbidden_keys.isdisjoint(replay_keys)
    assert active_forbidden_keys.isdisjoint(packet_keys)
    assert artifacts["replay"]["real_execution_available"] is False
    assert artifacts["operator_packet"]["live_execution_approved"] is False


def test_operator_packet_idempotency_same_inputs_produce_same_packet() -> None:
    artifacts = _base_artifacts()

    first = artifacts["operator_packet"]
    second = build_operator_live_approval_packet(
        audit_replay_result=deepcopy(artifacts["replay"]),
        disabled_connector_status=build_disabled_connector_passive_status(result=deepcopy(artifacts["result"])),
        blocker_matrix=deepcopy(artifacts["blocker_matrix"]),
    )

    assert first == second


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

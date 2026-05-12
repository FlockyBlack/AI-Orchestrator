from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_operator_intent_packet import (
    INTENT_PACKET_STATUS_REVIEW_READY,
    NON_EXECUTION_STATEMENTS,
    VALIDATION_STATUS_DRY_RUN_VALID,
    build_live_canary_operator_intent_packet,
    validate_live_canary_operator_intent_packet,
)
from pm_bot.trading_core.live_canary_replay_acceptance import (
    build_canary_acceptance_case_artifacts,
    build_live_connector_blocker_matrix,
)
from pm_bot.trading_core.live_connector_audit_replay import (
    REPLAY_STATUS_PASSED,
    build_live_connector_audit_replay,
)
from pm_bot.trading_core.operator_live_approval_packet import (
    OPERATOR_REVIEW_READY,
    build_operator_live_approval_packet,
)
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    CONNECTOR_STATUS_DISABLED,
    DisabledRealWalletConnectorConfig,
    RealWalletConnectorDisabledAdapter,
    build_disabled_connector_passive_status,
    build_disabled_connector_request,
)
from pm_bot.trading_core.secret_boundary_policy import validate_secret_boundary_operator_intent_packet
from pm_bot.trading_core.tiny_live_canary_manual_runbook import build_tiny_live_canary_manual_runbook
from pm_bot.trading_core.tiny_live_canary_preflight_contract import (
    PREFLIGHT_STATUS_READY,
    build_tiny_live_canary_kill_switch_validation,
    build_tiny_live_canary_preflight_contract,
    evaluate_tiny_live_canary_preflight,
)


def _base_artifacts() -> dict[str, Any]:
    canary = build_canary_acceptance_case_artifacts("approved_for_dry_run_only")
    packet = canary["packet"]
    receipt = canary["canary_receipt"]
    contract = build_tiny_live_canary_preflight_contract()
    runbook = build_tiny_live_canary_manual_runbook()
    kill_switch_validation = build_tiny_live_canary_kill_switch_validation(contract["kill_switch_requirement"])
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
    disabled_result = adapter.build_blocked_result(request)
    disabled_audit = adapter.build_audit_record(request)
    blocker_matrix = build_live_connector_blocker_matrix()
    audit_replay = build_live_connector_audit_replay(
        disabled_connector_audit_records=[disabled_audit],
        canary_readiness_packet_references=[packet["canary_id"]],
        canary_replay_acceptance_references=[receipt["receipt_id"]],
        wallet_boundary_packet_references=[packet["wallet_boundary_packet_id"]],
        risk_decision_references=[packet["risk_decision_id"]],
        secret_boundary_validation_summaries=[
            disabled_audit["audit_secret_boundary_validation"],
            disabled_result["validation"]["request_secret_boundary_validation"],
            disabled_result["validation"]["config_secret_boundary_validation"],
        ],
        dry_run_receipt_references=[receipt["receipt_id"]],
        tiny_live_canary_preflight_contract_references=[contract["contract_id"]],
        tiny_live_canary_manual_runbook_references=[runbook["runbook_id"]],
        operator_intent_packet_references=["pm_bot/trading_core/artifacts/night_020_021/live_canary_operator_intent_packet.json"],
        live_connector_blocker_matrix=blocker_matrix,
    )
    initial_operator_packet = build_operator_live_approval_packet(
        audit_replay_result=audit_replay,
        disabled_connector_status=build_disabled_connector_passive_status(result=disabled_result),
        blocker_matrix=blocker_matrix,
        tiny_live_canary_preflight_contract=contract,
        tiny_live_canary_manual_runbook=runbook,
    )
    intent_packet = build_live_canary_operator_intent_packet(
        tiny_live_canary_preflight_contract=contract,
        tiny_live_canary_manual_runbook=runbook,
        operator_approval_packet=initial_operator_packet,
        operator_approval_packet_reference="operator_live_review_packet:current-run",
        live_connector_audit_replay=audit_replay,
        disabled_connector_audit=disabled_audit,
        secret_boundary_validation=audit_replay["secret_boundary_validation_summary"],
        blocker_matrix=blocker_matrix,
        risk_review_reference=packet["risk_decision_id"],
    )
    operator_packet = build_operator_live_approval_packet(
        audit_replay_result=audit_replay,
        disabled_connector_status=build_disabled_connector_passive_status(result=disabled_result),
        blocker_matrix=blocker_matrix,
        tiny_live_canary_preflight_contract=contract,
        tiny_live_canary_manual_runbook=runbook,
        operator_intent_packet=intent_packet,
        latest_operator_intent_packet_path="pm_bot/trading_core/artifacts/night_020_021/live_canary_operator_intent_packet.json",
    )
    preflight = evaluate_tiny_live_canary_preflight(
        contract=contract,
        manual_runbook=runbook,
        operator_packet=operator_packet,
        operator_intent_packet=intent_packet,
        audit_replay_result=audit_replay,
        secret_boundary_validation=audit_replay["secret_boundary_validation_summary"],
        blocker_matrix=blocker_matrix,
        kill_switch_validation=kill_switch_validation,
    )
    return {
        "packet": packet,
        "receipt": receipt,
        "contract": contract,
        "runbook": runbook,
        "kill_switch_validation": kill_switch_validation,
        "disabled_result": disabled_result,
        "disabled_audit": disabled_audit,
        "blocker_matrix": blocker_matrix,
        "audit_replay": audit_replay,
        "operator_packet": operator_packet,
        "intent_packet": intent_packet,
        "preflight": preflight,
    }


def test_intent_packet_builds_deterministically_and_validates_for_dry_run_review() -> None:
    artifacts = _base_artifacts()
    first = artifacts["intent_packet"]
    second = build_live_canary_operator_intent_packet(
        tiny_live_canary_preflight_contract=deepcopy(artifacts["contract"]),
        tiny_live_canary_manual_runbook=deepcopy(artifacts["runbook"]),
        operator_approval_packet=deepcopy(artifacts["operator_packet"]),
        operator_approval_packet_reference="operator_live_review_packet:current-run",
        live_connector_audit_replay=deepcopy(artifacts["audit_replay"]),
        disabled_connector_audit=deepcopy(artifacts["disabled_audit"]),
        secret_boundary_validation=deepcopy(artifacts["audit_replay"]["secret_boundary_validation_summary"]),
        blocker_matrix=deepcopy(artifacts["blocker_matrix"]),
        risk_review_reference=artifacts["packet"]["risk_decision_id"],
    )

    assert first == second
    assert first["intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert first["validation"]["status"] == VALIDATION_STATUS_DRY_RUN_VALID
    assert first["validation"]["valid"] is True
    assert first["operator_intent_packet_ready"] is True
    assert first["operator_acknowledgement_model_ready"] is True
    assert first["dry_run_intent_validation_ready"] is True


@pytest.mark.parametrize(
    "field",
    [
        "tiny_live_canary_preflight_contract_reference",
        "manual_runbook_reference",
        "operator_approval_packet_reference",
        "live_connector_audit_replay_reference",
        "disabled_connector_audit_reference",
        "secret_boundary_validation_reference",
        "blocker_matrix_reference",
        "risk_review_reference",
    ],
)
def test_intent_packet_requires_required_artifact_references(field: str) -> None:
    packet = deepcopy(_base_artifacts()["intent_packet"])
    packet[field] = ""
    validation = validate_live_canary_operator_intent_packet(packet)

    assert validation["valid"] is False
    assert "missing_required_artifacts" in validation["statuses"]
    assert field in validation["missing_required_artifacts"]
    assert validation["live_execution_approved"] is False
    assert validation["canary_executable_now"] is False
    assert validation["real_execution_available"] is False


def test_intent_packet_requires_unresolved_blocker_acknowledgement_and_non_execution_statement() -> None:
    packet = deepcopy(_base_artifacts()["intent_packet"])
    packet["acknowledged_unresolved_blocker_ids"] = []
    packet["unresolved_blocker_ids"] = []
    packet["unresolved_blockers_acknowledged"] = False
    validation = validate_live_canary_operator_intent_packet(packet)

    assert validation["valid"] is False
    assert "unresolved_blockers_not_acknowledged" in validation["statuses"]

    packet = deepcopy(_base_artifacts()["intent_packet"])
    packet["non_execution_statements"] = list(NON_EXECUTION_STATEMENTS[:-1])
    validation = validate_live_canary_operator_intent_packet(packet)

    assert validation["valid"] is False
    assert "missing_operator_acknowledgement" in validation["statuses"]


def test_intent_packet_validation_passes_only_for_dry_run_review_and_keeps_live_flags_false() -> None:
    packet = _base_artifacts()["intent_packet"]
    validation = validate_live_canary_operator_intent_packet(packet)

    assert validation["valid"] is True
    assert validation["status"] == VALIDATION_STATUS_DRY_RUN_VALID
    assert packet["live_execution_approved"] is False
    assert packet["canary_executable_now"] is False
    assert packet["real_execution_available"] is False
    assert packet["live_connector_enabled"] is False
    assert packet["operator_intent_is_not_live_approval"] is True


def test_human_context_operator_signed_terminology_is_allowed_only_when_non_cryptographic() -> None:
    packet = deepcopy(_base_artifacts()["intent_packet"])
    validation = validate_secret_boundary_operator_intent_packet(packet)

    assert validation["valid"] is True
    assert packet["operator_signed_intent_acknowledgement"] is True
    assert packet["operator_signed_intent_is_human_acknowledgement_only"] is True
    assert "human acknowledgement only" in packet["human_signed_acknowledgement_text"].lower()

    unsafe = deepcopy(packet)
    unsafe["operator_signed_intent_is_human_acknowledgement_only"] = False
    unsafe["human_signed_acknowledgement_text"] = "signed"
    validation = validate_live_canary_operator_intent_packet(unsafe)

    assert validation["valid"] is False
    assert "forbidden_signing_field_detected" in validation["statuses"]


@pytest.mark.parametrize(
    "field",
    [
        "signature",
        "signed_order",
        "signed_payload",
        "raw_transaction",
        "private_key",
        "mnemonic",
        "seed_phrase",
        "api_key",
        "auth_header",
        "bearer_token",
        "order_submission_payload",
        "transaction_payload",
    ],
)
def test_cryptographic_secret_order_and_auth_fields_are_rejected(field: str) -> None:
    packet = deepcopy(_base_artifacts()["intent_packet"])
    packet[field] = "<redacted>"
    validation = validate_live_canary_operator_intent_packet(packet)

    assert validation["valid"] is False
    assert "forbidden_signing_field_detected" in validation["statuses"]
    assert f"$.{field}" in validation["forbidden_field_paths"]


def test_operator_approval_packet_remains_review_only_with_intent_status() -> None:
    packet = _base_artifacts()["operator_packet"]

    assert packet["operator_packet_status"] == OPERATOR_REVIEW_READY
    assert packet["operator_review_ready"] is True
    assert packet["operator_intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert packet["operator_intent_packet_review_ready"] is True
    assert packet["operator_intent_is_not_live_approval"] is True
    assert packet["live_execution_approved"] is False
    assert packet["real_execution_available"] is False
    assert packet["live_connector_enabled"] is False
    assert packet["canary_executable_now"] is False


def test_tiny_canary_preflight_and_audit_replay_remain_non_executable_with_intent_reference() -> None:
    artifacts = _base_artifacts()
    preflight = artifacts["preflight"]
    replay = artifacts["audit_replay"]

    assert preflight["status"] == PREFLIGHT_STATUS_READY
    assert preflight["operator_intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert preflight["operator_intent_packet_review_ready"] is True
    assert preflight["canary_executable_now"] is False
    assert preflight["live_execution_approved"] is False
    assert preflight["real_execution_available"] is False
    assert replay["status"] == REPLAY_STATUS_PASSED
    assert replay["operator_intent_packet_status"] == "referenced"
    assert replay["real_execution_available"] is False
    assert replay["live_execution_approved"] is False
    assert replay["live_connector_enabled"] is False
    assert replay["external_api_calls_performed"] is False


def test_dashboard_surfaces_operator_intent_status_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    intent_packet = json.loads((tmp_path / "live_canary_operator_intent_packet.json").read_text(encoding="utf-8"))
    summary = dashboard["operator_intent_packet_summary"]

    assert result.validation_passed is True
    assert result.operator_intent_packet_path.endswith("live_canary_operator_intent_packet.json")
    assert summary["operator_intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert summary["operator_intent_packet_review_ready"] is True
    assert summary["operator_intent_is_not_live_approval"] is True
    assert summary["canary_executable_now"] is False
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False
    assert summary["kill_switch_verified_for_live"] is False
    assert summary["unresolved_live_blocker_count"] >= 24
    assert intent_packet["operator_signed_intent_is_human_acknowledgement_only"] is True


def test_strategy_evaluation_surfaces_passive_operator_intent_status_only(tmp_path: Path) -> None:
    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    strategy = json.loads((tmp_path / "paper_strategy_evaluation_ledger.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "paper_strategy_evaluation_summary.json").read_text(encoding="utf-8"))

    assert strategy["operator_intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert strategy["operator_intent_packet_review_ready"] is True
    assert strategy["operator_intent_is_not_live_approval"] is True
    assert strategy["canary_executable_now"] is False
    assert strategy["live_execution_approved"] is False
    assert strategy["real_execution_available"] is False
    assert summary["operator_intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert summary["operator_intent_packet_review_ready"] is True
    assert summary["operator_intent_is_not_live_approval"] is True
    assert summary["canary_executable_now"] is False
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False


def test_blocker_matrix_keeps_critical_live_blockers_unresolved_and_adds_intent_categories() -> None:
    matrix = build_live_connector_blocker_matrix()
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert {
        "operator_intent_packet_dry_run_only",
        "operator_intent_not_live_approval",
        "operator_intent_acknowledgement_not_collected_for_live",
        "cryptographic_signing_still_unavailable",
        "live_canary_execution_still_disabled",
        "live_canary_funding_still_not_configured",
        "live_canary_order_adapter_still_disabled",
    }.issubset(categories)
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["critical_blocker_count"] == matrix["unresolved_blocker_count"]
    assert matrix["live_execution_available"] is False
    assert all(row["resolution_status"] == "unresolved" for row in matrix["blockers"])


def test_no_forbidden_active_fields_appear_in_allowed_outputs() -> None:
    artifacts = _base_artifacts()
    active_forbidden_keys = {
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
        "order_submission_payload",
        "transaction_payload",
        "order_payload",
    }
    keys = set()
    for artifact in (
        artifacts["intent_packet"],
        artifacts["operator_packet"],
        artifacts["preflight"],
        artifacts["audit_replay"],
    ):
        keys.update(key for _path, key, _value in _walk(artifact))

    assert active_forbidden_keys.isdisjoint(keys)
    assert artifacts["intent_packet"]["live_execution_approved"] is False
    assert artifacts["disabled_result"]["connector_status"] == CONNECTOR_STATUS_DISABLED
    assert artifacts["disabled_result"]["real_execution_available"] is False


def test_same_inputs_produce_same_packet_and_validation_result() -> None:
    artifacts = _base_artifacts()
    first = artifacts["intent_packet"]
    second = build_live_canary_operator_intent_packet(
        tiny_live_canary_preflight_contract=deepcopy(artifacts["contract"]),
        tiny_live_canary_manual_runbook=deepcopy(artifacts["runbook"]),
        operator_approval_packet=deepcopy(artifacts["operator_packet"]),
        operator_approval_packet_reference="operator_live_review_packet:current-run",
        live_connector_audit_replay=deepcopy(artifacts["audit_replay"]),
        disabled_connector_audit=deepcopy(artifacts["disabled_audit"]),
        secret_boundary_validation=deepcopy(artifacts["audit_replay"]["secret_boundary_validation_summary"]),
        blocker_matrix=deepcopy(artifacts["blocker_matrix"]),
        risk_review_reference=artifacts["packet"]["risk_decision_id"],
    )

    assert first == second
    assert validate_live_canary_operator_intent_packet(first) == validate_live_canary_operator_intent_packet(second)


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

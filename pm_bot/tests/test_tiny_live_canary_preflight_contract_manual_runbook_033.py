from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
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
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_tiny_canary_evidence_requirement_packet,
    validate_secret_boundary_tiny_canary_kill_switch_requirement_packet,
    validate_secret_boundary_tiny_canary_manual_runbook,
    validate_secret_boundary_tiny_canary_preflight_contract,
)
from pm_bot.trading_core.tiny_live_canary_manual_runbook import (
    NON_EXECUTION_STATEMENT,
    build_tiny_live_canary_manual_runbook,
    validate_tiny_live_canary_manual_runbook,
)
from pm_bot.trading_core.tiny_live_canary_preflight_contract import (
    PREFLIGHT_STATUS_READY,
    build_tiny_live_canary_kill_switch_validation,
    build_tiny_live_canary_preflight_contract,
    evaluate_tiny_live_canary_preflight,
    validate_tiny_live_canary_preflight_contract,
)


def _base_artifacts() -> dict[str, Any]:
    canary = build_canary_acceptance_case_artifacts("approved_for_dry_run_only")
    packet = canary["packet"]
    receipt = canary["canary_receipt"]
    contract = build_tiny_live_canary_preflight_contract()
    runbook = build_tiny_live_canary_manual_runbook()
    kill_switch_validation = build_tiny_live_canary_kill_switch_validation(
        contract["kill_switch_requirement"]
    )
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
        live_connector_blocker_matrix=blocker_matrix,
    )
    operator_packet = build_operator_live_approval_packet(
        audit_replay_result=audit_replay,
        disabled_connector_status=build_disabled_connector_passive_status(result=disabled_result),
        blocker_matrix=blocker_matrix,
        tiny_live_canary_preflight_contract=contract,
        tiny_live_canary_manual_runbook=runbook,
    )
    preflight = evaluate_tiny_live_canary_preflight(
        contract=contract,
        manual_runbook=runbook,
        operator_packet=operator_packet,
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
        "preflight": preflight,
    }


def test_preflight_contract_builds_deterministically_and_validates_required_artifacts() -> None:
    first = build_tiny_live_canary_preflight_contract()
    second = build_tiny_live_canary_preflight_contract()
    validation = validate_tiny_live_canary_preflight_contract(first)
    limit_policy = first["limit_policy"]
    requirement_keys = {row["artifact_key"] for row in first["evidence_requirements"]}

    assert first == second
    assert validation["valid"] is True
    assert first["preflight_contract_ready"] is True
    assert first["future_tiny_canary_defined"] is True
    assert limit_policy["max_market_count"] == 1
    assert limit_policy["max_order_count"] == 1
    assert limit_policy["allowed_market_status"] == "review_only"
    assert {
        "operator_review_packet",
        "disabled_connector_audit_replay",
        "secret_boundary_validation",
        "live_connector_blocker_matrix",
        "manual_runbook_acknowledgement",
        "kill_switch_requirement_packet",
        "evidence_capture_packet",
    }.issubset(requirement_keys)
    assert first["live_execution_approved"] is False
    assert first["real_execution_available"] is False
    assert first["canary_executable_now"] is False


def test_missing_required_preflight_inputs_block_readiness_without_enabling_execution() -> None:
    artifacts = _base_artifacts()

    cases = {
        "missing_operator_packet": {"operator_packet": None, "category": "live_canary_manual_approval_not_collected"},
        "missing_audit_replay": {
            "audit_replay_result": None,
            "category": "tiny_live_canary_preflight_contract_review_only",
        },
        "missing_secret_boundary_validation": {
            "secret_boundary_validation": None,
            "category": "secret_boundary_validation_missing",
        },
        "missing_kill_switch_validation": {
            "kill_switch_validation": None,
            "category": "kill_switch_not_live_verified",
        },
    }
    for overrides in cases.values():
        result = evaluate_tiny_live_canary_preflight(
            contract=artifacts["contract"],
            manual_runbook=artifacts["runbook"],
            operator_packet=overrides.get("operator_packet", artifacts["operator_packet"]),
            audit_replay_result=overrides.get("audit_replay_result", artifacts["audit_replay"]),
            secret_boundary_validation=overrides.get(
                "secret_boundary_validation",
                artifacts["audit_replay"]["secret_boundary_validation_summary"],
            ),
            blocker_matrix=artifacts["blocker_matrix"],
            kill_switch_validation=overrides.get("kill_switch_validation", artifacts["kill_switch_validation"]),
        )
        assert overrides["category"] in result["blocker_categories"]
        assert result["static_preflight_checks_passed"] is False
        assert result["live_execution_approved"] is False
        assert result["real_execution_available"] is False
        assert result["canary_executable_now"] is False


def test_all_static_preflight_checks_can_pass_while_live_execution_remains_false() -> None:
    result = _base_artifacts()["preflight"]

    assert result["status"] == PREFLIGHT_STATUS_READY
    assert result["static_preflight_checks_passed"] is True
    assert result["preflight_contract_ready"] is True
    assert result["manual_runbook_ready"] is True
    assert result["future_canary_shape_defined"] is True
    assert result["kill_switch_requirements_defined"] is True
    assert result["kill_switch_verified_for_live"] is False
    assert result["live_execution_approved"] is False
    assert result["real_execution_available"] is False
    assert result["canary_executable_now"] is False
    assert result["live_connector_enabled"] is False


def test_manual_runbook_includes_required_non_execution_kill_switch_abort_and_evidence_sections() -> None:
    runbook = build_tiny_live_canary_manual_runbook()
    validation = validate_tiny_live_canary_manual_runbook(runbook)
    section_ids = {row["section_id"] for row in runbook["sections"]}
    runbook_text = json.dumps(runbook, sort_keys=True).lower()

    assert validation["valid"] is True
    assert runbook["manual_runbook_ready"] is True
    assert NON_EXECUTION_STATEMENT.lower() in runbook_text
    assert "kill_switch_verification" in section_ids
    assert "manual_pause_abort_conditions" in section_ids
    assert "evidence_capture_checklist" in section_ids
    assert "final_non_authorization_statement" in section_ids
    assert runbook["live_execution_approved"] is False
    assert runbook["real_execution_available"] is False
    assert runbook["canary_executable_now"] is False


def test_operator_packet_remains_review_only_with_tiny_canary_passive_awareness() -> None:
    artifacts = _base_artifacts()
    packet = artifacts["operator_packet"]
    summary = packet["tiny_live_canary_preflight_summary"]

    assert packet["operator_packet_status"] == OPERATOR_REVIEW_READY
    assert packet["operator_review_ready"] is True
    assert packet["operator_review_is_not_live_approval"] is True
    assert packet["live_execution_approved"] is False
    assert packet["real_execution_available"] is False
    assert packet["live_connector_enabled"] is False
    assert packet["canary_executable_now"] is False
    assert summary["preflight_contract_ready"] is True
    assert summary["manual_runbook_ready"] is True
    assert summary["future_canary_shape_defined"] is True
    assert summary["kill_switch_verified_for_live"] is False
    assert summary["canary_executable_now"] is False


def test_audit_replay_remains_non_executable_with_preflight_runbook_references() -> None:
    replay = _base_artifacts()["audit_replay"]
    refs = replay["artifact_references"]

    assert replay["status"] == REPLAY_STATUS_PASSED
    assert replay["tiny_live_canary_preflight_status"] == "referenced"
    assert replay["manual_runbook_status"] == "referenced"
    assert refs["tiny_live_canary_preflight_contract_references"]
    assert refs["tiny_live_canary_manual_runbook_references"]
    assert replay["real_execution_available"] is False
    assert replay["live_execution_approved"] is False
    assert replay["live_connector_enabled"] is False
    assert replay["canary_executable_now"] is False
    assert replay["external_api_calls_performed"] is False


def test_dashboard_surfaces_tiny_canary_preflight_and_runbook_status_passively(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    summary = dashboard["tiny_live_canary_preflight_runbook_summary"]

    assert result.validation_passed is True
    assert summary["tiny_live_canary_preflight_status"] == PREFLIGHT_STATUS_READY
    assert summary["manual_runbook_status"] == "manual_runbook_ready_for_future_review_only"
    assert summary["future_canary_shape_defined"] is True
    assert summary["preflight_contract_ready"] is True
    assert summary["manual_runbook_ready"] is True
    assert summary["canary_executable_now"] is False
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False
    assert summary["kill_switch_requirements_defined"] is True
    assert summary["kill_switch_verified_for_live"] is False
    assert summary["unresolved_live_blocker_count"] >= 17
    assert summary["latest_tiny_canary_contract_path"].endswith("tiny_live_canary_preflight_contract.json")
    assert summary["latest_manual_runbook_path"].endswith("tiny_live_canary_manual_runbook.json")


def test_strategy_evaluation_surfaces_tiny_canary_passive_status_only(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    strategy = json.loads((tmp_path / "paper_strategy_evaluation_ledger.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "paper_strategy_evaluation_summary.json").read_text(encoding="utf-8"))

    assert strategy["tiny_live_canary_preflight_status"] == PREFLIGHT_STATUS_READY
    assert strategy["manual_runbook_status"] == "manual_runbook_ready_for_future_review_only"
    assert strategy["canary_executable_now"] is False
    assert strategy["live_execution_approved"] is False
    assert strategy["real_execution_available"] is False
    assert summary["tiny_live_canary_preflight_status"] == PREFLIGHT_STATUS_READY
    assert summary["manual_runbook_status"] == "manual_runbook_ready_for_future_review_only"
    assert summary["canary_executable_now"] is False
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False


def test_secret_boundary_rejects_forbidden_fields_in_preflight_runbook_and_requirement_payloads() -> None:
    preflight_validation = validate_secret_boundary_tiny_canary_preflight_contract({"private_key": "<redacted>"})
    runbook_validation = validate_secret_boundary_tiny_canary_manual_runbook({"api_key": "<redacted>"})
    kill_switch_validation = validate_secret_boundary_tiny_canary_kill_switch_requirement_packet(
        {"mnemonic": "<redacted>"}
    )
    evidence_validation = validate_secret_boundary_tiny_canary_evidence_requirement_packet(
        {"signed_order": "<redacted>"}
    )

    assert preflight_validation["valid"] is False
    assert "$.private_key" in preflight_validation["forbidden_secret_field_paths"]
    assert runbook_validation["valid"] is False
    assert "$.api_key" in runbook_validation["forbidden_secret_field_paths"]
    assert kill_switch_validation["valid"] is False
    assert "$.mnemonic" in kill_switch_validation["forbidden_secret_field_paths"]
    assert evidence_validation["valid"] is False
    assert "$.signed_order" in evidence_validation["forbidden_secret_field_paths"]


def test_blocker_matrix_keeps_tiny_canary_categories_critical_and_unresolved() -> None:
    matrix = build_live_connector_blocker_matrix()
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert {
        "tiny_live_canary_preflight_contract_review_only",
        "manual_runbook_not_operator_executed",
        "kill_switch_not_live_verified",
        "live_canary_manual_approval_not_collected",
        "live_canary_execution_adapter_disabled",
        "live_canary_funding_not_configured",
        "live_canary_market_selection_not_finalized",
    }.issubset(categories)
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["critical_blocker_count"] == matrix["unresolved_blocker_count"]
    assert matrix["live_execution_available"] is False
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

    keys = set()
    for artifact in (
        artifacts["contract"],
        artifacts["runbook"],
        artifacts["kill_switch_validation"],
        artifacts["audit_replay"],
        artifacts["operator_packet"],
        artifacts["preflight"],
    ):
        keys.update(key for _path, key, _value in _walk(artifact))

    assert active_forbidden_keys.isdisjoint(keys)
    assert artifacts["disabled_result"]["connector_status"] == CONNECTOR_STATUS_DISABLED
    assert artifacts["disabled_result"]["real_execution_available"] is False
    assert artifacts["preflight"]["canary_executable_now"] is False


def test_idempotency_same_inputs_produce_same_preflight_and_runbook_result() -> None:
    artifacts = _base_artifacts()

    runbook_again = build_tiny_live_canary_manual_runbook()
    preflight_again = evaluate_tiny_live_canary_preflight(
        contract=deepcopy(artifacts["contract"]),
        manual_runbook=deepcopy(artifacts["runbook"]),
        operator_packet=deepcopy(artifacts["operator_packet"]),
        audit_replay_result=deepcopy(artifacts["audit_replay"]),
        secret_boundary_validation=deepcopy(artifacts["audit_replay"]["secret_boundary_validation_summary"]),
        blocker_matrix=deepcopy(artifacts["blocker_matrix"]),
        kill_switch_validation=deepcopy(artifacts["kill_switch_validation"]),
    )

    assert artifacts["runbook"] == runbook_again
    assert artifacts["preflight"] == preflight_again


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

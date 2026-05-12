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
    build_live_canary_operator_intent_packet,
)
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    BUNDLE_STATUS_REVIEW_READY,
    REQUIRED_EVIDENCE_TYPES,
    VALIDATION_STATUS_AUDIT_REPLAY_EVIDENCE_MISSING,
    VALIDATION_STATUS_DISABLED_CONNECTOR_EVIDENCE_MISSING,
    VALIDATION_STATUS_DRY_RUN_VALID,
    VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL,
    VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD,
    VALIDATION_STATUS_KILL_SWITCH_EVIDENCE_MISSING,
    VALIDATION_STATUS_MANUAL_RUNBOOK_EVIDENCE_MISSING,
    VALIDATION_STATUS_OPERATOR_INTENT_EVIDENCE_MISSING,
    VALIDATION_STATUS_OPERATOR_PACKET_EVIDENCE_MISSING,
    VALIDATION_STATUS_PREFLIGHT_CONTRACT_EVIDENCE_MISSING,
    VALIDATION_STATUS_SECRET_BOUNDARY_EVIDENCE_MISSING,
    VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT,
    build_live_canary_readiness_evidence_bundle,
    build_live_canary_readiness_evidence_manifest,
    summarize_live_canary_readiness_evidence_bundle,
    validate_live_canary_readiness_evidence_bundle,
    validate_live_canary_readiness_evidence_manifest,
)
from pm_bot.trading_core.live_canary_replay_acceptance import (
    build_canary_acceptance_case_artifacts,
    build_live_connector_blocker_matrix,
)
from pm_bot.trading_core.live_connector_audit_replay import REPLAY_STATUS_PASSED, build_live_connector_audit_replay
from pm_bot.trading_core.operator_live_approval_packet import OPERATOR_REVIEW_READY, build_operator_live_approval_packet
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    CONNECTOR_STATUS_DISABLED,
    DisabledRealWalletConnectorConfig,
    RealWalletConnectorDisabledAdapter,
    build_disabled_connector_passive_status,
    build_disabled_connector_request,
)
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_readiness_evidence_bundle,
    validate_secret_boundary_readiness_evidence_item,
    validate_secret_boundary_readiness_evidence_manifest,
)
from pm_bot.trading_core.tiny_live_canary_manual_runbook import (
    MANUAL_RUNBOOK_STATUS_READY,
    build_tiny_live_canary_manual_runbook,
)
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
        operator_intent_packet_references=["live_canary_operator_intent_packet:unit-test"],
        readiness_evidence_bundle_references=["live_canary_readiness_evidence_bundle:unit-test"],
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
        operator_approval_packet_reference="operator_live_review_packet:unit-test",
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
        latest_operator_intent_packet_path="live_canary_operator_intent_packet:unit-test",
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
    bundle = build_live_canary_readiness_evidence_bundle(
        disabled_connector_status=build_disabled_connector_passive_status(result=disabled_result),
        disabled_connector_audit=disabled_audit,
        secret_boundary_validation=audit_replay["secret_boundary_validation_summary"],
        live_canary_readiness_packet=packet,
        canary_replay_acceptance={"status": "passed", "contract_version": "pmbot_live_canary_acceptance_matrix.v1"},
        live_connector_audit_replay=audit_replay,
        operator_approval_packet=operator_packet,
        tiny_live_canary_preflight_contract=contract,
        tiny_live_canary_manual_runbook=runbook,
        operator_intent_packet=intent_packet,
        blocker_matrix=blocker_matrix,
        kill_switch_validation=kill_switch_validation,
        preflight_result=preflight,
        dry_run_receipt_references=[receipt["receipt_id"]],
        result_artifact_references=["paper_daily_loop_result:unit-test"],
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
        "bundle": bundle,
    }


def test_evidence_bundle_builds_deterministically_and_validates_for_dry_run_review() -> None:
    artifacts = _base_artifacts()
    first = artifacts["bundle"]
    second = build_live_canary_readiness_evidence_bundle(
        disabled_connector_status=build_disabled_connector_passive_status(result=deepcopy(artifacts["disabled_result"])),
        disabled_connector_audit=deepcopy(artifacts["disabled_audit"]),
        secret_boundary_validation=deepcopy(artifacts["audit_replay"]["secret_boundary_validation_summary"]),
        live_canary_readiness_packet=deepcopy(artifacts["packet"]),
        canary_replay_acceptance={"status": "passed", "contract_version": "pmbot_live_canary_acceptance_matrix.v1"},
        live_connector_audit_replay=deepcopy(artifacts["audit_replay"]),
        operator_approval_packet=deepcopy(artifacts["operator_packet"]),
        tiny_live_canary_preflight_contract=deepcopy(artifacts["contract"]),
        tiny_live_canary_manual_runbook=deepcopy(artifacts["runbook"]),
        operator_intent_packet=deepcopy(artifacts["intent_packet"]),
        blocker_matrix=deepcopy(artifacts["blocker_matrix"]),
        kill_switch_validation=deepcopy(artifacts["kill_switch_validation"]),
        preflight_result=deepcopy(artifacts["preflight"]),
        dry_run_receipt_references=[artifacts["receipt"]["receipt_id"]],
        result_artifact_references=["paper_daily_loop_result:unit-test"],
    )

    assert first == second
    assert first["bundle_status"] == BUNDLE_STATUS_REVIEW_READY
    assert first["validation"]["status"] == VALIDATION_STATUS_DRY_RUN_VALID
    assert first["validation"]["valid"] is True
    assert first["readiness_evidence_bundle_ready"] is True
    assert first["evidence_bundle_review_ready"] is True
    assert first["readiness_chain_complete_for_dry_run_review"] is True
    assert first["evidence_manifest_ready"] is True
    assert {row["evidence_type"] for row in first["evidence_items"]}.issuperset(REQUIRED_EVIDENCE_TYPES)


@pytest.mark.parametrize(
    ("evidence_type", "expected_status"),
    [
        ("disabled_connector_adapter_status", VALIDATION_STATUS_DISABLED_CONNECTOR_EVIDENCE_MISSING),
        ("secret_boundary_validation_summary", VALIDATION_STATUS_SECRET_BOUNDARY_EVIDENCE_MISSING),
        ("live_connector_audit_replay", VALIDATION_STATUS_AUDIT_REPLAY_EVIDENCE_MISSING),
        ("operator_live_approval_packet", VALIDATION_STATUS_OPERATOR_PACKET_EVIDENCE_MISSING),
        ("tiny_live_canary_preflight_contract", VALIDATION_STATUS_PREFLIGHT_CONTRACT_EVIDENCE_MISSING),
        ("tiny_live_canary_manual_runbook", VALIDATION_STATUS_MANUAL_RUNBOOK_EVIDENCE_MISSING),
        ("dry_run_operator_intent_packet", VALIDATION_STATUS_OPERATOR_INTENT_EVIDENCE_MISSING),
        ("kill_switch_requirements", VALIDATION_STATUS_KILL_SWITCH_EVIDENCE_MISSING),
    ],
)
def test_evidence_bundle_requires_each_required_artifact_type(
    evidence_type: str,
    expected_status: str,
) -> None:
    bundle = deepcopy(_base_artifacts()["bundle"])
    bundle["evidence_items"] = [
        row for row in bundle["evidence_items"] if row["evidence_type"] != evidence_type
    ]
    bundle["evidence_references"] = [
        row for row in bundle["evidence_references"] if row["evidence_type"] != evidence_type
    ]

    validation = validate_live_canary_readiness_evidence_bundle(bundle)

    assert validation["valid"] is False
    assert expected_status in validation["statuses"]
    assert evidence_type in validation["missing_required_evidence"]
    assert validation["live_execution_approved"] is False
    assert validation["canary_executable_now"] is False
    assert validation["real_execution_available"] is False
    assert validation["live_connector_enabled"] is False


def test_evidence_bundle_requires_unresolved_blockers_and_non_execution_statements() -> None:
    bundle = deepcopy(_base_artifacts()["bundle"])
    bundle["unresolved_blockers"] = []
    bundle["blocker_summary"]["unresolved_live_blocker_count"] = 0
    bundle["blocker_summary"]["all_live_connector_blockers_unresolved"] = False
    validation = validate_live_canary_readiness_evidence_bundle(bundle)

    assert validation["valid"] is False
    assert VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT in validation["statuses"]

    bundle = deepcopy(_base_artifacts()["bundle"])
    bundle["non_execution_statements"] = bundle["non_execution_statements"][:-1]
    validation = validate_live_canary_readiness_evidence_bundle(bundle)

    assert validation["valid"] is False
    assert "missing_required_evidence" in validation["statuses"]


def test_validation_passes_only_for_dry_run_review_and_keeps_live_flags_false() -> None:
    bundle = _base_artifacts()["bundle"]
    validation = validate_live_canary_readiness_evidence_bundle(bundle)

    assert validation["valid"] is True
    assert validation["status"] == VALIDATION_STATUS_DRY_RUN_VALID
    assert bundle["readiness_evidence_bundle_is_not_live_approval"] is True
    assert bundle["live_execution_approved"] is False
    assert bundle["canary_executable_now"] is False
    assert bundle["real_execution_available"] is False
    assert bundle["live_connector_enabled"] is False
    assert all(item["execution_enabling"] is False for item in bundle["evidence_items"])
    assert all(reference["execution_enabling"] is False for reference in bundle["evidence_references"])


def test_missing_required_evidence_produces_deterministic_blocker() -> None:
    first = deepcopy(_base_artifacts()["bundle"])
    second = deepcopy(_base_artifacts()["bundle"])
    for bundle in (first, second):
        bundle["evidence_items"][0]["present"] = False
        bundle["evidence_items"][0]["review_ready"] = False

    assert validate_live_canary_readiness_evidence_bundle(first) == validate_live_canary_readiness_evidence_bundle(second)


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_forbidden_secret_signing_order_and_auth_fields_are_rejected(field: str) -> None:
    bundle = deepcopy(_base_artifacts()["bundle"])
    bundle[field] = "<redacted>"
    validation = validate_live_canary_readiness_evidence_bundle(bundle)

    assert validation["valid"] is False
    assert VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD in validation["statuses"]
    assert f"$.{field}" in validation["forbidden_field_paths"]


def test_forbidden_execution_approval_is_rejected() -> None:
    bundle = deepcopy(_base_artifacts()["bundle"])
    bundle["live_execution_approved"] = True

    validation = validate_live_canary_readiness_evidence_bundle(bundle)

    assert validation["valid"] is False
    assert VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL in validation["statuses"]


def test_secret_boundary_helpers_cover_bundle_items_and_manifest() -> None:
    bundle = _base_artifacts()["bundle"]
    manifest = build_live_canary_readiness_evidence_manifest(bundle)

    assert validate_secret_boundary_readiness_evidence_bundle(bundle)["valid"] is True
    assert validate_secret_boundary_readiness_evidence_item(bundle["evidence_items"][0])["valid"] is True
    assert validate_secret_boundary_readiness_evidence_manifest(manifest)["valid"] is True
    assert validate_secret_boundary_readiness_evidence_bundle({"signed_order": "<redacted>"})["valid"] is False


def test_manifest_and_summary_are_json_compatible_and_idempotent() -> None:
    bundle = _base_artifacts()["bundle"]
    first_manifest = build_live_canary_readiness_evidence_manifest(bundle)
    second_manifest = build_live_canary_readiness_evidence_manifest(deepcopy(bundle))
    summary = summarize_live_canary_readiness_evidence_bundle(bundle, latest_readiness_evidence_bundle_path="bundle.json")

    assert first_manifest == second_manifest
    assert validate_live_canary_readiness_evidence_manifest(first_manifest)["valid"] is True
    assert json.loads(json.dumps(first_manifest, sort_keys=True)) == first_manifest
    assert summary["readiness_evidence_bundle_review_ready"] is True
    assert summary["readiness_evidence_bundle_is_not_live_approval"] is True
    assert summary["latest_readiness_evidence_bundle_path"] == "bundle.json"


def test_operator_intent_approval_preflight_and_audit_remain_non_executable() -> None:
    artifacts = _base_artifacts()

    assert artifacts["intent_packet"]["intent_packet_status"] == INTENT_PACKET_STATUS_REVIEW_READY
    assert artifacts["intent_packet"]["operator_intent_is_not_live_approval"] is True
    assert artifacts["intent_packet"]["operator_signed_intent_is_human_acknowledgement_only"] is True
    assert artifacts["operator_packet"]["operator_packet_status"] == OPERATOR_REVIEW_READY
    assert artifacts["operator_packet"]["operator_review_is_not_live_approval"] is True
    assert artifacts["preflight"]["status"] == PREFLIGHT_STATUS_READY
    assert artifacts["audit_replay"]["status"] == REPLAY_STATUS_PASSED
    for artifact in (
        artifacts["intent_packet"],
        artifacts["operator_packet"],
        artifacts["preflight"],
        artifacts["audit_replay"],
    ):
        assert artifact["live_execution_approved"] is False
        assert artifact["real_execution_available"] is False
        assert artifact["canary_executable_now"] is False
    assert artifacts["audit_replay"]["live_connector_enabled"] is False
    assert artifacts["runbook"]["status"] == MANUAL_RUNBOOK_STATUS_READY


def test_dashboard_surfaces_readiness_evidence_bundle_status_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    bundle = json.loads((tmp_path / "live_canary_readiness_evidence_bundle.json").read_text(encoding="utf-8"))
    summary = dashboard["readiness_evidence_bundle_summary"]

    assert result.validation_passed is True
    assert result.readiness_evidence_bundle_path.endswith("live_canary_readiness_evidence_bundle.json")
    assert bundle["bundle_status"] == BUNDLE_STATUS_REVIEW_READY
    assert summary["readiness_evidence_bundle_status"] == BUNDLE_STATUS_REVIEW_READY
    assert summary["readiness_evidence_bundle_review_ready"] is True
    assert summary["readiness_evidence_bundle_is_not_live_approval"] is True
    assert summary["evidence_item_count"] >= len(REQUIRED_EVIDENCE_TYPES)
    assert summary["missing_required_evidence_count"] == 0
    assert summary["unresolved_live_blocker_count"] >= 31
    assert summary["canary_executable_now"] is False
    assert summary["live_execution_approved"] is False
    assert summary["real_execution_available"] is False
    assert summary["live_connector_enabled"] is False


def test_strategy_evaluation_surfaces_passive_readiness_evidence_bundle_status(tmp_path: Path) -> None:
    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    strategy = json.loads((tmp_path / "paper_strategy_evaluation_ledger.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "paper_strategy_evaluation_summary.json").read_text(encoding="utf-8"))

    for artifact in (strategy, summary):
        assert artifact["readiness_evidence_bundle_status"] == BUNDLE_STATUS_REVIEW_READY
        assert artifact["readiness_evidence_bundle_review_ready"] is True
        assert artifact["readiness_evidence_bundle_is_not_live_approval"] is True
        assert artifact["canary_executable_now"] is False
        assert artifact["live_execution_approved"] is False
        assert artifact["real_execution_available"] is False
        assert artifact["live_connector_enabled"] is False


def test_blocker_matrix_keeps_critical_live_blockers_unresolved_and_adds_bundle_categories() -> None:
    matrix = build_live_connector_blocker_matrix()
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert {
        "readiness_evidence_bundle_review_only",
        "readiness_evidence_bundle_not_live_approval",
        "readiness_evidence_bundle_not_operator_executed",
        "evidence_bundle_does_not_resolve_live_blockers",
        "live_canary_execution_still_disabled",
        "live_canary_real_funding_still_not_configured",
        "live_canary_order_adapter_still_disabled",
    }.issubset(categories)
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["critical_blocker_count"] == matrix["unresolved_blocker_count"]
    assert matrix["live_execution_available"] is False
    assert all(row["resolution_status"] == "unresolved" for row in matrix["blockers"])


def test_no_forbidden_active_fields_appear_in_allowed_bundle_outputs() -> None:
    bundle = _base_artifacts()["bundle"]
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
        "access_token",
        "order_submission_payload",
        "transaction_payload",
    }
    keys = {key for _path, key, _value in _walk(bundle)}

    assert active_forbidden_keys.isdisjoint(keys)
    assert bundle["readiness_evidence_bundle_is_not_live_approval"] is True
    assert bundle["operator_intent_remains_human_acknowledgement_only"] is True
    assert bundle["canary_executable_now"] is False
    assert bundle["live_execution_approved"] is False
    assert bundle["real_execution_available"] is False
    assert bundle["live_connector_enabled"] is False
    assert _base_artifacts()["disabled_result"]["connector_status"] == CONNECTOR_STATUS_DISABLED


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

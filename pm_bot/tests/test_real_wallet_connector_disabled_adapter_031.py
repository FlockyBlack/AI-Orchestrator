from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_replay_acceptance import (
    build_canary_acceptance_matrix,
    build_live_connector_blocker_matrix,
)
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    CONNECTOR_STATUS_DISABLED,
    DISABLED_CONNECTOR_RESULT_STATUS,
    DISABLED_CONNECTOR_UNRESOLVED_BLOCKER_IDS,
    REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS,
    DisabledRealWalletConnectorConfig,
    RealWalletConnectorDisabledAdapter,
    build_disabled_connector_audit_record,
    build_disabled_connector_request,
    build_disabled_connector_result,
    build_disabled_connector_passive_status,
    validate_disabled_connector_request,
)
from pm_bot.trading_core.secret_boundary_policy import (
    FORBIDDEN_PAYLOAD_KEYS,
    SAFE_PLACEHOLDER_MARKERS,
    find_forbidden_secret_field_paths,
    is_safe_placeholder,
    validate_secret_boundary_audit_record,
    validate_secret_boundary_doc_example,
    validate_secret_boundary_receipt,
    validate_secret_boundary_request,
    validate_static_env_var_names,
)


def _config() -> DisabledRealWalletConnectorConfig:
    return DisabledRealWalletConnectorConfig(
        require_canary_readiness_packet_reference=True,
        require_replay_acceptance_reference=True,
    )


def _request(**overrides: Any) -> dict[str, Any]:
    request = build_disabled_connector_request(
        run_id="disabled-adapter-test-run",
        market_id="market-031",
        risk_decision_reference="risk-decision-v1-test",
        wallet_boundary_packet_reference="wallet-boundary-execution-request-test",
        canary_readiness_packet_reference="live-canary-readiness-test",
        replay_acceptance_reference="live-canary-dry-run-acceptance-test",
        dry_run_only=True,
    ).to_dict()
    request.update(overrides)
    return request


def test_disabled_adapter_always_refuses_execution() -> None:
    adapter = RealWalletConnectorDisabledAdapter(_config())

    result = adapter.build_blocked_result(_request())

    assert result["connector_status"] == CONNECTOR_STATUS_DISABLED
    assert result["status"] == DISABLED_CONNECTOR_RESULT_STATUS
    assert result["execution_refused"] is True
    assert result["real_execution_available"] is False
    assert result["live_execution_allowed"] is False
    assert result["live_execution_enabled"] is False
    assert result["external_api_calls_performed"] is False
    assert set(REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS).issubset(result["blocked_reason_ids"])


def test_dry_run_only_is_required() -> None:
    request = _request(dry_run_only=False)

    validation = validate_disabled_connector_request(request, config=_config())

    assert validation["valid"] is False
    assert "dry_run_only_required" in validation["validation_errors"]
    assert "dry_run_only_required" in validation["blocked_reason_ids"]


def test_no_secret_fields_are_accepted_in_request_or_config() -> None:
    request = _request(private_key="<redacted>")
    config = _config().to_dict()
    config["client_secret"] = "<redacted>"

    request_validation = validate_disabled_connector_request(request, config=_config())
    config_validation = validate_disabled_connector_request(_request(), config=config)

    assert request_validation["valid"] is False
    assert "request_secret_boundary_violation" in request_validation["validation_errors"]
    assert "$.private_key" in request_validation["request_secret_boundary_validation"]["forbidden_secret_field_paths"]
    assert config_validation["valid"] is False
    assert "config_secret_boundary_violation" in config_validation["validation_errors"]
    assert "$.client_secret" in config_validation["config_secret_boundary_validation"]["forbidden_secret_field_paths"]


def test_forbidden_secret_like_fields_are_detected_and_safe_placeholders_are_allowed() -> None:
    for field_name in FORBIDDEN_PAYLOAD_KEYS:
        validation = validate_secret_boundary_request({field_name: "<redacted>"})
        assert validation["valid"] is False, field_name
        assert f"$.{field_name}" in validation["forbidden_secret_field_paths"]

    for marker in SAFE_PLACEHOLDER_MARKERS:
        validation = validate_secret_boundary_doc_example({"placeholder": marker, "mode": "dry_run_only"})
        assert validation["valid"] is True, marker
        assert is_safe_placeholder(marker) is True


def test_adapter_never_reports_signed_submitted_or_sent_status() -> None:
    result = build_disabled_connector_result(_request(), config=_config())
    audit = build_disabled_connector_audit_record(request=_request(), result=result, config=_config())

    for _path, key, value in _walk(audit):
        key_text = str(key).lower()
        value_text = str(value).lower()
        if key_text == "status" or key_text.endswith("_status"):
            assert value_text not in {"signed", "submitted", "sent"}
    assert result["real_execution_available"] is False
    assert result["real_order_placement_performed"] is False
    assert result["cryptographic_signing_performed"] is False
    assert result["authenticated_endpoint_call_performed"] is False


def test_blocker_matrix_keeps_all_real_live_blockers_unresolved() -> None:
    matrix = build_live_connector_blocker_matrix()
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert matrix["status"] == "passed"
    assert matrix["live_execution_available"] is False
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["all_blockers_unresolved"] is True
    assert set(DISABLED_CONNECTOR_UNRESOLVED_BLOCKER_IDS).issubset(categories)
    assert matrix["unresolved_blocker_count"] == matrix["blocker_count"]
    assert all(row["resolution_status"] == "unresolved" for row in matrix["blockers"])


def test_paper_daily_dashboard_surfaces_disabled_connector_summary(tmp_path: Path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    audit = json.loads((tmp_path / "disabled_real_wallet_connector_audit.json").read_text(encoding="utf-8"))
    strategy = json.loads((tmp_path / "paper_strategy_evaluation_ledger.json").read_text(encoding="utf-8"))
    summary = dashboard["disabled_real_connector_summary"]

    assert result.validation_passed is True
    assert result.simulated_fill_count == 2
    assert summary["connector_status"] == "disabled"
    assert summary["real_execution_available"] is False
    assert summary["secrets_present"] == "not_inspected"
    assert summary["secret_boundary_status"] == "static_policy_only"
    assert summary["blocked_reason_count"] >= len(REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS)
    assert summary["latest_disabled_connector_audit_path"].endswith("disabled_real_wallet_connector_audit.json")
    assert summary["live_canary_replay_acceptance_status"] == "passed"
    assert audit["audit_valid"] is True
    assert audit["real_execution_available"] is False
    assert strategy["disabled_real_connector_status"]["connector_status"] == "disabled"
    assert strategy["disabled_real_connector_status"]["real_execution_available"] is False


def test_replay_acceptance_remains_blocker_only() -> None:
    acceptance = build_canary_acceptance_matrix()
    blocker = build_live_connector_blocker_matrix()

    assert acceptance["status"] == "passed"
    assert acceptance["live_execution_available"] is False
    assert acceptance["external_api_calls_performed"] is False
    assert all(row["live_execution_remains_forbidden"] is True for row in acceptance["rows"])
    assert blocker["current_live_connector_status"] == "blocked"
    assert blocker["live_execution_available"] is False


def test_idempotency_same_request_produces_deterministic_result_and_audit() -> None:
    request = _request()
    adapter = RealWalletConnectorDisabledAdapter(_config())

    first_result = adapter.build_blocked_result(request)
    second_result = adapter.build_blocked_result(deepcopy(request))
    first_audit = adapter.build_audit_record(request)
    second_audit = adapter.build_audit_record(deepcopy(request))

    assert first_result == second_result
    assert first_audit == second_audit


def test_static_scan_catches_forbidden_fields_in_packets_configs_and_env_names() -> None:
    packet = {"request": {"wallet_password": "<redacted>"}, "safe": "dry_run_only"}
    config = {"nested": {"polymarket_api_key": "<redacted>"}}
    env_validation = validate_static_env_var_names(["PMBOT_DISABLED_MODE", "PMBOT_PRIVATE_KEY"])

    assert find_forbidden_secret_field_paths(packet) == ["$.request.wallet_password"]
    assert validate_secret_boundary_request(packet)["valid"] is False
    assert validate_secret_boundary_doc_example(config)["valid"] is False
    assert "$.nested.polymarket_api_key" in validate_secret_boundary_doc_example(config)[
        "forbidden_secret_field_paths"
    ]
    assert env_validation["valid"] is False
    assert env_validation["forbidden_env_var_names"] == ["PMBOT_PRIVATE_KEY"]


def test_result_artifacts_do_not_include_secret_fields() -> None:
    result = build_disabled_connector_result(_request(), config=_config())
    audit = build_disabled_connector_audit_record(request=_request(), result=result, config=_config())
    passive = build_disabled_connector_passive_status(result=result)

    assert validate_secret_boundary_receipt(result)["valid"] is True
    assert validate_secret_boundary_audit_record(audit)["valid"] is True
    assert validate_secret_boundary_doc_example(passive)["valid"] is True
    assert result["environment_secrets_read"] is False
    assert audit["secrets_present"] == "not_inspected"


def test_no_active_wallet_signing_order_or_auth_fields_are_introduced_in_allowed_outputs() -> None:
    result = build_disabled_connector_result(_request(), config=_config())
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
    }

    keys = {str(key) for _path, key, _value in _walk(result)}

    assert active_forbidden_keys.isdisjoint(keys)
    assert result["real_wallet_access_performed"] is False
    assert result["cryptographic_signing_performed"] is False
    assert result["real_order_placement_performed"] is False
    assert result["authenticated_endpoint_call_performed"] is False


def test_no_real_wallet_secret_signing_order_endpoint_code_or_external_calls(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    adapter_source = Path("pm_bot/trading_core/real_wallet_connector_disabled_adapter.py").read_text(
        encoding="utf-8"
    ).lower()
    policy_source = Path("pm_bot/trading_core/secret_boundary_policy.py").read_text(encoding="utf-8").lower()
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
        "submit_order(",
        "os.environ",
        "getenv(",
    )

    assert all(marker not in adapter_source for marker in forbidden_runtime_markers)
    assert "os.environ" not in policy_source
    assert "getenv(" not in policy_source
    assert build_disabled_connector_result(_request(), config=_config())["external_api_calls_performed"] is False


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

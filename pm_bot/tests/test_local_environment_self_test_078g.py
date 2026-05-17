from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.live_account_readonly_state_probe import LiveAccountSdkBinding
from pm_bot.trading_core.local_environment_self_test_bundle_078g import (
    STATUS_BLOCKED_MISSING_FUNDER_ADDRESS,
    STATUS_BLOCKED_PAYLOAD_READINESS_NOT_OK,
    STATUS_BLOCKED_SDK_UNAVAILABLE,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY,
    STATUS_READY,
    local_environment_self_test_artifact_paths,
    run_local_environment_self_test_bundle,
    validate_local_environment_self_test_result,
)

GENERATED_AT = "2026-05-17T00:00:00+04:00"

FAKE_ENV = {
    "POLYMARKET_API_KEY": "fake-api-key-never-output-078g",
    "POLYMARKET_API_SECRET": "fake-api-secret-never-output-078g",
    "POLYMARKET_API_PASSPHRASE": "fake-passphrase-never-output-078g",
    "POLYMARKET_PRIVATE_KEY": "0x" + "8" * 64,
    "POLYMARKET_WALLET_ADDRESS": "0x1111111111111111111111111111111111111111",
    "POLYMARKET_FUNDER_ADDRESS": "0x2222222222222222222222222222222222222222",
    "POLYMARKET_SIGNATURE_TYPE": "2",
    "TELEGRAM_BOT_TOKEN": "fake-telegram-token-never-output-078g",
    "TELEGRAM_ALLOWED_OPERATOR_IDS": "123456789,987654321",
    "PMBOT_TELEGRAM_BOT_TOKEN": "fake-pmbot-telegram-token-never-output-078g",
    "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": "123456789,987654321",
}

FAKE_SECRET_LIKE_VALUES = (
    "fake-api-key-never-output-078g",
    "fake-api-secret-never-output-078g",
    "fake-passphrase-never-output-078g",
    "0x" + "8" * 64,
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222",
    "fake-telegram-token-never-output-078g",
    "fake-pmbot-telegram-token-never-output-078g",
    "123456789,987654321",
)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _minimal_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def _artifact_text(root: Path) -> str:
    chunks: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _walk_mappings(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        rows: list[Mapping[str, Any]] = [value]
        for nested in value.values():
            rows.extend(_walk_mappings(nested))
        return rows
    if isinstance(value, list):
        rows = []
        for nested in value:
            rows.extend(_walk_mappings(nested))
        return rows
    return []


def _assert_no_fake_secret_values(text_or_value: Any) -> None:
    text = text_or_value if isinstance(text_or_value, str) else json.dumps(text_or_value, sort_keys=True)
    for fake_value in FAKE_SECRET_LIKE_VALUES:
        assert fake_value not in text


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in (
            "allowed_for_live",
            "trading_requested",
            "live_execution_approved",
            "live_execution_allowed",
            "live_execution_performed",
            "real_execution_available",
            "order_submission_enabled",
            "order_submission_attempted",
            "order_submission_performed",
            "order_submitted",
            "order_cancel_enabled",
            "order_cancellation_attempted",
            "order_cancellation_performed",
            "signing_enabled",
            "signing_attempted",
            "signing_by_default",
            "signer_instantiated",
            "signer_instantiation_attempted",
            "wallet_connection_attempted",
            "wallet_connection_ui_added",
            "wallet_signing_enabled",
            "wallet_signing_attempted",
            "authenticated_endpoint_enabled",
            "authenticated_request_performed",
            "trading_write_call_performed",
            "network_write_performed",
            "network_post_performed",
            "network_put_performed",
            "network_patch_performed",
            "network_delete_performed",
            "full_signed_payload_output",
            "full_signed_payload_emitted",
            "raw_signed_payload_emitted",
            "raw_secret_values_emitted",
            "raw_values_emitted",
            "secrets_printed",
            "secrets_persisted",
            "wallet_files_read",
            "browser_profiles_read",
            "credential_stores_read",
            "browser_automation_added",
            "scheduler_or_daemon_added",
            "background_worker_added",
            "autonomous_live_trading_added",
            "telegram_network_check_requested",
            "polymarket_trading_api_call_performed",
        ):
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def _sdk_available() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(
        status="available",
        module_name="fake_safe_sdk",
        attempted_modules=("fake_safe_sdk",),
    )


def _sdk_unavailable() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(
        status="dependency_missing",
        attempted_modules=("py_clob_client_v2", "py_clob_client"),
        error_type="ModuleNotFoundError",
        error_message_sanitized="dependency_missing",
    )


def _telegram_ready_builder(**kwargs: Any) -> Mapping[str, Any]:
    assert kwargs["network_check"] is False
    return {
        "status": "telegram_runtime_ready",
        "ready_to_start_runtime": True,
        "review_only_safety_flags_ok": True,
        "network_check_requested": False,
        "env_status": {
            "telegram_token": "present",
            "allowed_operator_id_count": 2,
        },
        "dependency_check": {"status": "installed"},
        "runtime_module_import": {"status": "ok"},
        "config_errors": [],
        "generated_at": kwargs.get("generated_at", GENERATED_AT),
    }


def _telegram_blocked_builder(**kwargs: Any) -> Mapping[str, Any]:
    assert kwargs["network_check"] is False
    return {
        "status": STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY,
        "ready_to_start_runtime": False,
        "review_only_safety_flags_ok": True,
        "network_check_requested": False,
        "env_status": {
            "telegram_token": "missing",
            "allowed_operator_id_count": 0,
        },
        "dependency_check": {"status": "missing"},
        "runtime_module_import": {"status": "failed"},
        "config_errors": ["TELEGRAM_BOT_TOKEN missing"],
        "generated_at": kwargs.get("generated_at", GENERATED_AT),
    }


def _write_ready_source_artifacts(root: Path) -> None:
    _write_json(
        root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
        {
            "contract_version": "pmbot_latest_live_account_readonly_state_070c.v1",
            "status": "account_state_probe_succeeded_live_blocked",
            "account_state_probe_performed": True,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root / "local_real_check_bundle_072c" / "latest_local_real_check_bundle_status_072c.json",
        {
            "contract_version": "pmbot_latest_local_real_check_bundle_072c.v1",
            "status": "local_real_check_bundle_completed_reported_live_blocked",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root / "selected_candidate_artifact_075d" / "latest_selected_candidate_artifact_075d.json",
        {
            "contract_version": "pmbot_latest_selected_candidate_artifact_075d.v1",
            "status": "selected_candidate_artifact_recorded",
            "selected_candidate_artifact_recorded": True,
            "selected_by_operator": True,
            "source_backed": True,
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root
        / "selected_token_verification_bridge_076a"
        / "latest_selected_token_verification_076a_status.json",
        {
            "contract_version": "pmbot_latest_selected_token_verification_bridge_076a_status.v1",
            "status": "selected_token_verified_for_payload_dry_run",
            "selected_token_verified_for_payload_dry_run": True,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root
        / "signer_diagnostic_evidence_bridge_076c"
        / "latest_signer_diagnostic_evidence_076c_status.json",
        {
            "contract_version": "pmbot_latest_signer_diagnostic_evidence_bridge_076c_status.v1",
            "status": "signer_diagnostic_evidence_ok_for_payload_dry_run",
            "signer_diagnostic_evidence_ok_for_payload_dry_run": True,
            "source_artifact_available": True,
            "allowed_for_live": False,
            "signer_ready_for_live": False,
            "order_submission_enabled": False,
            "order_submit_ready": False,
            "full_signed_payload_output": False,
            "signing_by_default": False,
            "signer_instantiated": False,
        },
    )
    _write_json(
        root / "payload_dry_run_readiness_076d" / "latest_payload_dry_run_readiness_076d_status.json",
        {
            "contract_version": "pmbot_latest_payload_dry_run_readiness_076d_status.v1",
            "status": "payload_dry_run_ready_for_operator_review",
            "payload_dry_run_ready": True,
            "current_top_blocker": "",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "full_signed_payload_output": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root
        / "first_supervised_tiny_order_readiness_077a"
        / "latest_first_supervised_tiny_order_readiness_077a_status.json",
        {
            "contract_version": "pmbot_latest_first_supervised_tiny_order_readiness_077a_status.v1",
            "status": "ready_for_separate_live_authorization_packet",
            "first_supervised_tiny_order_ready_for_authorization": True,
            "first_supervised_tiny_order_ready_for_execution": False,
            "current_top_blocker": "blocked_missing_explicit_live_authorization",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "order_submission_attempted": False,
            "signing_by_default": False,
            "signer_instantiated": False,
        },
    )


def _run_bundle(
    tmp_path: Path,
    *,
    env: Mapping[str, str] | None = None,
    sdk_loader: Any = _sdk_available,
    telegram_builder: Any = _telegram_ready_builder,
) -> dict[str, Any]:
    return run_local_environment_self_test_bundle(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        environ=dict(FAKE_ENV if env is None else env),
        sdk_loader=sdk_loader,
        telegram_smoke_builder=telegram_builder,
        generated_at=GENERATED_AT,
        head_before="head-before-078g",
        head_after="head-after-078g",
    )


def test_ready_bundle_reports_required_fields_and_no_live(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")

    result = _run_bundle(tmp_path)
    latest = result["latest_status"]
    paths = local_environment_self_test_artifact_paths(tmp_path / "out")

    assert result["status"] == STATUS_READY
    assert result["passed_count"] == 10
    assert result["check_count"] == 10
    assert result["blocker_count"] == 0
    assert latest["status"] == STATUS_READY
    assert latest["runtime_credential_visibility_status"] == "runtime_credentials_visible"
    assert latest["funder_wallet_context_status"] in {
        "funder_differs_from_wallet_address",
        "wallet_context_visible",
    }
    assert latest["clob_sdk_account_readonly_probe_status"] == "account_state_probe_succeeded_live_blocked"
    assert latest["local_real_check_bundle_status"] == "local_real_check_bundle_completed_reported_live_blocked"
    assert latest["selected_candidate_artifact_status"] == "selected_candidate_artifact_recorded"
    assert latest["selected_token_verification_status"] == "selected_token_verified_for_payload_dry_run"
    assert latest["signer_diagnostic_evidence_status"] == "signer_diagnostic_evidence_ok_for_payload_dry_run"
    assert latest["payload_dry_run_readiness_status"] == "payload_dry_run_ready_for_operator_review"
    assert latest["first_supervised_tiny_order_readiness_status"] == "ready_for_separate_live_authorization_packet"
    assert latest["telegram_runtime_smoke_status"] == "telegram_runtime_ready"
    assert any(
        command.startswith("python -m pm_bot.operator_runner.local_environment_self_test_bundle")
        for command in result["exact_next_safe_commands"]
    )
    assert "python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run" in result[
        "exact_next_safe_commands"
    ]
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["checks"].exists()
    assert paths["blockers"].exists()
    assert paths["operator_md"].exists()
    assert paths["telegram_smoke"].exists()
    assert validate_local_environment_self_test_result(result)["valid"] is True
    _assert_no_fake_secret_values(result)
    _assert_no_fake_secret_values(_artifact_text(tmp_path / "out"))
    _assert_required_false_flags(result)


def test_missing_funder_maps_to_expected_status_and_safe_command(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")
    env = dict(FAKE_ENV)
    env.pop("POLYMARKET_FUNDER_ADDRESS")

    result = _run_bundle(tmp_path, env=env)

    assert result["status"] == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS
    assert result["latest_status"]["funder_wallet_context_status"] == "blocked_missing_funder_address"
    blockers = {row["check_id"]: row for row in result["top_blockers"]}
    assert "funder_wallet_context" in blockers
    assert blockers["funder_wallet_context"]["next_safe_command"] == (
        "python -m pm_bot.operator_runner.funder_wallet_context_diagnostic "
        "--market BTC --strategy tiny-momentum --dry-run"
    )
    assert validate_local_environment_self_test_result(result)["valid"] is True
    _assert_no_fake_secret_values(result)
    _assert_required_false_flags(result)


def test_sdk_unavailable_maps_to_expected_status(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")

    result = _run_bundle(tmp_path, sdk_loader=_sdk_unavailable)
    clob = next(check for check in result["checks"] if check["check_id"] == "clob_sdk_account_readonly_probe")

    assert result["status"] == STATUS_BLOCKED_SDK_UNAVAILABLE
    assert clob["passed"] is False
    assert clob["details"]["sdk_available"] is False
    assert clob["details"]["account_readonly_probe_performed"] is True
    assert validate_local_environment_self_test_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_signer_diagnostic_not_ok_maps_to_expected_status(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")
    _write_json(
        tmp_path
        / "sources"
        / "signer_diagnostic_evidence_bridge_076c"
        / "latest_signer_diagnostic_evidence_076c_status.json",
        {
            "contract_version": "pmbot_latest_signer_diagnostic_evidence_bridge_076c_status.v1",
            "status": "blocked_signer_diagnostic_failed",
            "signer_diagnostic_evidence_ok_for_payload_dry_run": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
            "signer_instantiated": False,
        },
    )

    result = _run_bundle(tmp_path)

    assert result["status"] == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    assert result["latest_status"]["signer_diagnostic_evidence_status"] == "blocked_signer_diagnostic_failed"
    assert result["top_blockers"][0]["check_id"] == "signer_diagnostic_evidence"
    assert validate_local_environment_self_test_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_payload_not_ok_maps_to_expected_status(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")
    _write_json(
        tmp_path / "sources" / "payload_dry_run_readiness_076d" / "latest_payload_dry_run_readiness_076d_status.json",
        {
            "contract_version": "pmbot_latest_payload_dry_run_readiness_076d_status.v1",
            "status": "blocked_signed_payload_dry_run_not_ready",
            "payload_dry_run_ready": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "full_signed_payload_output": False,
            "signing_by_default": False,
        },
    )

    result = _run_bundle(tmp_path)

    assert result["status"] == STATUS_BLOCKED_PAYLOAD_READINESS_NOT_OK
    assert result["latest_status"]["payload_dry_run_readiness_status"] == "blocked_signed_payload_dry_run_not_ready"
    assert result["top_blockers"][0]["check_id"] == "payload_dry_run_readiness"
    assert validate_local_environment_self_test_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_telegram_not_ready_maps_to_expected_status(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")

    result = _run_bundle(tmp_path, telegram_builder=_telegram_blocked_builder)

    assert result["status"] == STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY
    assert result["latest_status"]["telegram_runtime_smoke_status"] == STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY
    assert result["top_blockers"][0]["check_id"] == "telegram_runtime_smoke"
    assert validate_local_environment_self_test_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_runner_rejects_live_order_signing_flags_before_work(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.local_environment_self_test_bundle",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--submit",
            "--artifacts-dir",
            str(tmp_path / "out"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "no-live/no-submit/no-cancel/no-sign-by-default" in combined
    assert not (tmp_path / "out").exists()

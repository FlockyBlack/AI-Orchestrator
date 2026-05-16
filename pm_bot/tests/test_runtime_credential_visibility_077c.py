from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.runtime_credential_visibility_diagnostic as runner_module
import pm_bot.trading_core.runtime_credential_visibility_077c as diagnostic_module
from pm_bot.trading_core.runtime_credential_visibility_077c import (
    REQUESTED_ENV_VAR_NAMES,
    STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS,
    STATUS_BLOCKED_MISSING_PRIVATE_KEY,
    STATUS_BLOCKED_MISSING_TELEGRAM_CREDENTIALS,
    STATUS_BLOCKED_MISSING_WALLET_ADDRESS,
    STATUS_RUNTIME_CREDENTIALS_VISIBLE,
    TELEGRAM_RUNTIME_ALIAS_ENV_VAR_NAMES,
    run_runtime_credential_visibility_diagnostic,
    runtime_credential_visibility_artifact_paths,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"

FAKE_ENV = {
    "POLYMARKET_API_KEY": "fake-api-key-never-output-077c",
    "POLYMARKET_API_SECRET": "fake-api-secret-never-output-077c",
    "POLYMARKET_API_PASSPHRASE": "fake-passphrase-never-output-077c",
    "POLYMARKET_PRIVATE_KEY": "0x" + "7" * 64,
    "POLYMARKET_WALLET_ADDRESS": "0x1111111111111111111111111111111111111111",
    "POLYMARKET_SIGNATURE_TYPE": "1",
    "POLYMARKET_FUNDER_ADDRESS": "0x2222222222222222222222222222222222222222",
    "TELEGRAM_BOT_TOKEN": "fake-telegram-token-never-output-077c",
    "TELEGRAM_ALLOWED_OPERATOR_IDS": "123456789,987654321",
    "PMBOT_TELEGRAM_BOT_TOKEN": "fake-pmbot-telegram-token-never-output-077c",
    "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": "123456789,987654321",
}

FAKE_SECRET_LIKE_VALUES = (
    "fake-api-key-never-output-077c",
    "fake-api-secret-never-output-077c",
    "fake-passphrase-never-output-077c",
    "0x" + "7" * 64,
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222",
    "fake-telegram-token-never-output-077c",
    "fake-pmbot-telegram-token-never-output-077c",
    "123456789,987654321",
)

REQUIRED_ARTIFACT_NAMES = {
    "latest_runtime_credential_visibility_077c_status.json",
    "runtime_credential_visibility_077c_result.json",
    "runtime_credential_visibility_077c_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/runtime_credential_visibility_077c.py"),
    Path("pm_bot/operator_runner/runtime_credential_visibility_diagnostic.py"),
)


def _minimal_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
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
            "order_submission_enabled",
            "order_submission_attempted",
            "order_submitted",
            "order_cancel_enabled",
            "order_cancellation_attempted",
            "signing_enabled",
            "signing_attempted",
            "signing_by_default",
            "signer_instantiated",
            "signer_instantiation_attempted",
            "wallet_connection_attempted",
            "wallet_signing_enabled",
            "authenticated_request_performed",
            "full_signed_payload_output",
            "raw_values_emitted",
            "raw_secret_values_emitted",
            "scheduler_or_daemon_added",
            "background_worker_added",
            "autonomous_live_trading_added",
        ):
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def test_missing_default_environment_fails_closed_on_private_key(tmp_path: Path) -> None:
    result = run_runtime_credential_visibility_diagnostic(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ={},
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_PRIVATE_KEY
    assert result["latest_status"]["private_key_visible"] is False
    assert result["latest_status"]["polymarket_l2_visible"] is False
    assert result["latest_status"]["telegram_credentials_visible"] is False
    assert result["validation"]["valid"] is True
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    _assert_required_false_flags(result)


def test_missing_l2_credentials_status_after_private_key_is_visible(tmp_path: Path) -> None:
    env = {
        "POLYMARKET_PRIVATE_KEY": FAKE_ENV["POLYMARKET_PRIVATE_KEY"],
        "POLYMARKET_WALLET_ADDRESS": FAKE_ENV["POLYMARKET_WALLET_ADDRESS"],
        "POLYMARKET_SIGNATURE_TYPE": FAKE_ENV["POLYMARKET_SIGNATURE_TYPE"],
        "POLYMARKET_FUNDER_ADDRESS": FAKE_ENV["POLYMARKET_FUNDER_ADDRESS"],
        "PMBOT_TELEGRAM_BOT_TOKEN": FAKE_ENV["PMBOT_TELEGRAM_BOT_TOKEN"],
        "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": FAKE_ENV["PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS"],
    }
    result = run_runtime_credential_visibility_diagnostic(
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS
    assert set(result["group_summary"]["polymarket_l2_missing_env_vars"]) == {
        "POLYMARKET_API_KEY",
        "POLYMARKET_API_SECRET",
        "POLYMARKET_API_PASSPHRASE",
    }
    _assert_no_fake_secret_values(result)
    _assert_required_false_flags(result)


def test_missing_wallet_context_status_after_l2_and_private_key_are_visible(tmp_path: Path) -> None:
    env = {
        "POLYMARKET_API_KEY": FAKE_ENV["POLYMARKET_API_KEY"],
        "POLYMARKET_API_SECRET": FAKE_ENV["POLYMARKET_API_SECRET"],
        "POLYMARKET_API_PASSPHRASE": FAKE_ENV["POLYMARKET_API_PASSPHRASE"],
        "POLYMARKET_PRIVATE_KEY": FAKE_ENV["POLYMARKET_PRIVATE_KEY"],
        "PMBOT_TELEGRAM_BOT_TOKEN": FAKE_ENV["PMBOT_TELEGRAM_BOT_TOKEN"],
        "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": FAKE_ENV["PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS"],
    }
    result = run_runtime_credential_visibility_diagnostic(
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_WALLET_ADDRESS
    assert set(result["group_summary"]["wallet_context_missing_env_vars"]) == {
        "POLYMARKET_WALLET_ADDRESS",
        "POLYMARKET_SIGNATURE_TYPE",
        "POLYMARKET_FUNDER_ADDRESS",
    }
    _assert_no_fake_secret_values(result)
    _assert_required_false_flags(result)


def test_missing_telegram_credentials_status_after_polymarket_context_is_visible(tmp_path: Path) -> None:
    env = {
        key: value
        for key, value in FAKE_ENV.items()
        if not key.startswith("TELEGRAM_") and not key.startswith("PMBOT_TELEGRAM_")
    }
    result = run_runtime_credential_visibility_diagnostic(
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_TELEGRAM_CREDENTIALS
    assert result["latest_status"]["telegram_credentials_visible"] is False
    _assert_no_fake_secret_values(result)
    _assert_required_false_flags(result)


def test_all_credentials_visible_emits_lengths_and_redacted_fingerprints_only(tmp_path: Path) -> None:
    result = run_runtime_credential_visibility_diagnostic(
        artifact_dir=tmp_path,
        environ=FAKE_ENV,
        generated_at=GENERATED_AT,
    )
    artifact_text = _artifact_text(runtime_credential_visibility_artifact_paths(tmp_path))
    rows = {row["env_var_name"]: row for row in result["requested_env_var_statuses"]}

    assert result["status"] == STATUS_RUNTIME_CREDENTIALS_VISIBLE
    assert rows["POLYMARKET_PRIVATE_KEY"]["present"] is True
    assert rows["POLYMARKET_PRIVATE_KEY"]["length"] == 66
    assert rows["POLYMARKET_PRIVATE_KEY"]["redacted_fingerprint_sha256_12"].startswith("sha256:")
    assert rows["TELEGRAM_ALLOWED_OPERATOR_IDS"]["parsed_item_count"] == 2
    assert result["latest_status"]["requested_present_count"] == len(REQUESTED_ENV_VAR_NAMES)
    assert result["latest_status"]["runtime_alias_present_count"] == len(TELEGRAM_RUNTIME_ALIAS_ENV_VAR_NAMES)
    assert result["validation"]["valid"] is True
    _assert_no_fake_secret_values(result)
    _assert_no_fake_secret_values(artifact_text)
    _assert_required_false_flags(result)


def test_pmbot_telegram_runtime_aliases_are_enough_for_runtime_visibility(tmp_path: Path) -> None:
    env = {key: value for key, value in FAKE_ENV.items() if not key.startswith("TELEGRAM_")}
    result = run_runtime_credential_visibility_diagnostic(
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_RUNTIME_CREDENTIALS_VISIBLE
    assert result["group_summary"]["telegram_prompt_alias_visible"] is False
    assert result["group_summary"]["telegram_runtime_alias_visible"] is True
    assert set(result["missing_required_env_vars"]) == {
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_ALLOWED_OPERATOR_IDS",
    }
    _assert_no_fake_secret_values(result)


def test_runner_emits_required_artifacts_and_rejects_secret_dump_flags(tmp_path: Path) -> None:
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.runtime_credential_visibility_diagnostic",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(FAKE_ENV),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.runtime_credential_visibility_diagnostic",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--env-dump",
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = json.loads(
        runtime_credential_visibility_artifact_paths(out_dir)["result"].read_text(encoding="utf-8")
    )

    assert completed.returncode == 0, completed.stderr
    assert "Runtime credential visibility diagnostic 077C completed." in completed.stdout
    assert "Status: runtime_credentials_visible" in completed.stdout
    assert "Raw secret output: false" in completed.stdout
    assert "Signer instantiated: false" in completed.stdout
    assert "Order submission enabled: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert set(p.name for p in out_dir.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["status"] == STATUS_RUNTIME_CREDENTIALS_VISIBLE
    assert result["allowed_for_live"] is False
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/sign/order/secret-dump flag" in forbidden.stderr
    _assert_no_fake_secret_values(completed.stdout)
    _assert_no_fake_secret_values(_artifact_text(runtime_credential_visibility_artifact_paths(out_dir)))
    _assert_required_false_flags(result)


def test_no_network_order_signing_wallet_or_background_runtime_calls_exist() -> None:
    source = (inspect.getsource(diagnostic_module) + "\n" + inspect.getsource(runner_module)).lower()
    forbidden_terms = (
        "requests.",
        "httpx.",
        "urllib.request",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "py_clob_client",
        "clobclient",
        "eth_account",
        "web3",
        "account.from_key",
        ".sign(",
        "sign_typed_data",
        "eip712",
        "create_order(",
        "post_order(",
        "submit_order(",
        "place_order(",
        "send_order(",
        "execute_order(",
        "cancel_order(",
        "delete_order(",
        "submit_cancel(",
        "while true",
        "time.sleep",
        "threading",
        "asyncio",
        "sched.",
        "start-process",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

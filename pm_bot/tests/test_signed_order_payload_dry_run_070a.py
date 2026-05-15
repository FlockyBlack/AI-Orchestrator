from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator, Mapping

from pm_bot.trading_core.signed_order_payload_dry_run import (
    build_signed_order_payload_dry_run,
    signed_order_payload_dry_run_artifact_paths,
)
from pm_bot.trading_core.signed_order_payload_dry_run_models import (
    LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED,
    LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID,
    LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED,
    LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED,
    REQUIRED_FALSE_FLAGS,
)
import pm_bot.trading_core.signed_order_payload_dry_run as dry_run_module
import pm_bot.trading_core.signed_order_payload_dry_run_models as models_module

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_PRIVATE_KEY = "0x" + "7" * 64
FAKE_FULL_SIGNED_PAYLOAD = '{"maker":"0xabc","signature":"0xdeadbeef"}'
FAKE_SECRET_VALUES = (
    FAKE_PRIVATE_KEY,
    "api-secret-marker-070a",
    "passphrase-marker-070a",
    FAKE_FULL_SIGNED_PAYLOAD,
)
FAKE_EXECUTION_VALUES = (
    "fake-order-id-070a",
    "fake-tx-hash-070a",
    "fake-fill-070a",
    "fake-pnl-070a",
)

REQUIRED_ARTIFACT_NAMES = {
    "signed_order_payload_dry_run_070a_result.json",
    "latest_signed_order_payload_dry_run_status_070a.json",
    "signed_order_payload_contract_070a.json",
    "signed_order_payload_redaction_policy_070a.json",
    "signed_order_payload_safety_contract_070a.json",
    "signed_order_payload_operator_summary_070a.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/signed_order_payload_dry_run_models.py"),
    Path("pm_bot/trading_core/signed_order_payload_dry_run.py"),
    Path("pm_bot/operator_runner/signed_order_payload_dry_run.py"),
)

EXECUTION_ARTIFACT_KEYS = {
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill_id",
    "fill",
    "fills",
    "balance",
    "balances",
    "position",
    "positions",
    "pnl",
    "realized_pnl",
    "unrealized_pnl",
}


class RaisingEnv(Mapping[str, str]):
    def __getitem__(self, key: str) -> str:
        raise AssertionError(f"unexpected environment read: {key}")

    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def get(self, key: str, default: Any = None) -> Any:
        raise AssertionError(f"unexpected environment read: {key}")


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


def _artifact_payloads(paths: Mapping[str, Path]) -> list[dict[str, Any]]:
    payloads = []
    for key, path in paths.items():
        if key != "root" and path.suffix == ".json":
            payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        keys = [str(key) for key in value]
        for nested in value.values():
            keys.extend(_walk_keys(nested))
        return keys
    if isinstance(value, list):
        keys: list[str] = []
        for nested in value:
            keys.extend(_walk_keys(nested))
        return keys
    return []


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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def test_default_mode_does_not_read_private_key_and_writes_required_artifacts(tmp_path: Path) -> None:
    result = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    second = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    paths = signed_order_payload_dry_run_artifact_paths(tmp_path)

    assert result == second
    assert result["status"] == "blocked_non_executable_signed_order_payload_dry_run_no_submit"
    assert result["local_signing_diagnostic_status"] == LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED
    assert result["private_key_read"] is False
    assert result["order_payload_contract_built"] is True
    assert result["order_payload_contract_executable"] is False
    assert result["signed_payload_submit_enabled"] is False
    assert result["order_submission_enabled"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)


def test_redaction_policy_exists_and_artifacts_emit_no_raw_key_or_full_signed_payload(tmp_path: Path) -> None:
    result = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id="token-marker-070a",
        artifact_dir=tmp_path,
        env={
            "POLYMARKET_PRIVATE_KEY": FAKE_PRIVATE_KEY,
            "POLYMARKET_API_SECRET": FAKE_SECRET_VALUES[1],
            "POLYMARKET_API_PASSPHRASE": FAKE_SECRET_VALUES[2],
            "FULL_SIGNED_PAYLOAD": FAKE_FULL_SIGNED_PAYLOAD,
        },
        generated_at=GENERATED_AT,
    )
    paths = signed_order_payload_dry_run_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)

    assert result["redaction_policy"]["redaction_policy_exists"] is True
    assert result["private_key_read"] is False
    assert result["private_key_value_emitted"] is False
    assert result["raw_private_key_emitted"] is False
    assert result["raw_secret_values_emitted"] is False
    assert result["full_signed_payload_emitted"] is False
    assert result["raw_signed_payload_emitted"] is False
    assert result["token_id_present"] is True
    assert result["token_id_fingerprint_sha256"]
    assert "token-marker-070a" not in artifact_text
    for fake in (*FAKE_SECRET_VALUES, *FAKE_EXECUTION_VALUES):
        assert fake not in artifact_text
    _assert_required_false_flags(result)


def test_optional_signing_diagnostic_is_explicitly_gated_and_fails_closed(tmp_path: Path) -> None:
    default = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "default",
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    missing_token = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_local_order_payload_signing_diagnostic=True,
        artifact_dir=tmp_path / "missing_token",
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    too_large = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id="token-marker-070a",
        max_notional_usd=1.01,
        allow_local_order_payload_signing_diagnostic=True,
        artifact_dir=tmp_path / "too_large",
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    not_implemented = build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id="token-marker-070a",
        max_notional_usd=1.0,
        allow_local_order_payload_signing_diagnostic=True,
        artifact_dir=tmp_path / "not_implemented",
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )

    assert default["local_signing_diagnostic_requested"] is False
    assert default["local_signing_diagnostic_status"] == LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED
    assert missing_token["local_signing_diagnostic_status"] == LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID
    assert too_large["local_signing_diagnostic_status"] == LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED
    assert not_implemented["local_signing_diagnostic_status"] == LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED
    assert not_implemented["local_signing_diagnostic_requirements_met"] is True
    assert not_implemented["signing_not_implemented"] is True
    for payload in (default, missing_token, too_large, not_implemented):
        assert payload["private_key_read"] is False
        assert payload["local_payload_signing_attempted"] is False
        assert payload["local_payload_signed"] is False
        assert payload["signed_payload_fingerprint_stored"] is False
        assert payload["signed_payload_submit_enabled"] is False
        assert payload["order_submission_enabled"] is False
        assert payload["allowed_for_live"] is False
        assert payload["validation"]["valid"] is True
        _assert_required_false_flags(payload)


def test_no_submit_cancel_post_put_patch_delete_or_trading_write_endpoint_code() -> None:
    source = (inspect.getsource(dry_run_module) + "\n" + inspect.getsource(models_module)).lower()
    forbidden_terms = (
        "requests.",
        "httpx.",
        "urllib.request",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "create_order(",
        "post_order(",
        "submit_order(",
        "place_order(",
        "send_order(",
        "execute_order(",
        "cancel_order(",
        "delete_order(",
        "submit_cancel(",
        "cancel_all_orders(",
        "sign_order(",
        "sign_payload(",
        "create_signed_order(",
        "generate_signed_payload(",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_artifacts_have_no_fake_order_tx_fill_balance_position_or_pnl_keys(tmp_path: Path) -> None:
    build_signed_order_payload_dry_run(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    paths = signed_order_payload_dry_run_artifact_paths(tmp_path)
    artifact_keys = {key for payload in _artifact_payloads(paths) for key in _walk_keys(payload)}
    artifact_text = _artifact_text(paths)

    assert not (artifact_keys & EXECUTION_ARTIFACT_KEYS)
    for fake in FAKE_EXECUTION_VALUES:
        assert fake not in artifact_text


def test_runner_works_in_default_dry_run_without_secrets(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signed_order_payload_dry_run",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = signed_order_payload_dry_run_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Signed order payload dry-run 070A completed." in completed.stdout
    assert "Local signing diagnostic status: diagnostic_not_requested" in completed.stdout
    assert "Private key read: false" in completed.stdout
    assert "Local payload signing attempted: false" in completed.stdout
    assert "Signed payload submit enabled: false" in completed.stdout
    assert "Order submission enabled: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert result["local_signing_diagnostic_status"] == LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED
    assert result["private_key_read"] is False
    _assert_required_false_flags(result)


def test_runner_requires_dry_run_and_rejects_submit_cancel_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signed_order_payload_dry_run",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--artifacts-dir",
            str(tmp_path / "missing_dry_run"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signed_order_payload_dry_run",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--submit",
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert missing_dry_run.returncode != 0
    assert "requires --dry-run" in missing_dry_run.stderr
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/order flag" in forbidden.stderr


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

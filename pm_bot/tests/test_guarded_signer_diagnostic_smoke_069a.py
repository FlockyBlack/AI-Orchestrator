from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator, Mapping

from pm_bot.trading_core.guarded_signer_diagnostic_models import REQUIRED_FALSE_FLAGS
from pm_bot.trading_core.guarded_signer_diagnostic_smoke import (
    DIAGNOSTIC_CHALLENGE,
    DependencyMissingError,
    diagnostic_challenge_is_order_payload_safe,
    guarded_signer_diagnostic_artifact_paths,
    run_guarded_signer_diagnostic_smoke,
)
import pm_bot.trading_core.guarded_signer_diagnostic_models as models_module
import pm_bot.trading_core.guarded_signer_diagnostic_smoke as smoke_module

GENERATED_AT = "2026-05-15T00:00:00+04:00"

VALID_KEY = "0x" + "2" * 64
EXPECTED_ADDRESS = "0x1111111111111111111111111111111111111111"
MISMATCH_ADDRESS = "0x2222222222222222222222222222222222222222"
FAKE_SIGNATURE = "0x" + "aa" * 65

RUNTIME_FILES = (
    Path("pm_bot/trading_core/guarded_signer_diagnostic_models.py"),
    Path("pm_bot/trading_core/guarded_signer_diagnostic_smoke.py"),
    Path("pm_bot/operator_runner/guarded_signer_diagnostic_smoke.py"),
)

FAKE_SECRET_VALUES = (
    VALID_KEY,
    "api-marker-069a",
    "phrase-marker-069a",
    FAKE_SIGNATURE,
)

EXECUTION_ARTIFACT_KEYS = (
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill_id",
    "fill_price",
    "filled_size",
    "balance",
    "balances",
    "position",
    "positions",
    "pnl",
    "realized_pnl",
    "unrealized_pnl",
)


class RaisingEnv(Mapping[str, str]):
    def __getitem__(self, key: str) -> str:
        raise AssertionError(f"unexpected environment read: {key}")

    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def get(self, key: str, default: Any = None) -> Any:
        raise AssertionError(f"unexpected environment read: {key}")


class FakeSignerAdapter:
    def __init__(self, derived_address: str = EXPECTED_ADDRESS, signature: str = FAKE_SIGNATURE) -> None:
        self.derived_address = derived_address
        self.signature = signature
        self.derive_calls = 0
        self.sign_calls = 0

    def derive_address(self, key_value: str) -> str:
        self.derive_calls += 1
        assert key_value == VALID_KEY
        return self.derived_address

    def sign_diagnostic_challenge(self, key_value: str, challenge: str) -> str:
        self.sign_calls += 1
        assert key_value == VALID_KEY
        assert challenge == DIAGNOSTIC_CHALLENGE
        return self.signature


class MissingDependencyAdapter:
    def derive_address(self, key_value: str) -> str:
        raise DependencyMissingError("eth-account missing")

    def sign_diagnostic_challenge(self, key_value: str, challenge: str) -> str:
        raise DependencyMissingError("eth-account missing")


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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def test_default_dry_run_does_not_read_polymarket_private_key(tmp_path: Path) -> None:
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=False,
        artifact_dir=tmp_path,
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "blocked_diagnostic_not_requested"
    assert result["diagnostic_status"] == "diagnostic_not_requested"
    assert result["diagnostic_requested"] is False
    assert result["private_key_read"] is False
    assert result["private_key_present"] is False
    assert result["derived_wallet_matches_expected"] == "unknown"
    assert result["diagnostic_challenge_signed"] is False
    assert result["allowed_for_live"] is False
    _assert_required_false_flags(result)


def test_explicit_flag_is_required_before_key_read_path(tmp_path: Path) -> None:
    env = {
        "POLYMARKET_PRIVATE_KEY": VALID_KEY,
        "POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS,
    }
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=False,
        artifact_dir=tmp_path,
        env=env,
        generated_at=GENERATED_AT,
    )
    paths = guarded_signer_diagnostic_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)

    assert result["private_key_read"] is False
    assert result["private_key_present"] is False
    assert VALID_KEY not in artifact_text
    assert EXPECTED_ADDRESS not in artifact_text


def test_missing_private_key_reports_blocked(tmp_path: Path) -> None:
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={"POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS},
        account_adapter=FakeSignerAdapter(),
        generated_at=GENERATED_AT,
    )

    assert result["diagnostic_status"] == "missing_private_key"
    assert result["status"] == "blocked_missing_private_key"
    assert result["private_key_read"] is True
    assert result["private_key_present"] is False
    assert result["diagnostic_challenge_signed"] is False
    _assert_required_false_flags(result)


def test_invalid_private_key_reports_blocked_without_dependency_call(tmp_path: Path) -> None:
    adapter = FakeSignerAdapter()
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={
            "POLYMARKET_PRIVATE_KEY": "not-a-valid-key",
            "POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS,
        },
        account_adapter=adapter,
        generated_at=GENERATED_AT,
    )

    assert result["diagnostic_status"] == "invalid_key_format"
    assert result["status"] == "blocked_invalid_key_format"
    assert result["private_key_present"] is True
    assert result["private_key_format_valid"] is False
    assert adapter.derive_calls == 0
    assert adapter.sign_calls == 0
    _assert_required_false_flags(result)


def test_wallet_address_missing_reports_blocked_or_unknown_safely(tmp_path: Path) -> None:
    adapter = FakeSignerAdapter()
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={"POLYMARKET_PRIVATE_KEY": VALID_KEY},
        account_adapter=adapter,
        generated_at=GENERATED_AT,
    )

    assert result["diagnostic_status"] == "missing_wallet_address"
    assert result["status"] == "blocked_missing_wallet_address"
    assert result["wallet_address_present"] is False
    assert result["derived_wallet_matches_expected"] == "unknown"
    assert result["diagnostic_challenge_signed"] is False
    assert adapter.derive_calls == 0
    assert adapter.sign_calls == 0
    _assert_required_false_flags(result)


def test_dependency_missing_fails_closed(tmp_path: Path) -> None:
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={
            "POLYMARKET_PRIVATE_KEY": VALID_KEY,
            "POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS,
        },
        account_adapter=MissingDependencyAdapter(),
        generated_at=GENERATED_AT,
    )

    assert result["diagnostic_status"] == "dependency_missing"
    assert result["status"] == "blocked_dependency_missing"
    assert result["dependency_status"] == "dependency_missing"
    assert result["diagnostic_challenge_signed"] is False
    _assert_required_false_flags(result)


def test_derived_wallet_mismatch_reports_blocked_without_signing(tmp_path: Path) -> None:
    adapter = FakeSignerAdapter(derived_address=MISMATCH_ADDRESS)
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={
            "POLYMARKET_PRIVATE_KEY": VALID_KEY,
            "POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS,
        },
        account_adapter=adapter,
        generated_at=GENERATED_AT,
    )

    assert result["diagnostic_status"] == "wallet_mismatch"
    assert result["status"] == "blocked_wallet_mismatch"
    assert result["derived_wallet_matches_expected"] is False
    assert result["derived_wallet_address_redacted"] == "0x2222...2222"
    assert result["diagnostic_challenge_signed"] is False
    assert adapter.derive_calls == 1
    assert adapter.sign_calls == 0
    _assert_required_false_flags(result)


def test_diagnostic_success_remains_not_allowed_for_live(tmp_path: Path) -> None:
    adapter = FakeSignerAdapter()
    result = run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={
            "POLYMARKET_PRIVATE_KEY": VALID_KEY,
            "POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS,
        },
        account_adapter=adapter,
        generated_at=GENERATED_AT,
    )

    assert result["diagnostic_status"] == "diagnostic_ok"
    assert result["status"] == "diagnostic_ok"
    assert result["signer_diagnostic_executable"] is True
    assert result["private_key_read"] is True
    assert result["private_key_format_valid"] is True
    assert result["derived_wallet_matches_expected"] is True
    assert result["diagnostic_challenge_signed"] is True
    assert result["diagnostic_signature_redacted"].startswith("redacted:sha256:")
    assert result["allowed_for_live"] is False
    assert result["order_payload_signing_enabled"] is False
    assert result["signed_order_generation_enabled"] is False
    assert result["order_submission_enabled"] is False
    assert result["order_cancel_enabled"] is False
    assert result["authenticated_trading_enabled"] is False
    assert adapter.derive_calls == 1
    assert adapter.sign_calls == 1
    _assert_required_false_flags(result)


def test_diagnostic_challenge_cannot_contain_order_payload_fields() -> None:
    assert diagnostic_challenge_is_order_payload_safe(DIAGNOSTIC_CHALLENGE) is True
    assert diagnostic_challenge_is_order_payload_safe('{"price":"1","size":"1","side":"BUY"}') is False
    assert diagnostic_challenge_is_order_payload_safe("PMBOT_SIGNER_DIAGNOSTIC_ONLY_NO_ORDER_NO_SUBMIT:price") is False


def test_artifacts_redact_sensitive_fields(tmp_path: Path) -> None:
    run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path,
        env={
            "POLYMARKET_PRIVATE_KEY": VALID_KEY,
            "POLYMARKET_WALLET_ADDRESS": EXPECTED_ADDRESS,
            "POLYMARKET_API_SECRET": "api-marker-069a",
            "POLYMARKET_API_PASSPHRASE": "phrase-marker-069a",
        },
        account_adapter=FakeSignerAdapter(signature=FAKE_SIGNATURE),
        generated_at=GENERATED_AT,
    )
    paths = guarded_signer_diagnostic_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert result["private_key_value_emitted"] is False
    assert result["raw_secret_values_emitted"] is False
    assert result["full_diagnostic_signature_emitted"] is False
    assert result["expected_wallet_address_redacted"] == "0x1111...1111"
    assert result["derived_wallet_address_redacted"] == "0x1111...1111"
    assert DIAGNOSTIC_CHALLENGE not in artifact_text
    assert EXPECTED_ADDRESS not in artifact_text
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text
    _assert_required_false_flags(result)


def test_runner_works_in_default_dry_run_without_secrets(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.guarded_signer_diagnostic_smoke",
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
    paths = guarded_signer_diagnostic_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Guarded signer diagnostic smoke 069A completed." in completed.stdout
    assert "Diagnostic requested: false" in completed.stdout
    assert "Private key read: false" in completed.stdout
    assert "Derived wallet match: unknown" in completed.stdout
    assert "Diagnostic challenge signed: false" in completed.stdout
    assert "Order payload signing: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Live trading: blocked" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert result["diagnostic_status"] == "diagnostic_not_requested"
    assert result["private_key_read"] is False
    _assert_required_false_flags(result)


def test_no_post_put_patch_delete_trading_endpoint_code() -> None:
    source = (inspect.getsource(smoke_module) + "\n" + inspect.getsource(models_module)).lower()
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


def test_no_order_ids_tx_hashes_fills_balances_positions_or_pnl_artifacts(tmp_path: Path) -> None:
    run_guarded_signer_diagnostic_smoke(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=False,
        artifact_dir=tmp_path,
        env=RaisingEnv(),
        generated_at=GENERATED_AT,
    )
    paths = guarded_signer_diagnostic_artifact_paths(tmp_path)
    artifact_payloads = [
        json.loads(path.read_text(encoding="utf-8"))
        for key, path in paths.items()
        if key != "root" and path.suffix == ".json"
    ]
    artifact_keys = {key for payload in artifact_payloads for key in _walk_keys(payload)}

    assert not (artifact_keys & set(EXECUTION_ARTIFACT_KEYS))


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

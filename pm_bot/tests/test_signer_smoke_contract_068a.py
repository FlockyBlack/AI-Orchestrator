from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.signer_smoke_contract import (
    build_signer_smoke_contract,
    signer_smoke_contract_artifact_paths,
)
import pm_bot.trading_core.signer_smoke_contract as contract_module
import pm_bot.trading_core.signer_smoke_contract_models as models_module
from pm_bot.trading_core.signer_smoke_contract_models import (
    REQUIRED_FALSE_FLAGS,
    FutureSignerSmokeContract,
    SignerSmokeRedactionPolicy,
    SignerSmokeSafetyContract,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

RUNTIME_FILES = (
    Path("pm_bot/trading_core/signer_smoke_contract_models.py"),
    Path("pm_bot/trading_core/signer_smoke_contract.py"),
    Path("pm_bot/operator_runner/signer_smoke_contract.py"),
)

REQUIRED_ARTIFACT_NAMES = {
    "signer_smoke_contract_068a_result.json",
    "latest_signer_smoke_contract_status_068a.json",
    "signer_smoke_safety_contract_068a.json",
    "signer_smoke_redaction_policy_068a.json",
    "signer_smoke_operator_summary_068a.md",
}

FAKE_SECRET_VALUES = (
    "fake-private-key-068a",
    "fake-seed-phrase-068a",
    "fake-mnemonic-068a",
    "fake-api-secret-068a",
    "fake-auth-token-068a",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "private_key",
    "seed_phrase",
    "mnemonic",
    "api_secret",
    "auth_token",
    "passphrase",
    "secret",
    "raw_value",
    "masked_value",
    "signature",
    "signed_payload",
    "signed_order",
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill_id",
    "fill_price",
    "filled_size",
    "execution_status",
    "balance",
    "balances",
    "position",
    "positions",
    "pnl",
    "realized_pnl",
    "unrealized_pnl",
}


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


def test_default_contract_writes_required_artifacts_and_false_flags(tmp_path: Path) -> None:
    result = build_signer_smoke_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    second = build_signer_smoke_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = signer_smoke_contract_artifact_paths(tmp_path)

    assert result == second
    assert result["status"] == "blocked_contract_only_no_signer_smoke_execution"
    assert result["validation"]["valid"] is True
    assert result["signer_smoke_executable"] is False
    assert result["allowed_for_live"] is False
    assert result["order_payload_signing_enabled"] is False
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)


def test_contract_documents_future_checks_without_enabling_them(tmp_path: Path) -> None:
    result = build_signer_smoke_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    future_contract = result["future_signer_smoke_contract"]
    checks = {
        str(row["check_id"]): row
        for row in future_contract["future_allowed_diagnostic_checks"]
        if isinstance(row, Mapping)
    }

    assert future_contract["future_mode_documented"] is True
    assert future_contract["future_mode_enabled"] is False
    assert future_contract["future_credential_source_marker"] == "POLYMARKET_PRIVATE_KEY"
    assert checks["address_derivation"]["future_may_verify"] is True
    assert checks["address_derivation"]["currently_enabled"] is False
    assert checks["address_derivation"]["uses_order_payload"] is False
    assert checks["diagnostic_challenge_signing"]["future_may_verify"] is True
    assert checks["diagnostic_challenge_signing"]["currently_enabled"] is False
    assert checks["diagnostic_challenge_signing"]["uses_order_payload"] is False
    assert result["address_derivation_performed"] is False
    assert result["diagnostic_challenge_signing_attempted"] is False
    assert result["diagnostic_challenge_signed"] is False
    assert result["order_payload_signed"] is False


def test_artifacts_exclude_secret_values_signed_material_orders_and_execution_keys(tmp_path: Path) -> None:
    result = build_signer_smoke_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = signer_smoke_contract_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)
    keys = set(_walk_keys(result))

    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)
    assert result["redaction_policy"]["redaction_policy_exists"] is True
    assert result["redaction_policy"]["credential_value_output_allowed"] is False
    assert result["redaction_policy"]["derived_address_output_allowed"] is False
    assert result["redaction_policy"]["diagnostic_challenge_output_allowed"] is False
    assert result["redaction_policy"]["order_payload_output_allowed"] is False
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text


def test_cli_default_dry_run_does_not_read_private_key_or_emit_fake_values(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_smoke_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "POLYMARKET_PRIVATE_KEY": FAKE_SECRET_VALUES[0],
                "SEED_PHRASE": FAKE_SECRET_VALUES[1],
                "MNEMONIC": FAKE_SECRET_VALUES[2],
                "POLYMARKET_API_SECRET": FAKE_SECRET_VALUES[3],
                "POLYMARKET_AUTH_TOKEN": FAKE_SECRET_VALUES[4],
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = signer_smoke_contract_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Signer smoke contract 068A completed." in completed.stdout
    assert "Signer smoke executable: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Private key read: false" in completed.stdout
    assert "Order payload signing: disabled" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert result["private_key_read"] is False
    assert result["polymarket_private_key_read"] is False
    for fake in FAKE_SECRET_VALUES:
        assert fake not in completed.stdout
        assert fake not in completed.stderr
        assert fake not in artifact_text


def test_cli_explicit_dry_run_and_forbidden_runtime_flags(tmp_path: Path) -> None:
    explicit_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_smoke_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "explicit"),
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
            "pm_bot.operator_runner.signer_smoke_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--private-key",
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert explicit_dry_run.returncode == 0, explicit_dry_run.stderr
    assert "Signer smoke contract 068A completed." in explicit_dry_run.stdout
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/signing/order flag" in forbidden.stderr


def test_no_signer_wallet_order_or_endpoint_code_exists() -> None:
    source = (inspect.getsource(contract_module) + "\n" + inspect.getsource(models_module)).lower()
    forbidden_terms = (
        "os.environ",
        "getenv",
        "environ[",
        ".sign(",
        "sign_typed_data",
        "eip712",
        "eth_account",
        "web3",
        "account.from_key",
        "sign_order(",
        "sign_payload(",
        "generate_signed_payload(",
        "create_signed_order(",
        "derive_api_key(",
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
        "requests.",
        "httpx.",
        "urllib.request",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_contract_classes_do_not_define_executable_methods() -> None:
    contract_classes = (
        FutureSignerSmokeContract,
        SignerSmokeSafetyContract,
        SignerSmokeRedactionPolicy,
    )
    forbidden_method_fragments = (
        "sign",
        "submit",
        "cancel",
        "post",
        "put",
        "patch",
        "delete",
        "derive",
        "wallet",
    )

    for cls in contract_classes:
        method_names = {
            name
            for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
            if not name.startswith("__")
        }
        assert method_names == {"to_dict"}
        for method_name in method_names:
            assert not any(fragment in method_name.lower() for fragment in forbidden_method_fragments)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

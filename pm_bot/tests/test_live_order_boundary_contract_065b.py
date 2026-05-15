from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.live_order_boundary_contract import (
    build_live_order_boundary_contract,
    live_order_boundary_contract_artifact_paths,
)
import pm_bot.trading_core.live_order_boundary_contract as contract_module
import pm_bot.trading_core.live_order_boundary_models as models_module
from pm_bot.trading_core.live_order_boundary_models import (
    REQUIRED_FALSE_FLAGS,
    FutureLiveOrderBoundaryChecklist,
    NonExecutableOrderCancelBoundary,
    NonExecutableOrderSubmissionBoundary,
    NonExecutableSignerBoundary,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

RUNTIME_FILES = (
    Path("pm_bot/trading_core/live_order_boundary_models.py"),
    Path("pm_bot/trading_core/live_order_boundary_contract.py"),
    Path("pm_bot/operator_runner/live_order_boundary_contract.py"),
)

REQUIRED_ARTIFACT_NAMES = {
    "live_order_boundary_contract_065b_result.json",
    "latest_live_order_boundary_contract_status_065b.json",
    "live_order_boundary_safety_contract_065b.json",
    "live_order_redaction_policy_065b.json",
    "live_order_boundary_checklist_065b.json",
    "live_order_non_executable_interfaces_065b.json",
    "live_order_boundary_operator_summary_065b.md",
}

FORBIDDEN_VALUE_KEYS = {
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

FAKE_SECRET_VALUES = (
    "fake-private-key-065b",
    "fake-seed-phrase-065b",
    "fake-mnemonic-065b",
    "fake-api-secret-065b",
    "fake-auth-token-065b",
    "fake-passphrase-065b",
)

FAKE_EXECUTION_VALUES = (
    "fake-order-id-065b",
    "fake-client-order-id-065b",
    "fake-tx-hash-065b",
    "fake-fill-id-065b",
    "fake-balance-065b",
    "fake-position-065b",
    "fake-pnl-065b",
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


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def test_default_contract_writes_required_artifacts_and_false_flags(tmp_path: Path) -> None:
    result = build_live_order_boundary_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    second = build_live_order_boundary_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = live_order_boundary_contract_artifact_paths(tmp_path)

    assert result == second
    assert result["status"] == "blocked_non_executable_boundary_skeleton"
    assert result["validation"]["valid"] is True
    assert result["all_boundaries_non_executable"] is True
    assert result["allowed_for_live"] is False
    assert result["boundary_is_executable"] is False
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)


def test_artifacts_exclude_secret_value_fields_and_fake_execution_values(tmp_path: Path) -> None:
    result = build_live_order_boundary_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = live_order_boundary_contract_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)
    keys = set(_walk_keys(result))

    assert not (keys & FORBIDDEN_VALUE_KEYS)
    assert result["redaction_policy"]["redaction_policy_exists"] is True
    assert result["future_live_order_boundary_checklist"]["checklist_exists"] is True
    for fake in (*FAKE_SECRET_VALUES, *FAKE_EXECUTION_VALUES):
        assert fake not in artifact_text


def test_no_signing_submission_cancel_or_endpoint_code_exists() -> None:
    source = (inspect.getsource(contract_module) + "\n" + inspect.getsource(models_module)).lower()
    forbidden_terms = (
        ".sign(",
        "sign_typed_data",
        "eip712",
        "eth_account",
        "web3",
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


def test_boundary_classes_do_not_define_executable_methods() -> None:
    boundary_classes = (
        NonExecutableSignerBoundary,
        NonExecutableOrderSubmissionBoundary,
        NonExecutableOrderCancelBoundary,
        FutureLiveOrderBoundaryChecklist,
    )
    forbidden_method_fragments = ("sign", "submit", "cancel", "post", "put", "patch", "delete")

    for cls in boundary_classes:
        method_names = {
            name
            for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
            if not name.startswith("__")
        }
        assert method_names == {"to_dict"}
        for method_name in method_names:
            assert not any(fragment in method_name.lower() for fragment in forbidden_method_fragments)


def test_cli_runner_writes_only_artifacts_and_emits_no_secret_values(tmp_path: Path) -> None:
    marker_env = {
        "PRIVATE_KEY": FAKE_SECRET_VALUES[0],
        "SEED_PHRASE": FAKE_SECRET_VALUES[1],
        "MNEMONIC": FAKE_SECRET_VALUES[2],
        "POLYMARKET_API_SECRET": FAKE_SECRET_VALUES[3],
        "POLYMARKET_AUTH_TOKEN": FAKE_SECRET_VALUES[4],
        "POLYMARKET_PASSPHRASE": FAKE_SECRET_VALUES[5],
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_order_boundary_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(marker_env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = live_order_boundary_contract_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Live order boundary contract 065B completed." in completed.stdout
    assert "Boundary executable: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Signer instantiated: false" in completed.stdout
    assert "Credential value read: false" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "Authenticated trading: blocked" in completed.stdout
    assert "Wallet connection: blocked" in completed.stdout
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    for fake in FAKE_SECRET_VALUES:
        assert fake not in completed.stdout
        assert fake not in completed.stderr
        assert fake not in artifact_text


def test_cli_requires_dry_run_and_rejects_forbidden_runtime_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_order_boundary_contract",
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
            "pm_bot.operator_runner.live_order_boundary_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--wallet",
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
    assert "unsupported live/auth/wallet/signing/order flag" in forbidden.stderr


def test_no_post_put_patch_delete_code_in_runtime_files() -> None:
    forbidden_runtime_terms = (
        "requests.post",
        "requests.put",
        "requests.patch",
        "requests.delete",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "method=\"post\"",
        "method=\"put\"",
        "method=\"patch\"",
        "method=\"delete\"",
    )
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_runtime_terms:
            assert term.replace(" ", "") not in lowered, path


def test_committed_default_artifact_payloads_are_safe_after_runner(tmp_path: Path) -> None:
    build_live_order_boundary_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = live_order_boundary_contract_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    latest = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    safety = json.loads(paths["safety_contract"].read_text(encoding="utf-8"))
    redaction = json.loads(paths["redaction_policy"].read_text(encoding="utf-8"))
    checklist = json.loads(paths["checklist"].read_text(encoding="utf-8"))
    interfaces = json.loads(paths["interfaces"].read_text(encoding="utf-8"))

    for payload in (result, latest, safety, redaction, checklist, interfaces):
        assert payload["allowed_for_live"] is False
        assert payload["boundary_is_executable"] is False
        assert payload["signer_boundary_available"] is False
        assert payload["signer_instantiated"] is False
        assert payload["private_key_read"] is False
        assert payload["credential_value_read"] is False
        assert payload["signed_payload_generation_enabled"] is False
        assert payload["order_submission_enabled"] is False
        assert payload["order_cancel_enabled"] is False
        assert payload["authenticated_trading_enabled"] is False
        assert payload["wallet_connection_enabled"] is False
        _assert_required_false_flags(payload)

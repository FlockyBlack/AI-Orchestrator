from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.first_live_order_blocker_matrix import (
    first_live_order_blocker_matrix_artifact_paths,
    run_first_live_order_blocker_matrix,
)
import pm_bot.trading_core.first_live_order_blocker_matrix as matrix_module
import pm_bot.trading_core.first_live_order_blocker_models as matrix_models
from pm_bot.trading_core.first_live_order_blocker_models import (
    FORCED_FALSE_EXECUTION_FIELDS,
    REQUIRED_UNRESOLVED_BLOCKER_IDS,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-065a",
    "fake-seed-phrase-065a",
    "fake-mnemonic-065a",
    "fake-api-secret-065a",
    "fake-auth-token-065a",
    "fake-passphrase-065a",
)

FORBIDDEN_RAW_KEYS = {
    "private_key",
    "seed_phrase",
    "mnemonic",
    "api_secret",
    "api_secret_value",
    "auth_token",
    "passphrase",
    "passphrase_value",
    "secret",
    "raw_secret",
    "raw_value",
    "signature",
    "signed_payload",
    "signed_order",
    "signed_payload_value",
    "signed_order_value",
    "auth_header",
    "authorization_header",
    "raw_request",
    "raw_response",
    "wallet_address",
    "wallet_id",
    "wallet_file",
    "wallet_path",
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
    "profit",
    "realized_pnl",
    "unrealized_pnl",
}

NEW_065A_RUNTIME_FILES = (
    Path("pm_bot/trading_core/first_live_order_blocker_models.py"),
    Path("pm_bot/trading_core/first_live_order_blocker_matrix.py"),
    Path("pm_bot/operator_runner/first_live_order_blocker_matrix.py"),
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
        if Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
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


def _blocker_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row.get("blocker_id")) for row in result.get("blockers", []) if isinstance(row, Mapping)}


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    assert value["preimplementation_only"] is True
    assert value["scaffold_only"] is True
    assert value["non_executable"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["allowed_for_live"] is False
    assert value["candidate_is_executable"] is False
    assert value["operator_approved"] is False
    assert value["resolved_blocker_count"] == 0


def test_default_run_writes_all_required_artifacts_and_flags_false(tmp_path: Path) -> None:
    result = run_first_live_order_blocker_matrix(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    second = run_first_live_order_blocker_matrix(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = first_live_order_blocker_matrix_artifact_paths(tmp_path / "artifacts")

    assert result == second
    assert result["status"] == "blocked_unresolved_first_live_order_preimplementation_matrix"
    assert result["validation"]["valid"] is True
    assert set(REQUIRED_UNRESOLVED_BLOCKER_IDS).issubset(_blocker_ids(result))
    assert result["blocker_count"] == len(REQUIRED_UNRESOLVED_BLOCKER_IDS)
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)
    _assert_required_false_flags(result["latest_status"])
    _assert_required_false_flags(result["blocker_matrix"])


def test_required_blocker_precondition_abort_required_artifact_and_test_plan_sections_exist(tmp_path: Path) -> None:
    result = run_first_live_order_blocker_matrix(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )

    assert result["preconditions"]["preconditions"]
    assert result["preconditions"]["missing_precondition_count"] > 0
    assert result["abort_conditions"]["abort_conditions"]
    assert result["abort_conditions"]["abort_policy"]
    assert result["required_artifacts"]["required_artifacts"]
    assert result["required_artifacts"]["operator_private_material_allowed_in_repo"] is False
    assert result["test_plan"]["test_plan_items"]
    assert result["test_plan"]["real_credentials_required"] is False
    assert result["test_plan"]["network_required"] is False


def test_cli_runs_with_fake_secret_env_values_without_emitting_them(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_blocker_matrix",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "PRIVATE_KEY": FAKE_SECRET_VALUES[0],
                "POLYMARKET_PK": FAKE_SECRET_VALUES[1],
                "POLYGON_WALLET_PRIVATE_KEY": FAKE_SECRET_VALUES[2],
                "POLYMARKET_API_SECRET": FAKE_SECRET_VALUES[3],
                "POLYMARKET_AUTH_TOKEN": FAKE_SECRET_VALUES[4],
                "POLYMARKET_PASSPHRASE": FAKE_SECRET_VALUES[5],
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = first_live_order_blocker_matrix_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "First live order blocker matrix completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Candidate executable: false" in completed.stdout
    assert "Operator approved: false" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "Authenticated trading calls: blocked" in completed.stdout
    assert "Resolved blockers: 0" in completed.stdout
    assert result["validation"]["valid"] is True
    for fake in FAKE_SECRET_VALUES:
        assert fake not in completed.stdout
        assert fake not in completed.stderr
        assert fake not in artifact_text


def test_cli_requires_dry_run_and_rejects_forbidden_runtime_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_blocker_matrix",
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
            "pm_bot.operator_runner.first_live_order_blocker_matrix",
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


def test_artifacts_exclude_signed_wallet_secret_runtime_outcome_and_raw_order_fields(tmp_path: Path) -> None:
    result = run_first_live_order_blocker_matrix(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = first_live_order_blocker_matrix_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths).lower()
    forbidden_fake_values = (
        *FAKE_SECRET_VALUES,
        "fake-signature-065a",
        "fake-signed-payload-065a",
        "fake-order-id-065a",
        "fake-client-order-id-065a",
        "fake-tx-hash-065a",
        "fake-fill-065a",
        "fake-balance-065a",
        "fake-pnl-065a",
        "fake-position-065a",
    )

    for fake in forbidden_fake_values:
        assert fake.lower() not in artifact_text
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_RAW_KEYS)


def test_no_wallet_signing_order_auth_network_or_browser_capability_exists() -> None:
    source = (inspect.getsource(matrix_module) + "\n" + inspect.getsource(matrix_models)).lower()
    forbidden_terms = (
        "polymarket_pk",
        "polygon_wallet_private_key",
        "polymarket_private_key",
        "py_clob_client",
        "clobclient",
        "eth_account",
        "web3",
        "account.from_key",
        "os.environ.get",
        "os.getenv",
        ".sign(",
        "sign_typed_data",
        "eip712",
        "create_order(",
        "post_order(",
        "submit_order(",
        "place_order(",
        "send_order(",
        "cancel_order(",
        "delete_order(",
        "get_balance(",
        "get_balances(",
        "get_position(",
        "get_positions(",
        "get_fill(",
        "get_fills(",
        "get_pnl(",
        "requests.",
        "httpx.",
        "selenium",
        "playwright",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_scheduler_daemon_background_autonomous_loop_or_trading_endpoint_behavior_added() -> None:
    forbidden_runtime_terms = (
        "while true",
        "time.sleep",
        "import threading",
        "import asyncio",
        "sched.",
        "daemon=true",
        "start-process",
        "requests.post",
        "requests.put",
        "requests.patch",
        "requests.delete",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
    )
    for path in NEW_065A_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_runtime_terms:
            assert term.replace(" ", "") not in lowered, path

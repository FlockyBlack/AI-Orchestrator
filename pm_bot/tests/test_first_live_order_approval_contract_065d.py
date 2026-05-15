from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.first_live_order_approval_contract import (
    first_live_order_approval_contract_artifact_paths,
    run_first_live_order_approval_contract,
)
import pm_bot.trading_core.first_live_order_approval_contract as contract_module
import pm_bot.trading_core.first_live_order_approval_models as model_module
from pm_bot.trading_core.first_live_order_approval_models import (
    APPROVAL_TIMEOUT_MINUTES,
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXACT_REQUIRED_APPROVAL_TEXT,
    FORBIDDEN_EXECUTION_PAYLOAD_FIELDS,
    FORBIDDEN_FAKE_EXECUTION_VALUE_TOKENS,
    FORCED_FALSE_APPROVAL_CONTRACT_FIELDS,
    MAX_NOTIONAL_USD,
    MAX_ORDERS_PER_DAY,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

EXPECTED_ARTIFACT_KEYS = {
    "result",
    "latest_status",
    "approval_text",
    "approval_scope",
    "approval_limits",
    "revocation_policy",
    "timeout_policy",
    "audit_template",
    "operator_summary",
}


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


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for nested in value.values():
            strings.extend(_walk_strings(nested))
        return strings
    if isinstance(value, list):
        strings: list[str] = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return strings
    return []


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key != "root" and Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_contract_run_writes_required_artifacts_and_exact_approval_text(tmp_path: Path) -> None:
    result = run_first_live_order_approval_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = first_live_order_approval_contract_artifact_paths(tmp_path / "artifacts")

    assert result["validation"]["valid"] is True
    assert set(paths) == EXPECTED_ARTIFACT_KEYS | {"root"}
    for key in EXPECTED_ARTIFACT_KEYS:
        assert paths[key].exists(), key
    approval_text = json.loads(paths["approval_text"].read_text(encoding="utf-8"))
    assert approval_text["required_approval_text"] == EXACT_REQUIRED_APPROVAL_TEXT
    assert approval_text["required_approval_text"].strip()
    assert result["required_approval_text"]["required_approval_text"] == EXACT_REQUIRED_APPROVAL_TEXT


def test_default_scope_limits_timeout_and_one_shot_semantics(tmp_path: Path) -> None:
    result = run_first_live_order_approval_contract(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    scope = result["approval_scope"]
    limits = result["approval_limits"]
    timeout = result["timeout_policy"]
    revocation = result["revocation_policy"]

    assert scope["allowed_markets"] == [DEFAULT_ALLOWED_MARKET]
    assert scope["allowed_strategies"] == [DEFAULT_ALLOWED_STRATEGY]
    assert scope["requested_market"] == "BTC"
    assert scope["requested_strategy"] == "tiny-momentum"
    assert scope["btc_only"] is True
    assert scope["tiny_momentum_only"] is True
    assert scope["scope_valid"] is True
    assert limits["max_notional_usd"] <= MAX_NOTIONAL_USD
    assert limits["max_orders_per_day"] == MAX_ORDERS_PER_DAY
    assert limits["one_shot_only"] is True
    assert limits["approval_reuse_allowed"] is False
    assert limits["autonomous_repeat_allowed"] is False
    assert timeout["approval_expires"] is True
    assert 0 < timeout["approval_timeout_minutes"] <= APPROVAL_TIMEOUT_MINUTES
    assert timeout["approval_timeout_seconds"] <= APPROVAL_TIMEOUT_MINUTES * 60
    assert revocation["revocable_by_operator"] is True
    assert revocation["revoked_approval_blocks_future_use"] is True
    assert revocation["no_approval_means_no_execution"] is True


def test_contract_is_non_executable_and_not_allowed_for_live(tmp_path: Path) -> None:
    result = run_first_live_order_approval_contract(
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )

    assert result["approval_contract_executable"] is False
    assert result["allowed_for_live"] is False
    assert result["latest_status"]["approval_contract_executable"] is False
    assert result["latest_status"]["allowed_for_live"] is False
    assert result["no_approval_means_no_execution"] is True
    for field in FORCED_FALSE_APPROVAL_CONTRACT_FIELDS:
        assert result[field] is False, field
        assert result["latest_status"][field] is False, field


def test_no_signing_wallet_order_submission_payload_or_raw_secret_fields(tmp_path: Path) -> None:
    result = run_first_live_order_approval_contract(
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = first_live_order_approval_contract_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)
    keys = {key.lower() for key in _walk_keys(result)}

    assert not (keys & FORBIDDEN_EXECUTION_PAYLOAD_FIELDS)
    for key in keys:
        assert "wallet" not in key
        assert "signer" not in key
        assert "signature" not in key
        assert "signed_payload" not in key
        assert "signed_order" not in key
        assert "order_submission" not in key
        assert "submission_payload" not in key
        assert "cancel_payload" not in key
    for token in FORBIDDEN_FAKE_EXECUTION_VALUE_TOKENS:
        assert token not in artifact_text.lower()
    assert "execution_id" not in artifact_text.lower()
    assert "fill_id" not in artifact_text.lower()


def test_no_fake_execution_ids_fills_or_pnl_values(tmp_path: Path) -> None:
    result = run_first_live_order_approval_contract(
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    strings = "\n".join(_walk_strings(result)).lower()

    assert "fake-" not in strings
    assert "execution_id" not in strings
    assert "fill_id" not in strings
    assert "filled_size" not in strings
    assert "realized_pnl" not in strings
    assert "unrealized_pnl" not in strings


def test_no_background_loop_references_as_executable_behavior() -> None:
    source = (inspect.getsource(contract_module) + "\n" + inspect.getsource(model_module)).lower()
    forbidden_executable_patterns = (
        "while true",
        "time.sleep",
        "import threading",
        "import asyncio",
        "sched.",
        "daemon=true",
        "start-process",
        "requests.",
        "httpx.",
        "os.environ",
        "os.getenv",
        "connect_wallet(",
        "wallet_connect(",
        ".sign(",
        "sign_payload(",
        "create_order(",
        "submit_order(",
        "place_order(",
        "send_order(",
        "cancel_order(",
        "delete_order(",
    )

    for pattern in forbidden_executable_patterns:
        assert pattern not in source, pattern


def test_cli_generates_non_executable_contract(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_approval_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "cli_artifacts"),
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = first_live_order_approval_contract_artifact_paths(tmp_path / "cli_artifacts")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "First live order approval contract completed." in completed.stdout
    assert "Approval contract executable: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "No approval means no execution: true" in completed.stdout
    assert result["approval_contract_executable"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True


def test_cli_requires_dry_run_and_rejects_executable_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_approval_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--artifacts-dir",
            str(tmp_path / "missing_dry_run"),
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden_flag = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_approval_contract",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--wallet",
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert missing_dry_run.returncode != 0
    assert "requires --dry-run" in missing_dry_run.stderr
    assert forbidden_flag.returncode != 0
    assert "unsupported live/auth/wallet/signing/order flag" in forbidden_flag.stderr

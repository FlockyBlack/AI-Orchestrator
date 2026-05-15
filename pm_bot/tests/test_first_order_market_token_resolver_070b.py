from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.first_order_market_token_models import REQUIRED_FALSE_FLAGS
from pm_bot.trading_core.first_order_market_token_resolver import (
    first_order_market_token_artifact_paths,
    run_first_order_market_token_resolver,
)
import pm_bot.trading_core.first_order_market_token_models as models_module
import pm_bot.trading_core.first_order_market_token_resolver as resolver_module

GENERATED_AT = "2026-05-15T00:00:00+04:00"
VALID_TOKEN_ID = "1234567890123456789012345678901234567890"
VALID_CONDITION_ID = "0x" + ("a" * 64)

RUNTIME_FILES = (
    Path("pm_bot/trading_core/first_order_market_token_models.py"),
    Path("pm_bot/trading_core/first_order_market_token_resolver.py"),
    Path("pm_bot/operator_runner/first_order_market_token_resolver.py"),
)

REQUIRED_ARTIFACT_NAMES = {
    "first_order_market_token_resolver_070b_result.json",
    "latest_first_order_market_token_status_070b.json",
    "first_order_market_token_contract_070b.json",
    "first_order_market_token_validation_070b.json",
    "first_order_market_token_operator_summary_070b.md",
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


def test_missing_token_id_blocks_without_generating_fake_token(tmp_path: Path) -> None:
    result = run_first_order_market_token_resolver(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    target = result["target_contract"]

    assert result["status"] == "blocked_missing_token_id"
    assert target["status"] == "blocked_missing_token_id"
    assert target["token_id"] == ""
    assert target["outcome_token_id"] == ""
    assert target["token_id_present"] is False
    assert target["token_id_source"] == "missing_explicit_cli"
    assert target["token_id_format_status"] == "missing_required"
    assert target["token_id_generated"] is False
    assert target["fake_token_id_generated"] is False
    assert result["validation"]["valid"] is True
    assert "missing_token_id" in {row["blocker_id"] for row in result["blockers"]}
    _assert_required_false_flags(result)


def test_provided_token_id_market_slug_and_condition_id_are_format_validated(tmp_path: Path) -> None:
    result = run_first_order_market_token_resolver(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        market_slug="bitcoin-up-or-down-may-15-2026",
        condition_id=VALID_CONDITION_ID,
        token_id=VALID_TOKEN_ID,
        outcome_name="Yes",
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    target = result["target_contract"]

    assert result["status"] == "first_order_market_token_contract_ready_review_only"
    assert target["market_slug"] == "bitcoin-up-or-down-may-15-2026"
    assert target["condition_id"] == VALID_CONDITION_ID
    assert target["token_id"] == VALID_TOKEN_ID
    assert target["outcome_token_id"] == VALID_TOKEN_ID
    assert target["outcome_name"] == "Yes"
    assert target["market_slug_format_status"] == "valid"
    assert target["condition_id_format_status"] == "valid"
    assert target["token_id_format_status"] == "valid"
    assert target["token_id_format_valid"] is True
    assert target["token_id_source"] == "explicit_cli"
    assert target["target_contract_only"] is True
    assert target["target_contract_executable"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_no_fake_token_id_is_generated_or_persisted(tmp_path: Path) -> None:
    result = run_first_order_market_token_resolver(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = first_order_market_token_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)

    assert result["target_contract"]["token_id"] == ""
    assert result["token_id_generated"] is False
    assert result["fake_token_id_generated"] is False
    assert "fake-token-id-070b" not in artifact_text
    assert "fake-token-id" not in artifact_text
    assert "placeholder_token_id" not in artifact_text


def test_market_btc_and_strategy_tiny_momentum_scope_is_enforced(tmp_path: Path) -> None:
    wrong_market = run_first_order_market_token_resolver(
        market="ETH",
        strategy="tiny-momentum",
        dry_run=True,
        token_id=VALID_TOKEN_ID,
        artifact_dir=tmp_path / "wrong_market",
        generated_at=GENERATED_AT,
    )
    wrong_strategy = run_first_order_market_token_resolver(
        market="BTC",
        strategy="other-strategy",
        dry_run=True,
        token_id=VALID_TOKEN_ID,
        artifact_dir=tmp_path / "wrong_strategy",
        generated_at=GENERATED_AT,
    )

    assert wrong_market["status"] == "blocked_scope_mismatch"
    assert wrong_market["target_contract"]["scope_valid"] is False
    assert wrong_strategy["status"] == "blocked_scope_mismatch"
    assert wrong_strategy["target_contract"]["scope_valid"] is False


def test_invalid_token_id_format_blocks_target_contract(tmp_path: Path) -> None:
    result = run_first_order_market_token_resolver(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id="fake-token-id",
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "blocked_invalid_token_id"
    assert result["target_contract"]["token_id"] == ""
    assert result["target_contract"]["token_id_format_status"] == "invalid"
    assert result["validation"]["valid"] is True
    assert "invalid_token_id_format" in {row["blocker_id"] for row in result["blockers"]}


def test_allowed_for_live_and_all_execution_flags_remain_false(tmp_path: Path) -> None:
    result = run_first_order_market_token_resolver(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id=VALID_TOKEN_ID,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )

    assert result["allowed_for_live"] is False
    assert result["target_contract"]["allowed_for_live"] is False
    assert result["latest_status"]["allowed_for_live"] is False
    assert result["order_payload_generated"] is False
    assert result["signed_payload_generated"] is False
    assert result["order_submission_attempted"] is False
    assert result["authenticated_request_performed"] is False
    assert result["network_trading_calls_performed"] == 0
    _assert_required_false_flags(result)


def test_no_signing_order_auth_network_or_browser_runtime_calls_exist() -> None:
    source = (inspect.getsource(resolver_module) + "\n" + inspect.getsource(models_module)).lower()
    forbidden_terms = (
        "os.environ",
        "getenv",
        "environ[",
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
        "requests.",
        "httpx.",
        "urllib.request",
        "selenium",
        "playwright",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_runner_emits_required_artifacts_only_and_no_order_object(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_order_market_token_resolver",
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
    paths = first_order_market_token_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    keys = set(_walk_keys(result))

    assert completed.returncode == 0, completed.stderr
    assert "First order market token resolver 070B completed." in completed.stdout
    assert "Status: blocked_missing_token_id" in completed.stdout
    assert "Token id generated: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert not (keys & {"order_id", "client_order_id", "signed_payload", "signed_order"})
    assert result["target_contract_only"] is True
    assert result["order_payload_generated"] is False
    assert result["order_submission_attempted"] is False


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

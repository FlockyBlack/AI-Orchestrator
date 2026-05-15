from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.live_order_ledger_models import (
    FORBIDDEN_ARTIFACT_KEYS,
    FORCED_FALSE_EXECUTION_FIELDS,
)
from pm_bot.trading_core.live_order_ledger_scaffold import (
    live_order_ledger_scaffold_artifact_paths,
    run_live_order_ledger_scaffold,
)
import pm_bot.operator_runner.live_order_ledger_scaffold as runner_module
import pm_bot.trading_core.live_order_ledger_models as models_module
import pm_bot.trading_core.live_order_ledger_scaffold as scaffold_module

GENERATED_AT = "2026-05-15T00:00:00+04:00"

NEW_066_RUNTIME_FILES = (
    Path("pm_bot/trading_core/live_order_ledger_models.py"),
    Path("pm_bot/trading_core/live_order_ledger_scaffold.py"),
    Path("pm_bot/operator_runner/live_order_ledger_scaffold.py"),
)

FAKE_EXECUTION_VALUES = (
    "fake-order-id-066",
    "fake-client-order-id-066",
    "fake-tx-hash-066",
    "fake-fill-066",
    "fake-balance-066",
    "fake-position-066",
    "fake-pnl-066",
    "fake-signature-066",
    "fake-signed-payload-066",
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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    assert value["schema_only"] is True
    assert value["scaffold_only"] is True
    assert value["non_executable"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["authenticated_fetch_enabled"] is False
    assert value["live_order_ledger_executable"] is False
    assert value["allowed_for_live"] is False
    assert value["resolved_blocker_count"] == 0


def test_builder_writes_required_schema_only_artifacts(tmp_path: Path) -> None:
    result = run_live_order_ledger_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = live_order_ledger_scaffold_artifact_paths(tmp_path / "artifacts")

    expected_keys = {
        "result",
        "latest_status",
        "ledger_schema",
        "reconciliation_plan",
        "redaction_policy",
        "failure_ledger_schema",
        "no_fake_execution_policy",
        "operator_md",
    }
    for key in expected_keys:
        assert paths[key].exists(), key

    assert result["validation"]["valid"] is True
    assert result["ledger_schema"]["ledger_rows"] == []
    assert result["ledger_schema"]["record_count"] == 0
    assert result["failure_ledger_schema"]["failure_rows"] == []
    assert result["failure_ledger_schema"]["failure_row_count"] == 0
    assert result["ledger_record_count"] == 0
    assert result["failure_record_count"] == 0
    _assert_required_false_flags(result)
    _assert_required_false_flags(result["latest_status"])


def test_artifacts_contain_no_fake_execution_records_identifiers_or_account_values(tmp_path: Path) -> None:
    result = run_live_order_ledger_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = live_order_ledger_scaffold_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)

    for fake in FAKE_EXECUTION_VALUES:
        assert fake not in artifact_text
    assert "0xabc" not in artifact_text
    assert "submitted" not in result["status"]
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)
    assert result["no_fake_execution_policy"]["fake_execution_values_allowed"] is False
    assert result["no_fake_execution_policy"]["synthetic_runtime_identifiers_allowed"] is False
    assert result["no_fake_execution_policy"]["synthetic_account_values_allowed"] is False


def test_redaction_policy_failure_schema_and_reconciliation_plan_are_review_only(tmp_path: Path) -> None:
    result = run_live_order_ledger_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    redaction = result["redaction_policy"]
    failure_schema = result["failure_ledger_schema"]
    plan = result["reconciliation_plan"]

    assert redaction["redaction_policy_exists"] is True
    assert redaction["redaction_required"] is True
    assert redaction["raw_response_storage_enabled"] is False
    assert redaction["raw_response_persisted"] is False
    assert failure_schema["failure_ledger_schema_exists"] is True
    assert failure_schema["failure_rows"] == []
    assert plan["descriptive_only"] is True
    assert plan["runtime_collection_enabled"] is False
    assert plan["runtime_collection_steps"] == []
    assert all(step["descriptive_only"] is True for step in plan["plan_steps"])
    assert all(step["runtime_action_enabled"] is False for step in plan["plan_steps"])


def test_cli_runner_only_emits_artifacts_and_requires_dry_run(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_order_ledger_scaffold",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "cli_artifacts"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_order_ledger_scaffold",
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
    paths = live_order_ledger_scaffold_artifact_paths(tmp_path / "cli_artifacts")
    produced = sorted(path.name for path in (tmp_path / "cli_artifacts").iterdir())

    assert completed.returncode == 0, completed.stderr
    assert "Live order ledger scaffold completed." in completed.stdout
    assert "Authenticated fetch enabled: false" in completed.stdout
    assert "Live order ledger executable: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Runner effect: artifacts only" in completed.stdout
    assert json.loads(paths["result"].read_text(encoding="utf-8"))["validation"]["valid"] is True
    assert produced == sorted(path.name for key, path in paths.items() if key != "root")
    assert missing_dry_run.returncode != 0
    assert "requires --dry-run" in missing_dry_run.stderr


def test_no_trading_endpoint_wallet_signing_order_or_account_runtime_behavior_exists() -> None:
    source = (
        inspect.getsource(scaffold_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + inspect.getsource(runner_module)
    ).lower()
    forbidden_terms = (
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
        "urllib.",
        "aiohttp.",
        "selenium",
        "playwright",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_mutating_endpoint_scheduler_daemon_background_or_autonomous_loop_added() -> None:
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
    for path in NEW_066_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_runtime_terms:
            assert term.replace(" ", "") not in lowered, path

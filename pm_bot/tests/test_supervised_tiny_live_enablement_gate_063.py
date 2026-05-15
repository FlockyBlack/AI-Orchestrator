from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.supervised_tiny_live_enablement_gate import (
    DEFAULT_READINESS_MARKERS,
    run_supervised_tiny_live_enablement_gate,
    supervised_tiny_live_enablement_gate_artifact_paths,
)
import pm_bot.trading_core.supervised_tiny_live_enablement_gate as gate_module
import pm_bot.trading_core.supervised_tiny_live_enablement_models as gate_models
from pm_bot.trading_core.supervised_tiny_live_enablement_models import (
    FORCED_FALSE_EXECUTION_FIELDS,
    REQUIRED_UNRESOLVED_BLOCKER_IDS,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-063",
    "fake-seed-phrase-063",
    "fake-mnemonic-063",
    "fake-api-secret-063",
    "fake-auth-token-063",
)

FORBIDDEN_ARTIFACT_KEYS = {
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
    "pnl",
    "profit",
    "realized_pnl",
    "unrealized_pnl",
    "position",
    "positions",
    "position_opened",
    "position_closed",
    "signature",
    "signed_payload_value",
    "signed_order_value",
}

NEW_063_RUNTIME_FILES = (
    Path("pm_bot/trading_core/supervised_tiny_live_enablement_models.py"),
    Path("pm_bot/trading_core/supervised_tiny_live_enablement_gate.py"),
    Path("pm_bot/operator_runner/supervised_tiny_live_enablement_gate.py"),
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
    assert value["preparation_only"] is True
    assert value["gate_only"] is True
    assert value["non_executable"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["live_execution_approved"] is False
    assert value["canary_executable_now"] is False
    assert value["real_execution_available"] is False
    assert value["order_submission_enabled"] is False
    assert value["order_cancel_enabled"] is False
    assert value["wallet_signing_enabled"] is False
    assert value["signing_enabled"] is False
    assert value["signed_payload_generation_enabled"] is False
    assert value["signed_order_generation_enabled"] is False
    assert value["authenticated_polymarket_enabled"] is False
    assert value["live_connector_enabled"] is False
    assert value["allowed_for_live"] is False
    assert value["operator_approved"] is False
    assert value["candidate_is_executable"] is False
    assert value["resolved_blocker_count"] == 0


def _run_with_missing_markers(tmp_path: Path) -> dict[str, Any]:
    return run_supervised_tiny_live_enablement_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        readiness_marker_presence={marker: False for marker in DEFAULT_READINESS_MARKERS},
        generated_at=GENERATED_AT,
    )


def test_command_and_model_produce_deterministic_preparation_artifacts(tmp_path: Path) -> None:
    result = _run_with_missing_markers(tmp_path / "artifacts")
    second = _run_with_missing_markers(tmp_path / "artifacts")
    paths = supervised_tiny_live_enablement_gate_artifact_paths(tmp_path / "artifacts")

    assert result == second
    assert result["status"] == "supervised_tiny_live_enablement_prepared_live_blocked"
    assert result["validation"]["valid"] is True
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)


def test_cli_runs_without_private_keys_and_writes_required_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.supervised_tiny_live_enablement_gate",
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
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = supervised_tiny_live_enablement_gate_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Supervised tiny live enablement gate completed." in completed.stdout
    assert "Operator approved: false" in completed.stdout
    assert "Candidate executable: false" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout
    assert "Resolved blockers: 0" in completed.stdout
    assert result["validation"]["valid"] is True
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text


def test_required_blockers_operator_approval_and_candidate_execution_remain_false(tmp_path: Path) -> None:
    result = _run_with_missing_markers(tmp_path / "artifacts")

    assert set(REQUIRED_UNRESOLVED_BLOCKER_IDS).issubset(_blocker_ids(result))
    assert result["resolved_blocker_count"] == 0
    assert result["operator_approved"] is False
    assert result["candidate_is_executable"] is False
    assert result["manual_approval_packet"]["operator_approved"] is False
    assert result["manual_approval_packet"]["approval_required"] is True
    assert result["manual_approval_packet"]["approval_scope"] == "first_tiny_live_order_preparation_only"
    assert result["manual_approval_packet"]["this_packet_is_not_executable"] is True
    assert result["manual_approval_packet"]["later_live_enabling_task_required"] is True
    assert result["manual_approval_packet"]["no_order_can_be_submitted_from_this_packet"] is True
    _assert_required_false_flags(result["latest_status"])
    _assert_required_false_flags(result["readiness_summary"])


def test_no_signing_signer_payload_order_submission_cancel_or_wallet_capability_exists() -> None:
    source = (inspect.getsource(gate_module) + "\n" + inspect.getsource(gate_models)).lower()
    forbidden_terms = (
        "polymarket_pk",
        "polygon_wallet_private_key",
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
        "selenium",
        "playwright",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_risk_limits_are_tiny_and_non_executable(tmp_path: Path) -> None:
    result = _run_with_missing_markers(tmp_path / "artifacts")
    limits = result["risk_limits"]

    assert limits["max_order_notional_usd"] <= 1.0
    assert limits["max_daily_notional_usd"] <= 1.0
    assert limits["max_orders_per_day"] == 1
    assert limits["max_market_count"] == 1
    assert limits["allowed_market"] == "BTC"
    assert limits["allowed_strategy"] == "tiny-momentum"
    assert limits["preparation_constraints_only"] is True
    assert limits["limits_are_executable"] is False
    assert limits["operator_approval_required_for_later_live_task"] is True


def test_kill_cancel_and_failure_plans_exist_and_are_descriptive_only(tmp_path: Path) -> None:
    result = _run_with_missing_markers(tmp_path / "artifacts")

    for key in ("kill_switch_plan", "cancel_plan", "failure_plan"):
        plan = result[key]
        assert plan["plan_is_descriptive_only"] is True
        assert plan["plan_is_executable"] is False
        assert plan["operator_confirmation_required"] is True
    assert result["kill_switch_plan"]["stop_future_live_enablement_steps"]
    assert result["cancel_plan"]["required_before_any_real_order"]
    assert result["failure_plan"]["later_task_failure_steps"]
    assert result["kill_switch_plan"]["kill_switch_plan_executable"] is False
    assert result["cancel_plan"]["cancel_plan_executable"] is False
    assert result["failure_plan"]["failure_plan_executable"] is False


def test_env_readiness_is_redacted_presence_only_and_live_blocking(tmp_path: Path) -> None:
    result = _run_with_missing_markers(tmp_path / "artifacts")
    env_readiness = result["env_readiness"]

    assert env_readiness["env_presence_checked"] is True
    assert env_readiness["presence_only"] is True
    assert env_readiness["values_redacted"] is True
    assert env_readiness["raw_values_emitted"] is False
    assert env_readiness["missing_marker_count"] == len(DEFAULT_READINESS_MARKERS)
    assert env_readiness["all_required_markers_present"] is False
    assert env_readiness["readiness_status"] == "blocked"
    for marker in env_readiness["marker_checks"]:
        assert set(marker) == {"marker_label", "present", "required", "value_redacted", "raw_value_emitted"}
        assert marker["present"] is False
        assert marker["required"] is True
        assert marker["value_redacted"] is True
        assert marker["raw_value_emitted"] is False


def test_artifacts_exclude_fake_execution_identifiers_and_raw_secret_fields(tmp_path: Path) -> None:
    result = _run_with_missing_markers(tmp_path / "artifacts")
    paths = supervised_tiny_live_enablement_gate_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)
    forbidden_fake_values = (
        "fake-private-key-063",
        "fake-signature-063",
        "fake-signed-payload-063",
        "fake-order-id-063",
        "fake-client-order-id-063",
        "fake-tx-hash-063",
        "fake-fill-063",
        "fake-balance-063",
        "fake-pnl-063",
        "fake-position-063",
    )

    for fake in forbidden_fake_values:
        assert fake not in artifact_text
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)
    assert not (keys & {"private_key", "mnemonic", "seed_phrase", "api_secret", "auth_token", "passphrase", "secret"})


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
    for path in NEW_063_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_runtime_terms:
            assert term.replace(" ", "") not in lowered, path

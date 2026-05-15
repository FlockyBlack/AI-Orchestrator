from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.first_live_order_final_blocker_models import (
    FORCED_FALSE_EXECUTION_FIELDS,
    GROUP_IDS,
)
from pm_bot.trading_core.first_live_order_final_blocker_reducer import (
    first_live_order_final_blocker_artifact_paths,
    run_first_live_order_final_blocker_reducer,
)
import pm_bot.trading_core.first_live_order_final_blocker_models as models_module
import pm_bot.trading_core.first_live_order_final_blocker_reducer as reducer_module

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-072d",
    "fake-seed-phrase-072d",
    "fake-api-secret-072d",
    "fake-auth-token-072d",
    "fake-passphrase-072d",
)

RUNTIME_FILES = (
    Path("pm_bot/trading_core/first_live_order_final_blocker_models.py"),
    Path("pm_bot/trading_core/first_live_order_final_blocker_reducer.py"),
    Path("pm_bot/operator_runner/first_live_order_final_blocker_reducer.py"),
)

REQUIRED_ARTIFACT_NAMES = {
    "first_live_order_final_blocker_reducer_072d_result.json",
    "latest_first_live_order_final_blockers_072d.json",
    "first_live_order_blocker_groups_072d.json",
    "first_live_order_next_actions_072d.json",
    "first_live_order_final_blocker_safety_snapshot_072d.json",
    "first_live_order_final_blocker_operator_summary_072d.md",
}

FORBIDDEN_RAW_KEYS = {
    "private_key",
    "seed_phrase",
    "mnemonic",
    "api_secret",
    "api_secret_value",
    "auth_token",
    "passphrase",
    "secret",
    "raw_secret",
    "raw_value",
    "masked_value",
    "signature",
    "signed_payload",
    "signed_order",
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill",
    "fills",
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
        if key != "root" and path.exists():
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


def _assert_forced_false_flags(value: Mapping[str, Any]) -> None:
    assert value["allowed_for_live"] is False
    assert value["resolved_blocker_count"] == 0
    for row in _walk_mappings(value):
        for field in FORCED_FALSE_EXECUTION_FIELDS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def _write_json(path: Path, value: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _safe_artifact(status: str, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "contract_version": "test_commit_safe_artifact.v1",
        "task_id": "test",
        "status": status,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "validation": {"valid": True, "status": "passed"},
    }
    value.update(extra)
    return value


def _complete_input_artifacts(tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "inputs"
    return {
        "order_prep_packet": _write_json(
            root / "order_prep_packet_072a.json",
            _safe_artifact("order_prep_packet_review_ready"),
        ),
        "local_real_check_bundle": _write_json(
            root / "local_real_check_bundle_072c.json",
            _safe_artifact("local_real_check_bundle_review_ready"),
        ),
        "credentials_auth": _write_json(
            root / "credentials_auth_064.json",
            _safe_artifact("credentials_readiness_review_only"),
        ),
        "account_state": _write_json(
            root / "account_state_070c.json",
            _safe_artifact("account_state_probe_succeeded_live_blocked"),
        ),
        "signer_diagnostic": _write_json(
            root / "signer_diagnostic_069a.json",
            _safe_artifact("diagnostic_ok", diagnostic_status="diagnostic_ok"),
        ),
        "token_selection": _write_json(
            root / "token_selection_070b.json",
            _safe_artifact(
                "first_order_market_token_contract_ready_review_only",
                token_id_present=True,
                token_id_format_valid=True,
                token_id_generated=False,
            ),
        ),
        "signed_payload_dry_run": _write_json(
            root / "signed_payload_dry_run_070a.json",
            _safe_artifact(
                "blocked_non_executable_signed_order_payload_dry_run_no_submit",
                signed_payload_generated=False,
                order_payload_contract_executable=False,
            ),
        ),
        "approval_contract": _write_json(
            root / "approval_contract_065d.json",
            _safe_artifact(
                "approval_contract_defined_execution_blocked",
                operator_approval_recorded=False,
            ),
        ),
        "initial_blocker_matrix": _write_json(
            root / "initial_blocker_matrix_065a.json",
            _safe_artifact("blocked_unresolved_first_live_order_preimplementation_matrix"),
        ),
    }


def test_default_run_writes_required_artifacts_and_keeps_live_blocked(tmp_path: Path) -> None:
    result = run_first_live_order_final_blocker_reducer(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    second = run_first_live_order_final_blocker_reducer(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = first_live_order_final_blocker_artifact_paths(tmp_path / "artifacts")

    assert result == second
    assert result["status"] == "blocked_remaining_first_live_order_final_blockers"
    assert result["validation"]["valid"] is True
    assert {row["group_id"] for row in result["groups"]} == set(GROUP_IDS)
    assert result["remaining_blocker_count"] > 0
    assert result["unknown_group_count"] > 0
    assert set(path.name for key, path in paths.items() if key != "root") == REQUIRED_ARTIFACT_NAMES
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_forced_false_flags(result)


def test_complete_commit_safe_input_artifacts_are_consumed_without_fake_live_pass(tmp_path: Path) -> None:
    inputs = _complete_input_artifacts(tmp_path)
    result = run_first_live_order_final_blocker_reducer(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        input_artifact_paths=inputs,
        generated_at=GENERATED_AT,
    )
    blocker_ids = {row["blocker_id"] for row in result["remaining_blockers"]}

    assert result["validation"]["valid"] is True
    assert result["unknown_group_count"] == 0
    assert "token_selection_requires_final_operator_match_check" in blocker_ids
    assert "signer_diagnostic_not_order_payload_authorization" in blocker_ids
    assert "operator_approval_not_recorded" in blocker_ids
    assert "allowed_for_live_false" in blocker_ids
    assert result["allowed_for_live"] is False
    assert result["live_execution_authorized"] is False
    assert all(group["status"] == "blocked_remaining_first_live_order_final_blockers" for group in result["groups"])


def test_missing_order_prep_and_local_real_check_remain_unknown(tmp_path: Path) -> None:
    inputs = _complete_input_artifacts(tmp_path)
    inputs.pop("order_prep_packet")
    inputs.pop("local_real_check_bundle")
    result = run_first_live_order_final_blocker_reducer(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        input_artifact_paths=inputs,
        generated_at=GENERATED_AT,
    )
    blocker_ids = {row["blocker_id"] for row in result["remaining_blockers"]}

    assert result["validation"]["valid"] is True
    assert "order_prep_packet_missing" in blocker_ids
    assert "local_real_check_auth_evidence_unknown" in blocker_ids
    assert "upstream_evidence_unknown" in blocker_ids
    assert "token_selection" in result["unknown_group_ids"]
    assert "live_execution_authorization" in result["unknown_group_ids"]


def test_cli_runs_with_fake_secret_env_values_without_emitting_them(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_final_blocker_reducer",
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
                "POLYMARKET_PRIVATE_KEY": FAKE_SECRET_VALUES[0],
                "SEED_PHRASE": FAKE_SECRET_VALUES[1],
                "POLYMARKET_API_SECRET": FAKE_SECRET_VALUES[2],
                "POLYMARKET_AUTH_TOKEN": FAKE_SECRET_VALUES[3],
                "POLYMARKET_PASSPHRASE": FAKE_SECRET_VALUES[4],
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    artifact_text = _artifact_text(first_live_order_final_blocker_artifact_paths(tmp_path))

    assert completed.returncode == 0, completed.stderr
    assert "First live order final blocker reducer 072D completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Live execution authorization: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    for fake in FAKE_SECRET_VALUES:
        assert fake not in completed.stdout
        assert fake not in completed.stderr
        assert fake not in artifact_text


def test_cli_requires_dry_run_and_rejects_forbidden_runtime_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_live_order_final_blocker_reducer",
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
            "pm_bot.operator_runner.first_live_order_final_blocker_reducer",
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
    assert "unsupported live/auth/wallet/signing/order flag" in forbidden.stderr


def test_artifacts_exclude_raw_secret_execution_and_account_value_fields(tmp_path: Path) -> None:
    result = run_first_live_order_final_blocker_reducer(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        input_artifact_paths=_complete_input_artifacts(tmp_path),
        generated_at=GENERATED_AT,
    )
    artifact_text = _artifact_text(first_live_order_final_blocker_artifact_paths(tmp_path / "artifacts"))
    keys = set(_walk_keys(result))

    assert not (keys & FORBIDDEN_RAW_KEYS)
    assert "fake-order-id-072d" not in artifact_text
    assert "fake-signed-payload-072d" not in artifact_text
    assert "fake-balance-072d" not in artifact_text
    assert "fake-pnl-072d" not in artifact_text


def test_no_sign_submit_cancel_auth_network_env_or_browser_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(reducer_module)
        + "\n"
        + inspect.getsource(models_module)
    ).lower()
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
        "get_balance(",
        "get_balances(",
        "get_position(",
        "get_positions(",
        "requests.",
        "httpx.",
        "urllib.request",
        "selenium",
        "playwright",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

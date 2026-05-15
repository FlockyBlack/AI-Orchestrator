from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator, Mapping

from pm_bot.trading_core.explicit_live_credentials_readiness_gate import (
    explicit_live_credentials_readiness_gate_artifact_paths,
    run_explicit_live_credentials_readiness_gate,
)
import pm_bot.trading_core.explicit_live_credentials_readiness_gate as gate_module
import pm_bot.trading_core.explicit_live_credentials_readiness_models as gate_models
from pm_bot.trading_core.explicit_live_credentials_readiness_models import (
    CREDENTIAL_SOURCE_MARKERS,
    EXECUTION_FLAG_MARKERS,
    FORCED_FALSE_EXECUTION_FIELDS,
    MANUAL_CONTROL_MARKERS,
    REQUIRED_UNRESOLVED_BLOCKER_IDS,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-064",
    "fake-seed-phrase-064",
    "fake-mnemonic-064",
    "fake-api-secret-064",
    "fake-auth-token-064",
    "fake-passphrase-064",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "private_key",
    "seed_phrase",
    "mnemonic",
    "api_secret",
    "api_secret_value",
    "auth_token",
    "passphrase",
    "passphrase_value",
    "secret",
    "raw_value",
    "value_hash",
    "value_prefix",
    "value_suffix",
    "value_length",
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
    "profit",
}

NEW_064_RUNTIME_FILES = (
    Path("pm_bot/trading_core/explicit_live_credentials_readiness_models.py"),
    Path("pm_bot/trading_core/explicit_live_credentials_readiness_gate.py"),
    Path("pm_bot/operator_runner/explicit_live_credentials_readiness_gate.py"),
)


class PresenceOnlyEnviron(Mapping[str, str]):
    def __init__(self, present: set[str]) -> None:
        self.present = set(present)
        self.contains_calls: list[str] = []

    def __contains__(self, key: object) -> bool:
        text = str(key)
        self.contains_calls.append(text)
        return text in self.present

    def __getitem__(self, key: str) -> str:
        raise AssertionError(f"environment value read for {key}")

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("environment iteration attempted")

    def __len__(self) -> int:
        raise AssertionError("environment length read attempted")

    def get(self, key: str, default: Any = None) -> str:
        raise AssertionError(f"environment get attempted for {key}")

    def items(self):  # type: ignore[no-untyped-def]
        raise AssertionError("environment items read attempted")

    def values(self):  # type: ignore[no-untyped-def]
        raise AssertionError("environment values read attempted")


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


def _all_required_present() -> dict[str, bool]:
    return {marker: True for marker in (*CREDENTIAL_SOURCE_MARKERS, *MANUAL_CONTROL_MARKERS)}


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    assert value["preparation_only"] is True
    assert value["gate_only"] is True
    assert value["non_executable"] is True
    assert value["presence_only"] is True
    assert value["presence_booleans_only"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["allowed_for_live"] is False
    assert value["operator_approved"] is False
    assert value["candidate_is_executable"] is False
    assert value["resolved_blocker_count"] == 0


def test_default_run_is_blocked_and_writes_presence_only_artifacts(tmp_path: Path) -> None:
    env = PresenceOnlyEnviron(set())
    result = run_explicit_live_credentials_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        environ=env,
        generated_at=GENERATED_AT,
    )
    second = run_explicit_live_credentials_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        environ=PresenceOnlyEnviron(set()),
        generated_at=GENERATED_AT,
    )
    paths = explicit_live_credentials_readiness_gate_artifact_paths(tmp_path / "artifacts")

    assert result == second
    assert result["status"] == "blocked"
    assert result["validation"]["valid"] is True
    assert set(REQUIRED_UNRESOLVED_BLOCKER_IDS).issubset(_blocker_ids(result))
    assert env.contains_calls
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)
    _assert_required_false_flags(result["latest_status"])
    _assert_required_false_flags(result["readiness_summary"])


def test_presence_checks_use_allowlisted_membership_without_value_reads(tmp_path: Path) -> None:
    present = set(CREDENTIAL_SOURCE_MARKERS) | set(MANUAL_CONTROL_MARKERS)
    env = PresenceOnlyEnviron(present)

    result = run_explicit_live_credentials_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        environ=env,
        generated_at=GENERATED_AT,
    )
    report = result["marker_presence_report"]

    assert set(env.contains_calls) == set(report["marker_label"] for report in report["marker_checks"])
    assert report["all_required_markers_present"] is True
    assert report["execution_flags_absent"] is True
    assert report["missing_required_marker_count"] == 0
    assert report["presence_booleans_only"] is True
    assert report["environment_values_read"] is False
    assert report["environment_values_serialized"] is False
    assert result["status"] == "redacted_presence_review_ready_live_blocked"
    assert result["allowed_for_live"] is False
    assert result["resolved_blocker_count"] == 0


def test_execution_flag_presence_is_conflict_but_value_is_not_read(tmp_path: Path) -> None:
    present = set(CREDENTIAL_SOURCE_MARKERS) | set(MANUAL_CONTROL_MARKERS) | {EXECUTION_FLAG_MARKERS[0]}
    env = PresenceOnlyEnviron(present)

    result = run_explicit_live_credentials_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        environ=env,
        generated_at=GENERATED_AT,
    )
    report = result["marker_presence_report"]

    assert result["status"] == "blocked"
    assert report["present_execution_flag_count"] == 1
    assert report["present_execution_flags"] == [EXECUTION_FLAG_MARKERS[0]]
    assert f"execution_flag_present_blocked:{EXECUTION_FLAG_MARKERS[0]}" in _blocker_ids(result)
    _assert_required_false_flags(result)


def test_cli_runs_with_fake_secret_env_values_without_emitting_them(tmp_path: Path) -> None:
    marker_env = {marker: FAKE_SECRET_VALUES[index % len(FAKE_SECRET_VALUES)] for index, marker in enumerate(CREDENTIAL_SOURCE_MARKERS)}
    marker_env.update({marker: FAKE_SECRET_VALUES[index % len(FAKE_SECRET_VALUES)] for index, marker in enumerate(MANUAL_CONTROL_MARKERS)})
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.explicit_live_credentials_readiness_gate",
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
                **marker_env,
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
    paths = explicit_live_credentials_readiness_gate_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Explicit live credentials readiness gate completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Credential values read: false" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert "Authenticated calls: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout
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
            "pm_bot.operator_runner.explicit_live_credentials_readiness_gate",
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
            "pm_bot.operator_runner.explicit_live_credentials_readiness_gate",
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


def test_artifacts_exclude_fake_execution_identifiers_and_raw_secret_fields(tmp_path: Path) -> None:
    result = run_explicit_live_credentials_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        marker_presence=_all_required_present(),
        generated_at=GENERATED_AT,
    )
    paths = explicit_live_credentials_readiness_gate_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)
    forbidden_fake_values = (
        *FAKE_SECRET_VALUES,
        "fake-signature-064",
        "fake-signed-payload-064",
        "fake-order-id-064",
        "fake-client-order-id-064",
        "fake-tx-hash-064",
        "fake-fill-064",
        "fake-balance-064",
        "fake-pnl-064",
        "fake-position-064",
    )

    for fake in forbidden_fake_values:
        assert fake not in artifact_text
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)


def test_no_wallet_signing_order_auth_network_or_browser_capability_exists() -> None:
    source = (inspect.getsource(gate_module) + "\n" + inspect.getsource(gate_models)).lower()
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
    for path in NEW_064_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_runtime_terms:
            assert term.replace(" ", "") not in lowered, path

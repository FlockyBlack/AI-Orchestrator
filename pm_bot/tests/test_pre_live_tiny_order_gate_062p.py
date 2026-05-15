from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.pre_live_tiny_order_gate import (
    pre_live_tiny_order_gate_artifact_paths,
    run_pre_live_tiny_order_gate,
)
import pm_bot.trading_core.pre_live_tiny_order_gate as gate_module
import pm_bot.trading_core.pre_live_tiny_order_gate_models as gate_models
from pm_bot.trading_core.pre_live_tiny_order_gate_models import FORCED_FALSE_EXECUTION_FIELDS
from pm_bot.trading_core.static_safety_invariant_report import run_static_safety_invariant_report

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-062p",
    "fake-seed-phrase-062p",
    "fake-mnemonic-062p",
    "fake-api-secret-062p",
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
    "pnl",
    "profit",
    "realized_pnl",
    "unrealized_pnl",
    "position_opened",
    "position_closed",
    "signature",
    "signed_payload_value",
}

NEW_062P_RUNTIME_FILES = (
    Path("pm_bot/trading_core/pre_live_tiny_order_gate_models.py"),
    Path("pm_bot/trading_core/pre_live_tiny_order_gate.py"),
    Path("pm_bot/operator_runner/pre_live_tiny_order_gate.py"),
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "tiny": tmp_path / "sources" / "latest_tiny_order_scaffold_status_061.json",
        "signer": tmp_path / "sources" / "latest_signer_boundary_preflight_status_060.json",
        "auth": tmp_path / "sources" / "latest_no_order_auth_get_preflight_status_059.json",
        "safety": tmp_path / "sources" / "latest_static_safety_invariant_report_status_060q.json",
    }


def _write_source_artifacts(tmp_path: Path) -> dict[str, Path]:
    paths = _source_paths(tmp_path)
    _write_json(
        paths["tiny"],
        {
            "contract_version": "pmbot_latest_tiny_order_scaffold_status_061.v1",
            "status": "tiny_order_scaffold_completed_live_blocked",
            "market_symbol": "BTC",
            "market": "BTC",
            "strategy_name": "tiny-momentum",
            "tiny_candidate": "created",
            "approval_packet": "created",
            "approval_packet_created": True,
            "candidate_is_executable": False,
            "operator_approved": False,
            "hard_limits_passed": True,
            "candidate_notional": 0.52,
            "signed_payload_available": False,
            "order_submission_available": False,
            "wallet_available": False,
            "live_execution_approved": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "generated_at": GENERATED_AT,
        },
    )
    _write_json(
        paths["signer"],
        {
            "contract_version": "pmbot_latest_signer_boundary_preflight_status_060.v1",
            "status": "signer_boundary_preflight_completed_live_blocked",
            "market_symbol": "BTC",
            "market": "BTC",
            "strategy_name": "tiny-momentum",
            "live_candidate_intent_status": "created",
            "signer_status": "blocked",
            "signed_payload_status": "unavailable",
            "order_submission_status": "blocked",
            "signer_instantiated": False,
            "signing_attempted": False,
            "signed_payload_available": False,
            "order_submission_available": False,
            "wallet_connection_attempted": False,
            "live_execution_approved": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "generated_at": GENERATED_AT,
        },
    )
    _write_json(
        paths["auth"],
        {
            "contract_version": "pmbot_latest_no_order_authenticated_get_status_059.v1",
            "status": "no_order_auth_get_preflight_mocked_live_blocked",
            "market": "BTC",
            "no_order_auth_get_status": "mocked",
            "request_method": "GET",
            "auth_used": False,
            "real_authenticated_get_performed": False,
            "order_submission_enabled": False,
            "signing_enabled": False,
            "wallet_connection_attempted": False,
            "live_execution_approved": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "generated_at": GENERATED_AT,
        },
    )
    _write_json(
        paths["safety"],
        {
            "contract_version": "pmbot_static_safety_invariant_latest_status_060q.v1",
            "status": "passed",
            "safety_ok": True,
            "critical_count": 0,
            "warning_count": 0,
            "live_execution_approved": False,
            "order_submission_enabled": False,
            "signing_enabled": False,
            "wallet_signing_enabled": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "generated_at": GENERATED_AT,
        },
    )
    return paths


def _patch_source_paths(monkeypatch: Any, paths: Mapping[str, Path] | None = None) -> None:
    missing_root = (next(iter(paths.values())) if paths else Path("missing-source-062p.json")).parent
    missing = missing_root / "missing-source-062p.json"
    paths = dict(paths or {})
    monkeypatch.setattr(gate_module, "DEFAULT_TINY_SCAFFOLD_LATEST_STATUS_061_PATH", paths.get("tiny", missing))
    monkeypatch.setattr(gate_module, "DEFAULT_TINY_SCAFFOLD_RESULT_061_PATH", missing.with_name("missing-tiny-result.json"))
    monkeypatch.setattr(gate_module, "DEFAULT_SIGNER_BOUNDARY_LATEST_STATUS_060_PATH", paths.get("signer", missing))
    monkeypatch.setattr(
        gate_module,
        "DEFAULT_SIGNER_BOUNDARY_RESULT_060_PATH",
        missing.with_name("missing-signer-result.json"),
    )
    monkeypatch.setattr(gate_module, "DEFAULT_AUTH_PREFLIGHT_LATEST_STATUS_059_PATH", paths.get("auth", missing))
    monkeypatch.setattr(
        gate_module,
        "DEFAULT_AUTH_PREFLIGHT_RESULT_059_PATH",
        missing.with_name("missing-auth-result.json"),
    )
    monkeypatch.setattr(
        gate_module,
        "DEFAULT_AUTH_PREFLIGHT_LATEST_STATUS_057_PATH",
        missing.with_name("missing-auth-057.json"),
    )
    monkeypatch.setattr(gate_module, "DEFAULT_SAFETY_SCAN_LATEST_STATUS_060Q_PATH", paths.get("safety", missing))
    monkeypatch.setattr(
        gate_module,
        "DEFAULT_SAFETY_SCAN_RESULT_060Q_PATH",
        missing.with_name("missing-safety-result.json"),
    )


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
    assert value["gate_only"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["live_execution_approved"] is False
    assert value["canary_executable_now"] is False
    assert value["real_execution_available"] is False
    assert value["order_submission_enabled"] is False
    assert value["wallet_signing_enabled"] is False
    assert value["signing_enabled"] is False
    assert value["signed_payload_generation_enabled"] is False
    assert value["signed_order_generation_enabled"] is False
    assert value["authenticated_polymarket_enabled"] is False
    assert value["live_connector_enabled"] is False
    assert value["allowed_for_live"] is False
    assert value["resolved_blocker_count"] == 0


def _blocker_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row.get("blocker_id")) for row in result.get("blockers", []) if isinstance(row, Mapping)}


def _norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def test_cli_runs_without_private_keys_and_writes_review_only_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.pre_live_tiny_order_gate",
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
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = pre_live_tiny_order_gate_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Pre-live tiny order gate completed." in completed.stdout
    assert "Tiny scaffold: present" in completed.stdout
    assert "Operator approved: false" in completed.stdout
    assert "Candidate executable: false" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert "Ready for future live enablement: false" in completed.stdout
    assert result["validation"]["valid"] is True
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text


def test_missing_source_artifacts_write_blockers_and_do_not_crash(tmp_path: Path, monkeypatch: Any) -> None:
    _patch_source_paths(monkeypatch)

    result = run_pre_live_tiny_order_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = pre_live_tiny_order_gate_artifact_paths(tmp_path / "artifacts")

    assert result["status"] == "pre_live_tiny_order_gate_incomplete_missing_source_live_blocked"
    assert {"missing_tiny_scaffold", "missing_signer_boundary", "missing_auth_preflight", "missing_safety_scan"}.issubset(
        _blocker_ids(result)
    )
    assert result["tiny_candidate_present"] is False
    assert result["approval_packet_present"] is False
    assert result["hard_limits_passed"] is False
    assert paths["latest_status"].exists()
    _assert_required_false_flags(result)


def test_latest_sources_are_read_and_paths_are_recorded(tmp_path: Path, monkeypatch: Any) -> None:
    source_paths = _write_source_artifacts(tmp_path)
    _patch_source_paths(monkeypatch, source_paths)

    result = run_pre_live_tiny_order_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )

    assert result["source_tiny_scaffold_path"] == _norm(source_paths["tiny"])
    assert result["source_signer_boundary_path"] == _norm(source_paths["signer"])
    assert result["source_auth_preflight_path"] == _norm(source_paths["auth"])
    assert result["source_safety_scan_path"] == _norm(source_paths["safety"])
    assert result["tiny_candidate_present"] is True
    assert result["approval_packet_present"] is True
    assert result["hard_limits_passed"] is True
    assert result["market_whitelisted"] is True
    assert result["signer_boundary_present"] is True
    _assert_required_false_flags(result)


def test_operator_approval_candidate_execution_and_runtime_boundaries_remain_blockers(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    source_paths = _write_source_artifacts(tmp_path)
    _patch_source_paths(monkeypatch, source_paths)

    result = run_pre_live_tiny_order_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        require_operator_approval=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    blocker_ids = _blocker_ids(result)

    assert result["operator_approved"] is False
    assert result["candidate_is_executable"] is False
    assert result["signing_available"] is False
    assert result["signed_payload_available"] is False
    assert result["order_submission_available"] is False
    assert result["wallet_available"] is False
    assert result["live_execution_approved"] is False
    assert result["ready_for_future_live_enablement"] is False
    assert result["allowed_for_live"] is False
    assert {
        "operator_approved_false",
        "candidate_non_executable",
        "signing_unavailable",
        "signed_payload_unavailable",
        "order_submission_unavailable",
        "wallet_unavailable",
        "live_execution_not_approved",
        "cancel_plan_missing",
        "failure_plan_missing",
        "live_enablement_task_not_present",
    }.issubset(blocker_ids)
    _assert_required_false_flags(result)


def test_no_private_key_signer_signing_order_wallet_or_account_runtime_calls_are_used() -> None:
    source = (
        inspect.getsource(gate_module)
        + "\n"
        + inspect.getsource(gate_models)
    ).lower()
    forbidden_terms = (
        "os.environ",
        "getenv",
        "environ[",
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
        "create_order",
        "post_order",
        "submit_order",
        "cancel_order",
        "get_balance",
        "get_balances",
        "get_position",
        "get_positions",
        "get_fill",
        "get_fills",
        "get_pnl",
        "requests.",
        "httpx.",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_artifacts_exclude_fake_execution_values_and_forbidden_runtime_keys(tmp_path: Path, monkeypatch: Any) -> None:
    source_paths = _write_source_artifacts(tmp_path)
    _patch_source_paths(monkeypatch, source_paths)
    result = run_pre_live_tiny_order_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = pre_live_tiny_order_gate_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)
    forbidden_fake_values = (
        "fake-private-key-062p",
        "fake-signature-062p",
        "fake-signed-payload-062p",
        "fake-order-id-062p",
        "fake-client-order-id-062p",
        "fake-tx-hash-062p",
        "fake-fill-062p",
        "fake-balance-062p",
        "fake-pnl-062p",
        "fake-position-062p",
    )

    for fake in forbidden_fake_values:
        assert fake not in artifact_text
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)


def test_latest_status_operator_markdown_and_readiness_artifacts_are_written(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    source_paths = _write_source_artifacts(tmp_path)
    _patch_source_paths(monkeypatch, source_paths)
    result = run_pre_live_tiny_order_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = pre_live_tiny_order_gate_artifact_paths(tmp_path / "artifacts")
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    markdown = paths["operator_md"].read_text(encoding="utf-8")
    readiness = json.loads(paths["readiness_summary"].read_text(encoding="utf-8"))

    assert latest_status["status"] == result["status"]
    assert latest_status["tiny_scaffold"] == "present"
    assert readiness["ready_for_future_live_enablement"] is False
    assert readiness["blocker_count"] == result["blocker_count"]
    assert "live_enablement_task_not_present" in {
        str(row.get("blocker_id")) for row in readiness.get("blockers", []) if isinstance(row, Mapping)
    }
    assert "## Blockers" in markdown
    assert "operator_approved=false" in markdown
    assert "candidate_is_executable=false" in markdown
    assert "signing blocked" in markdown
    assert "order submission blocked" in markdown
    assert "wallet blocked" in markdown
    assert "live execution blocked" in markdown
    assert "review blockers before any future live-enabling task" in markdown
    _assert_required_false_flags(latest_status)
    _assert_required_false_flags(readiness)


def test_static_safety_scanner_passes_with_critical_zero(tmp_path: Path) -> None:
    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        artifact_dir=tmp_path / "scanner",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] == 0
    assert report["safety_ok"] is True


def test_existing_tiny_signer_and_no_order_commands_still_work(tmp_path: Path) -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.tiny_order_scaffold",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "tiny_order_scaffold_061"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_boundary_preflight",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "signer_boundary_preflight_060"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--no-order-auth-get",
            "--artifacts-dir",
            str(tmp_path / "no_order_auth_get_059"),
        ],
    ]
    outputs = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            env=_minimal_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        outputs.append(completed.stdout)
        assert completed.returncode == 0, completed.stderr

    assert "Tiny order scaffold completed." in outputs[0]
    assert "Signer boundary preflight completed." in outputs[1]
    assert "No-order auth GET: mocked" in outputs[2]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "daemon=true")
    for path in NEW_062P_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_terms:
            assert term.replace(" ", "") not in lowered, path

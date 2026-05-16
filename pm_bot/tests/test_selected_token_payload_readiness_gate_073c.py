from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.selected_token_payload_readiness_gate import (
    run_selected_token_payload_readiness_gate,
    selected_token_payload_readiness_artifact_paths,
)
from pm_bot.trading_core.selected_token_payload_readiness_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT,
    STATUS_BLOCKED_MISSING_SELECTED_TOKEN,
    STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN,
    STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_READY,
)
import pm_bot.operator_runner.selected_token_payload_readiness_gate as runner_module
import pm_bot.trading_core.selected_token_payload_readiness_gate as gate_module
import pm_bot.trading_core.selected_token_payload_readiness_models as models_module

GENERATED_AT = "2026-05-16T00:00:00+04:00"
VALID_TOKEN_ID = "1234567890123456789012345678901234567890"
OTHER_TOKEN_ID = "2234567890123456789012345678901234567890"

REQUIRED_ARTIFACT_NAMES = {
    "selected_token_payload_readiness_gate_073c_result.json",
    "latest_selected_token_payload_readiness_status_073c.json",
    "selected_token_payload_readiness_sources_073c.json",
    "selected_token_payload_readiness_blockers_073c.json",
    "selected_token_payload_readiness_safety_snapshot_073c.json",
    "selected_token_payload_readiness_operator_summary_073c.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/selected_token_payload_readiness_models.py"),
    Path("pm_bot/trading_core/selected_token_payload_readiness_gate.py"),
    Path("pm_bot/operator_runner/selected_token_payload_readiness_gate.py"),
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_selected_candidate_artifact(tmp_path: Path, *, token_id: str = VALID_TOKEN_ID) -> Path:
    return _write_json(
        tmp_path / "sources" / "selected_candidate_artifact_075d.json",
        {
            "contract_version": "pmbot_selected_candidate_artifact_075d.v1",
            "task_id": "ORCH-PMBOT-TRADING-MVP-075D-SELECTED-CANDIDATE-ARTIFACT-CONTRACT-NO-LIVE",
            "status": "selected_candidate_artifact_recorded",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "candidate_index": 0,
            "market_title": "Will BTC close above the local review threshold?",
            "outcome_label": "Yes",
            "token_id_short": "123456...7890",
            "token_id_hash": hashlib.sha256(token_id.encode("utf-8")).hexdigest(),
            "source_backed": True,
            "selected_by_operator": True,
            "selected_candidate_executable_for_live": False,
            "selected_candidate_submit_ready": False,
            "allowed_for_live": False,
            "token_id_generated": False,
            "fake_token_id_generated": False,
            "order_payload_generated": False,
            "signed_payload_generated": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "private_key_read": False,
        },
    )


def _ready_source_paths(
    tmp_path: Path,
    *,
    token_id: str = VALID_TOKEN_ID,
    resolver_token_id: str | None = None,
    verified: bool = True,
    signer_ok: bool = True,
    include_selection: bool = True,
    include_signer: bool = True,
    include_approval: bool = True,
    include_dry_run: bool = True,
    include_adapter: bool = True,
) -> dict[str, Path]:
    source_dir = tmp_path / "sources"
    paths: dict[str, Path] = {}
    resolver_token = resolver_token_id if resolver_token_id is not None else token_id
    token_present = bool(token_id)
    resolver_token_present = bool(resolver_token)

    if include_selection:
        paths["selection"] = _write_json(
            source_dir / "operator_token_selection_packet_073b.json",
            {
                "contract_version": "pmbot_operator_token_selection_packet_073b.v1",
                "status": "operator_token_selection_packet_ready_review_only" if token_present else "blocked_missing_selected_token",
                "market_symbol": "BTC",
                "strategy_name": "tiny-momentum",
                "selected_token_id": token_id,
                "selected_token_verified": verified,
                "token_id_format_status": "valid" if token_present else "missing_required",
                "token_id_format_valid": token_present,
                "token_id_generated": False,
                "fake_token_id_generated": False,
                "order_payload_generated": False,
                "signed_payload_generated": False,
                "order_submission_enabled": False,
                "order_cancellation_enabled": False,
                "private_key_read": False,
                "allowed_for_live": False,
            },
        )
    paths["resolver"] = _write_json(
        source_dir / "first_order_market_token_contract_070b.json",
        {
            "contract_version": "pmbot_first_order_market_token_contract_070b.v1",
            "status": "first_order_market_token_contract_ready_review_only"
            if resolver_token_present
            else "blocked_missing_token_id",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "token_id": resolver_token,
            "outcome_token_id": resolver_token,
            "token_id_present": resolver_token_present,
            "token_id_format_status": "valid" if resolver_token_present else "missing_required",
            "token_id_format_valid": resolver_token_present,
            "token_id_source": "explicit_test_source" if resolver_token_present else "missing_explicit_cli",
            "target_contract_executable": False,
            "token_id_generated": False,
            "fake_token_id_generated": False,
            "order_payload_generated": False,
            "signed_payload_generated": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "private_key_read": False,
            "allowed_for_live": False,
        },
    )
    if include_signer:
        paths["signer"] = _write_json(
            source_dir / "latest_guarded_signer_diagnostic_status_069a.json",
            {
                "contract_version": "pmbot_latest_guarded_signer_diagnostic_status_069a.v1",
                "status": "diagnostic_ok" if signer_ok else "blocked_diagnostic_not_requested",
                "diagnostic_status": "diagnostic_ok" if signer_ok else "diagnostic_not_requested",
                "diagnostic_challenge_signed": signer_ok,
                "private_key_read": signer_ok,
                "order_payload_signing_enabled": False,
                "order_payload_signing_attempted": False,
                "order_submission_enabled": False,
                "order_cancellation_enabled": False,
                "private_key_value_emitted": False,
                "raw_private_key_emitted": False,
                "raw_secret_values_emitted": False,
                "raw_diagnostic_signature_emitted": False,
                "full_diagnostic_signature_emitted": False,
                "authenticated_trading_enabled": False,
                "authenticated_trading_call_performed": False,
                "allowed_for_live": False,
            },
        )
    if include_approval:
        paths["approval"] = _write_json(
            source_dir / "latest_first_live_order_approval_contract_status_065d.json",
            {
                "contract_version": "pmbot_latest_first_live_order_approval_contract_status_065d.v1",
                "status": "approval_contract_defined_execution_blocked",
                "market_symbol": "BTC",
                "strategy_name": "tiny-momentum",
                "definition_only": True,
                "approval_contract_executable": False,
                "contract_can_execute": False,
                "required_approval_text": "STOP - test approval text for one future diagnostic only.",
                "approval_required_before_future_execution": True,
                "no_approval_means_no_execution": True,
                "approval_consumed": False,
                "live_execution_approved": False,
                "real_execution_performed": False,
                "authenticated_trading_calls_made": False,
                "credential_values_read": False,
                "credential_values_serialized": False,
                "fill_or_pnl_recorded": False,
                "scheduler_or_daemon_allowed": False,
                "background_loop_allowed": False,
                "autonomous_repeat_allowed": False,
                "allowed_for_live": False,
            },
        )
    if include_dry_run:
        paths["dry_run"] = _write_json(
            source_dir / "latest_signed_order_payload_dry_run_status_070a.json",
            {
                "contract_version": "pmbot_latest_signed_order_payload_dry_run_status_070a.v1",
                "status": "blocked_non_executable_signed_order_payload_dry_run_no_submit",
                "local_signing_diagnostic_status": "diagnostic_not_requested",
                "payload_contract_fingerprint_sha256": "a" * 64,
                "local_payload_signed": False,
                "local_payload_signing_attempted": False,
                "order_payload_signing_attempted": False,
                "signed_payload_generated": False,
                "signed_payload_submit_enabled": False,
                "signed_payload_submit_attempted": False,
                "signed_payload_submitted": False,
                "order_submission_enabled": False,
                "order_submission_attempted": False,
                "order_cancellation_enabled": False,
                "order_cancellation_attempted": False,
                "network_write_performed": False,
                "network_post_performed": False,
                "network_put_performed": False,
                "network_patch_performed": False,
                "network_delete_performed": False,
                "raw_signed_payload_emitted": False,
                "full_signed_payload_emitted": False,
                "raw_signed_order_emitted": False,
                "full_signed_order_emitted": False,
                "private_key_value_emitted": False,
                "raw_private_key_emitted": False,
                "raw_secret_values_emitted": False,
                "allowed_for_live": False,
            },
        )
    if include_adapter:
        paths["adapter"] = _write_json(
            source_dir / "latest_signed_payload_diagnostic_adapter_status_072e.json",
            {
                "contract_version": "pmbot_latest_signed_payload_diagnostic_adapter_status_072e.v1",
                "status": "blocked_selected_token_candidate_not_ready",
                "allowed_for_live": False,
                "order_payload_signing_attempted": False,
                "signed_payload_generated": False,
                "signed_payload_generation_attempted": False,
                "signed_payload_submit_enabled": False,
                "signed_payload_submit_attempted": False,
                "order_submission_enabled": False,
                "order_cancellation_enabled": False,
                "network_write_performed": False,
                "network_post_performed": False,
                "network_put_performed": False,
                "network_patch_performed": False,
                "network_delete_performed": False,
                "raw_signed_payload_emitted": False,
                "full_signed_payload_emitted": False,
                "private_key_read": False,
                "raw_private_key_emitted": False,
                "raw_secret_values_emitted": False,
            },
        )
    return paths


def _run_gate_with_sources(tmp_path: Path, paths: Mapping[str, Path]) -> dict[str, Any]:
    return run_selected_token_payload_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        selected_candidate_artifact_path=paths.get("selected_candidate", tmp_path / "missing_selected_candidate.json"),
        operator_token_selection_packet_path=paths.get("selection", tmp_path / "missing_selection.json"),
        first_order_market_token_contract_path=paths["resolver"],
        signer_diagnostic_status_path=paths.get("signer", tmp_path / "missing_signer.json"),
        approval_contract_status_path=paths.get("approval", tmp_path / "missing_approval.json"),
        signed_payload_dry_run_status_path=paths.get("dry_run", tmp_path / "missing_dry_run.json"),
        signed_payload_diagnostic_adapter_status_path=paths.get("adapter", tmp_path / "missing_adapter.json"),
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )


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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def _assert_blocker(result: Mapping[str, Any], blocker_id: str) -> None:
    assert blocker_id in {str(row.get("blocker_id")) for row in result["blockers"]}


def test_missing_selected_token_blocks_without_inventing_token(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, token_id="", verified=False)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_MISSING_SELECTED_TOKEN
    assert result["readiness_summaries"]["selected_token"]["selected_token_present"] is False
    assert result["readiness_summaries"]["selected_token"]["selected_token_fingerprint_sha256"] == ""
    assert result["ready_for_signed_payload_diagnostic"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    _assert_blocker(result, "selected_token_missing")
    _assert_required_false_flags(result)


def test_unverified_token_blocks_even_when_token_id_is_present(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, token_id=VALID_TOKEN_ID, verified=False)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    assert result["readiness_summaries"]["selected_token"]["selected_token_present"] is True
    assert result["readiness_summaries"]["selected_token"]["selected_token_verified"] is False
    assert result["ready_for_signed_payload_diagnostic"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    _assert_blocker(result, "selected_token_unverified")
    _assert_required_false_flags(result)


def test_missing_signer_diagnostic_blocks(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, include_signer=False)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC
    assert result["latest_status"]["signer_diagnostic_artifact_available"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    _assert_blocker(result, "signer_diagnostic_missing")
    _assert_required_false_flags(result)


def test_signer_diagnostic_not_ok_blocks(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, signer_ok=False)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    assert result["readiness_summaries"]["signer_diagnostic"]["diagnostic_ok"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    _assert_blocker(result, "signer_diagnostic_not_ok")
    _assert_required_false_flags(result)


def test_missing_approval_contract_blocks(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, include_approval=False)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT
    assert result["latest_status"]["approval_contract_artifact_available"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    _assert_blocker(result, "approval_contract_missing")
    _assert_required_false_flags(result)


def test_missing_signed_payload_dry_run_blocks(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, include_dry_run=False)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN
    assert result["latest_status"]["signed_payload_dry_run_artifact_available"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    _assert_blocker(result, "signed_payload_dry_run_missing")
    _assert_required_false_flags(result)


def test_no_fake_ready_status_on_token_resolver_mismatch(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, token_id=VALID_TOKEN_ID, resolver_token_id=OTHER_TOKEN_ID)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    assert result["status"] != STATUS_READY
    assert result["ready_for_signed_payload_diagnostic"] is False
    assert result["latest_status"]["ready_for_signed_payload_diagnostic"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    _assert_blocker(result, "selected_token_unverified")
    _assert_required_false_flags(result)


def test_all_required_sources_ready_allows_future_diagnostic_but_never_submit(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path)
    result = _run_gate_with_sources(tmp_path, paths)

    assert result["status"] == STATUS_READY
    assert result["ready_for_signed_payload_diagnostic"] is True
    assert result["latest_status"]["ready_for_signed_payload_diagnostic"] is True
    assert result["blocker_count"] == 0
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    assert result["order_submission_enabled"] is False
    assert result["order_cancellation_enabled"] is False
    assert result["trading_write_call_performed"] is False
    assert result["signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_selected_candidate_artifact_supplies_hash_only_selected_token(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path, include_selection=False)
    paths["selected_candidate"] = _write_selected_candidate_artifact(tmp_path)

    result = _run_gate_with_sources(tmp_path, paths)
    selected_token = result["readiness_summaries"]["selected_token"]

    assert result["status"] == STATUS_READY
    assert selected_token["selected_candidate_artifact_available"] is True
    assert selected_token["selected_candidate_artifact_verified"] is True
    assert selected_token["selected_token_present"] is True
    assert selected_token["selected_token_verified"] is True
    assert selected_token["selected_token_fingerprint_sha256"] == hashlib.sha256(
        VALID_TOKEN_ID.encode("utf-8")
    ).hexdigest()
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    _assert_required_false_flags(result)


def test_no_submit_cancel_write_calls_or_signing_by_default_code() -> None:
    source = (
        inspect.getsource(gate_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + inspect.getsource(runner_module)
    ).lower()
    forbidden_terms = (
        "requests.",
        "httpx.",
        "urllib.request",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
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
        "sign_order(",
        "sign_payload(",
        "create_signed_order(",
        "generate_signed_payload(",
        "account.from_key",
        "eth_account",
        "web3",
        "os.environ",
        "os.getenv",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_runner_emits_required_artifacts_only_and_no_execution_objects(tmp_path: Path) -> None:
    paths = _ready_source_paths(tmp_path)
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_token_payload_readiness_gate",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--operator-token-selection-packet-path",
            str(paths["selection"]),
            "--first-order-market-token-contract-path",
            str(paths["resolver"]),
            "--signer-diagnostic-status-path",
            str(paths["signer"]),
            "--approval-contract-status-path",
            str(paths["approval"]),
            "--signed-payload-dry-run-status-path",
            str(paths["dry_run"]),
            "--signed-payload-diagnostic-adapter-status-path",
            str(paths["adapter"]),
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "POLYMARKET_PRIVATE_KEY": "0x" + "9" * 64,
                "POLYMARKET_API_SECRET": "api-secret-marker-073c",
                "POLYMARKET_API_PASSPHRASE": "passphrase-marker-073c",
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    artifact_paths = selected_token_payload_readiness_artifact_paths(out_dir)
    result = json.loads(artifact_paths["result"].read_text(encoding="utf-8"))
    keys = set(_walk_keys(result))

    assert completed.returncode == 0, completed.stderr
    assert "Selected token payload readiness gate 073C completed." in completed.stdout
    assert "Selected token payload ready for submit: false" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "Trading writes: blocked" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert set(p.name for p in out_dir.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert not (keys & {"order_id", "client_order_id", "signed_payload", "signed_order", "tx_hash", "fill", "balance", "pnl"})
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    _assert_required_false_flags(result)


def test_runner_requires_dry_run_and_rejects_submit_cancel_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_token_payload_readiness_gate",
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
            "pm_bot.operator_runner.selected_token_payload_readiness_gate",
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
    assert "unsupported live/auth/wallet/order flag" in forbidden.stderr


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

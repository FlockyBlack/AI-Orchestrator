from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.signer_diagnostic_evidence_bridge as runner_module
import pm_bot.trading_core.signer_diagnostic_evidence_bridge as bridge_module
import pm_bot.trading_core.signer_diagnostic_evidence_models as models_module
from pm_bot.trading_core.selected_token_payload_readiness_gate import run_selected_token_payload_readiness_gate
from pm_bot.trading_core.selected_token_payload_readiness_models import (
    STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY,
)
from pm_bot.trading_core.selected_token_verification_bridge import (
    run_selected_token_verification_bridge,
    selected_token_verification_artifact_paths,
)
from pm_bot.trading_core.signer_diagnostic_evidence_bridge import (
    run_signer_diagnostic_evidence_bridge,
    signer_diagnostic_evidence_artifact_paths,
)
from pm_bot.trading_core.signer_diagnostic_evidence_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED,
    STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_TOKEN_ID = "123456789012345678900761"
FAKE_SECRET = "raw-secret-marker-076c"
FAKE_SIGNED_PAYLOAD = "full-signed-payload-marker-076c"

REQUIRED_ARTIFACT_NAMES = {
    "signer_diagnostic_evidence_076c_result.json",
    "latest_signer_diagnostic_evidence_076c_status.json",
    "signer_diagnostic_evidence_076c_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/signer_diagnostic_evidence_models.py"),
    Path("pm_bot/trading_core/signer_diagnostic_evidence_bridge.py"),
    Path("pm_bot/operator_runner/signer_diagnostic_evidence_bridge.py"),
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


def _write_guarded_signer_source(
    root: Path,
    *,
    ok: bool,
    include_fake_sensitive_values: bool = False,
) -> Path:
    payload: dict[str, Any] = {
        "contract_version": "pmbot_latest_guarded_signer_diagnostic_status_069a.v1",
        "status": "diagnostic_ok" if ok else "blocked_missing_private_key",
        "diagnostic_status": "diagnostic_ok" if ok else "missing_private_key",
        "market_symbol": "BTC",
        "strategy_name": "tiny-momentum",
        "diagnostic_requested": True,
        "diagnostic_challenge_signed": ok,
        "diagnostic_challenge_is_order_payload": False,
        "expected_wallet_address_redacted": "0x1111...1111",
        "derived_wallet_address_redacted": "0x1111...1111" if ok else "not_derived",
        "derived_wallet_matches_expected": True if ok else "unknown",
        "dependency_status": "available" if ok else "not_loaded",
        "block_reason": "live_trading_still_blocked" if ok else "missing_private_key",
        "allowed_for_live": False,
        "order_payload_signing_enabled": False,
        "order_payload_signing_attempted": False,
        "order_payload_signed": False,
        "order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signed_order_generated": False,
        "signed_order_payload_generated": False,
        "signed_payload_generated": False,
        "raw_signed_payload_emitted": False,
        "full_signed_payload_emitted": False,
        "raw_signed_order_emitted": False,
        "full_signed_order_emitted": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "order_cancel_enabled": False,
        "order_cancel_attempted": False,
        "order_cancel_performed": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "authenticated_trading_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "private_key_value_emitted": False,
        "raw_private_key_emitted": False,
        "raw_secret_values_emitted": False,
        "full_diagnostic_signature_emitted": False,
        "raw_diagnostic_signature_emitted": False,
        "diagnostic_challenge_order_payload_fields_present": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
    }
    if include_fake_sensitive_values:
        payload["private_key"] = FAKE_SECRET
        payload["api_secret"] = FAKE_SECRET
        payload["passphrase"] = FAKE_SECRET
        payload["signed_payload"] = FAKE_SIGNED_PAYLOAD
    return _write_json(
        root / "guarded_signer_diagnostic_smoke_069a" / "latest_guarded_signer_diagnostic_status_069a.json",
        payload,
    )


def _write_selected_candidate_artifact(root: Path) -> Path:
    return _write_json(
        root / "selected_candidate_artifact_075d" / "selected_candidate_artifact_075d.json",
        {
            "contract_version": "pmbot_selected_candidate_artifact_075d.v1",
            "status": "selected_candidate_artifact_recorded",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "candidate_index": 0,
            "candidate_id": "candidate-076c-0",
            "market_title": "Will BTC close above the local review threshold?",
            "market_slug": "btc-up-or-down-076c",
            "outcome_label": "Yes",
            "outcome_index": 0,
            "token_id_short": "123456...0761",
            "token_id_hash": hashlib.sha256(RAW_TOKEN_ID.encode("utf-8")).hexdigest(),
            "selected_by_operator": True,
            "source_backed": True,
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


def _write_073b_candidates(root: Path) -> Path:
    return _write_json(
        root / "operator_token_selection_packet_073b" / "operator_token_selection_candidates_073b.json",
        {
            "contract_version": "pmbot_operator_token_selection_candidates_073b.v1",
            "status": "selection_required",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "candidate_index_base": 0,
            "source_backed_candidates": [
                {
                    "candidate_index": 0,
                    "candidate_id": "candidate-076c-0",
                    "market_slug": "btc-up-or-down-076c",
                    "question": "Will BTC close above the local review threshold?",
                    "outcome_name": "Yes",
                    "outcome_index": 0,
                    "token_id": RAW_TOKEN_ID,
                    "source_backed": True,
                    "token_id_source_backed": True,
                    "token_id_generated": False,
                    "fake_token_id_generated": False,
                    "operator_selectable": True,
                    "allowed_for_live": False,
                }
            ],
            "allowed_for_live": False,
            "review_only": True,
            "dry_run_only": True,
        },
    )


def _write_approval_contract(path: Path) -> Path:
    return _write_json(
        path,
        {
            "contract_version": "pmbot_latest_first_live_order_approval_contract_status_065d.v1",
            "status": "approval_contract_defined_execution_blocked",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "definition_only": True,
            "approval_contract_executable": False,
            "contract_can_execute": False,
            "required_approval_text": "STOP - 076C test approval text.",
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


def _write_unready_signed_payload_dry_run(path: Path) -> Path:
    return _write_json(
        path,
        {
            "contract_version": "pmbot_latest_signed_order_payload_dry_run_status_070a.v1",
            "status": "blocked_missing_payload_contract_fingerprint",
            "local_signing_diagnostic_status": "diagnostic_not_requested",
            "payload_contract_fingerprint_sha256": "",
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


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def test_missing_signer_diagnostic_evidence_blocks(tmp_path: Path) -> None:
    result = run_signer_diagnostic_evidence_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing_sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE
    assert result["signer_diagnostic_evidence_ok_for_payload_dry_run"] is False
    assert result["signer_ready_for_live"] is False
    assert result["order_submit_ready"] is False
    assert result["full_signed_payload_output"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_failed_guarded_diagnostic_evidence_blocks_and_does_not_reemit_secrets(tmp_path: Path) -> None:
    source_path = _write_guarded_signer_source(
        tmp_path / "sources",
        ok=False,
        include_fake_sensitive_values=True,
    )
    result = run_signer_diagnostic_evidence_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        guarded_signer_diagnostic_path=source_path,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    artifact_text = _artifact_text(signer_diagnostic_evidence_artifact_paths(tmp_path / "out"))

    assert result["status"] == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED
    assert result["signer_diagnostic_evidence_ok_for_payload_dry_run"] is False
    assert FAKE_SECRET not in artifact_text
    assert FAKE_SIGNED_PAYLOAD not in artifact_text
    assert result["source_guarded_signer_diagnostic"]["source_payload_embedded"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_ok_guarded_diagnostic_evidence_becomes_payload_dry_run_evidence_only(tmp_path: Path) -> None:
    source_path = _write_guarded_signer_source(tmp_path / "sources", ok=True)
    result = run_signer_diagnostic_evidence_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        guarded_signer_diagnostic_path=source_path,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
    assert result["signer_diagnostic_evidence_ok_for_payload_dry_run"] is True
    assert result["evidence_summary"]["source_diagnostic_status"] == "diagnostic_ok"
    assert result["evidence_summary"]["source_safety_flags_ok"] is True
    assert result["signer_ready_for_live"] is False
    assert result["order_submit_ready"] is False
    assert result["full_signed_payload_output"] is False
    assert result["signing_by_default"] is False
    assert result["allowed_for_live"] is False
    assert set(p.name for p in (tmp_path / "out").iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_readiness_gate_consumes_076c_ok_and_moves_beyond_signer_blocker(tmp_path: Path) -> None:
    selected_path = _write_selected_candidate_artifact(tmp_path / "sources")
    selection_path = _write_073b_candidates(tmp_path / "sources")
    verification = run_selected_token_verification_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "verification",
        generated_at=GENERATED_AT,
    )
    signer_source_path = _write_guarded_signer_source(tmp_path / "sources", ok=True)
    signer_evidence = run_signer_diagnostic_evidence_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        guarded_signer_diagnostic_path=signer_source_path,
        artifact_dir=tmp_path / "signer_evidence",
        generated_at=GENERATED_AT,
    )
    approval_path = _write_approval_contract(tmp_path / "sources" / "approval.json")
    dry_run_path = _write_unready_signed_payload_dry_run(tmp_path / "sources" / "dry_run.json")
    result = run_selected_token_payload_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        selected_candidate_artifact_path=selected_path,
        operator_token_selection_packet_path=selection_path,
        selected_token_verification_bridge_path=selected_token_verification_artifact_paths(tmp_path / "verification")["result"],
        first_order_market_token_contract_path=tmp_path / "missing_resolver.json",
        signer_diagnostic_evidence_path=signer_diagnostic_evidence_artifact_paths(tmp_path / "signer_evidence")["result"],
        approval_contract_status_path=approval_path,
        signed_payload_dry_run_status_path=dry_run_path,
        signed_payload_diagnostic_adapter_status_path=tmp_path / "missing_adapter.json",
        artifact_dir=tmp_path / "readiness",
        generated_at=GENERATED_AT,
    )

    assert verification["selected_token_verified_for_payload_dry_run"] is True
    assert signer_evidence["status"] == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
    assert result["status"] == STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY
    assert result["status"] != "blocked_signer_diagnostic_not_ok"
    assert result["latest_status"]["selected_token_verified"] is True
    assert result["latest_status"]["signer_diagnostic_evidence_ok_for_payload_dry_run"] is True
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False


def test_runner_emits_required_artifacts_only_and_rejects_sensitive_diagnostic_flag(tmp_path: Path) -> None:
    source_path = _write_guarded_signer_source(tmp_path / "sources", ok=True)
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_diagnostic_evidence_bridge",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--guarded-signer-diagnostic-path",
            str(source_path),
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        env=_minimal_env({"POLYMARKET_PRIVATE_KEY": FAKE_SECRET, "POLYMARKET_API_SECRET": FAKE_SECRET}),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_diagnostic_evidence_bridge",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--allow-private-key-diagnostic",
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = json.loads(signer_diagnostic_evidence_artifact_paths(out_dir)["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Signer diagnostic evidence bridge 076C completed." in completed.stdout
    assert "Evidence OK for payload dry-run: true" in completed.stdout
    assert "Signer ready for live: false" in completed.stdout
    assert "Order submit ready: false" in completed.stdout
    assert "Full signed payload output: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert FAKE_SECRET not in _artifact_text(signer_diagnostic_evidence_artifact_paths(out_dir))
    assert set(p.name for p in out_dir.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["signer_diagnostic_evidence_ok_for_payload_dry_run"] is True
    assert result["allowed_for_live"] is False
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/sign/order/write/diagnostic flag" in forbidden.stderr
    _assert_required_false_flags(result)


def test_no_network_order_signing_secret_browser_or_background_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(bridge_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + inspect.getsource(runner_module)
    ).lower()
    forbidden_terms = (
        "requests.",
        "httpx.",
        "urllib.request",
        "selenium",
        "playwright",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
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
        "while true",
        "time.sleep",
        "threading",
        "asyncio",
        "sched.",
        "start-process",
        "os.environ",
        "os.getenv",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

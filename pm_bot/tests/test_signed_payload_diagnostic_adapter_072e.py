from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.signed_payload_diagnostic_adapter import (
    run_signed_payload_diagnostic_adapter,
    signed_payload_diagnostic_adapter_artifact_paths,
)
from pm_bot.trading_core.signed_payload_diagnostic_adapter_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED,
    STATUS_BLOCKED_REQUIRED_FIELDS,
    STATUS_BLOCKED_TOKEN_SELECTION,
    STATUS_UNSIGNED_READY,
)
import pm_bot.trading_core.signed_payload_diagnostic_adapter as adapter_module
import pm_bot.trading_core.signed_payload_diagnostic_adapter_models as models_module

GENERATED_AT = "2026-05-15T00:00:00+04:00"
VALID_TOKEN_ID = "1234567890123456789012345678901234567890"
FORBIDDEN_FULL_SIGNED_PAYLOAD_SENTINEL = '{"maker":"0xabc","signature":"0xdeadbeef"}'
FORBIDDEN_SECRET_SENTINELS = (
    "0x" + "3" * 64,
    "api-secret-marker-072e",
    "passphrase-marker-072e",
    FORBIDDEN_FULL_SIGNED_PAYLOAD_SENTINEL,
)
FORBIDDEN_EXECUTION_SENTINELS = (
    "forbidden-execution-identifier-072e",
    "forbidden-transaction-hash-072e",
    "forbidden-fill-marker-072e",
    "forbidden-pnl-marker-072e",
)

REQUIRED_ARTIFACT_NAMES = {
    "signed_payload_diagnostic_adapter_072e_result.json",
    "latest_signed_payload_diagnostic_adapter_status_072e.json",
    "signed_payload_diagnostic_adapter_contract_072e.json",
    "signed_payload_diagnostic_adapter_redaction_policy_072e.json",
    "signed_payload_diagnostic_adapter_safety_snapshot_072e.json",
    "signed_payload_diagnostic_adapter_operator_summary_072e.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/signed_payload_diagnostic_adapter_models.py"),
    Path("pm_bot/trading_core/signed_payload_diagnostic_adapter.py"),
    Path("pm_bot/operator_runner/signed_payload_diagnostic_adapter.py"),
)

EXECUTION_ARTIFACT_KEYS = {
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill_id",
    "fill",
    "fills",
    "balance",
    "balances",
    "position",
    "positions",
    "pnl",
    "realized_pnl",
    "unrealized_pnl",
    "signed_payload",
    "signed_order",
    "signature",
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _source_paths(tmp_path: Path, *, token_id: str = VALID_TOKEN_ID) -> dict[str, Path]:
    source_dir = tmp_path / "sources"
    token_path = _write_json(
        source_dir / "selected_token_candidate.json",
        {
            "contract_version": "pmbot_first_order_market_token_contract_070b.v1",
            "status": "first_order_market_token_contract_ready_review_only",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "token_id": token_id,
            "outcome_token_id": token_id,
            "token_id_present": True,
            "token_id_format_status": "valid",
            "token_id_format_valid": True,
            "token_id_source": "explicit_test_source",
            "target_contract_executable": False,
            "order_payload_generated": False,
            "signed_payload_generated": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "private_key_read": False,
            "allowed_for_live": False,
        },
    )
    order_prep_path = _write_json(
        source_dir / "order_prep_status.json",
        {
            "contract_version": "pmbot_order_prep_status_test.v1",
            "status": "order_prep_unsigned_ready_review_only",
            "market_found": True,
            "token_id_found": True,
            "signature_contract_ready": False,
            "signed_payload_generated": False,
            "signing_attempted": False,
            "order_submission_enabled": False,
            "order_submission_attempted": False,
            "private_key_read": False,
            "allowed_for_live": False,
        },
    )
    signer_path = _write_json(
        source_dir / "signer_status.json",
        {
            "contract_version": "pmbot_latest_guarded_signer_diagnostic_status_069a.v1",
            "status": "blocked_diagnostic_not_requested",
            "diagnostic_status": "diagnostic_not_requested",
            "private_key_read": False,
            "diagnostic_challenge_signed": False,
            "order_payload_signing_enabled": False,
            "order_payload_signing_attempted": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "private_key_value_emitted": False,
            "raw_private_key_emitted": False,
            "raw_secret_values_emitted": False,
            "allowed_for_live": False,
        },
    )
    payload_path = _write_json(
        source_dir / "signed_payload_dry_run_status.json",
        {
            "contract_version": "pmbot_latest_signed_order_payload_dry_run_status_070a.v1",
            "status": "blocked_non_executable_signed_order_payload_dry_run_no_submit",
            "local_signing_diagnostic_status": "diagnostic_not_requested",
            "token_id_present": True,
            "payload_contract_fingerprint_sha256": "0" * 64,
            "order_payload_contract_executable": False,
            "order_payload_signing_attempted": False,
            "signed_payload_generated": False,
            "signed_payload_submit_enabled": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "private_key_read": False,
            "raw_signed_payload_emitted": False,
            "full_signed_payload_emitted": False,
            "allowed_for_live": False,
        },
    )
    return {
        "token": token_path,
        "order_prep": order_prep_path,
        "signer": signer_path,
        "payload": payload_path,
    }


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _artifact_payloads(paths: Mapping[str, Path]) -> list[dict[str, Any]]:
    payloads = []
    for key, path in paths.items():
        if key != "root" and path.suffix == ".json":
            payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


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


def test_default_adapter_reads_local_artifacts_without_signing_or_submit(tmp_path: Path) -> None:
    result = run_signed_payload_diagnostic_adapter(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = signed_payload_diagnostic_adapter_artifact_paths(tmp_path)

    assert result["status"] == STATUS_BLOCKED_TOKEN_SELECTION
    assert result["unsigned_readiness_only"] is True
    assert result["private_key_read"] is False
    assert result["order_payload_signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    assert result["order_submission_enabled"] is False
    assert result["order_cancellation_enabled"] is False
    assert result["trading_write_call_performed"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_required_false_flags(result)


def test_valid_source_artifacts_produce_unsigned_readiness_only(tmp_path: Path) -> None:
    sources = _source_paths(tmp_path)
    result = run_signed_payload_diagnostic_adapter(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_candidate_path=sources["token"],
        order_prep_artifact_path=sources["order_prep"],
        signer_diagnostic_status_path=sources["signer"],
        signed_payload_dry_run_status_path=sources["payload"],
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_UNSIGNED_READY
    assert result["token_candidate_summary"]["selected_token_candidate_ready"] is True
    assert result["token_candidate_summary"]["token_id_present"] is True
    assert result["token_candidate_summary"]["token_id_fingerprint_sha256"]
    assert result["latest_status"]["token_candidate_status"] == "ready"
    assert result["latest_status"]["future_signing_status"] == "not_implemented_blocked"
    assert result["private_key_read"] is False
    assert result["local_payload_signing_attempted"] is False
    assert result["signed_payload_submit_enabled"] is False
    assert result["order_submission_attempted"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_adapter_redacts_token_id_and_signed_material_from_own_artifacts(tmp_path: Path) -> None:
    sources = _source_paths(tmp_path)
    run_signed_payload_diagnostic_adapter(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_candidate_path=sources["token"],
        order_prep_artifact_path=sources["order_prep"],
        signer_diagnostic_status_path=sources["signer"],
        signed_payload_dry_run_status_path=sources["payload"],
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    paths = signed_payload_diagnostic_adapter_artifact_paths(tmp_path / "out")
    artifact_text = _artifact_text(paths)

    assert VALID_TOKEN_ID not in artifact_text
    for sentinel in (*FORBIDDEN_SECRET_SENTINELS, *FORBIDDEN_EXECUTION_SENTINELS):
        assert sentinel not in artifact_text
    assert FORBIDDEN_FULL_SIGNED_PAYLOAD_SENTINEL not in artifact_text


def test_missing_required_source_field_blocks_without_execution_identifiers(tmp_path: Path) -> None:
    sources = _source_paths(tmp_path)
    bad_token_payload = json.loads(sources["token"].read_text(encoding="utf-8"))
    bad_token_payload.pop("status")
    _write_json(sources["token"], bad_token_payload)

    result = run_signed_payload_diagnostic_adapter(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_candidate_path=sources["token"],
        order_prep_artifact_path=sources["order_prep"],
        signer_diagnostic_status_path=sources["signer"],
        signed_payload_dry_run_status_path=sources["payload"],
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    paths = signed_payload_diagnostic_adapter_artifact_paths(tmp_path / "out")
    artifact_keys = {key for payload in _artifact_payloads(paths) for key in _walk_keys(payload)}

    assert result["status"] == STATUS_BLOCKED_REQUIRED_FIELDS
    assert "status" in result["token_candidate_summary"]["missing_required_fields"]
    assert not (artifact_keys & EXECUTION_ARTIFACT_KEYS)
    _assert_required_false_flags(result)


def test_explicit_future_signing_request_is_blocked_not_implemented(tmp_path: Path) -> None:
    sources = _source_paths(tmp_path)
    result = run_signed_payload_diagnostic_adapter(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_candidate_path=sources["token"],
        order_prep_artifact_path=sources["order_prep"],
        signer_diagnostic_status_path=sources["signer"],
        signed_payload_dry_run_status_path=sources["payload"],
        allow_future_signing_diagnostic=True,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED
    assert result["future_signing_requested"] is True
    assert result["future_signing_implemented"] is False
    assert result["private_key_read"] is False
    assert result["order_payload_signing_enabled"] is False
    assert result["order_payload_signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    assert result["order_submission_enabled"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_no_submit_cancel_post_put_patch_or_signing_endpoint_code() -> None:
    source = (inspect.getsource(adapter_module) + "\n" + inspect.getsource(models_module)).lower()
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
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_runner_works_in_default_dry_run_without_secrets(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signed_payload_diagnostic_adapter",
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
                    "POLYMARKET_PRIVATE_KEY": FORBIDDEN_SECRET_SENTINELS[0],
                    "POLYMARKET_API_SECRET": FORBIDDEN_SECRET_SENTINELS[1],
                    "POLYMARKET_API_PASSPHRASE": FORBIDDEN_SECRET_SENTINELS[2],
                    "FULL_SIGNED_PAYLOAD": FORBIDDEN_FULL_SIGNED_PAYLOAD_SENTINEL,
                }
            ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = signed_payload_diagnostic_adapter_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Signed payload diagnostic adapter 072E completed." in completed.stdout
    assert "Unsigned readiness only: true" in completed.stdout
    assert "Private key read: false" in completed.stdout
    assert "Order payload signing attempted: false" in completed.stdout
    assert "Signed payload generated: false" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "Trading writes: blocked" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert result["private_key_read"] is False
    assert result["raw_secret_values_emitted"] is False
    _assert_required_false_flags(result)


def test_runner_requires_dry_run_and_rejects_submit_cancel_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signed_payload_diagnostic_adapter",
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
            "pm_bot.operator_runner.signed_payload_diagnostic_adapter",
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

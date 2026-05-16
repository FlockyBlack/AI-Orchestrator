from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet as runner_module
import pm_bot.trading_core.first_supervised_tiny_order_readiness as packet_module
import pm_bot.trading_core.first_supervised_tiny_order_readiness_models as models_module
from pm_bot.trading_core.first_supervised_tiny_order_readiness import (
    first_supervised_tiny_order_readiness_artifact_paths,
    run_first_supervised_tiny_order_readiness_packet,
)
from pm_bot.trading_core.first_supervised_tiny_order_readiness_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
    STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
    STATUS_BLOCKED_OPERATOR_STOP_REQUESTED,
    STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_RISK_ENGINE_REVIEW,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET,
    validate_first_supervised_tiny_order_readiness_result,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_TOKEN_ID = "12345678901234567890077"
FAKE_SECRET = "raw-secret-marker-077a"
FAKE_SIGNED_PAYLOAD = "full-signed-payload-marker-077a"

REQUIRED_ARTIFACT_NAMES = {
    "latest_first_supervised_tiny_order_readiness_077a_status.json",
    "first_supervised_tiny_order_readiness_077a_result.json",
    "first_supervised_tiny_order_readiness_077a_blockers.json",
    "first_supervised_tiny_order_readiness_077a_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/first_supervised_tiny_order_readiness_models.py"),
    Path("pm_bot/trading_core/first_supervised_tiny_order_readiness.py"),
    Path("pm_bot/operator_runner/first_supervised_tiny_order_readiness_packet.py"),
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


def _write_local_real_check(root: Path) -> None:
    _write_json(
        root / "local_real_check_bundle_072c" / "latest_local_real_check_bundle_status_072c.json",
        {
            "contract_version": "pmbot_latest_local_real_check_bundle_status_072c.v1",
            "status": "local_real_check_bundle_completed_with_blockers_live_blocked",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_selected_candidate(root: Path, *, ready: bool = True) -> None:
    if not ready:
        return
    _write_json(
        root / "selected_candidate_artifact_075d" / "latest_selected_candidate_artifact_075d.json",
        {
            "contract_version": "pmbot_latest_selected_candidate_artifact_075d.v1",
            "status": "selected_candidate_artifact_recorded",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "candidate_index": 0,
            "selected_by_operator": True,
            "source_backed": True,
            "token_id_hash": "f" * 64,
            "token_id_short": "123456...077a",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_selected_token_verification(root: Path, *, verified: bool = True) -> None:
    _write_json(
        root / "selected_token_verification_bridge_076a" / "latest_selected_token_verification_076a_status.json",
        {
            "contract_version": "pmbot_latest_selected_token_verification_bridge_076a_status.v1",
            "status": "selected_token_verified_for_payload_dry_run"
            if verified
            else "blocked_selected_token_not_source_verified",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "selected_token_verified_for_payload_dry_run": verified,
            "token_id_hash": "f" * 64,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_signer_diagnostic(root: Path, *, ok: bool = True) -> None:
    _write_json(
        root / "signer_diagnostic_evidence_bridge_076c" / "latest_signer_diagnostic_evidence_076c_status.json",
        {
            "contract_version": "pmbot_latest_signer_diagnostic_evidence_bridge_076c_status.v1",
            "status": "signer_diagnostic_evidence_ok_for_payload_dry_run"
            if ok
            else "blocked_signer_diagnostic_failed",
            "signer_diagnostic_evidence_status": "signer_diagnostic_evidence_ok_for_payload_dry_run"
            if ok
            else "blocked_signer_diagnostic_failed",
            "source_diagnostic_status": "diagnostic_ok" if ok else "missing_private_key",
            "signer_diagnostic_evidence_ok_for_payload_dry_run": ok,
            "signer_ready_for_live": False,
            "order_submit_ready": False,
            "full_signed_payload_output": False,
            "signing_by_default": False,
            "live": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "signer_instantiated": False,
            "signer_instantiation_attempted": False,
        },
    )


def _write_payload_stack(root: Path, *, ready: bool = True, include_fake_values: bool = False) -> None:
    _write_json(
        root / "payload_dry_run_readiness_076d" / "latest_payload_dry_run_readiness_076d_status.json",
        {
            "contract_version": "pmbot_latest_payload_dry_run_readiness_076d_status.v1",
            "status": "payload_dry_run_ready_for_operator_review"
            if ready
            else "blocked_signed_payload_dry_run_not_ready",
            "payload_dry_run_ready": ready,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "signing_by_default": False,
            "signed_payload_generated": False,
        },
    )
    signed_payload_source = {
        "contract_version": "pmbot_latest_signed_order_payload_dry_run_status_070a.v1",
        "status": "blocked_non_executable_signed_order_payload_dry_run_no_submit",
        "payload_contract_fingerprint_sha256": "a" * 64 if ready else "",
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "order_cancellation_enabled": False,
        "signing_by_default": False,
    }
    if include_fake_values:
        signed_payload_source["signed_payload"] = FAKE_SIGNED_PAYLOAD
        signed_payload_source["private_key"] = FAKE_SECRET
    _write_json(
        root / "signed_order_payload_dry_run_070a" / "latest_signed_order_payload_dry_run_status_070a.json",
        signed_payload_source,
    )


def _write_risk_stack(root: Path, *, ready: bool = True) -> None:
    _write_json(
        root / "risk_engine_v2_074d" / "latest_risk_engine_v2_074d_status.json",
        {
            "contract_version": "pmbot_latest_risk_engine_v2_review_074d.v1",
            "status": "passed_review_check_no_live" if ready else "blocked_risk_engine_v2_review",
            "risk_engine_v2_ready": ready,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root
        / "first_live_order_final_blocker_reducer_072d"
        / "latest_first_live_order_final_blockers_072d.json",
        {
            "contract_version": "pmbot_latest_first_live_order_final_blockers_072d.v1",
            "status": "review_ready_no_live_authorization"
            if ready
            else "blocked_remaining_first_live_order_final_blockers",
            "remaining_blocker_count": 0 if ready else 2,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root / "static_safety_invariant_report_060q" / "latest_static_safety_invariant_report_status_060q.json",
        {
            "contract_version": "pmbot_static_safety_invariant_latest_status_060q.v1",
            "status": "passed_with_warnings",
            "safety_ok": True,
            "critical_count": 0,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_telegram_config(root: Path, *, stop: bool = False) -> Path:
    return _write_json(
        root / "telegram_state.json",
        {
            "contract_version": "pmbot_telegram_operator_state_fixture.v1",
            "status": "local_no_live_launch_config_updated",
            "launch_daily_limit": "$5",
            "launch_max_loss": "$1",
            "launch_selected_markets": ["BTC"],
            "telegram_launch_config": {
                "daily_limit": "$5",
                "max_loss": "$1",
                "selected_markets": ["BTC"],
                "trading_requested": False,
                "operator_stop_requested": stop,
            },
            "operator_stop_requested": stop,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_ready_inputs(root: Path, *, telegram_stop: bool = False, include_fake_values: bool = False) -> Path:
    _write_local_real_check(root)
    _write_selected_candidate(root)
    _write_selected_token_verification(root)
    _write_signer_diagnostic(root)
    _write_payload_stack(root, include_fake_values=include_fake_values)
    _write_risk_stack(root)
    return _write_telegram_config(root, stop=telegram_stop)


def _run(root: Path, out: Path, telegram_path: Path | None = None) -> dict[str, Any]:
    return run_first_supervised_tiny_order_readiness_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=root,
        artifact_dir=out,
        telegram_launch_config_path=telegram_path,
        generated_at=GENERATED_AT,
        head_before="head-before-test",
        head_after="head-after-test",
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


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_missing_local_real_check_evidence_blocks_first(tmp_path: Path) -> None:
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_diagnostic(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")
    telegram = _write_telegram_config(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE
    assert result["component_statuses"]["local_real_check_evidence"]["ready"] is False
    assert result["current_top_blocker"] == STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE
    assert result["first_supervised_tiny_order_ready_for_authorization"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_missing_selected_candidate_blocks_after_local_evidence(tmp_path: Path) -> None:
    _write_local_real_check(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_diagnostic(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")
    telegram = _write_telegram_config(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE
    assert result["component_statuses"]["selected_candidate"]["ready"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_unverified_selected_token_blocks(tmp_path: Path) -> None:
    _write_local_real_check(tmp_path / "sources")
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources", verified=False)
    _write_signer_diagnostic(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")
    telegram = _write_telegram_config(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    assert result["component_statuses"]["selected_token_verification"]["verified"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_signer_diagnostic_not_ok_blocks(tmp_path: Path) -> None:
    _write_local_real_check(tmp_path / "sources")
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_diagnostic(tmp_path / "sources", ok=False)
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")
    telegram = _write_telegram_config(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    assert result["component_statuses"]["signer_diagnostic"]["diagnostic_ok"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_payload_dry_run_not_ready_blocks_after_signer_ok(tmp_path: Path) -> None:
    _write_local_real_check(tmp_path / "sources")
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_diagnostic(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources", ready=False)
    _write_risk_stack(tmp_path / "sources")
    telegram = _write_telegram_config(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY
    assert result["component_statuses"]["payload_dry_run_readiness"]["ready"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_risk_engine_review_blocks_after_payload_ready(tmp_path: Path) -> None:
    _write_local_real_check(tmp_path / "sources")
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_diagnostic(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources", ready=False)
    telegram = _write_telegram_config(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_RISK_ENGINE_REVIEW
    assert result["component_statuses"]["risk_engine"]["ready"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_operator_stop_blocks_even_when_non_live_gates_are_ready(tmp_path: Path) -> None:
    telegram = _write_ready_inputs(tmp_path / "sources", telegram_stop=True)

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)

    assert result["status"] == STATUS_BLOCKED_OPERATOR_STOP_REQUESTED
    assert result["operator_stop_requested"] is True
    assert result["first_supervised_tiny_order_ready_for_authorization"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_ready_for_separate_authorization_packet_remains_no_live_no_execution(tmp_path: Path) -> None:
    telegram = _write_ready_inputs(tmp_path / "sources", include_fake_values=True)

    result = _run(tmp_path / "sources", tmp_path / "out", telegram)
    paths = first_supervised_tiny_order_readiness_artifact_paths(tmp_path / "out")
    artifact_text = _artifact_text(paths)
    keys = set(_walk_keys(result))

    assert result["status"] == STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET
    assert result["answer"] == "yes_ready_to_ask_for_separate_authorization"
    assert result["first_supervised_tiny_order_ready_for_authorization"] is True
    assert result["first_supervised_tiny_order_ready_for_execution"] is False
    assert result["current_top_blocker"] == STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION
    assert result["explicit_live_authorization_present"] is False
    assert result["allowed_for_live"] is False
    assert result["order_submission_enabled"] is False
    assert result["order_cancel_enabled"] is False
    assert result["signing_by_default"] is False
    assert result["latest_status"]["daily_limit"] == "$5"
    assert result["latest_status"]["max_loss"] == "$1"
    assert result["latest_status"]["selected_markets"] == ["BTC"]
    assert set(path.name for path in (tmp_path / "out").iterdir() if path.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert RAW_TOKEN_ID not in artifact_text
    assert FAKE_SECRET not in artifact_text
    assert FAKE_SIGNED_PAYLOAD not in artifact_text
    assert not (keys & {"selected_token_id", "signed_payload", "signed_order", "private_key", "order_id"})
    assert validate_first_supervised_tiny_order_readiness_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_runner_cli_outputs_required_summary_fields_and_rejects_live_flags(tmp_path: Path) -> None:
    telegram = _write_ready_inputs(tmp_path / "sources")
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "sources"),
            "--telegram-launch-config-path",
            str(telegram),
            "--artifacts-dir",
            str(out_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_minimal_env({"POLYMARKET_PRIVATE_KEY": FAKE_SECRET, "POLYMARKET_API_SECRET": FAKE_SECRET}),
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--submit",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_minimal_env(),
    )

    assert completed.returncode == 0, completed.stderr
    assert "selected candidate status:" in completed.stdout
    assert "selected token verified:" in completed.stdout
    assert "signer diagnostic status:" in completed.stdout
    assert "payload dry-run readiness status:" in completed.stdout
    assert "risk engine status:" in completed.stdout
    assert "current top blocker:" in completed.stdout
    assert "allowed for live: false" in completed.stdout
    assert "order submission enabled: false" in completed.stdout
    assert "signing by default: false" in completed.stdout
    assert set(path.name for path in out_dir.iterdir() if path.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert FAKE_SECRET not in _artifact_text(first_supervised_tiny_order_readiness_artifact_paths(out_dir))
    assert forbidden.returncode != 0
    assert "rejects forbidden flag" in forbidden.stderr


def test_runtime_files_keep_no_live_no_secret_no_background_contract() -> None:
    combined = (
        inspect.getsource(packet_module)
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
        "allowed_for_live\": true",
        "order_submission_enabled\": true",
        "signing_by_default\": true",
        "trading_requested\": true",
    )

    for term in forbidden_terms:
        assert term not in combined, term
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        assert "wallet_connected\": true" not in lowered
        assert "full_signed_payload_output\": true" not in lowered

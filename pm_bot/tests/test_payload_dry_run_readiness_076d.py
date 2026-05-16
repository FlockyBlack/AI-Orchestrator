from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.payload_dry_run_readiness_review as runner_module
import pm_bot.trading_core.payload_dry_run_readiness as readiness_module
import pm_bot.trading_core.payload_dry_run_readiness_models as models_module
from pm_bot.trading_core.payload_dry_run_readiness import (
    payload_dry_run_readiness_artifact_paths,
    run_payload_dry_run_readiness_review,
)
from pm_bot.trading_core.payload_dry_run_readiness_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
    STATUS_BLOCKED_RISK_ENGINE_REVIEW,
    STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_READY_FOR_OPERATOR_REVIEW,
    validate_payload_dry_run_readiness_result,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_TOKEN_ID = "123456789012345678900776"

REQUIRED_ARTIFACT_NAMES = {
    "latest_payload_dry_run_readiness_076d_status.json",
    "payload_dry_run_readiness_076d_result.json",
    "payload_dry_run_readiness_076d_blockers.json",
    "payload_dry_run_readiness_076d_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/payload_dry_run_readiness_models.py"),
    Path("pm_bot/trading_core/payload_dry_run_readiness.py"),
    Path("pm_bot/operator_runner/payload_dry_run_readiness_review.py"),
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
            "token_id_short": "123456...0776",
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
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
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_legacy_guarded_signer(root: Path) -> None:
    _write_json(
        root / "guarded_signer_diagnostic_smoke_069a" / "latest_guarded_signer_diagnostic_status_069a.json",
        {
            "contract_version": "pmbot_latest_guarded_signer_diagnostic_status_069a.v1",
            "status": "diagnostic_ok",
            "diagnostic_ok": True,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_signer_evidence(root: Path, *, ok: bool = True) -> None:
    _write_json(
        root / "signer_diagnostic_evidence_bridge_076c" / "latest_signer_diagnostic_evidence_076c_status.json",
        {
            "contract_version": "pmbot_latest_signer_diagnostic_evidence_bridge_076c_status.v1",
            "status": "diagnostic_ok" if ok else "blocked_diagnostic_not_ok",
            "diagnostic_ok": ok,
            "signer_diagnostic_evidence_ok": ok,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
            "signer_instantiated_by_default": False,
        },
    )


def _write_payload_stack(root: Path, *, ready: bool = True) -> None:
    _write_json(
        root / "selected_token_payload_readiness_gate_073c" / "latest_selected_token_payload_readiness_status_073c.json",
        {
            "contract_version": "pmbot_latest_selected_token_payload_readiness_status_073c.v1",
            "status": "ready_for_signed_payload_diagnostic" if ready else "blocked_signed_payload_dry_run_not_ready",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "ready_for_signed_payload_diagnostic": ready,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root / "signed_order_payload_dry_run_070a" / "latest_signed_order_payload_dry_run_status_070a.json",
        {
            "contract_version": "pmbot_latest_signed_order_payload_dry_run_status_070a.v1",
            "status": "blocked_non_executable_signed_order_payload_dry_run_no_submit",
            "payload_contract_fingerprint_sha256": "a" * 64 if ready else "",
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root / "signed_payload_diagnostic_adapter_072e" / "latest_signed_payload_diagnostic_adapter_status_072e.json",
        {
            "contract_version": "pmbot_latest_signed_payload_diagnostic_adapter_status_072e.v1",
            "status": "unsigned_diagnostic_readiness_ready_no_signing"
            if ready
            else "blocked_selected_token_candidate_not_ready",
            "unsigned_readiness_only": ready,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )
    _write_json(
        root / "order_prep_packet_072a" / "latest_order_prep_packet_status_072a.json",
        {
            "contract_version": "pmbot_latest_order_prep_packet_status_072a.v1",
            "status": "order_prep_packet_ready_for_operator_review_non_executable"
            if ready
            else "blocked_order_prep_packet_not_ready",
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_risk_stack(root: Path, *, ready: bool = True) -> None:
    _write_json(
        root / "risk_engine_v2_074d" / "latest_risk_engine_v2_074d_status.json",
        {
            "contract_version": "pmbot_latest_risk_engine_v2_review_074d.v1",
            "status": "passed_review_check_no_live" if ready else "blocked_risk_engine_v2_review",
            "remaining_blocker_count": 0 if ready else 2,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
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
            "status": "review_ready_no_live_authorization" if ready else "blocked_remaining_first_live_order_final_blockers",
            "remaining_blocker_count": 0 if ready else 2,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
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
            "warning_count": 1,
            "allowed_for_live": False,
            "submit_ready": False,
            "live_ready": False,
            "order_submission_enabled": False,
            "signing_by_default": False,
        },
    )


def _write_ready_inputs(root: Path) -> None:
    _write_selected_candidate(root)
    _write_selected_token_verification(root)
    _write_signer_evidence(root)
    _write_payload_stack(root)
    _write_risk_stack(root)


def _run(root: Path, out: Path) -> dict[str, Any]:
    return run_payload_dry_run_readiness_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=root,
        artifact_dir=out,
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


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_missing_selected_candidate_blocks(tmp_path: Path) -> None:
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_evidence(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out")

    assert result["status"] == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE
    assert result["component_statuses"]["selected_candidate"]["ready"] is False
    assert result["current_top_blocker"] == "blocked_missing_selected_candidate"
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_unverified_selected_token_blocks_after_candidate_ready(tmp_path: Path) -> None:
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources", verified=False)
    _write_signer_evidence(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out")

    assert result["status"] == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    assert result["component_statuses"]["selected_token_verification"]["verified"] is False
    assert result["current_top_blocker"] == "blocked_unverified_selected_token"
    assert validate_payload_dry_run_readiness_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_missing_076c_signer_bridge_blocks_even_when_legacy_069a_exists(tmp_path: Path) -> None:
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_legacy_guarded_signer(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out")
    signer = result["component_statuses"]["signer_diagnostic_evidence"]

    assert result["status"] == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    assert signer["diagnostic_ok"] is False
    assert signer["available"] is False
    assert signer["legacy_guarded_signer_available"] is True
    assert result["latest_status"]["next_recommended_safe_command"].startswith(
        "python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge"
    )
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_payload_dry_run_not_ready_blocks_after_signer_ok(tmp_path: Path) -> None:
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_evidence(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources", ready=False)
    _write_risk_stack(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out")

    assert result["status"] == STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY
    assert result["component_statuses"]["payload_dry_run"]["ready"] is False
    assert result["current_top_blocker"] == "blocked_signed_payload_dry_run_not_ready"
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_risk_engine_review_blocks_after_payload_ready(tmp_path: Path) -> None:
    _write_selected_candidate(tmp_path / "sources")
    _write_selected_token_verification(tmp_path / "sources")
    _write_signer_evidence(tmp_path / "sources")
    _write_payload_stack(tmp_path / "sources")
    _write_risk_stack(tmp_path / "sources", ready=False)

    result = _run(tmp_path / "sources", tmp_path / "out")

    assert result["status"] == STATUS_BLOCKED_RISK_ENGINE_REVIEW
    assert result["component_statuses"]["risk_engine"]["ready"] is False
    assert result["current_top_blocker"] == "blocked_risk_engine_review"
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_ready_for_operator_review_remains_no_live_no_submit(tmp_path: Path) -> None:
    _write_ready_inputs(tmp_path / "sources")

    result = _run(tmp_path / "sources", tmp_path / "out")
    paths = payload_dry_run_readiness_artifact_paths(tmp_path / "out")
    artifact_text = _artifact_text(paths)
    keys = set(_walk_keys(result))

    assert result["status"] == STATUS_READY_FOR_OPERATOR_REVIEW
    assert result["submit_ready"] is False
    assert result["live_ready"] is False
    assert result["allowed_for_live"] is False
    assert result["order_submission_enabled"] is False
    assert result["signing_by_default"] is False
    assert result["latest_status"]["status"] == STATUS_READY_FOR_OPERATOR_REVIEW
    assert set(p.name for p in (tmp_path / "out").iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert RAW_TOKEN_ID not in artifact_text
    assert not (keys & {"token_id", "selected_token_id", "signed_payload", "signed_order", "private_key"})
    assert validate_payload_dry_run_readiness_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_runner_cli_outputs_required_summary_fields(tmp_path: Path) -> None:
    _write_ready_inputs(tmp_path / "sources")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.payload_dry_run_readiness_review",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "sources"),
            "--artifacts-dir",
            str(tmp_path / "out"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_minimal_env(),
    )

    assert completed.returncode == 0, completed.stderr
    assert "selected candidate status:" in completed.stdout
    assert "selected token verification status:" in completed.stdout
    assert "signer diagnostic status:" in completed.stdout
    assert "payload dry-run status:" in completed.stdout
    assert "risk status:" in completed.stdout
    assert "final blockers:" in completed.stdout
    assert "next recommended safe command:" in completed.stdout


def test_runner_rejects_forbidden_live_flags(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.payload_dry_run_readiness_review",
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

    assert completed.returncode != 0
    assert "rejects forbidden flag" in completed.stderr


def test_runtime_files_keep_no_live_contract_language() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in RUNTIME_FILES)

    assert "allowed_for_live\": True" not in combined
    assert "allowed_for_live = True" not in combined
    assert "order_submission_enabled\": True" not in combined
    assert "signing_by_default\": True" not in combined
    assert "wallet_connected\": True" not in combined
    assert "full_signed_payload_output\": True" not in combined
    assert "--dry-run" in inspect.getsource(runner_module)
    assert "signer_diagnostic_evidence_bridge_076c" in inspect.getsource(readiness_module)
    assert STATUS_READY_FOR_OPERATOR_REVIEW in inspect.getsource(models_module)

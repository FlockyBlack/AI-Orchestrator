from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.risk_engine_v2 import (
    run_risk_engine_v2_review,
    risk_engine_v2_review_artifact_paths,
)
from pm_bot.trading_core.risk_engine_v2_models import (
    FORCED_FALSE_EXECUTION_FIELDS,
    REQUIRED_BLOCKER_IDS,
    REQUIRED_GATE_IDS,
    STATUS_BLOCKED,
    validate_risk_engine_v2_review_result,
)
import pm_bot.operator_runner.risk_engine_v2_review as runner_module
import pm_bot.trading_core.risk_engine_v2 as engine_module
import pm_bot.trading_core.risk_engine_v2_models as models_module

GENERATED_AT = "2026-05-16T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-074d",
    "fake-seed-phrase-074d",
    "fake-api-secret-074d",
    "fake-auth-token-074d",
    "fake-passphrase-074d",
)

REQUIRED_ARTIFACT_NAMES = {
    "risk_engine_v2_074d_result.json",
    "latest_risk_engine_v2_074d_status.json",
    "risk_engine_v2_074d_blockers.json",
    "risk_engine_v2_074d_gate_evaluations.json",
    "risk_engine_v2_074d_safety_snapshot.json",
    "risk_engine_v2_074d_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/risk_engine_v2_models.py"),
    Path("pm_bot/trading_core/risk_engine_v2.py"),
    Path("pm_bot/operator_runner/risk_engine_v2_review.py"),
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


def _good_evidence() -> dict[str, dict[str, Any]]:
    safe_false = {
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "order_cancellation_enabled": False,
        "signing_enabled": False,
        "wallet_connection_attempted": False,
        "private_key_read": False,
    }
    return {
        "data_freshness": {"status": "fresh", **safe_false},
        "liquidity": {"status": "strong", **safe_false},
        "source_backed_token_candidate": {"status": "source_backed", **safe_false},
        "account_readonly": {"status": "read_only_ok", **safe_false},
        "signer_diagnostic": {"status": "diagnostic_ok", **safe_false},
        "selected_token_payload_readiness": {
            "status": "ready_for_signed_payload_diagnostic",
            **safe_false,
        },
    }


def _good_state(**overrides: Any) -> dict[str, Any]:
    value = {
        "requested_notional_usd": 1.0,
        "current_total_exposure_usd": 0.0,
        "current_market_exposure_usd": 0.0,
        "realized_daily_loss_usd": 0.0,
        "attempt_key": "risk-v2-review-attempt-074d",
        "prior_attempt_keys": [],
        "halt_state_known": True,
        "active_halt_states": [],
    }
    value.update(overrides)
    return value


def _good_limits(**overrides: Any) -> dict[str, Any]:
    value = {
        "max_total_exposure_usd": 10.0,
        "max_market_exposure_usd": 5.0,
        "max_daily_loss_usd": 5.0,
    }
    value.update(overrides)
    return value


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
    assert value["risk_engine_v2_executable_for_live"] is False
    assert value["first_supervised_tiny_order_blocked"] is True
    assert value["resolved_blocker_count"] == 0
    for row in _walk_mappings(value):
        for field in FORCED_FALSE_EXECUTION_FIELDS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key != "root" and path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_default_review_writes_artifacts_and_blocks_all_unknowns(tmp_path: Path) -> None:
    result = run_risk_engine_v2_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    second = run_risk_engine_v2_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = risk_engine_v2_review_artifact_paths(tmp_path / "artifacts")
    blocker_ids = set(result["blocker_ids"])

    assert result == second
    assert result["status"] == STATUS_BLOCKED
    assert result["validation"]["valid"] is True
    assert {row["gate_id"] for row in result["gate_evaluations"]} == set(REQUIRED_GATE_IDS)
    assert set(REQUIRED_BLOCKER_IDS).issubset(blocker_ids)
    assert result["allowed_for_live"] is False
    assert result["risk_engine_v2_executable_for_live"] is False
    assert result["first_supervised_tiny_order_blocked"] is True
    assert result["unknown_blocker_count"] >= 1
    assert set(path.name for key, path in paths.items() if key != "root") == REQUIRED_ARTIFACT_NAMES
    for key, path in paths.items():
        if key != "root":
            assert path.exists(), key
    _assert_forced_false_flags(result)


def test_local_artifact_context_references_073_074_layers_without_unblocking(tmp_path: Path) -> None:
    artifact_root = tmp_path / "source_artifacts"
    _write_json(
        artifact_root / "local_real_check_snapshot_073a" / "latest_local_real_check_snapshot_status_073a.json",
        {
            "contract_version": "fixture.latest_local_real_check_snapshot_073a.v1",
            "status": "local_real_check_snapshot_recorded_live_blocked",
            "allowed_for_live": False,
        },
    )
    _write_json(
        artifact_root / "operator_token_selection_packet_073b" / "latest_operator_token_selection_status_073b.json",
        {
            "contract_version": "fixture.latest_operator_token_selection_status_073b.v1",
            "status": "selection_required",
            "selected_token_id_present": False,
            "selected_token_source_backed": False,
            "allowed_for_live": False,
        },
    )
    _write_json(
        artifact_root
        / "selected_token_payload_readiness_gate_073c"
        / "latest_selected_token_payload_readiness_status_073c.json",
        {
            "contract_version": "fixture.latest_selected_token_payload_readiness_status_073c.v1",
            "status": "blocked_missing_selected_token",
            "ready_for_signed_payload_diagnostic": False,
            "selected_token_payload_ready_for_submit": False,
            "allowed_for_live": False,
        },
    )
    _write_json(
        artifact_root
        / "real_local_check_evidence_review_074a"
        / "latest_real_local_check_evidence_review_status_074a.json",
        {
            "contract_version": "fixture.latest_real_local_check_evidence_review_status_074a.v1",
            "status": "blocked_first_supervised_tiny_order_not_ready",
            "remaining_blocker_count": 12,
            "unknown_group_count": 0,
            "allowed_for_live": False,
        },
    )

    result = run_risk_engine_v2_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=artifact_root,
        consume_local_artifacts=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    status_by_gate = {row["gate_id"]: row["evidence_status"] for row in result["gate_evaluations"]}
    source_keys_by_gate = {row["gate_id"]: set(row["source_keys"]) for row in result["gate_evaluations"]}

    assert result["validation"]["valid"] is True
    assert result["observed_source_artifact_count"] == 4
    assert set(result["source_artifact_ids"]) == {
        "local_real_check_snapshot_073a",
        "operator_token_selection_packet_073b",
        "selected_token_payload_readiness_gate_073c",
        "real_local_check_evidence_review_074a",
    }
    assert status_by_gate["source_backed_token_candidate"] == "selection_required"
    assert status_by_gate["selected_token_payload_readiness"] == "blocked_missing_selected_token"
    assert status_by_gate["account_readonly_evidence"] == "blocked_first_supervised_tiny_order_not_ready"
    assert "operator_token_selection_packet_073b" in source_keys_by_gate["source_backed_token_candidate"]
    assert "selected_token_payload_readiness_gate_073c" in source_keys_by_gate["selected_token_payload_readiness"]
    assert result["allowed_for_live"] is False
    assert result["risk_engine_v2_executable_for_live"] is False
    assert result["first_supervised_tiny_order_blocked"] is True
    assert result["remaining_blocker_count"] > 0
    _assert_forced_false_flags(result)


def test_complete_review_context_still_blocks_without_operator_and_live_authorization(tmp_path: Path) -> None:
    result = run_risk_engine_v2_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        evidence=_good_evidence(),
        risk_state=_good_state(),
        risk_limits=_good_limits(),
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    blocker_ids = set(result["blocker_ids"])

    assert result["validation"]["valid"] is True
    assert result["unknown_blocker_count"] == 0
    assert result["passed_gate_count"] if "passed_gate_count" in result else True
    assert "risk_v2_operator_approval_required" in blocker_ids
    assert "risk_v2_explicit_live_authorization_missing" in blocker_ids
    assert "risk_v2_unknown_evidence_blocks" not in blocker_ids
    assert result["remaining_blocker_count"] == 2
    assert result["allowed_for_live"] is False
    assert result["first_supervised_tiny_order_blocked"] is True
    _assert_forced_false_flags(result)


def test_caps_duplicate_guard_and_halt_states_block_with_stable_ids(tmp_path: Path) -> None:
    result = run_risk_engine_v2_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        evidence=_good_evidence(),
        risk_state=_good_state(
            requested_notional_usd=2.0,
            current_total_exposure_usd=9.5,
            current_market_exposure_usd=4.5,
            realized_daily_loss_usd=5.0,
            prior_attempt_keys=["risk-v2-review-attempt-074d"],
            active_halt_states=["manual_halt"],
        ),
        risk_limits=_good_limits(),
        review_controls={
            "operator_approval_status": "operator_approved_review_only",
            "operator_approval_required_acknowledged": True,
        },
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    blocker_ids = set(result["blocker_ids"])

    assert "risk_v2_total_exposure_cap_unknown_or_exceeded" in blocker_ids
    assert "risk_v2_per_market_cap_unknown_or_exceeded" in blocker_ids
    assert "risk_v2_daily_loss_cap_unknown_or_exceeded" in blocker_ids
    assert "risk_v2_duplicate_attempt_guard_unknown_or_triggered" in blocker_ids
    assert "risk_v2_halt_state_unknown_or_active" in blocker_ids
    assert "risk_v2_operator_approval_required" not in blocker_ids
    assert "risk_v2_explicit_live_authorization_missing" in blocker_ids
    assert result["allowed_for_live"] is False
    _assert_forced_false_flags(result)


def test_stale_weak_missing_and_unsafe_source_evidence_blocks(tmp_path: Path) -> None:
    evidence = _good_evidence()
    evidence["data_freshness"] = {"status": "stale", "allowed_for_live": False}
    evidence["liquidity"] = {"status": "weak", "allowed_for_live": False}
    evidence.pop("source_backed_token_candidate")
    evidence["signer_diagnostic"] = {"status": "diagnostic_ok", "allowed_for_live": True}

    result = run_risk_engine_v2_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        evidence=evidence,
        risk_state=_good_state(),
        risk_limits=_good_limits(),
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    blocker_ids = set(result["blocker_ids"])
    status_by_gate = {row["gate_id"]: row["evidence_status"] for row in result["gate_evaluations"]}

    assert "risk_v2_stale_data_or_freshness_unknown" in blocker_ids
    assert "risk_v2_liquidity_evidence_missing_or_weak" in blocker_ids
    assert "risk_v2_source_backed_token_candidate_missing" in blocker_ids
    assert "risk_v2_signer_diagnostic_evidence_missing" in blocker_ids
    assert status_by_gate["stale_data"] == "stale"
    assert status_by_gate["liquidity_evidence"] == "weak"
    assert status_by_gate["source_backed_token_candidate"] == "missing_evidence"
    assert status_by_gate["signer_diagnostic_evidence"] == "unsafe_source_flag"
    assert result["allowed_for_live"] is False
    _assert_forced_false_flags(result)


def test_validation_rejects_any_live_enablement_mutation(tmp_path: Path) -> None:
    result = run_risk_engine_v2_review(
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    unsafe = dict(result)
    unsafe["allowed_for_live"] = True
    unsafe["risk_engine_v2_executable_for_live"] = True

    validation = validate_risk_engine_v2_review_result(unsafe, generated_at=GENERATED_AT)

    assert validation["valid"] is False
    assert "allowed_for_live_not_false" in validation["statuses"]
    assert "risk_engine_v2_executable_for_live_not_false" in validation["statuses"]


def test_cli_runs_with_fake_secret_env_values_without_emitting_them(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.risk_engine_v2_review",
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
    paths = risk_engine_v2_review_artifact_paths(tmp_path)
    artifact_text = _artifact_text(paths)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    keys = set(_walk_keys(result))

    assert completed.returncode == 0, completed.stderr
    assert "Risk Engine v2 review 074D completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Risk Engine v2 executable for live: false" in completed.stdout
    assert "First supervised tiny order blocked: true" in completed.stdout
    assert set(p.name for p in tmp_path.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert not (keys & {"order_id", "client_order_id", "signed_payload", "signed_order", "tx_hash", "fill", "balance", "pnl"})
    for fake in FAKE_SECRET_VALUES:
        assert fake not in completed.stdout
        assert fake not in completed.stderr
        assert fake not in artifact_text
    _assert_forced_false_flags(result)


def test_cli_requires_dry_run_and_rejects_forbidden_runtime_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.risk_engine_v2_review",
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
            "pm_bot.operator_runner.risk_engine_v2_review",
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
    assert "unsupported flag" in forbidden.stderr


def test_no_submit_cancel_sign_network_env_or_browser_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(engine_module)
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
        "playwright",
        "selenium",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path

from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.local_real_check_bundle as runner_module
import pm_bot.trading_core.local_real_check_bundle as bundle_module
import pm_bot.trading_core.local_real_check_bundle_models as models_module
from pm_bot.trading_core.local_real_check_bundle import (
    local_real_check_bundle_artifact_paths,
    run_local_real_check_bundle,
)
from pm_bot.trading_core.local_real_check_bundle_models import (
    CLOB_SUBCHECK_ID,
    DISCOVERY_BRIDGE_SUBCHECK_ID,
    GUARDED_SIGNER_SUBCHECK_ID,
    LIVE_ACCOUNT_SUBCHECK_ID,
    LIVE_STATUS_SUBCHECK_ID,
    PUBLIC_DISCOVERY_SUBCHECK_ID,
    STATUS_COMPLETED_WITH_FAILED_SUBCHECKS,
    SUBCHECK_SEQUENCE,
    validate_local_real_check_bundle_result,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

RAW_SECRET = "raw-secret-072c-never-output"
RAW_PRIVATE_KEY = "0x" + "7" * 64


def _minimal_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def _fake_result(
    subcheck_id: str,
    status: str,
    *,
    blockers: list[dict[str, Any]] | None = None,
    latest_extra: Mapping[str, Any] | None = None,
    result_extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_path = f"pm_bot/trading_core/artifacts/{subcheck_id}/{subcheck_id}_result.json"
    latest_status_path = f"pm_bot/trading_core/artifacts/{subcheck_id}/latest_{subcheck_id}.json"
    latest = {
        "contract_version": f"fixture.{subcheck_id}.latest.v1",
        "status": status,
        "artifact_path": artifact_path,
        "latest_status_path": latest_status_path,
        "allowed_for_live": False,
    }
    latest.update(dict(latest_extra or {}))
    value = {
        "contract_version": f"fixture.{subcheck_id}.result.v1",
        "status": status,
        "latest_status": latest,
        "blockers": list(blockers or []),
        "artifact_paths": {"result": artifact_path, "latest_status": latest_status_path},
        "allowed_for_live": False,
    }
    value.update(dict(result_extra or {}))
    return value


def _install_fake_success_subchecks(monkeypatch) -> dict[str, list[dict[str, Any]]]:  # type: ignore[no-untyped-def]
    calls: dict[str, list[dict[str, Any]]] = {subcheck_id: [] for subcheck_id in SUBCHECK_SEQUENCE}

    def fake_clob(**kwargs: Any) -> dict[str, Any]:
        calls[CLOB_SUBCHECK_ID].append(kwargs)
        return _fake_result(
            CLOB_SUBCHECK_ID,
            "authenticated_readonly_probe_succeeded_live_blocked",
            latest_extra={"auth_verified": True, "credential_presence_status": "present_redacted"},
        )

    def fake_account(**kwargs: Any) -> dict[str, Any]:
        calls[LIVE_ACCOUNT_SUBCHECK_ID].append(kwargs)
        return _fake_result(
            LIVE_ACCOUNT_SUBCHECK_ID,
            "account_state_probe_succeeded_live_blocked",
            latest_extra={"open_orders_status": "succeeded", "balance_allowance_status": "succeeded_redacted"},
        )

    def fake_signer(**kwargs: Any) -> dict[str, Any]:
        calls[GUARDED_SIGNER_SUBCHECK_ID].append(kwargs)
        requested = kwargs.get("allow_private_key_diagnostic") is True
        return _fake_result(
            GUARDED_SIGNER_SUBCHECK_ID,
            "diagnostic_ok" if requested else "blocked_diagnostic_not_requested",
            latest_extra={
                "diagnostic_requested": requested,
                "private_key_read": requested,
                "diagnostic_challenge_signed": requested,
                "derived_wallet_matches_expected": True if requested else "unknown",
                "diagnostic_status": "diagnostic_ok" if requested else "diagnostic_not_requested",
            },
        )

    def fake_discovery(**kwargs: Any) -> dict[str, Any]:
        calls[PUBLIC_DISCOVERY_SUBCHECK_ID].append(kwargs)
        return _fake_result(
            PUBLIC_DISCOVERY_SUBCHECK_ID,
            "source_backed_candidates_ready",
            result_extra={"market_candidate_count": 1, "outcome_token_candidate_count": 1},
        )

    def fake_bridge(**kwargs: Any) -> dict[str, Any]:
        calls[DISCOVERY_BRIDGE_SUBCHECK_ID].append(kwargs)
        return _fake_result(
            DISCOVERY_BRIDGE_SUBCHECK_ID,
            "ready_source_backed_token_contract",
            latest_extra={"target_token_id_present": True, "target_token_id_source_backed": True},
            result_extra={"source_backed_candidate_count": 1, "valid_source_backed_candidate_count": 1},
        )

    def fake_status(**kwargs: Any) -> dict[str, Any]:
        calls[LIVE_STATUS_SUBCHECK_ID].append(kwargs)
        return _fake_result(
            LIVE_STATUS_SUBCHECK_ID,
            "live_readonly_status_aggregated",
            latest_extra={
                "l2_auth_status": "authenticated_readonly_probe_succeeded_live_blocked",
                "open_orders_status": "succeeded",
                "balance_status": "available_redacted",
                "allowance_status": "available_redacted",
            },
        )

    monkeypatch.setattr(bundle_module, "run_clob_l2_auth_readonly_probe", fake_clob)
    monkeypatch.setattr(bundle_module, "run_live_account_readonly_state_probe", fake_account)
    monkeypatch.setattr(bundle_module, "run_guarded_signer_diagnostic_smoke", fake_signer)
    monkeypatch.setattr(bundle_module, "run_public_market_token_discovery", fake_discovery)
    monkeypatch.setattr(bundle_module, "run_discovery_to_token_resolver_bridge", fake_bridge)
    monkeypatch.setattr(bundle_module, "run_live_readonly_status_aggregator", fake_status)
    return calls


def _write_public_discovery_local_artifact(path: Path) -> Path:
    payload = {
        "contract_version": "fixture.normalized_public_market_snapshot_054.v1",
        "source_name": "public_gamma_local_fixture",
        "source_type": "public_gamma_read_only",
        "selected_market": {
            "market_id": "0x" + ("a" * 64),
            "market_slug": "bitcoin-up-or-down-may-15-2026",
            "question": "Will Bitcoin be above the public threshold?",
            "active": True,
            "closed": False,
            "outcome_labels": ["Yes", "No"],
            "public_market_token_ids": ["1001", "1002"],
        },
        "generated_at": GENERATED_AT,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_subcheck_failures_are_preserved_without_fake_success(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake_success_subchecks(monkeypatch)

    def failing_public_discovery(**kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("public discovery failed before artifact write")

    monkeypatch.setattr(bundle_module, "run_public_market_token_discovery", failing_public_discovery)
    result = run_local_real_check_bundle(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "bundle",
        subcheck_artifact_root=tmp_path / "subchecks",
        generated_at=GENERATED_AT,
    )

    discovery_row = next(row for row in result["subchecks"] if row["subcheck_id"] == PUBLIC_DISCOVERY_SUBCHECK_ID)
    assert result["status"] == STATUS_COMPLETED_WITH_FAILED_SUBCHECKS
    assert result["all_subchecks_reported_success"] is False
    assert result["subcheck_failed_count"] == 1
    assert discovery_row["failed"] is True
    assert discovery_row["exception_type"] == "RuntimeError"
    assert "public discovery failed" in discovery_row["error_message_sanitized"]
    assert any(row["blocker_category"] == "subcheck_failure" for row in result["blockers"])
    assert validate_local_real_check_bundle_result(result)["valid"] is True


def test_private_key_diagnostic_flag_is_passed_only_to_guarded_signer(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls = _install_fake_success_subchecks(monkeypatch)
    run_local_real_check_bundle(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        allow_private_key_diagnostic=True,
        artifact_dir=tmp_path / "bundle",
        subcheck_artifact_root=tmp_path / "subchecks",
        generated_at=GENERATED_AT,
    )

    assert calls[GUARDED_SIGNER_SUBCHECK_ID][0]["allow_private_key_diagnostic"] is True
    for subcheck_id in (
        CLOB_SUBCHECK_ID,
        LIVE_ACCOUNT_SUBCHECK_ID,
        PUBLIC_DISCOVERY_SUBCHECK_ID,
        DISCOVERY_BRIDGE_SUBCHECK_ID,
        LIVE_STATUS_SUBCHECK_ID,
    ):
        assert "allow_private_key_diagnostic" not in calls[subcheck_id][0]


def test_default_bundle_does_not_request_private_key_diagnostic(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls = _install_fake_success_subchecks(monkeypatch)
    result = run_local_real_check_bundle(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "bundle",
        subcheck_artifact_root=tmp_path / "subchecks",
        generated_at=GENERATED_AT,
    )
    signer_row = next(row for row in result["subchecks"] if row["subcheck_id"] == GUARDED_SIGNER_SUBCHECK_ID)

    assert calls[GUARDED_SIGNER_SUBCHECK_ID][0]["allow_private_key_diagnostic"] is False
    assert result["private_key_diagnostic_requested"] is False
    assert signer_row["status_fields"]["diagnostic_requested"] is False
    assert signer_row["status_fields"]["diagnostic_private_key_read"] is False
    assert result["allowed_for_live"] is False
    assert result["bundle_executable_for_live"] is False


def test_bundle_does_not_embed_raw_subcheck_payload_or_secret_values(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake_success_subchecks(monkeypatch)

    def fake_clob_with_raw_secret(**kwargs: Any) -> dict[str, Any]:
        return _fake_result(
            CLOB_SUBCHECK_ID,
            "blocked_missing_l2_credentials",
            blockers=[{"blocker_id": "missing", "blocker_category": "env", "reason": f"missing {RAW_SECRET}"}],
            result_extra={"raw_secret_payload": RAW_SECRET, "private_key": RAW_PRIVATE_KEY},
        )

    monkeypatch.setattr(bundle_module, "run_clob_l2_auth_readonly_probe", fake_clob_with_raw_secret)
    result = run_local_real_check_bundle(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "bundle",
        subcheck_artifact_root=tmp_path / "subchecks",
        generated_at=GENERATED_AT,
        secret_redaction_values=(RAW_SECRET, RAW_PRIVATE_KEY),
    )
    paths = local_real_check_bundle_artifact_paths(tmp_path / "bundle")
    artifact_text = _artifact_text(paths)

    assert RAW_SECRET not in json.dumps(result, sort_keys=True)
    assert RAW_PRIVATE_KEY not in json.dumps(result, sort_keys=True)
    assert RAW_SECRET not in artifact_text
    assert RAW_PRIVATE_KEY not in artifact_text
    assert result["subchecks"][0]["raw_subcheck_payload_embedded"] is False


def test_missing_env_produces_blocked_auth_subchecks(tmp_path: Path) -> None:
    local_artifact = _write_public_discovery_local_artifact(tmp_path / "input" / "public_market.json")
    result = run_local_real_check_bundle(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "bundle",
        subcheck_artifact_root=tmp_path / "subchecks",
        public_discovery_local_artifact_paths=[local_artifact],
        environ={},
        generated_at=GENERATED_AT,
    )
    statuses = {row["subcheck_id"]: row["status"] for row in result["subchecks"]}

    assert statuses[CLOB_SUBCHECK_ID] == "blocked_missing_l2_credentials"
    assert statuses[LIVE_ACCOUNT_SUBCHECK_ID] == "blocked_missing_l2_credentials"
    assert result["all_subchecks_reported_success"] is False
    assert result["allowed_for_live"] is False
    assert result["bundle_executable_for_live"] is False


def test_runner_emits_required_artifacts(tmp_path: Path) -> None:
    local_artifact = _write_public_discovery_local_artifact(tmp_path / "input" / "public_market.json")
    out_dir = tmp_path / "bundle"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.local_real_check_bundle",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--local-artifact",
            str(local_artifact),
            "--subcheck-artifact-root",
            str(tmp_path / "subchecks"),
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = local_real_check_bundle_artifact_paths(out_dir)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Local real-check bundle 072C completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Bundle executable for live: false" in completed.stdout
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["subchecks"].exists()
    assert paths["blockers"].exists()
    assert paths["safety_snapshot"].exists()
    assert paths["operator_summary"].exists()
    assert result["allowed_for_live"] is False
    assert result["bundle_executable_for_live"] is False
    assert result["subcheck_count"] == len(SUBCHECK_SEQUENCE)


def test_no_submit_cancel_sign_payload_or_scheduler_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(bundle_module)
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
        "generate_signed_payload(",
        "create_signed_order(",
        "time.sleep(",
        "threading",
        "asyncio",
        "sched.",
        "start-process",
    )
    for term in forbidden_terms:
        assert term not in source, term
    assert re.search(r"\bwhile\s+true\b", source) is None

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.final_blocker_action_planner as runner_module
import pm_bot.trading_core.final_blocker_action_planner_078j as planner_module
from pm_bot.trading_core.final_blocker_action_planner_078j import (
    STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
    STATUS_BLOCKED_MISSING_FUNDER_ADDRESS,
    STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_POLYMARKET_SDK_UNAVAILABLE,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    final_blocker_action_planner_artifact_paths,
    run_final_blocker_action_planner,
)

GENERATED_AT = "2026-05-17T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-api-secret-never-output-078j",
    "fake-passphrase-never-output-078j",
    "0x" + "7" * 64,
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222",
    "fake-signed-payload-never-output-078j",
)

REQUIRED_ARTIFACT_NAMES = {
    "final_blocker_action_planner_078j_result.json",
    "latest_final_blocker_action_planner_078j_status.json",
    "final_blocker_action_planner_078j_actions.json",
    "final_blocker_action_planner_078j_safety_snapshot.json",
    "final_blocker_action_planner_078j_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/final_blocker_action_planner_078j.py"),
    Path("pm_bot/operator_runner/final_blocker_action_planner.py"),
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


def _safe_source(status: str, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "contract_version": "pmbot_078j_test_source.v1",
        "status": status,
        "market_symbol": "BTC",
        "strategy_name": "tiny-momentum",
        "allowed_for_live": False,
        "trading_requested": False,
        "order_submission_enabled": False,
        "order_cancellation_attempted": False,
        "signing_by_default": False,
        "wallet_connection_attempted": False,
        "resolved_blocker_count": 0,
    }
    value.update(extra)
    return value


def _write_runtime(root: Path, *, ready: bool = True, missing_funder_only: bool = False) -> None:
    status = "runtime_credentials_visible" if ready else "blocked_missing_wallet_address"
    _write_json(
        root / "runtime_credential_visibility_077c" / "latest_runtime_credential_visibility_077c_status.json",
        _safe_source(
            status,
            polymarket_l2_visible=True,
            private_key_visible=True,
            wallet_context_visible=ready,
            wallet_context_missing_env_vars=["POLYMARKET_FUNDER_ADDRESS"] if missing_funder_only else [],
        ),
    )


def _write_funder(root: Path, *, missing: bool = False) -> None:
    _write_json(
        root / "funder_wallet_context_077g" / "latest_funder_wallet_context_077g_status.json",
        _safe_source(
            "blocked_missing_funder_address" if missing else "funder_differs_from_wallet_address",
            wallet_address_present=True,
            funder_address_present=not missing,
            signature_type_present=True,
            private_key_present=True,
            wallet_context_visible=not missing,
            suggested_safe_action="set POLYMARKET_FUNDER_ADDRESS if required by account/proxy wallet setup"
            if missing
            else "no automatic funder action",
        ),
    )


def _write_account(root: Path, *, sdk_missing: bool = False, ready: bool = True) -> None:
    _write_json(
        root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
        _safe_source(
            "blocked_sdk_unavailable" if sdk_missing else "account_state_probe_succeeded_live_blocked",
            account_state_probe_performed=ready and not sdk_missing,
            probe_is_readonly=True,
            sdk_status="dependency_missing" if sdk_missing else "available_readonly_methods_checked",
            blockers=[
                {
                    "blocker_id": "polymarket_clob_sdk_dependency_missing",
                    "allowed_for_live": False,
                }
            ]
            if sdk_missing
            else [],
        ),
    )


def _write_local_real_check(root: Path) -> None:
    _write_json(
        root / "local_real_check_bundle_072c" / "latest_local_real_check_bundle_status_072c.json",
        _safe_source("local_real_check_bundle_completed_with_blockers_live_blocked"),
    )


def _write_payload(root: Path, *, ready: bool = True, signer_ok: bool = True, fake_values: bool = False) -> None:
    payload = _safe_source(
        "payload_dry_run_ready_for_operator_review" if ready else "blocked_signed_payload_dry_run_not_ready",
        payload_dry_run_ready=ready,
        signer_diagnostic_ok=signer_ok,
        signer_diagnostic_status=(
            "signer_diagnostic_evidence_ok_for_payload_dry_run"
            if signer_ok
            else "blocked_signer_diagnostic_failed"
        ),
    )
    if fake_values:
        payload["redacted_note"] = "fake secret markers are intentionally absent from planner artifacts"
    _write_json(
        root / "payload_dry_run_readiness_076d" / "latest_payload_dry_run_readiness_076d_status.json",
        payload,
    )


def _write_first_packet(root: Path, *, ready: bool = True, signer_ok: bool = True) -> None:
    status = (
        "ready_for_separate_live_authorization_packet"
        if ready
        else "blocked_payload_dry_run_not_ready"
    )
    _write_json(
        root
        / "first_supervised_tiny_order_readiness_077a"
        / "latest_first_supervised_tiny_order_readiness_077a_status.json",
        _safe_source(
            status,
            first_supervised_tiny_order_ready_for_authorization=ready,
            first_supervised_tiny_order_ready_for_execution=False,
            explicit_live_authorization_present=False,
            current_top_blocker=STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION
            if ready
            else "blocked_payload_dry_run_not_ready",
            signer_diagnostic_ok=signer_ok,
            signer_diagnostic_status="signer_diagnostic_evidence_ok_for_payload_dry_run"
            if signer_ok
            else "blocked_signer_diagnostic_failed",
        ),
    )


def _write_risk(root: Path, *, ready: bool = True) -> None:
    _write_json(
        root / "risk_engine_v2_074d" / "latest_risk_engine_v2_074d_status.json",
        _safe_source(
            "passed_review_check_no_live" if ready else "blocked_risk_engine_v2_review",
            risk_engine_v2_ready=ready,
            remaining_blocker_count=0 if ready else 1,
        ),
    )


def _write_final_reducer(root: Path, *, clear: bool = True) -> None:
    _write_json(
        root
        / "first_live_order_final_blocker_reducer_072d"
        / "latest_first_live_order_final_blockers_072d.json",
        _safe_source(
            "review_ready_no_live_authorization" if clear else "blocked_remaining_first_live_order_final_blockers",
            remaining_blocker_count=0 if clear else 2,
        ),
    )


def _write_ready_sources(root: Path, *, fake_values: bool = False) -> None:
    _write_runtime(root)
    _write_funder(root)
    _write_account(root)
    _write_local_real_check(root)
    _write_payload(root, fake_values=fake_values)
    _write_first_packet(root)
    _write_risk(root)
    _write_final_reducer(root)


def _run(root: Path, out: Path) -> dict[str, Any]:
    return run_final_blocker_action_planner(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=root,
        artifact_dir=out,
        generated_at=GENERATED_AT,
        head_before="head-before-test",
        head_after="head-after-test",
    )


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


def _assert_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in (
            "allowed_for_live",
            "trading_requested",
            "order_submission_enabled",
            "order_submission_attempted",
            "order_submitted",
            "order_cancel_enabled",
            "order_cancellation_attempted",
            "signing_enabled",
            "signing_attempted",
            "signing_by_default",
            "signer_instantiated",
            "wallet_connection_attempted",
            "wallet_connect_enabled",
            "authenticated_request_performed",
            "raw_secret_values_emitted",
            "browser_automation_added",
            "scheduler_or_daemon_added",
            "background_worker_added",
            "autonomous_live_trading_added",
        ):
            if field in row:
                assert row[field] is False, field


def _top_action(result: Mapping[str, Any]) -> Mapping[str, Any]:
    return result["ordered_next_actions"][0]


def test_missing_funder_maps_to_required_local_env_action(tmp_path: Path) -> None:
    _write_ready_sources(tmp_path / "sources")
    _write_runtime(tmp_path / "sources", ready=False, missing_funder_only=True)
    _write_funder(tmp_path / "sources", missing=True)

    result = _run(tmp_path / "sources", tmp_path / "out")
    top = _top_action(result)

    assert result["status"] == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS
    assert result["top_blocker"] == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS
    assert top["category"] == "user/local env"
    assert top["action"] == "set POLYMARKET_FUNDER_ADDRESS if required by account/proxy wallet setup"
    assert top["exact_safe_command"] == (
        "python -m pm_bot.operator_runner.funder_wallet_context_diagnostic "
        "--market BTC --strategy tiny-momentum --dry-run"
    )
    assert result["validation"]["valid"] is True
    _assert_false_flags(result)


def test_sdk_unavailable_maps_to_dependency_install_action(tmp_path: Path) -> None:
    _write_ready_sources(tmp_path / "sources")
    _write_account(tmp_path / "sources", sdk_missing=True)

    result = _run(tmp_path / "sources", tmp_path / "out")
    action_ids = [row["blocker_id"] for row in result["ordered_next_actions"]]
    sdk_action = next(row for row in result["ordered_next_actions"] if row["blocker_id"] == STATUS_BLOCKED_POLYMARKET_SDK_UNAVAILABLE)

    assert STATUS_BLOCKED_POLYMARKET_SDK_UNAVAILABLE in action_ids
    assert sdk_action["category"] == "dependency install"
    assert sdk_action["action"] == "install/check py-clob-client, then rerun the read-only probe"
    assert sdk_action["exact_safe_command"] == "python -m pip install py-clob-client"
    assert sdk_action["follow_up_safe_command"].endswith(
        "pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run"
    )
    assert result["validation"]["valid"] is True
    _assert_false_flags(result)


def test_signer_diagnostic_failed_maps_to_guarded_rerun_after_env_visible(tmp_path: Path) -> None:
    _write_ready_sources(tmp_path / "sources")
    _write_payload(tmp_path / "sources", ready=False, signer_ok=False)
    _write_first_packet(tmp_path / "sources", ready=False, signer_ok=False)

    result = _run(tmp_path / "sources", tmp_path / "out")
    signer_action = next(row for row in result["ordered_next_actions"] if row["blocker_id"] == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK)

    assert signer_action["category"] == "code task"
    assert signer_action["action"] == "rerun guarded signer diagnostic after env is visible, then bridge signer evidence"
    assert signer_action["exact_safe_command"] == (
        "python -m pm_bot.operator_runner.guarded_signer_diagnostic_smoke "
        "--market BTC --strategy tiny-momentum --dry-run"
    )
    assert signer_action["follow_up_safe_command"].endswith(
        "pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run"
    )
    assert "runtime credential visibility is complete" in signer_action["preconditions"]
    assert result["validation"]["valid"] is True
    _assert_false_flags(result)


def test_payload_not_ready_maps_to_payload_readiness_after_signer_ok(tmp_path: Path) -> None:
    _write_ready_sources(tmp_path / "sources")
    _write_payload(tmp_path / "sources", ready=False, signer_ok=True)
    _write_first_packet(tmp_path / "sources", ready=False, signer_ok=True)

    result = _run(tmp_path / "sources", tmp_path / "out")
    payload_action = next(row for row in result["ordered_next_actions"] if row["blocker_id"] == STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY)

    assert payload_action["action"] == "rerun payload readiness after signer OK"
    assert payload_action["exact_safe_command"] == (
        "python -m pm_bot.operator_runner.payload_dry_run_readiness_review "
        "--market BTC --strategy tiny-momentum --dry-run"
    )
    assert "signer diagnostic evidence is OK" in payload_action["preconditions"]
    assert result["validation"]["valid"] is True
    _assert_false_flags(result)


def test_all_no_live_checks_pass_leaves_only_explicit_live_auth_action(tmp_path: Path) -> None:
    _write_ready_sources(tmp_path / "sources", fake_values=True)

    result = _run(tmp_path / "sources", tmp_path / "out")
    paths = final_blocker_action_planner_artifact_paths(tmp_path / "out")
    artifact_text = _artifact_text(paths)
    top = _top_action(result)

    assert result["status"] == STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION
    assert result["blocker_count"] == 1
    assert result["non_live_checks_passed"] is True
    assert top["only_after_all_no_live_checks_pass"] is True
    assert "only in a separate operator-approved task after all no-live checks remain passing" in top["action"]
    assert top["exact_safe_command"].endswith(
        "pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet --market BTC --strategy tiny-momentum --dry-run"
    )
    assert set(path.name for path in (tmp_path / "out").iterdir() if path.is_file()) == REQUIRED_ARTIFACT_NAMES
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text
        assert fake not in json.dumps(result, sort_keys=True)
    assert result["validation"]["valid"] is True
    _assert_false_flags(result)


def test_runner_cli_outputs_summary_and_rejects_forbidden_flags(tmp_path: Path) -> None:
    _write_ready_sources(tmp_path / "sources")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.final_blocker_action_planner",
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
        cwd=Path.cwd(),
        env=_minimal_env({"POLYMARKET_API_SECRET": FAKE_SECRET_VALUES[0]}),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.final_blocker_action_planner",
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

    assert completed.returncode == 0, completed.stderr
    assert "PMBOT final blocker action planner 078J completed." in completed.stdout
    assert "Blocker count:" in completed.stdout
    assert "Top blocker:" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Trading requested: false" in completed.stdout
    assert "Ordered next actions:" in completed.stdout
    assert FAKE_SECRET_VALUES[0] not in completed.stdout
    assert forbidden.returncode != 0
    assert "unsupported flag" in forbidden.stderr


def test_runtime_files_keep_no_live_no_network_no_background_contract() -> None:
    source = (inspect.getsource(planner_module) + "\n" + inspect.getsource(runner_module)).lower()
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
        "trading_requested\": true",
        "order_submission_enabled\": true",
        "signing_by_default\": true",
    )

    for term in forbidden_terms:
        assert term not in source, term
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        assert "wallet_connected\": true" not in lowered
        assert "full_signed_payload_output\": true" not in lowered

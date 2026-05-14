from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    summarize_operator_ui_panel_v1,
)
from pm_bot.operator_runner.telegram_operator_control_bot import build_telegram_operator_control_summary
from pm_bot.trading_core.authenticated_clob_preflight import (
    authenticated_clob_preflight_artifact_paths,
    run_authenticated_clob_preflight,
)
import pm_bot.trading_core.authenticated_clob_preflight as authenticated_clob_preflight_module
from pm_bot.trading_core.authenticated_clob_preflight_models import FORCED_FALSE_EXECUTION_FIELDS
from pm_bot.trading_core.live_credentials_boundary import build_redacted_l2_credential_presence_report

GENERATED_AT = "2026-05-14T00:00:00Z"

RAW_SECRET_LIKE_VALUES = (
    "raw-l2-api-key-secret-value-057",
    "raw-l2-api-secret-value-057",
    "raw-l2-passphrase-value-057",
)

NEW_057_RUNTIME_FILES = (
    Path("pm_bot/trading_core/authenticated_clob_preflight_models.py"),
    Path("pm_bot/trading_core/authenticated_clob_preflight.py"),
    Path("pm_bot/trading_core/live_credentials_boundary.py"),
    Path("pm_bot/operator_runner/authenticated_clob_preflight.py"),
    Path("pm_bot/operator_runner/operator_ui_panel_v1.py"),
    Path("pm_bot/operator_runner/telegram_operator_control_bot.py"),
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


def _safe_l2_marker_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PMBOT_POLYMARKET_CLOB_BASE_URL": "https://clob.polymarket.com",
        "PMBOT_POLYMARKET_L2_API_KEY_PRESENT": "true",
        "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": "true",
        "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": "true",
    }
    env.update(dict(extra or {}))
    return env


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["resolved_blocker_count"] == 0


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_default_cli_runs_without_secrets_and_records_missing_config_blockers(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = authenticated_clob_preflight_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Authenticated CLOB preflight completed." in completed.stdout
    assert "Auth presence: missing" in completed.stdout
    assert "Auth header boundary: blocked" in completed.stdout
    assert "Authenticated request: skipped" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert paths["latest_status"].exists()
    assert result["status"] == "authenticated_clob_preflight_completed_fail_closed"
    assert result["credential_presence"]["missing_count"] == 4
    assert result["clob_base_url_validation"]["status"] == "missing"
    assert result["auth_header_boundary_check"]["status"] == "blocked"
    assert result["no_order_authenticated_request_plan"]["status"] == "blocked"
    assert result["authenticated_request_performed"] is False
    assert result["blocker_count"] >= 8
    _assert_required_false_flags(result)


def test_redacted_l2_credential_presence_report_never_exposes_test_secret_values() -> None:
    env = _safe_l2_marker_env(
        {
            "PMBOT_POLYMARKET_L2_API_KEY_PRESENT": RAW_SECRET_LIKE_VALUES[0],
            "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": RAW_SECRET_LIKE_VALUES[1],
            "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": RAW_SECRET_LIKE_VALUES[2],
        }
    )
    report = build_redacted_l2_credential_presence_report(
        environ=env,
        generated_at=GENERATED_AT,
    )
    rendered = json.dumps(report, sort_keys=True)

    assert report["auth_presence_check_performed"] is True
    assert report["status"] == "present_redacted"
    assert report["configured_count"] == 4
    assert report["missing_count"] == 0
    assert report["unsafe_raw_value_detected"] is True
    assert all(row["presence_status"] == "present_redacted" for row in report["env_presence_items"])
    assert report["raw_values_emitted"] is False
    assert report["actual_secret_values_exposed"] is False
    assert report["raw_credential_values_persisted"] is False
    for raw in RAW_SECRET_LIKE_VALUES:
        assert raw not in rendered


def test_artifacts_do_not_contain_raw_fake_secret_strings_and_block_unsafe_markers(tmp_path: Path) -> None:
    env = _safe_l2_marker_env(
        {
            "PMBOT_POLYMARKET_L2_API_KEY_PRESENT": RAW_SECRET_LIKE_VALUES[0],
            "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": RAW_SECRET_LIKE_VALUES[1],
            "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": RAW_SECRET_LIKE_VALUES[2],
        }
    )
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )
    artifacts = _artifact_text(authenticated_clob_preflight_artifact_paths(tmp_path))

    assert result["credential_presence"]["status"] == "present_redacted"
    assert result["credential_presence"]["unsafe_raw_value_detected"] is True
    assert result["auth_header_boundary_check"]["status"] == "blocked"
    assert result["no_order_authenticated_request_plan"]["status"] == "blocked"
    assert result["authenticated_request_performed"] is False
    assert result["signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    for raw in RAW_SECRET_LIKE_VALUES:
        assert raw not in artifacts


def test_mocked_auth_header_boundary_and_no_order_get_plan_are_default_when_markers_are_safe(
    tmp_path: Path,
) -> None:
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_safe_l2_marker_env(),
        generated_at=GENERATED_AT,
    )
    paths = authenticated_clob_preflight_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert result["status"] == "authenticated_clob_preflight_completed_live_blocked"
    assert result["credential_presence"]["status"] == "present_redacted"
    assert result["clob_base_url_validation"]["status"] == "valid_public_url_shape"
    assert result["auth_header_boundary_check"]["status"] == "checked"
    assert result["auth_header_boundary_check"]["auth_header_boundary_checked"] is True
    assert result["auth_header_boundary_checked"] is True
    assert result["no_order_authenticated_request_plan"]["status"] == "mocked"
    assert result["no_order_authenticated_request_plan"]["allowed_methods"] == ["GET"]
    assert result["no_order_authenticated_request_plan"]["blocked_methods"] == [
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ]
    assert result["no_order_auth_check_performed"] is True
    assert result["authenticated_request_performed"] is False
    assert latest_status["auth_presence_status"] == "present_redacted"
    assert latest_status["authenticated_request_performed"] is False
    assert "order submission blocked" in operator_md
    assert "order cancellation blocked" in operator_md
    assert "signing blocked" in operator_md
    assert "wallet connection blocked" in operator_md
    assert "balances blocked" in operator_md
    assert "positions blocked" in operator_md
    assert "live execution blocked" in operator_md
    _assert_required_false_flags(result)


def test_no_network_mutation_order_cancel_sign_wallet_balance_or_position_methods_are_available() -> None:
    source = inspect.getsource(authenticated_clob_preflight_module)
    forbidden_terms = (
        "py_clob_client",
        "create_order",
        "post_order",
        "submit_order",
        "cancel_order",
        "get_balance",
        "get_balances",
        "get_position",
        "get_positions",
        "create_api_key",
        "derive_api_key",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "requests.",
        "httpx.",
    )

    assert "allowed_methods\" = [\"GET\"]" not in source
    for term in forbidden_terms:
        assert term not in source.lower(), term


def test_latest_status_operator_ui_and_telegram_include_authenticated_clob_preflight_status(
    tmp_path: Path,
) -> None:
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_safe_l2_marker_env(),
        generated_at=GENERATED_AT,
    )
    latest_status = result["latest_status"]
    panel = build_operator_ui_panel_v1(
        dashboard={"authenticated_clob_preflight_status_summary": latest_status},
        latest_paths={"authenticated_clob_preflight_status": latest_status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"authenticated_clob_preflight_status_summary": latest_status},
        generated_at=GENERATED_AT,
    )

    assert panel["authenticated_clob_preflight_section_ready"] is True
    assert panel_summary["authenticated_clob_preflight_status"] == latest_status["status"]
    assert panel_summary["authenticated_clob_preflight_auth_presence_status"] == "present_redacted"
    assert panel_summary["authenticated_clob_preflight_clob_base_url_status"] == "valid_public_url_shape"
    assert panel_summary["authenticated_clob_preflight_order_submission_blocked"] is True
    assert panel_summary["authenticated_clob_preflight_signing_blocked"] is True
    assert panel_summary["authenticated_clob_preflight_wallet_connection_blocked"] is True
    assert panel_summary["authenticated_clob_preflight_live_execution_blocked"] is True
    assert telegram_summary["authenticated_clob_preflight_status_summary"]["status"] == latest_status["status"]
    assert (
        telegram_summary["authenticated_clob_preflight_status_summary"]["auth_presence_status"]
        == "present_redacted"
    )
    assert telegram_summary["authenticated_clob_preflight_status_summary"]["order_submission_blocked"] is True
    assert telegram_summary["authenticated_clob_preflight_status_summary"]["signing_blocked"] is True
    assert telegram_summary["authenticated_clob_preflight_status_summary"]["wallet_connection_blocked"] is True
    assert telegram_summary["authenticated_clob_preflight_status_summary"]["live_execution_blocked"] is True
    assert telegram_summary["no_executable_live_action"] is True


def test_existing_052_053_054_055_056_commands_still_work(tmp_path: Path) -> None:
    env = _minimal_env({"PMBOT_GAMMA_BASE_URL": "http://127.0.0.1:1"})
    commands = [
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_canary_drill",
            "--market",
            "BTC",
            "--dry-run",
            "--artifact-dir",
            str(tmp_path / "paper_canary_drill_052"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_trading_loop",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "paper_trading_loop_053"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.public_market_paper_loop",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--offline-fixture-only",
            "--artifacts-dir",
            str(tmp_path / "public_market_paper_loop_054"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_decision_ledger",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--source",
            "public_market_loop_054",
            "--artifacts-dir",
            str(tmp_path / "paper_decision_ledger_055"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_connector_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "live_connector_preflight_056"),
        ],
    ]
    outputs = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        outputs.append(completed.stdout)
        assert completed.returncode == 0, completed.stderr

    assert "Paper canary drill completed." in outputs[0]
    assert "Paper trading loop completed." in outputs[1]
    assert "Public market paper loop completed." in outputs[2]
    assert "Paper decision ledger updated." in outputs[3]
    assert "Live connector preflight completed." in outputs[4]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in NEW_057_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in lowered, path

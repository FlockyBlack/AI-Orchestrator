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
    clob_l2_marker_preflight_artifact_paths,
    run_authenticated_clob_preflight,
    run_clob_l2_marker_preflight,
)
import pm_bot.trading_core.authenticated_clob_preflight as authenticated_clob_preflight_module
import pm_bot.trading_core.live_credentials_boundary as live_credentials_boundary_module
from pm_bot.trading_core.authenticated_clob_preflight_models import FORCED_FALSE_EXECUTION_FIELDS

GENERATED_AT = "2026-05-14T00:00:00Z"

RAW_SECRET_LIKE_VALUES = (
    "raw-l2-api-key-secret-value-058",
    "raw-l2-api-secret-value-058",
    "raw-l2-passphrase-value-058",
)

NEW_058_RUNTIME_FILES = (
    Path("pm_bot/trading_core/authenticated_clob_preflight.py"),
    Path("pm_bot/trading_core/authenticated_clob_preflight_models.py"),
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


def _safe_marker_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PMBOT_POLYMARKET_CLOB_BASE_URL": "https://clob.polymarket.com",
        "PMBOT_POLYMARKET_L2_API_KEY_PRESENT": "true",
        "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": "present",
        "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": "1",
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


def _blocker_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row.get("blocker_id")) for row in result.get("blockers", []) if isinstance(row, Mapping)}


def test_cli_default_preflight_records_missing_config_and_marker_blockers(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--mock-auth",
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
    paths = clob_l2_marker_preflight_artifact_paths(tmp_path / "clob_l2_marker_preflight_058")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Authenticated CLOB preflight completed." in completed.stdout
    assert "CLOB/L2 marker preflight: clob_l2_marker_preflight_fail_closed" in completed.stdout
    assert paths["latest_status"].exists()
    assert result["status"] == "clob_l2_marker_preflight_fail_closed"
    assert result["clob_base_url_config"]["status"] == "missing"
    assert result["redacted_l2_marker_presence"]["status"] == "missing"
    assert result["redacted_l2_marker_presence"]["missing_count"] == 3
    assert result["no_order_auth_boundary_plan"]["status"] == "blocked"
    assert result["no_order_auth_boundary_plan"]["authenticated_request_performed"] is False
    assert {"clob_base_url_missing", "l2_markers_missing"}.issubset(_blocker_ids(result))
    _assert_required_false_flags(result)


def test_valid_clob_base_url_and_complete_l2_markers_are_recognized_without_live_enablement(
    tmp_path: Path,
) -> None:
    result = run_clob_l2_marker_preflight(
        market="BTC",
        dry_run=True,
        mock_auth=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )
    paths = clob_l2_marker_preflight_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))

    assert result["status"] == "clob_l2_marker_preflight_ready_live_blocked"
    assert result["clob_base_url_config"]["status"] == "valid_public_url_shape"
    assert result["clob_base_url_config"]["public_clob_base_url"] == "https://clob.polymarket.com"
    assert result["clob_base_url_config"]["is_production_clob_base_url"] is True
    assert result["redacted_l2_marker_presence"]["status"] == "present_redacted"
    assert result["redacted_l2_marker_presence"]["marker_set_complete"] is True
    assert result["unsafe_l2_marker_detection"]["unsafe_raw_value_detected"] is False
    assert result["no_order_auth_boundary_plan"]["status"] == "mocked"
    assert result["no_order_auth_boundary_plan"]["auth_boundary_mock_checked"] is True
    assert result["no_order_auth_boundary_plan"]["no_order_auth_plan_ready"] is True
    assert result["authenticated_request_performed"] is False
    assert latest_status["auth_marker_presence_detected"] is True
    assert latest_status["authenticated_request_skipped_by_default"] is True
    _assert_required_false_flags(result)


def test_invalid_clob_base_url_blocks_no_order_auth_plan(tmp_path: Path) -> None:
    result = run_clob_l2_marker_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env({"PMBOT_POLYMARKET_CLOB_BASE_URL": "ftp://clob.polymarket.com"}),
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "clob_l2_marker_preflight_fail_closed"
    assert result["clob_base_url_config"]["status"] == "invalid_scheme"
    assert result["clob_base_url_config"]["clob_base_url_valid"] is False
    assert result["no_order_auth_boundary_plan"]["no_order_auth_plan_ready"] is False
    assert "clob_base_url_invalid" in _blocker_ids(result)
    _assert_required_false_flags(result)


def test_incomplete_l2_marker_set_is_blocked(tmp_path: Path) -> None:
    env = _safe_marker_env()
    env.pop("PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT")
    result = run_clob_l2_marker_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )

    assert result["redacted_l2_marker_presence"]["status"] == "incomplete"
    assert result["redacted_l2_marker_presence"]["marker_set_complete"] is False
    assert result["redacted_l2_marker_presence"]["missing_count"] == 1
    assert result["auth_marker_presence_detected"] is False
    assert "l2_markers_incomplete" in _blocker_ids(result)
    _assert_required_false_flags(result)


def test_unsafe_raw_like_marker_values_are_detected_without_outputting_values(tmp_path: Path) -> None:
    env = _safe_marker_env(
        {
            "PMBOT_POLYMARKET_L2_API_KEY_PRESENT": RAW_SECRET_LIKE_VALUES[0],
            "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": RAW_SECRET_LIKE_VALUES[1],
            "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": RAW_SECRET_LIKE_VALUES[2],
        }
    )
    result = run_clob_l2_marker_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )
    artifacts = _artifact_text(clob_l2_marker_preflight_artifact_paths(tmp_path))

    assert result["redacted_l2_marker_presence"]["status"] == "unsafe_raw_value_detected"
    assert result["redacted_l2_marker_presence"]["unsafe_raw_value_detected"] is True
    assert result["unsafe_l2_marker_detection"]["unsafe_raw_value_detected"] is True
    assert result["no_order_auth_boundary_plan"]["status"] == "blocked"
    assert "unsafe_raw_l2_marker_value" in _blocker_ids(result)
    assert result["redacted_l2_marker_presence"]["value_hashes_emitted"] is False
    for raw in RAW_SECRET_LIKE_VALUES:
        assert raw not in artifacts
    _assert_required_false_flags(result)


def test_mock_auth_uses_marker_presence_only_and_never_performs_authenticated_request(
    tmp_path: Path,
) -> None:
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        mock_auth=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )
    marker_summary = result["clob_l2_marker_preflight_status_summary"]

    assert marker_summary["status"] == "clob_l2_marker_preflight_ready_live_blocked"
    assert marker_summary["auth_marker_presence_detected"] is True
    assert marker_summary["auth_boundary_mock_checked"] is True
    assert marker_summary["no_order_auth_plan_ready"] is True
    assert marker_summary["authenticated_request_performed"] is False
    assert result["authenticated_request_performed"] is False
    assert result["auth_marker_presence_detected"] is True
    assert result["auth_boundary_mock_checked"] is True
    assert result["no_order_auth_plan_ready"] is True
    _assert_required_false_flags(result)


def test_no_network_mutation_order_cancel_sign_wallet_balance_or_position_calls_are_added() -> None:
    source = "\n".join(
        [
            inspect.getsource(authenticated_clob_preflight_module),
            inspect.getsource(live_credentials_boundary_module),
        ]
    ).lower()
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

    for term in forbidden_terms:
        assert term not in source, term


def test_operator_markdown_and_latest_status_are_written_with_blocked_safety(tmp_path: Path) -> None:
    result = run_clob_l2_marker_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )
    paths = clob_l2_marker_preflight_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert latest_status["status"] == result["status"]
    assert "order submission blocked" in operator_md
    assert "order cancellation blocked" in operator_md
    assert "signing blocked" in operator_md
    assert "signed payload generation blocked" in operator_md
    assert "wallet connection blocked" in operator_md
    assert "balances blocked" in operator_md
    assert "positions blocked" in operator_md
    assert "live execution blocked" in operator_md
    _assert_required_false_flags(latest_status)


def test_ui_and_telegram_passive_summaries_include_058_marker_status(tmp_path: Path) -> None:
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )
    latest_status = result["latest_status"]
    panel = build_operator_ui_panel_v1(
        dashboard={"authenticated_clob_preflight_status_summary": latest_status},
        latest_paths={
            "authenticated_clob_preflight_status": latest_status["latest_status_path"],
            "clob_l2_marker_preflight_status": result["latest_clob_l2_marker_preflight_status_path"],
        },
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"authenticated_clob_preflight_status_summary": latest_status},
        generated_at=GENERATED_AT,
    )

    assert panel["clob_l2_marker_preflight_section_ready"] is True
    assert panel_summary["clob_l2_marker_preflight_status"] == "clob_l2_marker_preflight_ready_live_blocked"
    assert panel_summary["clob_l2_marker_preflight_clob_base_url_configured"] is True
    assert panel_summary["clob_l2_marker_preflight_l2_marker_set_complete"] is True
    assert panel_summary["clob_l2_marker_preflight_unsafe_raw_value_detected"] is False
    assert panel_summary["clob_l2_marker_preflight_no_order_auth_plan_ready"] is True
    assert panel_summary["authenticated_clob_preflight_order_submission_blocked"] is True
    assert telegram_summary["clob_l2_marker_preflight_status_summary"]["status"] == (
        "clob_l2_marker_preflight_ready_live_blocked"
    )
    assert telegram_summary["clob_l2_marker_preflight_status_summary"]["l2_marker_set_complete"] is True
    assert telegram_summary["clob_l2_marker_preflight_status_summary"]["unsafe_raw_value_detected"] is False
    assert telegram_summary["no_executable_live_action"] is True


def test_existing_052_053_054_055_056_057_commands_still_work(tmp_path: Path) -> None:
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
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--mock-auth",
            "--artifacts-dir",
            str(tmp_path / "authenticated_clob_preflight_057"),
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
    assert "Authenticated CLOB preflight completed." in outputs[5]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in NEW_058_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in lowered, path

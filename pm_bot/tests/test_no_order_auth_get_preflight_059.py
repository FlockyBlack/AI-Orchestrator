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
    no_order_auth_get_preflight_artifact_paths,
    run_authenticated_clob_preflight,
    run_no_order_auth_get_preflight,
    validate_safe_no_order_auth_get_endpoint,
)
import pm_bot.trading_core.authenticated_clob_preflight as authenticated_clob_preflight_module
from pm_bot.trading_core.authenticated_clob_preflight_models import FORCED_FALSE_EXECUTION_FIELDS

GENERATED_AT = "2026-05-14T00:00:00Z"

RAW_SECRET_LIKE_VALUES = (
    "raw-l2-api-key-secret-value-059",
    "raw-l2-api-secret-value-059",
    "raw-l2-passphrase-value-059",
)

NEW_059_RUNTIME_FILES = (
    Path("pm_bot/trading_core/authenticated_clob_preflight_models.py"),
    Path("pm_bot/trading_core/authenticated_clob_preflight.py"),
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
        "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": "true",
        "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": "true",
    }
    env.update(dict(extra or {}))
    return env


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["private_key_read"] is False
    assert value["signing_attempted"] is False
    assert value["signed_payload_generated"] is False
    assert value["order_submission_attempted"] is False
    assert value["order_cancellation_attempted"] is False
    assert value["balance_read_attempted"] is False
    assert value["position_read_attempted"] is False
    assert value["wallet_connection_attempted"] is False
    assert value["live_execution_approved"] is False
    assert value["allowed_for_live"] is False
    assert value["credentials_values_exposed"] is False
    assert value["resolved_blocker_count"] == 0


def _blocker_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row.get("blocker_id")) for row in result.get("blockers", []) if isinstance(row, Mapping)}


def test_no_order_auth_get_uses_mocked_path_by_default_without_credentials_or_network(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--no-order-auth-get",
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
    paths = no_order_auth_get_preflight_artifact_paths(tmp_path / "no_order_auth_get_preflight_059")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Authenticated CLOB preflight completed." in completed.stdout
    assert "No-order auth GET: mocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert result["status"] == "no_order_auth_get_preflight_mocked_live_blocked"
    assert result["no_order_auth_get_status"] == "mocked"
    assert result["no_order_auth_get_requested"] is True
    assert result["real_auth_read_only_requested"] is False
    assert result["real_authenticated_get_performed"] is False
    assert result["request_method"] == "GET"
    assert result["auth_used"] is False
    assert result["credentials_used"] == "redacted_presence_only"
    assert paths["response_evidence"].exists()
    _assert_required_false_flags(result)


def test_real_auth_read_only_without_no_order_auth_get_is_blocked_not_crashed(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--real-auth-read-only",
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
    paths = no_order_auth_get_preflight_artifact_paths(tmp_path / "no_order_auth_get_preflight_059")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "No-order auth GET: blocked" in completed.stdout
    assert "real_auth_read_only_requires_no_order_auth_get" in _blocker_ids(result)
    assert result["real_auth_read_only_requested"] is True
    assert result["real_authenticated_get_performed"] is False
    assert result["auth_used"] is False
    _assert_required_false_flags(result)


def test_real_auth_read_only_missing_env_opt_in_is_blocked(tmp_path: Path) -> None:
    result = run_no_order_auth_get_preflight(
        market="BTC",
        dry_run=True,
        no_order_auth_get_requested=True,
        real_auth_read_only_requested=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )

    assert result["no_order_auth_get_status"] == "blocked"
    assert result["real_auth_read_only_requested"] is True
    assert result["real_auth_read_only_opt_in_present"] is False
    assert result["real_authenticated_get_performed"] is False
    assert result["auth_used"] is False
    assert "real_no_order_auth_get_not_enabled" in _blocker_ids(result)
    assert not no_order_auth_get_preflight_artifact_paths(tmp_path)["response_evidence"].exists()
    _assert_required_false_flags(result)


def test_real_auth_read_only_with_env_opt_in_still_blocks_without_safe_endpoint(tmp_path: Path) -> None:
    result = run_no_order_auth_get_preflight(
        market="BTC",
        dry_run=True,
        no_order_auth_get_requested=True,
        real_auth_read_only_requested=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env({"PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET": "true"}),
        generated_at=GENERATED_AT,
    )

    assert result["no_order_auth_get_status"] == "blocked"
    assert result["real_auth_read_only_opt_in_present"] is True
    assert result["endpoint_safe_for_no_order_check"] is False
    assert result["endpoint_blocked_reason"] == "no_clearly_safe_authenticated_get_endpoint"
    assert result["real_authenticated_get_performed"] is False
    assert result["auth_used"] is False
    assert "no_clearly_safe_authenticated_get_endpoint" in _blocker_ids(result)
    _assert_required_false_flags(result)


def test_safe_endpoint_allowlist_accepts_only_mock_safe_get_and_denylist_blocks_private_scopes() -> None:
    allowed = validate_safe_no_order_auth_get_endpoint("/auth/no-order-boundary/mock-get")
    assert allowed["status"] == "checked"
    assert allowed["endpoint_safe_for_no_order_check"] is True
    assert allowed["request_method"] == "GET"

    non_get = validate_safe_no_order_auth_get_endpoint(
        "/auth/no-order-boundary/mock-get",
        request_method="POST",
    )
    assert non_get["status"] == "blocked"
    assert non_get["endpoint_blocked_reason"] == "non_get_method_blocked"

    for path in (
        "/order",
        "/orders",
        "/cancel",
        "/balance",
        "/balances",
        "/position",
        "/positions",
        "/fill",
        "/fills",
        "/trade",
        "/trades",
        "/wallet",
        "/allowance",
        "/approvals",
    ):
        blocked = validate_safe_no_order_auth_get_endpoint(path)
        assert blocked["status"] == "blocked", path
        assert blocked["endpoint_safe_for_no_order_check"] is False
        assert blocked["endpoint_blocked_reason"].startswith("forbidden_endpoint:"), path


def test_artifacts_never_contain_fake_secret_values_and_credentials_are_never_exposed(tmp_path: Path) -> None:
    env = _safe_marker_env(
        {
            "PMBOT_POLYMARKET_L2_API_KEY_PRESENT": RAW_SECRET_LIKE_VALUES[0],
            "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT": RAW_SECRET_LIKE_VALUES[1],
            "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT": RAW_SECRET_LIKE_VALUES[2],
        }
    )
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        no_order_auth_get_requested=True,
        artifact_dir=tmp_path,
        environ=env,
        generated_at=GENERATED_AT,
    )
    paths = no_order_auth_get_preflight_artifact_paths(tmp_path / "no_order_auth_get_preflight_059")
    artifacts = _artifact_text(paths)

    assert result["no_order_auth_get_status"] == "mocked"
    assert result["no_order_auth_get_preflight_status_summary"]["credentials_values_exposed"] is False
    for raw in RAW_SECRET_LIKE_VALUES:
        assert raw not in artifacts


def test_latest_status_operator_markdown_and_safety_flags_are_written(tmp_path: Path) -> None:
    result = run_no_order_auth_get_preflight(
        market="BTC",
        dry_run=True,
        no_order_auth_get_requested=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )
    paths = no_order_auth_get_preflight_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert latest_status["no_order_auth_get_status"] == "mocked"
    assert latest_status["request_method"] == "GET"
    assert "order submission blocked" in operator_md
    assert "order cancellation blocked" in operator_md
    assert "signing blocked" in operator_md
    assert "wallet connection blocked" in operator_md
    assert "live execution blocked" in operator_md
    _assert_required_false_flags(result)
    _assert_required_false_flags(latest_status)


def test_ui_and_telegram_passive_summaries_include_059_status(tmp_path: Path) -> None:
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        no_order_auth_get_requested=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )
    latest_status = result["latest_status"]
    no_order_status = result["no_order_auth_get_preflight_status_summary"]
    panel = build_operator_ui_panel_v1(
        dashboard={
            "authenticated_clob_preflight_status_summary": latest_status,
            "no_order_auth_get_preflight_status_summary": no_order_status,
        },
        latest_paths={
            "authenticated_clob_preflight_status": latest_status["latest_status_path"],
            "no_order_auth_get_preflight_status": no_order_status["latest_status_path"],
        },
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"authenticated_clob_preflight_status_summary": latest_status},
        generated_at=GENERATED_AT,
    )

    assert panel["no_order_auth_get_preflight_section_ready"] is True
    assert panel_summary["no_order_auth_get_status"] == "mocked"
    assert panel_summary["no_order_auth_get_clob_base_url_status"] == "valid_public_url_shape"
    assert panel_summary["no_order_auth_get_l2_marker_status"] == "present_redacted"
    assert panel_summary["no_order_auth_get_order_submission_blocked"] is True
    assert panel_summary["no_order_auth_get_signing_blocked"] is True
    assert panel_summary["no_order_auth_get_wallet_connection_blocked"] is True
    assert panel_summary["no_order_auth_get_live_execution_blocked"] is True
    assert telegram_summary["no_order_auth_get_preflight_status_summary"]["no_order_auth_get_status"] == "mocked"
    assert telegram_summary["no_order_auth_get_preflight_status_summary"]["order_submission_blocked"] is True
    assert telegram_summary["no_order_auth_get_preflight_status_summary"]["signing_blocked"] is True
    assert telegram_summary["no_order_auth_get_preflight_status_summary"]["wallet_connection_blocked"] is True
    assert telegram_summary["no_order_auth_get_preflight_status_summary"]["live_execution_blocked"] is True
    assert telegram_summary["no_executable_live_action"] is True


def test_marker_simulation_keeps_058_ready_and_059_mocked(tmp_path: Path) -> None:
    result = run_authenticated_clob_preflight(
        market="BTC",
        dry_run=True,
        mock_auth=True,
        no_order_auth_get_requested=True,
        artifact_dir=tmp_path,
        environ=_safe_marker_env(),
        generated_at=GENERATED_AT,
    )

    assert result["credential_presence"]["status"] == "present_redacted"
    assert result["clob_base_url_validation"]["status"] == "valid_public_url_shape"
    assert result["clob_l2_marker_preflight_status_summary"]["status"] == (
        "clob_l2_marker_preflight_ready_live_blocked"
    )
    assert result["auth_header_boundary_check"]["status"] == "checked"
    assert result["no_order_authenticated_request_plan"]["status"] == "mocked"
    assert result["no_order_auth_get_status"] == "mocked"
    assert result["real_authenticated_get_performed"] is False
    _assert_required_false_flags(result)


def test_no_post_put_patch_delete_signing_wallet_order_balance_or_position_calls_added() -> None:
    source = inspect.getsource(authenticated_clob_preflight_module).lower()
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


def test_existing_052_053_054_055_056_057_058_commands_still_work(tmp_path: Path) -> None:
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
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--no-order-auth-get",
            "--artifacts-dir",
            str(tmp_path / "no_order_auth_get_059"),
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
    assert "No-order auth GET: mocked" in outputs[6]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in NEW_059_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in lowered, path

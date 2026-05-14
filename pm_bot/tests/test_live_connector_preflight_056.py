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
from pm_bot.trading_core.live_connector_preflight import (
    LiveConnectorPublicPreflightClient,
    live_connector_preflight_artifact_paths,
    run_live_connector_preflight,
)
import pm_bot.trading_core.live_connector_preflight as live_connector_preflight_module
from pm_bot.trading_core.live_connector_preflight_models import FORCED_FALSE_EXECUTION_FIELDS
from pm_bot.trading_core.live_credentials_boundary import build_live_credentials_presence_report
from pm_bot.trading_core.public_gamma_market_client import build_default_public_gamma_fixture

GENERATED_AT = "2026-05-14T00:00:00Z"

RAW_SECRET_LIKE_VALUES = (
    "sk-test-secret-like-value-056",
    "bearer raw-token-056",
    "mnemonic: one two three four",
)

NEW_056_RUNTIME_FILES = (
    Path("pm_bot/trading_core/live_connector_preflight_models.py"),
    Path("pm_bot/trading_core/live_credentials_boundary.py"),
    Path("pm_bot/trading_core/live_connector_preflight.py"),
    Path("pm_bot/operator_runner/live_connector_preflight.py"),
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


def _ok_transport(calls: list[dict[str, Any]]):
    def transport(url: str, timeout: float) -> tuple[int | None, Any]:
        calls.append({"method": "GET", "url": url, "timeout": timeout})
        return 200, build_default_public_gamma_fixture(market="BTC", generated_at=GENERATED_AT)

    return transport


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "paper_or_preflight"
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


def test_default_cli_runs_without_secrets_and_writes_fail_closed_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_connector_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env({"PMBOT_GAMMA_BASE_URL": "http://127.0.0.1:1"}),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = live_connector_preflight_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Live connector preflight completed." in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert paths["latest_status"].exists()
    assert result["public_network_check_performed"] is True
    assert result["auth_presence_check_performed"] is False
    assert result["allowed_for_live"] is False
    _assert_required_false_flags(result)


def test_public_only_preflight_uses_mocked_get_and_writes_required_artifacts(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    result = run_live_connector_preflight(
        market="BTC",
        dry_run=True,
        public_only=True,
        artifact_dir=tmp_path,
        public_client=LiveConnectorPublicPreflightClient(transport=_ok_transport(calls)),
        generated_at=GENERATED_AT,
    )
    paths = live_connector_preflight_artifact_paths(tmp_path)

    assert result["status"] == "preflight_completed_live_blocked"
    assert result["public_network_check_performed"] is True
    assert result["auth_presence_check_performed"] is False
    assert result["network_preflight"]["public_network_status"] == "ok"
    assert result["auth_boundary"]["auth_boundary_status"] == "skipped"
    assert [call["method"] for call in calls] == ["GET"]
    for key in (
        "result",
        "operator_md",
        "latest_status",
        "network_evidence",
        "credential_presence",
        "blockers",
    ):
        assert paths[key].exists(), key
    _assert_required_false_flags(result)


def test_credential_presence_report_redacts_all_values() -> None:
    env = {
        "PMBOT_POLYMARKET_LIVE_PREFLIGHT_ENABLED": RAW_SECRET_LIKE_VALUES[0],
        "PMBOT_POLYMARKET_CLOB_BASE_URL": "https://clob.polymarket.com",
        "PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT": RAW_SECRET_LIKE_VALUES[1],
        "PMBOT_POLYMARKET_API_KEY_CONFIGURED": "true",
        "PMBOT_POLYMARKET_API_SECRET_CONFIGURED": RAW_SECRET_LIKE_VALUES[2],
        "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED": "true",
    }
    report = build_live_credentials_presence_report(
        environ=env,
        auth_check=True,
        generated_at=GENERATED_AT,
    )
    rendered = json.dumps(report, sort_keys=True)

    assert report["auth_presence_check_performed"] is True
    assert report["configured_count"] == 6
    assert report["missing_count"] == 0
    assert all(row["value_length_category"] == "present_redacted" for row in report["env_presence_items"])
    assert report["raw_values_emitted"] is False
    assert report["actual_secret_values_exposed"] is False
    for raw in RAW_SECRET_LIKE_VALUES:
        assert raw not in rendered


def test_auth_check_artifacts_do_not_contain_raw_secret_like_values(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    env = {
        "PMBOT_POLYMARKET_LIVE_PREFLIGHT_ENABLED": RAW_SECRET_LIKE_VALUES[0],
        "PMBOT_POLYMARKET_CLOB_BASE_URL": "https://clob.polymarket.com",
        "PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT": "true",
        "PMBOT_POLYMARKET_API_KEY_CONFIGURED": RAW_SECRET_LIKE_VALUES[1],
        "PMBOT_POLYMARKET_API_SECRET_CONFIGURED": "true",
        "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED": RAW_SECRET_LIKE_VALUES[2],
    }
    result = run_live_connector_preflight(
        market="BTC",
        dry_run=True,
        public_only=False,
        auth_check=True,
        network_check=True,
        artifact_dir=tmp_path,
        public_client=LiveConnectorPublicPreflightClient(
            clob_base_url="https://clob.polymarket.com",
            transport=_ok_transport(calls),
        ),
        environ=env,
        generated_at=GENERATED_AT,
    )
    paths = live_connector_preflight_artifact_paths(tmp_path)
    artifacts = _artifact_text(paths)

    assert result["auth_presence_check_performed"] is True
    assert result["authenticated_request_performed"] is False
    assert result["order_submission_attempted"] is False
    assert result["signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    assert result["network_preflight"]["clob_public_read_status"] == "skipped"
    assert [call["method"] for call in calls] == ["GET"]
    for raw in RAW_SECRET_LIKE_VALUES:
        assert raw not in artifacts


def test_auth_check_never_enables_order_signing_payload_or_wallet_flags(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    result = run_live_connector_preflight(
        market="BTC",
        dry_run=True,
        public_only=False,
        auth_check=True,
        artifact_dir=tmp_path,
        public_client=LiveConnectorPublicPreflightClient(transport=_ok_transport(calls)),
        environ={},
        generated_at=GENERATED_AT,
    )

    assert result["auth_boundary"]["auth_boundary_status"] == "missing"
    assert result["authenticated_request_performed"] is False
    assert result["order_submission_attempted"] is False
    assert result["order_cancellation_attempted"] is False
    assert result["signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    assert result["wallet_connection_attempted"] is False
    assert result["wallet_spend_enabled"] is False
    _assert_required_false_flags(result)


def test_no_non_get_calls_and_no_wallet_signing_order_methods_exist_on_preflight_client() -> None:
    public_methods = {name for name in dir(LiveConnectorPublicPreflightClient) if not name.startswith("_")}
    source = inspect.getsource(live_connector_preflight_module)

    assert public_methods == {"check_public_clob_shape", "check_public_gamma"}
    for forbidden_method_term in ("wallet", "sign", "order", "submit", "cancel", "balance", "position"):
        assert all(forbidden_method_term not in name.lower() for name in public_methods)
    assert "method=\"POST\"" not in source
    assert "method=\"PUT\"" not in source
    assert "method=\"PATCH\"" not in source
    assert "method=\"DELETE\"" not in source


def test_latest_status_operator_markdown_and_passive_surfaces_include_preflight_status(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    result = run_live_connector_preflight(
        market="BTC",
        dry_run=True,
        public_only=True,
        artifact_dir=tmp_path,
        public_client=LiveConnectorPublicPreflightClient(transport=_ok_transport(calls)),
        generated_at=GENERATED_AT,
    )
    paths = live_connector_preflight_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")
    panel = build_operator_ui_panel_v1(
        dashboard={"live_connector_preflight_status_summary": latest_status},
        latest_paths={"live_connector_preflight_status": latest_status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"live_connector_preflight_status_summary": latest_status},
        generated_at=GENERATED_AT,
    )

    assert latest_status["public_network_status"] == "ok"
    assert latest_status["auth_boundary_status"] == "skipped"
    assert latest_status["order_submission_enabled"] is False
    assert "order submission blocked" in operator_md
    assert "signing blocked" in operator_md
    assert "live execution blocked" in operator_md
    assert panel["live_connector_preflight_section_ready"] is True
    assert panel_summary["live_connector_preflight_public_network_status"] == "ok"
    assert panel_summary["live_connector_preflight_auth_boundary_status"] == "skipped"
    assert panel_summary["live_connector_preflight_order_submission_blocked"] is True
    assert telegram_summary["live_connector_preflight_status_summary"]["public_network_status"] == "ok"
    assert telegram_summary["live_connector_preflight_status_summary"]["order_submission_blocked"] is True
    assert telegram_summary["no_executable_live_action"] is True
    assert result["latest_status"]["artifact_path"] == paths["result"].as_posix()


def test_existing_052_053_054_055_commands_still_work(tmp_path: Path) -> None:
    env = _minimal_env()
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
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in NEW_056_RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in lowered, path

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_status_registry import (
    SAFE_ACTIONS,
    build_telegram_console_context,
    build_telegram_status_registry_snapshot,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
    telegram_console_safety_state,
    validate_safe_action,
)
from pm_bot.trading_core.static_safety_invariant_report import run_static_safety_invariant_report

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
TINY_ACTION_ID = "run_tiny_order_scaffold_061"
TINY_CALLBACK = "pmbot:run:tiny_order_scaffold_061"
TINY_COMMAND_DISPLAY = (
    "python",
    "-m",
    "pm_bot.operator_runner.tiny_order_scaffold",
    "--market",
    "BTC",
    "--strategy",
    "tiny-momentum",
    "--dry-run",
)

FORBIDDEN_BUTTON_TEXT = (
    "Send Order",
    "Submit Order",
    "Cancel Order",
    "Sign Payload",
    "Approve Live",
    "Enable Live",
    "Connect Wallet",
    "View Balance",
    "View Position",
    "View Fills",
    "Execute Trade",
    "Trade Now",
)

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_061_artifacts(root: Path) -> Path:
    artifact_dir = root / "tiny_order_scaffold_061"
    safety = telegram_console_safety_state()
    latest_path = artifact_dir / "latest_tiny_order_scaffold_status_061.json"
    candidate_path = artifact_dir / "tiny_order_candidate_061.json"
    approval_path = artifact_dir / "manual_tiny_order_approval_packet_061.json"
    hard_limits_path = artifact_dir / "tiny_order_hard_limits_061.json"
    submission_path = artifact_dir / "tiny_order_submission_availability_061.json"
    common = {
        "task_id": "ORCH-PMBOT-TRADING-MVP-061-MANUAL-APPROVED-TINY-ORDER-SCAFFOLD-NO-SUBMISSION",
        "generated_at": GENERATED_AT,
        "market": "BTC",
        "market_symbol": "BTC",
        "strategy_name": "tiny-momentum",
        "mode": "preflight / review-only",
        "execution_mode": "preflight",
        "review_only": True,
        "preflight_only": True,
        "scaffold_only": True,
        "operator_approved": False,
        "candidate_is_executable": False,
        "hard_limits_passed": True,
        "blocker_count": 7,
        "top_blocker_reasons": [
            "Manual operator approval is required and operator_approved remains false.",
            "Signing is blocked.",
            "Order submission is blocked.",
            "Live execution is blocked.",
        ],
        **safety,
    }
    _write_json(
        candidate_path,
        {
            **common,
            "contract_version": "pmbot_tiny_order_candidate_061.v1",
            "status": "created",
            "candidate_outcome": "Yes",
            "candidate_side": "paper_track_outcome",
            "candidate_limit_price": 0.52,
            "candidate_size": 1.0,
            "candidate_notional": 0.52,
            "operator_summary": "Tiny order candidate was created for manual review only and is not executable.",
        },
    )
    _write_json(
        approval_path,
        {
            **common,
            "contract_version": "pmbot_manual_tiny_order_approval_packet_061.v1",
            "status": "created",
            "approval_packet_created": True,
            "approval_required": True,
            "operator_must_not_execute_from_packet": True,
            "operator_summary": "Manual approval packet was created for review only.",
        },
    )
    _write_json(
        hard_limits_path,
        {
            **common,
            "contract_version": "pmbot_tiny_order_hard_limits_061.v1",
            "status": "created",
            "max_notional": 1.0,
            "max_size": 1.0,
            "max_price": 0.99,
            "operator_summary": "Tiny hard limits passed for the review object.",
        },
    )
    _write_json(
        submission_path,
        {
            **common,
            "contract_version": "pmbot_tiny_order_submission_availability_061.v1",
            "status": "blocked",
            "signing_blocked": True,
            "signed_payload_unavailable": True,
            "order_submission_blocked": True,
            "order_cancellation_blocked": True,
            "wallet_connection_blocked": True,
            "live_execution_blocked": True,
            "operator_summary": "Order submission and cancellation remain unavailable.",
        },
    )
    _write_json(
        latest_path,
        {
            **common,
            "contract_version": "pmbot_latest_tiny_order_scaffold_status_061.v1",
            "status": "tiny_order_scaffold_completed_live_blocked",
            "tiny_candidate": "created",
            "approval_packet": "created",
            "approval_packet_created": True,
            "candidate_outcome": "Yes",
            "candidate_side": "paper_track_outcome",
            "candidate_limit_price": 0.52,
            "candidate_size": 1.0,
            "candidate_notional": 0.52,
            "max_notional": 1.0,
            "max_size": 1.0,
            "max_price": 0.99,
            "signing": "blocked",
            "signed_payload_status": "unavailable",
            "order_submission": "blocked",
            "wallet": "blocked",
            "live_execution": "blocked",
            "artifact_path": (artifact_dir / "tiny_order_scaffold_061_result.json").as_posix(),
            "latest_status_path": latest_path.as_posix(),
            "tiny_order_candidate_path": candidate_path.as_posix(),
            "manual_tiny_order_approval_packet_path": approval_path.as_posix(),
            "tiny_order_hard_limits_path": hard_limits_path.as_posix(),
            "tiny_order_submission_availability_path": submission_path.as_posix(),
        },
    )
    return artifact_dir


def _adapter(
    *,
    context: Mapping[str, Any],
    action_runner=None,  # type: ignore[no-untyped-def]
) -> runtime.TelegramOperatorRuntimeAdapter:
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        action_runner=action_runner,
        generated_at=GENERATED_AT,
    )
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        bot=bot,
    )


def _button_labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def test_registry_reads_061_tiny_scaffold_latest_status_and_companion_artifacts(tmp_path: Path) -> None:
    _write_061_artifacts(tmp_path)

    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)
    card = snapshot["cards_by_flow"]["tiny_order_scaffold_061"]
    summary = card["status_summary"]
    review = snapshot["tiny_order_review_061t"]

    assert card["available"] is True
    assert summary["status"] == "tiny_order_scaffold_completed_live_blocked"
    assert summary["tiny_candidate_status"] == "created"
    assert summary["approval_packet_path"].endswith("manual_tiny_order_approval_packet_061.json")
    assert summary["operator_approved"] is False
    assert summary["candidate_is_executable"] is False
    assert summary["hard_limits_summary"]["hard_limits_passed"] is True
    assert summary["hard_limits_summary"]["max_notional"] == 1.0
    assert summary["submission_status"]["signing_blocked"] is True
    assert summary["submission_status"]["order_submission_blocked"] is True
    assert summary["submission_status"]["live_execution_blocked"] is True
    assert review["run_tiny_scaffold_command"] == list(TINY_COMMAND_DISPLAY)
    assert review["operator_approved"] is False
    assert review["candidate_is_executable"] is False


def test_missing_061_artifacts_do_not_crash_and_remain_blocked(tmp_path: Path) -> None:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)
    card = snapshot["cards_by_flow"]["tiny_order_scaffold_061"]
    summary = card["status_summary"]

    assert card["available"] is False
    assert card["status"] == "not_available"
    assert summary["tiny_candidate_status"] == "not_available"
    assert summary["operator_approved"] is False
    assert summary["candidate_is_executable"] is False
    assert summary["signing_blocked"] is True
    assert summary["order_submission_blocked"] is True
    assert summary["wallet_connection_blocked"] is True
    assert summary["live_execution_blocked"] is True


def test_telegram_menu_includes_tiny_order_review_and_no_forbidden_controls(tmp_path: Path) -> None:
    _write_061_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")

    panel = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    labels = _button_labels(panel)
    all_console_labels = tuple(label for row in telegram_console_button_rows("en") for label, _ in row)
    rendered_labels = " ".join((*labels, *all_console_labels))

    assert "Tiny Order Review" in panel.text
    assert "Tiny Candidate" in panel.text
    assert "Approval Packet" in panel.text
    assert "Hard Limits" in panel.text
    assert "Submission Status" in panel.text
    assert "Run Tiny Scaffold Dry-Run" in panel.text
    assert "Run Tiny Scaffold 061" in labels
    for forbidden in FORBIDDEN_BUTTON_TEXT:
        assert forbidden not in rendered_labels


def test_run_tiny_scaffold_button_maps_only_to_required_dry_run_command(tmp_path: Path) -> None:
    _write_061_artifacts(tmp_path)
    calls: list[str] = []

    def fake_action_runner(action_id: str) -> dict[str, Any]:
        calls.append(action_id)
        return {
            "status": "completed",
            "returncode": 0,
            "stdout_excerpt": "Tiny order scaffold completed in dry-run mode.",
            "stderr_excerpt": "",
        }

    action = safe_action_by_id(TINY_ACTION_ID)
    callback_action = safe_action_by_callback(TINY_CALLBACK)
    assert action is not None
    assert callback_action is action
    assert action.command_display == TINY_COMMAND_DISPLAY
    assert validate_safe_action(action) == []
    assert "--dry-run" in action.args
    assert "--live" not in action.args
    assert "--sign" not in action.args
    assert "--submit" not in action.args

    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context, action_runner=fake_action_runner)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data=TINY_CALLBACK)

    assert calls == [TINY_ACTION_ID]
    assert "Run Tiny Scaffold 061: dry-run/preflight action" in reply.text
    assert "order_submission_enabled: false" in reply.text
    assert "candidate_is_executable: false" in reply.text


def test_approval_packet_and_safety_status_render_in_en_and_ru(tmp_path: Path) -> None:
    _write_061_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)

    en_adapter = _adapter(context=context)
    en = en_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/tiny_order_review")

    ru_adapter = _adapter(context=context)
    ru_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    ru = ru_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/tiny_order_review")

    assert "Tiny Order Review" in en.text
    assert "Approval Packet:" in en.text
    assert "Operator approved: false" in en.text
    assert "Candidate is executable: false" in en.text
    assert "Signing blocked" in en.text
    assert "Order submission blocked" in en.text
    assert "Wallet blocked" in en.text
    assert "Live execution blocked" in en.text
    assert "Малый ордер" in ru.text
    assert "Пакет ручного подтверждения" in ru.text
    assert "Лимиты" in ru.text
    assert "Оператор подтвердил: нет" in ru.text
    assert "Кандидат не исполняемый" in ru.text
    assert "Подписание заблокировано" in ru.text
    assert "Отправка ордера заблокирована" in ru.text
    assert "Live-торговля заблокирована" in ru.text


def test_live_auth_signing_order_wallet_flags_remain_false(tmp_path: Path) -> None:
    _write_061_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/tiny_order_review")
    safety = dict(reply.summary.get("telegram_operator_console_safety_state", {}))

    for flag in REQUIRED_FALSE_FLAGS:
        assert reply.summary[flag] is False
        assert safety[flag] is False
    assert reply.summary["resolved_blocker_count"] == 0
    assert safety["resolved_blocker_count"] == 0


def test_runtime_tiny_signer_no_order_auth_and_static_safety_commands_still_pass(tmp_path: Path) -> None:
    env = _minimal_env({"PMBOT_GAMMA_BASE_URL": "http://127.0.0.1:1"})
    commands = [
        [sys.executable, "-m", "pm_bot.operator_runner.telegram_runtime_smoke"],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.tiny_order_scaffold",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "tiny_order_scaffold_061"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_boundary_preflight",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "signer_boundary_preflight_060"),
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
            str(tmp_path / "no_order_auth_get_preflight_059"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.static_safety_invariant_report",
            "--scope",
            "pm_bot",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "static_safety_invariant_report_060q"),
        ],
    ]
    outputs: list[str] = []
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
        assert completed.returncode == 0, completed.stderr
        outputs.append(completed.stdout)

    assert "PMBOT Telegram runtime smoke" in outputs[0]
    assert "Tiny order scaffold completed." in outputs[1]
    assert "Signer boundary preflight completed." in outputs[2]
    assert "No-order auth GET: mocked" in outputs[3]
    assert "Critical findings: 0" in outputs[4]

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        artifact_dir=tmp_path / "scanner_api",
        generated_at=GENERATED_AT,
    )
    assert report["critical_count"] == 0
    assert report["safety_ok"] is True
    for flag in REQUIRED_FALSE_FLAGS:
        assert report[flag] is False
    assert report["resolved_blocker_count"] == 0


def test_safe_action_registry_contains_only_dry_run_review_commands() -> None:
    tiny_action_count = 0
    for action in SAFE_ACTIONS:
        assert validate_safe_action(action) == []
        assert "--dry-run" in action.args
        assert "--live" not in action.args
        assert "--execute" not in action.args
        assert "--wallet" not in action.args
        assert "--sign" not in action.args
        assert "--submit" not in action.args
        if action.action_id == TINY_ACTION_ID:
            tiny_action_count += 1
            assert action.command_display == TINY_COMMAND_DISPLAY
    assert tiny_action_count == 1

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
    PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID,
    SAFE_ACTIONS,
    STATUS_SOURCES,
    build_telegram_console_context,
    build_telegram_status_registry_snapshot,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
    telegram_console_safety_state,
    validate_safe_action,
    write_telegram_pre_live_gate_review_062t_artifacts,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
PRE_LIVE_ACTION_ID = "run_pre_live_tiny_order_gate_062p_review_dry_run"
PRE_LIVE_CALLBACK = "pmbot:run:pre_live_tiny_order_gate_062p_review_dry_run"
PRE_LIVE_COMMAND_DISPLAY = (
    "python",
    "-m",
    "pm_bot.operator_runner.pre_live_tiny_order_gate",
    "--market",
    "BTC",
    "--strategy",
    "tiny-momentum",
    "--dry-run",
)

REQUIRED_FALSE_FLAGS = (
    "operator_approved",
    "candidate_is_executable",
    "signing_available",
    "signed_payload_available",
    "order_submission_available",
    "wallet_available",
    "live_execution_approved",
    "ready_for_future_live_enablement",
    "allowed_for_live",
)

FORBIDDEN_LIVE_CONTROL_TERMS = (
    "approve-live",
    "send-order",
    "submit-order",
    "cancel-order",
    "connect-wallet",
    "unlock-wallet",
    "live-enable",
    "live-execute",
    "approve live",
    "send order",
    "submit order",
    "cancel order",
    "connect wallet",
    "unlock wallet",
    "live enable",
    "live execute",
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


def _write_062p_artifacts(root: Path) -> Path:
    artifact_dir = root / "pre_live_tiny_order_gate_062p"
    latest_path = artifact_dir / "latest_pre_live_tiny_order_gate_status_062p.json"
    checklist_path = artifact_dir / "pre_live_tiny_order_checklist_062p.json"
    blockers_path = artifact_dir / "pre_live_tiny_order_blockers_062p.json"
    readiness_path = artifact_dir / "pre_live_tiny_order_readiness_summary_062p.json"
    operator_md_path = artifact_dir / "pre_live_tiny_order_gate_062p_operator.md"
    safety = telegram_console_safety_state()
    blocker_reasons = [
        "operator_approved remains false; this gate cannot approve live execution.",
        "candidate_is_executable remains false; the candidate is for review only.",
        "Signing is unavailable and blocked.",
        "Order submission and cancellation are unavailable and blocked.",
    ]
    common = {
        "task_id": "ORCH-PMBOT-TRADING-MVP-062P-PRE-LIVE-TINY-ORDER-GATE-AND-OPERATOR-CHECKLIST-NO-SUBMISSION",
        "generated_at": GENERATED_AT,
        "market": "BTC",
        "market_symbol": "BTC",
        "strategy_name": "tiny-momentum",
        "mode": "preflight / review-only",
        "execution_mode": "preflight",
        "review_only": True,
        "preflight_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "tiny_candidate_present": True,
        "approval_packet_present": True,
        "hard_limits_passed": True,
        "market_whitelisted": True,
        "signer_boundary_present": True,
        "auth_preflight_present": True,
        "safety_scan_present": True,
        "blocker_count": len(blocker_reasons),
        "resolved_blocker_count": 0,
        "top_blocker_reasons": blocker_reasons,
        "source_tiny_scaffold_path": "pm_bot/trading_core/artifacts/tiny_order_scaffold_061/latest_tiny_order_scaffold_status_061.json",
        "source_signer_boundary_path": "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json",
        "source_auth_preflight_path": "pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/latest_no_order_auth_get_preflight_status_059.json",
        "source_safety_scan_path": "pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/latest_static_safety_invariant_report_status_060q.json",
        **safety,
    }
    checklist_items = [
        {"check_id": "operator_approved_false", "ready": False, "status": "blocked"},
        {"check_id": "candidate_non_executable", "ready": False, "status": "blocked"},
    ]
    _write_json(
        checklist_path,
        {
            **common,
            "contract_version": "pmbot_pre_live_tiny_order_checklist_062p.v1",
            "checklist_items": checklist_items,
        },
    )
    _write_json(
        blockers_path,
        {
            **common,
            "contract_version": "pmbot_pre_live_tiny_order_blockers_062p.v1",
            "status": "unresolved_blockers_present",
            "blockers": [
                {
                    **safety,
                    "blocker_id": f"fixture_blocker_{index}",
                    "reason": reason,
                    "resolution_status": "unresolved",
                    "resolved": False,
                    "blocks_live_execution": True,
                }
                for index, reason in enumerate(blocker_reasons, start=1)
            ],
        },
    )
    _write_json(
        readiness_path,
        {
            **common,
            "contract_version": "pmbot_pre_live_tiny_order_readiness_summary_062p.v1",
            "readiness_status": "blocked",
            "ready_for_future_live_enablement": False,
            "allowed_for_live": False,
            "next_operator_action": "review blockers before any future live-enabling task",
        },
    )
    _write_json(
        latest_path,
        {
            **common,
            "contract_version": "pmbot_latest_pre_live_tiny_order_gate_status_062p.v1",
            "status": "pre_live_tiny_order_gate_completed_live_blocked",
            "artifact_path": (artifact_dir / "pre_live_tiny_order_gate_062p_result.json").as_posix(),
            "latest_status_path": latest_path.as_posix(),
            "operator_markdown_path": operator_md_path.as_posix(),
            "checklist_path": checklist_path.as_posix(),
            "blockers_path": blockers_path.as_posix(),
            "readiness_summary_path": readiness_path.as_posix(),
            "next_operator_action": "review blockers before any future live-enabling task",
        },
    )
    operator_md_path.write_text("# Pre-live tiny order gate fixture\n", encoding="utf-8")
    return artifact_dir


def _adapter(*, context: Mapping[str, Any], action_runner=None) -> runtime.TelegramOperatorRuntimeAdapter:  # type: ignore[no-untyped-def]
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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        assert value[flag] is False, flag
    assert value["resolved_blocker_count"] == 0


def test_062p_status_is_registered_as_first_class_safe_status_item(tmp_path: Path) -> None:
    _write_062p_artifacts(tmp_path)

    source = next(item for item in STATUS_SOURCES if item.flow_id == PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID)
    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)
    card = snapshot["cards_by_flow"][PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID]
    review = snapshot["pre_live_tiny_order_gate_review_062t"]

    assert source.label_en == "Pre-live tiny order gate"
    assert source.label_ru == "Предлайв-гейт tiny order"
    assert card["available"] is True
    assert card["status"] == "pre_live_tiny_order_gate_completed_live_blocked"
    assert card["status_summary"]["checklist_path"].endswith("pre_live_tiny_order_checklist_062p.json")
    assert card["status_summary"]["blockers_path"].endswith("pre_live_tiny_order_blockers_062p.json")
    assert card["status_summary"]["readiness_summary_path"].endswith(
        "pre_live_tiny_order_readiness_summary_062p.json"
    )
    assert review["source_status_available"] is True
    assert review["label_en"] == "Pre-live tiny order gate"
    assert review["label_ru"] == "Предлайв-гейт tiny order"
    _assert_required_false_flags(review)


def test_pre_live_dry_run_action_points_only_to_062p_gate_command() -> None:
    action = safe_action_by_id(PRE_LIVE_ACTION_ID)
    callback_action = safe_action_by_callback(PRE_LIVE_CALLBACK)

    assert action is not None
    assert callback_action is action
    assert action.command_display == PRE_LIVE_COMMAND_DISPLAY
    assert action.module == "pm_bot.operator_runner.pre_live_tiny_order_gate"
    assert action.args == ("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run")
    assert validate_safe_action(action) == []
    assert "--dry-run" in action.args
    assert "--live" not in action.args
    assert "--execute" not in action.args
    assert "--sign" not in action.args
    assert "--submit" not in action.args


def test_pre_live_gate_review_renders_en_ru_labels_and_safe_command(tmp_path: Path) -> None:
    _write_062p_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)

    en_adapter = _adapter(context=context)
    en_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    en = en_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/pre_live_gate_review")

    ru_adapter = _adapter(context=context)
    ru_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    ru = ru_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/pre_live_gate_review")

    command = "python -m pm_bot.operator_runner.pre_live_tiny_order_gate --market BTC --strategy tiny-momentum --dry-run"
    assert "Pre-live tiny order gate" in en.text
    assert "Checklist:" in en.text
    assert "Blockers:" in en.text
    assert "Readiness summary:" in en.text
    assert "Run Pre-live Gate 062P Dry-Run" in en.text
    assert command in en.text
    assert "Operator approved: false" in en.text
    assert "Candidate is executable: false" in en.text
    assert "Ready for future live enablement: false" in en.text
    assert "Предлайв-гейт tiny order" in ru.text
    assert "Чеклист:" in ru.text
    assert "Блокеры:" in ru.text
    assert "Dry-run предлайв-гейта 062P" in ru.text
    assert "Оператор подтвердил: нет" in ru.text
    assert "Кандидат не исполняемый" in ru.text


def test_pre_live_gate_controls_have_no_forbidden_live_callbacks(tmp_path: Path) -> None:
    _write_062p_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")

    panel = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    labels = _button_labels(panel)
    all_console_controls = tuple(
        (label, callback_data)
        for language in ("en", "ru")
        for row in telegram_console_button_rows(language)
        for label, callback_data in row
    )
    pre_live_controls = [
        f"{label} {callback_data}"
        for label, callback_data in all_console_controls
        if callback_data in {PRE_LIVE_CALLBACK, "pmbot:pre_live_gate_review"}
    ]
    action = safe_action_by_id(PRE_LIVE_ACTION_ID)
    assert action is not None
    rendered = " ".join(
        [
            *pre_live_controls,
            action.action_id,
            action.callback_data,
            action.label_en,
            action.label_ru,
        ]
    ).lower()

    assert "Run Pre-live Gate 062P Dry-Run" in labels
    assert "Pre-live tiny order gate" in panel.text
    for forbidden in FORBIDDEN_LIVE_CONTROL_TERMS:
        assert forbidden not in rendered


def test_062t_generated_artifacts_preserve_false_flags_and_resolved_zero(tmp_path: Path) -> None:
    _write_062p_artifacts(tmp_path)
    output = tmp_path / "telegram_pre_live_gate_review_062t"

    generated = write_telegram_pre_live_gate_review_062t_artifacts(
        artifact_root=tmp_path,
        output_dir=output,
        generated_at=GENERATED_AT,
    )
    result = generated["result"]
    latest = generated["latest_status"]
    controls = generated["controls"]

    for key in ("result_path", "latest_status_path", "registry_snapshot_path", "controls_path"):
        assert Path(generated[key]).exists()
    assert latest["run_pre_live_gate_command"] == list(PRE_LIVE_COMMAND_DISPLAY)
    assert controls["allowed_dry_run_command"] == list(PRE_LIVE_COMMAND_DISPLAY)
    assert controls["forbidden_live_controls_added"] is False
    for payload in (result, latest, controls):
        _assert_required_false_flags(payload)


def test_telegram_runtime_smoke_still_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pm_bot.operator_runner.telegram_runtime_smoke"],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "PMBOT Telegram runtime smoke" in completed.stdout
    assert "Safety flags expected false: ok" in completed.stdout


def test_safe_action_registry_contains_only_dry_run_pre_live_062t_action_once() -> None:
    matches = [action for action in SAFE_ACTIONS if action.action_id == PRE_LIVE_ACTION_ID]

    assert len(matches) == 1
    for action in SAFE_ACTIONS:
        assert validate_safe_action(action) == []
        assert "--dry-run" in action.args

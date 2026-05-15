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
    STATUS_SOURCES,
    SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID,
    build_telegram_console_context,
    build_telegram_status_registry_snapshot,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
    validate_safe_action,
    write_telegram_supervised_live_enablement_review_063t_artifacts,
)
from pm_bot.trading_core.supervised_tiny_live_enablement_gate import (
    DEFAULT_READINESS_MARKERS,
    run_supervised_tiny_live_enablement_gate,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
SUPERVISED_ACTION_ID = "run_supervised_tiny_gate_063_review_dry_run"
SUPERVISED_CALLBACK = "pmbot:run:supervised_tiny_gate_063_review_dry_run"
SUPERVISED_VIEW_CALLBACK = "pmbot:supervised_live_review"
SUPERVISED_COMMAND_DISPLAY = (
    "python",
    "-m",
    "pm_bot.operator_runner.supervised_tiny_live_enablement_gate",
    "--market",
    "BTC",
    "--strategy",
    "tiny-momentum",
    "--dry-run",
)

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "order_cancel_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "operator_approved",
    "candidate_is_executable",
)

FORBIDDEN_CONTROL_TERMS = (
    "run_signer",
    "pmbot:run:signer",
    "run signer",
    "approve-live",
    "approve_live",
    "send-order",
    "send_order",
    "submit-order",
    "submit_order",
    "cancel-order",
    "cancel_order",
    "connect-wallet",
    "connect_wallet",
    "unlock-wallet",
    "unlock_wallet",
    "live-enable",
    "live_enable",
    "live-execute",
    "live_execute",
)

FAKE_SECRET_VALUES = (
    "fake-private-key-063t",
    "fake-seed-phrase-063t",
    "fake-mnemonic-063t",
    "fake-api-secret-063t",
    "fake-auth-token-063t",
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


def _write_063_artifacts(root: Path) -> Path:
    artifact_dir = root / "supervised_tiny_live_enablement_gate_063"
    run_supervised_tiny_live_enablement_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=artifact_dir,
        readiness_marker_presence={marker: False for marker in DEFAULT_READINESS_MARKERS},
        generated_at=GENERATED_AT,
    )
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


def test_063_panel_appears_in_telegram_status_registry(tmp_path: Path) -> None:
    _write_063_artifacts(tmp_path)

    source = next(
        item for item in STATUS_SOURCES if item.flow_id == SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID
    )
    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)
    card = snapshot["cards_by_flow"][SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID]
    review = snapshot["supervised_live_enablement_review_063t"]

    assert source.label_en == "Supervised live enablement gate"
    assert source.label_ru == "Гейт supervised live enablement"
    assert card["available"] is True
    assert card["status"] == "supervised_tiny_live_enablement_prepared_live_blocked"
    assert card["status_summary"]["operator_checklist_path"].endswith(
        "supervised_tiny_live_operator_checklist_063.json"
    )
    assert card["status_summary"]["blockers_path"].endswith("supervised_tiny_live_blockers_063.json")
    assert card["status_summary"]["risk_limits_path"].endswith("supervised_tiny_live_risk_limits_063.json")
    assert card["status_summary"]["kill_switch_plan_path"].endswith(
        "supervised_tiny_live_kill_switch_plan_063.json"
    )
    assert card["status_summary"]["cancel_plan_path"].endswith("supervised_tiny_live_cancel_plan_063.json")
    assert card["status_summary"]["failure_plan_path"].endswith("supervised_tiny_live_failure_plan_063.json")
    assert card["status_summary"]["env_readiness_path"].endswith("supervised_tiny_live_env_readiness_063.json")
    assert card["status_summary"]["manual_approval_packet_path"].endswith(
        "supervised_tiny_live_manual_approval_packet_063.json"
    )
    assert review["source_status_available"] is True
    assert review["label_en"] == "Supervised live enablement gate"
    assert review["label_ru"] == "Гейт supervised live enablement"
    assert review["env_readiness_summary"]["presence_only"] is True
    assert review["env_readiness_summary"]["values_redacted"] is True
    assert review["env_readiness_summary"]["raw_values_emitted"] is False
    _assert_required_false_flags(review)


def test_063_dry_run_action_points_only_to_supervised_gate_command() -> None:
    action = safe_action_by_id(SUPERVISED_ACTION_ID)
    callback_action = safe_action_by_callback(SUPERVISED_CALLBACK)

    assert action is not None
    assert callback_action is action
    assert action.command_display == SUPERVISED_COMMAND_DISPLAY
    assert action.module == "pm_bot.operator_runner.supervised_tiny_live_enablement_gate"
    assert action.args == ("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run")
    assert validate_safe_action(action) == []
    assert "--dry-run" in action.args
    for forbidden in ("--live", "--execute", "--trade", "--wallet", "--sign", "--submit", "--cancel"):
        assert forbidden not in action.args


def test_supervised_live_review_renders_en_ru_labels_and_safe_command(tmp_path: Path) -> None:
    _write_063_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)

    en_adapter = _adapter(context=context)
    en_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    en = en_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/supervised_live_review")

    ru_adapter = _adapter(context=context)
    ru_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    ru = ru_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/supervised_live_review")

    command = (
        "python -m pm_bot.operator_runner.supervised_tiny_live_enablement_gate "
        "--market BTC --strategy tiny-momentum --dry-run"
    )
    assert "Supervised live enablement gate" in en.text
    assert "Review only" in en.text
    assert "Dry-run only" in en.text
    assert "Not executable" in en.text
    assert "Operator approval required" in en.text
    assert "Operator checklist:" in en.text
    assert "Blocker matrix:" in en.text
    assert "Risk limits:" in en.text
    assert "Kill switch plan:" in en.text
    assert "Cancel plan:" in en.text
    assert "Failure plan:" in en.text
    assert "Env readiness:" in en.text
    assert "Manual approval packet:" in en.text
    assert command in en.text
    assert "operator_approved: false" in en.text
    assert "candidate_is_executable: false" in en.text
    assert "resolved_blocker_count: 0" in en.text
    assert "Гейт supervised live enablement" in ru.text
    assert "Только просмотр" in ru.text
    assert "Только dry-run" in ru.text
    assert "Не исполняется" in ru.text
    assert "Требуется подтверждение оператора" in ru.text
    assert "Готовность окружения:" in ru.text


def test_063_controls_have_no_forbidden_live_order_sign_or_wallet_callbacks(tmp_path: Path) -> None:
    _write_063_artifacts(tmp_path)
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
    supervised_controls = [
        f"{label} {callback_data}"
        for label, callback_data in all_console_controls
        if callback_data in {SUPERVISED_CALLBACK, SUPERVISED_VIEW_CALLBACK}
    ]
    action = safe_action_by_id(SUPERVISED_ACTION_ID)
    assert action is not None
    rendered = " ".join(
        [
            *supervised_controls,
            action.action_id,
            action.callback_data,
            action.label_en,
            action.label_ru,
        ]
    ).lower()

    assert "Run Supervised Gate 063 Dry-Run" in labels
    assert "Supervised live enablement gate" in panel.text
    for forbidden in FORBIDDEN_CONTROL_TERMS:
        assert forbidden not in rendered
    assert " sign " not in f" {rendered} "
    assert " signer " not in f" {rendered} "
    assert " wallet " not in f" {rendered} "


def test_063t_generated_artifacts_preserve_false_flags_and_resolved_zero(tmp_path: Path) -> None:
    _write_063_artifacts(tmp_path)
    output = tmp_path / "telegram_supervised_live_enablement_review_063t"

    generated = write_telegram_supervised_live_enablement_review_063t_artifacts(
        artifact_root=tmp_path,
        output_dir=output,
        generated_at=GENERATED_AT,
    )
    result = generated["result"]
    latest = generated["latest_status"]
    controls = generated["controls"]

    for key in ("result_path", "latest_status_path", "registry_snapshot_path", "controls_path"):
        assert Path(generated[key]).exists()
    assert latest["run_supervised_gate_command"] == list(SUPERVISED_COMMAND_DISPLAY)
    assert controls["allowed_dry_run_command"] == list(SUPERVISED_COMMAND_DISPLAY)
    assert controls["forbidden_live_controls_added"] is False
    assert controls["approve_live_control_added"] is False
    assert controls["send_order_control_added"] is False
    assert controls["submit_order_control_added"] is False
    assert controls["cancel_order_control_added"] is False
    assert controls["sign_control_added"] is False
    assert controls["wallet_control_added"] is False
    for payload in (result, latest, controls):
        _assert_required_false_flags(payload)


def test_063_panel_emits_no_raw_secrets_or_fake_execution_values(tmp_path: Path) -> None:
    _write_063_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    context["raw_secret_fixture"] = " ".join(FAKE_SECRET_VALUES)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/supervised_live_review")
    generated = write_telegram_supervised_live_enablement_review_063t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / "telegram_supervised_live_enablement_review_063t",
        generated_at=GENERATED_AT,
    )
    rendered = reply.text + "\n" + json.dumps(generated, sort_keys=True)

    for fake in FAKE_SECRET_VALUES:
        assert fake not in rendered
    for fake_execution in ("fake-order-id", "fake-tx-hash", "fake-fill", "fake-balance", "fake-pnl"):
        assert fake_execution not in rendered


def test_safe_action_registry_contains_only_dry_run_063t_action_once() -> None:
    matches = [action for action in SAFE_ACTIONS if action.action_id == SUPERVISED_ACTION_ID]

    assert len(matches) == 1
    for action in SAFE_ACTIONS:
        assert validate_safe_action(action) == []
        assert "--dry-run" in action.args
        for forbidden in ("--live", "--execute", "--wallet", "--sign", "--submit", "--cancel"):
            assert forbidden not in action.args


def test_telegram_runtime_smoke_still_passes_for_063t() -> None:
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

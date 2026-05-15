from __future__ import annotations

import json
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
    build_telegram_console_context,
    build_telegram_status_registry_snapshot,
    safe_action_by_callback,
    telegram_console_button_rows,
    telegram_console_safety_state,
    validate_safe_action,
)

GENERATED_AT = "2026-05-15T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
UNAUTHORIZED_USER_ID = "9999"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_OPERATOR_TOKEN = "operator-secret-token-value"

FORBIDDEN_BUTTON_TEXT = (
    "Send Order",
    "Cancel Order",
    "Sign Payload",
    "Connect Wallet",
    "Approve Live",
    "Enable Live",
    "View Balance",
    "View Position",
    "View Fills",
    "Trade Now",
)

FORCED_FALSE_FLAGS = (
    "live_execution_approved",
    "order_submission_enabled",
    "order_cancel_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)


def _write_status_artifacts(root: Path) -> None:
    for source in STATUS_SOURCES:
        path = root / source.artifact_dir_name / source.latest_status_filename
        payload = {
            "contract_version": f"fixture.{source.flow_id}.v1",
            "status": f"{source.flow_id}_ready",
            "market": "BTC",
            "strategy_name": "tiny-momentum",
            "mode": "paper / review-only" if "paper" in source.flow_id else "preflight / review-only",
            "artifact_path": (path.parent / f"{source.flow_id}_result.json").as_posix(),
            "latest_status_path": path.as_posix(),
            "operator_markdown_path": (path.parent / f"{source.flow_id}_operator.md").as_posix(),
            "blocker_count": 0,
            "top_blocker_reasons": [],
            "ledger_entry_count": 1 if source.flow_id == "paper_decision_ledger_055" else 0,
            "last_outcome": "paper_intent_review_ready",
            "source": "fixture_fallback",
            "public_network_status": "ok",
            "auth_boundary_status": "checked",
            "auth_presence_status": "present_redacted",
            "clob_base_url_status": "valid",
            "l2_marker_presence_status": "present_redacted",
            "l2_marker_set_complete": True,
            "no_order_auth_get_status": "mocked",
            "real_authenticated_get_performed": False,
            "review_only": True,
            "execution_enabling": False,
            "live_execution": "blocked",
            **telegram_console_safety_state(),
        }
        if source.flow_id == "signer_boundary_preflight_060":
            payload.update(
                {
                    "status": "signer_boundary_preflight_completed_live_blocked",
                    "live_candidate_intent_status": "created",
                    "unsigned_plan_status": "schema_only_non_executable",
                    "unsigned_plan_created": True,
                    "unsigned_plan_is_executable": False,
                    "signer_status": "blocked",
                    "signed_payload_status": "unavailable",
                    "order_submission_status": "blocked",
                    "signer_config_present": False,
                    "signed_payload_available": False,
                    "order_submission_available": False,
                    "blocker_count": 5,
                    "top_blocker_reasons": [
                        "Signer is unavailable and blocked; no signer is configured or instantiated."
                    ],
                }
            )
        if source.flow_id == "tiny_order_scaffold_061":
            payload.update(
                {
                    "status": "tiny_order_scaffold_completed_live_blocked",
                    "tiny_candidate": "created",
                    "approval_packet": "created",
                    "manual_tiny_order_approval_packet_path": (
                        path.parent / "manual_tiny_order_approval_packet_061.json"
                    ).as_posix(),
                    "operator_approved": False,
                    "approval_packet_created": True,
                    "candidate_is_executable": False,
                    "source_intent_path": "pm_bot/trading_core/artifacts/paper_trading_loop_053/paper_trading_order_intent_053.json",
                    "source_signer_boundary_path": "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json",
                    "hard_limits_passed": True,
                    "blocker_count": 7,
                    "top_blocker_reasons": [
                        "Manual operator approval is required and operator_approved remains false."
                    ],
                }
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _callback_data(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def test_status_registry_reads_existing_052_059_latest_artifacts(tmp_path: Path) -> None:
    _write_status_artifacts(tmp_path)

    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)

    assert snapshot["available_status_count"] == len(STATUS_SOURCES)
    assert snapshot["missing_status_count"] == 0
    for source in STATUS_SOURCES:
        card = snapshot["cards_by_flow"][source.flow_id]
        assert card["available"] is True
        if source.flow_id == "signer_boundary_preflight_060":
            assert card["status"] == "signer_boundary_preflight_completed_live_blocked"
            assert card["status_summary"]["live_candidate_intent_status"] == "created"
            assert card["status_summary"]["unsigned_plan_status"] == "schema_only_non_executable"
            assert card["status_summary"]["signer_status"] == "blocked"
            assert card["status_summary"]["signed_payload_status"] == "unavailable"
        elif source.flow_id == "tiny_order_scaffold_061":
            assert card["status"] == "tiny_order_scaffold_completed_live_blocked"
            assert card["status_summary"]["tiny_candidate"] == "created"
            assert card["status_summary"]["approval_packet"] == "created"
            assert card["status_summary"]["operator_approved"] is False
            assert card["status_summary"]["candidate_is_executable"] is False
        else:
            assert card["status"] == f"{source.flow_id}_ready"
        assert card["latest_status_path"].endswith(source.latest_status_filename)
        assert card["status_summary"]["market"] == "BTC"
        for flag in FORCED_FALSE_FLAGS:
            assert card[flag] is False
            assert card["status_summary"][flag] is False


def test_missing_artifact_paths_do_not_crash_and_readiness_is_produced(tmp_path: Path) -> None:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)
    readiness = snapshot["readiness_summary"]

    assert snapshot["available_status_count"] == 0
    assert snapshot["missing_status_count"] == len(STATUS_SOURCES)
    assert len(snapshot["status_cards"]) == len(STATUS_SOURCES)
    assert readiness["items"]["paper_system"] == "blocked"
    assert readiness["items"]["signer_boundary"] == "not implemented yet"
    assert readiness["items"]["tiny_order_scaffold"] == "not implemented yet"
    assert readiness["items"]["pre_live_tiny_order_gate"] == "not implemented yet"
    assert readiness["items"]["supervised_tiny_live_enablement_gate"] == "not implemented yet"
    assert readiness["items"]["order_submission"] == "blocked"
    assert readiness["items"]["live_execution"] == "blocked"
    assert set(readiness["labels"]) == {
        "paper_demo_ready",
        "pre_live_boundary_ready",
        "signer_boundary_missing",
        "tiny_order_scaffold_missing",
        "pre_live_tiny_order_gate_missing",
        "supervised_tiny_live_enablement_gate_missing",
        "live_execution_blocked",
    }


def test_telegram_panel_menu_contains_safe_dry_run_and_preflight_actions(tmp_path: Path) -> None:
    _write_status_artifacts(tmp_path)
    adapter = _adapter(context=build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT))
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    labels = _button_labels(reply)

    assert "Main PMBOT menu" in reply.text
    for section in (
        "PMBOT Status",
        "Paper Runs",
        "Public Market Evidence",
        "Decision Ledger",
        "Live Readiness",
        "Blockers",
        "Latest Artifacts",
        "Safety State",
    ):
        assert section in reply.text
    for required in (
        "Run Paper Canary 052",
        "Run Paper Loop 053",
        "Run Public Market Paper Loop 054",
        "Update Decision Ledger 055",
        "Run Live Connector Preflight 056",
        "Run Authenticated CLOB Preflight 057/058",
        "Run No-Order Auth GET Preflight 059",
        "Run Pre-live Gate 062P Dry-Run",
        "Run Supervised Gate 063 Dry-Run",
        "Show Latest Status",
        "Show Blockers",
        "Show Readiness %",
    ):
        assert required in labels
    for forbidden in FORBIDDEN_BUTTON_TEXT:
        assert forbidden not in labels


def test_telegram_menu_has_no_live_execution_wallet_balance_position_or_fill_controls() -> None:
    for language in ("en", "ru"):
        rows = telegram_console_button_rows(language)
        labels = tuple(label for row in rows for label, _callback_data in row)
        callbacks = tuple(callback_data for row in rows for _label, callback_data in row)
        rendered = " ".join([*labels, *callbacks]).lower()

        assert "send order" not in rendered
        assert "cancel order" not in rendered
        assert "sign payload" not in rendered
        assert "signer" not in rendered
        assert "connect wallet" not in rendered
        assert "wallet" not in rendered
        assert "approve live" not in rendered
        assert "enable live" not in rendered
        assert "view balance" not in rendered
        assert "view position" not in rendered
        assert "view fills" not in rendered
        assert "trade now" not in rendered


def test_callbacks_execute_only_safe_dry_run_preflight_paths_or_status_reads(tmp_path: Path) -> None:
    _write_status_artifacts(tmp_path)
    calls: list[str] = []

    def fake_action_runner(action_id: str) -> dict[str, Any]:
        calls.append(action_id)
        return {
            "status": "completed",
            "returncode": 0,
            "stdout_excerpt": f"{action_id} finished in dry-run/preflight mode",
            "stderr_excerpt": "",
        }

    adapter = _adapter(
        context=build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT),
        action_runner=fake_action_runner,
    )
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    panel = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    action_callbacks = [callback for callback in _callback_data(panel) if callback.startswith("pmbot:run:")]
    status_callbacks = {"pmbot:status", "pmbot:blockers", "pmbot:readiness"}

    assert len(action_callbacks) == len(SAFE_ACTIONS)
    for action in SAFE_ACTIONS:
        assert validate_safe_action(action) == []
        assert "--dry-run" in action.args
    for callback in action_callbacks:
        action = safe_action_by_callback(callback)
        assert action is not None
        reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data=callback)
        assert "dry-run/preflight action" in reply.text
        assert "order_submission_enabled: false" in reply.text
    for callback in status_callbacks:
        reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data=callback)
        assert reply.command in {"/status", "/blockers", "/readiness"}

    assert calls == [action.action_id for action in SAFE_ACTIONS]


def test_ru_and_en_labels_render_where_language_is_supported(tmp_path: Path) -> None:
    _write_status_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)

    en_adapter = _adapter(context=context)
    en_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    en_panel = en_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")

    ru_adapter = _adapter(context=context)
    ru_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    ru_panel = ru_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")

    assert "Main PMBOT menu" in en_panel.text
    assert "Run Paper Canary 052" in _button_labels(en_panel)
    assert "Главное меню" in ru_panel.text
    assert "Бумажный прогон" in ru_panel.text
    assert "Публичный рынок" in ru_panel.text
    assert "Журнал решений" in ru_panel.text
    assert "Live-проверка" in ru_panel.text
    assert "Предлайв-гейт tiny order" in ru_panel.text
    assert "Гейт supervised live enablement" in ru_panel.text
    assert "Блокеры" in ru_panel.text
    assert "Только review-only" in ru_panel.text
    assert "Live-торговля заблокирована" in ru_panel.text


def test_no_raw_secrets_operator_tokens_or_operator_ids_are_printed(tmp_path: Path) -> None:
    _write_status_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    context["raw_telegram_bot_token"] = RAW_TOKEN
    context["raw_operator_token"] = RAW_OPERATOR_TOKEN
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")

    replies = [
        adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel"),
        adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:readiness"),
        adapter.handle_callback(user_id=UNAUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:status"),
    ]

    for reply in replies:
        rendered = json.dumps(reply.to_redacted_dict(), sort_keys=True)
        assert RAW_TOKEN not in reply.text
        assert RAW_OPERATOR_TOKEN not in reply.text
        assert AUTHORIZED_USER_ID not in reply.text
        assert UNAUTHORIZED_USER_ID not in reply.text
        assert RAW_TOKEN not in rendered
        assert RAW_OPERATOR_TOKEN not in rendered
        assert AUTHORIZED_USER_ID not in rendered
        assert UNAUTHORIZED_USER_ID not in rendered


def test_all_live_auth_signing_order_wallet_flags_remain_false(tmp_path: Path) -> None:
    _write_status_artifacts(tmp_path)
    adapter = _adapter(context=build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT))
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    summary = reply.summary
    safety = dict(summary.get("telegram_operator_console_safety_state", {}))

    for flag in FORCED_FALSE_FLAGS:
        assert summary[flag] is False
        assert safety[flag] is False
    assert summary["resolved_blocker_count"] == 0
    assert safety["resolved_blocker_count"] == 0
    assert safety["balance_view_enabled"] is False
    assert safety["position_view_enabled"] is False
    assert safety["fills_view_enabled"] is False
    assert safety["pnl_view_enabled"] is False

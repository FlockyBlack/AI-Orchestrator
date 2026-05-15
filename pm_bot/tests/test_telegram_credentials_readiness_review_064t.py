from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_status_registry import (
    EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID,
    SAFE_ACTIONS,
    STATUS_SOURCES,
    build_telegram_console_context,
    build_telegram_status_registry_snapshot,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
    validate_safe_action,
    write_telegram_credentials_readiness_review_064t_artifacts,
)
from pm_bot.trading_core.explicit_live_credentials_readiness_gate import (
    run_explicit_live_credentials_readiness_gate,
)
from pm_bot.trading_core.explicit_live_credentials_readiness_models import (
    CREDENTIAL_SOURCE_MARKERS,
    MANUAL_CONTROL_MARKERS,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
DRY_RUN_ACTION_ID = "run_credentials_readiness_review_064_dry_run"
DRY_RUN_CALLBACK = "pmbot:run:credentials_readiness_review_064_dry_run"
VIEW_CALLBACK = "pmbot:credentials_readiness_review"
DRY_RUN_COMMAND = [
    "python",
    "-m",
    "pm_bot.operator_runner.explicit_live_credentials_readiness_gate",
    "--market",
    "BTC",
    "--strategy",
    "tiny-momentum",
    "--dry-run",
]
DRY_RUN_TEXT = "python -m pm_bot.operator_runner.explicit_live_credentials_readiness_gate --market BTC --strategy tiny-momentum --dry-run"

FAKE_SECRET_VALUES = (
    "fake-private-key-064t",
    "fake-seed-phrase-064t",
    "fake-mnemonic-064t",
    "fake-api-secret-064t",
    "fake-auth-token-064t",
    "fake-passphrase-064t",
)

FORBIDDEN_CONTROL_TERMS = (
    "run_signer",
    "pmbot:run:signer",
    "Run Signer",
    "approve-live",
    "approve_live",
    "send-order",
    "send_order",
    "submit-order",
    "submit_order",
    "cancel-order",
    "cancel_order",
    "sign",
    "signer",
    "wallet",
    "connect-wallet",
    "connect_wallet",
    "unlock-wallet",
    "unlock_wallet",
    "live-enable",
    "live_enable",
    "live-execute",
    "live_execute",
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "operator_approved",
    "candidate_is_executable",
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
    "credential_values_read",
    "raw_values_emitted",
    "broad_environment_scan_performed",
)


def _write_064_artifacts(root: Path, *, all_required_present: bool = False) -> Path:
    artifact_dir = root / "explicit_live_credentials_readiness_gate_064"
    marker_presence = {
        marker: all_required_present
        for marker in (*CREDENTIAL_SOURCE_MARKERS, *MANUAL_CONTROL_MARKERS)
    }
    run_explicit_live_credentials_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=artifact_dir,
        marker_presence=marker_presence,
        generated_at=GENERATED_AT,
    )
    return artifact_dir


def _adapter(*, context: Mapping[str, Any]) -> runtime.TelegramOperatorRuntimeAdapter:
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
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


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _forbidden_hits(value: Any) -> list[str]:
    text = str(value)
    lower = text.lower()
    tokens = _tokenize(text)
    hits: list[str] = []
    for term in FORBIDDEN_CONTROL_TERMS:
        term_lower = term.lower()
        if term_lower in {"sign", "signer", "wallet"}:
            if term_lower in tokens:
                hits.append(term)
        elif term_lower in lower:
            hits.append(term)
    return sorted(set(hits))


def _assert_no_forbidden_control_terms(records: Iterable[tuple[str, Any]]) -> None:
    violations = []
    for label, value in records:
        hits = _forbidden_hits(value)
        if hits:
            violations.append({"field": label, "value": str(value), "hits": hits})
    assert violations == []


def _control_records(controls: Mapping[str, Any] | None = None) -> list[tuple[str, Any]]:
    records: list[tuple[str, Any]] = []
    for language in ("en", "ru"):
        for row_index, row in enumerate(telegram_console_button_rows(language)):
            for button_index, (label, callback_data) in enumerate(row):
                prefix = f"telegram_console.{language}.{row_index}.{button_index}"
                records.append((f"{prefix}.label", label))
                records.append((f"{prefix}.callback_data", callback_data))
    for index, command in enumerate(SUPPORTED_COMMANDS):
        records.append((f"supported_commands.{index}", command))
    for index, command in enumerate(SAFE_ACTION_COMMANDS):
        records.append((f"safe_action_commands.{index}", command))
    for callback_data, command in CALLBACK_COMMAND_MAP.items():
        records.append((f"callback_command_map.{callback_data}.callback_data", callback_data))
        records.append((f"callback_command_map.{callback_data}.command", command))
    for action in SAFE_ACTIONS:
        prefix = f"safe_actions.{action.action_id}"
        records.extend(
            [
                (f"{prefix}.action_id", action.action_id),
                (f"{prefix}.callback_data", action.callback_data),
                (f"{prefix}.label_en", action.label_en),
                (f"{prefix}.label_ru", action.label_ru),
                (f"{prefix}.module", action.module),
                (f"{prefix}.action_type", action.action_type),
            ]
        )
        for index, item in enumerate(action.args):
            records.append((f"{prefix}.args.{index}", item))
    if controls:
        action = dict(controls.get("allowed_dry_run_action", {}))
        records.extend(
            [
                ("controls.safe_status_view_command", controls.get("safe_status_view_command", "")),
                ("controls.safe_status_view_callback_data", controls.get("safe_status_view_callback_data", "")),
                ("controls.allowed_dry_run_action.action_id", action.get("action_id", "")),
                ("controls.allowed_dry_run_action.callback_data", action.get("callback_data", "")),
                ("controls.allowed_dry_run_action.label_en", action.get("label_en", "")),
                ("controls.allowed_dry_run_action.label_ru", action.get("label_ru", "")),
                ("controls.allowed_dry_run_action.action_type", action.get("action_type", "")),
            ]
        )
        for index, item in enumerate(controls.get("allowed_dry_run_command", [])):
            records.append((f"controls.allowed_dry_run_command.{index}", item))
    return records


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        assert value[flag] is False, flag
    assert value["resolved_blocker_count"] == 0


def test_064_credentials_panel_appears_in_telegram_status_registry(tmp_path: Path) -> None:
    _write_064_artifacts(tmp_path)

    source = next(
        item for item in STATUS_SOURCES if item.flow_id == EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID
    )
    snapshot = build_telegram_status_registry_snapshot(artifact_root=tmp_path, generated_at=GENERATED_AT)
    card = snapshot["cards_by_flow"][EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID]
    review = snapshot["credentials_readiness_review_064t"]

    assert source.label_en == "Credentials readiness review"
    assert source.label_ru == "Проверка готовности credentials"
    assert card["available"] is True
    assert review["source_status_available"] is True
    assert review["label_en"] == "Credentials readiness review"
    assert review["label_ru"] == "Проверка готовности credentials"
    assert review["presence_only"] is True
    assert review["values_never_shown"] is True
    assert review["redacted_labels_only"] is True
    assert review["missing_required_marker_count"] == 14
    assert review["present_execution_flag_count"] == 0
    assert len(review["required_marker_presence"]) == 14
    for row in review["required_marker_presence"]:
        assert set(row) == {
            "marker_label",
            "marker_group",
            "required_for_redacted_review",
            "present",
            "result_category",
            "presence_boolean_only",
            "value_redacted",
            "value_read",
            "raw_value_emitted",
        }
        assert row["value_redacted"] is True
        assert row["value_read"] is False
        assert row["raw_value_emitted"] is False
    _assert_required_false_flags(review)


def test_credentials_readiness_review_renders_en_ru_labels_warning_and_safe_command(tmp_path: Path) -> None:
    _write_064_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)

    en_adapter = _adapter(context=context)
    en_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    en = en_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/credentials_readiness_review")

    ru_adapter = _adapter(context=context)
    ru_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    ru = ru_adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/credentials_readiness_review")

    assert "Credentials readiness review" in en.text
    assert "Presence-only" in en.text
    assert "Values never shown" in en.text
    assert "Not live-enabled" in en.text
    assert "Dry-run only" in en.text
    assert "Presence-only cannot validate correctness, funding, permissions, or safety of secrets" in en.text
    assert DRY_RUN_TEXT in en.text
    assert "credential_values_read: false" in en.text
    assert "raw_values_emitted: false" in en.text
    assert "allowed_for_live: false" in en.text
    assert "resolved_blocker_count: 0" in en.text
    assert "PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED: absent" in en.text
    assert "missing_required_marker:PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED" in en.text

    assert "Проверка готовности credentials" in ru.text
    assert "Только наличие маркеров" in ru.text
    assert "Значения не показываются" in ru.text
    assert "Live не включён" in ru.text
    assert "Только dry-run" in ru.text


def test_dry_run_action_points_only_to_explicit_064_gate_with_dry_run(tmp_path: Path) -> None:
    _write_064_artifacts(tmp_path)
    action = safe_action_by_id(DRY_RUN_ACTION_ID)
    generated = write_telegram_credentials_readiness_review_064t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / "telegram_credentials_readiness_review_064t",
        generated_at=GENERATED_AT,
    )
    controls = generated["controls"]

    assert action is not None
    assert safe_action_by_callback(DRY_RUN_CALLBACK) == action
    assert validate_safe_action(action) == []
    assert action.module == "pm_bot.operator_runner.explicit_live_credentials_readiness_gate"
    assert action.args == ("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run")
    assert list(action.command_display) == DRY_RUN_COMMAND
    assert controls["allowed_dry_run_command"] == DRY_RUN_COMMAND
    assert controls["allowed_dry_run_action"]["action_id"] == DRY_RUN_ACTION_ID
    assert controls["allowed_dry_run_action"]["callback_data"] == DRY_RUN_CALLBACK
    assert controls["safe_status_view_command"] == "/credentials_readiness_review"
    assert controls["safe_status_view_callback_data"] == VIEW_CALLBACK
    _assert_required_false_flags(controls)


def test_064t_generated_artifacts_emit_no_raw_credential_values(tmp_path: Path) -> None:
    _write_064_artifacts(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    context["raw_secret_fixture"] = " ".join(FAKE_SECRET_VALUES)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/credentials_readiness_review")
    generated = write_telegram_credentials_readiness_review_064t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / "telegram_credentials_readiness_review_064t",
        generated_at=GENERATED_AT,
    )
    rendered = reply.text + "\n" + json.dumps(generated, sort_keys=True)

    for fake in FAKE_SECRET_VALUES:
        assert fake not in rendered
    for payload in (generated["result"], generated["latest_status"], generated["controls"]):
        _assert_required_false_flags(payload)


def test_064t_introduces_no_broad_environment_enumeration() -> None:
    source = inspect.getsource(__import__("pm_bot.operator_runner.telegram_status_registry", fromlist=[""]))

    assert "os.environ" not in source
    assert "environ.items(" not in source
    assert "environ.values(" not in source
    assert "environment_values_read\": True" not in source
    assert "broad_environment_scan_performed\": True" not in source


def test_no_forbidden_telegram_controls_exist_for_064t(tmp_path: Path) -> None:
    _write_064_artifacts(tmp_path)
    generated = write_telegram_credentials_readiness_review_064t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / "telegram_credentials_readiness_review_064t",
        generated_at=GENERATED_AT,
    )

    _assert_no_forbidden_control_terms(_control_records(generated["controls"]))

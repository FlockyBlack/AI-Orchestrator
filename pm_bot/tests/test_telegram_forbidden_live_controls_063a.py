from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from pm_bot.operator_runner import telegram_operator_i18n as i18n
from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
)
from pm_bot.operator_runner.telegram_status_registry import (
    SAFE_ACTIONS,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
    validate_safe_action,
    write_telegram_pre_live_gate_review_062t_artifacts,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FORBIDDEN_EXACT_VALUES = (
    "run_signer",
    "pmbot:run:signer",
    "Run Signer",
)

FORBIDDEN_PHRASE_TERMS = (
    "approve-live",
    "send-order",
    "submit-order",
    "cancel-order",
    "connect-wallet",
    "unlock-wallet",
    "live-enable",
    "live-execute",
)

FORBIDDEN_TOKEN_TERMS = (
    "sign",
    "signer",
    "wallet",
)

FORBIDDEN_CLI_ARGS = (
    "--approve-live",
    "--send-order",
    "--submit-order",
    "--cancel-order",
    "--sign",
    "--wallet",
    "--connect-wallet",
    "--unlock-wallet",
    "--live-enable",
    "--live-execute",
    "--execute",
)

FORBIDDEN_062T_CONTROL_FLAGS = (
    "forbidden_live_controls_added",
    "approve_live_control_added",
    "send_order_control_added",
    "submit_order_control_added",
    "cancel_order_control_added",
    "sign_control_added",
    "wallet_control_added",
    "connect_wallet_control_added",
    "unlock_wallet_control_added",
    "live_enable_control_added",
    "live_execute_control_added",
)


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _forbidden_hits(value: Any) -> list[str]:
    text = str(value)
    lower = text.lower()
    tokens = _tokenize(text)
    hits: list[str] = []
    for exact in FORBIDDEN_EXACT_VALUES:
        if exact.lower() == lower or exact.lower() in lower:
            hits.append(exact)
    for phrase in FORBIDDEN_PHRASE_TERMS:
        forms = {phrase, phrase.replace("-", " "), phrase.replace("-", "_")}
        for form in forms:
            if form in lower:
                hits.append(phrase)
                break
    for token in FORBIDDEN_TOKEN_TERMS:
        if token in tokens:
            hits.append(token)
    return sorted(set(hits))


def _assert_no_forbidden_control_terms(records: Iterable[tuple[str, Any]]) -> None:
    violations = []
    for label, value in records:
        hits = _forbidden_hits(value)
        if hits:
            violations.append({"field": label, "value": str(value), "hits": hits})
    assert violations == []


def _button_records() -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for language in ("en", "ru"):
        row_sets = {
            "telegram_console": telegram_console_button_rows(language),
            "home": i18n.home_button_rows(language),
            "panel_fallback": i18n.panel_fallback_button_rows(language),
        }
        for row_set_name, rows in row_sets.items():
            for row_index, row in enumerate(rows):
                for button_index, (label, callback_data) in enumerate(row):
                    prefix = f"{row_set_name}.{language}.{row_index}.{button_index}"
                    records.append((f"{prefix}.label", label))
                    records.append((f"{prefix}.callback_data", callback_data))
        records.append((f"panel_launch.{language}.label", i18n.panel_launch_button_label(language)))
    for row_index, row in enumerate(i18n.language_selection_button_rows()):
        for button_index, (label, callback_data) in enumerate(row):
            prefix = f"language_selection.{row_index}.{button_index}"
            records.append((f"{prefix}.label", label))
            records.append((f"{prefix}.callback_data", callback_data))
    for row_index, row in enumerate(i18n.all_button_rows()):
        for button_index, (label, callback_data) in enumerate(row):
            prefix = f"all_button_rows.{row_index}.{button_index}"
            records.append((f"{prefix}.label", label))
            records.append((f"{prefix}.callback_data", callback_data))
    return records


def _supported_command_records() -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for index, command in enumerate(SUPPORTED_COMMANDS):
        records.append((f"supported_commands.{index}", command))
    for index, command in enumerate(SAFE_ACTION_COMMANDS):
        records.append((f"safe_action_commands.{index}", command))
    for callback_data, command in CALLBACK_COMMAND_MAP.items():
        records.append((f"callback_command_map.{callback_data}.callback_data", callback_data))
        records.append((f"callback_command_map.{callback_data}.command", command))
    for index, (command, description) in enumerate(runtime.telegram_command_menu_items()):
        records.append((f"telegram_command_menu.{index}.command", command))
        records.append((f"telegram_command_menu.{index}.description", description))
    return records


def _safe_action_records() -> list[tuple[str, Any]]:
    records: list[tuple[str, Any]] = []
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
        for index, item in enumerate(action.command_display):
            records.append((f"{prefix}.command_display.{index}", item))
    return records


def _controls_manifest_control_records(controls: Mapping[str, Any]) -> list[tuple[str, Any]]:
    action = dict(controls.get("allowed_dry_run_action", {}))
    records: list[tuple[str, Any]] = [
        ("controls.safe_status_view_command", controls.get("safe_status_view_command", "")),
        ("controls.safe_status_view_callback_data", controls.get("safe_status_view_callback_data", "")),
        ("controls.allowed_dry_run_action.action_id", action.get("action_id", "")),
        ("controls.allowed_dry_run_action.callback_data", action.get("callback_data", "")),
        ("controls.allowed_dry_run_action.label_en", action.get("label_en", "")),
        ("controls.allowed_dry_run_action.label_ru", action.get("label_ru", "")),
        ("controls.allowed_dry_run_action.action_type", action.get("action_type", "")),
    ]
    for index, item in enumerate(controls.get("allowed_dry_run_command", [])):
        records.append((f"controls.allowed_dry_run_command.{index}", item))
    return records


def test_telegram_control_labels_callbacks_and_commands_have_no_forbidden_live_sign_wallet_controls() -> None:
    records = [
        *_button_records(),
        *_supported_command_records(),
        *_safe_action_records(),
    ]

    _assert_no_forbidden_control_terms(records)


def test_safe_action_registry_excludes_signer_wallet_and_live_execution_actions() -> None:
    assert safe_action_by_id("run_signer") is None
    assert safe_action_by_callback("pmbot:run:signer") is None

    for action in SAFE_ACTIONS:
        assert validate_safe_action(action) == []
        assert "--dry-run" in action.args
        assert "signer" not in _tokenize(action.module)
        assert "wallet" not in _tokenize(action.module)
        for forbidden_arg in FORBIDDEN_CLI_ARGS:
            assert forbidden_arg not in action.args
            assert forbidden_arg not in action.command_display


def test_generated_062t_controls_manifest_keeps_forbidden_live_control_flags_false(tmp_path: Path) -> None:
    generated = write_telegram_pre_live_gate_review_062t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / "telegram_pre_live_gate_review_062t",
        generated_at=GENERATED_AT,
    )
    controls = generated["controls"]

    for field in FORBIDDEN_062T_CONTROL_FLAGS:
        assert controls[field] is False, field
    assert controls["allowed_dry_run_command"] == [
        "python",
        "-m",
        "pm_bot.operator_runner.pre_live_tiny_order_gate",
        "--market",
        "BTC",
        "--strategy",
        "tiny-momentum",
        "--dry-run",
    ]
    _assert_no_forbidden_control_terms(_controls_manifest_control_records(controls))

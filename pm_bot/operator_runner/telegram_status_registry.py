from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json
from pm_bot.trading_core.telegram_real_check_results_display_073t import (
    ARTIFACT_DIR_NAME as TELEGRAM_REAL_CHECK_RESULTS_073T_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_REAL_CHECK_RESULTS_073T_LATEST_STATUS_FILENAME,
    normalize_telegram_real_check_results_status_summary,
)
from pm_bot.trading_core.telegram_order_prep_packet_status_072b import (
    ARTIFACT_DIR_NAME as TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_LATEST_STATUS_FILENAME,
    normalize_telegram_order_prep_packet_status_summary,
)
from pm_bot.trading_core.telegram_order_prep_status_071e import (
    ARTIFACT_DIR_NAME as TELEGRAM_ORDER_PREP_STATUS_071E_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_ORDER_PREP_STATUS_071E_LATEST_STATUS_FILENAME,
    TASK_ID as TASK_ID_071E,
)
from pm_bot.trading_core.telegram_operator_token_selection_074b import (
    ARTIFACT_DIR_NAME as TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_LATEST_STATUS_FILENAME,
    normalize_telegram_operator_token_selection_summary,
)
from pm_bot.trading_core.telegram_risk_engine_v2_status_075b import (
    ARTIFACT_DIR_NAME as TELEGRAM_RISK_ENGINE_V2_STATUS_075B_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_RISK_ENGINE_V2_STATUS_075B_LATEST_STATUS_FILENAME,
    build_telegram_risk_engine_v2_status,
    normalize_telegram_risk_engine_v2_status_summary,
)
from pm_bot.trading_core.telegram_wallet_auth_status_dashboard import (
    ARTIFACT_DIR_NAME as TELEGRAM_CONNECTION_STATUS_067E_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_CONNECTION_STATUS_067E_LATEST_STATUS_FILENAME,
    TASK_ID as TASK_ID_067E,
)

TASK_ID = "ORCH-PMBOT-TELEGRAM-060T-OPERATOR-CONSOLE-FOR-PMBOT-STATUS-AND-DRY-RUNS"
TASK_ID_061T = "ORCH-PMBOT-TELEGRAM-061T-TINY-ORDER-SCAFFOLD-REVIEW-PANEL"
TASK_ID_062T = "ORCH-PMBOT-TELEGRAM-062T-PRE-LIVE-TINY-ORDER-GATE-REVIEW-PANEL"
TASK_ID_063T = "ORCH-PMBOT-TELEGRAM-063T-SUPERVISED-LIVE-ENABLEMENT-REVIEW-PANEL"
TASK_ID_064T = "ORCH-PMBOT-TELEGRAM-064T-CREDENTIALS-READINESS-REVIEW-PANEL"
TELEGRAM_CONNECTION_STATUS_067E_FLOW_ID = "telegram_connection_status_067e"
TELEGRAM_ORDER_PREP_STATUS_071E_FLOW_ID = "telegram_order_prep_status_071e"
TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_FLOW_ID = "telegram_order_prep_packet_status_072b"
TELEGRAM_REAL_CHECK_RESULTS_073T_FLOW_ID = "telegram_real_check_results_073t"
TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_FLOW_ID = "telegram_operator_token_selection_074b"
TELEGRAM_RISK_ENGINE_V2_STATUS_075B_FLOW_ID = "telegram_risk_engine_v2_status_075b"
STATUS_REGISTRY_CONTRACT = "pmbot_telegram_operator_console_060t_status_registry.v1"
STATUS_CARD_CONTRACT = "pmbot_telegram_operator_console_060t_status_card.v1"
READINESS_SUMMARY_CONTRACT = "pmbot_telegram_operator_console_060t_readiness.v1"
ACTION_RESULT_CONTRACT = "pmbot_telegram_operator_console_060t_action_result.v1"
TINY_ORDER_REVIEW_061T_STATUS_CONTRACT = "pmbot_telegram_tiny_order_review_061t_status.v1"
TINY_ORDER_REVIEW_061T_RESULT_CONTRACT = "pmbot_telegram_tiny_order_review_061t_result.v1"
PRE_LIVE_GATE_REVIEW_062T_STATUS_CONTRACT = "pmbot_telegram_pre_live_gate_review_062t_status.v1"
PRE_LIVE_GATE_REVIEW_062T_RESULT_CONTRACT = "pmbot_telegram_pre_live_gate_review_062t_result.v1"
PRE_LIVE_GATE_REVIEW_062T_CONTROLS_CONTRACT = "pmbot_telegram_pre_live_gate_review_062t_controls.v1"
SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_STATUS_CONTRACT = (
    "pmbot_telegram_supervised_live_enablement_review_063t_status.v1"
)
SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_RESULT_CONTRACT = (
    "pmbot_telegram_supervised_live_enablement_review_063t_result.v1"
)
SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_CONTROLS_CONTRACT = (
    "pmbot_telegram_supervised_live_enablement_review_063t_controls.v1"
)
CREDENTIALS_READINESS_REVIEW_064T_STATUS_CONTRACT = (
    "pmbot_telegram_credentials_readiness_review_064t_status.v1"
)
CREDENTIALS_READINESS_REVIEW_064T_RESULT_CONTRACT = (
    "pmbot_telegram_credentials_readiness_review_064t_result.v1"
)
CREDENTIALS_READINESS_REVIEW_064T_CONTROLS_CONTRACT = (
    "pmbot_telegram_credentials_readiness_review_064t_controls.v1"
)

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
TELEGRAM_OPERATOR_CONSOLE_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "telegram_operator_console_060t"
TELEGRAM_OPERATOR_CONSOLE_RESULT_PATH = (
    TELEGRAM_OPERATOR_CONSOLE_ARTIFACT_DIR / "telegram_operator_console_060t_result.json"
)
TELEGRAM_OPERATOR_CONSOLE_REGISTRY_SNAPSHOT_PATH = (
    TELEGRAM_OPERATOR_CONSOLE_ARTIFACT_DIR / "telegram_operator_console_060t_status_registry_snapshot.json"
)
LATEST_TELEGRAM_OPERATOR_CONSOLE_STATUS_PATH = (
    TELEGRAM_OPERATOR_CONSOLE_ARTIFACT_DIR / "latest_telegram_operator_console_status_060t.json"
)
TELEGRAM_TINY_ORDER_REVIEW_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "telegram_tiny_order_review_061t"
TELEGRAM_TINY_ORDER_REVIEW_RESULT_PATH = (
    TELEGRAM_TINY_ORDER_REVIEW_ARTIFACT_DIR / "telegram_tiny_order_review_061t_result.json"
)
LATEST_TELEGRAM_TINY_ORDER_REVIEW_STATUS_PATH = (
    TELEGRAM_TINY_ORDER_REVIEW_ARTIFACT_DIR / "latest_telegram_tiny_order_review_status_061t.json"
)
TELEGRAM_TINY_ORDER_REVIEW_REGISTRY_SNAPSHOT_PATH = (
    TELEGRAM_TINY_ORDER_REVIEW_ARTIFACT_DIR / "telegram_tiny_order_review_registry_snapshot_061t.json"
)
TELEGRAM_PRE_LIVE_GATE_REVIEW_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "telegram_pre_live_gate_review_062t"
TELEGRAM_PRE_LIVE_GATE_REVIEW_RESULT_PATH = (
    TELEGRAM_PRE_LIVE_GATE_REVIEW_ARTIFACT_DIR / "telegram_pre_live_gate_review_062t_result.json"
)
LATEST_TELEGRAM_PRE_LIVE_GATE_REVIEW_STATUS_PATH = (
    TELEGRAM_PRE_LIVE_GATE_REVIEW_ARTIFACT_DIR / "latest_telegram_pre_live_gate_review_status_062t.json"
)
TELEGRAM_PRE_LIVE_GATE_REVIEW_REGISTRY_SNAPSHOT_PATH = (
    TELEGRAM_PRE_LIVE_GATE_REVIEW_ARTIFACT_DIR / "telegram_pre_live_gate_review_registry_snapshot_062t.json"
)
TELEGRAM_PRE_LIVE_GATE_REVIEW_CONTROLS_PATH = (
    TELEGRAM_PRE_LIVE_GATE_REVIEW_ARTIFACT_DIR / "telegram_pre_live_gate_review_controls_062t.json"
)
TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_ARTIFACT_DIR = (
    DEFAULT_ARTIFACT_ROOT / "telegram_supervised_live_enablement_review_063t"
)
TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_RESULT_PATH = (
    TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_ARTIFACT_DIR
    / "telegram_supervised_live_enablement_review_063t_result.json"
)
LATEST_TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_STATUS_PATH = (
    TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_ARTIFACT_DIR
    / "latest_telegram_supervised_live_enablement_review_status_063t.json"
)
TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_REGISTRY_SNAPSHOT_PATH = (
    TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_ARTIFACT_DIR
    / "telegram_supervised_live_enablement_review_registry_snapshot_063t.json"
)
TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_CONTROLS_PATH = (
    TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_ARTIFACT_DIR
    / "telegram_supervised_live_enablement_review_controls_063t.json"
)
TELEGRAM_CREDENTIALS_READINESS_REVIEW_ARTIFACT_DIR = (
    DEFAULT_ARTIFACT_ROOT / "telegram_credentials_readiness_review_064t"
)
TELEGRAM_CREDENTIALS_READINESS_REVIEW_RESULT_PATH = (
    TELEGRAM_CREDENTIALS_READINESS_REVIEW_ARTIFACT_DIR
    / "telegram_credentials_readiness_review_064t_result.json"
)
LATEST_TELEGRAM_CREDENTIALS_READINESS_REVIEW_STATUS_PATH = (
    TELEGRAM_CREDENTIALS_READINESS_REVIEW_ARTIFACT_DIR
    / "latest_telegram_credentials_readiness_review_status_064t.json"
)
TELEGRAM_CREDENTIALS_READINESS_REVIEW_REGISTRY_SNAPSHOT_PATH = (
    TELEGRAM_CREDENTIALS_READINESS_REVIEW_ARTIFACT_DIR
    / "telegram_credentials_readiness_review_registry_snapshot_064t.json"
)
TELEGRAM_CREDENTIALS_READINESS_REVIEW_CONTROLS_PATH = (
    TELEGRAM_CREDENTIALS_READINESS_REVIEW_ARTIFACT_DIR
    / "telegram_credentials_readiness_review_controls_064t.json"
)

TINY_ORDER_SCAFFOLD_061_FLOW_ID = "tiny_order_scaffold_061"
TINY_ORDER_SCAFFOLD_061_ARTIFACT_DIR_NAME = "tiny_order_scaffold_061"
TINY_ORDER_SCAFFOLD_061_ARTIFACT_FILENAMES = {
    "latest_status": "latest_tiny_order_scaffold_status_061.json",
    "approval_packet": "manual_tiny_order_approval_packet_061.json",
    "candidate": "tiny_order_candidate_061.json",
    "hard_limits": "tiny_order_hard_limits_061.json",
    "submission_availability": "tiny_order_submission_availability_061.json",
}
PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID = "pre_live_tiny_order_gate_062p"
PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_DIR_NAME = "pre_live_tiny_order_gate_062p"
PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_FILENAMES = {
    "latest_status": "latest_pre_live_tiny_order_gate_status_062p.json",
    "checklist": "pre_live_tiny_order_checklist_062p.json",
    "blockers": "pre_live_tiny_order_blockers_062p.json",
    "readiness_summary": "pre_live_tiny_order_readiness_summary_062p.json",
    "operator_md": "pre_live_tiny_order_gate_062p_operator.md",
}
SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID = "supervised_tiny_live_enablement_gate_063"
SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_DIR_NAME = (
    "supervised_tiny_live_enablement_gate_063"
)
SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_FILENAMES = {
    "latest_status": "latest_supervised_tiny_live_enablement_status_063.json",
    "operator_checklist": "supervised_tiny_live_operator_checklist_063.json",
    "blockers": "supervised_tiny_live_blockers_063.json",
    "risk_limits": "supervised_tiny_live_risk_limits_063.json",
    "kill_switch_plan": "supervised_tiny_live_kill_switch_plan_063.json",
    "cancel_plan": "supervised_tiny_live_cancel_plan_063.json",
    "failure_plan": "supervised_tiny_live_failure_plan_063.json",
    "env_readiness": "supervised_tiny_live_env_readiness_063.json",
    "manual_approval_packet": "supervised_tiny_live_manual_approval_packet_063.json",
    "operator_md": "supervised_tiny_live_enablement_gate_063_operator.md",
}
EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID = "explicit_live_credentials_readiness_gate_064"
EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_DIR_NAME = (
    "explicit_live_credentials_readiness_gate_064"
)
EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_FILENAMES = {
    "latest_status": "latest_explicit_live_credentials_readiness_gate_status_064.json",
    "marker_presence": "redacted_marker_presence_064.json",
    "operator_approval_boundary": "operator_approval_boundary_064.json",
    "safety_policy_validation": "credential_safety_policy_validation_064.json",
    "blockers": "live_credentials_readiness_blockers_064.json",
    "operator_checklist": "explicit_live_credentials_operator_checklist_064.json",
    "readiness_summary": "explicit_live_credentials_readiness_summary_064.json",
    "result": "explicit_live_credentials_readiness_gate_064_result.json",
    "operator_md": "explicit_live_credentials_readiness_gate_064_operator.md",
}

FORCED_FALSE_SAFETY_FLAGS = (
    "operator_approved",
    "candidate_is_executable",
    "signing_available",
    "signed_payload_available",
    "order_submission_available",
    "wallet_available",
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
    "ready_for_future_live_enablement",
)

FORBIDDEN_ACTION_LABEL_TERMS = (
    "SEND ORDER",
    "CANCEL ORDER",
    "SIGN PAYLOAD",
    "CONNECT WALLET",
    "APPROVE LIVE",
    "ENABLE LIVE",
    "VIEW BALANCE",
    "VIEW POSITION",
    "VIEW FILLS",
    "VIEW FILL",
    "TRADE NOW",
)

FORBIDDEN_COMMAND_TERMS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--wallet",
    "--signing",
    "--sign",
    "--order",
    "--submit",
    "--cancel",
    "--approve-live",
    "--balances",
    "--positions",
    "--fills",
)


@dataclass(frozen=True)
class TelegramStatusSource:
    flow_id: str
    section: str
    artifact_dir_name: str
    latest_status_filename: str
    context_key: str
    label_en: str
    label_ru: str


@dataclass(frozen=True)
class TelegramSafeAction:
    action_id: str
    callback_data: str
    label_en: str
    label_ru: str
    module: str
    args: tuple[str, ...]
    action_type: str = "dry_run_command"

    @property
    def command_display(self) -> tuple[str, ...]:
        return ("python", "-m", self.module, *self.args)


STATUS_SOURCES: tuple[TelegramStatusSource, ...] = (
    TelegramStatusSource(
        flow_id="paper_canary_drill_052",
        section="Paper Runs",
        artifact_dir_name="paper_canary_drill_052",
        latest_status_filename="latest_paper_canary_status_052.json",
        context_key="paper_canary_drill_status_summary",
        label_en="Paper Canary 052",
        label_ru="Бумажный canary 052",
    ),
    TelegramStatusSource(
        flow_id="paper_trading_loop_053",
        section="Paper Runs",
        artifact_dir_name="paper_trading_loop_053",
        latest_status_filename="latest_paper_trading_status_053.json",
        context_key="paper_trading_loop_status_summary",
        label_en="Paper Loop 053",
        label_ru="Бумажный прогон 053",
    ),
    TelegramStatusSource(
        flow_id="public_market_paper_loop_054",
        section="Public Market Evidence",
        artifact_dir_name="public_market_paper_loop_054",
        latest_status_filename="latest_public_market_paper_status_054.json",
        context_key="public_market_paper_loop_status_summary",
        label_en="Public Market Paper Loop 054",
        label_ru="Публичный рынок 054",
    ),
    TelegramStatusSource(
        flow_id="paper_decision_ledger_055",
        section="Decision Ledger",
        artifact_dir_name="paper_decision_ledger_055",
        latest_status_filename="latest_paper_decision_ledger_status_055.json",
        context_key="paper_decision_ledger_status_summary",
        label_en="Decision Ledger 055",
        label_ru="Журнал решений 055",
    ),
    TelegramStatusSource(
        flow_id="live_connector_preflight_056",
        section="Live Readiness",
        artifact_dir_name="live_connector_preflight_056",
        latest_status_filename="latest_live_connector_preflight_status_056.json",
        context_key="live_connector_preflight_status_summary",
        label_en="Live Connector Preflight 056",
        label_ru="Live-проверка 056",
    ),
    TelegramStatusSource(
        flow_id="authenticated_clob_preflight_057",
        section="Live Readiness",
        artifact_dir_name="authenticated_clob_preflight_057",
        latest_status_filename="latest_authenticated_clob_preflight_status_057.json",
        context_key="authenticated_clob_preflight_status_summary",
        label_en="Authenticated CLOB Preflight 057",
        label_ru="Authenticated CLOB 057",
    ),
    TelegramStatusSource(
        flow_id="clob_l2_marker_preflight_058",
        section="Live Readiness",
        artifact_dir_name="clob_l2_marker_preflight_058",
        latest_status_filename="latest_clob_l2_marker_preflight_status_058.json",
        context_key="clob_l2_marker_preflight_status_summary",
        label_en="CLOB L2 Marker Preflight 058",
        label_ru="CLOB L2 marker 058",
    ),
    TelegramStatusSource(
        flow_id="no_order_auth_get_preflight_059",
        section="Live Readiness",
        artifact_dir_name="no_order_auth_get_preflight_059",
        latest_status_filename="latest_no_order_auth_get_preflight_status_059.json",
        context_key="no_order_auth_get_preflight_status_summary",
        label_en="No-Order Auth GET Preflight 059",
        label_ru="No-order auth GET 059",
    ),
    TelegramStatusSource(
        flow_id="signer_boundary_preflight_060",
        section="Live Readiness",
        artifact_dir_name="signer_boundary_preflight_060",
        latest_status_filename="latest_signer_boundary_preflight_status_060.json",
        context_key="signer_boundary_preflight_status_summary",
        label_en="Signer Boundary Preflight 060",
        label_ru="Граница подписи 060",
    ),
    TelegramStatusSource(
        flow_id=TINY_ORDER_SCAFFOLD_061_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TINY_ORDER_SCAFFOLD_061_ARTIFACT_DIR_NAME,
        latest_status_filename=TINY_ORDER_SCAFFOLD_061_ARTIFACT_FILENAMES["latest_status"],
        context_key="tiny_order_scaffold_status_summary",
        label_en="Tiny Order Scaffold 061",
        label_ru="Малый ордер 061",
    ),
    TelegramStatusSource(
        flow_id=PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_DIR_NAME,
        latest_status_filename=PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_FILENAMES["latest_status"],
        context_key="pre_live_tiny_order_gate_status_summary",
        label_en="Pre-live tiny order gate",
        label_ru="Предлайв-гейт tiny order",
    ),
    TelegramStatusSource(
        flow_id=SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_DIR_NAME,
        latest_status_filename=SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_FILENAMES["latest_status"],
        context_key="supervised_tiny_live_enablement_gate_status_summary",
        label_en="Supervised readiness review 063",
        label_ru="Обзор supervised readiness 063",
    ),
    TelegramStatusSource(
        flow_id=EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_DIR_NAME,
        latest_status_filename=EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_FILENAMES["latest_status"],
        context_key="explicit_live_credentials_readiness_gate_status_summary",
        label_en="Credentials readiness review",
        label_ru="Проверка готовности credentials",
    ),
    TelegramStatusSource(
        flow_id=TELEGRAM_CONNECTION_STATUS_067E_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TELEGRAM_CONNECTION_STATUS_067E_ARTIFACT_DIR_NAME,
        latest_status_filename=TELEGRAM_CONNECTION_STATUS_067E_LATEST_STATUS_FILENAME,
        context_key="telegram_connection_status_067e_status_summary",
        label_en="Connection status 067E",
        label_ru="Подключение 067E",
    ),
    TelegramStatusSource(
        flow_id=TELEGRAM_REAL_CHECK_RESULTS_073T_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TELEGRAM_REAL_CHECK_RESULTS_073T_ARTIFACT_DIR_NAME,
        latest_status_filename=TELEGRAM_REAL_CHECK_RESULTS_073T_LATEST_STATUS_FILENAME,
        context_key="telegram_real_check_results_073t_status_summary",
        label_en="Real-check results display",
        label_ru="Проверка подключения",
    ),
    TelegramStatusSource(
        flow_id=TELEGRAM_ORDER_PREP_STATUS_071E_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TELEGRAM_ORDER_PREP_STATUS_071E_ARTIFACT_DIR_NAME,
        latest_status_filename=TELEGRAM_ORDER_PREP_STATUS_071E_LATEST_STATUS_FILENAME,
        context_key="telegram_order_prep_status_071e_status_summary",
        label_en="Order prep status 071E",
        label_ru="Подготовка ордера 071E",
    ),
    TelegramStatusSource(
        flow_id=TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_ARTIFACT_DIR_NAME,
        latest_status_filename=TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_LATEST_STATUS_FILENAME,
        context_key="telegram_order_prep_packet_status_072b_status_summary",
        label_en="Order prep packet screen",
        label_ru="Подготовка первого ордера",
    ),
    TelegramStatusSource(
        flow_id=TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_ARTIFACT_DIR_NAME,
        latest_status_filename=TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_LATEST_STATUS_FILENAME,
        context_key="telegram_operator_token_selection_074b_status_summary",
        label_en="Token selection review",
        label_ru="Выбор рынка / Token ID",
    ),
    TelegramStatusSource(
        flow_id=TELEGRAM_RISK_ENGINE_V2_STATUS_075B_FLOW_ID,
        section="Live Readiness",
        artifact_dir_name=TELEGRAM_RISK_ENGINE_V2_STATUS_075B_ARTIFACT_DIR_NAME,
        latest_status_filename=TELEGRAM_RISK_ENGINE_V2_STATUS_075B_LATEST_STATUS_FILENAME,
        context_key="telegram_risk_engine_v2_status_075b_status_summary",
        label_en="Risk Engine v2",
        label_ru="Risk Engine v2",
    ),
)

SAFE_ACTIONS: tuple[TelegramSafeAction, ...] = (
    TelegramSafeAction(
        action_id="run_paper_canary_052",
        callback_data="pmbot:run:paper_canary_052",
        label_en="Run Paper Canary 052",
        label_ru="Бумажный canary 052",
        module="pm_bot.operator_runner.paper_canary_drill",
        args=("--market", "BTC", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_paper_loop_053",
        callback_data="pmbot:run:paper_loop_053",
        label_en="Run Paper Loop 053",
        label_ru="Бумажный прогон 053",
        module="pm_bot.operator_runner.paper_trading_loop",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_public_market_paper_loop_054",
        callback_data="pmbot:run:public_market_paper_loop_054",
        label_en="Run Public Market Paper Loop 054",
        label_ru="Публичный рынок 054",
        module="pm_bot.operator_runner.public_market_paper_loop",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_decision_ledger_055",
        callback_data="pmbot:run:decision_ledger_055",
        label_en="Update Decision Ledger 055",
        label_ru="Журнал решений 055",
        module="pm_bot.operator_runner.paper_decision_ledger",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_live_connector_preflight_056",
        callback_data="pmbot:run:live_connector_preflight_056",
        label_en="Run Live Connector Preflight 056",
        label_ru="Live-проверка 056",
        module="pm_bot.operator_runner.live_connector_preflight",
        args=("--market", "BTC", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_authenticated_clob_preflight_057_058",
        callback_data="pmbot:run:authenticated_clob_preflight_057_058",
        label_en="Run Authenticated CLOB Preflight 057/058",
        label_ru="Authenticated CLOB 057/058",
        module="pm_bot.operator_runner.authenticated_clob_preflight",
        args=("--market", "BTC", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_no_order_auth_get_preflight_059",
        callback_data="pmbot:run:no_order_auth_get_preflight_059",
        label_en="Run No-Order Auth GET Preflight 059",
        label_ru="No-order auth GET 059",
        module="pm_bot.operator_runner.authenticated_clob_preflight",
        args=("--market", "BTC", "--dry-run", "--no-order-auth-get"),
    ),
    TelegramSafeAction(
        action_id="run_tiny_order_scaffold_061",
        callback_data="pmbot:run:tiny_order_scaffold_061",
        label_en="Run Tiny Scaffold 061",
        label_ru="Малый ордер 061",
        module="pm_bot.operator_runner.tiny_order_scaffold",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_pre_live_tiny_order_gate_062p_review_dry_run",
        callback_data="pmbot:run:pre_live_tiny_order_gate_062p_review_dry_run",
        label_en="Run Pre-live Gate 062P Dry-Run",
        label_ru="Dry-run предлайв-гейта 062P",
        module="pm_bot.operator_runner.pre_live_tiny_order_gate",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_credentials_readiness_review_064_dry_run",
        callback_data="pmbot:run:credentials_readiness_review_064_dry_run",
        label_en="Dry-run credentials readiness 064",
        label_ru="Dry-run готовности credentials 064",
        module="pm_bot.operator_runner.explicit_live_credentials_readiness_gate",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
    TelegramSafeAction(
        action_id="run_connection_status_067e",
        callback_data="pmbot:run:connection_status_067e",
        label_en="Run read-only status check 067E",
        label_ru="Запустить read-only проверку",
        module="pm_bot.operator_runner.telegram_connection_status_dashboard",
        args=("--dry-run",),
    ),
    TelegramSafeAction(
        action_id="run_local_real_check_bundle_072c",
        callback_data="pmbot:run:local_real_check_bundle_072c",
        label_en="Run local real-check bundle 072C",
        label_ru="Запустить локальную проверку",
        module="pm_bot.operator_runner.local_real_check_bundle",
        args=("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run"),
    ),
)

STATUS_READ_BUTTONS = {
    "pmbot:status": {"label_en": "Show Latest Status", "label_ru": "📊 Статус", "command": "/status"},
    "pmbot:blockers": {"label_en": "Show Blockers", "label_ru": "🚧 Блокеры", "command": "/blockers"},
    "pmbot:readiness": {"label_en": "Show Readiness %", "label_ru": "Готовность %", "command": "/readiness"},
}

_TOKEN_RE = re.compile(r"\b\d{5,}:[A-Za-z0-9_-]{20,}\b")
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b|\bsk-proj-[A-Za-z0-9_-]{16,}\b")
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    flags=re.DOTALL,
)


def build_telegram_status_registry_snapshot(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    cards = [_build_status_card(source, artifact_root=root, generated_at=generated_at) for source in STATUS_SOURCES]
    cards_by_flow = {card["flow_id"]: card for card in cards}
    context_fields = {
        source.context_key: dict(cards_by_flow[source.flow_id]["status_summary"]) for source in STATUS_SOURCES
    }
    readiness = build_readiness_summary(cards_by_flow, generated_at=generated_at)
    blockers = build_blockers_summary(cards_by_flow)
    latest_artifacts = build_latest_artifacts(cards_by_flow)
    safety_state = telegram_console_safety_state()
    tiny_order_review = build_tiny_order_review_061t_status(cards_by_flow, generated_at=generated_at)
    pre_live_gate_review = build_pre_live_gate_review_062t_status(cards_by_flow, generated_at=generated_at)
    supervised_live_enablement_review = build_supervised_live_enablement_review_063t_status(
        cards_by_flow,
        generated_at=generated_at,
    )
    credentials_readiness_review = build_credentials_readiness_review_064t_status(
        cards_by_flow,
        generated_at=generated_at,
    )
    snapshot = {
        "contract_version": STATUS_REGISTRY_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "artifact_root": normalize_path(root),
        "status_cards": cards,
        "cards_by_flow": cards_by_flow,
        "status_card_count": len(cards),
        "available_status_count": sum(1 for card in cards if card["available"] is True),
        "missing_status_count": sum(1 for card in cards if card["available"] is not True),
        "readiness_summary": readiness,
        "blockers_summary": blockers,
        "latest_artifacts": latest_artifacts,
        "tiny_order_review_061t": tiny_order_review,
        "pre_live_tiny_order_gate_review_062t": pre_live_gate_review,
        "supervised_live_enablement_review_063t": supervised_live_enablement_review,
        "credentials_readiness_review_064t": credentials_readiness_review,
        "context_fields": context_fields,
        "safe_actions": [safe_action_to_dict(action) for action in SAFE_ACTIONS],
        "status_read_buttons": dict(STATUS_READ_BUTTONS),
        "safe_action_count": len(SAFE_ACTIONS),
        "review_only": True,
        "telegram_safe": True,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
        "raw_telegram_init_data_exposed": False,
        "credential_values_exposed": False,
        "live_trading_available": False,
        "live_execution_blocked": True,
        "safety_state": safety_state,
        **safety_state,
    }
    return snapshot


def build_telegram_console_context(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=generated_at)
    context = dict(snapshot["context_fields"])
    context.update(
        {
            "telegram_operator_console_060t_status_registry": snapshot,
            "telegram_operator_console_status_registry_snapshot": snapshot,
            "telegram_operator_console_readiness_summary": snapshot["readiness_summary"],
            "telegram_operator_console_blockers_summary": snapshot["blockers_summary"],
            "telegram_operator_console_latest_artifacts": snapshot["latest_artifacts"],
            "telegram_operator_console_safety_state": snapshot["safety_state"],
            "telegram_operator_console_artifact_root": snapshot["artifact_root"],
            "telegram_tiny_order_review_061t_status": snapshot["tiny_order_review_061t"],
            "telegram_pre_live_gate_review_062t_status": snapshot["pre_live_tiny_order_gate_review_062t"],
            "telegram_supervised_live_enablement_review_063t_status": snapshot[
                "supervised_live_enablement_review_063t"
            ],
            "telegram_credentials_readiness_review_064t_status": snapshot[
                "credentials_readiness_review_064t"
            ],
            "telegram_risk_engine_v2_status_075b_status": snapshot["context_fields"][
                "telegram_risk_engine_v2_status_075b_status_summary"
            ],
        }
    )
    return context


def build_readiness_summary(
    cards_by_flow: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    paper_ready = _all_available(cards_by_flow, ("paper_canary_drill_052", "paper_trading_loop_053"))
    public_ready = _available(cards_by_flow, "public_market_paper_loop_054")
    ledger_ready = _available(cards_by_flow, "paper_decision_ledger_055")
    live_preflight_ready = _available(cards_by_flow, "live_connector_preflight_056")
    auth_boundary_ready = any(
        _available(cards_by_flow, flow_id)
        for flow_id in (
            "authenticated_clob_preflight_057",
            "clob_l2_marker_preflight_058",
            "no_order_auth_get_preflight_059",
        )
    )
    signer_boundary_ready = _available(cards_by_flow, "signer_boundary_preflight_060")
    tiny_scaffold_ready = _available(cards_by_flow, "tiny_order_scaffold_061")
    pre_live_gate_ready = _available(cards_by_flow, "pre_live_tiny_order_gate_062p")
    supervised_live_enablement_ready = _available(cards_by_flow, "supervised_tiny_live_enablement_gate_063")
    credentials_readiness_ready = _available(cards_by_flow, EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID)
    readiness_items = {
        "paper_system": "ready" if paper_ready else "blocked",
        "public_market_data": "ready" if public_ready else "blocked",
        "decision_ledger": "ready" if ledger_ready else "blocked",
        "live_connector_preflight": "ready" if live_preflight_ready else "blocked",
        "auth_boundary": "ready_live_blocked" if auth_boundary_ready else "blocked",
        "signer_boundary": "ready_live_blocked" if signer_boundary_ready else "not implemented yet",
        "tiny_order_scaffold": "ready_live_blocked" if tiny_scaffold_ready else "not implemented yet",
        "pre_live_tiny_order_gate": "ready_live_blocked" if pre_live_gate_ready else "not implemented yet",
        "supervised_tiny_live_enablement_gate": (
            "ready_live_blocked" if supervised_live_enablement_ready else "not implemented yet"
        ),
        "explicit_live_credentials_readiness_gate": (
            "ready_live_blocked" if credentials_readiness_ready else "not implemented yet"
        ),
        "order_submission": "blocked",
        "live_execution": "blocked",
    }
    countable = (
        "paper_system",
        "public_market_data",
        "decision_ledger",
        "live_connector_preflight",
        "auth_boundary",
        "signer_boundary",
        "tiny_order_scaffold",
        "pre_live_tiny_order_gate",
        "supervised_tiny_live_enablement_gate",
        "explicit_live_credentials_readiness_gate",
    )
    ready_count = sum(1 for key in countable if readiness_items[key] in {"ready", "ready_live_blocked"})
    readiness_percent = int(round((ready_count / len(countable)) * 100))
    signer_boundary_label = "signer_boundary_ready" if signer_boundary_ready else "signer_boundary_missing"
    tiny_scaffold_label = "tiny_order_scaffold_ready" if tiny_scaffold_ready else "tiny_order_scaffold_missing"
    pre_live_gate_label = "pre_live_tiny_order_gate_ready" if pre_live_gate_ready else "pre_live_tiny_order_gate_missing"
    supervised_live_enablement_label = (
        "supervised_tiny_live_enablement_gate_ready"
        if supervised_live_enablement_ready
        else "supervised_tiny_live_enablement_gate_missing"
    )
    credentials_readiness_label = (
        "credentials_readiness_review_ready"
        if credentials_readiness_ready
        else "credentials_readiness_review_missing"
    )
    return {
        "contract_version": READINESS_SUMMARY_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "readiness_percent": readiness_percent,
        "readiness_scope": "telegram_review_only_dry_run_and_preflight_console",
        "items": readiness_items,
        "labels": [
            "paper_demo_ready",
            "pre_live_boundary_ready",
            signer_boundary_label,
            tiny_scaffold_label,
            pre_live_gate_label,
            supervised_live_enablement_label,
            credentials_readiness_label,
            "live_execution_blocked",
        ],
        "paper_demo_ready": paper_ready and public_ready and ledger_ready,
        "pre_live_boundary_ready": live_preflight_ready or auth_boundary_ready,
        "signer_boundary_missing": not signer_boundary_ready,
        "signer_boundary_ready": signer_boundary_ready,
        "tiny_order_scaffold_missing": not tiny_scaffold_ready,
        "tiny_order_scaffold_ready": tiny_scaffold_ready,
        "pre_live_tiny_order_gate_missing": not pre_live_gate_ready,
        "pre_live_tiny_order_gate_ready": pre_live_gate_ready,
        "supervised_tiny_live_enablement_gate_missing": not supervised_live_enablement_ready,
        "supervised_tiny_live_enablement_gate_ready": supervised_live_enablement_ready,
        "credentials_readiness_review_missing": not credentials_readiness_ready,
        "credentials_readiness_review_ready": credentials_readiness_ready,
        "live_execution_blocked": True,
        "review_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def build_blockers_summary(cards_by_flow: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    blocker_reasons: list[str] = []
    unresolved_count = 0
    for flow_id, card in cards_by_flow.items():
        summary = dict(card.get("status_summary", {}))
        blocker_count = _int_or_zero(summary.get("blocker_count"))
        unresolved_count += blocker_count
        for reason in _clean_list(summary.get("top_blocker_reasons")):
            blocker_reasons.append(f"{flow_id}: {reason}")
    if not blocker_reasons:
        blocker_reasons.append("Live execution remains blocked by policy; no approval path exists in Telegram.")
    return {
        "status": "live_execution_blocked",
        "unresolved_blocker_count": unresolved_count,
        "resolved_blocker_count": 0,
        "top_blocker_reasons": blocker_reasons[:10],
        "review_only": True,
        "live_execution_blocked": True,
        **telegram_console_safety_state(),
    }


def build_latest_artifacts(cards_by_flow: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    latest = {
        flow_id: {
            "available": card.get("available") is True,
            "latest_status_path": clean_text(card.get("latest_status_path")),
            "artifact_path": clean_text(dict(card.get("status_summary", {})).get("artifact_path"))
            or clean_text(dict(card.get("status_summary", {})).get("artifact")),
        }
        for flow_id, card in cards_by_flow.items()
    }
    tiny = dict(cards_by_flow.get(TINY_ORDER_SCAFFOLD_061_FLOW_ID, {}).get("status_summary", {}))
    if tiny:
        latest[TINY_ORDER_SCAFFOLD_061_FLOW_ID].update(
            {
                "tiny_order_candidate_path": clean_text(tiny.get("tiny_order_candidate_path")),
                "approval_packet_path": clean_text(tiny.get("approval_packet_path")),
                "tiny_order_hard_limits_path": clean_text(tiny.get("tiny_order_hard_limits_path")),
                "tiny_order_submission_availability_path": clean_text(
                    tiny.get("tiny_order_submission_availability_path")
                ),
            }
        )
    pre_live = dict(cards_by_flow.get(PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID, {}).get("status_summary", {}))
    if pre_live:
        latest[PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID].update(
            {
                "checklist_path": clean_text(pre_live.get("checklist_path")),
                "blockers_path": clean_text(pre_live.get("blockers_path")),
                "readiness_summary_path": clean_text(pre_live.get("readiness_summary_path")),
                "operator_markdown_path": clean_text(pre_live.get("operator_markdown_path")),
            }
        )
    supervised = dict(
        cards_by_flow.get(SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID, {}).get("status_summary", {})
    )
    if supervised:
        latest[SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID].update(
            {
                "operator_checklist_path": clean_text(supervised.get("operator_checklist_path")),
                "blockers_path": clean_text(supervised.get("blockers_path")),
                "risk_limits_path": clean_text(supervised.get("risk_limits_path")),
                "kill_switch_plan_path": clean_text(supervised.get("kill_switch_plan_path")),
                "cancel_plan_path": clean_text(supervised.get("cancel_plan_path")),
                "failure_plan_path": clean_text(supervised.get("failure_plan_path")),
                "env_readiness_path": clean_text(supervised.get("env_readiness_path")),
                "manual_approval_packet_path": clean_text(supervised.get("manual_approval_packet_path")),
                "operator_markdown_path": clean_text(supervised.get("operator_markdown_path")),
            }
        )
    credentials = dict(
        cards_by_flow.get(EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID, {}).get("status_summary", {})
    )
    if credentials:
        latest[EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID].update(
            {
                "marker_presence_path": clean_text(credentials.get("marker_presence_path")),
                "operator_approval_boundary_path": clean_text(credentials.get("operator_approval_boundary_path")),
                "safety_policy_validation_path": clean_text(credentials.get("safety_policy_validation_path")),
                "blockers_path": clean_text(credentials.get("blockers_path")),
                "operator_checklist_path": clean_text(credentials.get("operator_checklist_path")),
                "readiness_summary_path": clean_text(credentials.get("readiness_summary_path")),
                "operator_markdown_path": clean_text(credentials.get("operator_markdown_path")),
            }
        )
    return latest


def build_tiny_order_review_061t_status(
    cards_by_flow: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    card = dict(cards_by_flow.get(TINY_ORDER_SCAFFOLD_061_FLOW_ID, {}))
    summary = dict(card.get("status_summary", {}))
    action = safe_action_by_id("run_tiny_order_scaffold_061")
    hard_limits = dict(summary.get("hard_limits_summary", {}))
    submission = dict(summary.get("submission_status", {}))
    return {
        "contract_version": TINY_ORDER_REVIEW_061T_STATUS_CONTRACT,
        "task_id": TASK_ID_061T,
        "generated_at": generated_at,
        "status": "telegram_tiny_order_review_ready_review_only",
        "source_flow_id": TINY_ORDER_SCAFFOLD_061_FLOW_ID,
        "source_status_available": card.get("available") is True,
        "tiny_candidate_status": clean_text(summary.get("tiny_candidate_status") or summary.get("tiny_candidate")),
        "approval_packet_status": clean_text(summary.get("approval_packet_status") or summary.get("approval_packet")),
        "approval_packet_path": clean_text(summary.get("approval_packet_path")),
        "operator_approved": False,
        "candidate_is_executable": False,
        "hard_limits_summary": hard_limits,
        "submission_status": submission,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "run_tiny_scaffold_action_id": action.action_id if action is not None else "",
        "run_tiny_scaffold_callback_data": action.callback_data if action is not None else "",
        "run_tiny_scaffold_command": list(action.command_display) if action is not None else [],
        "allowed_button_label": action.label_en if action is not None else "",
        "allowed_ru_button_label": action.label_ru if action is not None else "",
        "forbidden_live_buttons_added": False,
        "review_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def build_pre_live_gate_review_062t_status(
    cards_by_flow: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    card = dict(cards_by_flow.get(PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID, {}))
    summary = dict(card.get("status_summary", {}))
    action = safe_action_by_id("run_pre_live_tiny_order_gate_062p_review_dry_run")
    checklist = dict(summary.get("checklist_summary", {}))
    blockers = dict(summary.get("blockers_summary", {}))
    readiness = dict(summary.get("readiness_summary", {}))
    return {
        "contract_version": PRE_LIVE_GATE_REVIEW_062T_STATUS_CONTRACT,
        "task_id": TASK_ID_062T,
        "generated_at": generated_at,
        "status": "telegram_pre_live_gate_review_ready_review_only",
        "source_flow_id": PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID,
        "source_status_available": card.get("available") is True,
        "label_en": "Pre-live tiny order gate",
        "label_ru": "Предлайв-гейт tiny order",
        "source_status": clean_text(summary.get("status") or "not_available"),
        "checklist_path": clean_text(summary.get("checklist_path")),
        "blockers_path": clean_text(summary.get("blockers_path")),
        "readiness_summary_path": clean_text(summary.get("readiness_summary_path")),
        "operator_markdown_path": clean_text(summary.get("operator_markdown_path")),
        "checklist_summary": checklist,
        "blockers_summary": blockers,
        "readiness_summary": readiness,
        "blocker_count": _int_or_zero(summary.get("blocker_count")),
        "resolved_blocker_count": 0,
        "top_blocker_reasons": _clean_list(summary.get("top_blocker_reasons"))[:10],
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "live_execution_approved": False,
        "ready_for_future_live_enablement": False,
        "allowed_for_live": False,
        "run_pre_live_gate_action_id": action.action_id if action is not None else "",
        "run_pre_live_gate_callback_data": action.callback_data if action is not None else "",
        "run_pre_live_gate_command": list(action.command_display) if action is not None else [],
        "allowed_button_label": action.label_en if action is not None else "",
        "allowed_ru_button_label": action.label_ru if action is not None else "",
        "forbidden_live_buttons_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def build_supervised_live_enablement_review_063t_status(
    cards_by_flow: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    card = dict(cards_by_flow.get(SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID, {}))
    summary = dict(card.get("status_summary", {}))
    action = None
    checklist = dict(summary.get("operator_checklist_summary", {}))
    blockers = dict(summary.get("blockers_summary", {}))
    risk_limits = dict(summary.get("risk_limits_summary", {}))
    kill_switch_plan = dict(summary.get("kill_switch_plan_summary", {}))
    cancel_plan = dict(summary.get("cancel_plan_summary", {}))
    failure_plan = dict(summary.get("failure_plan_summary", {}))
    env_readiness = dict(summary.get("env_readiness_summary", {}))
    manual_approval_packet = dict(summary.get("manual_approval_packet_summary", {}))
    return {
        "contract_version": SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_STATUS_CONTRACT,
        "task_id": TASK_ID_063T,
        "generated_at": generated_at,
        "status": "telegram_supervised_live_enablement_review_ready_review_only",
        "source_flow_id": SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID,
        "source_status_available": card.get("available") is True,
        "label_en": "Supervised readiness review 063",
        "label_ru": "Обзор supervised readiness 063",
        "source_status": clean_text(summary.get("status") or "not_available"),
        "operator_checklist_path": clean_text(summary.get("operator_checklist_path")),
        "blockers_path": clean_text(summary.get("blockers_path")),
        "risk_limits_path": clean_text(summary.get("risk_limits_path")),
        "kill_switch_plan_path": clean_text(summary.get("kill_switch_plan_path")),
        "cancel_plan_path": clean_text(summary.get("cancel_plan_path")),
        "failure_plan_path": clean_text(summary.get("failure_plan_path")),
        "env_readiness_path": clean_text(summary.get("env_readiness_path")),
        "manual_approval_packet_path": clean_text(summary.get("manual_approval_packet_path")),
        "operator_markdown_path": clean_text(summary.get("operator_markdown_path")),
        "operator_checklist_summary": checklist,
        "blockers_summary": blockers,
        "risk_limits_summary": risk_limits,
        "kill_switch_plan_summary": kill_switch_plan,
        "cancel_plan_summary": cancel_plan,
        "failure_plan_summary": failure_plan,
        "env_readiness_summary": env_readiness,
        "manual_approval_packet_summary": manual_approval_packet,
        "blocker_count": _int_or_zero(summary.get("blocker_count")),
        "resolved_blocker_count": 0,
        "missing_env_marker_count": _int_or_zero(summary.get("missing_env_marker_count")),
        "top_blocker_reasons": _clean_list(summary.get("top_blocker_reasons"))[:10],
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "run_supervised_gate_action_id": action.action_id if action is not None else "",
        "run_supervised_gate_callback_data": action.callback_data if action is not None else "",
        "run_supervised_gate_command": list(action.command_display) if action is not None else [],
        "allowed_button_label": action.label_en if action is not None else "",
        "allowed_ru_button_label": action.label_ru if action is not None else "",
        "forbidden_live_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def build_credentials_readiness_review_064t_status(
    cards_by_flow: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    card = dict(cards_by_flow.get(EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID, {}))
    summary = dict(card.get("status_summary", {}))
    action = safe_action_by_id("run_credentials_readiness_review_064_dry_run")
    return {
        "contract_version": CREDENTIALS_READINESS_REVIEW_064T_STATUS_CONTRACT,
        "task_id": TASK_ID_064T,
        "generated_at": generated_at,
        "status": "telegram_credentials_readiness_review_ready_review_only",
        "source_flow_id": EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID,
        "source_status_available": card.get("available") is True,
        "label_en": "Credentials readiness review",
        "label_ru": "Проверка готовности credentials",
        "source_status": clean_text(summary.get("status") or "not_available"),
        "readiness_status": clean_text(summary.get("readiness_status") or "blocked"),
        "marker_presence_path": clean_text(summary.get("marker_presence_path")),
        "operator_approval_boundary_path": clean_text(summary.get("operator_approval_boundary_path")),
        "safety_policy_validation_path": clean_text(summary.get("safety_policy_validation_path")),
        "blockers_path": clean_text(summary.get("blockers_path")),
        "operator_checklist_path": clean_text(summary.get("operator_checklist_path")),
        "readiness_summary_path": clean_text(summary.get("readiness_summary_path")),
        "operator_markdown_path": clean_text(summary.get("operator_markdown_path")),
        "marker_summary": dict(summary.get("marker_summary", {})),
        "required_marker_presence": [
            dict(row) for row in summary.get("required_marker_presence", []) if isinstance(row, Mapping)
        ],
        "missing_required_markers": _clean_list(summary.get("missing_required_markers")),
        "missing_marker_blockers": [
            dict(row) for row in summary.get("missing_marker_blockers", []) if isinstance(row, Mapping)
        ],
        "operator_approval_boundary_summary": dict(summary.get("operator_approval_boundary_summary", {})),
        "safety_policy_validation_summary": dict(summary.get("safety_policy_validation_summary", {})),
        "blockers_summary": dict(summary.get("blockers_summary", {})),
        "blocker_count": _int_or_zero(summary.get("blocker_count")),
        "resolved_blocker_count": 0,
        "marker_count": _int_or_zero(summary.get("marker_count")),
        "required_marker_count": _int_or_zero(summary.get("required_marker_count")),
        "missing_required_marker_count": _int_or_zero(summary.get("missing_required_marker_count")),
        "present_execution_flag_count": _int_or_zero(summary.get("present_execution_flag_count")),
        "top_blocker_reasons": _clean_list(summary.get("top_blocker_reasons")),
        "redacted_presence_review_ready": summary.get("redacted_presence_review_ready") is True,
        "presence_only_warning": (
            "Presence-only review cannot validate whether credential values are correct, usable, funded, "
            "authorized, or safe. It checks marker names only. Live execution remains blocked."
        ),
        "presence_only": True,
        "values_never_shown": True,
        "redacted_labels_only": True,
        "raw_values_emitted": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "live_ready": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "run_credentials_readiness_action_id": action.action_id if action is not None else "",
        "run_credentials_readiness_callback_data": action.callback_data if action is not None else "",
        "run_credentials_readiness_command": list(action.command_display) if action is not None else [],
        "allowed_button_label": action.label_en if action is not None else "",
        "allowed_ru_button_label": action.label_ru if action is not None else "",
        "forbidden_live_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def execute_safe_telegram_operator_action(
    action_id: str,
    *,
    command_runner: Callable[..., Any] | None = None,
    timeout_seconds: int = 120,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    action = safe_action_by_id(action_id)
    if action is None:
        return _action_result(
            action_id=action_id,
            status="blocked",
            returncode=2,
            stdout="",
            stderr="Unknown Telegram operator action.",
            command=(),
            generated_at=generated_at,
        )
    validation_errors = validate_safe_action(action)
    if validation_errors:
        return _action_result(
            action_id=action_id,
            status="blocked",
            returncode=2,
            stdout="",
            stderr="; ".join(validation_errors),
            command=action.command_display,
            generated_at=generated_at,
        )
    actual_command = (sys.executable, "-m", action.module, *action.args)
    runner = command_runner or subprocess.run
    try:
        completed = runner(
            actual_command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return _action_result(
            action_id=action.action_id,
            status="completed" if int(getattr(completed, "returncode", 1) or 0) == 0 else "failed",
            returncode=int(getattr(completed, "returncode", 1) or 0),
            stdout=clean_text(getattr(completed, "stdout", "")),
            stderr=clean_text(getattr(completed, "stderr", "")),
            command=action.command_display,
            generated_at=generated_at,
        )
    except subprocess.TimeoutExpired as exc:
        return _action_result(
            action_id=action.action_id,
            status="timeout",
            returncode=124,
            stdout=clean_text(exc.stdout),
            stderr=clean_text(exc.stderr) or "Timed out.",
            command=action.command_display,
            generated_at=generated_at,
        )


def write_telegram_operator_console_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path = TELEGRAM_OPERATOR_CONSOLE_ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=generated_at)
    output = Path(output_dir)
    result = {
        "contract_version": "pmbot_telegram_operator_console_060t_result.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "telegram_operator_console_060t_ready",
        "status_registry_snapshot_path": normalize_path(TELEGRAM_OPERATOR_CONSOLE_REGISTRY_SNAPSHOT_PATH),
        "latest_status_path": normalize_path(LATEST_TELEGRAM_OPERATOR_CONSOLE_STATUS_PATH),
        "status_registry": snapshot,
        "safe_actions": snapshot["safe_actions"],
        "readiness_summary": snapshot["readiness_summary"],
        "safety_state": snapshot["safety_state"],
        "review_only": True,
        "live_trading_available": False,
        **telegram_console_safety_state(),
    }
    latest_status = {
        "contract_version": "pmbot_latest_telegram_operator_console_status_060t.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "telegram_operator_console_ready_review_only",
        "readiness_summary": snapshot["readiness_summary"],
        "available_status_count": snapshot["available_status_count"],
        "missing_status_count": snapshot["missing_status_count"],
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_OPERATOR_CONSOLE_STATUS_PATH.name),
        "result_path": normalize_path(output / TELEGRAM_OPERATOR_CONSOLE_RESULT_PATH.name),
        "status_registry_snapshot_path": normalize_path(
            output / TELEGRAM_OPERATOR_CONSOLE_REGISTRY_SNAPSHOT_PATH.name
        ),
        "review_only": True,
        "live_execution_blocked": True,
        **telegram_console_safety_state(),
    }
    write_json(output / TELEGRAM_OPERATOR_CONSOLE_RESULT_PATH.name, result)
    write_json(output / TELEGRAM_OPERATOR_CONSOLE_REGISTRY_SNAPSHOT_PATH.name, snapshot)
    write_json(output / LATEST_TELEGRAM_OPERATOR_CONSOLE_STATUS_PATH.name, latest_status)
    return {
        "result_path": normalize_path(output / TELEGRAM_OPERATOR_CONSOLE_RESULT_PATH.name),
        "status_registry_snapshot_path": normalize_path(output / TELEGRAM_OPERATOR_CONSOLE_REGISTRY_SNAPSHOT_PATH.name),
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_OPERATOR_CONSOLE_STATUS_PATH.name),
        "result": result,
        "status_registry": snapshot,
        "latest_status": latest_status,
    }


def write_telegram_tiny_order_review_061t_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path = TELEGRAM_TINY_ORDER_REVIEW_ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=generated_at)
    output = Path(output_dir)
    latest_status = dict(snapshot["tiny_order_review_061t"])
    result = {
        "contract_version": TINY_ORDER_REVIEW_061T_RESULT_CONTRACT,
        "task_id": TASK_ID_061T,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_TINY_ORDER_REVIEW_STATUS_PATH.name),
        "registry_snapshot_path": normalize_path(output / TELEGRAM_TINY_ORDER_REVIEW_REGISTRY_SNAPSHOT_PATH.name),
        "status_registry": snapshot,
        "tiny_order_review_061t": latest_status,
        "review_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    write_json(output / TELEGRAM_TINY_ORDER_REVIEW_RESULT_PATH.name, result)
    write_json(output / LATEST_TELEGRAM_TINY_ORDER_REVIEW_STATUS_PATH.name, latest_status)
    write_json(output / TELEGRAM_TINY_ORDER_REVIEW_REGISTRY_SNAPSHOT_PATH.name, snapshot)
    return {
        "result_path": normalize_path(output / TELEGRAM_TINY_ORDER_REVIEW_RESULT_PATH.name),
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_TINY_ORDER_REVIEW_STATUS_PATH.name),
        "registry_snapshot_path": normalize_path(output / TELEGRAM_TINY_ORDER_REVIEW_REGISTRY_SNAPSHOT_PATH.name),
        "result": result,
        "latest_status": latest_status,
        "status_registry": snapshot,
    }


def write_telegram_pre_live_gate_review_062t_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path = TELEGRAM_PRE_LIVE_GATE_REVIEW_ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=generated_at)
    output = Path(output_dir)
    latest_status = dict(snapshot["pre_live_tiny_order_gate_review_062t"])
    action = safe_action_by_id("run_pre_live_tiny_order_gate_062p_review_dry_run")
    controls = {
        "contract_version": PRE_LIVE_GATE_REVIEW_062T_CONTROLS_CONTRACT,
        "task_id": TASK_ID_062T,
        "generated_at": generated_at,
        "status": "safe_review_and_dry_run_controls_only",
        "safe_status_view_command": "/pre_live_gate_review",
        "safe_status_view_callback_data": "pmbot:pre_live_gate_review",
        "allowed_dry_run_action": safe_action_to_dict(action) if action is not None else {},
        "allowed_dry_run_command": list(action.command_display) if action is not None else [],
        "forbidden_live_controls_added": False,
        "approve_live_control_added": False,
        "send_order_control_added": False,
        "submit_order_control_added": False,
        "cancel_order_control_added": False,
        "sign_control_added": False,
        "wallet_control_added": False,
        "connect_wallet_control_added": False,
        "unlock_wallet_control_added": False,
        "live_enable_control_added": False,
        "live_execute_control_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    result = {
        "contract_version": PRE_LIVE_GATE_REVIEW_062T_RESULT_CONTRACT,
        "task_id": TASK_ID_062T,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_PRE_LIVE_GATE_REVIEW_STATUS_PATH.name),
        "registry_snapshot_path": normalize_path(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_REGISTRY_SNAPSHOT_PATH.name),
        "controls_path": normalize_path(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_CONTROLS_PATH.name),
        "status_registry": snapshot,
        "pre_live_tiny_order_gate_review_062t": latest_status,
        "controls": controls,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    write_json(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_RESULT_PATH.name, result)
    write_json(output / LATEST_TELEGRAM_PRE_LIVE_GATE_REVIEW_STATUS_PATH.name, latest_status)
    write_json(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_REGISTRY_SNAPSHOT_PATH.name, snapshot)
    write_json(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_CONTROLS_PATH.name, controls)
    return {
        "result_path": normalize_path(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_RESULT_PATH.name),
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_PRE_LIVE_GATE_REVIEW_STATUS_PATH.name),
        "registry_snapshot_path": normalize_path(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_REGISTRY_SNAPSHOT_PATH.name),
        "controls_path": normalize_path(output / TELEGRAM_PRE_LIVE_GATE_REVIEW_CONTROLS_PATH.name),
        "result": result,
        "latest_status": latest_status,
        "status_registry": snapshot,
        "controls": controls,
    }


def write_telegram_supervised_live_enablement_review_063t_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path = TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=generated_at)
    output = Path(output_dir)
    latest_status = dict(snapshot["supervised_live_enablement_review_063t"])
    action = None
    controls = {
        "contract_version": SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_CONTROLS_CONTRACT,
        "task_id": TASK_ID_063T,
        "generated_at": generated_at,
        "status": "safe_review_and_dry_run_controls_only",
        "safe_status_view_command": "/supervised_live_review",
        "safe_status_view_callback_data": "pmbot:supervised_live_review",
        "allowed_dry_run_action": safe_action_to_dict(action) if action is not None else {},
        "allowed_dry_run_command": list(action.command_display) if action is not None else [],
        "forbidden_live_controls_added": False,
        "approve_live_control_added": False,
        "send_order_control_added": False,
        "submit_order_control_added": False,
        "cancel_order_control_added": False,
        "sign_control_added": False,
        "wallet_control_added": False,
        "connect_wallet_control_added": False,
        "unlock_wallet_control_added": False,
        "live_enable_control_added": False,
        "live_execute_control_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    result = {
        "contract_version": SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_RESULT_CONTRACT,
        "task_id": TASK_ID_063T,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(
            output / LATEST_TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_STATUS_PATH.name
        ),
        "registry_snapshot_path": normalize_path(
            output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_REGISTRY_SNAPSHOT_PATH.name
        ),
        "controls_path": normalize_path(output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_CONTROLS_PATH.name),
        "status_registry": snapshot,
        "supervised_live_enablement_review_063t": latest_status,
        "controls": controls,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    write_json(output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_RESULT_PATH.name, result)
    write_json(output / LATEST_TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_STATUS_PATH.name, latest_status)
    write_json(output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_REGISTRY_SNAPSHOT_PATH.name, snapshot)
    write_json(output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_CONTROLS_PATH.name, controls)
    return {
        "result_path": normalize_path(output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_RESULT_PATH.name),
        "latest_status_path": normalize_path(
            output / LATEST_TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_STATUS_PATH.name
        ),
        "registry_snapshot_path": normalize_path(
            output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_REGISTRY_SNAPSHOT_PATH.name
        ),
        "controls_path": normalize_path(output / TELEGRAM_SUPERVISED_LIVE_ENABLEMENT_REVIEW_CONTROLS_PATH.name),
        "result": result,
        "latest_status": latest_status,
        "status_registry": snapshot,
        "controls": controls,
    }


def write_telegram_credentials_readiness_review_064t_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path = TELEGRAM_CREDENTIALS_READINESS_REVIEW_ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    snapshot = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=generated_at)
    output = Path(output_dir)
    latest_status = dict(snapshot["credentials_readiness_review_064t"])
    action = safe_action_by_id("run_credentials_readiness_review_064_dry_run")
    controls = {
        "contract_version": CREDENTIALS_READINESS_REVIEW_064T_CONTROLS_CONTRACT,
        "task_id": TASK_ID_064T,
        "generated_at": generated_at,
        "status": "safe_review_and_dry_run_controls_only",
        "safe_status_view_command": "/credentials_readiness_review",
        "safe_status_view_callback_data": "pmbot:credentials_readiness_review",
        "allowed_dry_run_action": safe_action_to_dict(action) if action is not None else {},
        "allowed_dry_run_command": list(action.command_display) if action is not None else [],
        "forbidden_live_controls_added": False,
        "approve_live_control_added": False,
        "send_order_control_added": False,
        "submit_order_control_added": False,
        "cancel_order_control_added": False,
        "sign_control_added": False,
        "wallet_control_added": False,
        "connect_wallet_control_added": False,
        "unlock_wallet_control_added": False,
        "live_enable_control_added": False,
        "live_execute_control_added": False,
        "credential_values_read": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    result = {
        "contract_version": CREDENTIALS_READINESS_REVIEW_064T_RESULT_CONTRACT,
        "task_id": TASK_ID_064T,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(output / LATEST_TELEGRAM_CREDENTIALS_READINESS_REVIEW_STATUS_PATH.name),
        "registry_snapshot_path": normalize_path(
            output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_REGISTRY_SNAPSHOT_PATH.name
        ),
        "controls_path": normalize_path(output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_CONTROLS_PATH.name),
        "status_registry": snapshot,
        "credentials_readiness_review_064t": latest_status,
        "controls": controls,
        "credential_values_read": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }
    write_json(output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_RESULT_PATH.name, result)
    write_json(output / LATEST_TELEGRAM_CREDENTIALS_READINESS_REVIEW_STATUS_PATH.name, latest_status)
    write_json(output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_REGISTRY_SNAPSHOT_PATH.name, snapshot)
    write_json(output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_CONTROLS_PATH.name, controls)
    return {
        "result_path": normalize_path(output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_RESULT_PATH.name),
        "latest_status_path": normalize_path(
            output / LATEST_TELEGRAM_CREDENTIALS_READINESS_REVIEW_STATUS_PATH.name
        ),
        "registry_snapshot_path": normalize_path(
            output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_REGISTRY_SNAPSHOT_PATH.name
        ),
        "controls_path": normalize_path(output / TELEGRAM_CREDENTIALS_READINESS_REVIEW_CONTROLS_PATH.name),
        "result": result,
        "latest_status": latest_status,
        "status_registry": snapshot,
        "controls": controls,
    }


def safe_action_to_dict(action: TelegramSafeAction) -> dict[str, Any]:
    return {
        "action_id": action.action_id,
        "callback_data": action.callback_data,
        "label_en": action.label_en,
        "label_ru": action.label_ru,
        "action_type": action.action_type,
        "command": list(action.command_display),
        "safe_label": is_safe_action_label(action.label_en) and is_safe_action_label(action.label_ru),
        "dry_run_or_preflight_only": True,
        "review_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def safe_action_by_id(action_id: str) -> TelegramSafeAction | None:
    normalized = clean_text(action_id)
    return next((action for action in SAFE_ACTIONS if action.action_id == normalized), None)


def safe_action_by_callback(callback_data: str) -> TelegramSafeAction | None:
    normalized = clean_text(callback_data)
    return next((action for action in SAFE_ACTIONS if action.callback_data == normalized), None)


def safe_action_command_for_callback(callback_data: str) -> str:
    action = safe_action_by_callback(callback_data)
    return f"/{action.action_id}" if action is not None else ""


def telegram_console_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    ru = clean_text(language).lower() == "ru"
    label_key = "label_ru" if ru else "label_en"
    rows: list[tuple[tuple[str, str], ...]] = []
    rows.append(
        (
            (STATUS_READ_BUTTONS["pmbot:status"][label_key], "pmbot:status"),
            (STATUS_READ_BUTTONS["pmbot:blockers"][label_key], "pmbot:blockers"),
        )
    )
    rows.append(((STATUS_READ_BUTTONS["pmbot:readiness"][label_key], "pmbot:readiness"),))
    rows.append(
        (
            (
                "Предлайв-гейт tiny order" if ru else "Pre-live tiny order gate",
                "pmbot:pre_live_gate_review",
            ),
        )
    )
    rows.append(
        (
            (
                "Обзор supervised readiness 063" if ru else "Supervised readiness review 063",
                "pmbot:supervised_live_review",
            ),
        )
    )
    rows.append(
        (
            (
                "Проверка готовности credentials" if ru else "Credentials readiness review",
                "pmbot:credentials_readiness_review",
            ),
        )
    )
    rows.append((("🔐 Подключение" if ru else "Connection status 067E", "pmbot:connection_status"),))
    rows.append((("Выбор рынка / Token ID" if ru else "Token selection review", "pmbot:token_selection"),))
    rows.append((("🛡 Risk Engine v2", "pmbot:risk_engine_v2"),))
    action_rows = [
        ("run_paper_canary_052", "run_paper_loop_053"),
        ("run_public_market_paper_loop_054", "run_decision_ledger_055"),
        ("run_live_connector_preflight_056",),
        ("run_authenticated_clob_preflight_057_058",),
        ("run_no_order_auth_get_preflight_059",),
        ("run_tiny_order_scaffold_061",),
        ("run_pre_live_tiny_order_gate_062p_review_dry_run",),
        ("run_credentials_readiness_review_064_dry_run",),
        ("run_connection_status_067e",),
        ("run_local_real_check_bundle_072c",),
    ]
    actions_by_id = {action.action_id: action for action in SAFE_ACTIONS}
    for row in action_rows:
        rows.append(
            tuple(
                (
                    getattr(actions_by_id[action_id], "label_ru" if ru else "label_en"),
                    actions_by_id[action_id].callback_data,
                )
                for action_id in row
            )
        )
    return tuple(rows)


def is_safe_action_label(label: str) -> bool:
    upper = clean_text(label).upper()
    return bool(upper) and not any(term in upper for term in FORBIDDEN_ACTION_LABEL_TERMS)


def validate_safe_action(action: TelegramSafeAction) -> list[str]:
    errors: list[str] = []
    if not is_safe_action_label(action.label_en):
        errors.append(f"unsafe English action label: {action.label_en}")
    if not is_safe_action_label(action.label_ru):
        errors.append(f"unsafe Russian action label: {action.label_ru}")
    command_terms = {clean_text(item).lower() for item in action.args}
    for forbidden in FORBIDDEN_COMMAND_TERMS:
        if forbidden in command_terms:
            errors.append(f"forbidden command term in Telegram action {action.action_id}: {forbidden}")
    if "--dry-run" not in command_terms:
        errors.append(f"Telegram action {action.action_id} must include --dry-run")
    if action.module not in {
        "pm_bot.operator_runner.paper_canary_drill",
        "pm_bot.operator_runner.paper_trading_loop",
        "pm_bot.operator_runner.public_market_paper_loop",
        "pm_bot.operator_runner.paper_decision_ledger",
        "pm_bot.operator_runner.live_connector_preflight",
        "pm_bot.operator_runner.authenticated_clob_preflight",
        "pm_bot.operator_runner.tiny_order_scaffold",
        "pm_bot.operator_runner.pre_live_tiny_order_gate",
        "pm_bot.operator_runner.explicit_live_credentials_readiness_gate",
        "pm_bot.operator_runner.telegram_connection_status_dashboard",
        "pm_bot.operator_runner.local_real_check_bundle",
    }:
        errors.append(f"unsupported module for Telegram action {action.action_id}")
    return errors


def telegram_console_safety_state() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "dry_run_actions_only": True,
        "preflight_actions_only": True,
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "live_execution_approved": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "ready_for_future_live_enablement": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "would_submit_order": False,
        "real_order_submitted": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_connection_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
        "raw_telegram_init_data_exposed": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "credential_values_serialized": False,
        "credentials_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credentials_values_exposed": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "environment_values_serialized": False,
        "environment_values_printed": False,
        "environment_values_stored": False,
        "balance_view_enabled": False,
        "position_view_enabled": False,
        "fills_view_enabled": False,
        "pnl_view_enabled": False,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "autonomous_live_trading_added": False,
        "scheduler_or_daemon_added": False,
        "browser_automation_added": False,
        "resolved_blocker_count": 0,
    }


def _build_status_card(
    source: TelegramStatusSource,
    *,
    artifact_root: Path,
    generated_at: str,
) -> dict[str, Any]:
    latest_path = _first_existing_path(_candidate_latest_status_paths(source, artifact_root))
    load_error = ""
    payload: dict[str, Any] = {}
    if latest_path is not None:
        try:
            payload = load_json_object(latest_path, label=f"{source.flow_id} latest status")
        except Exception as exc:
            load_error = exc.__class__.__name__
            payload = {}
    expected_path = _candidate_latest_status_paths(source, artifact_root)[0]
    status_summary = _status_summary_from_payload(payload)
    tiny_order_review: dict[str, Any] = {}
    pre_live_gate_review: dict[str, Any] = {}
    supervised_live_enablement_review: dict[str, Any] = {}
    credentials_readiness_review: dict[str, Any] = {}
    if source.flow_id == TINY_ORDER_SCAFFOLD_061_FLOW_ID:
        tiny_order_review = _tiny_order_review_from_artifacts(
            artifact_root=artifact_root,
            latest_payload=payload,
            generated_at=generated_at,
        )
        status_summary.update(_tiny_order_review_status_summary(tiny_order_review))
    if source.flow_id == PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID:
        pre_live_gate_review = _pre_live_gate_review_from_artifacts(
            artifact_root=artifact_root,
            latest_payload=payload,
            generated_at=generated_at,
        )
        status_summary.update(_pre_live_gate_review_status_summary(pre_live_gate_review))
    if source.flow_id == SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID:
        supervised_live_enablement_review = _supervised_live_enablement_review_from_artifacts(
            artifact_root=artifact_root,
            latest_payload=payload,
            generated_at=generated_at,
        )
        status_summary.update(
            _supervised_live_enablement_review_status_summary(supervised_live_enablement_review)
        )
    if source.flow_id == EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID:
        credentials_readiness_review = _credentials_readiness_review_from_artifacts(
            artifact_root=artifact_root,
            latest_payload=payload,
            generated_at=generated_at,
        )
        status_summary.update(_credentials_readiness_review_status_summary(credentials_readiness_review))
    if source.flow_id == TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_FLOW_ID:
        status_summary.update(normalize_telegram_order_prep_packet_status_summary(payload))
    if source.flow_id == TELEGRAM_REAL_CHECK_RESULTS_073T_FLOW_ID:
        status_summary.update(normalize_telegram_real_check_results_status_summary(payload))
    if source.flow_id == TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_FLOW_ID:
        status_summary.update(normalize_telegram_operator_token_selection_summary(payload))
    risk_engine_explicit_payload_available = False
    if source.flow_id == TELEGRAM_RISK_ENGINE_V2_STATUS_075B_FLOW_ID:
        risk_engine_explicit_payload_available = latest_path is not None and bool(payload) and not load_error
        if not payload:
            payload = build_telegram_risk_engine_v2_status(
                artifact_root=artifact_root,
                generated_at=generated_at,
            )
        status_summary.update(normalize_telegram_risk_engine_v2_status_summary(payload))
    available = bool(payload)
    if source.flow_id == TELEGRAM_RISK_ENGINE_V2_STATUS_075B_FLOW_ID:
        available = (
            risk_engine_explicit_payload_available
            or status_summary.get("source_artifact_available") is True
        )
    return {
        "contract_version": STATUS_CARD_CONTRACT,
        "task_id": TASK_ID,
        "flow_id": source.flow_id,
        "section": source.section,
        "label_en": source.label_en,
        "label_ru": source.label_ru,
        "generated_at": generated_at,
        "available": available,
        "status": clean_text(status_summary.get("status") or "missing"),
        "market": clean_text(status_summary.get("market") or "not_available"),
        "mode": clean_text(status_summary.get("mode") or "review-only"),
        "latest_status_path": normalize_path(latest_path or expected_path),
        "load_error": load_error,
        "status_summary": status_summary,
        "tiny_order_review": tiny_order_review,
        "pre_live_gate_review": pre_live_gate_review,
        "supervised_live_enablement_review": supervised_live_enablement_review,
        "credentials_readiness_review": credentials_readiness_review,
        "telegram_safe": True,
        "review_only": True,
        "live_execution": "blocked",
        "credential_values_exposed": False,
        **telegram_console_safety_state(),
    }


def _candidate_latest_status_paths(source: TelegramStatusSource, artifact_root: Path) -> tuple[Path, ...]:
    paths = [
        artifact_root / source.artifact_dir_name / source.latest_status_filename,
    ]
    if artifact_root.name == source.artifact_dir_name:
        paths.append(artifact_root / source.latest_status_filename)
    paths.append(
        artifact_root
        / "authenticated_clob_preflight_057"
        / source.artifact_dir_name
        / source.latest_status_filename
    )
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(path)
    return tuple(unique)


def _first_existing_path(paths: Sequence[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def _status_summary_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in blockers
            if isinstance(row, Mapping) and clean_text(row.get("reason"))
        ][:8]
    summary = {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or value.get("execution_mode") or "review-only"),
        "live_execution": "blocked",
        "artifact_path": clean_text(value.get("artifact_path") or value.get("artifact")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "evidence_pack_path": clean_text(value.get("evidence_pack_path")),
        "source": clean_text(value.get("source") or value.get("source_type") or "not_available"),
        "risk_decision": clean_text(value.get("risk_decision") or "not_available"),
        "paper_intent_status": clean_text(
            value.get("paper_intent_status") or value.get("paper_order_intent_status") or "not_available"
        ),
        "last_outcome": clean_text(value.get("last_outcome") or value.get("latest_outcome") or "not_available"),
        "ledger_entry_count": _int_or_zero(value.get("ledger_entry_count")),
        "public_network_status": clean_text(value.get("public_network_status") or "not_available"),
        "auth_boundary_status": clean_text(value.get("auth_boundary_status") or "not_available"),
        "auth_presence_status": clean_text(value.get("auth_presence_status") or "not_available"),
        "clob_base_url_status": clean_text(value.get("clob_base_url_status") or "not_available"),
        "l2_marker_presence_status": clean_text(value.get("l2_marker_presence_status") or "not_available"),
        "l2_marker_set_complete": value.get("l2_marker_set_complete") is True,
        "unsafe_raw_value_detected": value.get("unsafe_raw_value_detected") is True,
        "no_order_auth_get_status": clean_text(value.get("no_order_auth_get_status") or "not_available"),
        "real_authenticated_get_performed": value.get("real_authenticated_get_performed") is True,
        "live_candidate_intent_status": clean_text(value.get("live_candidate_intent_status") or "not_available"),
        "unsigned_plan_status": clean_text(value.get("unsigned_plan_status") or "not_available"),
        "unsigned_plan_created": value.get("unsigned_plan_created") is True,
        "unsigned_plan_is_executable": value.get("unsigned_plan_is_executable") is True,
        "signer_status": clean_text(value.get("signer_status") or "blocked"),
        "signed_payload_status": clean_text(value.get("signed_payload_status") or "unavailable"),
        "order_submission_status": clean_text(value.get("order_submission_status") or "blocked"),
        "signer_config_present": value.get("signer_config_present") is True,
        "signed_payload_available": value.get("signed_payload_available") is True,
        "order_submission_available": value.get("order_submission_available") is True,
        "tiny_candidate": clean_text(value.get("tiny_candidate") or "not_available"),
        "tiny_candidate_status": clean_text(value.get("tiny_candidate") or "not_available"),
        "approval_packet": clean_text(value.get("approval_packet") or "not_available"),
        "approval_packet_status": clean_text(value.get("approval_packet") or "not_available"),
        "manual_tiny_order_approval_packet_path": clean_text(
            value.get("manual_tiny_order_approval_packet_path")
        ),
        "approval_packet_path": clean_text(value.get("manual_tiny_order_approval_packet_path")),
        "tiny_order_candidate_path": clean_text(value.get("tiny_order_candidate_path")),
        "tiny_order_hard_limits_path": clean_text(value.get("tiny_order_hard_limits_path")),
        "tiny_order_submission_availability_path": clean_text(
            value.get("tiny_order_submission_availability_path")
        ),
        "pre_live_gate_status": clean_text(value.get("status") or "not_available"),
        "checklist_path": clean_text(value.get("checklist_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "readiness_summary_path": clean_text(value.get("readiness_summary_path")),
        "source_tiny_scaffold_path": clean_text(value.get("source_tiny_scaffold_path")),
        "source_auth_preflight_path": clean_text(value.get("source_auth_preflight_path")),
        "source_safety_scan_path": clean_text(value.get("source_safety_scan_path")),
        "tiny_candidate_present": value.get("tiny_candidate_present") is True,
        "approval_packet_present": value.get("approval_packet_present") is True,
        "market_whitelisted": value.get("market_whitelisted") is True,
        "signer_boundary_present": value.get("signer_boundary_present") is True,
        "auth_preflight_present": value.get("auth_preflight_present") is True,
        "safety_scan_present": value.get("safety_scan_present") is True,
        "operator_checklist_path": clean_text(value.get("operator_checklist_path")),
        "risk_limits_path": clean_text(value.get("risk_limits_path")),
        "kill_switch_plan_path": clean_text(value.get("kill_switch_plan_path")),
        "cancel_plan_path": clean_text(value.get("cancel_plan_path")),
        "failure_plan_path": clean_text(value.get("failure_plan_path")),
        "env_readiness_path": clean_text(value.get("env_readiness_path")),
        "manual_approval_packet_path": clean_text(value.get("manual_approval_packet_path")),
        "source_pre_live_gate_path": clean_text(value.get("source_pre_live_gate_path")),
        "source_tiny_scaffold_path": clean_text(value.get("source_tiny_scaffold_path")),
        "missing_env_marker_count": _int_or_zero(value.get("missing_env_marker_count")),
        "marker_presence_path": clean_text(value.get("marker_presence_path")),
        "operator_approval_boundary_path": clean_text(value.get("operator_approval_boundary_path")),
        "safety_policy_validation_path": clean_text(value.get("safety_policy_validation_path")),
        "missing_required_marker_count": _int_or_zero(value.get("missing_required_marker_count")),
        "present_execution_flag_count": _int_or_zero(value.get("present_execution_flag_count")),
        "required_marker_count": _int_or_zero(value.get("required_marker_count")),
        "marker_count": _int_or_zero(value.get("marker_count")),
        "redacted_presence_review_ready": value.get("redacted_presence_review_ready") is True,
        "live_ready": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "values_never_shown": True,
        "redacted_labels_only": True,
        "readiness_status": clean_text(value.get("readiness_status") or "blocked"),
        "api_keys_added": value.get("api_keys_added") is True,
        "api_keys_status": clean_text(value.get("api_keys_status") or "not_added"),
        "api_keys_display_ru": clean_text(value.get("api_keys_display_ru") or "не добавлены"),
        "api_keys_display_en": clean_text(value.get("api_keys_display_en") or "not added"),
        "private_key_added": value.get("private_key_added") is True,
        "private_key_status": clean_text(value.get("private_key_status") or "not_added"),
        "private_key_display_ru": clean_text(value.get("private_key_display_ru") or "не добавлен"),
        "private_key_display_en": clean_text(value.get("private_key_display_en") or "not added"),
        "wallet_display": clean_text(value.get("wallet_display") or "missing"),
        "signature_type_display": clean_text(value.get("signature_type_display") or "missing"),
        "funder_display": clean_text(value.get("funder_display") or "missing"),
        "l2_auth_probe_status": clean_text(value.get("l2_auth_probe_status") or "not_run"),
        "l2_auth_probe_display": clean_text(value.get("l2_auth_probe_display") or "not run"),
        "open_orders_status": clean_text(value.get("open_orders_status") or "unknown"),
        "balance_allowance_status": clean_text(value.get("balance_allowance_status") or "unknown"),
        "clob_l2_auth_readonly_probe_artifact_available": (
            value.get("clob_l2_auth_readonly_probe_artifact_available") is True
        ),
        "clob_l2_auth_readonly_probe_path": clean_text(value.get("clob_l2_auth_readonly_probe_path")),
        "dashboard_does_not_run_probe": value.get("dashboard_does_not_run_probe") is True,
        "latest_067c_probe_artifact_only": value.get("latest_067c_probe_artifact_only") is True,
        "telegram_screen_title_ru": clean_text(value.get("telegram_screen_title_ru")),
        "telegram_screen_title_en": clean_text(value.get("telegram_screen_title_en")),
        "market_discovery_artifact_available": value.get("market_discovery_artifact_available") is True,
        "market_discovery_artifact_path": clean_text(value.get("market_discovery_artifact_path")),
        "token_resolver_artifact_available": value.get("token_resolver_artifact_available") is True,
        "token_resolver_artifact_path": clean_text(value.get("token_resolver_artifact_path")),
        "account_readonly_artifact_available": value.get("account_readonly_artifact_available") is True,
        "account_readonly_artifact_path": clean_text(value.get("account_readonly_artifact_path")),
        "signed_payload_dry_run_artifact_available": value.get("signed_payload_dry_run_artifact_available") is True,
        "signed_payload_dry_run_artifact_path": clean_text(value.get("signed_payload_dry_run_artifact_path")),
        "market_found": value.get("market_found") is True,
        "market_display_ru": clean_text(value.get("market_display_ru") or "не найден"),
        "market_display_en": clean_text(value.get("market_display_en") or "not found"),
        "token_id_found": value.get("token_id_found") is True,
        "token_id_display_ru": clean_text(value.get("token_id_display_ru") or "требуется выбор"),
        "token_id_display_en": clean_text(value.get("token_id_display_en") or "selection required"),
        "account_checked": value.get("account_checked") is True,
        "account_readonly_ok": value.get("account_readonly_ok") is True,
        "account_display_ru": clean_text(value.get("account_display_ru") or "не проверен"),
        "account_display_en": clean_text(value.get("account_display_en") or "not checked"),
        "signature_contract_ready": value.get("signature_contract_ready") is True,
        "signature_display_ru": clean_text(value.get("signature_display_ru") or "не выполнялась"),
        "signature_display_en": clean_text(value.get("signature_display_en") or "not run"),
        "order_submission_display_ru": clean_text(value.get("order_submission_display_ru") or "выключена"),
        "order_submission_display_en": clean_text(value.get("order_submission_display_en") or "disabled"),
        "live_display_ru": clean_text(value.get("live_display_ru") or "выключен"),
        "live_display_en": clean_text(value.get("live_display_en") or "disabled"),
        "status_text_ru": clean_text(value.get("status_text_ru")),
        "status_text_en": clean_text(value.get("status_text_en")),
        "raw_token_id_exposed": False,
        "raw_account_values_exposed": False,
        "telegram_authenticated_call_performed": False,
        "next_operator_action": clean_text(value.get("next_operator_action")),
        "ready_for_future_live_enablement": False,
        "signing_available": False,
        "wallet_available": False,
        "operator_approved": False,
        "approval_packet_created": value.get("approval_packet_created") is True,
        "candidate_is_executable": False,
        "source_intent_path": clean_text(value.get("source_intent_path")),
        "source_signer_boundary_path": clean_text(value.get("source_signer_boundary_path")),
        "hard_limits_passed": value.get("hard_limits_passed") is True,
        "hard_limits_summary": {},
        "submission_status": {
            "status": "blocked",
            "signing_blocked": True,
            "signed_payload_unavailable": True,
            "order_submission_blocked": True,
            "wallet_connection_blocked": True,
            "live_execution_blocked": True,
        },
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "blocker_count": _int_or_zero(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": _clean_list(top_blockers),
        "review_only": True,
        "execution_enabling": False,
    }
    summary.update(telegram_console_safety_state())
    for field in FORCED_FALSE_SAFETY_FLAGS:
        summary[field] = False
    return summary


def _tiny_order_review_from_artifacts(
    *,
    artifact_root: Path,
    latest_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    paths = _tiny_order_scaffold_061_paths(artifact_root)
    candidate = _load_optional_json(paths["candidate"], label="tiny order candidate 061")
    approval = _load_optional_json(paths["approval_packet"], label="manual tiny order approval packet 061")
    hard_limits = _load_optional_json(paths["hard_limits"], label="tiny order hard limits 061")
    submission = _load_optional_json(
        paths["submission_availability"],
        label="tiny order submission availability 061",
    )
    latest = dict(latest_payload or {})
    return {
        "contract_version": TINY_ORDER_REVIEW_061T_STATUS_CONTRACT + ".registry_detail",
        "task_id": TASK_ID_061T,
        "generated_at": generated_at,
        "source_flow_id": TINY_ORDER_SCAFFOLD_061_FLOW_ID,
        "latest_status_path": normalize_path(paths["latest_status"]),
        "tiny_order_candidate_path": normalize_path(paths["candidate"]),
        "approval_packet_path": normalize_path(paths["approval_packet"]),
        "tiny_order_hard_limits_path": normalize_path(paths["hard_limits"]),
        "tiny_order_submission_availability_path": normalize_path(paths["submission_availability"]),
        "tiny_candidate_status": clean_text(candidate.get("status") or latest.get("tiny_candidate") or "not_available"),
        "approval_packet_status": clean_text(approval.get("status") or latest.get("approval_packet") or "not_available"),
        "operator_approved": False,
        "candidate_is_executable": False,
        "candidate_summary": {
            "available": bool(candidate),
            "status": clean_text(candidate.get("status") or latest.get("tiny_candidate") or "not_available"),
            "candidate_outcome": clean_text(candidate.get("candidate_outcome") or latest.get("candidate_outcome")),
            "candidate_side": clean_text(candidate.get("candidate_side") or latest.get("candidate_side")),
            "candidate_limit_price": candidate.get("candidate_limit_price", latest.get("candidate_limit_price")),
            "candidate_size": candidate.get("candidate_size", latest.get("candidate_size")),
            "candidate_notional": candidate.get("candidate_notional", latest.get("candidate_notional")),
            "candidate_is_executable": False,
        },
        "approval_packet_summary": {
            "available": bool(approval),
            "status": clean_text(approval.get("status") or latest.get("approval_packet") or "not_available"),
            "approval_packet_created": approval.get("approval_packet_created") is True
            or latest.get("approval_packet_created") is True,
            "approval_required": True,
            "operator_approved": False,
            "candidate_is_executable": False,
            "operator_must_not_execute_from_packet": True,
        },
        "hard_limits_summary": {
            "available": bool(hard_limits),
            "status": clean_text(hard_limits.get("status") or "not_available"),
            "hard_limits_passed": hard_limits.get("hard_limits_passed") is True
            or latest.get("hard_limits_passed") is True,
            "max_notional": hard_limits.get("max_notional", latest.get("max_notional")),
            "max_size": hard_limits.get("max_size", latest.get("max_size")),
            "max_price": hard_limits.get("max_price", latest.get("max_price")),
            "operator_summary": clean_text(hard_limits.get("operator_summary")),
        },
        "submission_status": {
            "available": bool(submission),
            "status": clean_text(submission.get("status") or "blocked"),
            "signing_blocked": True,
            "signed_payload_unavailable": True,
            "order_submission_blocked": True,
            "order_cancellation_blocked": True,
            "wallet_connection_blocked": True,
            "live_execution_blocked": True,
            "operator_summary": clean_text(submission.get("operator_summary")),
        },
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "review_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def _tiny_order_review_status_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(review or {})
    hard_limits = dict(value.get("hard_limits_summary", {}))
    submission = dict(value.get("submission_status", {}))
    return {
        "tiny_candidate": clean_text(value.get("tiny_candidate_status") or "not_available"),
        "tiny_candidate_status": clean_text(value.get("tiny_candidate_status") or "not_available"),
        "approval_packet": clean_text(value.get("approval_packet_status") or "not_available"),
        "approval_packet_status": clean_text(value.get("approval_packet_status") or "not_available"),
        "approval_packet_path": clean_text(value.get("approval_packet_path")),
        "manual_tiny_order_approval_packet_path": clean_text(value.get("approval_packet_path")),
        "tiny_order_candidate_path": clean_text(value.get("tiny_order_candidate_path")),
        "tiny_order_hard_limits_path": clean_text(value.get("tiny_order_hard_limits_path")),
        "tiny_order_submission_availability_path": clean_text(value.get("tiny_order_submission_availability_path")),
        "operator_approved": False,
        "candidate_is_executable": False,
        "hard_limits_summary": hard_limits,
        "hard_limits_passed": hard_limits.get("hard_limits_passed") is True,
        "submission_status": submission,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
    }


def _tiny_order_scaffold_061_paths(artifact_root: Path) -> dict[str, Path]:
    return {
        key: _first_existing_path(_candidate_tiny_order_scaffold_061_paths(filename, artifact_root))
        or _candidate_tiny_order_scaffold_061_paths(filename, artifact_root)[0]
        for key, filename in TINY_ORDER_SCAFFOLD_061_ARTIFACT_FILENAMES.items()
    }


def _candidate_tiny_order_scaffold_061_paths(filename: str, artifact_root: Path) -> tuple[Path, ...]:
    paths = [
        artifact_root / TINY_ORDER_SCAFFOLD_061_ARTIFACT_DIR_NAME / filename,
    ]
    if artifact_root.name == TINY_ORDER_SCAFFOLD_061_ARTIFACT_DIR_NAME:
        paths.append(artifact_root / filename)
    paths.append(
        artifact_root
        / "authenticated_clob_preflight_057"
        / TINY_ORDER_SCAFFOLD_061_ARTIFACT_DIR_NAME
        / filename
    )
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(path)
    return tuple(unique)


def _pre_live_gate_review_from_artifacts(
    *,
    artifact_root: Path,
    latest_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    paths = _pre_live_tiny_order_gate_062p_paths(artifact_root)
    checklist = _load_optional_json(paths["checklist"], label="pre-live tiny order checklist 062P")
    blockers = _load_optional_json(paths["blockers"], label="pre-live tiny order blockers 062P")
    readiness = _load_optional_json(paths["readiness_summary"], label="pre-live tiny order readiness summary 062P")
    latest = dict(latest_payload or {})
    return {
        "contract_version": PRE_LIVE_GATE_REVIEW_062T_STATUS_CONTRACT + ".registry_detail",
        "task_id": TASK_ID_062T,
        "generated_at": generated_at,
        "source_flow_id": PRE_LIVE_TINY_ORDER_GATE_062P_FLOW_ID,
        "latest_status_path": normalize_path(paths["latest_status"]),
        "checklist_path": normalize_path(paths["checklist"]),
        "blockers_path": normalize_path(paths["blockers"]),
        "readiness_summary_path": normalize_path(paths["readiness_summary"]),
        "operator_markdown_path": normalize_path(paths["operator_md"]),
        "operator_markdown_available": paths["operator_md"].exists(),
        "source_status": clean_text(latest.get("status") or "not_available"),
        "checklist_summary": {
            "available": bool(checklist),
            "status": clean_text(checklist.get("status") or latest.get("status") or "not_available"),
            "checklist_item_count": len(checklist.get("checklist_items", []))
            if isinstance(checklist.get("checklist_items"), list)
            else 0,
            "tiny_candidate_present": checklist.get("tiny_candidate_present") is True
            or latest.get("tiny_candidate_present") is True,
            "approval_packet_present": checklist.get("approval_packet_present") is True
            or latest.get("approval_packet_present") is True,
            "hard_limits_passed": checklist.get("hard_limits_passed") is True
            or latest.get("hard_limits_passed") is True,
            "market_whitelisted": checklist.get("market_whitelisted") is True
            or latest.get("market_whitelisted") is True,
            "operator_approved": False,
            "candidate_is_executable": False,
        },
        "blockers_summary": {
            "available": bool(blockers),
            "status": clean_text(blockers.get("status") or "unresolved_blockers_present"),
            "blocker_count": _int_or_zero(blockers.get("blocker_count"), latest.get("blocker_count")),
            "resolved_blocker_count": 0,
            "top_blocker_reasons": _clean_list(
                blockers.get("top_blocker_reasons") or latest.get("top_blocker_reasons")
            )[:10],
        },
        "readiness_summary": {
            "available": bool(readiness),
            "status": clean_text(readiness.get("readiness_status") or "blocked"),
            "ready_for_future_live_enablement": False,
            "allowed_for_live": False,
            "next_operator_action": clean_text(
                readiness.get("next_operator_action") or latest.get("next_operator_action")
            ),
            "operator_summary": clean_text(readiness.get("operator_summary")),
        },
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "live_execution_approved": False,
        "ready_for_future_live_enablement": False,
        "allowed_for_live": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def _pre_live_gate_review_status_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(review or {})
    checklist = dict(value.get("checklist_summary", {}))
    blockers = dict(value.get("blockers_summary", {}))
    readiness = dict(value.get("readiness_summary", {}))
    return {
        "pre_live_gate_status": clean_text(value.get("source_status") or "not_available"),
        "checklist_path": clean_text(value.get("checklist_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "readiness_summary_path": clean_text(value.get("readiness_summary_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "operator_markdown_available": value.get("operator_markdown_available") is True,
        "checklist_summary": checklist,
        "blockers_summary": blockers,
        "readiness_summary": readiness,
        "tiny_candidate_present": checklist.get("tiny_candidate_present") is True,
        "approval_packet_present": checklist.get("approval_packet_present") is True,
        "hard_limits_passed": checklist.get("hard_limits_passed") is True,
        "market_whitelisted": checklist.get("market_whitelisted") is True,
        "blocker_count": _int_or_zero(blockers.get("blocker_count")),
        "resolved_blocker_count": 0,
        "top_blocker_reasons": _clean_list(blockers.get("top_blocker_reasons")),
        "readiness_status": clean_text(readiness.get("status") or "blocked"),
        "next_operator_action": clean_text(readiness.get("next_operator_action")),
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "live_execution_approved": False,
        "ready_for_future_live_enablement": False,
        "allowed_for_live": False,
    }


def _pre_live_tiny_order_gate_062p_paths(artifact_root: Path) -> dict[str, Path]:
    return {
        key: _first_existing_path(_candidate_pre_live_tiny_order_gate_062p_paths(filename, artifact_root))
        or _candidate_pre_live_tiny_order_gate_062p_paths(filename, artifact_root)[0]
        for key, filename in PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_FILENAMES.items()
    }


def _candidate_pre_live_tiny_order_gate_062p_paths(filename: str, artifact_root: Path) -> tuple[Path, ...]:
    paths = [
        artifact_root / PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_DIR_NAME / filename,
    ]
    if artifact_root.name == PRE_LIVE_TINY_ORDER_GATE_062P_ARTIFACT_DIR_NAME:
        paths.append(artifact_root / filename)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(path)
    return tuple(unique)


def _supervised_live_enablement_review_from_artifacts(
    *,
    artifact_root: Path,
    latest_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    paths = _supervised_tiny_live_enablement_gate_063_paths(artifact_root)
    checklist = _load_optional_json(paths["operator_checklist"], label="supervised tiny live checklist 063")
    blockers = _load_optional_json(paths["blockers"], label="supervised tiny live blockers 063")
    risk_limits = _load_optional_json(paths["risk_limits"], label="supervised tiny live risk limits 063")
    kill_switch_plan = _load_optional_json(paths["kill_switch_plan"], label="supervised tiny live stop plan 063")
    cancel_plan = _load_optional_json(paths["cancel_plan"], label="supervised tiny live cancel plan 063")
    failure_plan = _load_optional_json(paths["failure_plan"], label="supervised tiny live failure plan 063")
    env_readiness = _load_optional_json(paths["env_readiness"], label="supervised tiny live env readiness 063")
    manual_approval_packet = _load_optional_json(
        paths["manual_approval_packet"],
        label="supervised tiny live manual approval packet 063",
    )
    latest = dict(latest_payload or {})
    blocker_rows = [dict(row) for row in blockers.get("blockers", []) if isinstance(row, Mapping)]
    top_blockers = blockers.get("top_blocker_reasons") or latest.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in blocker_rows
            if clean_text(row.get("reason"))
        ][:10]
    return {
        "contract_version": SUPERVISED_LIVE_ENABLEMENT_REVIEW_063T_STATUS_CONTRACT + ".registry_detail",
        "task_id": TASK_ID_063T,
        "generated_at": generated_at,
        "source_flow_id": SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_FLOW_ID,
        "latest_status_path": normalize_path(paths["latest_status"]),
        "operator_checklist_path": normalize_path(paths["operator_checklist"]),
        "blockers_path": normalize_path(paths["blockers"]),
        "risk_limits_path": normalize_path(paths["risk_limits"]),
        "kill_switch_plan_path": normalize_path(paths["kill_switch_plan"]),
        "cancel_plan_path": normalize_path(paths["cancel_plan"]),
        "failure_plan_path": normalize_path(paths["failure_plan"]),
        "env_readiness_path": normalize_path(paths["env_readiness"]),
        "manual_approval_packet_path": normalize_path(paths["manual_approval_packet"]),
        "operator_markdown_path": normalize_path(paths["operator_md"]),
        "operator_markdown_available": paths["operator_md"].exists(),
        "source_status": clean_text(latest.get("status") or "not_available"),
        "operator_checklist_summary": {
            "available": bool(checklist),
            "status": clean_text(checklist.get("status") or latest.get("status") or "not_available"),
            "checklist_item_count": len(checklist.get("checklist_items", []))
            if isinstance(checklist.get("checklist_items"), list)
            else 0,
            "risk_limits_present": checklist.get("risk_limits_present") is True,
            "kill_switch_plan_present": checklist.get("kill_switch_plan_present") is True,
            "cancel_plan_present": checklist.get("cancel_plan_present") is True,
            "failure_plan_present": checklist.get("failure_plan_present") is True,
            "env_readiness_present": checklist.get("env_readiness_present") is True,
            "manual_approval_packet_present": checklist.get("manual_approval_packet_present") is True,
            "blocker_matrix_present": checklist.get("blocker_matrix_present") is True,
            "operator_approved": False,
            "candidate_is_executable": False,
        },
        "blockers_summary": {
            "available": bool(blockers),
            "status": clean_text(blockers.get("status") or "unresolved_blockers_present"),
            "blocker_count": _int_or_zero(blockers.get("blocker_count"), latest.get("blocker_count"), len(blocker_rows)),
            "resolved_blocker_count": 0,
            "unresolved_blocker_ids": _clean_list(blockers.get("unresolved_blocker_ids") or latest.get("unresolved_blocker_ids")),
            "top_blocker_reasons": _clean_list(top_blockers)[:10],
        },
        "risk_limits_summary": {
            "available": bool(risk_limits),
            "status": clean_text(risk_limits.get("status") or "preparation_constraints_only"),
            "max_order_notional_usd": risk_limits.get("max_order_notional_usd"),
            "max_daily_notional_usd": risk_limits.get("max_daily_notional_usd"),
            "max_orders_per_day": risk_limits.get("max_orders_per_day"),
            "max_market_count": risk_limits.get("max_market_count"),
            "allowed_market": clean_text(risk_limits.get("allowed_market") or "BTC"),
            "allowed_strategy": clean_text(risk_limits.get("allowed_strategy") or "tiny-momentum"),
            "limits_are_executable": False,
        },
        "kill_switch_plan_summary": _review_plan_summary(kill_switch_plan),
        "cancel_plan_summary": _review_plan_summary(cancel_plan),
        "failure_plan_summary": _review_plan_summary(failure_plan),
        "env_readiness_summary": {
            "available": bool(env_readiness),
            "status": clean_text(env_readiness.get("readiness_status") or "blocked"),
            "marker_count": _int_or_zero(env_readiness.get("marker_count")),
            "missing_marker_count": _int_or_zero(
                env_readiness.get("missing_marker_count"),
                latest.get("missing_env_marker_count"),
            ),
            "all_required_markers_present": env_readiness.get("all_required_markers_present") is True,
            "presence_only": True,
            "values_redacted": True,
            "raw_values_emitted": False,
        },
        "manual_approval_packet_summary": {
            "available": bool(manual_approval_packet),
            "approval_required": True,
            "approval_scope": clean_text(
                manual_approval_packet.get("approval_scope") or "first_tiny_live_order_preparation_only"
            ),
            "operator_approved": False,
            "approval_packet_is_executable": False,
            "this_packet_is_not_executable": True,
            "later_live_enabling_task_required": True,
            "no_order_can_be_submitted_from_this_packet": True,
        },
        "blocker_count": _int_or_zero(blockers.get("blocker_count"), latest.get("blocker_count"), len(blocker_rows)),
        "resolved_blocker_count": 0,
        "missing_env_marker_count": _int_or_zero(
            env_readiness.get("missing_marker_count"),
            latest.get("missing_env_marker_count"),
        ),
        "top_blocker_reasons": _clean_list(top_blockers)[:10],
        "operator_approved": False,
        "candidate_is_executable": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def _supervised_live_enablement_review_status_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(review or {})
    checklist = dict(value.get("operator_checklist_summary", {}))
    blockers = dict(value.get("blockers_summary", {}))
    risk_limits = dict(value.get("risk_limits_summary", {}))
    kill_switch_plan = dict(value.get("kill_switch_plan_summary", {}))
    cancel_plan = dict(value.get("cancel_plan_summary", {}))
    failure_plan = dict(value.get("failure_plan_summary", {}))
    env_readiness = dict(value.get("env_readiness_summary", {}))
    manual_approval_packet = dict(value.get("manual_approval_packet_summary", {}))
    return {
        "supervised_live_enablement_status": clean_text(value.get("source_status") or "not_available"),
        "operator_checklist_path": clean_text(value.get("operator_checklist_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "risk_limits_path": clean_text(value.get("risk_limits_path")),
        "kill_switch_plan_path": clean_text(value.get("kill_switch_plan_path")),
        "cancel_plan_path": clean_text(value.get("cancel_plan_path")),
        "failure_plan_path": clean_text(value.get("failure_plan_path")),
        "env_readiness_path": clean_text(value.get("env_readiness_path")),
        "manual_approval_packet_path": clean_text(value.get("manual_approval_packet_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "operator_markdown_available": value.get("operator_markdown_available") is True,
        "operator_checklist_summary": checklist,
        "blockers_summary": blockers,
        "risk_limits_summary": risk_limits,
        "kill_switch_plan_summary": kill_switch_plan,
        "cancel_plan_summary": cancel_plan,
        "failure_plan_summary": failure_plan,
        "env_readiness_summary": env_readiness,
        "manual_approval_packet_summary": manual_approval_packet,
        "blocker_count": _int_or_zero(blockers.get("blocker_count"), value.get("blocker_count")),
        "resolved_blocker_count": 0,
        "missing_env_marker_count": _int_or_zero(
            env_readiness.get("missing_marker_count"),
            value.get("missing_env_marker_count"),
        ),
        "top_blocker_reasons": _clean_list(blockers.get("top_blocker_reasons") or value.get("top_blocker_reasons")),
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _supervised_tiny_live_enablement_gate_063_paths(artifact_root: Path) -> dict[str, Path]:
    return {
        key: _first_existing_path(_candidate_supervised_tiny_live_enablement_gate_063_paths(filename, artifact_root))
        or _candidate_supervised_tiny_live_enablement_gate_063_paths(filename, artifact_root)[0]
        for key, filename in SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_FILENAMES.items()
    }


def _candidate_supervised_tiny_live_enablement_gate_063_paths(
    filename: str,
    artifact_root: Path,
) -> tuple[Path, ...]:
    paths = [
        artifact_root / SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_DIR_NAME / filename,
    ]
    if artifact_root.name == SUPERVISED_TINY_LIVE_ENABLEMENT_GATE_063_ARTIFACT_DIR_NAME:
        paths.append(artifact_root / filename)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(path)
    return tuple(unique)


def _credentials_readiness_review_from_artifacts(
    *,
    artifact_root: Path,
    latest_payload: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    paths = _explicit_live_credentials_readiness_gate_064_paths(artifact_root)
    marker_presence = _load_optional_json(paths["marker_presence"], label="explicit live credentials marker presence 064")
    blockers = _load_optional_json(paths["blockers"], label="explicit live credentials blockers 064")
    operator_boundary = _load_optional_json(
        paths["operator_approval_boundary"],
        label="explicit live credentials operator approval boundary 064",
    )
    safety_policy = _load_optional_json(
        paths["safety_policy_validation"],
        label="explicit live credentials safety policy validation 064",
    )
    readiness = _load_optional_json(paths["readiness_summary"], label="explicit live credentials readiness summary 064")
    latest = dict(latest_payload or {})
    marker_rows = _safe_marker_presence_rows(marker_presence)
    required_rows = [row for row in marker_rows if row.get("required_for_redacted_review") is True]
    missing_required = _clean_list(marker_presence.get("missing_required_markers")) or [
        clean_text(row.get("marker_label")) for row in required_rows if row.get("present") is not True
    ]
    blocker_rows = _safe_blocker_rows(blockers)
    missing_marker_blockers = [
        row for row in blocker_rows if clean_text(row.get("blocker_id")).startswith("missing_required_marker:")
    ]
    top_blockers = blockers.get("top_blocker_reasons") or latest.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [row["reason"] for row in blocker_rows if clean_text(row.get("reason"))][:10]
    marker_count = _int_or_zero(marker_presence.get("marker_count"), len(marker_rows))
    required_marker_count = _int_or_zero(marker_presence.get("required_marker_count"), len(required_rows))
    missing_required_marker_count = _int_or_zero(
        marker_presence.get("missing_required_marker_count"),
        latest.get("missing_required_marker_count"),
        len(missing_required),
    )
    present_execution_flag_count = _int_or_zero(
        marker_presence.get("present_execution_flag_count"),
        latest.get("present_execution_flag_count"),
    )
    return {
        "contract_version": CREDENTIALS_READINESS_REVIEW_064T_STATUS_CONTRACT + ".registry_detail",
        "task_id": TASK_ID_064T,
        "generated_at": generated_at,
        "source_flow_id": EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_FLOW_ID,
        "latest_status_path": normalize_path(paths["latest_status"]),
        "marker_presence_path": normalize_path(paths["marker_presence"]),
        "operator_approval_boundary_path": normalize_path(paths["operator_approval_boundary"]),
        "safety_policy_validation_path": normalize_path(paths["safety_policy_validation"]),
        "blockers_path": normalize_path(paths["blockers"]),
        "operator_checklist_path": normalize_path(paths["operator_checklist"]),
        "readiness_summary_path": normalize_path(paths["readiness_summary"]),
        "operator_markdown_path": normalize_path(paths["operator_md"]),
        "operator_markdown_available": paths["operator_md"].exists(),
        "source_status": clean_text(latest.get("status") or readiness.get("readiness_status") or "not_available"),
        "readiness_status": clean_text(readiness.get("readiness_status") or latest.get("readiness_status") or "blocked"),
        "redacted_presence_review_ready": readiness.get("redacted_presence_review_ready") is True
        or latest.get("redacted_presence_review_ready") is True,
        "marker_summary": {
            "available": bool(marker_presence),
            "marker_count": marker_count,
            "required_marker_count": required_marker_count,
            "present_marker_count": _int_or_zero(marker_presence.get("present_marker_count")),
            "missing_required_marker_count": missing_required_marker_count,
            "present_execution_flag_count": present_execution_flag_count,
            "all_required_markers_present": marker_presence.get("all_required_markers_present") is True,
            "execution_flags_absent": marker_presence.get("execution_flags_absent") is True,
            "presence_only": True,
            "presence_booleans_only": True,
            "values_redacted": True,
            "raw_values_emitted": False,
        },
        "required_marker_presence": required_rows,
        "missing_required_markers": missing_required,
        "missing_marker_blockers": missing_marker_blockers,
        "blockers_summary": {
            "available": bool(blockers),
            "status": clean_text(blockers.get("status") or "unresolved_blockers_present"),
            "blocker_count": _int_or_zero(blockers.get("blocker_count"), latest.get("blocker_count"), len(blocker_rows)),
            "resolved_blocker_count": 0,
            "top_blocker_reasons": _clean_list(top_blockers)[:10],
        },
        "operator_approval_boundary_summary": {
            "available": bool(operator_boundary),
            "operator_review_marker_present": operator_boundary.get("operator_review_marker_present") is True,
            "dual_control_review_marker_present": operator_boundary.get("dual_control_review_marker_present") is True,
            "operator_approved": False,
            "allowed_for_live": False,
            "operator_review_does_not_enable_live": True,
            "separate_live_enabling_task_required": True,
            "separate_wallet_signing_task_required": True,
            "separate_authenticated_request_task_required": True,
            "separate_order_submission_or_cancel_task_required": True,
        },
        "safety_policy_validation_summary": {
            "available": bool(safety_policy),
            "valid": safety_policy.get("valid") is True,
            "status": clean_text(safety_policy.get("status") or "not_available"),
            "presence_check_count": _int_or_zero(safety_policy.get("presence_check_count")),
            "forbidden_field_count": _int_or_zero(safety_policy.get("forbidden_field_count")),
            "explicit_allowlist_only": safety_policy.get("explicit_allowlist_only") is True,
            "presence_booleans_only": safety_policy.get("presence_booleans_only") is True,
            "broad_environment_scan_performed": False,
            "credential_values_read": False,
            "credential_values_serialized": False,
            "credential_values_printed": False,
            "credential_values_stored": False,
            "credential_values_hashed": False,
            "credential_values_transformed": False,
        },
        "blocker_count": _int_or_zero(blockers.get("blocker_count"), latest.get("blocker_count"), len(blocker_rows)),
        "resolved_blocker_count": 0,
        "missing_required_marker_count": missing_required_marker_count,
        "present_execution_flag_count": present_execution_flag_count,
        "allowed_for_live": False,
        "live_ready": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "presence_only": True,
        "values_never_shown": True,
        "redacted_labels_only": True,
        "credential_values_read": False,
        "credentials_values_read": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_console_safety_state(),
    }


def _credentials_readiness_review_status_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(review or {})
    marker_summary = dict(value.get("marker_summary", {}))
    blockers_summary = dict(value.get("blockers_summary", {}))
    operator_boundary = dict(value.get("operator_approval_boundary_summary", {}))
    safety_policy = dict(value.get("safety_policy_validation_summary", {}))
    return {
        "credentials_readiness_status": clean_text(value.get("source_status") or "not_available"),
        "readiness_status": clean_text(value.get("readiness_status") or "blocked"),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "marker_presence_path": clean_text(value.get("marker_presence_path")),
        "operator_approval_boundary_path": clean_text(value.get("operator_approval_boundary_path")),
        "safety_policy_validation_path": clean_text(value.get("safety_policy_validation_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "operator_checklist_path": clean_text(value.get("operator_checklist_path")),
        "readiness_summary_path": clean_text(value.get("readiness_summary_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "operator_markdown_available": value.get("operator_markdown_available") is True,
        "marker_summary": marker_summary,
        "required_marker_presence": [
            dict(row) for row in value.get("required_marker_presence", []) if isinstance(row, Mapping)
        ],
        "missing_required_markers": _clean_list(value.get("missing_required_markers")),
        "missing_marker_blockers": [
            dict(row) for row in value.get("missing_marker_blockers", []) if isinstance(row, Mapping)
        ],
        "operator_approval_boundary_summary": operator_boundary,
        "safety_policy_validation_summary": safety_policy,
        "blockers_summary": blockers_summary,
        "blocker_count": _int_or_zero(blockers_summary.get("blocker_count"), value.get("blocker_count")),
        "resolved_blocker_count": 0,
        "marker_count": _int_or_zero(marker_summary.get("marker_count")),
        "required_marker_count": _int_or_zero(marker_summary.get("required_marker_count")),
        "missing_required_marker_count": _int_or_zero(
            marker_summary.get("missing_required_marker_count"),
            value.get("missing_required_marker_count"),
        ),
        "present_execution_flag_count": _int_or_zero(
            marker_summary.get("present_execution_flag_count"),
            value.get("present_execution_flag_count"),
        ),
        "top_blocker_reasons": _clean_list(blockers_summary.get("top_blocker_reasons")),
        "redacted_presence_review_ready": value.get("redacted_presence_review_ready") is True,
        "presence_only": True,
        "values_never_shown": True,
        "redacted_labels_only": True,
        "raw_values_emitted": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "live_ready": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
    }


def _explicit_live_credentials_readiness_gate_064_paths(artifact_root: Path) -> dict[str, Path]:
    return {
        key: _first_existing_path(_candidate_explicit_live_credentials_readiness_gate_064_paths(filename, artifact_root))
        or _candidate_explicit_live_credentials_readiness_gate_064_paths(filename, artifact_root)[0]
        for key, filename in EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_FILENAMES.items()
    }


def _candidate_explicit_live_credentials_readiness_gate_064_paths(
    filename: str,
    artifact_root: Path,
) -> tuple[Path, ...]:
    paths = [
        artifact_root / EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_DIR_NAME / filename,
    ]
    if artifact_root.name == EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_064_ARTIFACT_DIR_NAME:
        paths.append(artifact_root / filename)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(path)
    return tuple(unique)


def _safe_marker_presence_rows(marker_presence: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_rows = marker_presence.get("marker_checks") if isinstance(marker_presence.get("marker_checks"), list) else []
    for row in source_rows:
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "marker_label": clean_text(row.get("marker_label")),
                "marker_group": clean_text(row.get("marker_group")),
                "required_for_redacted_review": row.get("required_for_redacted_review") is True,
                "present": row.get("present") is True,
                "result_category": clean_text(row.get("result_category") or "missing"),
                "presence_boolean_only": True,
                "value_redacted": True,
                "value_read": False,
                "raw_value_emitted": False,
            }
        )
    return rows


def _safe_blocker_rows(blockers: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_rows = blockers.get("blockers") if isinstance(blockers.get("blockers"), list) else []
    for row in source_rows:
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "blocker_id": clean_text(row.get("blocker_id")),
                "blocker_category": clean_text(row.get("blocker_category")),
                "severity": clean_text(row.get("severity") or "critical"),
                "resolution_status": "unresolved",
                "reason": clean_text(row.get("reason")),
                "blocks_live_execution": True,
            }
        )
    return rows


def _review_plan_summary(plan: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(plan or {})
    return {
        "available": bool(value),
        "status": clean_text(value.get("status") or "descriptive_only"),
        "operator_confirmation_required": value.get("operator_confirmation_required") is True,
        "plan_is_descriptive_only": value.get("plan_is_descriptive_only") is True or bool(value),
        "plan_is_executable": False,
        "operator_summary": clean_text(value.get("operator_summary")),
    }


def _load_optional_json(path: Path, *, label: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return load_json_object(path, label=label)
    except Exception:
        return {}


def _action_result(
    *,
    action_id: str,
    status: str,
    returncode: int,
    stdout: str,
    stderr: str,
    command: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": ACTION_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "action_id": clean_text(action_id),
        "status": clean_text(status),
        "returncode": returncode,
        "command": list(command),
        "stdout_excerpt": _redact_sensitive_text(stdout)[:2000],
        "stderr_excerpt": _redact_sensitive_text(stderr)[:2000],
        "review_only": True,
        "dry_run_or_preflight_only": True,
        "live_trading_available": False,
        **telegram_console_safety_state(),
    }


def _redact_sensitive_text(value: str) -> str:
    text = clean_text(value)
    text = _PRIVATE_KEY_RE.sub("<redacted-private-key>", text)
    text = _TOKEN_RE.sub("<redacted-token>", text)
    text = _OPENAI_KEY_RE.sub("<redacted-api-key>", text)
    return text


def _available(cards_by_flow: Mapping[str, Mapping[str, Any]], flow_id: str) -> bool:
    return dict(cards_by_flow.get(flow_id, {})).get("available") is True


def _all_available(cards_by_flow: Mapping[str, Mapping[str, Any]], flow_ids: Sequence[str]) -> bool:
    return all(_available(cards_by_flow, flow_id) for flow_id in flow_ids)


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values] if clean_text(values) else []
    try:
        return [clean_text(item) for item in values if clean_text(item)]
    except TypeError:
        return []


def _int_or_zero(*values: Any) -> int:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Telegram PMBOT operator console 060T status registry.")
    parser.add_argument("--artifact-root", default="", help="Optional PMBOT artifact root.")
    parser.add_argument("--generated-at", default=GENERATED_AT, help="Timestamp to record in generated artifacts.")
    parser.add_argument("--write-artifacts", action="store_true", help="Write 060T registry/result artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a concise status line.")
    args = parser.parse_args(argv)
    artifact_root = Path(args.artifact_root) if args.artifact_root else None
    if args.write_artifacts:
        result = write_telegram_operator_console_artifacts(artifact_root=artifact_root, generated_at=args.generated_at)
        payload = result["latest_status"]
    else:
        payload = build_telegram_status_registry_snapshot(artifact_root=artifact_root, generated_at=args.generated_at)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        readiness = dict(payload.get("readiness_summary", payload))
        print(
            "PMBOT Telegram operator console 060T: review-only; "
            f"readiness={readiness.get('readiness_percent', 'not_available')}%; live execution blocked."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

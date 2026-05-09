from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from .files import validate_task_id
from .schema import default_packet

PMBOT_TEMPLATE_SCHEMA_VERSION = "pmbot_task_template.v1"
PMBOT_PROJECT = "PMBOT"
WEATHER_SOURCE_MONITORING_TEMPLATE = "weather-source-monitoring"
WEATHER_OBSERVATION_REFRESH_LEDGER_TEMPLATE = "weather-observation-refresh-ledger"
WEATHER_OUTCOME_RECONCILIATION_STUB_TEMPLATE = "weather-outcome-reconciliation-stub"
WEATHER_OPERATOR_REVIEW_SURFACE_TEMPLATE = "weather-operator-review-surface"
SOURCE_QUALITY_LEDGER_TEMPLATE = "source-quality-ledger"
SOURCE_QUALITY_VALIDATOR_TEMPLATE = "source-quality-validator"
SIMULATED_DECISION_PACKET_SCHEMA_TEMPLATE = "simulated-decision-packet-schema"
SIMULATED_DECISION_VALIDATOR_TEMPLATE = "simulated-decision-validator"
PAPER_ACCOUNTING_LEDGER_TEMPLATE = "paper-accounting-ledger"
LOCAL_OPERATOR_DASHBOARD_SUMMARY_TEMPLATE = "local-operator-dashboard-summary"
READINESS_BLOCKER_MATRIX_TEMPLATE = "readiness-blocker-matrix"
SOURCE_QUALITY_REPORT_SUMMARY_TEMPLATE = "source-quality-report-summary"
SOURCE_QUALITY_REGRESSION_FIXTURE_TEMPLATE = "source-quality-regression-fixture"
SIMULATED_DECISION_AUDIT_LEDGER_TEMPLATE = "simulated-decision-audit-ledger"
SIMULATED_DECISION_REPLAY_SUMMARY_TEMPLATE = "simulated-decision-replay-summary"
PAPER_ACCOUNTING_VALIDATOR_TEMPLATE = "paper-accounting-validator"
PAPER_ACCOUNTING_SESSION_SUMMARY_TEMPLATE = "paper-accounting-session-summary"
CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE = "crypto-market-class-capture"
CRYPTO_OPERATOR_REVIEW_PROTOCOL_TEMPLATE = "crypto-operator-review-protocol"
CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_TEMPLATE = "crypto-paperlive-observation-ledger"
CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_TEMPLATE = "crypto-source-quality-capture-surface"
QUEUE_AND_PAPERLIVE_STATUS_SURFACE_TEMPLATE = "queue-and-paperlive-status-surface"
SOURCE_QUALITY_DASHBOARD_SUMMARY_TEMPLATE = "source-quality-dashboard-summary"
PAPER_ACCOUNTING_DASHBOARD_SUMMARY_TEMPLATE = "paper-accounting-dashboard-summary"
AUTONOMY_GATE_CHECKLIST_TEMPLATE = "autonomy-gate-checklist"
NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_TEMPLATE = "night-batch-postrun-audit-summary"
FORBIDDEN_ACTION_SCAN_TEMPLATE = "forbidden-action-scan"
LOCAL_TO_SUPERVISED_GAP_MATRIX_TEMPLATE = "local-to-supervised-gap-matrix"
NEXT_20_TASK_BACKLOG_GENERATOR_TEMPLATE = "next-20-task-backlog-generator"
MORNING_REVIEW_PACK_TEMPLATE = "morning-review-pack"
NIGHT_BATCH_ACCEPTANCE_REPORT_TEMPLATE = "night-batch-acceptance-report"

SUPPORTED_PMBOT_TEMPLATES = (
    WEATHER_SOURCE_MONITORING_TEMPLATE,
    WEATHER_OBSERVATION_REFRESH_LEDGER_TEMPLATE,
    WEATHER_OUTCOME_RECONCILIATION_STUB_TEMPLATE,
    WEATHER_OPERATOR_REVIEW_SURFACE_TEMPLATE,
    SOURCE_QUALITY_LEDGER_TEMPLATE,
    SOURCE_QUALITY_VALIDATOR_TEMPLATE,
    SIMULATED_DECISION_PACKET_SCHEMA_TEMPLATE,
    SIMULATED_DECISION_VALIDATOR_TEMPLATE,
    PAPER_ACCOUNTING_LEDGER_TEMPLATE,
    LOCAL_OPERATOR_DASHBOARD_SUMMARY_TEMPLATE,
    READINESS_BLOCKER_MATRIX_TEMPLATE,
    SOURCE_QUALITY_REPORT_SUMMARY_TEMPLATE,
    SOURCE_QUALITY_REGRESSION_FIXTURE_TEMPLATE,
    SIMULATED_DECISION_AUDIT_LEDGER_TEMPLATE,
    SIMULATED_DECISION_REPLAY_SUMMARY_TEMPLATE,
    PAPER_ACCOUNTING_VALIDATOR_TEMPLATE,
    PAPER_ACCOUNTING_SESSION_SUMMARY_TEMPLATE,
    CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE,
    CRYPTO_OPERATOR_REVIEW_PROTOCOL_TEMPLATE,
    CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_TEMPLATE,
    CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_TEMPLATE,
    QUEUE_AND_PAPERLIVE_STATUS_SURFACE_TEMPLATE,
    SOURCE_QUALITY_DASHBOARD_SUMMARY_TEMPLATE,
    PAPER_ACCOUNTING_DASHBOARD_SUMMARY_TEMPLATE,
    AUTONOMY_GATE_CHECKLIST_TEMPLATE,
    NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_TEMPLATE,
    FORBIDDEN_ACTION_SCAN_TEMPLATE,
    LOCAL_TO_SUPERVISED_GAP_MATRIX_TEMPLATE,
    NEXT_20_TASK_BACKLOG_GENERATOR_TEMPLATE,
    MORNING_REVIEW_PACK_TEMPLATE,
    NIGHT_BATCH_ACCEPTANCE_REPORT_TEMPLATE,
)

WEATHER_SOURCE_MONITORING_TASK_ID = (
    "PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE"
)

PMBOT_REQUIRED_FORBIDDEN_ACTIONS = (
    "No wallet/private keys",
    "No orders",
    "No trading endpoints",
    "No OpenRouter calls",
    "No Polymarket API calls",
    "No authenticated endpoints",
    "No runtime/dispatcher/run_codex changes",
    "No background worker",
    "No scheduler execution",
    "No browser automation",
    "No destructive commands",
    "No git add .",
    "No git add -A",
    "No git add --all",
    "No force push",
    "No probability / EV / edge / confidence / side selection",
    "No buy/sell/hold/enter/exit recommendations",
    "No market-action guidance",
)

PMBOT_WEATHER_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests/test_weather_source_monitoring_plan_runner.py",
)

PMBOT_ALLOWED_ACTIONS = (
    "Inspect local files under the allowed paths before editing.",
    "Add deterministic local code, tests, fixtures, or docs only for weather outcome/source monitoring plan-runner support.",
    "Use local fixtures, local sample data, and operator-reviewed artifacts only.",
    "Run only the listed local validation commands.",
    "Return a strict result JSON packet for operator review.",
)

PMBOT_WEATHER_ALLOWED_PATHS = (
    "pm_bot/weather/",
    "pm_bot/tests/",
    "tests/",
    "docs/",
)

PMBOT_WEATHER_FORBIDDEN_PATHS = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)

PMBOT_NIGHT_BATCH_TASKS: tuple[dict[str, Any], ...] = (
    {
        "task_id": "PMBOT-PAPERLIVE-010W-003-WEATHER-OBSERVATION-REFRESH-LEDGER-NO-TRADE",
        "template": WEATHER_OBSERVATION_REFRESH_LEDGER_TEMPLATE,
        "title": "PMBOT weather observation refresh ledger",
        "objective": "Add deterministic local support for refreshing weather observation ledger records.",
        "summary": "Prepare local PMBOT weather observation ledger refresh support using fixtures and operator-readable artifacts.",
        "allowed_paths": ("pm_bot/weather/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Weather observation ledger refresh code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPERLIVE-010W-004-WEATHER-OUTCOME-RECONCILIATION-PLACEHOLDER-NO-TRADE",
        "template": WEATHER_OUTCOME_RECONCILIATION_STUB_TEMPLATE,
        "title": "PMBOT weather outcome reconciliation stub",
        "objective": "Add deterministic local reconciliation stub artifacts for weather outcomes.",
        "summary": "Prepare a local PMBOT weather outcome reconciliation stub with clear operator review records.",
        "allowed_paths": ("pm_bot/weather/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Weather outcome reconciliation stub code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPERLIVE-010W-005-WEATHER-OPERATOR-REVIEW-SURFACE-UPDATE-NO-TRADE",
        "template": WEATHER_OPERATOR_REVIEW_SURFACE_TEMPLATE,
        "title": "PMBOT weather operator review surface update",
        "objective": "Improve deterministic local operator review artifacts for weather workflows.",
        "summary": "Update local PMBOT weather review surfaces so operators can inspect ledger and reconciliation records.",
        "allowed_paths": ("pm_bot/weather/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Weather operator review surface code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SOURCE-LEDGER-001-UNIFIED-SOURCE-QUALITY-LEDGER-LOCAL-ONLY",
        "template": SOURCE_QUALITY_LEDGER_TEMPLATE,
        "title": "PMBOT unified source quality ledger",
        "objective": "Add a deterministic local source quality ledger artifact.",
        "summary": "Prepare a unified local source quality ledger for PMBOT source review workflows.",
        "allowed_paths": ("pm_bot/source_quality/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Source quality ledger code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SOURCE-LEDGER-002-SOURCE-QUALITY-VALIDATOR-LOCAL-ONLY",
        "template": SOURCE_QUALITY_VALIDATOR_TEMPLATE,
        "title": "PMBOT source quality validator",
        "objective": "Add deterministic local validation for source quality ledger records.",
        "summary": "Prepare local validation support for PMBOT source quality ledger artifacts.",
        "allowed_paths": ("pm_bot/source_quality/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Source quality validator code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPERLIVE-DECISION-001-SIMULATED-DECISION-PACKET-SCHEMA-NO-RECOMMENDATIONS",
        "template": SIMULATED_DECISION_PACKET_SCHEMA_TEMPLATE,
        "title": "PMBOT simulated decision packet schema",
        "objective": "Add a deterministic local schema for simulated decision packets without guidance fields.",
        "summary": "Prepare a local PMBOT simulated decision packet schema for offline recordkeeping only.",
        "allowed_paths": ("pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Simulated decision packet schema code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPERLIVE-DECISION-002-SIMULATED-DECISION-VALIDATOR-NO-RECOMMENDATIONS",
        "template": SIMULATED_DECISION_VALIDATOR_TEMPLATE,
        "title": "PMBOT simulated decision validator",
        "objective": "Add deterministic local validation for simulated decision packets without guidance fields.",
        "summary": "Prepare local PMBOT validation support for simulated decision packet records.",
        "allowed_paths": ("pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Simulated decision validator code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPER-ACCOUNTING-001-PAPER-ONLY-ACCOUNTING-LEDGER-LOCAL-ONLY",
        "template": PAPER_ACCOUNTING_LEDGER_TEMPLATE,
        "title": "PMBOT paper accounting ledger",
        "objective": "Add deterministic local paper accounting ledger artifacts.",
        "summary": "Prepare a local PMBOT accounting ledger for offline paper records and operator review.",
        "allowed_paths": ("pm_bot/paper_accounting/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Paper accounting ledger code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-DASHBOARD-001-LOCAL-OPERATOR-DASHBOARD-SUMMARY",
        "template": LOCAL_OPERATOR_DASHBOARD_SUMMARY_TEMPLATE,
        "title": "PMBOT local operator dashboard summary",
        "objective": "Add deterministic local dashboard summary artifacts for operator review.",
        "summary": "Prepare a local PMBOT dashboard summary for queue, ledger, and validation status records.",
        "allowed_paths": ("pm_bot/dashboard/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Local dashboard summary code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-ROADMAP-001-REAL-WALLET-READINESS-BLOCKER-MATRIX",
        "template": READINESS_BLOCKER_MATRIX_TEMPLATE,
        "title": "PMBOT readiness blocker matrix",
        "objective": "Add a local readiness blocker matrix document for sensitive-access review.",
        "summary": "Prepare a local PMBOT readiness blocker matrix that records unresolved operator approval gates.",
        "allowed_paths": ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Readiness blocker matrix docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY",
        "template": SOURCE_QUALITY_REPORT_SUMMARY_TEMPLATE,
        "title": "PMBOT source quality report summary",
        "objective": "Add a deterministic local source quality report summary artifact.",
        "summary": "Prepare a local PMBOT source quality report summary for operator review.",
        "allowed_paths": ("pm_bot/source_quality/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Source quality report summary code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY",
        "template": SOURCE_QUALITY_REGRESSION_FIXTURE_TEMPLATE,
        "title": "PMBOT source quality regression fixture",
        "objective": "Add a deterministic local source quality regression fixture.",
        "summary": "Prepare a local PMBOT source quality regression fixture for repeatable review.",
        "allowed_paths": ("pm_bot/source_quality/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Source quality regression fixture code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPERLIVE-DECISION-003-SIMULATED-DECISION-AUDIT-LEDGER-NO-RECOMMENDATIONS",
        "template": SIMULATED_DECISION_AUDIT_LEDGER_TEMPLATE,
        "title": "PMBOT simulated decision audit ledger",
        "objective": "Add a deterministic local audit ledger for simulated decision records.",
        "summary": "Prepare a local PMBOT simulated decision audit ledger for record review only.",
        "allowed_paths": ("pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Simulated decision audit ledger code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPERLIVE-DECISION-004-SIMULATED-DECISION-REPLAY-SUMMARY-NO-RECOMMENDATIONS",
        "template": SIMULATED_DECISION_REPLAY_SUMMARY_TEMPLATE,
        "title": "PMBOT simulated decision replay summary",
        "objective": "Add a deterministic local replay summary for simulated decision records.",
        "summary": "Prepare a local PMBOT simulated decision replay summary for record review only.",
        "allowed_paths": ("pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Simulated decision replay summary code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY",
        "template": PAPER_ACCOUNTING_VALIDATOR_TEMPLATE,
        "title": "PMBOT paper accounting validator",
        "objective": "Add deterministic local validation for paper accounting records.",
        "summary": "Prepare local PMBOT paper accounting validation support for operator review.",
        "allowed_paths": ("pm_bot/paper_accounting/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Paper accounting validator code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-PAPER-ACCOUNTING-003-PAPER-ONLY-SESSION-SUMMARY-LOCAL-ONLY",
        "template": PAPER_ACCOUNTING_SESSION_SUMMARY_TEMPLATE,
        "title": "PMBOT paper accounting session summary",
        "objective": "Add a deterministic local session summary for paper accounting records.",
        "summary": "Prepare a local PMBOT paper accounting session summary for operator review.",
        "allowed_paths": ("pm_bot/paper_accounting/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Paper accounting session summary code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY",
        "template": CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE,
        "title": "PMBOT crypto market class capture template",
        "objective": "Add a deterministic local capture template for crypto market class records.",
        "summary": "Prepare a local PMBOT crypto market class capture template for descriptive records.",
        "allowed_paths": ("docs/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Crypto market class capture template docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY",
        "template": CRYPTO_OPERATOR_REVIEW_PROTOCOL_TEMPLATE,
        "title": "PMBOT crypto operator review protocol",
        "objective": "Add a deterministic local operator review protocol for crypto pilot records.",
        "summary": "Prepare a local PMBOT crypto operator review protocol for descriptive record checks.",
        "allowed_paths": ("docs/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Crypto operator review protocol docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY",
        "template": CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_TEMPLATE,
        "title": "PMBOT crypto paperlive observation ledger",
        "objective": "Add a deterministic local observation ledger for crypto paperlive records.",
        "summary": "Prepare a local PMBOT crypto paperlive observation ledger for descriptive records.",
        "allowed_paths": ("docs/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Crypto paperlive observation ledger docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY",
        "template": CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_TEMPLATE,
        "title": "PMBOT crypto source quality capture surface",
        "objective": "Add a deterministic local source quality capture surface for crypto pilot records.",
        "summary": "Prepare a local PMBOT crypto source quality capture surface for operator review.",
        "allowed_paths": ("docs/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Crypto source quality capture surface docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE",
        "template": QUEUE_AND_PAPERLIVE_STATUS_SURFACE_TEMPLATE,
        "title": "PMBOT queue and paperlive status surface",
        "objective": "Add a deterministic local queue and paperlive status surface.",
        "summary": "Prepare a local PMBOT queue and paperlive status surface for operator review.",
        "allowed_paths": ("pm_bot/dashboard/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Queue and paperlive status surface code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY",
        "template": SOURCE_QUALITY_DASHBOARD_SUMMARY_TEMPLATE,
        "title": "PMBOT source quality dashboard summary",
        "objective": "Add a deterministic local source quality dashboard summary.",
        "summary": "Prepare a local PMBOT source quality dashboard summary for operator review.",
        "allowed_paths": ("pm_bot/dashboard/", "pm_bot/source_quality/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Source quality dashboard summary code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY",
        "template": PAPER_ACCOUNTING_DASHBOARD_SUMMARY_TEMPLATE,
        "title": "PMBOT paper accounting dashboard summary",
        "objective": "Add a deterministic local paper accounting dashboard summary.",
        "summary": "Prepare a local PMBOT paper accounting dashboard summary for operator review.",
        "allowed_paths": ("pm_bot/dashboard/", "pm_bot/paper_accounting/", "pm_bot/tests/", "tests/", "docs/"),
        "expected_outputs": (
            "Paper accounting dashboard summary code, fixtures, tests, or docs under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY",
        "template": AUTONOMY_GATE_CHECKLIST_TEMPLATE,
        "title": "PMBOT autonomy gate checklist",
        "objective": "Add a deterministic local autonomy gate checklist for operator review.",
        "summary": "Prepare a local PMBOT autonomy gate checklist for safety review.",
        "allowed_paths": ("docs/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Autonomy gate checklist docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY",
        "template": NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_TEMPLATE,
        "title": "PMBOT night batch postrun audit summary",
        "objective": "Add a deterministic local postrun audit summary for night batch records.",
        "summary": "Prepare a local PMBOT night batch postrun audit summary for operator review.",
        "allowed_paths": ("docs/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Night batch postrun audit summary docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY",
        "template": FORBIDDEN_ACTION_SCAN_TEMPLATE,
        "title": "PMBOT forbidden action scan",
        "objective": "Add a deterministic local forbidden action scan artifact.",
        "summary": "Prepare a local PMBOT forbidden action scan for operator review.",
        "allowed_paths": ("docs/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Forbidden action scan docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX",
        "template": LOCAL_TO_SUPERVISED_GAP_MATRIX_TEMPLATE,
        "title": "PMBOT local to supervised live gap matrix",
        "objective": "Add a deterministic local gap matrix for supervised review gates.",
        "summary": "Prepare a local PMBOT gap matrix for supervised review gate tracking.",
        "allowed_paths": ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Local to supervised gap matrix docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR",
        "template": NEXT_20_TASK_BACKLOG_GENERATOR_TEMPLATE,
        "title": "PMBOT next 20 task backlog generator",
        "objective": "Add a deterministic local backlog generator artifact for future operator review.",
        "summary": "Prepare a local PMBOT next task backlog generator artifact for operator review.",
        "allowed_paths": ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Next task backlog generator docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY",
        "template": MORNING_REVIEW_PACK_TEMPLATE,
        "title": "PMBOT morning review pack",
        "objective": "Add a deterministic local morning review pack for operator use.",
        "summary": "Prepare a local PMBOT morning review pack for operator review.",
        "allowed_paths": ("docs/", "pm_bot/dashboard/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Morning review pack docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
    {
        "task_id": "PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY",
        "template": NIGHT_BATCH_ACCEPTANCE_REPORT_TEMPLATE,
        "title": "PMBOT night batch acceptance report",
        "objective": "Add a deterministic local acceptance report for night batch operator review.",
        "summary": "Prepare a local PMBOT night batch acceptance report for operator review.",
        "allowed_paths": ("docs/", "pm_bot/dashboard/", "pm_bot/tests/", "tests/"),
        "expected_outputs": (
            "Night batch acceptance report docs, fixtures, tests, or local artifacts under allowed paths.",
            "A strict result JSON packet for operator review.",
        ),
    },
)

PMBOT_NIGHT_BATCH_TASKS_BY_TEMPLATE = {str(spec["template"]): spec for spec in PMBOT_NIGHT_BATCH_TASKS}
PMBOT_NIGHT_BATCH_TASK_IDS = tuple(str(spec["task_id"]) for spec in PMBOT_NIGHT_BATCH_TASKS)
PMBOT_NEXT_TWENTY_TASK_IDS = (
    "PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY",
    "PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY",
    "PMBOT-PAPERLIVE-DECISION-003-SIMULATED-DECISION-AUDIT-LEDGER-NO-RECOMMENDATIONS",
    "PMBOT-PAPERLIVE-DECISION-004-SIMULATED-DECISION-REPLAY-SUMMARY-NO-RECOMMENDATIONS",
    "PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY",
    "PMBOT-PAPER-ACCOUNTING-003-PAPER-ONLY-SESSION-SUMMARY-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY",
    "PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY",
    "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE",
    "PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY",
    "PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY",
    "PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY",
    "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY",
    "PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY",
    "PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX",
    "PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR",
    "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY",
    "PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY",
)
PMBOT_NEXT_TWENTY_TASKS = tuple(
    spec for spec in PMBOT_NIGHT_BATCH_TASKS if str(spec["task_id"]) in PMBOT_NEXT_TWENTY_TASK_IDS
)

PMBOT_NIGHT_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

PMBOT_NIGHT_ALLOWED_ACTIONS = (
    "Inspect local files under the allowed paths before editing.",
    "Add deterministic local code, tests, fixtures, or docs only for the named PMBOT artifact.",
    "Use local fixtures, local sample data, and operator-reviewed artifacts only.",
    "Run only the listed local validation commands.",
    "Return a strict result JSON packet for operator review.",
)

PMBOT_NIGHT_SAFETY_BOUNDARIES = (
    "Local files and fixtures only.",
    "No external service calls.",
    "No sensitive credential or signing material access.",
    "No transaction endpoint or execution endpoint work.",
    "No core execution wiring changes.",
    "No timed automation or resident process.",
    "No browser automation.",
    "No destructive commands.",
    "No forecast scoring, action guidance, or selection advice.",
)

PMBOT_NIGHT_FORBIDDEN_PATHS = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)


def build_pmbot_task_packet(
    task_id: str,
    template: str,
    *,
    repo_root: str = ".",
    base_branch: str = "master",
    expected_head: str | None = None,
) -> dict[str, Any]:
    safe_task_id = validate_task_id(task_id)
    if template in PMBOT_NIGHT_BATCH_TASKS_BY_TEMPLATE:
        return _build_night_batch_task_packet(
            safe_task_id,
            template,
            repo_root=repo_root,
            base_branch=base_branch,
            expected_head=expected_head,
        )
    if template != WEATHER_SOURCE_MONITORING_TEMPLATE:
        raise ValueError(f"unsupported PMBOT template: {template}")

    clean_expected_head = expected_head.strip() if isinstance(expected_head, str) else expected_head
    if clean_expected_head == "":
        clean_expected_head = None

    packet = default_packet()
    packet.update(
        {
            "task_id": safe_task_id,
            "title": "PMBOT weather outcome source monitoring plan runner",
            "status": "inbox",
            "created_by": "operator_cli",
            "created_at": _utc_iso(),
            "approved_by": None,
            "approved_at": None,
            "priority": "normal",
            "project": PMBOT_PROJECT,
            "task_template": {
                "schema_version": PMBOT_TEMPLATE_SCHEMA_VERSION,
                "name": template,
                "project": PMBOT_PROJECT,
            },
            "task_type": "local_code_tests",
            "objective": (
                "Prepare a deterministic local PMBOT weather outcome/source monitoring plan runner "
                "with operator review and local validation only."
            ),
            "summary": (
                "Create local PMBOT weather outcome/source monitoring plan-runner support with fixtures, "
                "tests, docs, and explicit operator review boundaries."
            ),
            "instructions": [
                "Inspect local PMBOT files under the allowed paths before editing.",
                "Build only deterministic local plan-runner support for weather outcome/source monitoring using fixtures or static test data.",
                "Keep the implementation operator-reviewed and local-only; write docs and tests for the exact behavior.",
                "Do not use network calls.",
                "Do not call OpenRouter.",
                "Do not call Polymarket API.",
                "Do not touch wallet code.",
                "Do not create orders.",
                "Do not add scheduler execution, background worker support, runtime changes, dispatcher changes, run_codex changes, browser automation, or authenticated endpoint use.",
                "Do not add probability, EV, edge, confidence, side-selection, recommendation, or market-action output.",
                "Do not add buy, sell, hold, enter, or exit recommendations.",
                "Do not use git add ., git add -A, git add --all, force push, or destructive commands.",
                "Return a strict result JSON packet that follows the result contract expectations.",
            ],
            "safety_boundaries": list(PMBOT_REQUIRED_FORBIDDEN_ACTIONS),
            "explicit_safety_boundaries": list(PMBOT_REQUIRED_FORBIDDEN_ACTIONS),
            "allowed_actions": list(PMBOT_ALLOWED_ACTIONS),
            "forbidden_actions": list(PMBOT_REQUIRED_FORBIDDEN_ACTIONS),
            "acceptance_checks": list(PMBOT_WEATHER_VALIDATION_COMMANDS),
            "validation_commands": list(PMBOT_WEATHER_VALIDATION_COMMANDS),
            "expected_outputs": [
                "Local PMBOT weather monitoring plan-runner code, tests, or docs under allowed paths.",
                "Focused validation output for the listed commands.",
                "Strict result JSON packet for operator review.",
            ],
            "result_contract_expectations": _result_contract_expectations(safe_task_id),
            "operator_notes": (
                "Generated by operator_cli create-pmbot-task from weather-source-monitoring. "
                "Review the inbox packet before approval."
            ),
        }
    )
    packet["source"] = {
        "origin": "operator_cli_pmbot_template",
        "reference": template,
    }
    packet["symphony_mapping"] = {
        "issue_id": safe_task_id,
        "workspace_key": safe_task_id.lower(),
        "proof_of_work_required": True,
        "human_review_required": True,
    }
    packet["repo"] = {
        "repo_root": repo_root,
        "base_branch": base_branch,
        "target_branch": None,
        "expected_head": clean_expected_head,
        "allowed_paths": list(PMBOT_WEATHER_ALLOWED_PATHS),
        "forbidden_paths": list(PMBOT_WEATHER_FORBIDDEN_PATHS),
    }
    packet["risk_flags"] = {key: False for key in packet["risk_flags"]}
    return packet


def _build_night_batch_task_packet(
    safe_task_id: str,
    template: str,
    *,
    repo_root: str,
    base_branch: str,
    expected_head: str | None,
) -> dict[str, Any]:
    spec = PMBOT_NIGHT_BATCH_TASKS_BY_TEMPLATE[template]
    if safe_task_id != spec["task_id"]:
        raise ValueError(f"template {template} is for task_id {spec['task_id']}, got {safe_task_id}")

    clean_expected_head = expected_head.strip() if isinstance(expected_head, str) else expected_head
    if clean_expected_head == "":
        clean_expected_head = None

    instructions = [
        "Inspect local PMBOT files under the allowed paths before editing.",
        str(spec["objective"]),
        "Use only local files, local fixtures, and static samples.",
        "Keep outputs descriptive, deterministic, and operator-reviewed.",
        "Do not produce forecast scoring, action guidance, or selection advice.",
        "Do not use git add ., git add -A, git add --all, force push, or destructive commands.",
        "Return a strict result JSON packet that follows the result contract expectations.",
    ]
    validation_commands = list(PMBOT_NIGHT_VALIDATION_COMMANDS)

    packet = default_packet()
    packet.update(
        {
            "task_id": safe_task_id,
            "title": str(spec["title"]),
            "status": "inbox",
            "created_by": "operator_cli",
            "created_at": _utc_iso(),
            "approved_by": None,
            "approved_at": None,
            "priority": "normal",
            "project": PMBOT_PROJECT,
            "task_template": {
                "schema_version": PMBOT_TEMPLATE_SCHEMA_VERSION,
                "name": template,
                "project": PMBOT_PROJECT,
            },
            "task_type": "local_code_tests",
            "objective": str(spec["objective"]),
            "summary": str(spec["summary"]),
            "instructions": instructions,
            "safety_boundaries": list(PMBOT_NIGHT_SAFETY_BOUNDARIES),
            "explicit_safety_boundaries": list(PMBOT_NIGHT_SAFETY_BOUNDARIES),
            "allowed_actions": list(PMBOT_NIGHT_ALLOWED_ACTIONS),
            "forbidden_actions": list(PMBOT_NIGHT_SAFETY_BOUNDARIES),
            "acceptance_checks": validation_commands,
            "validation_commands": validation_commands,
            "expected_outputs": list(spec["expected_outputs"]),
            "result_contract_expectations": _result_contract_expectations(safe_task_id),
            "operator_notes": (
                f"Generated by operator_cli create-pmbot-task from {template}. "
                "Review the inbox packet before approval."
            ),
        }
    )
    packet["source"] = {
        "origin": "operator_cli_pmbot_template",
        "reference": template,
    }
    packet["symphony_mapping"] = {
        "issue_id": safe_task_id,
        "workspace_key": safe_task_id.lower(),
        "proof_of_work_required": True,
        "human_review_required": True,
    }
    packet["repo"] = {
        "repo_root": repo_root,
        "base_branch": base_branch,
        "target_branch": None,
        "expected_head": clean_expected_head,
        "allowed_paths": list(spec["allowed_paths"]),
        "forbidden_paths": list(PMBOT_NIGHT_FORBIDDEN_PATHS),
    }
    packet["risk_flags"] = {key: False for key in packet["risk_flags"]}
    return packet


def example_pmbot_weather_task_packet() -> dict[str, Any]:
    packet = build_pmbot_task_packet(
        WEATHER_SOURCE_MONITORING_TASK_ID,
        WEATHER_SOURCE_MONITORING_TEMPLATE,
        repo_root=".",
        base_branch="master",
        expected_head=None,
    )
    example = copy.deepcopy(packet)
    example["created_at"] = None
    example["created_by"] = "operator"
    example["operator_notes"] = (
        "Safe example only. Create a fresh inbox packet with operator_cli create-pmbot-task before approval."
    )
    return example


def _result_contract_expectations(task_id: str) -> dict[str, Any]:
    return {
        "schema_version": "codex_task_result.v1",
        "task_id": task_id,
        "status_values": ["completed", "partial", "blocked", "failed"],
        "required_top_level_fields": [
            "schema_version",
            "task_id",
            "status",
            "completed_by",
            "completed_at",
            "summary",
            "files_created",
            "files_modified",
            "files_deleted",
            "commands_run",
            "validation_results",
            "acceptance_checks_passed",
            "safety_confirmation",
            "operator_review_notes",
            "next_recommended_action",
        ],
        "required_safety_confirmation": {
            "network_calls_performed": 0,
            "credentials_accessed": False,
            "wallet_or_trading_touched": False,
            "runtime_or_dispatcher_touched": False,
            "background_worker_added": False,
            "scheduler_added": False,
            "telegram_or_openclaw_added": False,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "codex_app_server_used": False,
            "destructive_commands_used": False,
        },
        "additional_expectations": [
            "Report every command that was run.",
            "Set acceptance_checks_passed to false unless the listed validation commands passed.",
            "Use status blocked or partial when a safety boundary prevents completion.",
            "Do not include probability, EV, edge, confidence, side selection, or market-action guidance.",
        ],
    }


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

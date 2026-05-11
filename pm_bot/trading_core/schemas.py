from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

GENERATED_AT = "2026-05-11T00:00:00Z"
ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/night_020_021")

PAPER_TRADE_INTENT_CONTRACT = "pmbot_paper_trade_intent_candidate.v1"
RISK_GATE_RESULT_CONTRACT = "pmbot_risk_gate_result.v1"
SIMULATED_EXECUTION_RESULT_CONTRACT = "pmbot_simulated_execution_result.v1"
PAPER_POSITION_RECORD_CONTRACT = "pmbot_paper_position_record.v1"
PAPER_POSITION_LEDGER_CONTRACT = "pmbot_paper_position_ledger.v1"
PORTFOLIO_STATE_CONTRACT = "pmbot_portfolio_state.v1"
POST_EXECUTION_AUDIT_RECORD_CONTRACT = "pmbot_post_execution_audit_record.v1"
POST_EXECUTION_AUDIT_CONTRACT = "pmbot_post_execution_audit.v1"
PAPER_TRADING_DASHBOARD_CONTRACT = "pmbot_paper_trading_dashboard.v1"

SIDE_LABELS = {"track_yes", "track_no", "no_action"}
PAPER_ACTION_TYPES = {"observe_only", "simulated_entry", "simulated_skip"}


class TradingCoreValidationError(ValueError):
    pass


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_json_object(path: str | Path, *, label: str = "input") -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise TradingCoreValidationError(f"{label} JSON must be an object")
    return value


def write_json(path: str | Path, value: Any) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, value: str) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(value, encoding="utf-8")


def clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def bullet_lines(items: Iterable[str]) -> list[str]:
    rows = [str(item) for item in items if str(item)]
    if not rows:
        return ["- none"]
    return [f"- {row}" for row in rows]


def trading_core_safety_summary() -> dict[str, Any]:
    return {
        "paper_only": True,
        "non_executable": True,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "wallet_required": False,
        "wallet_used": False,
        "trading_endpoint_required": False,
        "trading_endpoint_used": False,
        "real_money_used": False,
        "authenticated_endpoints_used": False,
        "live_network_used": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "autonomous_trading_enabled": False,
        "scheduler_created": False,
        "daemon_created": False,
        "background_worker_created": False,
    }


def assert_valid(name: str, valid: bool, errors: list[str]) -> None:
    if not valid:
        joined = "; ".join(errors)
        raise TradingCoreValidationError(f"{name} failed validation: {joined}")


def validate_paper_trade_intent_candidate(candidate: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(candidate, "contract_version", PAPER_TRADE_INTENT_CONTRACT, errors)
    for field in (
        "intent_id",
        "created_at",
        "market_id",
        "market_title",
        "hypothesis_id",
        "analysis_source_path",
        "rationale_summary",
        "evidence_basis",
        "uncertainty_notes",
    ):
        _require_nonempty_string(candidate, field, errors)
    _require_list(candidate, "evidence_source_paths", errors)
    _require_list(candidate, "missing_evidence", errors)
    if candidate.get("side_label") not in SIDE_LABELS:
        errors.append("side_label must be track_yes, track_no, or no_action")
    if candidate.get("paper_action_type") not in PAPER_ACTION_TYPES:
        errors.append("paper_action_type must be observe_only, simulated_entry, or simulated_skip")
    for field, expected in (
        ("paper_only", True),
        ("non_executable", True),
        ("real_order_allowed", False),
        ("wallet_required", False),
        ("trading_endpoint_required", False),
        ("operator_review_required", True),
        ("no_real_trade_decision", True),
    ):
        _require_bool(candidate, field, expected, errors)
    _require_number(candidate, "intended_notional_usd", errors, minimum=0)
    _require_number(candidate, "max_loss_usd", errors, minimum=0)
    return not errors, errors


def validate_risk_gate_result(result: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(result, "contract_version", RISK_GATE_RESULT_CONTRACT, errors)
    for field in ("gate_result_id", "intent_id", "market_id", "risk_gate_status"):
        _require_nonempty_string(result, field, errors)
    _require_bool_type(result, "allowed", errors)
    _require_bool_type(result, "blocked", errors)
    _require_list(result, "block_reasons", errors)
    _require_list(result, "warnings", errors)
    for field, expected in (
        ("paper_only", True),
        ("non_executable", True),
        ("real_order_allowed", False),
        ("wallet_required", False),
        ("trading_endpoint_required", False),
        ("operator_review_required", True),
    ):
        _require_bool(result, field, expected, errors)
    if bool(result.get("allowed")) == bool(result.get("blocked")):
        errors.append("exactly one of allowed or blocked must be true")
    return not errors, errors


def validate_simulated_execution_result(result: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(result, "contract_version", SIMULATED_EXECUTION_RESULT_CONTRACT, errors)
    for field in ("execution_id", "intent_id", "market_id", "execution_status"):
        _require_nonempty_string(result, field, errors)
    _require_bool_type(result, "simulated_fill", errors)
    _require_number(result, "filled_notional_usd", errors, minimum=0)
    for field, expected in (
        ("paper_only", True),
        ("real_order_submitted", False),
        ("wallet_used", False),
        ("trading_endpoint_used", False),
        ("live_price_used", False),
    ):
        _require_bool(result, field, expected, errors)
    return not errors, errors


def validate_paper_position_record(record: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(record, "contract_version", PAPER_POSITION_RECORD_CONTRACT, errors)
    for field in ("position_id", "market_id", "market_title", "hypothesis_id", "source_execution_id", "outcome_status"):
        _require_nonempty_string(record, field, errors)
    _require_number(record, "paper_exposure_usd", errors, minimum=0)
    _require_number(record, "paper_units", errors, minimum=0)
    for field, expected in (
        ("paper_only", True),
        ("real_position", False),
        ("live_price_used", False),
    ):
        _require_bool(record, field, expected, errors)
    return not errors, errors


def validate_paper_position_ledger(ledger: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(ledger, "contract_version", PAPER_POSITION_LEDGER_CONTRACT, errors)
    _require_list(ledger, "positions", errors)
    _require_number(ledger, "total_paper_exposure_usd", errors, minimum=0)
    _require_bool(ledger, "paper_only", True, errors)
    for index, record in enumerate(mapping_rows(ledger.get("positions"))):
        valid, nested_errors = validate_paper_position_record(record)
        if not valid:
            errors.extend(f"positions[{index}].{err}" for err in nested_errors)
    return not errors, errors


def validate_portfolio_state(state: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(state, "contract_version", PORTFOLIO_STATE_CONTRACT, errors)
    for field in ("portfolio_id", "generated_at"):
        _require_nonempty_string(state, field, errors)
    for field in ("total_paper_capital_usd", "total_paper_exposure_usd", "available_paper_capital_usd"):
        _require_number(state, field, errors, minimum=0)
    _require_bool(state, "paper_only", True, errors)
    return not errors, errors


def validate_post_execution_audit_record(record: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(record, "contract_version", POST_EXECUTION_AUDIT_RECORD_CONTRACT, errors)
    for field in ("check_id", "check_name", "status"):
        _require_nonempty_string(record, field, errors)
    if record.get("status") not in {"passed", "warning", "failed"}:
        errors.append("status must be passed, warning, or failed")
    _require_list(record, "details", errors)
    return not errors, errors


def validate_paper_trading_dashboard(dashboard: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    _require_equal(dashboard, "contract_version", PAPER_TRADING_DASHBOARD_CONTRACT, errors)
    for field in ("dashboard_id", "generated_at"):
        _require_nonempty_string(dashboard, field, errors)
    for field in (
        "intent_candidates",
        "risk_gate_results",
        "simulated_executions",
        "paper_positions",
        "next_operator_actions",
        "what_is_still_not_real_trading",
    ):
        _require_list(dashboard, field, errors)
    _require_bool(dashboard, "paper_only", True, errors)
    return not errors, errors


def _require_equal(value: Mapping[str, Any], field: str, expected: Any, errors: list[str]) -> None:
    if value.get(field) != expected:
        errors.append(f"{field} must be {expected!r}")


def _require_nonempty_string(value: Mapping[str, Any], field: str, errors: list[str]) -> None:
    if not isinstance(value.get(field), str) or not value.get(field, "").strip():
        errors.append(f"{field} must be a non-empty string")


def _require_list(value: Mapping[str, Any], field: str, errors: list[str]) -> None:
    if not isinstance(value.get(field), list):
        errors.append(f"{field} must be a list")


def _require_bool_type(value: Mapping[str, Any], field: str, errors: list[str]) -> None:
    if not isinstance(value.get(field), bool):
        errors.append(f"{field} must be a boolean")


def _require_bool(value: Mapping[str, Any], field: str, expected: bool, errors: list[str]) -> None:
    if value.get(field) is not expected:
        errors.append(f"{field} must be {str(expected).lower()}")


def _require_number(value: Mapping[str, Any], field: str, errors: list[str], *, minimum: float | None = None) -> None:
    number = value.get(field)
    if not isinstance(number, (int, float)) or isinstance(number, bool):
        errors.append(f"{field} must be numeric")
        return
    if minimum is not None and number < minimum:
        errors.append(f"{field} must be >= {minimum}")

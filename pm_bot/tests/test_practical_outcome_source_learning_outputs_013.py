from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")
JOIN_JSON = ARTIFACT_DIR / "outcome_source_learning_join_013.json"
DASHBOARD_JSON = ARTIFACT_DIR / "operator_dashboard_outcome_recheck_013.json"
OPERATOR_VIEW_JSON = ARTIFACT_DIR / "source_learning_scorecard_operator_view_013.json"
TEMPLATE_JSON = ARTIFACT_DIR / "manual_outcome_resolution_update_template_013.json"
FEEDBACK_JSON = ARTIFACT_DIR / "feedback_readiness_report_013.json"
SAFETY_SCAN_JSON = ARTIFACT_DIR / "outcome_recheck_source_learning_safety_scan_013.result.json"

UNSAFE_ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
UNSAFE_SIGNAL_PATTERN = re.compile(
    r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b",
    re.IGNORECASE,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_join_and_operator_outputs_exist() -> None:
    join = _load(JOIN_JSON)
    dashboard = _load(DASHBOARD_JSON)
    operator_view = _load(OPERATOR_VIEW_JSON)
    template = _load(TEMPLATE_JSON)
    feedback = _load(FEEDBACK_JSON)

    assert join["contract_version"] == "pmbot_outcome_source_learning_join.v1"
    assert dashboard["contract_version"] == "pmbot_operator_dashboard_outcome_recheck.v1"
    assert operator_view["contract_version"] == "pmbot_source_learning_scorecard_operator_view.v1"
    assert template["contract_version"] == "pmbot_manual_outcome_resolution_update_template.v1"
    assert feedback["contract_version"] == "pmbot_feedback_readiness_report.v1"


def test_join_links_markets_sources_updates_and_outcomes() -> None:
    join = _load(JOIN_JSON)

    assert len(join["market_records"]) == 5
    assert join["source_to_market_links"]
    assert join["source_to_outcome_pending_links"]
    assert join["applied_update_to_outcome_links"]
    assert join["evidence_to_outcome_links"]
    assert join["what_can_be_judged_now"]
    assert join["what_requires_future_outcome_resolution"]
    assert join["no_real_trade_decision"] is True


def test_operator_outputs_show_required_counts_and_templates() -> None:
    dashboard = _load(DASHBOARD_JSON)
    operator_view = _load(OPERATOR_VIEW_JSON)
    template = _load(TEMPLATE_JSON)
    feedback = _load(FEEDBACK_JSON)

    assert dashboard["tracked_market_count"] == 5
    assert dashboard["applied_paper_update_count"] == 1
    assert dashboard["unresolved_outcome_count"] == 5
    assert dashboard["outcome_recheck_priorities"]["high"] == 1
    assert dashboard["source_records_pending_outcome_resolution"]
    assert operator_view["useful_for_paper_tracking_update"]
    assert template["outcome_status"] == "unresolved"
    assert template["actual_outcome_summary"] is None
    assert template["resolution_source_reference"] is None
    assert template["approval_required"] is True
    assert feedback["feedback_ready_count"] == 0
    assert feedback["blocked_feedback_count"] == 5


def test_safety_scan_passes_and_unsafe_flags_are_closed() -> None:
    safety_scan = _load(SAFETY_SCAN_JSON)

    assert safety_scan["safety_ok"] is True
    assert safety_scan["issue_count"] == 0
    assert safety_scan["live_network_used"] is False
    assert safety_scan["openrouter_calls_performed"] == 0
    assert safety_scan["new_polymarket_api_calls_performed"] == 0
    assert safety_scan["authenticated_endpoints_used"] is False
    assert safety_scan["wallet_or_private_key_access"] is False
    assert safety_scan["orders_or_trading_actions"] is False
    assert safety_scan["runtime_or_dispatcher_changes"] is False
    assert safety_scan["market_recommendation_generated"] is False
    assert safety_scan["probability_ev_edge_or_side_selection_generated"] is False
    assert safety_scan["outcome_resolution_invented"] is False
    assert safety_scan["no_scheduler_daemon_background_worker"] is True
    assert safety_scan["no_autonomous_trading"] is True


def test_artifacts_do_not_emit_trading_language_or_signal_phrasing() -> None:
    for path in ARTIFACT_DIR.glob("*"):
        if path.suffix.lower() not in {".json", ".md"}:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            normalized = line.lower()
            if any(marker in normalized for marker in ("no ", "not ", "false", "blocked", "disallowed")):
                continue
            assert not UNSAFE_ACTION_PATTERN.search(line), path
            assert not UNSAFE_SIGNAL_PATTERN.search(line), path


def test_no_wallet_order_trading_or_runtime_unsafe_flags() -> None:
    unsafe_true_fields = {
        "authenticated_endpoints_used",
        "wallet_or_private_key_access",
        "orders_or_trading_actions",
        "runtime_or_dispatcher_changes",
        "market_recommendation_generated",
        "probability_ev_edge_or_side_selection_generated",
        "outcome_resolution_invented",
    }
    unsafe_positive_fields = {
        "openrouter_calls_performed",
        "new_polymarket_api_calls_performed",
        "polymarket_api_calls_performed",
    }
    for path in ARTIFACT_DIR.glob("*.json"):
        _assert_no_unsafe_flags(_load(path), unsafe_true_fields, unsafe_positive_fields, path)


def _assert_no_unsafe_flags(
    value: Any,
    unsafe_true_fields: set[str],
    unsafe_positive_fields: set[str],
    path: Path,
) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in unsafe_true_fields:
                assert nested is False, (path, key)
            if key in unsafe_positive_fields:
                assert nested == 0, (path, key)
            _assert_no_unsafe_flags(nested, unsafe_true_fields, unsafe_positive_fields, path)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_unsafe_flags(nested, unsafe_true_fields, unsafe_positive_fields, path)

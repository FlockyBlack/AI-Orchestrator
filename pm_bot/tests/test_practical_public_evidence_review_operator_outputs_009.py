from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_review_009")
CONSOLE_JSON = ARTIFACT_DIR / "operator_console_public_evidence_review_009.json"
DELTA_JSON = ARTIFACT_DIR / "paper_tracking_delta_report_009.json"
URL_FIX_JSON = ARTIFACT_DIR / "failed_source_url_fix_packet_009.json"
SAFETY_JSON = ARTIFACT_DIR / "public_evidence_review_safety_scan_009.result.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_operator_console_delta_and_url_fix_outputs_exist() -> None:
    console = _load(CONSOLE_JSON)
    delta = _load(DELTA_JSON)
    url_fix = _load(URL_FIX_JSON)

    assert (ARTIFACT_DIR / "operator_console_public_evidence_review_009.md").exists()
    assert (ARTIFACT_DIR / "paper_tracking_delta_report_009.md").exists()
    assert (ARTIFACT_DIR / "failed_source_url_fix_packet_009.md").exists()
    assert console["contract_version"] == "pmbot_operator_console_public_evidence_review.v1"
    assert delta["contract_version"] == "pmbot_paper_tracking_delta_report.v1"
    assert url_fix["contract_version"] == "pmbot_failed_source_url_fix_packet.v1"


def test_paper_tracking_delta_is_operator_review_only() -> None:
    delta = _load(DELTA_JSON)

    assert delta["evidence_reviewed"] is True
    assert delta["update_candidate_created"] is True
    assert delta["original_hypothesis_changed"] is False
    assert delta["operator_approval_required"] is True
    assert delta["unresolved_outcome_still_required"] is True
    assert delta["automatic_update_performed"] is False
    assert delta["automatic_analysis_update_performed"] is False
    assert delta["no_real_trade_decision"] is True


def test_failed_source_url_fix_packet_is_non_executable() -> None:
    url_fix = _load(URL_FIX_JSON)

    assert url_fix["failed_source_count"] == 4
    assert url_fix["failed_sources"]
    assert url_fix["requires_operator_review"] is True
    assert url_fix["no_live_fetch_performed_in_this_task"] is True
    assert url_fix["next_candidate_task"] == "ORCH-PMBOT-PRACTICAL-010-PUBLIC-SOURCE-URL-FIXES-AND-SECOND-CONTROLLED-FETCH-PACKET"


def test_operator_outputs_have_safe_flags_and_safety_scan_passed() -> None:
    scan_report = _load(SAFETY_JSON)
    scan = run_practical_safety_scan(artifact_dirs=[ARTIFACT_DIR])

    assert scan_report["public_evidence_review_safety_scan_passed"] is True
    assert scan_report["live_network_used"] is False
    assert scan_report["openrouter_calls_performed"] == 0
    assert scan_report["new_polymarket_api_calls_performed"] == 0
    assert scan_report["authenticated_endpoints_used"] is False
    assert scan_report["wallet_or_private_key_access"] is False
    assert scan_report["orders_or_trading_actions"] is False
    assert scan_report["runtime_or_dispatcher_changes"] is False
    assert scan_report["market_recommendation_generated"] is False
    assert scan_report["probability_ev_edge_or_side_selection_generated"] is False
    assert scan_report["automatic_analysis_update_performed"] is False
    assert scan_report["scheduler_background_worker_or_polling"] is False
    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pm_bot.practical.one_market_analysis import INPUT_CONTRACT_VERSION, OUTCOME_RECORD_CONTRACT_VERSION, PAPER_HYPOTHESIS_SAFETY_LABEL

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/real_market_batch_004")
DOC_PATHS = [
    Path("docs/PMBOT_REAL_MARKET_PAPER_TRACKING_WORKFLOW.md"),
    Path("docs/ORCH_PMBOT_PRACTICAL_004_REAL_MARKET_MULTI_PACKET_PAPER_TRACKING_BATCH.md"),
    Path("docs/ORCH_PMBOT_PRACTICAL_004_RESULT.json"),
]

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b", re.IGNORECASE)


def test_candidate_inventory_and_selected_batch_are_valid() -> None:
    inventory = _load_json(ARTIFACT_DIR / "candidate_market_artifact_inventory.json")
    selected = _load_json(ARTIFACT_DIR / "selected_real_market_batch.json")

    assert inventory["real_local_market_candidates_found"] is True
    assert inventory["live_network_used"] is False
    assert inventory["no_external_fetch_required"] is True
    assert inventory["candidates_considered_count"] >= selected["selected_count"]
    assert selected["selected_count"] >= 1
    assert selected["live_network_used"] is False
    assert selected["no_external_fetch_required"] is True

    required_candidate_fields = {
        "candidate_id",
        "candidate_path",
        "market_id",
        "market_title",
        "artifact_type",
        "market_class",
        "evidence_available",
        "source_references_available",
        "rules_available",
        "outcome_status_if_known",
        "missing_data",
        "safety_notes",
        "selected_for_batch",
        "selection_or_rejection_reason",
    }
    for candidate in inventory["candidates"]:
        assert required_candidate_fields <= set(candidate)
    assert {row["market_id"] for row in selected["selected_markets"]} <= {
        row["market_id"] for row in inventory["candidates"]
    }


def test_per_market_artifacts_exist_and_are_paper_only() -> None:
    selected = _selected_markets()

    for market in selected:
        market_id = market["market_id"]
        market_dir = ARTIFACT_DIR / "markets" / market_id
        normalized = _load_json(market_dir / "normalized_input.json")
        analysis = _load_json(market_dir / "analysis.result.json")
        paper = _load_json(market_dir / "paper_hypothesis.json")
        outcome = _load_json(market_dir / "outcome_record.unresolved.json")

        for name in ("import_summary.md", "analysis.md", "paper_hypothesis.md", "outcome_record.unresolved.md"):
            assert (market_dir / name).exists(), f"missing market markdown artifact: {market_dir / name}"

        assert normalized["contract_version"] == INPUT_CONTRACT_VERSION
        for field in (
            "market_id",
            "market_title",
            "market_slug_or_reference",
            "market_type",
            "outcomes",
            "resolution_source_summary",
            "rules_summary",
            "current_context_summary",
            "available_evidence",
            "missing_evidence",
            "known_uncertainties",
            "source_packets",
            "operator_notes",
            "created_at",
            "source_artifact_path",
        ):
            assert field in normalized
        assert normalized["market_id"] == market_id
        assert normalized["source_packets"]

        assert analysis["market_id"] == market_id
        assert analysis["paper_hypothesis_safety_label"] == PAPER_HYPOTHESIS_SAFETY_LABEL
        assert analysis["sources_used"]
        _assert_all_safety_flags_safe(analysis)

        assert paper["market_id"] == market_id
        assert paper["safety_label"] == PAPER_HYPOTHESIS_SAFETY_LABEL
        assert paper["no_real_trade_decision"] is True
        assert paper["market_recommendation_generated"] is False
        assert paper["probability_ev_edge_or_side_selection_generated"] is False
        assert paper["orders_or_trading_actions"] is False
        assert paper["source_dependencies"]

        assert outcome["contract_version"] == OUTCOME_RECORD_CONTRACT_VERSION
        assert outcome["market_id"] == market_id
        assert outcome["outcome_status"] == "unresolved"
        assert outcome["actual_outcome_summary"] == "unresolved"
        assert outcome["resolved_at"] is None
        assert outcome["resolution_source_reference"]
        assert outcome["next_outcome_check_action"]


def test_multi_market_queue_and_tracking_outputs_exist() -> None:
    selected = _selected_markets()
    selected_ids = {row["market_id"] for row in selected}

    queue = _load_json(ARTIFACT_DIR / "real_market_batch_004.market_queue.json")
    queue_summary = _load_json(ARTIFACT_DIR / "real_market_batch_004.market_queue.summary.json")
    active = _load_json(ARTIFACT_DIR / "real_market_batch_004.active_paper_hypotheses.result.json")
    outcome_queue = _load_json(ARTIFACT_DIR / "real_market_batch_004.outcome_check_queue.result.json")

    assert len(queue["items"]) == len(selected)
    assert {item["market_id"] for item in queue["items"]} == selected_ids
    assert queue_summary["total_count"] == len(selected)
    assert queue_summary["status_counts"] == {"hypothesis_active": len(selected)}
    assert queue_summary["missing_linked_artifacts"] == []
    assert active["unresolved_count"] == len(selected)
    assert active["resolved_count"] == 0
    assert {row["market_id"] for row in active["active_hypotheses"]} == selected_ids
    assert len(outcome_queue["outcome_checks"]) == len(selected)
    assert {row["market_id"] for row in outcome_queue["outcome_checks"]} == selected_ids
    assert set(outcome_queue["status_counts"]) <= {"due_now", "overdue", "unknown", "not_due", "resolved", "ambiguous"}

    for item in queue["items"]:
        for field in (
            "local_input_path",
            "analysis_result_path",
            "analysis_markdown_path",
            "paper_hypothesis_path",
            "outcome_record_path",
        ):
            assert Path(item[field]).exists(), f"missing linked queue artifact: {item[field]}"
        assert item["status"] in {"hypothesis_active", "outcome_pending"}


def test_batch_ledgers_console_next_actions_and_quality_outputs_exist() -> None:
    selected = _selected_markets()
    selected_ids = {row["market_id"] for row in selected}

    source_learning = _load_json(ARTIFACT_DIR / "real_market_batch_004.source_learning_pending.json")
    dependency_map = _load_json(ARTIFACT_DIR / "real_market_batch_004.source_dependency_map.json")
    console = _load_json(ARTIFACT_DIR / "real_market_batch_004.operator_console.result.json")
    next_actions = _load_json(ARTIFACT_DIR / "real_market_batch_004.operator_next_actions.json")
    quality = _load_json(ARTIFACT_DIR / "real_market_batch_004.analysis_quality_pending.json")

    assert source_learning["no_autonomous_training_performed"] is True
    assert source_learning["selected_market_count"] == len(selected)
    assert source_learning["unresolved_outcome_count"] == len(selected)
    assert source_learning["sources_used"]
    assert source_learning["pending_feedback_dependencies"]

    assert dependency_map["selected_market_count"] == len(selected)
    assert dependency_map["dependencies"]
    for row in dependency_map["dependencies"]:
        assert row["source_id"]
        assert set(row["market_ids"]) <= selected_ids
        assert row["hypothesis_ids"]
        assert row["dependency_role"]
        assert row["known_limitations"]
        assert row["pending_outcome_check"] is True
        assert row["future_source_learning_possible"] is True

    assert console["active_paper_hypotheses_count"] == len(selected)
    assert console["unresolved_outcomes_count"] == len(selected)
    assert {row["market_id"] for row in console["selected_real_local_markets"]} == selected_ids
    assert console["market_review_details"]
    assert console["sources_used_total"] > 0
    assert console["missing_evidence_total"] > 0
    _assert_all_safety_flags_safe(console)

    assert next_actions["inspect_first"]["market_id"] in selected_ids
    assert next_actions["most_missing_evidence_market"]["missing_evidence_count"] >= 1
    assert {row["market_id"] for row in next_actions["hypotheses_needing_future_outcome_check"]} == selected_ids
    assert next_actions["source_dependencies_to_watch"]
    assert next_actions["blocked_or_weakest_market"]["market_id"] in selected_ids
    assert next_actions["source_learning_after_resolution_only"]
    assert next_actions["next_safe_action"]
    assert next_actions["no_trading_instructions"] is True

    assert quality["selected_market_count"] == len(selected)
    assert quality["active_hypothesis_count"] == len(selected)
    assert quality["resolved_outcome_count"] == 0
    assert quality["quality_judgement_available"] is False
    assert quality["pending_resolution_count"] == len(selected)
    assert quality["what_can_be_judged_now"]
    assert quality["what_requires_future_outcomes"]
    assert quality["next_feedback_actions"]


def test_practical_safety_scan_passes_and_flags_are_safe() -> None:
    scan = _load_json(ARTIFACT_DIR / "real_market_batch_004.practical_safety_scan.result.json")

    assert scan["safety_ok"] is True
    assert scan["issue_count"] == 0
    assert scan["issues"] == []
    _assert_all_safety_flags_safe(scan)

    for expected in (
        "live_network_used",
        "openrouter_calls_performed",
        "polymarket_api_calls_performed",
        "authenticated_endpoints_used",
        "wallet_or_private_key_access",
        "orders_or_trading_actions",
        "runtime_or_dispatcher_changes",
        "market_recommendation_generated",
        "probability_ev_edge_or_side_selection_generated",
    ):
        assert expected in json.dumps(scan, sort_keys=True)


def test_artifacts_have_no_actionable_trading_or_signal_language() -> None:
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in list(ARTIFACT_DIR.rglob("*.json")) + list(ARTIFACT_DIR.rglob("*.md")) + DOC_PATHS
    )

    assert ACTION_PATTERN.search(artifact_text) is None
    assert SIGNAL_PATTERN.search(artifact_text) is None


def _selected_markets() -> list[dict[str, Any]]:
    payload = _load_json(ARTIFACT_DIR / "selected_real_market_batch.json")
    assert payload["selected_count"] >= 1
    markets = payload["selected_markets"]
    assert isinstance(markets, list)
    assert len(markets) == payload["selected_count"]
    return markets


def _load_json(path: Path) -> dict[str, Any]:
    assert path.exists(), f"missing artifact: {path}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _assert_all_safety_flags_safe(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {
                "authenticated_endpoints_used",
                "live_network_used",
                "market_recommendation_generated",
                "orders_or_trading_actions",
                "runtime_or_dispatcher_changes",
                "wallet_or_private_key_access",
            }:
                assert nested is False
            if key in {"openrouter_calls_performed", "polymarket_api_calls_performed"}:
                assert nested == 0
            _assert_all_safety_flags_safe(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_all_safety_flags_safe(nested)

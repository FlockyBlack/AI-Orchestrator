from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pm_bot.practical.local_market_packet_import import normalize_local_market_packet
from pm_bot.practical.one_market_analysis import INPUT_CONTRACT_VERSION, PAPER_HYPOTHESIS_SAFETY_LABEL

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/real_market_003")
SELECTED_SOURCE = Path("pm_bot/llm/manual_packet_batch/692258_packet.v1.json")

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b", re.IGNORECASE)


def test_selected_source_pointer_is_valid() -> None:
    pointer = _load_json("selected_real_market_source_pointer.json")

    if pointer["selected"] is False:
        assert (ARTIFACT_DIR / "real_market_003.blocker.md").exists()
        return

    assert pointer["selected"] is True
    assert pointer["market_id"] == "692258"
    assert pointer["selected_artifact_path"] == _repo_path(SELECTED_SOURCE)
    assert Path(pointer["selected_artifact_path"]).exists()
    assert pointer["live_network_used"] is False
    assert pointer["no_external_fetch_required"] is True


def test_manual_packet_normalizes_to_required_one_market_fields() -> None:
    generated = _load_json("real_market_003.normalized_input.json")
    direct = normalize_local_market_packet(SELECTED_SOURCE)

    assert generated == direct
    assert generated["contract_version"] == INPUT_CONTRACT_VERSION
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
        assert field in generated
    assert generated["market_id"] == "692258"
    assert generated["market_title"] == "MicroStrategy sells any Bitcoin by June 30, 2026?"
    assert generated["source_packets"]
    assert any("Referenced source artifact path is not present locally" in row for row in generated["missing_evidence"])


def test_analysis_and_paper_hypothesis_are_safe() -> None:
    analysis = _load_json("real_market_003.analysis.result.json")
    paper = _load_json("real_market_003.paper_hypothesis.json")

    assert analysis["market_id"] == "692258"
    assert analysis["live_network_used"] is False
    assert analysis["openrouter_calls_performed"] == 0
    assert analysis["polymarket_api_calls_performed"] == 0
    assert analysis["authenticated_endpoints_used"] is False
    assert analysis["wallet_or_private_key_access"] is False
    assert analysis["orders_or_trading_actions"] is False
    assert analysis["runtime_or_dispatcher_changes"] is False
    assert analysis["market_recommendation_generated"] is False
    assert analysis["probability_ev_edge_or_side_selection_generated"] is False
    assert paper["safety_label"] == PAPER_HYPOTHESIS_SAFETY_LABEL
    assert paper["no_real_trade_decision"] is True
    assert paper["market_recommendation_generated"] is False
    assert paper["probability_ev_edge_or_side_selection_generated"] is False
    assert paper["orders_or_trading_actions"] is False


def test_queue_console_outcome_and_source_learning_artifacts_exist() -> None:
    outcome = _load_json("real_market_003.outcome_record.unresolved.json")
    queue = _load_json("real_market_003.market_queue.json")
    queue_summary = _load_json("real_market_003.market_queue.summary.json")
    active = _load_json("real_market_003.active_paper_hypotheses.result.json")
    outcome_queue = _load_json("real_market_003.outcome_check_queue.result.json")
    console = _load_json("real_market_003.operator_console.result.json")
    source_learning = _load_json("real_market_003.source_learning_pending.json")

    assert outcome["outcome_status"] == "unresolved"
    assert len(queue["items"]) == 1
    assert queue["items"][0]["status"] == "hypothesis_active"
    assert queue["items"][0]["paper_hypothesis_path"].endswith("real_market_003.paper_hypothesis.json")
    assert queue_summary["status_counts"] == {"hypothesis_active": 1}
    assert active["active_hypotheses"][0]["market_id"] == "692258"
    assert active["active_hypotheses"][0]["outcome_status"] == "unresolved"
    assert outcome_queue["outcome_checks"][0]["outcome_check_status"] == "due_now"
    assert console["market_review_details"][0]["outcome_status"] == "unresolved"
    assert console["market_review_details"][0]["sources_used"]
    assert console["market_review_details"][0]["missing_evidence"]
    assert source_learning["no_autonomous_training_performed"] is True
    assert source_learning["pending_feedback_dependency"]


def test_safety_scan_passes_and_artifacts_have_no_actionable_language() -> None:
    safety_scan = _load_json("real_market_003.practical_safety_scan.result.json")

    assert safety_scan["safety_ok"] is True
    assert safety_scan["issue_count"] == 0
    _assert_all_safety_flags_safe(safety_scan)

    scanned_text = "\n".join(path.read_text(encoding="utf-8") for path in ARTIFACT_DIR.glob("real_market_003.*") if path.suffix in {".json", ".md"})
    assert ACTION_PATTERN.search(scanned_text) is None
    assert SIGNAL_PATTERN.search(scanned_text) is None


def _load_json(name: str) -> dict[str, Any]:
    path = ARTIFACT_DIR / name
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


def _repo_path(path: Path) -> str:
    return str(path).replace("\\", "/")

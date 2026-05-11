from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    PAPER_TRADE_INTENT_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    normalize_path,
    trading_core_safety_summary,
    validate_paper_trade_intent_candidate,
    write_json,
    write_text,
)

TRADE_INTENT_BATCH_CONTRACT = "pmbot_paper_trade_intent_candidate_batch.v1"

DEFAULT_MARKET_QUEUE_PATH = Path("pm_bot/practical/artifacts/add_market_016/market_queue_6_016.json")
DEFAULT_ACTIVE_HYPOTHESES_PATH = Path("pm_bot/practical/artifacts/add_market_016/active_paper_hypotheses_6_016.json")
DEFAULT_PUBLIC_EVIDENCE_DASHBOARD_PATH = Path(
    "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json"
)
DEFAULT_PAPER_SNAPSHOT_PATH = Path(
    "pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json"
)
DEFAULT_FILLED_URL_DASHBOARD_PATH = Path(
    "pm_bot/practical/artifacts/manual_url_collection_017c/public_evidence_dashboard_url_filled_pending_approval_017c.json"
)


def load_practical_paper_state(
    *,
    market_queue_path: str | Path = DEFAULT_MARKET_QUEUE_PATH,
    active_hypotheses_path: str | Path = DEFAULT_ACTIVE_HYPOTHESES_PATH,
    public_evidence_dashboard_path: str | Path = DEFAULT_PUBLIC_EVIDENCE_DASHBOARD_PATH,
    paper_snapshot_path: str | Path = DEFAULT_PAPER_SNAPSHOT_PATH,
    filled_url_dashboard_path: str | Path = DEFAULT_FILLED_URL_DASHBOARD_PATH,
) -> dict[str, Any]:
    return {
        "market_queue_path": normalize_path(market_queue_path),
        "active_hypotheses_path": normalize_path(active_hypotheses_path),
        "public_evidence_dashboard_path": normalize_path(public_evidence_dashboard_path),
        "paper_snapshot_path": normalize_path(paper_snapshot_path),
        "filled_url_dashboard_path": normalize_path(filled_url_dashboard_path),
        "market_queue": load_json_object(market_queue_path, label="market queue"),
        "active_hypotheses": load_json_object(active_hypotheses_path, label="active hypotheses"),
        "public_evidence_dashboard": load_json_object(public_evidence_dashboard_path, label="public evidence dashboard"),
        "paper_snapshot": load_json_object(paper_snapshot_path, label="paper tracking snapshot"),
        "filled_url_dashboard": load_json_object(filled_url_dashboard_path, label="filled URL dashboard"),
    }


def build_paper_trade_intent_candidates(
    *,
    state: Mapping[str, Any] | None = None,
    evidence_completeness_threshold: int = 1,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    practical_state = dict(state or load_practical_paper_state())
    markets = _active_markets(practical_state)
    hypotheses_by_market = _hypotheses_by_market(practical_state)
    evidence_by_market = _evidence_by_market(practical_state)
    filled_dashboard = practical_state.get("filled_url_dashboard", {})

    candidates = []
    for market in markets:
        market_id = clean_text(market.get("market_id"))
        hypothesis = hypotheses_by_market.get(market_id, {})
        evidence_paths = sorted(evidence_by_market.get(market_id, []))
        action_type = "simulated_entry" if len(evidence_paths) >= evidence_completeness_threshold else "observe_only"
        side_label = "track_yes" if action_type == "simulated_entry" else "no_action"
        missing_evidence = _missing_evidence(market, hypothesis, evidence_paths, filled_dashboard)
        intended_notional = 25.0 if action_type == "simulated_entry" else 0.0
        candidate = {
            "contract_version": PAPER_TRADE_INTENT_CONTRACT,
            "intent_id": f"paper-intent-020-021-{market_id}",
            "created_at": generated_at,
            "market_id": market_id,
            "market_title": clean_text(market.get("market_title")),
            "hypothesis_id": clean_text(
                hypothesis.get("hypothesis_id")
                or market.get("paper_hypothesis_id")
            ),
            "analysis_source_path": clean_text(market.get("analysis_result_path") or market.get("analysis_markdown_path")),
            "evidence_source_paths": evidence_paths,
            "side_label": side_label,
            "side_label_meaning": "paper tracking label only; not a real market side or recommendation",
            "paper_action_type": action_type,
            "rationale_summary": _rationale_summary(action_type, evidence_paths),
            "evidence_basis": _evidence_basis(market_id, evidence_paths, filled_dashboard),
            "uncertainty_notes": (
                "Outcome is unresolved and no live market data, real price, wallet, order, or authenticated endpoint "
                "is available to this paper simulation."
            ),
            "missing_evidence": missing_evidence,
            "intended_notional_usd": intended_notional,
            "max_loss_usd": intended_notional,
            "paper_only": True,
            "non_executable": True,
            "real_order_allowed": False,
            "wallet_required": False,
            "trading_endpoint_required": False,
            "operator_review_required": True,
            "no_real_trade_decision": True,
        }
        valid, errors = validate_paper_trade_intent_candidate(candidate)
        assert_valid(candidate["intent_id"], valid, errors)
        candidates.append(candidate)

    return {
        "contract_version": TRADE_INTENT_BATCH_CONTRACT,
        "batch_id": "paper-trade-intent-candidates-night-020-021",
        "generated_at": generated_at,
        "source_artifacts": {
            "market_queue_path": practical_state["market_queue_path"],
            "active_hypotheses_path": practical_state["active_hypotheses_path"],
            "public_evidence_dashboard_path": practical_state["public_evidence_dashboard_path"],
            "paper_snapshot_path": practical_state["paper_snapshot_path"],
            "filled_url_dashboard_path": practical_state["filled_url_dashboard_path"],
        },
        "paper_intent_count": len(candidates),
        "simulated_entry_count": len([row for row in candidates if row["paper_action_type"] == "simulated_entry"]),
        "observe_only_count": len([row for row in candidates if row["paper_action_type"] == "observe_only"]),
        "candidates": candidates,
        "safety_summary": trading_core_safety_summary(),
    }


def run_trade_intent_candidate_generation(
    *,
    out_json_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    batch = build_paper_trade_intent_candidates(generated_at=generated_at)
    write_json(out_json_path, batch)
    write_text(out_md_path, render_paper_trade_intent_candidates_markdown(batch))
    return batch


def render_paper_trade_intent_candidates_markdown(batch: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Trade Intent Candidates",
        "",
        "- Paper-only, non-executable candidate batch.",
        f"- Intent candidates: {batch.get('paper_intent_count')}",
        f"- Simulated-entry candidates: {batch.get('simulated_entry_count')}",
        f"- Observe-only candidates: {batch.get('observe_only_count')}",
        "",
        "## Candidates",
        "",
    ]
    for candidate in mapping_rows(batch.get("candidates")):
        lines.extend(
            [
                f"### `{candidate.get('market_id')}`",
                "",
                f"- Title: {candidate.get('market_title')}",
                f"- Intent: `{candidate.get('intent_id')}`",
                f"- Hypothesis: `{candidate.get('hypothesis_id')}`",
                f"- Paper action type: `{candidate.get('paper_action_type')}`",
                f"- Side label: `{candidate.get('side_label')}` paper-tracking label only",
                f"- Intended paper notional: `${candidate.get('intended_notional_usd')}`",
                f"- Saved local evidence paths: {len(candidate.get('evidence_source_paths', []))}",
                f"- Rationale: {candidate.get('rationale_summary')}",
                "- Missing evidence:",
                *bullet_lines(str(item) for item in candidate.get("missing_evidence", [])),
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            "",
            "- Every candidate is paper-only and non-executable.",
            "- real_order_allowed remains `false`.",
            "- wallet_required remains `false`.",
            "- trading_endpoint_required remains `false`.",
            "- operator_review_required remains `true`.",
            "- Side labels are paper tracking labels only, not real trading instructions.",
        ]
    )
    return "\n".join(lines) + "\n"


def _active_markets(state: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    queue_items = mapping_rows(state.get("market_queue", {}).get("items"))
    if queue_items:
        return sorted(queue_items, key=lambda row: clean_text(row.get("market_id")))
    return sorted(mapping_rows(state.get("filled_url_dashboard", {}).get("markets")), key=lambda row: clean_text(row.get("market_id")))


def _hypotheses_by_market(state: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = mapping_rows(state.get("active_hypotheses", {}).get("active_hypotheses"))
    return {clean_text(row.get("market_id")): row for row in rows}


def _evidence_by_market(state: Mapping[str, Any]) -> dict[str, list[str]]:
    evidence: dict[str, list[str]] = {}
    for packet in mapping_rows(state.get("public_evidence_dashboard", {}).get("evidence_packets")):
        path = clean_text(packet.get("evidence_packet_path"))
        for market_id in packet.get("market_ids", []):
            if path:
                evidence.setdefault(clean_text(market_id), []).append(path)
    for link in mapping_rows(state.get("paper_snapshot", {}).get("evidence_links")):
        path = clean_text(link.get("evidence_packet_path"))
        market_id = clean_text(link.get("market_id"))
        if path:
            evidence.setdefault(market_id, []).append(path)
    return {market_id: sorted(set(paths)) for market_id, paths in evidence.items()}


def _missing_evidence(
    market: Mapping[str, Any],
    hypothesis: Mapping[str, Any],
    evidence_paths: list[str],
    filled_dashboard: Mapping[str, Any],
) -> list[str]:
    missing = []
    if not clean_text(market.get("analysis_result_path") or market.get("analysis_markdown_path")):
        missing.append("analysis_source_missing")
    if not clean_text(hypothesis.get("hypothesis_id") or market.get("paper_hypothesis_id")):
        missing.append("active_hypothesis_missing")
    if not evidence_paths:
        missing.append("saved_public_evidence_packet_missing")
    if clean_text(market.get("market_id")) == clean_text(filled_dashboard.get("market_id")):
        if filled_dashboard.get("approval_pending") is True:
            missing.append("new_market_public_fetch_approval_pending")
        if filled_dashboard.get("live_fetch_performed") is False:
            missing.append("new_market_saved_fetch_evidence_missing")
    missing.append("outcome_unresolved")
    return missing


def _rationale_summary(action_type: str, evidence_paths: list[str]) -> str:
    if action_type == "simulated_entry":
        return (
            "Saved local public evidence exists for this market, so the paper simulator can create a "
            "small non-executable tracking fill for ledger plumbing."
        )
    return (
        "Saved local public evidence is incomplete for this market, so the paper candidate stays in "
        "observe-only tracking."
    )


def _evidence_basis(market_id: str, evidence_paths: list[str], filled_dashboard: Mapping[str, Any]) -> str:
    if evidence_paths:
        return "Uses saved local public evidence packet metadata from previous approved practical tasks."
    if market_id == clean_text(filled_dashboard.get("market_id")):
        return "Uses local filled URL packet metadata only; no live fetch was performed for this candidate."
    return "Uses practical market queue and active paper hypothesis metadata only."


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build paper-only trade intent candidates from local PMBOT artifacts.")
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.md"))
    args = parser.parse_args(argv)
    run_trade_intent_candidate_generation(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, mapping_rows

UNRESOLVED_MARKET_REPORT_CONTRACT = "pmbot_unresolved_market_report.v1"
RESOLVED_OUTCOME_STATUSES = {"resolved", "void", "ambiguous"}


class UnresolvedMarketGuardError(ValueError):
    pass


def verify_markets_unresolved(
    markets: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = _market_rows(markets)
    statuses = [_market_status(row) for row in rows]
    violations = [
        {
            "market_id": clean_text(row.get("market_id")),
            "market_title": clean_text(row.get("market_title")),
            "outcome_status": status,
            "reason": "outcome_status_must_remain_unresolved",
        }
        for row, status in zip(rows, statuses)
        if status != "unresolved"
    ]
    return {
        "contract_version": UNRESOLVED_MARKET_REPORT_CONTRACT,
        "generated_at": generated_at,
        "market_count": len(rows),
        "unresolved_market_count": len([status for status in statuses if status == "unresolved"]),
        "feedback_ready_count": 0,
        "unresolved_verified": not violations,
        "violations": violations,
        "markets": [
            {
                "market_id": clean_text(row.get("market_id")),
                "market_title": clean_text(row.get("market_title")),
                "outcome_status": status,
                "feedback_ready": False,
            }
            for row, status in zip(rows, statuses)
        ],
        "safety": {
            "outcome_invented": False,
            "resolved_without_evidence": False,
            "paper_only": True,
        },
    }


def reject_invented_outcomes(
    markets: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    outcome_inputs: Sequence[Mapping[str, Any]] | Mapping[str, Any],
) -> dict[str, Any]:
    market_ids = {clean_text(row.get("market_id")) for row in _market_rows(markets)}
    invented = []
    for outcome in _outcome_rows(outcome_inputs):
        market_id = clean_text(outcome.get("market_id"))
        if market_ids and market_id not in market_ids:
            continue
        status = clean_text(outcome.get("outcome_status") or outcome.get("status")).lower()
        if status not in RESOLVED_OUTCOME_STATUSES:
            continue
        if _has_resolution_evidence(outcome):
            continue
        invented.append(
            {
                "market_id": market_id,
                "outcome_status": status,
                "reason": "resolved_outcome_without_explicit_local_evidence",
            }
        )
    if invented:
        raise UnresolvedMarketGuardError(f"invented outcome guard rejected inputs: {invented}")
    return {
        "outcome_invented": False,
        "checked_market_count": len(market_ids),
        "checked_outcome_input_count": len(_outcome_rows(outcome_inputs)),
    }


def build_unresolved_market_report(
    markets: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return verify_markets_unresolved(markets, generated_at=generated_at)


def assert_markets_unresolved(
    markets: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    report = verify_markets_unresolved(markets, generated_at=generated_at)
    if not report["unresolved_verified"]:
        raise UnresolvedMarketGuardError(f"markets are not all unresolved: {report['violations']}")
    return report


def _market_rows(markets: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if isinstance(markets, Mapping):
        for key in ("tracked_markets", "markets", "items", "active_hypotheses", "active_paper_hypotheses"):
            rows = mapping_rows(markets.get(key))
            if rows:
                return rows
        return [markets]
    return [row for row in markets if isinstance(row, Mapping)]


def _outcome_rows(outcome_inputs: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if isinstance(outcome_inputs, Mapping):
        for key in ("outcomes", "outcome_inputs", "records", "items"):
            rows = mapping_rows(outcome_inputs.get(key))
            if rows:
                return rows
        if all(isinstance(value, Mapping) for value in outcome_inputs.values()):
            return [value for value in outcome_inputs.values() if isinstance(value, Mapping)]
        return [outcome_inputs]
    return [row for row in outcome_inputs if isinstance(row, Mapping)]


def _market_status(row: Mapping[str, Any]) -> str:
    direct = clean_text(row.get("outcome_status") or row.get("status")).lower()
    if direct in {"unresolved", "resolved", "void", "ambiguous", "unknown"}:
        return direct
    outcome = row.get("outcome")
    if isinstance(outcome, Mapping):
        nested = clean_text(outcome.get("outcome_status") or outcome.get("status")).lower()
        if nested:
            return nested
    return direct or "unknown"


def _has_resolution_evidence(outcome: Mapping[str, Any]) -> bool:
    for field in (
        "resolution_evidence_path",
        "resolution_evidence_artifact",
        "resolution_source_artifact",
        "resolution_evidence_summary",
    ):
        if clean_text(outcome.get(field)):
            return True
    evidence_rows = outcome.get("source_evidence_used_for_resolution")
    if isinstance(evidence_rows, list) and evidence_rows:
        return True
    reference = clean_text(outcome.get("resolution_source_reference"))
    if reference and not reference.lower().startswith("stub summary only"):
        return True
    evidence_path = outcome.get("resolution_evidence_path")
    if evidence_path and Path(str(evidence_path)).exists():
        return True
    return False

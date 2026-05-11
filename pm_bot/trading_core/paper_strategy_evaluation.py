from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    normalize_path,
    trading_core_safety_summary,
    write_json,
    write_text,
)

PAPER_STRATEGY_EVALUATION_RECORD_CONTRACT = "pmbot_paper_strategy_evaluation_record.v1"
PAPER_STRATEGY_EVALUATION_LEDGER_CONTRACT = "pmbot_paper_strategy_evaluation_ledger.v1"
PAPER_STRATEGY_EVALUATION_SUMMARY_CONTRACT = "pmbot_paper_strategy_evaluation_summary.v1"


def build_paper_strategy_evaluation_ledger(
    *,
    candidates_batch: Mapping[str, Any],
    risk_gate_batch: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
    position_ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    feedback_readiness: Mapping[str, Any] | None = None,
    source_evidence_refresh_ledger: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    run_id = _first_text(
        candidates_batch.get("daily_run_id"),
        execution_batch.get("daily_run_id"),
        position_ledger.get("daily_run_id"),
    )
    run_date = _first_text(
        candidates_batch.get("run_date"),
        execution_batch.get("run_date"),
        position_ledger.get("run_date"),
    )
    risk_by_intent = {clean_text(row.get("intent_id")): row for row in mapping_rows(risk_gate_batch.get("results"))}
    execution_by_intent = {
        clean_text(row.get("intent_id")): row for row in mapping_rows(execution_batch.get("results"))
    }
    position_by_open_key = {
        _open_position_key(row.get("market_id"), row.get("intent_id")): row
        for row in mapping_rows(position_ledger.get("positions"))
    }
    exposure_by_market = dict(portfolio_state.get("exposure_by_market_usd", {}))
    total_unresolved_exposure = round(
        sum(
            float(row.get("paper_exposure_usd", 0) or 0)
            for row in mapping_rows(position_ledger.get("positions"))
            if clean_text(row.get("outcome_status")) == "unresolved"
        ),
        2,
    )

    records = []
    for candidate in sorted(
        mapping_rows(candidates_batch.get("candidates")),
        key=lambda row: (clean_text(row.get("market_id")), clean_text(row.get("intent_id"))),
    ):
        intent_id = clean_text(candidate.get("intent_id"))
        market_id = clean_text(candidate.get("market_id"))
        risk_result = risk_by_intent.get(intent_id, {})
        execution = execution_by_intent.get(intent_id, {})
        position = position_by_open_key.get(_open_position_key(market_id, intent_id), {})
        record = _strategy_record(
            candidate=candidate,
            risk_result=risk_result,
            execution=execution,
            position=position,
            run_id=run_id,
            run_date=run_date,
            generated_at=generated_at,
            exposure_by_market=exposure_by_market,
            total_unresolved_exposure_usd=total_unresolved_exposure,
            feedback_readiness=feedback_readiness or {},
            source_evidence_refresh_ledger=source_evidence_refresh_ledger or {},
        )
        records.append(record)

    record_ids = [clean_text(row.get("evaluation_record_id")) for row in records]
    hypotheses_waiting = _hypotheses_waiting_for_resolution(records)
    missing_data = sorted(
        {
            clean_text(item)
            for row in records
            for item in row.get("missing_future_evaluation_data", [])
            if clean_text(item)
        }
    )
    ledger = {
        "contract_version": PAPER_STRATEGY_EVALUATION_LEDGER_CONTRACT,
        "ledger_id": f"paper-strategy-evaluation-ledger-024-{_slug(run_date)}",
        "generated_at": generated_at,
        "run_id": run_id,
        "run_date": run_date,
        "records": records,
        "record_count": len(records),
        "filled_record_count": len([row for row in records if row.get("simulated_fill") is True]),
        "open_position_record_count": len([row for row in records if row.get("position", {}).get("position_id")]),
        "unresolved_position_record_count": len(
            [row for row in records if row.get("position", {}).get("outcome_status") == "unresolved"]
        ),
        "unresolved_paper_exposure_usd": total_unresolved_exposure,
        "hypotheses_waiting_for_outcome_resolution": hypotheses_waiting,
        "missing_future_evaluation_data": missing_data,
        "source_evidence_refresh_status": _source_refresh_ledger_summary(source_evidence_refresh_ledger or {}),
        "idempotency": {
            "record_ids_unique": len(record_ids) == len(set(record_ids)),
            "record_order": "market_id_then_intent_id",
        },
        "paper_only": True,
        "analysis_only": True,
        "performance_pnl_claimed": False,
        "unresolved_pnl_not_invented": True,
        "real_positions_created": False,
        "live_prices_used": False,
        "safety_summary": trading_core_safety_summary(),
    }
    return ledger


def build_paper_strategy_evaluation_summary(
    *,
    strategy_ledger: Mapping[str, Any],
    feedback_readiness: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    unresolved_exposure = float(strategy_ledger.get("unresolved_paper_exposure_usd", 0) or 0)
    unresolved_count = int(strategy_ledger.get("unresolved_position_record_count", 0) or 0)
    summary = {
        "contract_version": PAPER_STRATEGY_EVALUATION_SUMMARY_CONTRACT,
        "summary_id": f"paper-strategy-evaluation-summary-024-{_slug(strategy_ledger.get('run_date'))}",
        "generated_at": generated_at,
        "run_id": clean_text(strategy_ledger.get("run_id")),
        "run_date": clean_text(strategy_ledger.get("run_date")),
        "ledger_id": clean_text(strategy_ledger.get("ledger_id")),
        "performance_readiness_status": (
            "blocked_pending_outcome_resolution" if unresolved_count else "ready_for_local_feedback_review"
        ),
        "performance_statement": "No paper profit/loss is claimed while tracked outcomes remain unresolved.",
        "paper_realized_pnl_usd": None,
        "paper_unrealized_pnl_usd": None,
        "unresolved_pnl_not_invented": True,
        "unresolved_paper_exposure_usd": unresolved_exposure,
        "total_paper_exposure_usd": float(portfolio_state.get("total_paper_exposure_usd", 0) or 0),
        "unresolved_position_record_count": unresolved_count,
        "feedback_ready_count": int(feedback_readiness.get("feedback_ready_count", 0) or 0),
        "blocked_feedback_count": int(feedback_readiness.get("blocked_feedback_count", 0) or 0),
        "hypotheses_waiting_for_outcome_resolution": list(
            strategy_ledger.get("hypotheses_waiting_for_outcome_resolution", [])
        ),
        "missing_future_evaluation_data": list(strategy_ledger.get("missing_future_evaluation_data", [])),
        "source_evidence_refresh_status": dict(strategy_ledger.get("source_evidence_refresh_status", {})),
        "next_operator_action": "Add saved local outcome resolution evidence before evaluating paper performance.",
        "paper_only": True,
        "analysis_only": True,
        "real_positions_created": False,
        "live_prices_used": False,
        "safety_summary": trading_core_safety_summary(),
    }
    return summary


def run_paper_strategy_evaluation(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    risk_gate_path: str | Path = ARTIFACT_DIR / "risk_gate_results.json",
    executions_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.json",
    ledger_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.json",
    portfolio_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.json",
    feedback_readiness_path: str | Path | None = None,
    out_ledger_json_path: str | Path = ARTIFACT_DIR / "paper_strategy_evaluation_ledger.json",
    out_ledger_md_path: str | Path = ARTIFACT_DIR / "paper_strategy_evaluation_ledger.md",
    out_summary_json_path: str | Path = ARTIFACT_DIR / "paper_strategy_evaluation_summary.json",
    out_summary_md_path: str | Path = ARTIFACT_DIR / "paper_strategy_evaluation_summary.md",
    generated_at: str = GENERATED_AT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    feedback_readiness = (
        load_json_object(feedback_readiness_path, label="feedback readiness")
        if feedback_readiness_path is not None and Path(feedback_readiness_path).exists()
        else {}
    )
    portfolio_state = load_json_object(portfolio_path, label="portfolio state")
    strategy_ledger = build_paper_strategy_evaluation_ledger(
        candidates_batch=load_json_object(candidates_path, label="intent candidates"),
        risk_gate_batch=load_json_object(risk_gate_path, label="risk gate"),
        execution_batch=load_json_object(executions_path, label="executions"),
        position_ledger=load_json_object(ledger_path, label="position ledger"),
        portfolio_state=portfolio_state,
        feedback_readiness=feedback_readiness,
        source_evidence_refresh_ledger=None,
        generated_at=generated_at,
    )
    summary = build_paper_strategy_evaluation_summary(
        strategy_ledger=strategy_ledger,
        feedback_readiness=feedback_readiness,
        portfolio_state=portfolio_state,
        generated_at=generated_at,
    )
    write_json(out_ledger_json_path, strategy_ledger)
    write_text(out_ledger_md_path, render_paper_strategy_evaluation_ledger_markdown(strategy_ledger))
    write_json(out_summary_json_path, summary)
    write_text(out_summary_md_path, render_paper_strategy_evaluation_summary_markdown(summary))
    return strategy_ledger, summary


def render_paper_strategy_evaluation_ledger_markdown(ledger: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Strategy Evaluation Ledger",
        "",
        "- Paper-only analysis ledger; no live trading instruction is produced.",
        f"- Records: {ledger.get('record_count')}",
        f"- Filled paper records: {ledger.get('filled_record_count')}",
        f"- Unresolved paper exposure: `${ledger.get('unresolved_paper_exposure_usd')}`",
        f"- Unresolved PnL invented: `{str(not ledger.get('unresolved_pnl_not_invented')).lower()}`",
        "",
        "## Records",
        "",
    ]
    for record in mapping_rows(ledger.get("records")):
        risk = dict(record.get("risk_gate_result", {}))
        fill = dict(record.get("fill", {}))
        impact = dict(record.get("portfolio_exposure_impact", {}))
        lines.extend(
            [
                f"### `{record.get('market_id')}`",
                "",
                f"- Record: `{record.get('evaluation_record_id')}`",
                f"- Hypothesis: `{record.get('hypothesis_id')}`",
                f"- Paper action type: `{record.get('simulated_action_type')}`",
                f"- Risk gate: `{risk.get('risk_gate_status')}`",
                f"- Simulated fill: `{str(record.get('simulated_fill')).lower()}`",
                f"- Fill status: `{fill.get('execution_status')}`",
                f"- Open position exposure: `${impact.get('open_position_exposure_usd')}`",
                f"- Exposure delta this run: `${impact.get('paper_exposure_delta_usd')}`",
                f"- Outcome status: `{record.get('outcome_status')}`",
                f"- PnL note: {record.get('pnl_note')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Missing Future Evaluation Data",
            "",
            *bullet_lines(str(item) for item in ledger.get("missing_future_evaluation_data", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def render_paper_strategy_evaluation_summary_markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Paper Strategy Evaluation Summary",
            "",
            f"- Readiness: `{summary.get('performance_readiness_status')}`",
            f"- Unresolved paper exposure: `${summary.get('unresolved_paper_exposure_usd')}`",
            f"- Feedback ready: {summary.get('feedback_ready_count')}",
            f"- Blocked feedback: {summary.get('blocked_feedback_count')}",
            f"- Paper realized PnL: `{summary.get('paper_realized_pnl_usd')}`",
            f"- Paper unrealized PnL: `{summary.get('paper_unrealized_pnl_usd')}`",
            f"- Unresolved PnL not invented: `{str(summary.get('unresolved_pnl_not_invented')).lower()}`",
            "",
            "## Waiting Hypotheses",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('hypothesis_id')}`"
                for row in summary.get("hypotheses_waiting_for_outcome_resolution", [])
            ),
            "",
            "## Missing Future Evaluation Data",
            "",
            *bullet_lines(str(item) for item in summary.get("missing_future_evaluation_data", [])),
            "",
            "## Next Operator Action",
            "",
            f"- {summary.get('next_operator_action')}",
        ]
    ) + "\n"


def _strategy_record(
    *,
    candidate: Mapping[str, Any],
    risk_result: Mapping[str, Any],
    execution: Mapping[str, Any],
    position: Mapping[str, Any],
    run_id: str,
    run_date: str,
    generated_at: str,
    exposure_by_market: Mapping[str, Any],
    total_unresolved_exposure_usd: float,
    feedback_readiness: Mapping[str, Any],
    source_evidence_refresh_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    market_id = clean_text(candidate.get("market_id"))
    intent_id = clean_text(candidate.get("intent_id"))
    simulated_fill = execution.get("simulated_fill") is True
    idempotency_status = clean_text(execution.get("idempotency_status"))
    open_position_exposure = float(position.get("paper_exposure_usd", 0) or 0)
    paper_exposure_delta = (
        float(execution.get("filled_notional_usd", 0) or 0)
        if simulated_fill and idempotency_status in {"newly_applied", "not_applied", ""}
        else 0.0
    )
    outcome_status = clean_text(position.get("outcome_status") or "unresolved")
    missing_data = _missing_future_evaluation_data(
        candidate=candidate,
        position=position,
        feedback_readiness=feedback_readiness,
    )
    source_refresh_status = _source_refresh_status_for_market(
        market_id=market_id,
        intent_id=intent_id,
        hypothesis_id=clean_text(candidate.get("hypothesis_id")),
        source_evidence_refresh_ledger=source_evidence_refresh_ledger,
    )
    missing_data.extend(_missing_source_refresh_data(source_refresh_status))
    missing_data = sorted(set(missing_data))
    return {
        "contract_version": PAPER_STRATEGY_EVALUATION_RECORD_CONTRACT,
        "evaluation_record_id": f"paper-strategy-eval-024-{_slug(run_date)}-{_slug(market_id)}-{_slug(intent_id)}",
        "created_at": generated_at,
        "run_id": run_id,
        "run_date": run_date,
        "market_id": market_id,
        "market_title": clean_text(candidate.get("market_title")),
        "hypothesis_id": clean_text(candidate.get("hypothesis_id")),
        "intent_id": intent_id,
        "source_links": {
            "analysis_artifact_path": clean_text(candidate.get("analysis_source_path")),
            "evidence_artifact_paths": [clean_text(item) for item in candidate.get("evidence_source_paths", [])],
        },
        "source_evidence_refresh": source_refresh_status,
        "simulated_action_type": clean_text(candidate.get("paper_action_type")),
        "simulated_price_usd": execution.get("paper_fill_price_usd"),
        "simulated_size_units": execution.get("paper_units") if simulated_fill else None,
        "simulated_notional_usd": float(execution.get("filled_notional_usd", 0) or 0),
        "simulated_fill": simulated_fill,
        "risk_gate_result": {
            "gate_result_id": clean_text(risk_result.get("gate_result_id")),
            "risk_gate_status": clean_text(risk_result.get("risk_gate_status")),
            "allowed": risk_result.get("allowed") is True,
            "blocked": risk_result.get("blocked") is True,
            "block_reasons": [clean_text(item) for item in risk_result.get("block_reasons", [])],
            "warnings": [clean_text(item) for item in risk_result.get("warnings", [])],
        },
        "fill": {
            "execution_id": clean_text(execution.get("execution_id")),
            "execution_status": clean_text(execution.get("execution_status")),
            "execution_reason": clean_text(execution.get("execution_reason")),
            "idempotency_key": clean_text(execution.get("idempotency_key")),
            "idempotency_status": idempotency_status,
            "filled_notional_usd": float(execution.get("filled_notional_usd", 0) or 0),
            "paper_fill_price_usd": execution.get("paper_fill_price_usd"),
            "paper_units": float(execution.get("paper_units", 0) or 0),
        },
        "position": {
            "position_id": clean_text(position.get("position_id")),
            "source_execution_id": clean_text(position.get("source_execution_id")),
            "outcome_status": outcome_status,
            "paper_exposure_usd": open_position_exposure,
            "realized_pnl_usd": None,
            "unrealized_pnl_usd": None,
        },
        "portfolio_exposure_impact": {
            "paper_exposure_delta_usd": round(paper_exposure_delta, 2),
            "open_position_exposure_usd": round(open_position_exposure, 2),
            "market_exposure_after_usd": float(exposure_by_market.get(market_id, 0) or 0),
            "total_unresolved_paper_exposure_after_usd": total_unresolved_exposure_usd,
        },
        "outcome_status": outcome_status,
        "evaluation_state": (
            "waiting_for_outcome_resolution" if open_position_exposure > 0 else "no_open_paper_position"
        ),
        "missing_future_evaluation_data": missing_data,
        "realized_pnl_usd": None,
        "unrealized_pnl_usd": None,
        "pnl_note": "No paper PnL is computed until saved local outcome resolution evidence exists.",
        "paper_only": True,
        "analysis_only": True,
        "real_position": False,
        "real_order_submitted": False,
        "wallet_used": False,
        "signing_used": False,
        "trading_endpoint_used": False,
        "live_price_used": False,
    }


def _missing_future_evaluation_data(
    *,
    candidate: Mapping[str, Any],
    position: Mapping[str, Any],
    feedback_readiness: Mapping[str, Any],
) -> list[str]:
    missing = {clean_text(item) for item in candidate.get("missing_evidence", []) if clean_text(item)}
    market_id = clean_text(candidate.get("market_id"))
    blocked_by_market = {
        clean_text(row.get("market_id")): clean_text(row.get("feedback_blocked_reason"))
        for row in mapping_rows(feedback_readiness.get("blocked_items"))
    }
    if clean_text(position.get("outcome_status") or "unresolved") == "unresolved":
        missing.add("saved_local_outcome_resolution")
        missing.add("paper_feedback_after_outcome_resolution")
    if market_id in blocked_by_market:
        missing.add(blocked_by_market[market_id].replace(" ", "_"))
    if not position:
        missing.add("paper_position_not_opened")
    return sorted(missing)


def _hypotheses_waiting_for_resolution(records: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    waiting = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        if record.get("outcome_status") != "unresolved":
            continue
        hypothesis_id = clean_text(record.get("hypothesis_id"))
        if not hypothesis_id:
            continue
        key = (clean_text(record.get("market_id")), hypothesis_id)
        if key in seen:
            continue
        seen.add(key)
        waiting.append(
            {
                "market_id": key[0],
                "hypothesis_id": key[1],
                "market_title": clean_text(record.get("market_title")),
            }
        )
    return waiting


def _source_refresh_status_for_market(
    *,
    market_id: str,
    intent_id: str,
    hypothesis_id: str,
    source_evidence_refresh_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    records = [
        row
        for row in mapping_rows(source_evidence_refresh_ledger.get("records"))
        if clean_text(row.get("market_id")) == market_id
        and (
            not clean_text(row.get("intent_id"))
            or clean_text(row.get("intent_id")) == intent_id
            or clean_text(row.get("hypothesis_id")) == hypothesis_id
        )
    ]
    if not records:
        return {
            "refresh_id": clean_text(source_evidence_refresh_ledger.get("refresh_id")),
            "status": "missing_source_evidence_refresh_record",
            "record_ids": [],
            "fresh_records": 0,
            "stale_records": 0,
            "missing_source_reference_records": 1,
            "pending_approval_records": 0,
            "contradiction_note_records": 0,
            "network_used": False,
        }
    return {
        "refresh_id": clean_text(source_evidence_refresh_ledger.get("refresh_id")),
        "status": "source_evidence_refresh_linked",
        "record_ids": [clean_text(row.get("record_id")) for row in records],
        "fresh_records": len([row for row in records if row.get("freshness_status") == "fresh_enough"]),
        "stale_records": len([row for row in records if row.get("freshness_status") == "stale"]),
        "missing_source_reference_records": len(
            [row for row in records if row.get("source_status") == "missing_source_reference"]
        ),
        "pending_approval_records": len([row for row in records if row.get("source_status") == "pending_operator_approval"]),
        "contradiction_note_records": len(
            [row for row in records if row.get("contradiction_status") == "contradiction_note_present"]
        ),
        "network_used": False,
    }


def _missing_source_refresh_data(source_refresh_status: Mapping[str, Any]) -> list[str]:
    missing: set[str] = set()
    if int(source_refresh_status.get("missing_source_reference_records", 0) or 0) > 0:
        missing.add("saved_public_evidence_packet_missing")
    if int(source_refresh_status.get("pending_approval_records", 0) or 0) > 0:
        missing.add("public_evidence_refresh_pending_operator_approval")
    if int(source_refresh_status.get("stale_records", 0) or 0) > 0:
        missing.add("fresh_public_evidence_refresh_needed")
    if int(source_refresh_status.get("contradiction_note_records", 0) or 0) > 0:
        missing.add("source_contradiction_review_pending")
    return sorted(missing)


def _source_refresh_ledger_summary(source_evidence_refresh_ledger: Mapping[str, Any]) -> dict[str, Any]:
    if not source_evidence_refresh_ledger:
        return {
            "refresh_id": "",
            "quality_ledger_id": "",
            "network_used": False,
            "records": 0,
            "fresh_records": 0,
            "stale_records": 0,
            "missing_source_reference_records": 0,
            "pending_approval_records": 0,
            "contradiction_note_records": 0,
            "markets_with_gaps": 0,
        }
    counts = dict(source_evidence_refresh_ledger.get("summary_counts", {}))
    quality = dict(source_evidence_refresh_ledger.get("quality_ledger", {}))
    quality_counts = dict(quality.get("summary_counts", {}))
    return {
        "refresh_id": clean_text(source_evidence_refresh_ledger.get("refresh_id")),
        "quality_ledger_id": clean_text(quality.get("quality_ledger_id")),
        "network_used": source_evidence_refresh_ledger.get("network_used") is True,
        "records": int(counts.get("records", 0) or 0),
        "fresh_records": int(counts.get("fresh_records", 0) or 0),
        "stale_records": int(counts.get("stale_records", 0) or 0),
        "missing_source_reference_records": int(counts.get("missing_source_reference_records", 0) or 0),
        "pending_approval_records": int(counts.get("pending_approval_records", 0) or 0),
        "contradiction_note_records": int(counts.get("contradiction_note_records", 0) or 0),
        "markets_with_gaps": int(quality_counts.get("markets_with_gaps", 0) or 0),
    }


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _open_position_key(market_id: Any, intent_id: Any) -> str:
    return ":".join([clean_text(market_id), clean_text(intent_id)])


def _slug(value: Any) -> str:
    clean = clean_text(value).replace(":", "-").replace("/", "-").replace("\\", "-")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in clean) or "unknown"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT paper strategy evaluation artifacts.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--risk-gate", default=str(ARTIFACT_DIR / "risk_gate_results.json"))
    parser.add_argument("--executions", default=str(ARTIFACT_DIR / "simulated_execution_results.json"))
    parser.add_argument("--ledger", default=str(ARTIFACT_DIR / "paper_position_ledger.json"))
    parser.add_argument("--portfolio", default=str(ARTIFACT_DIR / "paper_portfolio_state.json"))
    parser.add_argument("--feedback-readiness", default=None)
    parser.add_argument("--out-ledger-json", default=str(ARTIFACT_DIR / "paper_strategy_evaluation_ledger.json"))
    parser.add_argument("--out-ledger-md", default=str(ARTIFACT_DIR / "paper_strategy_evaluation_ledger.md"))
    parser.add_argument("--out-summary-json", default=str(ARTIFACT_DIR / "paper_strategy_evaluation_summary.json"))
    parser.add_argument("--out-summary-md", default=str(ARTIFACT_DIR / "paper_strategy_evaluation_summary.md"))
    args = parser.parse_args(argv)
    run_paper_strategy_evaluation(
        candidates_path=args.candidates,
        risk_gate_path=args.risk_gate,
        executions_path=args.executions,
        ledger_path=args.ledger,
        portfolio_path=args.portfolio,
        feedback_readiness_path=args.feedback_readiness,
        out_ledger_json_path=args.out_ledger_json,
        out_ledger_md_path=args.out_ledger_md,
        out_summary_json_path=args.out_summary_json,
        out_summary_md_path=args.out_summary_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

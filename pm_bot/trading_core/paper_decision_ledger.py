from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.operator_runner.public_market_paper_loop import public_market_paper_loop_artifact_paths
from pm_bot.trading_core.paper_canary_drill import paper_canary_artifact_paths
from pm_bot.trading_core.paper_decision_ledger_models import (
    EVIDENCE_DECISION_TRACE_CONTRACT,
    OPERATOR_REVIEW_PENDING,
    OUTCOME_INCOMPLETE_ARTIFACTS,
    OUTCOME_NO_SIGNAL,
    OUTCOME_PAPER_INTENT_REVIEW_READY,
    OUTCOME_RISK_BLOCKED,
    RUN_SOURCE_PAPER_CANARY_052,
    RUN_SOURCE_PAPER_LOOP_053,
    RUN_SOURCE_PUBLIC_MARKET_LOOP_054,
    TASK_ID,
    EvidenceDecisionTrace,
    LatestPaperDecisionLedgerStatus,
    PaperDecisionLedger,
    PaperDecisionLedgerEntry,
    PaperDecisionSummary,
    count_by_outcome,
    paper_decision_safety_flags,
    stable_id,
    validate_paper_decision_ledger,
)
from pm_bot.trading_core.paper_trading_loop import paper_trading_loop_artifact_paths
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/paper_decision_ledger_055")
PAPER_DECISION_INCOMPLETE_ARTIFACTS_CONTRACT = "pmbot_paper_decision_incomplete_artifacts_055.v1"
PAPER_DECISION_LEDGER_RUN_RESULT_CONTRACT = "pmbot_paper_decision_ledger_run_result_055.v1"

SOURCE_LATEST = "latest"
SUPPORTED_SOURCES = (
    SOURCE_LATEST,
    RUN_SOURCE_PUBLIC_MARKET_LOOP_054,
    RUN_SOURCE_PAPER_LOOP_053,
    RUN_SOURCE_PAPER_CANARY_052,
)

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--signing",
    "--sign",
    "--order",
    "--submit",
    "--cancel",
    "--approve-live",
)


def paper_decision_ledger_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "ledger": root / "paper_decision_ledger_055.json",
        "operator_md": root / "paper_decision_ledger_055_operator.md",
        "latest_status": root / "latest_paper_decision_ledger_status_055.json",
        "summary": root / "paper_decision_summary_055.json",
        "trace": root / "paper_decision_trace_055.json",
        "incomplete_artifacts": root / "paper_decision_incomplete_artifacts_055.json",
    }


def run_paper_decision_ledger(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    source: str = SOURCE_LATEST,
    reset_for_test: bool = False,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("paper decision ledger requires --dry-run; live execution is blocked")
    selected_source = clean_text(source) or SOURCE_LATEST
    if selected_source not in SUPPORTED_SOURCES:
        raise ValueError(f"unsupported paper decision ledger source: {selected_source}")

    paths = paper_decision_ledger_artifact_paths(artifact_dir)
    if reset_for_test:
        reset_paper_decision_ledger_artifacts(paths)

    existing_entries = _load_existing_entries(paths["ledger"])
    source_record = _discover_source_artifacts(
        source=selected_source,
        artifact_dir=artifact_dir,
        market=market,
        strategy=strategy,
    )
    entry = _build_ledger_entry(
        source_record=source_record,
        existing_entry_count=len(existing_entries),
        market=market,
        strategy=strategy,
        generated_at=generated_at,
    )
    trace = _build_trace(entry, source_record=source_record, generated_at=generated_at)
    entry["evidence_decision_trace"] = trace

    entries = [*existing_entries, entry]
    ledger = PaperDecisionLedger(entries=tuple(entries), generated_at=generated_at).to_dict()
    if ledger["validation"].get("valid") is not True:
        raise ValueError("; ".join(ledger["validation"].get("errors", [])))
    summary = _build_summary(entry=entry, entries=entries, generated_at=generated_at)
    latest_status = _build_latest_status(
        entry=entry,
        entries=entries,
        paths=paths,
        generated_at=generated_at,
    )
    incomplete = (
        _build_incomplete_artifacts_report(
            source_record=source_record,
            entry=entry,
            paths=paths,
            generated_at=generated_at,
        )
        if entry.get("outcome") == OUTCOME_INCOMPLETE_ARTIFACTS
        else None
    )

    write_json(paths["ledger"], ledger)
    write_json(paths["summary"], summary)
    write_json(paths["trace"], trace)
    write_json(paths["latest_status"], latest_status)
    write_text(paths["operator_md"], render_paper_decision_ledger_markdown(summary, latest_status))
    if incomplete is not None:
        write_json(paths["incomplete_artifacts"], incomplete)
    elif paths["incomplete_artifacts"].exists():
        paths["incomplete_artifacts"].unlink()

    result = {
        "contract_version": PAPER_DECISION_LEDGER_RUN_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": "paper_decision_ledger_completed",
        "ledger_entry": entry,
        "ledger": ledger,
        "summary": summary,
        "trace": trace,
        "latest_status": latest_status,
        "incomplete_artifacts": incomplete,
        "artifact_paths": {key: normalize_path(path) for key, path in paths.items() if key != "root"},
        "generated_at": generated_at,
    }
    result.update(paper_decision_safety_flags())
    return result


def reset_paper_decision_ledger_artifacts(paths: Mapping[str, Path] | None = None) -> None:
    artifact_paths = dict(paths or paper_decision_ledger_artifact_paths())
    for key in ("ledger", "operator_md", "latest_status", "summary", "trace", "incomplete_artifacts"):
        path = Path(artifact_paths[key])
        if path.exists():
            path.unlink()


def render_paper_decision_ledger_telegram_status(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    counts = dict(value.get("count_by_outcome", {}))
    return "\n".join(
        [
            "Paper decision ledger updated.",
            f"Market: {clean_text(value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Last outcome: {clean_text(value.get('last_outcome'))}",
            f"Ledger entries: {value.get('ledger_entry_count')}",
            f"paper_intent_review_ready: {counts.get(OUTCOME_PAPER_INTENT_REVIEW_READY, 0)}",
            f"no_signal: {counts.get(OUTCOME_NO_SIGNAL, 0)}",
            f"risk_blocked: {counts.get(OUTCOME_RISK_BLOCKED, 0)}",
            f"incomplete_artifacts: {counts.get(OUTCOME_INCOMPLETE_ARTIFACTS, 0)}",
            f"Evidence: {clean_text(value.get('evidence_pack_path') or 'not_available')}",
            "Live execution: blocked",
            "Next action: review only",
        ]
    )


def render_paper_decision_ledger_markdown(
    summary: Mapping[str, Any],
    latest_status: Mapping[str, Any],
) -> str:
    value = dict(summary or {})
    status = dict(latest_status or {})
    counts = dict(value.get("count_by_outcome", {}))
    lines = [
        "# PMBOT Paper Decision Ledger 055",
        "",
        f"- Latest run source: `{value.get('latest_run_source')}`",
        f"- Market: `{value.get('market_symbol')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        f"- Source type: `{value.get('source_type')}`",
        f"- Evidence pack path: `{value.get('evidence_pack_path') or 'not_available'}`",
        "",
        "## Decision Summary",
        "",
        f"- Latest outcome: `{value.get('latest_outcome')}`",
        f"- Risk decision: `{value.get('risk_decision')}`",
        f"- No-intent reason: {clean_text(value.get('no_intent_reason') or 'not_available')}",
        f"- Paper intent path: `{value.get('paper_intent_path') or 'not_available'}`",
        f"- No-signal path: `{value.get('no_signal_path') or 'not_available'}`",
        "",
        "## Ledger Counts",
        "",
        f"- Ledger entry count: `{value.get('ledger_entry_count')}`",
        f"- paper_intent_review_ready: `{counts.get(OUTCOME_PAPER_INTENT_REVIEW_READY, 0)}`",
        f"- no_signal: `{counts.get(OUTCOME_NO_SIGNAL, 0)}`",
        f"- risk_blocked: `{counts.get(OUTCOME_RISK_BLOCKED, 0)}`",
        f"- incomplete_artifacts: `{counts.get(OUTCOME_INCOMPLETE_ARTIFACTS, 0)}`",
        "",
        "## Safety",
        "",
        "- live execution blocked",
        "- review-only next action: inspect the linked artifacts; no live action is available",
        f"- Latest status path: `{status.get('latest_ledger_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "paper decision ledger is paper/review-only; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _discover_source_artifacts(
    *,
    source: str,
    artifact_dir: str | Path | None,
    market: str,
    strategy: str,
) -> dict[str, Any]:
    ordered_sources = (
        (RUN_SOURCE_PUBLIC_MARKET_LOOP_054, RUN_SOURCE_PAPER_LOOP_053, RUN_SOURCE_PAPER_CANARY_052)
        if source == SOURCE_LATEST
        else (source,)
    )
    records = [_probe_source(run_source, root) for run_source in ordered_sources for root in _candidate_roots(run_source, artifact_dir)]
    usable = [record for record in records if record["available"]]
    if usable:
        complete = [record for record in usable if not record["missing_artifacts"]]
        return complete[0] if complete else usable[0]
    fallback_source = ordered_sources[0]
    fallback_root = _candidate_roots(fallback_source, artifact_dir)[0]
    record = _probe_source(fallback_source, fallback_root)
    record["market_symbol"] = clean_text(market).upper() or "BTC"
    record["strategy_name"] = clean_text(strategy).lower() or "tiny-momentum"
    return record


def _candidate_roots(run_source: str, artifact_dir: str | Path | None) -> list[Path]:
    if artifact_dir is None:
        return [_default_source_root(run_source)]
    root = Path(artifact_dir)
    names = {
        RUN_SOURCE_PUBLIC_MARKET_LOOP_054: "public_market_paper_loop_054",
        RUN_SOURCE_PAPER_LOOP_053: "paper_trading_loop_053",
        RUN_SOURCE_PAPER_CANARY_052: "paper_canary_drill_052",
    }
    source_name = names[run_source]
    candidates = [
        root,
        root / source_name,
        root.parent / source_name,
    ]
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = normalize_path(candidate)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(candidate)
    return unique


def _default_source_root(run_source: str) -> Path:
    if run_source == RUN_SOURCE_PUBLIC_MARKET_LOOP_054:
        return public_market_paper_loop_artifact_paths()["root"]
    if run_source == RUN_SOURCE_PAPER_LOOP_053:
        return paper_trading_loop_artifact_paths()["root"]
    if run_source == RUN_SOURCE_PAPER_CANARY_052:
        return paper_canary_artifact_paths()["root"]
    raise ValueError(f"unsupported run source: {run_source}")


def _probe_source(run_source: str, root: Path) -> dict[str, Any]:
    if run_source == RUN_SOURCE_PUBLIC_MARKET_LOOP_054:
        return _probe_public_market_loop_054(root)
    if run_source == RUN_SOURCE_PAPER_LOOP_053:
        return _probe_paper_loop_053(root)
    if run_source == RUN_SOURCE_PAPER_CANARY_052:
        return _probe_paper_canary_052(root)
    raise ValueError(f"unsupported run source: {run_source}")


def _probe_public_market_loop_054(root: Path) -> dict[str, Any]:
    paths = public_market_paper_loop_artifact_paths(root)
    loaded = _load_source_json(paths)
    result = dict(loaded.get("result") or {})
    status = dict(loaded.get("latest_status") or {})
    risk = dict(loaded.get("risk") or result.get("risk") or {})
    no_signal = dict(loaded.get("no_signal") or result.get("no_signal") or {})
    intent = dict(loaded.get("order_intent") or result.get("paper_order_intent") or {})
    signal = dict(loaded.get("strategy_signal") or result.get("strategy_signal") or {})
    missing = _missing_paths(
        paths,
        required=("latest_status", "result", "evidence_pack", "normalized_snapshot", "risk"),
    )
    missing.extend(_missing_any_path(paths, keys=("strategy_signal", "no_signal")))
    return _source_record(
        run_source=RUN_SOURCE_PUBLIC_MARKET_LOOP_054,
        root=root,
        paths=paths,
        loaded=loaded,
        missing=missing,
        market=status.get("market") or result.get("market"),
        strategy=status.get("strategy_name") or result.get("strategy_name"),
        snapshot_source=status.get("source") or result.get("source") or status.get("source_type") or result.get("source_type"),
        risk=risk,
        signal=signal,
        no_signal=no_signal,
        intent=intent,
        evidence_key="evidence_pack",
        normalized_key="normalized_snapshot",
    )


def _probe_paper_loop_053(root: Path) -> dict[str, Any]:
    paths = paper_trading_loop_artifact_paths(root)
    loaded = _load_source_json(paths)
    result = dict(loaded.get("result") or {})
    status = dict(loaded.get("latest_status") or {})
    snapshot = dict(loaded.get("market_snapshot") or result.get("snapshot") or {})
    risk = dict(loaded.get("risk") or result.get("risk") or {})
    no_signal = dict(loaded.get("no_signal") or result.get("no_signal") or {})
    intent = dict(loaded.get("order_intent") or result.get("paper_order_intent") or {})
    signal = dict(loaded.get("strategy_signal") or result.get("strategy_signal") or {})
    missing = _missing_paths(
        paths,
        required=("latest_status", "result", "market_snapshot", "risk"),
    )
    missing.extend(_missing_any_path(paths, keys=("strategy_signal", "no_signal")))
    return _source_record(
        run_source=RUN_SOURCE_PAPER_LOOP_053,
        root=root,
        paths=paths,
        loaded=loaded,
        missing=missing,
        market=status.get("market") or result.get("market_symbol"),
        strategy=status.get("strategy_name") or result.get("strategy_name"),
        snapshot_source=snapshot.get("fixture_source") or "fixture_fallback",
        risk=risk,
        signal=signal,
        no_signal=no_signal,
        intent=intent,
        evidence_key="",
        normalized_key="market_snapshot",
    )


def _probe_paper_canary_052(root: Path) -> dict[str, Any]:
    paths = paper_canary_artifact_paths(root)
    loaded = _load_source_json(paths)
    result = dict(loaded.get("result") or {})
    status = dict(loaded.get("latest_status") or {})
    risk = dict(loaded.get("risk_readiness") or result.get("risk_readiness_summary") or {})
    intent = dict(loaded.get("order_intent") or result.get("simulated_paper_order_intent") or {})
    missing = _missing_paths(
        paths,
        required=("latest_status", "result", "normalized_market", "market_snapshot", "risk_readiness", "order_intent"),
    )
    return _source_record(
        run_source=RUN_SOURCE_PAPER_CANARY_052,
        root=root,
        paths=paths,
        loaded=loaded,
        missing=missing,
        market=status.get("market") or result.get("market"),
        strategy="paper-canary-drill",
        snapshot_source="fixture_fallback",
        risk=risk,
        signal={},
        no_signal={},
        intent=intent,
        evidence_key="",
        normalized_key="normalized_market",
    )


def _source_record(
    *,
    run_source: str,
    root: Path,
    paths: Mapping[str, Path],
    loaded: Mapping[str, Any],
    missing: list[str],
    market: Any,
    strategy: Any,
    snapshot_source: Any,
    risk: Mapping[str, Any],
    signal: Mapping[str, Any],
    no_signal: Mapping[str, Any],
    intent: Mapping[str, Any],
    evidence_key: str,
    normalized_key: str,
) -> dict[str, Any]:
    available = any(Path(path).exists() for key, path in paths.items() if key != "root")
    outcome = _derive_outcome(missing=missing, risk=risk, no_signal=no_signal, intent=intent)
    risk_decision = _risk_decision(risk=risk, outcome=outcome)
    return {
        "run_source": run_source,
        "root": normalize_path(root),
        "paths": {key: normalize_path(path) for key, path in paths.items() if key != "root"},
        "loaded": dict(loaded),
        "available": available,
        "missing_artifacts": missing,
        "market_symbol": clean_text(market).upper() or "BTC",
        "strategy_name": clean_text(strategy).lower() or "tiny-momentum",
        "snapshot_source": clean_text(snapshot_source) or "not_available",
        "outcome": outcome,
        "risk_decision": risk_decision,
        "risk_blockers": _risk_blockers(risk, outcome=outcome, missing=missing),
        "no_intent_reason": _no_intent_reason(outcome=outcome, risk=risk, no_signal=no_signal, missing=missing),
        "evidence_key": evidence_key,
        "normalized_key": normalized_key,
        "signal": dict(signal),
        "no_signal": dict(no_signal),
        "risk": dict(risk),
        "intent": dict(intent),
    }


def _build_ledger_entry(
    *,
    source_record: Mapping[str, Any],
    existing_entry_count: int,
    market: str,
    strategy: str,
    generated_at: str,
) -> dict[str, Any]:
    paths = dict(source_record.get("paths", {}))
    normalized_key = clean_text(source_record.get("normalized_key"))
    evidence_key = clean_text(source_record.get("evidence_key"))
    artifact_hashes = _artifact_hashes(source_record)
    sequence = existing_entry_count + 1
    ledger_entry_id = stable_id(
        "paper-decision-ledger-entry-055",
        {
            "sequence": sequence,
            "run_source": source_record.get("run_source"),
            "outcome": source_record.get("outcome"),
            "artifact_hashes": artifact_hashes,
            "created_at_utc": generated_at,
        },
    )
    entry = PaperDecisionLedgerEntry(
        ledger_entry_id=ledger_entry_id,
        run_source=clean_text(source_record.get("run_source")),
        market_symbol=clean_text(source_record.get("market_symbol") or market).upper() or "BTC",
        strategy_name=clean_text(source_record.get("strategy_name") or strategy).lower() or "tiny-momentum",
        snapshot_source=clean_text(source_record.get("snapshot_source") or "not_available"),
        evidence_pack_path=clean_text(paths.get(evidence_key)) if evidence_key else "",
        normalized_snapshot_path=clean_text(paths.get(normalized_key)) if normalized_key else "",
        signal_path=clean_text(paths.get("strategy_signal")),
        risk_path=clean_text(paths.get("risk") or paths.get("risk_readiness")),
        paper_intent_path=clean_text(paths.get("order_intent")) if _path_exists(paths.get("order_intent")) else "",
        no_signal_path=clean_text(paths.get("no_signal")) if _path_exists(paths.get("no_signal")) else "",
        outcome=clean_text(source_record.get("outcome") or OUTCOME_INCOMPLETE_ARTIFACTS),
        risk_decision=clean_text(source_record.get("risk_decision")),
        risk_blockers=tuple(clean_text(item) for item in source_record.get("risk_blockers", [])),
        operator_review_status=OPERATOR_REVIEW_PENDING,
        created_at_utc=generated_at,
        artifact_hashes=artifact_hashes,
    ).to_dict()
    return entry


def _build_trace(
    entry: Mapping[str, Any],
    *,
    source_record: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    paths = dict(source_record.get("paths", {}))
    steps = [
        _trace_step("evidence_snapshot", entry.get("evidence_pack_path"), source_record),
        _trace_step("normalized_market_snapshot", entry.get("normalized_snapshot_path"), source_record),
        _trace_step("strategy_signal_or_no_signal", entry.get("signal_path") or entry.get("no_signal_path"), source_record),
        _trace_step("risk_decision", entry.get("risk_path"), source_record),
        _trace_step("paper_intent_or_no_intent", entry.get("paper_intent_path") or entry.get("no_signal_path"), source_record),
        _trace_step("operator_review_record", paths.get("latest_status"), source_record),
    ]
    trace = EvidenceDecisionTrace(
        ledger_entry_id=clean_text(entry.get("ledger_entry_id")),
        run_source=clean_text(entry.get("run_source")),
        evidence_pack_path=clean_text(entry.get("evidence_pack_path")),
        normalized_snapshot_path=clean_text(entry.get("normalized_snapshot_path")),
        signal_path=clean_text(entry.get("signal_path")),
        risk_path=clean_text(entry.get("risk_path")),
        paper_intent_path=clean_text(entry.get("paper_intent_path")),
        no_signal_path=clean_text(entry.get("no_signal_path")),
        trace_steps=tuple(steps),
        created_at_utc=generated_at,
    ).to_dict()
    trace["contract_version"] = EVIDENCE_DECISION_TRACE_CONTRACT
    return trace


def _build_summary(
    *,
    entry: Mapping[str, Any],
    entries: list[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    summary = PaperDecisionSummary(
        latest_run_source=clean_text(entry.get("run_source")),
        market_symbol=clean_text(entry.get("market_symbol")),
        strategy_name=clean_text(entry.get("strategy_name")),
        source_type=clean_text(entry.get("snapshot_source")),
        latest_outcome=clean_text(entry.get("outcome")),
        risk_decision=clean_text(entry.get("risk_decision")),
        no_intent_reason=_entry_no_intent_reason(entry),
        evidence_pack_path=clean_text(entry.get("evidence_pack_path")),
        paper_intent_path=clean_text(entry.get("paper_intent_path")),
        no_signal_path=clean_text(entry.get("no_signal_path")),
        ledger_entry_count=len(entries),
        count_by_outcome=count_by_outcome(entries),
        created_at_utc=generated_at,
    ).to_dict()
    return summary


def _build_latest_status(
    *,
    entry: Mapping[str, Any],
    entries: list[Mapping[str, Any]],
    paths: Mapping[str, Path],
    generated_at: str,
) -> dict[str, Any]:
    return LatestPaperDecisionLedgerStatus(
        latest_run_source=clean_text(entry.get("run_source")),
        market_symbol=clean_text(entry.get("market_symbol")),
        strategy_name=clean_text(entry.get("strategy_name")),
        source_type=clean_text(entry.get("snapshot_source")),
        last_outcome=clean_text(entry.get("outcome")),
        ledger_entry_count=len(entries),
        count_by_outcome=count_by_outcome(entries),
        evidence_pack_path=clean_text(entry.get("evidence_pack_path")),
        latest_ledger_path=normalize_path(paths["ledger"]),
        summary_path=normalize_path(paths["summary"]),
        trace_path=normalize_path(paths["trace"]),
        operator_markdown_path=normalize_path(paths["operator_md"]),
        created_at_utc=generated_at,
    ).to_dict()


def _build_incomplete_artifacts_report(
    *,
    source_record: Mapping[str, Any],
    entry: Mapping[str, Any],
    paths: Mapping[str, Path],
    generated_at: str,
) -> dict[str, Any]:
    report = {
        "contract_version": PAPER_DECISION_INCOMPLETE_ARTIFACTS_CONTRACT,
        "task_id": TASK_ID,
        "status": OUTCOME_INCOMPLETE_ARTIFACTS,
        "run_source": clean_text(source_record.get("run_source")),
        "ledger_entry_id": clean_text(entry.get("ledger_entry_id")),
        "missing_artifacts": list(source_record.get("missing_artifacts", [])),
        "checked_paths": dict(source_record.get("paths", {})),
        "ledger_path": normalize_path(paths["ledger"]),
        "created_at_utc": generated_at,
        "review_only": True,
        "live_execution_blocked": True,
    }
    report.update(paper_decision_safety_flags())
    return report


def _derive_outcome(
    *,
    missing: Sequence[str],
    risk: Mapping[str, Any],
    no_signal: Mapping[str, Any],
    intent: Mapping[str, Any],
) -> str:
    if missing:
        return OUTCOME_INCOMPLETE_ARTIFACTS
    if no_signal or clean_text(no_signal.get("signal_status")) == OUTCOME_NO_SIGNAL:
        return OUTCOME_NO_SIGNAL
    risk_decision = clean_text(risk.get("risk_decision") or risk.get("risk_decision_status")).upper()
    if risk_decision == "BLOCKED" or risk.get("approved_for_paper_intent") is False:
        return OUTCOME_RISK_BLOCKED
    if intent:
        return OUTCOME_PAPER_INTENT_REVIEW_READY
    return OUTCOME_INCOMPLETE_ARTIFACTS


def _risk_decision(*, risk: Mapping[str, Any], outcome: str) -> str:
    if outcome == OUTCOME_INCOMPLETE_ARTIFACTS:
        return OUTCOME_INCOMPLETE_ARTIFACTS
    return clean_text(risk.get("risk_decision") or risk.get("risk_decision_status") or "not_available")


def _risk_blockers(
    risk: Mapping[str, Any],
    *,
    outcome: str,
    missing: Sequence[str],
) -> list[str]:
    if outcome == OUTCOME_INCOMPLETE_ARTIFACTS:
        return [f"missing artifact: {item}" for item in missing]
    blockers = risk.get("risk_blockers") or risk.get("blockers") or risk.get("top_blocker_reasons")
    if isinstance(blockers, list):
        return [clean_text(item) for item in blockers if clean_text(item)]
    if clean_text(blockers):
        return [clean_text(blockers)]
    return []


def _no_intent_reason(
    *,
    outcome: str,
    risk: Mapping[str, Any],
    no_signal: Mapping[str, Any],
    missing: Sequence[str],
) -> str:
    if outcome == OUTCOME_PAPER_INTENT_REVIEW_READY:
        return "paper intent review record is present"
    if outcome == OUTCOME_NO_SIGNAL:
        return clean_text(no_signal.get("reason") or "strategy produced no signal")
    if outcome == OUTCOME_RISK_BLOCKED:
        return clean_text(risk.get("operator_summary") or "paper risk gate blocked the review intent")
    return "required artifacts missing: " + ", ".join(missing)


def _entry_no_intent_reason(entry: Mapping[str, Any]) -> str:
    trace = dict(entry.get("evidence_decision_trace") or {})
    steps = [dict(step) for step in trace.get("trace_steps", []) if isinstance(step, Mapping)]
    for step in steps:
        if clean_text(step.get("stage")) == "paper_intent_or_no_intent":
            return clean_text(step.get("notes")) or "not_available"
    if clean_text(entry.get("outcome")) == OUTCOME_PAPER_INTENT_REVIEW_READY:
        return "paper intent review record is present"
    return "not_available"


def _trace_step(stage: str, path: Any, source_record: Mapping[str, Any]) -> dict[str, Any]:
    path_text = clean_text(path)
    exists = _path_exists(path_text)
    hashes = dict(source_record.get("artifact_hashes") or _artifact_hashes(source_record))
    path_hash = ""
    for artifact in hashes.values():
        if isinstance(artifact, Mapping) and clean_text(artifact.get("path")) == path_text:
            path_hash = clean_text(artifact.get("sha256"))
            break
    notes = clean_text(source_record.get("no_intent_reason")) if stage == "paper_intent_or_no_intent" else ""
    return {
        "stage": stage,
        "artifact_path": path_text,
        "artifact_present": exists,
        "sha256": path_hash,
        "notes": notes,
        "review_only": True,
        "live_execution_blocked": True,
    }


def _artifact_hashes(source_record: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    paths = dict(source_record.get("paths", {}))
    roles = (
        "latest_status",
        "result",
        "evidence_pack",
        "normalized_snapshot",
        "market_snapshot",
        "normalized_market",
        "strategy_signal",
        "risk",
        "risk_readiness",
        "order_intent",
        "no_signal",
    )
    hashes: dict[str, dict[str, str]] = {}
    for role in roles:
        path = clean_text(paths.get(role))
        if path and _path_exists(path):
            hashes[role] = {"path": path, "sha256": _sha256_file(Path(path))}
    return hashes


def _load_existing_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    ledger = load_json_object(path, label="paper decision ledger")
    validation = validate_paper_decision_ledger(ledger)
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return [dict(row) for row in ledger.get("entries", []) if isinstance(row, Mapping)]


def _load_source_json(paths: Mapping[str, Path]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for key, path in paths.items():
        if key == "root":
            continue
        if Path(path).exists() and Path(path).suffix == ".json":
            loaded[key] = load_json_object(path, label=key)
    return loaded


def _missing_paths(paths: Mapping[str, Path], *, required: Sequence[str]) -> list[str]:
    return [f"{key}:{normalize_path(paths[key])}" for key in required if not Path(paths[key]).exists()]


def _missing_any_path(paths: Mapping[str, Path], *, keys: Sequence[str]) -> list[str]:
    if any(Path(paths[key]).exists() for key in keys):
        return []
    joined = " or ".join(f"{key}:{normalize_path(paths[key])}" for key in keys)
    return [joined]


def _path_exists(path: Any) -> bool:
    return bool(clean_text(path)) and Path(clean_text(path)).exists()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

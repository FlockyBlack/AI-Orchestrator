from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    mapping_rows,
    trading_core_safety_summary,
    write_json,
    write_text,
)

REFRESH_REQUEST_CONTRACT = "pmbot_public_evidence_refresh_request.v1"
REFRESH_RECORD_CONTRACT = "pmbot_public_evidence_refresh_record.v1"
REFRESH_LEDGER_CONTRACT = "pmbot_public_evidence_refresh_ledger.v1"
QUALITY_LEDGER_CONTRACT = "pmbot_public_evidence_quality_ledger.v1"
PENDING_APPROVAL_PACKET_CONTRACT = "pmbot_public_evidence_refresh_pending_approval.v1"

NO_NETWORK_RUN_MODE = "local_dry_run_no_network"
OPERATOR_APPROVED_RUN_MODE = "operator_approved_network_not_executed"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
DEFAULT_FRESHNESS_MAX_AGE_SECONDS = 172800

APPROVED_OPERATOR_STATUSES = {
    "approved",
    "approved_for_scoped_public_read_only_fetch_only",
    "operator_approved_public_read_only_refresh",
}

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "docs/",
    "pm_bot/dashboard/",
    "pm_bot/operator_runner/artifacts/",
    "pm_bot/practical/artifacts/",
    "pm_bot/source_quality/",
    "pm_bot/tests/",
    "tests/",
)
FORBIDDEN_LOCAL_REFERENCE_PREFIXES = (
    ".codex/",
    ".env",
    ".env.",
    ".git/",
    "agent_tasks/running/",
    "dispatcher/",
    "pm_bot/llm/",
    "pm_bot/orders/",
    "pm_bot/wallet/",
    "run_codex/",
    "runtime/",
)
BLOCKED_URL_FRAGMENTS = (
    "api.polymarket",
    "clob.polymarket",
    "gamma-api.polymarket",
    "localhost",
    "127.0.0.1",
)


class PublicEvidenceRefreshError(ValueError):
    pass


def load_public_evidence_refresh_request(path: str | Path) -> dict[str, Any]:
    return _load_json_object(Path(path), label="public evidence refresh request")


def build_public_evidence_refresh_request_from_candidates(
    *,
    candidates_batch: Mapping[str, Any],
    tracked_markets: Sequence[Mapping[str, Any]],
    refresh_id: str | None = None,
    generated_at: str = GENERATED_AT,
    freshness_max_age_seconds: int = DEFAULT_FRESHNESS_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    markets = [
        {
            "market_id": clean_text(market.get("market_id")),
            "market_title": clean_text(market.get("market_title")),
            "outcome_status": clean_text(market.get("outcome_status") or "unknown"),
        }
        for market in tracked_markets
        if clean_text(market.get("market_id"))
    ]
    markets_by_id = {market["market_id"]: market for market in markets}
    sources: list[dict[str, Any]] = []

    for candidate in sorted(
        mapping_rows(candidates_batch.get("candidates")),
        key=lambda row: (clean_text(row.get("market_id")), clean_text(row.get("intent_id"))),
    ):
        market_id = clean_text(candidate.get("market_id"))
        if not market_id:
            continue
        if market_id not in markets_by_id:
            markets_by_id[market_id] = {
                "market_id": market_id,
                "market_title": clean_text(candidate.get("market_title")),
                "outcome_status": "unknown",
            }
        evidence_paths = [
            clean_text(path)
            for path in candidate.get("evidence_source_paths", [])
            if clean_text(path)
        ]
        if evidence_paths:
            for index, reference in enumerate(evidence_paths, start=1):
                sources.append(
                    {
                        "source_id": f"{market_id}.local_saved_public_evidence.{index}",
                        "market_id": market_id,
                        "market_title": clean_text(candidate.get("market_title")),
                        "hypothesis_id": clean_text(candidate.get("hypothesis_id")),
                        "intent_id": clean_text(candidate.get("intent_id")),
                        "source_category": "saved_public_evidence_packet",
                        "source_label": f"Saved public evidence packet {index}",
                        "evidence_role": "paper_strategy_evidence_link",
                        "local_captured_reference": reference,
                        "source_url": "",
                        "freshness_max_age_seconds": freshness_max_age_seconds,
                        "contradiction_notes": [],
                        "evidence_quality_notes": [
                            "Linked from the paper strategy candidate evidence_source_paths list.",
                            "Refresh runner only inspects the saved local artifact in this task.",
                        ],
                    }
                )
            continue

        sources.append(
            {
                "source_id": f"{market_id}.missing_public_evidence_reference",
                "market_id": market_id,
                "market_title": clean_text(candidate.get("market_title")),
                "hypothesis_id": clean_text(candidate.get("hypothesis_id")),
                "intent_id": clean_text(candidate.get("intent_id")),
                "source_category": "public_read_only_source_reference_missing",
                "source_label": "Missing saved public evidence reference",
                "evidence_role": "paper_strategy_evidence_gap",
                "local_captured_reference": "",
                "source_url": "",
                "freshness_max_age_seconds": freshness_max_age_seconds,
                "contradiction_notes": [],
                "evidence_quality_notes": [
                    "No saved public evidence packet is linked to this paper strategy candidate.",
                    *_missing_evidence_notes(candidate),
                ],
            }
        )

    for market_id in sorted(markets_by_id):
        if not any(source["market_id"] == market_id for source in sources):
            market = markets_by_id[market_id]
            sources.append(
                {
                    "source_id": f"{market_id}.missing_public_evidence_reference",
                    "market_id": market_id,
                    "market_title": market["market_title"],
                    "hypothesis_id": "",
                    "intent_id": "",
                    "source_category": "public_read_only_source_reference_missing",
                    "source_label": "Missing saved public evidence reference",
                    "evidence_role": "tracked_market_evidence_gap",
                    "local_captured_reference": "",
                    "source_url": "",
                    "freshness_max_age_seconds": freshness_max_age_seconds,
                    "contradiction_notes": [],
                    "evidence_quality_notes": ["Tracked market has no linked paper strategy evidence record."],
                }
            )

    run_date = clean_text(candidates_batch.get("run_date")) or generated_at[:10]
    return {
        "contract_version": REFRESH_REQUEST_CONTRACT,
        "default_no_network_mode": True,
        "generated_at": generated_at,
        "network_mode": "no_network",
        "operator_approval_reference": "",
        "operator_approval_required": True,
        "reference_timestamp_utc": generated_at,
        "refresh_id": refresh_id or f"public-evidence-refresh-025-{run_date}",
        "run_date": run_date,
        "run_id": clean_text(candidates_batch.get("daily_run_id")),
        "markets": [markets_by_id[market_id] for market_id in sorted(markets_by_id)],
        "sources": sorted(sources, key=lambda row: (row["market_id"], row["source_id"])),
    }


def build_public_evidence_refresh_artifacts(request: Mapping[str, Any]) -> dict[str, Any]:
    validation_errors = validate_public_evidence_refresh_request(request)
    if validation_errors:
        raise PublicEvidenceRefreshError("; ".join(validation_errors))

    approval = _load_operator_approval(request)
    reference_timestamp = clean_text(request.get("reference_timestamp_utc"))
    records = [
        _build_refresh_record(
            refresh_id=clean_text(request.get("refresh_id")),
            source=source,
            reference_timestamp=reference_timestamp,
            approval=approval,
        )
        for source in mapping_rows(request.get("sources"))
    ]
    records = sorted(records, key=lambda row: (row["market_id"], row["record_id"]))
    quality_ledger = _build_quality_ledger(request=request, records=records)
    pending_approval_packet = _build_pending_approval_packet(request=request, records=records, approval=approval)
    ledger = {
        "build_id": _build_deterministic_id(clean_text(request.get("refresh_id")), request, records, quality_ledger),
        "contract_version": REFRESH_LEDGER_CONTRACT,
        "default_no_network_mode": request.get("default_no_network_mode") is True,
        "errors": [],
        "external_api_calls_performed": False,
        "generated_at": clean_text(request.get("generated_at")),
        "network_mode": clean_text(request.get("network_mode")),
        "network_used": False,
        "operator_approval": approval,
        "operator_review_required": True,
        "outcome_resolution_invented": False,
        "paper_only": True,
        "pending_approval_packet": pending_approval_packet,
        "pending_approval_packet_ready": pending_approval_packet is not None,
        "pnl_invented": False,
        "quality_ledger": quality_ledger,
        "records": records,
        "refresh_id": clean_text(request.get("refresh_id")),
        "run_date": clean_text(request.get("run_date")),
        "run_id": clean_text(request.get("run_id")),
        "run_mode": _run_mode(request, approval),
        "safety_summary": _refresh_safety_summary(),
        "summary_counts": _refresh_summary_counts(records, pending_approval_packet),
        "warnings": [],
    }
    return {
        "ledger": ledger,
        "quality_ledger": quality_ledger,
        "pending_approval_packet": pending_approval_packet,
    }


def validate_public_evidence_refresh_request(request: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "default_no_network_mode",
        "generated_at",
        "network_mode",
        "operator_approval_reference",
        "operator_approval_required",
        "reference_timestamp_utc",
        "refresh_id",
        "run_date",
        "markets",
        "sources",
    )
    for field in required_fields:
        if field not in request:
            errors.append(f"{field} is required")
    if request.get("contract_version") != REFRESH_REQUEST_CONTRACT:
        errors.append(f"contract_version must be {REFRESH_REQUEST_CONTRACT}")
    if request.get("default_no_network_mode") is not True:
        errors.append("default_no_network_mode must be true")
    if request.get("operator_approval_required") is not True:
        errors.append("operator_approval_required must be true")
    if request.get("network_mode") not in {"no_network", "operator_approved"}:
        errors.append("network_mode must be no_network or operator_approved")
    for field in ("generated_at", "reference_timestamp_utc"):
        timestamp = request.get(field)
        if not isinstance(timestamp, str) or not timestamp:
            errors.append(f"{field} must be a non-empty UTC timestamp")
        else:
            try:
                _parse_utc_timestamp(timestamp)
            except ValueError as exc:
                errors.append(f"{field} must be an ISO-8601 UTC timestamp ending in Z: {exc}")
    approval_reference = clean_text(request.get("operator_approval_reference"))
    if approval_reference:
        errors.extend(_validate_local_reference(approval_reference, "operator_approval_reference"))
    if request.get("network_mode") == "operator_approved" and not approval_reference:
        errors.append("operator_approval_reference is required when network_mode is operator_approved")

    markets = request.get("markets")
    if not isinstance(markets, list) or not markets:
        errors.append("markets must be a non-empty list")
    else:
        errors.extend(_validate_markets(markets))
    sources = request.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
    else:
        market_ids = {
            clean_text(market.get("market_id"))
            for market in markets
            if isinstance(market, Mapping)
        }
        errors.extend(_validate_sources(sources, market_ids))
    return errors


def validate_public_evidence_refresh_ledger(ledger: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = (
        "build_id",
        "contract_version",
        "default_no_network_mode",
        "external_api_calls_performed",
        "network_used",
        "operator_approval",
        "outcome_resolution_invented",
        "pending_approval_packet_ready",
        "pnl_invented",
        "quality_ledger",
        "records",
        "refresh_id",
        "run_mode",
        "safety_summary",
        "summary_counts",
    )
    for field in required_fields:
        if field not in ledger:
            errors.append(f"{field} is required")
    if ledger.get("contract_version") != REFRESH_LEDGER_CONTRACT:
        errors.append(f"contract_version must be {REFRESH_LEDGER_CONTRACT}")
    for field in ("default_no_network_mode", "operator_review_required", "paper_only"):
        if ledger.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in ("external_api_calls_performed", "network_used", "outcome_resolution_invented", "pnl_invented"):
        if ledger.get(field) is not False:
            errors.append(f"{field} must be false")
    records = ledger.get("records")
    if not isinstance(records, list) or not records:
        errors.append("records must be a non-empty list")
    else:
        errors.extend(_validate_refresh_records(records, clean_text(ledger.get("refresh_id"))))
    quality_ledger = ledger.get("quality_ledger")
    if not isinstance(quality_ledger, Mapping):
        errors.append("quality_ledger must be an object")
    else:
        errors.extend(validate_public_evidence_quality_ledger(quality_ledger))
    if isinstance(records, list):
        expected = _refresh_summary_counts(
            [row for row in records if isinstance(row, Mapping)],
            ledger.get("pending_approval_packet") if isinstance(ledger.get("pending_approval_packet"), Mapping) else None,
        )
        if ledger.get("summary_counts") != expected:
            errors.append("summary_counts must match refresh records")
    return errors


def validate_public_evidence_quality_ledger(quality_ledger: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "freshness_status_counts",
        "market_source_status",
        "missing_evidence_gaps",
        "network_used",
        "quality_ledger_id",
        "source_record_count",
        "summary_counts",
    )
    for field in required_fields:
        if field not in quality_ledger:
            errors.append(f"quality_ledger.{field} is required")
    if quality_ledger.get("contract_version") != QUALITY_LEDGER_CONTRACT:
        errors.append(f"quality_ledger.contract_version must be {QUALITY_LEDGER_CONTRACT}")
    if quality_ledger.get("network_used") is not False:
        errors.append("quality_ledger.network_used must be false")
    market_rows = quality_ledger.get("market_source_status")
    if not isinstance(market_rows, list):
        errors.append("quality_ledger.market_source_status must be a list")
    gaps = quality_ledger.get("missing_evidence_gaps")
    if not isinstance(gaps, list):
        errors.append("quality_ledger.missing_evidence_gaps must be a list")
    return errors


def write_public_evidence_refresh_artifacts(
    *,
    request: Mapping[str, Any],
    out_dir: str | Path,
) -> dict[str, Any]:
    artifacts = build_public_evidence_refresh_artifacts(request)
    out_path = Path(out_dir)
    write_json(out_path / "public_evidence_refresh_request.json", request)
    write_json(out_path / "public_evidence_refresh_ledger.json", artifacts["ledger"])
    write_json(out_path / "public_evidence_quality_ledger.json", artifacts["quality_ledger"])
    write_text(out_path / "public_evidence_refresh_report.md", render_public_evidence_refresh_report(artifacts["ledger"]))
    if artifacts["pending_approval_packet"] is not None:
        write_json(out_path / "public_evidence_refresh_pending_approval_packet.json", artifacts["pending_approval_packet"])
        write_text(
            out_path / "public_evidence_refresh_pending_approval_packet.md",
            render_pending_approval_packet(artifacts["pending_approval_packet"]),
        )
    return artifacts


def render_public_evidence_refresh_report(ledger: Mapping[str, Any]) -> str:
    quality = dict(ledger.get("quality_ledger", {}))
    counts = dict(ledger.get("summary_counts", {}))
    lines = [
        "# PMBOT Public Evidence Refresh",
        "",
        f"- Refresh: `{ledger.get('refresh_id')}`",
        f"- Run mode: `{ledger.get('run_mode')}`",
        f"- Network used: `{str(ledger.get('network_used')).lower()}`",
        f"- Records: {counts.get('records')}",
        f"- Local captures ingested: {counts.get('local_captured_references')}",
        f"- Source URLs pending approval: {counts.get('pending_approval_records')}",
        f"- Missing source gaps: {counts.get('missing_source_reference_records')}",
        f"- Stale records: {counts.get('stale_records')}",
        "",
        "## Market Source Status",
        "",
    ]
    for row in quality.get("market_source_status", []):
        lines.append(
            f"- `{row.get('market_id')}` status `{row.get('gap_status')}`; "
            f"local records {row.get('local_captured_reference_count')}; "
            f"missing gaps {row.get('missing_source_reference_count')}; "
            f"stale {row.get('stale_count')}"
        )
    lines.extend(
        [
            "",
            "## Missing Evidence Gaps",
            "",
            *bullet_lines(
                f"`{gap.get('market_id')}` {gap.get('gap_type')}: {gap.get('notes')}"
                for gap in quality.get("missing_evidence_gaps", [])
            ),
            "",
            "## Safety",
            "",
            "- Default mode is local dry run with no network.",
            "- Source URLs without an approval artifact create a pending approval packet.",
            "- No outcome resolution, PnL, wallet, signing, order, authenticated endpoint, or runtime action is produced.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_pending_approval_packet(packet: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Public Evidence Refresh Pending Approval",
            "",
            f"- Packet: `{packet.get('approval_packet_id')}`",
            f"- Refresh: `{packet.get('refresh_id')}`",
            f"- Requested source URLs: {packet.get('requested_source_url_count')}",
            f"- Operator approval granted: `{str(packet.get('operator_approval_granted')).lower()}`",
            f"- Network used: `{str(packet.get('network_used')).lower()}`",
            "",
            "## Requested Sources",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('source_category')}` {row.get('source_url')}"
                for row in packet.get("requested_sources", [])
            ),
            "",
            "## Blocked Scope",
            "",
            *bullet_lines(packet.get("blocked_scope", [])),
        ]
    ) + "\n"


def _validate_markets(markets: Sequence[Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, market in enumerate(markets):
        path = f"markets[{index}]"
        if not isinstance(market, Mapping):
            errors.append(f"{path} must be an object")
            continue
        market_id = clean_text(market.get("market_id"))
        if not market_id:
            errors.append(f"{path}.market_id is required")
        elif market_id in seen:
            errors.append(f"{path}.market_id duplicates an earlier market")
        seen.add(market_id)
        if not clean_text(market.get("market_title")):
            errors.append(f"{path}.market_title is required")
    return errors


def _validate_sources(sources: Sequence[Any], market_ids: set[str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    required_fields = (
        "source_id",
        "market_id",
        "source_category",
        "source_label",
        "evidence_role",
        "freshness_max_age_seconds",
        "contradiction_notes",
        "evidence_quality_notes",
    )
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, Mapping):
            errors.append(f"{path} must be an object")
            continue
        for field in required_fields:
            if field not in source:
                errors.append(f"{path}.{field} is required")
        source_id = clean_text(source.get("source_id"))
        if not source_id:
            errors.append(f"{path}.source_id is required")
        elif source_id in seen:
            errors.append(f"{path}.source_id duplicates an earlier source")
        seen.add(source_id)
        market_id = clean_text(source.get("market_id"))
        if not market_id:
            errors.append(f"{path}.market_id is required")
        elif market_ids and market_id not in market_ids:
            errors.append(f"{path}.market_id must exist in markets")
        for field in ("source_category", "source_label", "evidence_role"):
            if not clean_text(source.get(field)):
                errors.append(f"{path}.{field} is required")
        local_reference = clean_text(source.get("local_captured_reference"))
        source_url = clean_text(source.get("source_url"))
        if local_reference:
            errors.extend(_validate_local_reference(local_reference, f"{path}.local_captured_reference"))
        if source_url:
            errors.extend(_validate_public_source_url(source_url, f"{path}.source_url"))
        max_age = source.get("freshness_max_age_seconds")
        if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age <= 0:
            errors.append(f"{path}.freshness_max_age_seconds must be a positive integer")
        if not isinstance(source.get("contradiction_notes"), list) or not all(
            isinstance(item, str) for item in source.get("contradiction_notes", [])
        ):
            errors.append(f"{path}.contradiction_notes must be a list of strings")
        if not isinstance(source.get("evidence_quality_notes"), list) or not all(
            isinstance(item, str) for item in source.get("evidence_quality_notes", [])
        ):
            errors.append(f"{path}.evidence_quality_notes must be a list of strings")
    return errors


def _build_refresh_record(
    *,
    refresh_id: str,
    source: Mapping[str, Any],
    reference_timestamp: str,
    approval: Mapping[str, Any],
) -> dict[str, Any]:
    local_reference = _normalize_reference(clean_text(source.get("local_captured_reference")))
    source_url = clean_text(source.get("source_url"))
    loaded: dict[str, Any] = {}
    local_reference_status = "not_provided"
    if local_reference:
        local_path = Path(local_reference)
        if local_path.exists():
            local_reference_status = "loaded"
            loaded = _load_json_object(local_path, label=f"local captured reference {local_reference}")
        else:
            local_reference_status = "missing"

    captured_at = _first_text(source.get("captured_at"), loaded.get("captured_at"), loaded.get("generated_at"))
    fetched_at = _first_text(source.get("fetched_at"), loaded.get("fetched_at"))
    source_reference = _first_text(source_url, loaded.get("source_reference"), loaded.get("final_url"))
    contradiction_notes = [
        clean_text(item)
        for item in list(source.get("contradiction_notes", [])) + list(loaded.get("contradiction_candidates", []))
        if clean_text(item)
    ]
    quality_notes = [
        clean_text(item)
        for item in list(source.get("evidence_quality_notes", []))
        + list(loaded.get("limitations", []))
        + list(loaded.get("capture_errors", []))
        if clean_text(item)
    ]
    freshness_status = _freshness_status(
        captured_at=captured_at,
        fetched_at=fetched_at,
        loaded_freshness_status=clean_text(loaded.get("freshness_status")),
        max_age_seconds=int(source.get("freshness_max_age_seconds") or DEFAULT_FRESHNESS_MAX_AGE_SECONDS),
        reference_timestamp=reference_timestamp,
        source_reference_present=bool(local_reference or source_url),
        local_reference_status=local_reference_status,
    )
    contradiction_status = "contradiction_note_present" if contradiction_notes else "no_contradiction_noted"
    source_status = _source_status(
        local_reference=local_reference,
        source_url=source_url,
        local_reference_status=local_reference_status,
        approval=approval,
    )
    market_id = clean_text(source.get("market_id"))
    source_id = clean_text(source.get("source_id"))
    return {
        "captured_at": captured_at or None,
        "contract_version": REFRESH_RECORD_CONTRACT,
        "contradiction_notes": contradiction_notes,
        "contradiction_status": contradiction_status,
        "evidence_quality_notes": quality_notes,
        "evidence_role": clean_text(source.get("evidence_role")),
        "fetched_at": fetched_at or None,
        "freshness_max_age_seconds": int(source.get("freshness_max_age_seconds") or DEFAULT_FRESHNESS_MAX_AGE_SECONDS),
        "freshness_status": freshness_status,
        "hypothesis_id": clean_text(source.get("hypothesis_id")),
        "intent_id": clean_text(source.get("intent_id")),
        "local_captured_reference": local_reference,
        "local_reference_status": local_reference_status,
        "market_id": market_id,
        "market_title": clean_text(source.get("market_title")),
        "network_used": False,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_id": f"{refresh_id}.{market_id}.{source_id}.refresh_record",
        "source_category": _first_text(source.get("source_category"), loaded.get("source_category")),
        "source_id": source_id,
        "source_label": clean_text(source.get("source_label")),
        "source_status": source_status,
        "source_url": source_reference,
    }


def _build_quality_ledger(*, request: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    market_rows = []
    markets = {
        clean_text(market.get("market_id")): market
        for market in mapping_rows(request.get("markets"))
    }
    for market_id in sorted(markets):
        market_records = [record for record in records if record.get("market_id") == market_id]
        missing_count = len([row for row in market_records if row.get("source_status") == "missing_source_reference"])
        pending_count = len([row for row in market_records if row.get("source_status") == "pending_operator_approval"])
        stale_count = len([row for row in market_records if row.get("freshness_status") == "stale"])
        contradiction_count = len(
            [row for row in market_records if row.get("contradiction_status") == "contradiction_note_present"]
        )
        local_count = len([row for row in market_records if row.get("local_reference_status") == "loaded"])
        gap_status = "covered_with_local_evidence" if local_count and not missing_count and not pending_count else "gaps_present"
        market_rows.append(
            {
                "contradiction_note_count": contradiction_count,
                "fresh_count": len([row for row in market_records if row.get("freshness_status") == "fresh_enough"]),
                "gap_status": gap_status,
                "local_captured_reference_count": local_count,
                "market_id": market_id,
                "market_title": clean_text(markets[market_id].get("market_title")),
                "missing_source_reference_count": missing_count,
                "pending_approval_count": pending_count,
                "source_record_ids": [clean_text(row.get("record_id")) for row in market_records],
                "stale_count": stale_count,
                "total_source_records": len(market_records),
            }
        )
    gaps = _missing_evidence_gaps(records)
    return {
        "contract_version": QUALITY_LEDGER_CONTRACT,
        "freshness_status_counts": _count_by(records, "freshness_status"),
        "generated_at": clean_text(request.get("generated_at")),
        "market_source_status": market_rows,
        "missing_evidence_gaps": gaps,
        "network_used": False,
        "operator_review_required": True,
        "quality_ledger_id": f"{request.get('refresh_id')}.quality_ledger",
        "source_record_count": len(records),
        "summary_counts": {
            "contradiction_note_records": len(
                [row for row in records if row.get("contradiction_status") == "contradiction_note_present"]
            ),
            "fresh_records": len([row for row in records if row.get("freshness_status") == "fresh_enough"]),
            "local_captured_references": len([row for row in records if row.get("local_reference_status") == "loaded"]),
            "markets_with_gaps": len([row for row in market_rows if row["gap_status"] == "gaps_present"]),
            "missing_evidence_gaps": len(gaps),
            "missing_source_reference_records": len(
                [row for row in records if row.get("source_status") == "missing_source_reference"]
            ),
            "pending_approval_records": len(
                [row for row in records if row.get("source_status") == "pending_operator_approval"]
            ),
            "source_records": len(records),
            "stale_records": len([row for row in records if row.get("freshness_status") == "stale"]),
        },
    }


def _build_pending_approval_packet(
    *,
    request: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    approval: Mapping[str, Any],
) -> dict[str, Any] | None:
    pending = [
        record
        for record in records
        if record.get("source_status") == "pending_operator_approval"
        and clean_text(record.get("source_url"))
    ]
    if not pending:
        return None
    refresh_id = clean_text(request.get("refresh_id"))
    requested_sources = [
        {
            "evidence_role": record.get("evidence_role"),
            "market_id": record.get("market_id"),
            "market_title": record.get("market_title"),
            "source_category": record.get("source_category"),
            "source_id": record.get("source_id"),
            "source_url": record.get("source_url"),
        }
        for record in pending
    ]
    return {
        "approval_packet_id": f"{refresh_id}.pending_network_approval",
        "blocked_scope": [
            "authenticated endpoints",
            "credentials, cookies, browser sessions, or private API keys",
            "wallet, private key, signing, order, custody, or settlement paths",
            "autonomous execution, scheduler, daemon, watcher, or polling loop",
            "runtime dispatcher changes",
            "live market action instructions or executable market output",
        ],
        "contract_version": PENDING_APPROVAL_PACKET_CONTRACT,
        "created_at": clean_text(request.get("generated_at")),
        "default_no_network_mode": True,
        "network_used": False,
        "operator_approval": approval,
        "operator_approval_granted": False,
        "operator_approval_required": True,
        "refresh_id": refresh_id,
        "requested_source_url_count": len(requested_sources),
        "requested_sources": requested_sources,
        "safety_summary": _refresh_safety_summary(),
    }


def _refresh_summary_counts(
    records: Sequence[Mapping[str, Any]],
    pending_approval_packet: Mapping[str, Any] | None,
) -> dict[str, int]:
    return {
        "contradiction_note_records": len(
            [row for row in records if row.get("contradiction_status") == "contradiction_note_present"]
        ),
        "fresh_records": len([row for row in records if row.get("freshness_status") == "fresh_enough"]),
        "local_captured_references": len([row for row in records if row.get("local_reference_status") == "loaded"]),
        "missing_source_reference_records": len(
            [row for row in records if row.get("source_status") == "missing_source_reference"]
        ),
        "pending_approval_packet_count": 1 if pending_approval_packet is not None else 0,
        "pending_approval_records": len(
            [row for row in records if row.get("source_status") == "pending_operator_approval"]
        ),
        "records": len(records),
        "stale_records": len([row for row in records if row.get("freshness_status") == "stale"]),
    }


def _missing_evidence_gaps(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for record in records:
        if record.get("source_status") == "missing_source_reference":
            gaps.append(
                {
                    "gap_type": "missing_source_reference",
                    "market_id": record.get("market_id"),
                    "record_id": record.get("record_id"),
                    "notes": "No source_url or local_captured_reference is available for this market record.",
                }
            )
        elif record.get("source_status") == "pending_operator_approval":
            gaps.append(
                {
                    "gap_type": "pending_operator_approval",
                    "market_id": record.get("market_id"),
                    "record_id": record.get("record_id"),
                    "notes": "A source_url exists, but the refresh task has no explicit approval artifact.",
                }
            )
        elif record.get("freshness_status") == "stale":
            gaps.append(
                {
                    "gap_type": "stale_source_evidence",
                    "market_id": record.get("market_id"),
                    "record_id": record.get("record_id"),
                    "notes": "Local captured evidence is outside the configured freshness window or marked stale.",
                }
            )
    return gaps


def _source_status(
    *,
    local_reference: str,
    source_url: str,
    local_reference_status: str,
    approval: Mapping[str, Any],
) -> str:
    if local_reference:
        return "local_reference_ingested" if local_reference_status == "loaded" else "local_reference_missing"
    if source_url:
        return "source_url_waiting_for_refresh" if approval.get("operator_approval_granted") is True else "pending_operator_approval"
    return "missing_source_reference"


def _freshness_status(
    *,
    captured_at: str,
    fetched_at: str,
    loaded_freshness_status: str,
    max_age_seconds: int,
    reference_timestamp: str,
    source_reference_present: bool,
    local_reference_status: str,
) -> str:
    if not source_reference_present:
        return "missing_source_reference"
    if local_reference_status == "missing":
        return "missing_local_capture"
    if loaded_freshness_status == "stale":
        return "stale"
    timestamp = captured_at or fetched_at
    if not timestamp:
        return "unknown_missing_capture_time"
    try:
        observed = _parse_utc_timestamp(timestamp)
        reference = _parse_utc_timestamp(reference_timestamp)
    except ValueError:
        return "unknown_invalid_capture_time"
    age_seconds = int((reference - observed).total_seconds())
    if age_seconds < 0:
        return "unknown_future_capture_time"
    return "stale" if age_seconds > max_age_seconds else "fresh_enough"


def _load_operator_approval(request: Mapping[str, Any]) -> dict[str, Any]:
    reference = _normalize_reference(clean_text(request.get("operator_approval_reference")))
    if not reference:
        return {
            "approval_reference": "",
            "operator_approval_granted": False,
            "approval_status": "missing",
            "approval_valid_for_refresh": False,
        }
    approval = _load_json_object(Path(reference), label="operator approval")
    status = clean_text(approval.get("approval_status"))
    approved = status in APPROVED_OPERATOR_STATUSES
    return {
        "approval_reference": reference,
        "operator_approval_granted": approved,
        "approval_status": status,
        "approval_valid_for_refresh": approved,
        "approved_at": approval.get("approved_at"),
        "approved_by": approval.get("approved_by"),
    }


def _run_mode(request: Mapping[str, Any], approval: Mapping[str, Any]) -> str:
    if request.get("network_mode") == "operator_approved" and approval.get("operator_approval_granted") is True:
        return OPERATOR_APPROVED_RUN_MODE
    return NO_NETWORK_RUN_MODE


def _validate_refresh_records(records: Sequence[Any], refresh_id: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        path = f"records[{index}]"
        if not isinstance(record, Mapping):
            errors.append(f"{path} must be an object")
            continue
        required_fields = (
            "captured_at",
            "contract_version",
            "contradiction_status",
            "evidence_quality_notes",
            "fetched_at",
            "freshness_status",
            "local_captured_reference",
            "market_id",
            "network_used",
            "operator_review_status",
            "record_id",
            "source_category",
            "source_status",
            "source_url",
        )
        for field in required_fields:
            if field not in record:
                errors.append(f"{path}.{field} is required")
        if record.get("contract_version") != REFRESH_RECORD_CONTRACT:
            errors.append(f"{path}.contract_version must be {REFRESH_RECORD_CONTRACT}")
        if record.get("network_used") is not False:
            errors.append(f"{path}.network_used must be false")
        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        record_id = clean_text(record.get("record_id"))
        if not record_id:
            errors.append(f"{path}.record_id is required")
        elif record_id in seen:
            errors.append(f"{path}.record_id duplicates an earlier record")
        seen.add(record_id)
        if refresh_id and not record_id.startswith(f"{refresh_id}."):
            errors.append(f"{path}.record_id must start with refresh_id")
        if not isinstance(record.get("evidence_quality_notes"), list):
            errors.append(f"{path}.evidence_quality_notes must be a list")
    return errors


def _validate_local_reference(reference: str, field_path: str) -> list[str]:
    normalized = _normalize_reference(reference)
    errors: list[str] = []
    if not normalized:
        errors.append(f"{field_path} must be a non-empty local reference")
    if _is_network_like(normalized):
        errors.append(f"{field_path} must be a local reference")
    if Path(normalized).is_absolute():
        errors.append(f"{field_path} must be repository-relative")
    if _contains_path_traversal(normalized):
        errors.append(f"{field_path} must not contain path traversal")
    if normalized.startswith(FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} is outside the public evidence refresh boundary")
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} must stay under an allowed public evidence artifact path")
    return errors


def _validate_public_source_url(url: str, field_path: str) -> list[str]:
    normalized = url.strip().lower()
    errors: list[str] = []
    if not normalized.startswith(("https://", "http://")):
        errors.append(f"{field_path} must be an http(s) public read-only URL")
    if any(fragment in normalized for fragment in BLOCKED_URL_FRAGMENTS):
        errors.append(f"{field_path} points to a blocked or non-public endpoint")
    return errors


def _normalize_reference(reference: str) -> str:
    return reference.replace("\\", "/").strip()


def _is_network_like(reference: str) -> bool:
    lowered = reference.lower()
    return "://" in lowered or lowered.startswith(("http:", "https:"))


def _contains_path_traversal(reference: str) -> bool:
    return any(part == ".." for part in reference.split("/"))


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PublicEvidenceRefreshError(f"{label} must be a JSON object")
    return value


def _parse_utc_timestamp(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("missing Z suffix")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("missing timezone")
    return parsed.astimezone(timezone.utc)


def _build_deterministic_id(
    refresh_id: str,
    request: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    quality_ledger: Mapping[str, Any],
) -> str:
    digest_input = {
        "quality_ledger": quality_ledger,
        "records": list(records),
        "request": request,
    }
    digest = hashlib.sha256(
        json.dumps(digest_input, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:12]
    return f"{refresh_id}-{digest}"


def _count_by(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = clean_text(row.get(field)) or "missing"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _missing_evidence_notes(candidate: Mapping[str, Any]) -> list[str]:
    return [
        f"Candidate missing evidence: {clean_text(item)}"
        for item in candidate.get("missing_evidence", [])
        if clean_text(item)
    ]


def _refresh_safety_summary() -> dict[str, Any]:
    summary = trading_core_safety_summary()
    summary.update(
        {
            "authenticated_endpoints_used": False,
            "browser_automation_used": False,
            "external_api_calls_performed": False,
            "network_used": False,
            "outcome_resolution_invented": False,
            "pnl_invented": False,
        }
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT local public evidence refresh artifacts.")
    parser.add_argument("--request", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    request = load_public_evidence_refresh_request(args.request)
    artifacts = write_public_evidence_refresh_artifacts(request=request, out_dir=args.out_dir)
    print(json.dumps(artifacts["ledger"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

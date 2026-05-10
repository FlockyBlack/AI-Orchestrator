from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_fetch_execution_preflight import build_execution_preflight, write_execution_preflight
from pm_bot.practical.saved_evidence_replay_adapter import map_saved_evidence_to_source_packets
from pm_bot.practical.saved_public_evidence_packet import build_saved_public_evidence_packet, write_saved_public_evidence_packet

EXECUTION_SUMMARY_CONTRACT_VERSION = "pmbot_controlled_public_fetch_execution_summary.v1"
FetchResponse = Mapping[str, Any]
FetchCallable = Callable[[Mapping[str, Any], Mapping[str, Any]], FetchResponse]


class ControlledPublicFetchExecutionError(RuntimeError):
    pass


def execute_controlled_public_fetch(
    *,
    approval: Mapping[str, Any],
    request_manifest: Mapping[str, Any],
    evidence_save_plan: Mapping[str, Any],
    replay_plan: Mapping[str, Any],
    out_dir: str | Path,
    fetcher: FetchCallable | None = None,
    fixture_mode: bool = False,
    timeout_seconds: int = 10,
    write_preflight_outputs: bool = True,
) -> dict[str, Any]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    evidence_dir = out_path / "evidence_packets"
    replay_dir = out_path / "replay"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    replay_dir.mkdir(parents=True, exist_ok=True)

    if write_preflight_outputs:
        preflight = write_execution_preflight(
            approval=approval,
            request_manifest=request_manifest,
            evidence_save_plan=evidence_save_plan,
            replay_plan=replay_plan,
            out_json_path=str(out_path / "execution_preflight.result.json"),
            out_md_path=str(out_path / "execution_preflight.md"),
            fixture_mode=fixture_mode,
        )
    else:
        preflight = build_execution_preflight(
            approval=approval,
            request_manifest=request_manifest,
            evidence_save_plan=evidence_save_plan,
            replay_plan=replay_plan,
            fixture_mode=fixture_mode,
        )

    max_request_count = int(preflight.get("max_request_count") or 0)
    executable = list(preflight.get("executable_request_intents", []))
    attempted: list[dict[str, Any]] = []
    succeeded: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    evidence_packets: list[dict[str, Any]] = []
    blockers = list(preflight.get("blockers", []))
    warnings = list(preflight.get("warnings", []))

    if preflight.get("ready_to_execute_public_read_only_fetch") is True:
        for row in executable[:max_request_count]:
            intent = _intent_by_id(request_manifest, row.get("request_intent_id", ""))
            url_safety = row.get("url_safety", {})
            attempted.append({"request_intent_id": row.get("request_intent_id"), "market_id": row.get("market_id")})
            try:
                response = _fetch_with_optional_fixture(
                    intent=intent,
                    url_safety=url_safety,
                    fetcher=fetcher,
                    timeout_seconds=timeout_seconds,
                )
                packet = _evidence_packet_from_response(
                    intent=intent,
                    url_safety=url_safety,
                    response=response,
                    fixture_mode=fixture_mode,
                )
                packet_path = evidence_dir / f"{packet['evidence_packet_id']}.json"
                write_saved_public_evidence_packet(packet, out_json_path=str(packet_path))
                succeeded.append(
                    {
                        "request_intent_id": intent.get("request_intent_id"),
                        "market_id": intent.get("market_id"),
                        "evidence_packet": str(packet_path).replace("\\", "/"),
                    }
                )
                evidence_packets.append(packet)
            except Exception as exc:  # noqa: BLE001 - execution summary must preserve failure reason.
                failed.append(
                    {
                        "request_intent_id": intent.get("request_intent_id"),
                        "market_id": intent.get("market_id"),
                        "error": str(exc),
                    }
                )
    else:
        _write_no_evidence_marker(evidence_dir, blockers)

    replay_result = _write_replay_artifacts(
        evidence_packets=evidence_packets,
        replay_dir=replay_dir,
    )
    summary = _execution_summary(
        preflight=preflight,
        attempted=attempted,
        succeeded=succeeded,
        failed=failed,
        evidence_packets=evidence_packets,
        blockers=blockers,
        warnings=warnings,
        replay_result=replay_result,
        fixture_mode=fixture_mode,
    )
    write_json(out_path / "fetch_execution_summary.result.json", summary)
    write_text(out_path / "fetch_execution_summary.md", render_execution_summary_markdown(summary))
    write_analysis_update_candidate_report(
        out_dir=out_path,
        replay_result=replay_result,
        evidence_packets=evidence_packets,
        preflight=preflight,
    )
    write_source_learning_pending_update(
        out_dir=out_path,
        summary=summary,
        preflight=preflight,
    )
    write_operator_public_fetch_execution_card(
        out_dir=out_path,
        summary=summary,
        replay_result=replay_result,
    )
    write_public_fetch_execution_safety_scan(out_dir=out_path, summary=summary)
    return summary


def render_execution_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Controlled Public Read-Only Fetch Execution Summary",
        "",
        f"- Live public read-only fetch occurred: `{str(summary.get('live_fetch_performed')).lower()}`",
        f"- Requests attempted: {summary.get('request_count_attempted')}",
        f"- Requests succeeded: {summary.get('request_count_succeeded')}",
        f"- Requests failed: {summary.get('request_count_failed')}",
        f"- Requests blocked: {summary.get('request_count_blocked')}",
        f"- Evidence packets created: {len(summary.get('evidence_packets_created', []))}",
        f"- Replay performed: `{str(summary.get('replay_performed')).lower()}`",
        "",
        "## Blockers",
        "",
        *bullet_lines(summary.get("blockers", [])),
        "",
        "## Warnings",
        "",
        *bullet_lines(summary.get("warnings", [])),
        "",
        "## Evidence Packets",
        "",
        *bullet_lines(f"`{path}`" for path in summary.get("evidence_packets_created", [])),
        "",
        "## Safety Boundary",
        "",
        "- Public read-only GET only.",
        "- No authentication, cookies, API keys, wallet access, order path, trading path, scheduler, or background worker.",
        "- No market action recommendation or executable quantitative market output is produced.",
    ]
    return "\n".join(lines) + "\n"


def write_replay_blocked_no_evidence(out_dir: str | Path, blockers: Sequence[str] = ()) -> dict[str, Any]:
    replay_dir = Path(out_dir)
    replay_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "contract_version": "pmbot_public_fetch_replay_blocked_no_evidence.v1",
        "generated_at": GENERATED_AT,
        "replay_performed": False,
        "replay_status": "blocked_no_evidence",
        "evidence_packets_available": 0,
        "blockers": list(blockers) or ["No saved evidence packets were created."],
        "automatic_analysis_update_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": safe_summary(),
    }
    write_json(replay_dir / "replay_blocked_no_evidence.json", result)
    write_text(replay_dir / "replay_blocked_no_evidence.md", render_replay_blocked_markdown(result))
    return result


def render_replay_blocked_markdown(result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Public Fetch Replay Blocked",
            "",
            f"- Replay performed: `{str(result.get('replay_performed')).lower()}`",
            f"- Replay status: `{result.get('replay_status')}`",
            f"- Evidence packets available: {result.get('evidence_packets_available')}",
            "",
            "## Blockers",
            "",
            *bullet_lines(result.get("blockers", [])),
            "",
            "## Safety Boundary",
            "",
            "- No analysis update is performed without saved evidence replay.",
            "- Paper tracking remains analysis-only.",
        ]
    ) + "\n"


def write_analysis_update_candidate_report(
    *,
    out_dir: str | Path,
    replay_result: Mapping[str, Any],
    evidence_packets: Sequence[Mapping[str, Any]],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    evidence_ids = [clean_text(packet.get("evidence_packet_id")) for packet in evidence_packets]
    affected_market_ids = sorted({market_id for packet in evidence_packets for market_id in packet.get("market_ids", [])})
    affected_hypothesis_ids = sorted(
        {hypothesis_id for packet in evidence_packets for hypothesis_id in packet.get("hypothesis_ids", [])}
    )
    report = {
        "contract_version": "pmbot_public_fetch_analysis_update_candidate_report.v1",
        "generated_at": GENERATED_AT,
        "update_candidate_available": bool(evidence_packets and replay_result.get("replay_performed") is True),
        "affected_market_ids": affected_market_ids,
        "affected_hypothesis_ids": affected_hypothesis_ids,
        "evidence_packets_used": evidence_ids,
        "replay_status": replay_result.get("replay_status", "not_performed"),
        "contradictions_detected": bool(
            any(packet.get("contradiction_candidates") for packet in evidence_packets)
        ),
        "staleness_status": _staleness_status(evidence_packets),
        "recommended_operator_review": "Review replay artifacts before any later paper-only analysis update.",
        "automatic_update_performed": False,
        "no_real_trade_decision": True,
        "blocked_request_count": preflight.get("blocked_request_count", 0),
        "safety_summary": safe_summary(),
    }
    write_json(Path(out_dir) / "analysis_update_candidate_report.json", report)
    write_text(Path(out_dir) / "analysis_update_candidate_report.md", render_analysis_update_candidate_markdown(report))
    return report


def render_analysis_update_candidate_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Analysis Update Candidate Report",
        "",
        f"- Update candidate available: `{str(report.get('update_candidate_available')).lower()}`",
        f"- Replay status: `{report.get('replay_status')}`",
        f"- Automatic update performed: `{str(report.get('automatic_update_performed')).lower()}`",
        "",
        "## Affected Markets",
        "",
        *bullet_lines(f"`{market_id}`" for market_id in report.get("affected_market_ids", [])),
        "",
        "## Evidence Packets Used",
        "",
        *bullet_lines(f"`{packet_id}`" for packet_id in report.get("evidence_packets_used", [])),
        "",
        "## Operator Review",
        "",
        f"- {report.get('recommended_operator_review')}",
        "",
        "## Safety Boundary",
        "",
        "- This report is a candidate review surface only.",
        "- It does not mutate prior market analyses or produce executable market output.",
    ]
    return "\n".join(lines) + "\n"


def write_source_learning_pending_update(
    *,
    out_dir: str | Path,
    summary: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    fetched = summary.get("succeeded_requests", [])
    blocked = preflight.get("blocked_request_intents", [])
    report = {
        "contract_version": "pmbot_public_fetch_source_learning_pending.v1",
        "generated_at": GENERATED_AT,
        "sources_fetched": fetched,
        "sources_blocked": blocked,
        "evidence_packets_created": summary.get("evidence_packets_created", []),
        "markets_affected": sorted(
            {
                clean_text(row.get("market_id"))
                for row in list(fetched) + list(blocked)
                if isinstance(row, Mapping) and clean_text(row.get("market_id"))
            }
        ),
        "what_can_be_learned_only_after_outcome_resolution": [
            "Whether captured public sources later aligned with final market outcomes.",
            "Whether source freshness correlated with useful paper-only analysis maintenance.",
        ],
        "what_can_be_learned_now_about_source_accessibility_freshness": [
            "Placeholder-only manifest entries are not executable.",
            "Concrete public URLs must be added locally before a live fetch can occur.",
        ]
        if not fetched
        else [
            "Concrete public URLs were accessible through finite read-only GET requests.",
            "Saved evidence freshness can be reviewed through replay artifacts.",
        ],
        "no_autonomous_training_performed": True,
        "safety_summary": safe_summary(),
    }
    write_json(Path(out_dir) / "source_learning_public_fetch_pending.json", report)
    write_text(Path(out_dir) / "source_learning_public_fetch_pending.md", render_source_learning_markdown(report))
    return report


def render_source_learning_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Source Learning Public Fetch Pending Update",
            "",
            f"- Sources fetched: {len(report.get('sources_fetched', []))}",
            f"- Sources blocked: {len(report.get('sources_blocked', []))}",
            f"- Evidence packets created: {len(report.get('evidence_packets_created', []))}",
            f"- Autonomous training performed: `{str(not report.get('no_autonomous_training_performed')).lower()}`",
            "",
            "## Markets Affected",
            "",
            *bullet_lines(f"`{market_id}`" for market_id in report.get("markets_affected", [])),
            "",
            "## Learn Later",
            "",
            *bullet_lines(report.get("what_can_be_learned_only_after_outcome_resolution", [])),
            "",
            "## Learn Now",
            "",
            *bullet_lines(report.get("what_can_be_learned_now_about_source_accessibility_freshness", [])),
            "",
            "## Safety Boundary",
            "",
            "- No autonomous training or executable market output is performed.",
        ]
    ) + "\n"


def write_operator_public_fetch_execution_card(
    *,
    out_dir: str | Path,
    summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
) -> dict[str, Any]:
    card = {
        "contract_version": "pmbot_operator_public_fetch_execution_card.v1",
        "card_id": "operator-public-fetch-execution-card-007",
        "generated_at": GENERATED_AT,
        "live_public_read_only_fetch_occurred": summary.get("live_fetch_performed") is True,
        "request_count_succeeded": summary.get("request_count_succeeded", 0),
        "request_count_failed": summary.get("request_count_failed", 0),
        "request_count_blocked": summary.get("request_count_blocked", 0),
        "evidence_packets_saved": bool(summary.get("evidence_packets_created")),
        "replay_happened": replay_result.get("replay_performed") is True,
        "automatic_analysis_update_performed": False,
        "operator_should_inspect_next": [
            "execution_preflight.md",
            "fetch_execution_summary.md",
            "replay/replay_blocked_no_evidence.md"
            if replay_result.get("replay_performed") is not True
            else "replay/replayed_source_packets.md",
            "analysis_update_candidate_report.md",
            "source_learning_public_fetch_pending.md",
            "public_fetch_execution_safety_scan.md",
        ],
        "what_remains_blocked": [
            "Authenticated endpoints",
            "API keys, cookies, KYC, login, and browser automation",
            "Wallet, signing, private key, order, and trading paths",
            "OpenRouter",
            "Market recommendations and executable quantitative market output",
            "Probability/EV/edge/side-selection as blocked trading-signal category",
            "Schedulers, polling, daemons, and background workers",
            "Autonomous execution",
        ],
        "safety_boundary": [
            "Analysis-only and paper-tracking-only.",
            "No real trade decision.",
            "No prior market analysis is updated automatically.",
        ],
        "safety_summary": safe_summary(),
    }
    write_json(Path(out_dir) / "operator_public_fetch_execution_card.json", card)
    write_text(Path(out_dir) / "operator_public_fetch_execution_card.md", render_operator_card_markdown(card))
    return card


def render_operator_card_markdown(card: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Operator Public Fetch Execution Card",
            "",
            f"- Live public read-only fetch occurred: `{str(card.get('live_public_read_only_fetch_occurred')).lower()}`",
            f"- Requests succeeded: {card.get('request_count_succeeded')}",
            f"- Requests failed: {card.get('request_count_failed')}",
            f"- Requests blocked: {card.get('request_count_blocked')}",
            f"- Evidence packets saved: `{str(card.get('evidence_packets_saved')).lower()}`",
            f"- Replay happened: `{str(card.get('replay_happened')).lower()}`",
            f"- Automatic analysis update performed: `{str(card.get('automatic_analysis_update_performed')).lower()}`",
            "",
            "## Operator Should Inspect Next",
            "",
            *bullet_lines(card.get("operator_should_inspect_next", [])),
            "",
            "## What Remains Blocked",
            "",
            *bullet_lines(card.get("what_remains_blocked", [])),
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(card.get("safety_boundary", [])),
        ]
    ) + "\n"


def write_public_fetch_execution_safety_scan(
    *,
    out_dir: str | Path,
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    out_path = Path(out_dir)
    report = run_practical_safety_scan(artifact_dirs=[out_path])
    report.update(
        {
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "public_read_only_fetch_count": summary.get("request_count_succeeded", 0),
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "scheduler_background_worker_or_polling": False,
            "no_scheduler_background_worker_polling": True,
            "no_autonomous_trading": True,
            "public_fetch_execution_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    write_json(out_path / "public_fetch_execution_safety_scan.result.json", report)
    write_text(out_path / "public_fetch_execution_safety_scan.md", render_practical_safety_scan_markdown(report))
    return report


def _fetch_with_optional_fixture(
    *,
    intent: Mapping[str, Any],
    url_safety: Mapping[str, Any],
    fetcher: FetchCallable | None,
    timeout_seconds: int,
) -> FetchResponse:
    if fetcher is not None:
        return fetcher(intent, url_safety)
    return http_get_public_read_only(
        clean_text(url_safety.get("sanitized_url_reference")),
        timeout_seconds=timeout_seconds,
    )


def http_get_public_read_only(url: str, *, timeout_seconds: int = 10) -> dict[str, Any]:
    opener = build_opener(_NoRedirectHandler)
    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": "PMBOT-public-read-only-fetch/1.0",
            "Accept": "text/plain, text/html, application/json;q=0.9, */*;q=0.5",
        },
    )
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            body = response.read(200_000)
            return {
                "status_code": int(response.status),
                "final_url": response.geturl(),
                "headers": dict(response.headers.items()),
                "body": body,
            }
    except HTTPError as exc:
        raise ControlledPublicFetchExecutionError(f"HTTP fetch failed with status {exc.code}") from exc
    except URLError as exc:
        raise ControlledPublicFetchExecutionError(f"HTTP fetch failed: {exc.reason}") from exc


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise ControlledPublicFetchExecutionError(f"redirect blocked: {code} {newurl}")


def _evidence_packet_from_response(
    *,
    intent: Mapping[str, Any],
    url_safety: Mapping[str, Any],
    response: FetchResponse,
    fixture_mode: bool,
) -> dict[str, Any]:
    body = response.get("body", b"")
    if isinstance(body, bytes):
        text = body.decode("utf-8", errors="replace")
    else:
        text = clean_text(body)
    excerpt = text[:4000]
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]
    evidence_packet_id = f"public_fetch_007_{clean_text(intent.get('request_intent_id'))}_{digest}"
    return build_saved_public_evidence_packet(
        evidence_packet_id=evidence_packet_id,
        source_id=clean_text(intent.get("request_intent_id")),
        source_name=clean_text(intent.get("source_name_or_placeholder") or intent.get("source_name")),
        source_category=clean_text(intent.get("source_category")),
        source_reference=clean_text(url_safety.get("sanitized_url_reference")),
        market_ids=[clean_text(intent.get("market_id"))],
        hypothesis_ids=[clean_text(intent.get("linked_hypothesis_id"))],
        raw_excerpt_or_summary=(
            f"HTTP {response.get('status_code')} public read-only response saved. "
            f"Content digest prefix: {digest}. Truncated excerpt: {excerpt}"
        ),
        normalized_claims=[
            f"Public source returned HTTP {response.get('status_code')} for request intent {intent.get('request_intent_id')}.",
            "Saved response excerpt is available for replay-only paper analysis review.",
        ],
        freshness_status="captured_at_task_time",
        contradiction_candidates=[],
        limitations=[
            "Response body was truncated before storage.",
            "This packet is evidence capture only and is not a market action instruction.",
        ],
        capture_mode="fixture" if fixture_mode else "future_public_read_only_fetch",
        live_network_used=not fixture_mode,
    )


def _write_replay_artifacts(
    *,
    evidence_packets: Sequence[Mapping[str, Any]],
    replay_dir: Path,
) -> dict[str, Any]:
    if not evidence_packets:
        return write_replay_blocked_no_evidence(replay_dir)
    mapped = map_saved_evidence_to_source_packets(evidence_packets)
    mapped["replay_status"] = "replayed_saved_evidence"
    mapped["replay_performed"] = True
    write_json(replay_dir / "replayed_source_packets.json", mapped)
    write_text(replay_dir / "replayed_source_packets.md", _render_replayed_source_packets_markdown(mapped))
    return mapped


def _render_replayed_source_packets_markdown(mapped: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Replayed Source Packets",
        "",
        f"- Replay performed: `{str(mapped.get('replay_performed')).lower()}`",
        f"- Source packets: {len(mapped.get('source_packets', []))}",
        "",
        "## Source Packets",
        "",
    ]
    for source in mapped.get("source_packets", []):
        lines.extend(
            [
                f"- `{source.get('source_id')}`",
                f"  Category: `{source.get('source_category')}`",
                f"  Freshness: `{source.get('freshness_status')}`",
            ]
        )
    lines.extend(["", "## Safety Boundary", "", "- Saved evidence replay only; no network request is made."])
    return "\n".join(lines) + "\n"


def _execution_summary(
    *,
    preflight: Mapping[str, Any],
    attempted: Sequence[Mapping[str, Any]],
    succeeded: Sequence[Mapping[str, Any]],
    failed: Sequence[Mapping[str, Any]],
    evidence_packets: Sequence[Mapping[str, Any]],
    blockers: Sequence[str],
    warnings: Sequence[str],
    replay_result: Mapping[str, Any],
    fixture_mode: bool,
) -> dict[str, Any]:
    evidence_paths = [clean_text(row.get("evidence_packet")) for row in succeeded if clean_text(row.get("evidence_packet"))]
    live_network_used = bool(succeeded) and not fixture_mode
    return {
        "contract_version": EXECUTION_SUMMARY_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "live_fetch_performed": live_network_used,
        "request_count_attempted": len(attempted),
        "request_count_succeeded": len(succeeded),
        "request_count_blocked": preflight.get("blocked_request_count", 0),
        "request_count_failed": len(failed),
        "attempted_requests": list(attempted),
        "succeeded_requests": list(succeeded),
        "failed_requests": list(failed),
        "evidence_packets_created": evidence_paths,
        "evidence_packet_ids": [packet.get("evidence_packet_id") for packet in evidence_packets],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "replay_performed": replay_result.get("replay_performed") is True,
        "replay_status": replay_result.get("replay_status", "not_performed"),
        "safety_summary": {
            **safe_summary(),
            "live_network_used": live_network_used,
            "public_read_only_fetch_count": len(succeeded),
        },
    }


def _intent_by_id(request_manifest: Mapping[str, Any], request_intent_id: str) -> Mapping[str, Any]:
    for intent in request_manifest.get("request_intents", []):
        if isinstance(intent, Mapping) and intent.get("request_intent_id") == request_intent_id:
            return intent
    raise ControlledPublicFetchExecutionError(f"request intent not found: {request_intent_id}")


def _write_no_evidence_marker(evidence_dir: Path, blockers: Sequence[str]) -> None:
    write_text(
        evidence_dir / "NO_EVIDENCE_CREATED.md",
        "\n".join(
            [
                "# No Evidence Created",
                "",
                "No live public read-only fetch was performed, so no saved evidence packets were created.",
                "",
                "## Why",
                "",
                *bullet_lines(blockers),
                "",
                "## Next Action",
                "",
                "- Enrich the local manifest with explicit safe public URLs before another controlled fetch attempt.",
            ]
        )
        + "\n",
    )


def _staleness_status(evidence_packets: Sequence[Mapping[str, Any]]) -> str:
    if not evidence_packets:
        return "no_evidence"
    statuses = {clean_text(packet.get("freshness_status")) for packet in evidence_packets}
    if "stale" in statuses:
        return "contains_stale_evidence"
    return "captured_for_review"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute finite controlled PMBOT public read-only fetches.")
    parser.add_argument("--approval", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence-save-plan", required=True)
    parser.add_argument("--replay-plan", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=10)
    args = parser.parse_args(argv)
    summary = execute_controlled_public_fetch(
        approval=load_json_object(args.approval, label="scoped approval"),
        request_manifest=load_json_object(args.manifest, label="request manifest"),
        evidence_save_plan=load_json_object(args.evidence_save_plan, label="evidence save plan"),
        replay_plan=load_json_object(args.replay_plan, label="replay plan"),
        out_dir=args.out_dir,
        fixture_mode=args.fixture_mode,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

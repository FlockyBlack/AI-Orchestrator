from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.paper_trading_loop import run_paper_trading_loop
from pm_bot.trading_core.public_gamma_market_client import (
    PublicGammaFetchError,
    PublicGammaMarketClient,
)
from pm_bot.trading_core.public_market_evidence_models import (
    FIXTURE_FALLBACK_SOURCE_NAME,
    FIXTURE_FALLBACK_SOURCE_TYPE,
    PUBLIC_GAMMA_SOURCE_NAME,
    PUBLIC_GAMMA_SOURCE_TYPE,
    PublicGammaResponseEvidence,
    PublicMarketEvidencePack,
    PublicMarketEvidenceSnapshot,
    PublicMarketEvidenceSource,
    hash_response_payload,
    public_market_safety_flags,
    validate_public_market_evidence_pack,
)
from pm_bot.trading_core.public_market_normalizer import (
    normalize_public_market_result,
    summarize_public_market_candidates,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-054-PUBLIC-MARKET-DATA-EVIDENCE-PACK-FOR-PAPER-TRADING-LOOP"
PUBLIC_MARKET_PAPER_LOOP_RESULT_CONTRACT = "pmbot_public_market_paper_loop_result_054.v1"
LATEST_PUBLIC_MARKET_PAPER_STATUS_CONTRACT = "pmbot_public_market_paper_loop_latest_status_054.v1"
PUBLIC_MARKET_FETCH_ERROR_CONTRACT = "pmbot_public_market_fetch_error_054.v1"
DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/public_market_paper_loop_054")

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
)


def public_market_paper_loop_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "public_market_paper_loop_054_result.json",
        "operator_md": root / "public_market_paper_loop_054_operator.md",
        "latest_status": root / "latest_public_market_paper_status_054.json",
        "request_evidence": root / "public_gamma_request_evidence_054.json",
        "response_evidence": root / "public_gamma_response_evidence_054.json",
        "evidence_pack": root / "public_market_evidence_pack_054.json",
        "normalized_snapshot": root / "normalized_public_market_snapshot_054.json",
        "strategy_signal": root / "public_market_strategy_signal_054.json",
        "risk": root / "public_market_risk_054.json",
        "order_intent": root / "public_market_order_intent_054.json",
        "no_signal": root / "public_market_no_signal_054.json",
        "fetch_error": root / "public_market_fetch_error_054.json",
    }


def run_public_market_paper_loop(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    query: str = "",
    slug: str = "",
    tag_id: str = "",
    limit: int = 20,
    fixture_fallback: bool = False,
    offline_fixture_only: bool = False,
    artifact_dir: str | Path | None = None,
    public_client: PublicGammaMarketClient | None = None,
    fixture_payload: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("public market paper loop requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy).lower() or "tiny-momentum"
    paths = public_market_paper_loop_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    client = public_client or PublicGammaMarketClient()
    fetch_error: dict[str, Any] | None = None

    if offline_fixture_only:
        fetch_result = client.load_fixture_fallback(
            market=market_symbol,
            query=query,
            slug=slug,
            tag_id=tag_id,
            limit=limit,
            fixture_payload=fixture_payload,
            generated_at=generated_at,
        )
    else:
        try:
            fetch_result = client.search_public_markets(
                market=market_symbol,
                query=query,
                slug=slug,
                tag_id=tag_id,
                limit=limit,
                generated_at=generated_at,
            )
        except PublicGammaFetchError as exc:
            fetch_error = _fetch_error_payload(exc.error_payload, generated_at=generated_at)
            if fixture_fallback is not True:
                _write_fetch_error(paths["fetch_error"], fetch_error)
                raise
            fetch_result = client.load_fixture_fallback(
                market=market_symbol,
                query=query,
                slug=slug,
                tag_id=tag_id,
                limit=limit,
                fixture_payload=fixture_payload,
                generated_at=generated_at,
            )

    try:
        normalized = normalize_public_market_result(
            fetch_result,
            market=market_symbol,
            query=query,
            slug=slug,
            generated_at=generated_at,
        )
    except ValueError as exc:
        fetch_error = _fetch_error_payload(
            {
                "source_name": fetch_result.get("source_name"),
                "source_type": fetch_result.get("source_type"),
                "base_url": fetch_result.get("base_url"),
                "endpoint_path": fetch_result.get("endpoint_path"),
                "sanitized_query": fetch_result.get("sanitized_query", {}),
                "request_method": "GET",
                "network_used": fetch_result.get("network_used") is True,
                "error_type": type(exc).__name__,
                "message": clean_text(exc),
            },
            generated_at=generated_at,
        )
        if fixture_fallback is not True or fetch_result.get("source_type") == FIXTURE_FALLBACK_SOURCE_TYPE:
            _write_fetch_error(paths["fetch_error"], fetch_error)
            raise
        fetch_result = client.load_fixture_fallback(
            market=market_symbol,
            query=query,
            slug=slug,
            tag_id=tag_id,
            limit=limit,
            fixture_payload=fixture_payload,
            generated_at=generated_at,
        )
        normalized = normalize_public_market_result(
            fetch_result,
            market=market_symbol,
            query=query,
            slug=slug,
            generated_at=generated_at,
        )

    request_evidence = dict(fetch_result.get("request_evidence", {}))
    response_evidence = _response_evidence_with_selection(
        fetch_result=fetch_result,
        normalized=normalized,
        generated_at=generated_at,
    )
    evidence_pack = _build_evidence_pack(
        fetch_result=fetch_result,
        request_evidence=request_evidence,
        response_evidence=response_evidence,
        normalized=normalized,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    _write_public_market_evidence_artifacts(
        paths=paths,
        request_evidence=request_evidence,
        response_evidence=response_evidence,
        evidence_pack=evidence_pack,
        normalized=normalized,
        fetch_error=fetch_error,
    )

    paper_result = run_paper_trading_loop(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        market_snapshot=dict(normalized.get("market_snapshot", {})),
        artifact_dir=paths["root"],
        write_artifacts=False,
        generated_at=generated_at,
    )
    status = build_latest_public_market_paper_status(
        market=market_symbol,
        strategy=strategy_name,
        source_name=clean_text(fetch_result.get("source_name")),
        source_type=clean_text(fetch_result.get("source_type")),
        evidence_pack=evidence_pack,
        normalized=normalized,
        paper_result=paper_result,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result = {
        "contract_version": PUBLIC_MARKET_PAPER_LOOP_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": "public_market_paper_loop_completed",
        "market": market_symbol,
        "strategy_name": strategy_name,
        "source": clean_text(fetch_result.get("source_name")),
        "source_type": clean_text(fetch_result.get("source_type")),
        "mode": "paper / review-only",
        "dry_run": True,
        "evidence_pack": evidence_pack,
        "normalized_public_market_snapshot": normalized,
        "paper_loop_result": paper_result,
        "strategy_signal": paper_result.get("strategy_signal"),
        "no_signal": paper_result.get("no_signal"),
        "risk": paper_result.get("risk"),
        "paper_order_intent": paper_result.get("paper_order_intent"),
        "latest_status": status,
        "operator_ui_status_feed": status,
        "telegram_visible_summary": render_public_market_paper_loop_telegram_status(status),
        "artifact_paths": path_refs,
        "generated_at": generated_at,
    }
    result.update(public_market_safety_flags(network_used=evidence_pack.get("network_used") is True))
    result["validation"] = {
        "contract_version": "pmbot_public_market_paper_loop_validation_054.v1",
        "valid": True,
        "status": "passed",
        "errors": [],
        "evidence_pack_validation": validate_public_market_evidence_pack(evidence_pack),
        "generated_at": generated_at,
        **public_market_safety_flags(network_used=evidence_pack.get("network_used") is True),
    }
    if result["validation"]["evidence_pack_validation"].get("valid") is not True:
        result["validation"]["valid"] = False
        result["validation"]["status"] = "blocked"
        result["validation"]["errors"].append("evidence pack validation failed")
        raise ValueError("public market evidence pack validation failed")

    _write_public_market_paper_artifacts(paths=paths, result=result, paper_result=paper_result, status=status)
    return result


def build_latest_public_market_paper_status(
    *,
    market: str,
    strategy: str,
    source_name: str,
    source_type: str,
    evidence_pack: Mapping[str, Any],
    normalized: Mapping[str, Any],
    paper_result: Mapping[str, Any],
    artifact_paths: Mapping[str, str],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    risk = dict(paper_result.get("risk", {}))
    signal = dict(paper_result.get("strategy_signal") or {})
    no_signal = dict(paper_result.get("no_signal") or {})
    intent = dict(paper_result.get("paper_order_intent") or {})
    selected_market = dict(normalized.get("selected_market", {}))
    paper_intent_status = clean_text(intent.get("paper_intent_status") or "no_paper_intent")
    paper_intent_summary = (
        f"{intent.get('outcome')} {intent.get('side')} at {intent.get('limit_price')} size {intent.get('size')}"
        if intent
        else clean_text(no_signal.get("reason") or risk.get("operator_summary") or "no paper intent")
    )
    status = {
        "contract_version": LATEST_PUBLIC_MARKET_PAPER_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(paper_result.get("loop_status") or "public_market_paper_loop_completed"),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy_name": clean_text(strategy),
        "source": clean_text(source_name),
        "source_type": clean_text(source_type),
        "evidence_pack_path": clean_text(artifact_paths.get("evidence_pack")),
        "normalized_snapshot_path": clean_text(artifact_paths.get("normalized_snapshot")),
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "selected_market_summary": {
            "market_id": clean_text(selected_market.get("market_id")),
            "market_slug": clean_text(selected_market.get("market_slug")),
            "question": clean_text(selected_market.get("question")),
            "event_slug": clean_text(selected_market.get("event_slug")),
            "active": selected_market.get("active") is True,
            "closed": selected_market.get("closed") is True,
        },
        "selected_market_reason": clean_text(normalized.get("selected_market_reason")),
        "evidence_hash": clean_text(evidence_pack.get("response_snapshot_hash")),
        "signal_status": clean_text(signal.get("signal_status") or no_signal.get("signal_status") or "not_available"),
        "risk_decision": clean_text(risk.get("risk_decision") or "not_available"),
        "paper_intent_status": paper_intent_status,
        "paper_intent_summary": paper_intent_summary,
        "mode": "paper / review-only",
        "execution_mode": "paper",
        "review_only": True,
        "live_execution": "blocked",
        "live_execution_blocked": True,
        "next_operator_action": "review only, no live action available",
        "generated_at": generated_at,
    }
    status.update(public_market_safety_flags(network_used=evidence_pack.get("network_used") is True))
    return status


def render_public_market_paper_loop_telegram_status(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Public market paper loop completed.",
            f"Market: {clean_text(value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Source: {clean_text(value.get('source'))}",
            "Mode: paper / review-only",
            "Live execution: blocked",
            f"Risk decision: {clean_text(value.get('risk_decision'))}",
            f"Paper intent: {clean_text(value.get('paper_intent_status'))}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_public_market_paper_loop_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    status = dict(value.get("latest_status", {}))
    evidence = dict(value.get("evidence_pack", {}))
    normalized = dict(value.get("normalized_public_market_snapshot", {}))
    selected = dict(normalized.get("selected_market", {}))
    risk = dict(value.get("risk", {}))
    intent = dict(value.get("paper_order_intent") or {})
    no_signal = dict(value.get("no_signal") or {})
    signal = dict(value.get("strategy_signal") or {})
    lines = [
        "# PMBOT Public Market Paper Loop 054",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        f"- Source used: `{value.get('source')}`",
        f"- Source type: `{value.get('source_type')}`",
        "- Mode: `paper / review-only`",
        "- live execution blocked",
        "- auth_used=false",
        "- credentials_used=false",
        "- wallet_used=false",
        "- signing_used=false",
        "- order_endpoint_used=false",
        "",
        "## Public Evidence",
        "",
        f"- Network used: `{str(evidence.get('network_used') is True).lower()}`",
        f"- Request method: `{evidence.get('request_method')}`",
        f"- Base URL: `{evidence.get('base_url')}`",
        f"- Endpoint path: `{evidence.get('endpoint_path')}`",
        f"- Sanitized query: `{json.dumps(evidence.get('sanitized_query', {}), sort_keys=True)}`",
        f"- Evidence hash: `{evidence.get('response_snapshot_hash')}`",
        f"- Evidence pack path: `{status.get('evidence_pack_path')}`",
        "",
        "## Selected Market",
        "",
        f"- Market id: `{selected.get('market_id')}`",
        f"- Market slug: `{selected.get('market_slug')}`",
        f"- Event slug: `{selected.get('event_slug')}`",
        f"- Question: {clean_text(selected.get('question'))}",
        f"- Active: `{str(selected.get('active') is True).lower()}`",
        f"- Closed: `{str(selected.get('closed') is True).lower()}`",
        f"- Outcome labels: `{json.dumps(selected.get('outcome_labels', []), sort_keys=True)}`",
        f"- Token IDs are public market metadata only: `{str(selected.get('token_ids_are_market_metadata_only') is True).lower()}`",
        f"- Selected market reason: {clean_text(normalized.get('selected_market_reason'))}",
        "",
        "## Strategy Summary",
        "",
    ]
    if signal:
        lines.extend(
            [
                f"- Signal status: `{signal.get('signal_status')}`",
                f"- Outcome: `{signal.get('outcome')}`",
                f"- Side: `{signal.get('side')}`",
                f"- Limit price: `{signal.get('limit_price')}`",
                f"- Size: `{signal.get('size')}`",
                f"- Reason: {clean_text(signal.get('reason'))}",
            ]
        )
    else:
        lines.extend(
            [
                "- Signal status: `no_signal`",
                f"- No-signal reason: {clean_text(no_signal.get('reason'))}",
            ]
        )
    lines.extend(
        [
            "",
            "## Risk Decision",
            "",
            f"- Risk decision: `{risk.get('risk_decision')}`",
            f"- Approved for paper intent: `{str(risk.get('approved_for_paper_intent') is True).lower()}`",
            f"- Operator summary: {clean_text(risk.get('operator_summary'))}",
            "",
            "## Paper Intent",
            "",
        ]
    )
    if intent:
        lines.extend(
            [
                f"- Paper intent status: `{intent.get('paper_intent_status')}`",
                f"- Paper intent ref: `{intent.get('paper_intent_ref')}`",
                "- Intent ref is execution identifier: `false`",
                f"- Outcome: `{intent.get('outcome')}`",
                f"- Side: `{intent.get('side')}`",
                f"- Limit price: `{intent.get('limit_price')}`",
                f"- Size: `{intent.get('size')}`",
                "- Intent is not order submission.",
            ]
        )
    else:
        lines.extend(
            [
                "- Paper intent status: `no_paper_intent`",
                f"- No-intent reason: {clean_text(no_signal.get('reason') or risk.get('operator_summary'))}",
            ]
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            *bullet_lines(f"{key}: `{path}`" for key, path in dict(value.get("artifact_paths", {})).items()),
            "",
            "## Next Operator Action",
            "",
            "- review only, no live action available",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PMBOT public market evidence paper loop 054.")
    parser.add_argument("--market", default="BTC", help="Market symbol or review label.")
    parser.add_argument("--strategy", default="tiny-momentum", help="Paper strategy name.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Generates review-only paper artifacts.")
    parser.add_argument("--query", default="", help="Optional public Gamma search query.")
    parser.add_argument("--slug", default="", help="Optional public Gamma market slug.")
    parser.add_argument("--tag-id", default="", help="Optional public Gamma tag id filter.")
    parser.add_argument("--limit", type=int, default=20, help="Public Gamma result limit.")
    parser.add_argument("--fixture-fallback", action="store_true", help="Use deterministic fallback if public fetch fails.")
    parser.add_argument("--offline-fixture-only", action="store_true", help="Skip network and use deterministic fallback.")
    parser.add_argument(
        "--artifacts-dir",
        "--artifact-dir",
        dest="artifacts_dir",
        default="",
        help="Optional output directory. Defaults to the 054 artifact directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print latest status JSON instead of concise text.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    _fail_closed_for_forbidden_flags(raw_args)
    args = build_parser().parse_args(raw_args)
    if args.dry_run is not True:
        raise SystemExit("public market paper loop requires --dry-run; live execution is blocked")
    try:
        result = run_public_market_paper_loop(
            market=args.market,
            strategy=args.strategy,
            dry_run=True,
            query=args.query,
            slug=args.slug,
            tag_id=args.tag_id,
            limit=args.limit,
            fixture_fallback=args.fixture_fallback,
            offline_fixture_only=args.offline_fixture_only,
            artifact_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
        )
    except PublicGammaFetchError as exc:
        raise SystemExit(f"public Gamma read-only fetch failed; fixture fallback not enabled: {exc}") from exc
    status = dict(result.get("latest_status", {}))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(render_public_market_paper_loop_telegram_status(status))
    return 0


def _build_evidence_pack(
    *,
    fetch_result: Mapping[str, Any],
    request_evidence: Mapping[str, Any],
    response_evidence: Mapping[str, Any],
    normalized: Mapping[str, Any],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    payload = fetch_result.get("data")
    candidate_summary = summarize_public_market_candidates(payload)
    evidence_snapshot = PublicMarketEvidenceSnapshot(
        source_name=clean_text(fetch_result.get("source_name")),
        source_type=clean_text(fetch_result.get("source_type")),
        event_count=int(candidate_summary.get("event_count", 0)),
        market_count=int(candidate_summary.get("market_count", 0)),
        selected_market_reason=clean_text(normalized.get("selected_market_reason")),
        response_snapshot_hash=clean_text(response_evidence.get("response_snapshot_hash")),
        generated_at=generated_at,
    ).to_dict()
    source = PublicMarketEvidenceSource(
        source_name=clean_text(fetch_result.get("source_name")),
        source_type=clean_text(fetch_result.get("source_type")),
        base_url=clean_text(fetch_result.get("base_url")),
        endpoint_path=clean_text(fetch_result.get("endpoint_path")),
        network_used=fetch_result.get("network_used") is True,
        generated_at=generated_at,
    ).to_dict()
    pack = PublicMarketEvidencePack(
        source=source,
        request=request_evidence,
        response=response_evidence,
        evidence_snapshot=evidence_snapshot,
        normalized_market_count=int(normalized.get("normalized_market_count", 0)),
        selected_market_reason=clean_text(normalized.get("selected_market_reason")),
        raw_response_hash=clean_text(response_evidence.get("raw_response_hash")),
        response_snapshot_hash=clean_text(response_evidence.get("response_snapshot_hash")),
        artifact_paths=artifact_paths,
        generated_at=generated_at,
    ).to_dict()
    pack["validation"] = validate_public_market_evidence_pack(pack)
    return pack


def _response_evidence_with_selection(
    *,
    fetch_result: Mapping[str, Any],
    normalized: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    response = dict(fetch_result.get("response_evidence", {}))
    source_type = clean_text(fetch_result.get("source_type"))
    response_hash = clean_text(response.get("raw_response_hash")) or hash_response_payload(fetch_result.get("data"))
    updated = PublicGammaResponseEvidence(
        source_name=clean_text(fetch_result.get("source_name")),
        source_type=source_type,
        base_url=clean_text(fetch_result.get("base_url")),
        endpoint_path=clean_text(fetch_result.get("endpoint_path")),
        response_timestamp_utc=clean_text(response.get("response_timestamp_utc")) or generated_at,
        status_code=response.get("status_code"),
        network_used=source_type == PUBLIC_GAMMA_SOURCE_TYPE,
        normalized_market_count=int(normalized.get("normalized_market_count", 0)),
        raw_response_hash=response_hash,
        response_snapshot_hash=clean_text(response.get("response_snapshot_hash")) or response_hash,
        selected_market_reason=clean_text(normalized.get("selected_market_reason")),
        generated_at=generated_at,
    ).to_dict()
    return updated


def _write_public_market_evidence_artifacts(
    *,
    paths: Mapping[str, Path],
    request_evidence: Mapping[str, Any],
    response_evidence: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
    normalized: Mapping[str, Any],
    fetch_error: Mapping[str, Any] | None,
) -> None:
    if fetch_error is not None:
        write_json(paths["fetch_error"], fetch_error)
    elif paths["fetch_error"].exists():
        paths["fetch_error"].unlink()
    write_json(paths["request_evidence"], request_evidence)
    write_json(paths["response_evidence"], response_evidence)
    write_json(paths["evidence_pack"], evidence_pack)
    write_json(paths["normalized_snapshot"], normalized)


def _write_public_market_paper_artifacts(
    *,
    paths: Mapping[str, Path],
    result: Mapping[str, Any],
    paper_result: Mapping[str, Any],
    status: Mapping[str, Any],
) -> None:
    _cleanup_conditional_paths(paths=paths, paper_result=paper_result)
    signal = paper_result.get("strategy_signal")
    no_signal = paper_result.get("no_signal")
    paper_intent = paper_result.get("paper_order_intent")
    if signal is not None:
        write_json(paths["strategy_signal"], signal)
    elif no_signal is not None:
        write_json(paths["strategy_signal"], no_signal)
    write_json(paths["risk"], paper_result.get("risk"))
    if paper_intent is not None:
        write_json(paths["order_intent"], paper_intent)
    if no_signal is not None:
        write_json(paths["no_signal"], no_signal)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_public_market_paper_loop_markdown(result))
    write_json(paths["latest_status"], status)


def _cleanup_conditional_paths(*, paths: Mapping[str, Path], paper_result: Mapping[str, Any]) -> None:
    if paper_result.get("paper_order_intent") is None and paths["order_intent"].exists():
        paths["order_intent"].unlink()
    if paper_result.get("no_signal") is None and paths["no_signal"].exists():
        paths["no_signal"].unlink()


def _write_fetch_error(path: Path, error: Mapping[str, Any]) -> None:
    write_json(path, error)


def _fetch_error_payload(error: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    value = dict(error or {})
    payload = {
        "contract_version": PUBLIC_MARKET_FETCH_ERROR_CONTRACT,
        "task_id": TASK_ID,
        "status": "public_gamma_fetch_failed",
        "source_name": clean_text(value.get("source_name") or PUBLIC_GAMMA_SOURCE_NAME),
        "source_type": clean_text(value.get("source_type") or PUBLIC_GAMMA_SOURCE_TYPE),
        "base_url": clean_text(value.get("base_url")),
        "endpoint_path": clean_text(value.get("endpoint_path")),
        "sanitized_query": dict(value.get("sanitized_query", {})),
        "request_method": "GET",
        "network_used": value.get("network_used") is True,
        "error_type": clean_text(value.get("error_type")),
        "message": clean_text(value.get("message")),
        "fixture_fallback_available": True,
        "generated_at": generated_at,
    }
    payload.update(public_market_safety_flags(network_used=payload["network_used"]))
    return payload


def _fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "public market paper loop is paper/review-only; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


if __name__ == "__main__":
    raise SystemExit(main())

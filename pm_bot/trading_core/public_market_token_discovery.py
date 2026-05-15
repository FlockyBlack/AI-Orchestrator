from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.public_gamma_market_client import PublicGammaFetchError, PublicGammaMarketClient
from pm_bot.trading_core.public_market_evidence_models import (
    PUBLIC_GAMMA_SOURCE_NAME,
    PUBLIC_GAMMA_SOURCE_TYPE,
    hash_response_payload,
)
from pm_bot.trading_core.public_market_token_discovery_models import (
    DISCOVERY_STATUS_MARKETS_WITHOUT_TOKENS,
    DISCOVERY_STATUS_NO_CANDIDATES,
    DISCOVERY_STATUS_READY,
    DISCOVERY_STATUS_UNAVAILABLE,
    PUBLIC_MARKET_TOKEN_DISCOVERY_LATEST_STATUS_CONTRACT,
    PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT,
    PublicMarketCandidate,
    PublicMarketTokenDiscoveryConfig,
    PublicOutcomeTokenCandidate,
    TASK_ID,
    build_public_market_token_discovery_redaction_policy,
    public_market_token_discovery_safety_flags,
    stable_public_token_discovery_id,
    validate_public_market_token_discovery_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/public_market_token_discovery_071a")
DEFAULT_LOCAL_ARTIFACT_CANDIDATES = (
    Path("pm_bot/trading_core/artifacts/public_market_paper_loop_054/normalized_public_market_snapshot_054.json"),
)

SOURCE_ORIGIN_NETWORK = "public_network"
SOURCE_ORIGIN_LOCAL_ARTIFACT = "local_artifact"
LOCAL_PUBLIC_ARTIFACT_SOURCE_TYPE = "public_local_artifact_read_only"

BTC_MARKET_KEYWORDS = {
    "BTC": ("btc", "bitcoin"),
    "ETH": ("eth", "ethereum", "ether"),
    "SOL": ("sol", "solana"),
    "XRP": ("xrp", "ripple"),
}

TOKEN_ID_FIELDS = ("clobTokenIds", "clob_token_ids", "tokenIds", "token_ids")


def public_market_token_discovery_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "public_market_token_discovery_071a_result.json",
        "latest_status": root / "latest_public_market_token_discovery_status_071a.json",
        "market_candidates": root / "public_market_candidates_071a.json",
        "outcome_token_candidates": root / "public_outcome_token_candidates_071a.json",
        "redaction_policy": root / "public_market_token_discovery_redaction_policy_071a.json",
        "operator_summary": root / "public_market_token_discovery_operator_summary_071a.md",
    }


def run_public_market_token_discovery(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    query: str = "",
    slug: str = "",
    tag_id: str = "",
    limit: int = 25,
    artifact_dir: str | Path | None = None,
    local_artifact_paths: Sequence[str | Path] | None = None,
    public_client: PublicGammaMarketClient | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("public market token discovery requires --dry-run")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy) or "tiny-momentum"
    paths = public_market_token_discovery_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    config = PublicMarketTokenDiscoveryConfig(
        market=market_symbol,
        strategy=strategy_name,
        query=clean_text(query),
        slug=clean_text(slug),
        tag_id=clean_text(tag_id),
        limit=limit,
        dry_run=True,
        generated_at=generated_at,
    ).to_dict()

    source_records: list[dict[str, Any]] = []
    source_errors: list[dict[str, Any]] = []
    source_records.extend(
        _load_local_source_records(
            local_artifact_paths=local_artifact_paths,
            market=market_symbol,
            generated_at=generated_at,
            source_errors=source_errors,
        )
    )
    network_used = False

    if not source_records:
        client = public_client or PublicGammaMarketClient()
        try:
            fetch_result = client.search_public_markets(
                market=market_symbol,
                query=query,
                slug=slug,
                tag_id=tag_id,
                limit=limit,
                generated_at=generated_at,
            )
            source_records.append(
                {
                    "source_name": clean_text(fetch_result.get("source_name")) or PUBLIC_GAMMA_SOURCE_NAME,
                    "source_type": clean_text(fetch_result.get("source_type")) or PUBLIC_GAMMA_SOURCE_TYPE,
                    "source_origin": SOURCE_ORIGIN_NETWORK,
                    "source_path": clean_text(fetch_result.get("endpoint_path")),
                    "payload": fetch_result.get("data"),
                    "network_used": fetch_result.get("network_used") is True,
                    "source_payload_hash": hash_response_payload(fetch_result.get("data")),
                }
            )
            network_used = fetch_result.get("network_used") is True
        except PublicGammaFetchError as exc:
            source_errors.append(_source_error_from_exception(exc, generated_at=generated_at))
        except Exception as exc:
            source_errors.append(
                {
                    "contract_version": "pmbot_public_market_token_discovery_source_error_071a.v1",
                    "task_id": TASK_ID,
                    "status": "public_source_unavailable",
                    "source_name": PUBLIC_GAMMA_SOURCE_NAME,
                    "source_type": PUBLIC_GAMMA_SOURCE_TYPE,
                    "source_origin": SOURCE_ORIGIN_NETWORK,
                    "error_type": type(exc).__name__,
                    "message": clean_text(exc),
                    "generated_at": generated_at,
                    **public_market_token_discovery_safety_flags(network_used=True),
                }
            )
            network_used = True

    market_candidates, token_candidates = _discover_source_backed_candidates(
        source_records=source_records,
        market=market_symbol,
        query=query,
        slug=slug,
        generated_at=generated_at,
    )
    status_name = _status_name(
        source_records=source_records,
        market_candidates=market_candidates,
        token_candidates=token_candidates,
    )
    redaction_policy = build_public_market_token_discovery_redaction_policy(generated_at=generated_at)
    latest_status = build_latest_public_market_token_discovery_status(
        status=status_name,
        market=market_symbol,
        strategy=strategy_name,
        market_candidates=market_candidates,
        token_candidates=token_candidates,
        source_errors=source_errors,
        artifact_paths=path_refs,
        network_used=network_used,
        generated_at=generated_at,
    )
    result = {
        "contract_version": PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status_name,
        "market": market_symbol,
        "strategy": strategy_name,
        "dry_run": True,
        "config": config,
        "source_records_attempted": len(source_records),
        "source_errors": source_errors,
        "market_candidate_count": len(market_candidates),
        "outcome_token_candidate_count": len(token_candidates),
        "market_candidates": market_candidates,
        "outcome_token_candidates": token_candidates,
        "latest_status": latest_status,
        "redaction_policy": redaction_policy,
        "artifact_paths": path_refs,
        "generated_at": generated_at,
        **public_market_token_discovery_safety_flags(network_used=network_used),
    }
    result["validation"] = validate_public_market_token_discovery_result(result)

    _write_public_market_token_discovery_artifacts(
        paths=paths,
        result=result,
        latest_status=latest_status,
        market_candidates=market_candidates,
        token_candidates=token_candidates,
        redaction_policy=redaction_policy,
    )
    return result


def build_latest_public_market_token_discovery_status(
    *,
    status: str,
    market: str,
    strategy: str,
    market_candidates: Sequence[Mapping[str, Any]],
    token_candidates: Sequence[Mapping[str, Any]],
    source_errors: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    network_used: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": PUBLIC_MARKET_TOKEN_DISCOVERY_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "market_candidate_count": len(market_candidates),
        "outcome_token_candidate_count": len(token_candidates),
        "source_error_count": len(source_errors),
        "result_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "market_candidates_path": clean_text(artifact_paths.get("market_candidates")),
        "outcome_token_candidates_path": clean_text(artifact_paths.get("outcome_token_candidates")),
        "redaction_policy_path": clean_text(artifact_paths.get("redaction_policy")),
        "operator_summary_path": clean_text(artifact_paths.get("operator_summary")),
        "live_execution": "blocked",
        "next_operator_action": _next_operator_action(status),
        "generated_at": generated_at,
    }
    value.update(public_market_token_discovery_safety_flags(network_used=network_used))
    return value


def render_public_market_token_discovery_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    return "\n".join(
        [
            "Public market token discovery completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy'))}",
            f"Market candidates: {int(value.get('market_candidate_count', 0) or 0)}",
            f"Outcome token candidates: {int(value.get('outcome_token_candidate_count', 0) or 0)}",
            "Live execution: blocked",
            f"Next action: {clean_text(latest.get('next_operator_action'))}",
            f"Artifact: {clean_text(latest.get('result_path'))}",
        ]
    )


def render_public_market_token_discovery_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    market_candidates = [dict(row) for row in value.get("market_candidates", []) if isinstance(row, Mapping)]
    token_candidates = [dict(row) for row in value.get("outcome_token_candidates", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Public Market Token Discovery 071A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        f"- Strategy: `{value.get('strategy')}`",
        f"- Market candidates: `{len(market_candidates)}`",
        f"- Outcome token candidates: `{len(token_candidates)}`",
        "- Mode: `public read-only discovery`",
        "- live execution blocked",
        "- private_key_read=false",
        "- wallet_connection_attempted=false",
        "- signing_attempted=false",
        "- order_submission_attempted=false",
        "- order_cancellation_attempted=false",
        "- authenticated_request_performed=false",
        "- browser_automation_added=false",
        "- scheduler_or_daemon_added=false",
        "- allowed_for_live=false",
        "",
        "## Source-Backed Markets",
        "",
        *bullet_lines(
            f"`{row.get('market_slug') or row.get('market_id')}` token candidates `{row.get('outcome_token_candidate_count')}` source `{row.get('source_type')}`"
            for row in market_candidates[:20]
        ),
        "",
        "## Source-Backed Outcome Tokens",
        "",
        *bullet_lines(
            f"`{row.get('market_slug')}` `{row.get('outcome_name')}` token_id `{row.get('token_id')}` source_field `{row.get('source_field')}`"
            for row in token_candidates[:20]
        ),
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"{key}: `{path}`" for key, path in dict(value.get("artifact_paths", {})).items()),
        "",
        "## Operator Boundary",
        "",
        "- This adapter discovers public metadata only.",
        "- It does not create, sign, submit, or cancel anything.",
        "- It does not use wallets, private keys, authenticated trading headers, browser automation, or background loops.",
        "- Empty token candidates mean no source-backed token_id was available; nothing is invented.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _load_local_source_records(
    *,
    local_artifact_paths: Sequence[str | Path] | None,
    market: str,
    generated_at: str,
    source_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    requested_paths = list(local_artifact_paths or DEFAULT_LOCAL_ARTIFACT_CANDIDATES)
    records: list[dict[str, Any]] = []
    for raw_path in requested_paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            continue
        try:
            payload = load_json_object(path, label="public market token discovery local artifact")
        except Exception as exc:
            source_errors.append(
                {
                    "contract_version": "pmbot_public_market_token_discovery_source_error_071a.v1",
                    "task_id": TASK_ID,
                    "status": "local_artifact_unreadable",
                    "source_origin": SOURCE_ORIGIN_LOCAL_ARTIFACT,
                    "source_path": normalize_path(path),
                    "error_type": type(exc).__name__,
                    "message": clean_text(exc),
                    "generated_at": generated_at,
                    **public_market_token_discovery_safety_flags(network_used=False),
                }
            )
            continue
        record = _source_record_from_local_artifact(payload, path=path, market=market, generated_at=generated_at)
        if record:
            records.append(record)
    return records


def _source_record_from_local_artifact(
    payload: Mapping[str, Any],
    *,
    path: Path,
    market: str,
    generated_at: str,
) -> dict[str, Any] | None:
    value = dict(payload or {})
    source_type = clean_text(value.get("source_type"))
    source_name = clean_text(value.get("source_name"))
    selected = dict(value.get("selected_market", {})) if isinstance(value.get("selected_market"), Mapping) else {}
    snapshot = dict(value.get("market_snapshot", {})) if isinstance(value.get("market_snapshot"), Mapping) else {}
    if source_type != PUBLIC_GAMMA_SOURCE_TYPE:
        return None
    if not selected and not snapshot:
        return None
    token_ids = selected.get("public_market_token_ids") or snapshot.get("public_market_token_ids") or []
    market_payload = {
        "id": selected.get("market_id") or snapshot.get("market_id"),
        "slug": selected.get("market_slug") or snapshot.get("market_slug"),
        "question": selected.get("question") or snapshot.get("question"),
        "active": selected.get("active", snapshot.get("active")),
        "closed": selected.get("closed", snapshot.get("closed")),
        "outcomes": selected.get("outcome_labels") or snapshot.get("outcome_labels") or [],
        "clobTokenIds": token_ids,
    }
    event_payload = {
        "id": selected.get("event_id") or snapshot.get("event_id"),
        "slug": selected.get("event_slug") or snapshot.get("event_slug"),
        "title": selected.get("event_title") or snapshot.get("event_title"),
    }
    source_payload = {"events": [{**event_payload, "markets": [market_payload]}], "source_market": market}
    return {
        "source_name": source_name or "public_gamma_local_artifact",
        "source_type": LOCAL_PUBLIC_ARTIFACT_SOURCE_TYPE,
        "original_source_type": source_type,
        "source_origin": SOURCE_ORIGIN_LOCAL_ARTIFACT,
        "source_path": normalize_path(path),
        "payload": source_payload,
        "network_used": False,
        "source_payload_hash": hash_response_payload(value),
        "local_artifact_generated_at": clean_text(value.get("generated_at")) or generated_at,
    }


def _source_error_from_exception(exc: PublicGammaFetchError, *, generated_at: str) -> dict[str, Any]:
    error_payload = dict(getattr(exc, "error_payload", {}) or {})
    return {
        "contract_version": "pmbot_public_market_token_discovery_source_error_071a.v1",
        "task_id": TASK_ID,
        "status": "public_source_unavailable",
        "source_name": clean_text(error_payload.get("source_name") or PUBLIC_GAMMA_SOURCE_NAME),
        "source_type": clean_text(error_payload.get("source_type") or PUBLIC_GAMMA_SOURCE_TYPE),
        "source_origin": SOURCE_ORIGIN_NETWORK,
        "endpoint_path": clean_text(error_payload.get("endpoint_path")),
        "sanitized_query": dict(error_payload.get("sanitized_query", {})),
        "error_type": clean_text(error_payload.get("error_type")),
        "message": clean_text(error_payload.get("message") or exc),
        "generated_at": generated_at,
        **public_market_token_discovery_safety_flags(network_used=True),
    }


def _discover_source_backed_candidates(
    *,
    source_records: Sequence[Mapping[str, Any]],
    market: str,
    query: str,
    slug: str,
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    market_candidates: list[dict[str, Any]] = []
    token_candidates: list[dict[str, Any]] = []
    for source_record in source_records:
        source_value = dict(source_record)
        source_payload_hash = clean_text(source_value.get("source_payload_hash")) or hash_response_payload(
            source_value.get("payload")
        )
        for index, row in enumerate(_extract_market_rows(source_value.get("payload"))):
            market_payload = dict(row.get("market", {}))
            event_payload = dict(row.get("event", {}))
            if not _is_requested_market(market_payload, event_payload=event_payload, market=market, query=query, slug=slug):
                continue
            if _is_closed_market(market_payload, event_payload):
                continue
            market_id = _first_text(market_payload.get("id"), market_payload.get("market_id"), market_payload.get("conditionId"))
            market_slug = _first_text(market_payload.get("slug"), market_payload.get("market_slug"))
            question = _first_text(market_payload.get("question"), market_payload.get("title"), market_payload.get("name"))
            if not (market_id or market_slug or question):
                continue
            market_candidate_id = stable_public_token_discovery_id(
                "public-market-token-market-candidate-071a",
                {
                    "market_id": market_id,
                    "market_slug": market_slug,
                    "question": question,
                    "source_payload_hash": source_payload_hash,
                    "index": index,
                },
            )
            labels = _outcome_labels(market_payload)
            token_rows = _source_token_rows(market_payload)
            valid_token_rows = [
                token_row for token_row in token_rows if _source_token_id_allowed(token_row.get("token_id"))
            ]
            market_candidate = PublicMarketCandidate(
                market_candidate_id=market_candidate_id,
                market_id=market_id,
                market_slug=market_slug,
                question=question,
                event_id=_first_text(event_payload.get("id"), event_payload.get("event_id")),
                event_slug=_first_text(event_payload.get("slug"), event_payload.get("event_slug")),
                active=_bool_value(market_payload.get("active"), event_payload.get("active")),
                closed=_bool_value(market_payload.get("closed"), event_payload.get("closed")),
                source_name=clean_text(source_value.get("source_name")),
                source_type=clean_text(source_value.get("source_type")),
                source_origin=clean_text(source_value.get("source_origin")),
                source_path=clean_text(source_value.get("source_path")),
                source_backed=True,
                source_payload_hash=source_payload_hash,
                outcome_count=len(labels),
                outcome_token_candidate_count=len(valid_token_rows),
                selection_reason=_selection_reason(market=market, query=query, slug=slug),
                generated_at=generated_at,
            ).to_dict()
            market_candidates.append(market_candidate)
            for token_row in valid_token_rows:
                outcome_index = int(token_row.get("outcome_index", 0) or 0)
                outcome_name = clean_text(_list_item(labels, outcome_index)) or f"outcome_{outcome_index + 1}"
                token_id = clean_text(token_row.get("token_id"))
                token_candidates.append(
                    PublicOutcomeTokenCandidate(
                        token_candidate_id=stable_public_token_discovery_id(
                            "public-market-token-outcome-candidate-071a",
                            {
                                "market_candidate_id": market_candidate_id,
                                "outcome_index": outcome_index,
                                "token_id": token_id,
                                "source_payload_hash": source_payload_hash,
                            },
                        ),
                        market_candidate_id=market_candidate_id,
                        market_id=market_id,
                        market_slug=market_slug,
                        question=question,
                        outcome_name=outcome_name,
                        outcome_index=outcome_index,
                        token_id=token_id,
                        source_field=clean_text(token_row.get("source_field")),
                        source_name=clean_text(source_value.get("source_name")),
                        source_type=clean_text(source_value.get("source_type")),
                        source_origin=clean_text(source_value.get("source_origin")),
                        source_path=clean_text(source_value.get("source_path")),
                        source_backed=True,
                        source_payload_hash=source_payload_hash,
                        generated_at=generated_at,
                    ).to_dict()
                )
    return _dedupe_by_id(market_candidates, "market_candidate_id"), _dedupe_by_id(token_candidates, "token_candidate_id")


def _extract_market_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            if isinstance(item, Mapping):
                rows.extend(_rows_from_mapping(item, index=index))
    elif isinstance(payload, Mapping):
        for key in ("events", "data", "results"):
            nested = payload.get(key)
            if isinstance(nested, list):
                for index, item in enumerate(nested):
                    if isinstance(item, Mapping):
                        rows.extend(_rows_from_mapping(item, index=index))
                return rows
        rows.extend(_rows_from_mapping(payload, index=0))
    return rows


def _rows_from_mapping(value: Mapping[str, Any], *, index: int) -> list[dict[str, Any]]:
    row = dict(value)
    markets = row.get("markets")
    if isinstance(markets, list):
        return [
            {"event": row, "market": dict(market), "index": index + offset}
            for offset, market in enumerate(markets)
            if isinstance(market, Mapping)
        ]
    if any(clean_text(row.get(key)) for key in ("question", "slug", "title", "market_id", "id")):
        return [{"event": {}, "market": row, "index": index}]
    return []


def _source_token_rows(market_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    market_value = dict(market_payload)
    rows: list[dict[str, Any]] = []
    for field in TOKEN_ID_FIELDS:
        parsed = _parse_list(market_value.get(field))
        if not parsed:
            continue
        for index, token_id in enumerate(parsed):
            if isinstance(token_id, Mapping):
                token_text = _first_text(token_id.get("token_id"), token_id.get("id"))
            else:
                token_text = clean_text(token_id)
            if token_text:
                rows.append({"token_id": token_text, "outcome_index": index, "source_field": field})
        if rows:
            return rows
    return rows


def _source_token_id_allowed(token_id: Any) -> bool:
    text = clean_text(token_id)
    if not text:
        return False
    lowered = text.lower()
    return not any(marker in lowered for marker in ("fake", "fixture", "placeholder", "sample", "mock", "demo-token"))


def _is_requested_market(
    market_payload: Mapping[str, Any],
    *,
    event_payload: Mapping[str, Any],
    market: str,
    query: str,
    slug: str,
) -> bool:
    haystack = _candidate_haystack(market_payload, event_payload)
    requested_slug = clean_text(slug).lower()
    if requested_slug:
        return requested_slug in haystack
    keywords = BTC_MARKET_KEYWORDS.get(clean_text(market).upper(), (clean_text(market).lower(),))
    if not any(keyword and keyword in haystack for keyword in keywords):
        return False
    query_terms = [term for term in clean_text(query).lower().split() if term]
    return all(term in haystack for term in query_terms)


def _candidate_haystack(market_payload: Mapping[str, Any], event_payload: Mapping[str, Any]) -> str:
    return " ".join(
        clean_text(item).lower()
        for item in (
            market_payload.get("id"),
            market_payload.get("market_id"),
            market_payload.get("conditionId"),
            market_payload.get("question"),
            market_payload.get("title"),
            market_payload.get("name"),
            market_payload.get("slug"),
            event_payload.get("id"),
            event_payload.get("title"),
            event_payload.get("name"),
            event_payload.get("slug"),
            json.dumps(market_payload.get("tags", ""), sort_keys=True, default=str),
        )
    )


def _is_closed_market(market_payload: Mapping[str, Any], event_payload: Mapping[str, Any]) -> bool:
    resolved = _bool_or_none(market_payload.get("resolved"), market_payload.get("outcomeResolved"))
    closed = _bool_or_none(market_payload.get("closed"), event_payload.get("closed"), market_payload.get("archived"))
    active = _bool_or_none(market_payload.get("active"), event_payload.get("active"))
    return resolved is True or closed is True or active is False


def _status_name(
    *,
    source_records: Sequence[Mapping[str, Any]],
    market_candidates: Sequence[Mapping[str, Any]],
    token_candidates: Sequence[Mapping[str, Any]],
) -> str:
    if not source_records:
        return DISCOVERY_STATUS_UNAVAILABLE
    if token_candidates:
        return DISCOVERY_STATUS_READY
    if market_candidates:
        return DISCOVERY_STATUS_MARKETS_WITHOUT_TOKENS
    return DISCOVERY_STATUS_NO_CANDIDATES


def _next_operator_action(status: str) -> str:
    if status == DISCOVERY_STATUS_READY:
        return "review source-backed market and outcome token candidates only"
    if status == DISCOVERY_STATUS_MARKETS_WITHOUT_TOKENS:
        return "review markets; no source-backed token_id is available"
    if status == DISCOVERY_STATUS_UNAVAILABLE:
        return "public discovery unavailable; do not proceed"
    return "no source-backed candidate available; do not proceed"


def _selection_reason(*, market: str, query: str, slug: str) -> str:
    if clean_text(slug):
        return f"matched requested public market slug {clean_text(slug)}"
    if clean_text(query):
        return f"matched {clean_text(market).upper()} public market query {clean_text(query)}"
    return f"matched {clean_text(market).upper()} public market keywords in source-backed metadata"


def _write_public_market_token_discovery_artifacts(
    *,
    paths: Mapping[str, Path],
    result: Mapping[str, Any],
    latest_status: Mapping[str, Any],
    market_candidates: Sequence[Mapping[str, Any]],
    token_candidates: Sequence[Mapping[str, Any]],
    redaction_policy: Mapping[str, Any],
) -> None:
    write_json(
        paths["market_candidates"],
        {
            "contract_version": PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT + ".market_candidates",
            "task_id": TASK_ID,
            "market_candidate_count": len(market_candidates),
            "market_candidates": list(market_candidates),
            "generated_at": result.get("generated_at"),
            **public_market_token_discovery_safety_flags(network_used=result.get("network_used") is True),
        },
    )
    write_json(
        paths["outcome_token_candidates"],
        {
            "contract_version": PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT + ".outcome_token_candidates",
            "task_id": TASK_ID,
            "outcome_token_candidate_count": len(token_candidates),
            "outcome_token_candidates": list(token_candidates),
            "generated_at": result.get("generated_at"),
            **public_market_token_discovery_safety_flags(network_used=result.get("network_used") is True),
        },
    )
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary"], render_public_market_token_discovery_markdown(result))


def _dedupe_by_id(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        row_value = dict(row)
        row_id = clean_text(row_value.get(key))
        if row_id in seen:
            continue
        seen.add(row_id)
        deduped.append(row_value)
    return deduped


def _outcome_labels(market_payload: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    for item in _parse_list(market_payload.get("outcomes") or market_payload.get("outcome")):
        if isinstance(item, Mapping):
            label = _first_text(item.get("name"), item.get("label"), item.get("outcome"))
        else:
            label = clean_text(item)
        if label:
            labels.append(label)
    return labels


def _parse_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = _try_json(value)
        if isinstance(parsed, list):
            return parsed
        text = clean_text(value)
        return [text] if text else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return list(value)
    return [value]


def _try_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _list_item(value: Sequence[Any], index: int) -> Any:
    if index < 0 or index >= len(value):
        return None
    return value[index]


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _bool_value(*values: Any) -> bool:
    parsed = _bool_or_none(*values)
    return parsed is True


def _bool_or_none(*values: Any) -> bool | None:
    for value in values:
        if isinstance(value, bool):
            return value
        text = clean_text(value).lower()
        if text in {"true", "1", "yes", "open", "active"}:
            return True
        if text in {"false", "0", "no", "closed", "inactive"}:
            return False
    return None

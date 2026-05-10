from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

PUBLIC_FETCH_FAILURE_DIAGNOSIS_CONTRACT_VERSION = "pmbot_public_fetch_failure_diagnosis.v1"
SOURCE_TASK_ID = "ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST"
FAILURE_CATEGORY_KEYS = [
    "timeout",
    "dns_error",
    "http_error",
    "content_type_rejected",
    "url_invalid",
    "source_unavailable",
    "unknown",
]


def build_public_fetch_failure_diagnosis(
    *,
    execution_summary: Mapping[str, Any],
    diagnosis_id: str = "public-fetch-failure-diagnosis-009",
    source_task_id: str = SOURCE_TASK_ID,
) -> dict[str, Any]:
    failed_requests = _failed_requests(execution_summary)
    per_request = [_diagnose_request(row) for row in failed_requests]
    categories = {key: 0 for key in FAILURE_CATEGORY_KEYS}
    for item in per_request:
        categories[item["failure_category"]] += 1
    return {
        "contract_version": PUBLIC_FETCH_FAILURE_DIAGNOSIS_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "diagnosis_id": diagnosis_id,
        "source_task_id": source_task_id,
        "attempted_request_count": int(execution_summary.get("request_count_attempted") or 0),
        "succeeded_request_count": int(execution_summary.get("request_count_succeeded") or 0),
        "failed_request_count": int(execution_summary.get("request_count_failed") or len(failed_requests)),
        "blocked_request_count": int(execution_summary.get("request_count_blocked") or 0),
        "failed_requests": failed_requests,
        "failure_categories": categories,
        "per_request_diagnosis": per_request,
        "safe_recovery_actions": _safe_recovery_actions(per_request),
        "url_manifest_fix_candidates": [_url_fix_candidate(item) for item in per_request],
        "do_not_retry_without_review": True,
        "no_live_fetch_performed_in_this_task": True,
        "no_real_trade_decision": True,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "safety_summary": safe_summary(),
    }


def write_public_fetch_failure_diagnosis(
    *,
    execution_summary_path: str | Path,
    out_json_path: str | Path,
    out_md_path: str | Path,
    diagnosis_id: str = "public-fetch-failure-diagnosis-009",
) -> dict[str, Any]:
    summary = load_json_object(execution_summary_path, label="PRACTICAL-008 execution summary")
    diagnosis = build_public_fetch_failure_diagnosis(execution_summary=summary, diagnosis_id=diagnosis_id)
    write_json(out_json_path, diagnosis)
    write_text(out_md_path, render_public_fetch_failure_diagnosis_markdown(diagnosis))
    return diagnosis


def render_public_fetch_failure_diagnosis_markdown(diagnosis: Mapping[str, Any]) -> str:
    lines = [
        "# Public fetch failure diagnosis",
        "",
        "## Request summary",
        "",
        f"- Attempted: {diagnosis.get('attempted_request_count')}",
        f"- Succeeded: {diagnosis.get('succeeded_request_count')}",
        f"- Failed: {diagnosis.get('failed_request_count')}",
        f"- Blocked: {diagnosis.get('blocked_request_count')}",
        "",
        "## Failed request table",
        "",
        "| Market | Source URL | Category | Likely cause |",
        "| --- | --- | --- | --- |",
    ]
    for item in diagnosis.get("per_request_diagnosis", []):
        lines.append(
            f"| `{item.get('market_id')}` | `{item.get('source_url')}` | `{item.get('failure_category')}` | {item.get('likely_cause')} |"
        )
    lines.extend(
        [
            "",
            "## Likely causes",
            "",
            *bullet_lines(
                f"`{key}`: {value}" for key, value in diagnosis.get("failure_categories", {}).items() if value
            ),
            "",
            "## Safe recovery actions",
            "",
            *bullet_lines(diagnosis.get("safe_recovery_actions", [])),
            "",
            "## URL manifest fixes needed",
            "",
            *bullet_lines(
                f"`{item.get('source_url')}` -> `{item.get('recommended_fix_type')}`"
                for item in diagnosis.get("url_manifest_fix_candidates", [])
            ),
            "",
            "## What not to do",
            "",
            "- Do not repeat these source requests until an operator reviews the URL/source fix candidates.",
            "- Do not use authenticated endpoints, cookies, browser automation, API keys, wallet paths, order paths, or trading paths.",
            "- Do not treat source accessibility failures as market outcome evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def _failed_requests(execution_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = execution_summary.get("fetch_results")
    if not isinstance(rows, list):
        rows = execution_summary.get("failed_requests", [])
    failed = []
    for row in rows:
        if isinstance(row, Mapping) and row.get("result_status", "failed") == "failed":
            failed.append({key: row.get(key) for key in row})
    return failed


def _diagnose_request(row: Mapping[str, Any]) -> dict[str, Any]:
    error = clean_text(row.get("error"))
    category = _failure_category(error)
    return {
        "request_intent_id": clean_text(row.get("request_intent_id")),
        "market_id": clean_text(row.get("market_id")),
        "market_title": clean_text(row.get("market_title")),
        "source_name": clean_text(row.get("source_name")),
        "source_category": clean_text(row.get("source_category")),
        "source_url": clean_text(row.get("source_url")),
        "error": error,
        "failure_category": category,
        "likely_cause": _likely_cause(category, error),
        "safe_recovery_action": _safe_recovery_action(category),
    }


def _failure_category(error: str) -> str:
    lowered = error.lower()
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if "name or service" in lowered or "getaddrinfo" in lowered or "dns" in lowered:
        return "dns_error"
    if "status" in lowered or "403" in lowered or "404" in lowered or "500" in lowered:
        return "http_error"
    if "content type" in lowered or "content-type" in lowered:
        return "content_type_rejected"
    if "invalid url" in lowered or "unknown url type" in lowered:
        return "url_invalid"
    if "certificate_verify_failed" in lowered or "redirect blocked" in lowered or "ssl:" in lowered:
        return "source_unavailable"
    return "unknown"


def _likely_cause(category: str, error: str) -> str:
    if category == "http_error" and "403" in error:
        return "The public site denied this simple read-only request in PRACTICAL-008."
    if category == "source_unavailable" and "certificate" in error.lower():
        return "The URL may require certificate-chain handling or a different official page."
    if category == "source_unavailable" and "redirect blocked" in error.lower():
        return "The configured URL redirects to a different host/path and the fetcher intentionally blocked redirects."
    return {
        "timeout": "The public source did not respond inside the finite request window.",
        "dns_error": "The hostname could not be resolved by the local runtime.",
        "content_type_rejected": "The response content type was not accepted by the controlled fetch policy.",
        "url_invalid": "The URL is malformed or unsupported by the local fetcher.",
        "unknown": "The saved error does not map cleanly to a known category.",
    }.get(category, "The saved error requires operator review.")


def _safe_recovery_action(category: str) -> str:
    return {
        "http_error": "Verify the URL manually and prefer an alternative official public source if access remains denied.",
        "source_unavailable": "Replace or normalize the URL only after operator review of the source category and redirect/certificate behavior.",
        "timeout": "Mark the source for later manual review before any retry.",
        "dns_error": "Verify the hostname and source domain manually.",
        "content_type_rejected": "Choose a source page with a fetch-safe public document format.",
        "url_invalid": "Correct the manifest URL syntax before any future controlled fetch.",
        "unknown": "Keep the request out of future fetch packets until an operator classifies the error.",
    }[category]


def _safe_recovery_actions(per_request: Sequence[Mapping[str, Any]]) -> list[str]:
    actions = []
    for item in per_request:
        action = clean_text(item.get("safe_recovery_action"))
        if action and action not in actions:
            actions.append(action)
    actions.append("Keep all recovery work non-executable until a later scoped task is approved.")
    return actions


def _url_fix_candidate(item: Mapping[str, Any]) -> dict[str, Any]:
    category = clean_text(item.get("failure_category"))
    fix_type = {
        "http_error": "use_alternative_official_source",
        "source_unavailable": "replace_url",
        "timeout": "retry_later",
        "dns_error": "verify_url_manually",
        "content_type_rejected": "replace_url",
        "url_invalid": "verify_url_manually",
        "unknown": "verify_url_manually",
    }.get(category, "verify_url_manually")
    return {
        "request_intent_id": clean_text(item.get("request_intent_id")),
        "market_id": clean_text(item.get("market_id")),
        "source_url": clean_text(item.get("source_url")),
        "failure_category": category,
        "recommended_fix_type": fix_type,
        "requires_operator_review": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose saved PRACTICAL-008 public fetch failures.")
    parser.add_argument("--execution-summary", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    write_public_fetch_failure_diagnosis(
        execution_summary_path=args.execution_summary,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

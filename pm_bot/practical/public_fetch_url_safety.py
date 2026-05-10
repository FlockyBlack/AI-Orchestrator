from __future__ import annotations

import argparse
import ipaddress
from typing import Any, Mapping, Sequence
from urllib.parse import ParseResult, parse_qsl, urlencode, urlparse, urlunparse

from pm_bot.practical.practical_io import clean_text, load_json_object, write_json, write_text
from pm_bot.practical.public_source_registry import validate_source_category

URL_SAFETY_CONTRACT_VERSION = "pmbot_public_fetch_url_safety.v1"

BLOCKED_SOURCE_CATEGORIES = {
    "authenticated_endpoint",
    "browser_session_cookie_based_source",
    "order_endpoint",
    "private_api_key_endpoint",
    "source_requiring_bypass_or_automation",
    "source_requiring_kyc_or_login",
    "trading_endpoint",
    "wallet_signing_endpoint",
}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "cookie",
    "key",
    "password",
    "private_key",
    "secret",
    "session",
    "signature",
    "token",
}
BLOCKED_PATH_HINTS = {
    "auth",
    "buy",
    "cancel-order",
    "clob",
    "kyc",
    "login",
    "oauth",
    "order",
    "orders",
    "private-key",
    "sell",
    "session",
    "sign",
    "signin",
    "signature",
    "trade",
    "trading",
    "wallet",
    "withdraw",
}
LOCAL_HOSTNAMES = {"localhost", "localhost.localdomain"}
INTERNAL_HOST_SUFFIXES = (".internal", ".local", ".lan", ".home", ".test")


def validate_public_fetch_request_intent(
    intent: Mapping[str, Any],
    *,
    request_index: int = 1,
    max_request_count: int = 5,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    """Validate one manifest request intent before any network access."""

    blockers: list[str] = []
    warnings: list[str] = []
    method = clean_text(intent.get("method") or intent.get("http_method") or "GET").upper()
    source_category = clean_text(intent.get("source_category"))
    source_reference = _source_reference(intent)
    parsed = urlparse(source_reference)
    category_validation = validate_source_category(source_category)

    if request_index < 1:
        blockers.append("request_index must be positive")
    if max_request_count < 1:
        blockers.append("max_request_count must be positive")
    if request_index > max_request_count:
        blockers.append("request count exceeds approved max request count")
    if method != "GET":
        blockers.append("only GET requests are allowed")
    if _is_placeholder_reference(source_reference):
        blockers.append("source reference is a placeholder, not an explicit URL")
    if parsed.scheme.lower() not in {"http", "https"}:
        blockers.append("URL scheme must be http or https")
    if parsed.username or parsed.password:
        blockers.append("URL must not contain credentials")
    if source_category in BLOCKED_SOURCE_CATEGORIES or category_validation["blocked"]:
        blockers.append(f"source category is blocked or unknown: {source_category}")
    if intent.get("requires_auth") is True or intent.get("auth_required") is True:
        blockers.append("request intent requires authentication")
    if intent.get("credentials_required") is True:
        blockers.append("request intent requires credentials")
    if intent.get("cookies_required") is True:
        blockers.append("request intent requires cookies")
    if intent.get("wallet_or_signing_required") is True or intent.get("wallet_required") is True:
        blockers.append("request intent requires wallet or signing access")
    if intent.get("trading_or_order_endpoint") is True or intent.get("trading_endpoint") is True or intent.get("order_endpoint") is True:
        blockers.append("request intent includes trading or order endpoint flags")
    blockers.extend(_blocked_header_reasons(intent))
    blockers.extend(_blocked_query_reasons(parsed))
    blockers.extend(_blocked_path_hint_reasons(parsed))

    host = clean_text(parsed.hostname or "")
    if parsed.scheme and not host:
        blockers.append("URL host is required")
    elif host:
        host_blockers, host_warnings = _validate_host(host, fixture_mode=fixture_mode)
        blockers.extend(host_blockers)
        warnings.extend(host_warnings)

    if "placeholder" in source_category and parsed.scheme.lower() in {"http", "https"}:
        warnings.append("source category is a placeholder category with a concrete URL reference")

    return {
        "contract_version": URL_SAFETY_CONTRACT_VERSION,
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "source_category": source_category,
        "method": method,
        "allowed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "sanitized_url_reference": sanitize_url_reference(source_reference),
        "fixture_mode": fixture_mode,
        "request_index": request_index,
        "max_request_count": max_request_count,
    }


def validate_public_fetch_request_batch(
    intents: Sequence[Mapping[str, Any]],
    *,
    max_request_count: int = 5,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    rows = [
        validate_public_fetch_request_intent(
            intent,
            request_index=index,
            max_request_count=max_request_count,
            fixture_mode=fixture_mode,
        )
        for index, intent in enumerate(intents, start=1)
    ]
    return {
        "contract_version": "pmbot_public_fetch_url_safety_batch.v1",
        "max_request_count": max_request_count,
        "request_count": len(intents),
        "allowed_count": sum(1 for row in rows if row["allowed"]),
        "blocked_count": sum(1 for row in rows if not row["allowed"]),
        "results": rows,
        "blockers": [] if len(intents) <= max_request_count else ["request count exceeds approved max request count"],
    }


def sanitize_url_reference(value: str) -> str:
    parsed = urlparse(clean_text(value))
    if parsed.scheme.lower() not in {"http", "https"}:
        return clean_text(value)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    query_pairs = []
    for key, item_value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            query_pairs.append((key, "REDACTED"))
        else:
            query_pairs.append((key, item_value))
    sanitized = ParseResult(
        scheme=parsed.scheme.lower(),
        netloc=netloc,
        path=parsed.path or "/",
        params="",
        query=urlencode(query_pairs, doseq=True),
        fragment="",
    )
    return urlunparse(sanitized)


def render_url_safety_markdown(result: Mapping[str, Any]) -> str:
    rows = result.get("results") if isinstance(result.get("results"), list) else [result]
    lines = [
        "# PMBOT Public Fetch URL Safety",
        "",
        f"- Contract: `{result.get('contract_version')}`",
        f"- Result count: {len(rows)}",
        "",
        "## Results",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` allowed: `{str(row.get('allowed')).lower()}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Source category: `{row.get('source_category')}`",
                f"  URL reference: `{row.get('sanitized_url_reference')}`",
                f"  Blockers: {', '.join(row.get('blockers', [])) or 'none'}",
                f"  Warnings: {', '.join(row.get('warnings', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- URL validation is local and happens before any request.",
            "- Placeholder, authenticated, cookie, wallet, order, and trading request shapes remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_reference(intent: Mapping[str, Any]) -> str:
    for key in (
        "source_reference",
        "source_reference_or_placeholder",
        "source_url",
        "url",
        "source_url_or_reference",
    ):
        raw_value = intent.get(key)
        if raw_value is None:
            continue
        value = clean_text(raw_value)
        if value:
            return value
    return clean_text(intent.get("source_name_or_placeholder"))


def _is_placeholder_reference(value: str) -> bool:
    normalized = clean_text(value).lower()
    return not normalized or normalized.startswith("public_source_placeholder:") or "placeholder" in normalized


def _blocked_header_reasons(intent: Mapping[str, Any]) -> list[str]:
    headers = intent.get("headers") or intent.get("required_headers") or {}
    if not isinstance(headers, Mapping):
        return []
    reasons = []
    for key in headers:
        normalized = clean_text(key).lower()
        if normalized in {"authorization", "cookie", "x-api-key", "x-auth-token"}:
            reasons.append(f"blocked auth/cookie/API-key header requested: {key}")
    return reasons


def _blocked_query_reasons(parsed: ParseResult) -> list[str]:
    reasons = []
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            reasons.append(f"URL query contains sensitive credential-like key: {key}")
    return reasons


def _blocked_path_hint_reasons(parsed: ParseResult) -> list[str]:
    normalized_path = parsed.path.lower().replace("_", "-")
    parts = {part for part in normalized_path.split("/") if part}
    reasons = []
    for hint in sorted(BLOCKED_PATH_HINTS):
        if hint in parts:
            reasons.append(f"URL path contains blocked auth/trading/wallet hint: {hint}")
    return reasons


def _validate_host(host: str, *, fixture_mode: bool) -> tuple[list[str], list[str]]:
    normalized = host.lower().strip(".")
    blockers: list[str] = []
    warnings: list[str] = []
    if normalized in LOCAL_HOSTNAMES:
        if fixture_mode:
            warnings.append("localhost URL allowed only in fixture mode")
        else:
            blockers.append("localhost URLs are blocked outside fixture mode")
        return blockers, warnings
    if normalized.endswith(INTERNAL_HOST_SUFFIXES):
        blockers.append("private/internal hostname suffix is blocked")
    try:
        ip = ipaddress.ip_address(normalized)
    except ValueError:
        return blockers, warnings
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        if fixture_mode and ip.is_loopback:
            warnings.append("loopback IP URL allowed only in fixture mode")
        else:
            blockers.append("localhost/private/internal IP address is blocked")
    return blockers, warnings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate public fetch URL safety for one manifest intent.")
    parser.add_argument("--intent", required=True, help="Input request intent JSON object.")
    parser.add_argument("--out-json", required=True, help="Output validation JSON.")
    parser.add_argument("--out-md", required=True, help="Output validation Markdown.")
    parser.add_argument("--max-request-count", type=int, default=5)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args(argv)
    intent = load_json_object(args.intent, label="request intent")
    result = validate_public_fetch_request_intent(
        intent,
        max_request_count=args.max_request_count,
        fixture_mode=args.fixture_mode,
    )
    write_json(args.out_json, result)
    write_text(args.out_md, render_url_safety_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

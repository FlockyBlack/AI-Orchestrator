from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, safe_summary, write_json, write_text

SOURCE_REGISTRY_CONTRACT_VERSION = "pmbot_public_source_registry.v1"

ALLOWED_SOURCE_CATEGORIES: dict[str, dict[str, str]] = {
    "public_market_metadata_endpoint_placeholder": {
        "reason": "Future public metadata lookup for market title, rules, status, and resolution terms.",
        "safety_boundary": "Public read-only placeholder only; no authenticated or trading endpoint.",
    },
    "public_resolution_source_page_placeholder": {
        "reason": "Future public page used to capture outcome or resolution evidence.",
        "safety_boundary": "Static public page capture only; no login, bypass, or private feed.",
    },
    "public_issuer_company_news_page_placeholder": {
        "reason": "Future public issuer or company news page for source evidence.",
        "safety_boundary": "Public web page only; no investor portal login or private API key.",
    },
    "public_court_government_page_placeholder": {
        "reason": "Future public court, government, parliament, or regulator page for official evidence.",
        "safety_boundary": "Public official page only; no account, KYC, or session cookies.",
    },
    "public_exchange_company_announcement_page_placeholder": {
        "reason": "Future public exchange, listing, IPO, or company announcement page for evidence.",
        "safety_boundary": "Public read-only announcement source only; no broker, order, or trading API.",
    },
    "public_static_web_page_placeholder": {
        "reason": "Future public static web page used as a low-risk source reference.",
        "safety_boundary": "Public static page only; no browser profile, cookies, or automation bypass.",
    },
    "public_btc_price_reference": {
        "reason": "Future public read-only Bitcoin price or chart reference for evidence capture.",
        "safety_boundary": "Public page reference only; no authenticated feed, API key, wallet, order, or trading endpoint.",
    },
    "public_resolution_reference": {
        "reason": "Future public read-only market or resolution context reference for evidence capture.",
        "safety_boundary": "Public page reference only; no authenticated endpoint, private API, wallet, order, or trading endpoint.",
    },
    "low_quality_forum_or_rumor_labeled_source": {
        "reason": "May be retained only when explicitly labeled low quality and not used as decisive evidence.",
        "safety_boundary": "Low-quality context label only; never an executable market instruction.",
    },
}

BLOCKED_SOURCE_CATEGORIES: dict[str, dict[str, str]] = {
    "authenticated_endpoint": {
        "reason": "Requires identity, session, token, or account access.",
        "safety_boundary": "Blocked for this public read-only preparation layer.",
    },
    "trading_endpoint": {
        "reason": "Could expose execution or market-taking behavior.",
        "safety_boundary": "Trading endpoints remain out of scope.",
    },
    "order_endpoint": {
        "reason": "Could create, cancel, or inspect executable order paths.",
        "safety_boundary": "Order endpoints remain out of scope.",
    },
    "wallet_signing_endpoint": {
        "reason": "Touches wallet, signing, private key, or custody boundaries.",
        "safety_boundary": "Wallet and signing paths remain out of scope.",
    },
    "private_api_key_endpoint": {
        "reason": "Requires private credentials or API keys.",
        "safety_boundary": "Credentials are not required or used.",
    },
    "browser_session_cookie_based_source": {
        "reason": "Depends on browser profile state, session cookies, or logged-in context.",
        "safety_boundary": "Browser sessions and cookies are not used.",
    },
    "forum_rumor_only_unlabeled_source": {
        "reason": "Rumor-only material is too weak unless explicitly labeled low quality.",
        "safety_boundary": "Unlabeled rumor sources are blocked.",
    },
    "source_requiring_kyc_or_login": {
        "reason": "Requires KYC, login, or account identity.",
        "safety_boundary": "Login and KYC sources are blocked.",
    },
    "source_requiring_bypass_or_automation": {
        "reason": "Requires bypassing controls, bot detection, or automated interactive access.",
        "safety_boundary": "Bypass and unattended automation are blocked.",
    },
}


class PublicSourceRegistryError(ValueError):
    pass


def build_public_source_registry() -> dict[str, Any]:
    allowed = [
        {"source_category": category, "allowed": True, **metadata}
        for category, metadata in sorted(ALLOWED_SOURCE_CATEGORIES.items())
    ]
    blocked = [
        {"source_category": category, "blocked": True, **metadata}
        for category, metadata in sorted(BLOCKED_SOURCE_CATEGORIES.items())
    ]
    return {
        "contract_version": SOURCE_REGISTRY_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "allowed_sources": allowed,
        "blocked_sources": blocked,
        "source_category_rules": [
            "Allowed categories are placeholders for future public read-only sources.",
            "Blocked categories must not be used in fetch plans.",
            "No source category may require auth, credentials, wallet access, signing, orders, trading, KYC, cookies, or bypass automation.",
            "Forum or rumor-only material is blocked unless explicitly labeled low quality.",
        ],
        "reason": "Make future public read-only fetch planning explicit and reviewable before any live request is allowed.",
        "safety_boundary": "Registry validation only; no network calls, browser sessions, credentials, wallet access, orders, or trading actions.",
        "safety_summary": safe_summary(),
    }


def allowed_source_categories() -> list[str]:
    return sorted(ALLOWED_SOURCE_CATEGORIES)


def blocked_source_categories() -> list[str]:
    return sorted(BLOCKED_SOURCE_CATEGORIES)


def validate_source_category(category: str) -> dict[str, Any]:
    normalized = clean_text(category)
    if normalized in ALLOWED_SOURCE_CATEGORIES:
        metadata = ALLOWED_SOURCE_CATEGORIES[normalized]
        return {
            "source_category": normalized,
            "allowed": True,
            "blocked": False,
            "reason": metadata["reason"],
            "safety_boundary": metadata["safety_boundary"],
        }
    if normalized in BLOCKED_SOURCE_CATEGORIES:
        metadata = BLOCKED_SOURCE_CATEGORIES[normalized]
        return {
            "source_category": normalized,
            "allowed": False,
            "blocked": True,
            "reason": metadata["reason"],
            "safety_boundary": metadata["safety_boundary"],
        }
    return {
        "source_category": normalized,
        "allowed": False,
        "blocked": True,
        "reason": "Unknown source categories are blocked until added to the registry.",
        "safety_boundary": "Unknown source categories require operator review before use.",
    }


def assert_source_category_allowed(category: str) -> None:
    validation = validate_source_category(category)
    if not validation["allowed"]:
        raise PublicSourceRegistryError(f"source category is not allowed: {category}")


def validate_requested_source(source: Mapping[str, Any]) -> dict[str, Any]:
    category = clean_text(source.get("source_category"))
    validation = validate_source_category(category)
    source_id = clean_text(source.get("source_id") or source.get("planned_source_id") or category)
    return {
        "source_id": source_id,
        "source_category": category,
        "allowed": validation["allowed"],
        "blocked": validation["blocked"],
        "reason": validation["reason"],
        "safety_boundary": validation["safety_boundary"],
    }


def render_public_source_registry_markdown(registry: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Source Registry",
        "",
        f"- Contract: `{registry['contract_version']}`",
        f"- Generated at: `{registry['generated_at']}`",
        "",
        "## Allowed Source Categories",
        "",
    ]
    for row in registry["allowed_sources"]:
        lines.extend(
            [
                f"- `{row['source_category']}`",
                f"  Reason: {row['reason']}",
                f"  Boundary: {row['safety_boundary']}",
            ]
        )
    lines.extend(["", "## Blocked Source Categories", ""])
    for row in registry["blocked_sources"]:
        lines.extend(
            [
                f"- `{row['source_category']}`",
                f"  Reason: {row['reason']}",
                f"  Boundary: {row['safety_boundary']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Rules",
            "",
            *bullet_lines(registry["source_category_rules"]),
            "",
            "## Safety Boundary",
            "",
            f"- {registry['safety_boundary']}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_source_registry(
    *,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    registry = build_public_source_registry()
    if out_json_path is not None:
        write_json(out_json_path, registry)
    if out_md_path is not None:
        write_text(out_md_path, render_public_source_registry_markdown(registry))
    return registry


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the local PMBOT public source registry snapshot.")
    parser.add_argument("--out-json", required=True, help="Output registry JSON.")
    parser.add_argument("--out-md", required=True, help="Output registry Markdown.")
    args = parser.parse_args(argv)
    write_public_source_registry(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

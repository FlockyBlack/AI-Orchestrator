from __future__ import annotations

from pm_bot.practical.public_fetch_execution_preflight import build_enriched_manifest_execution_preflight
from pm_bot.practical.public_fetch_url_manifest_enrichment import build_scoped_approval_for_enriched_manifest


def _executable(index: int, *, url: str = "https://example.org/public-evidence") -> dict:
    return {
        "request_intent_id": f"intent-{index}",
        "market_id": "563650",
        "market_title": "Test market",
        "source_category": "public_static_web_page_placeholder",
        "source_name": "Example public source",
        "source_reference": f"{url}/{index}",
        "source_url": f"{url}/{index}",
        "method": "GET",
        "requires_auth": False,
        "trading_or_order_endpoint": False,
        "wallet_or_signing_required": False,
        "live_fetch_performed": False,
    }


def _manifest(executable: list[dict], *, missing: int = 0, blocked: int = 0, max_request_count: int = 5) -> dict:
    return {
        "contract_version": "pmbot_enriched_public_fetch_request_manifest.v1",
        "executable_request_intents": executable,
        "missing_url_request_intents": [{"request_intent_id": f"missing-{index}"} for index in range(missing)],
        "blocked_request_intents": [{"request_intent_id": f"blocked-{index}"} for index in range(blocked)],
        "executable_request_count": len(executable),
        "missing_url_count": missing,
        "blocked_request_count": blocked,
        "max_request_count": max_request_count,
        "within_request_limit": len(executable) <= max_request_count,
        "live_fetch_performed": False,
    }


def test_pending_approval_keeps_ready_to_execute_false() -> None:
    manifest = _manifest([_executable(1)])
    approval = build_scoped_approval_for_enriched_manifest(manifest)

    result = build_enriched_manifest_execution_preflight(enriched_manifest=manifest, pending_approval=approval)

    assert result["ready_to_execute_public_read_only_fetch"] is False
    assert result["approval_granted"] is False
    assert "operator approval has not been granted" in result["blockers"]


def test_would_be_ready_after_operator_approval_when_concrete_urls_pass() -> None:
    manifest = _manifest([_executable(1), _executable(2)])
    approval = build_scoped_approval_for_enriched_manifest(manifest)

    result = build_enriched_manifest_execution_preflight(enriched_manifest=manifest, pending_approval=approval)

    assert result["would_be_ready_after_operator_approval"] is True
    assert result["request_count_within_limit"] is True


def test_would_not_be_ready_after_operator_approval_without_concrete_urls() -> None:
    manifest = _manifest([])
    approval = build_scoped_approval_for_enriched_manifest(manifest)

    result = build_enriched_manifest_execution_preflight(enriched_manifest=manifest, pending_approval=approval)

    assert result["would_be_ready_after_operator_approval"] is False
    assert "no concrete safe public URLs" in result["blockers"]


def test_max_request_count_is_enforced() -> None:
    manifest = _manifest([_executable(index) for index in range(1, 7)], max_request_count=5)
    approval = build_scoped_approval_for_enriched_manifest(manifest)

    result = build_enriched_manifest_execution_preflight(enriched_manifest=manifest, pending_approval=approval)

    assert result["request_count_within_limit"] is False
    assert result["would_be_ready_after_operator_approval"] is False
    assert "executable request count exceeds max request count" in result["blockers"]


def test_missing_and_blocked_urls_are_reported_without_network() -> None:
    manifest = _manifest([_executable(1)], missing=2, blocked=1)
    approval = build_scoped_approval_for_enriched_manifest(manifest)

    result = build_enriched_manifest_execution_preflight(enriched_manifest=manifest, pending_approval=approval)

    assert result["missing_url_count"] == 2
    assert result["blocked_request_count"] == 1
    assert result["live_fetch_performed"] is False
    assert any("missing URL" in warning for warning in result["warnings"])
    assert any("blocked request" in warning for warning in result["warnings"])

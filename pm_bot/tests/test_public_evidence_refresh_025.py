from __future__ import annotations

import json
import socket
from pathlib import Path

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.source_quality.public_evidence_refresh import (
    PENDING_APPROVAL_PACKET_CONTRACT,
    REFRESH_LEDGER_CONTRACT,
    REFRESH_REQUEST_CONTRACT,
    build_public_evidence_refresh_artifacts,
    validate_public_evidence_refresh_ledger,
)


SAVED_PUBLIC_EVIDENCE_563650 = (
    "pm_bot/practical/artifacts/public_read_only_fetch_execution_008/evidence_packets/"
    "public_fetch_008_563650_public_fetch_request_intent_006_02_563650_563650_domain_public_evidence_"
    "a6d1969391feeee9.json"
)
STALE_FIXTURE = "pm_bot/tests/fixtures/public_read_only_fetch_prep/saved_public_evidence_packet.stale.json"
CONTRADICTION_FIXTURE = (
    "pm_bot/tests/fixtures/public_read_only_fetch_prep/saved_public_evidence_packet.contradictory.json"
)


def _request(sources: list[dict[str, object]]) -> dict[str, object]:
    return {
        "contract_version": REFRESH_REQUEST_CONTRACT,
        "default_no_network_mode": True,
        "generated_at": "2026-05-11T00:00:00Z",
        "network_mode": "no_network",
        "operator_approval_reference": "",
        "operator_approval_required": True,
        "reference_timestamp_utc": "2026-05-11T00:00:00Z",
        "refresh_id": "public-evidence-refresh-025-test",
        "run_date": "2026-05-11",
        "run_id": "paper-daily-loop-022-2026-05-11",
        "markets": [
            {
                "market_id": "563650",
                "market_title": "SCOTUS accepts sports event contract case by July 31, 2026?",
                "outcome_status": "unresolved",
            },
            {
                "market_id": "597964",
                "market_title": "Macron out by June 30, 2026?",
                "outcome_status": "unresolved",
            },
        ],
        "sources": sources,
    }


def _source(
    *,
    source_id: str,
    market_id: str = "563650",
    source_url: str = "",
    local_captured_reference: str = "",
    contradiction_notes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "market_id": market_id,
        "market_title": "SCOTUS accepts sports event contract case by July 31, 2026?",
        "hypothesis_id": f"{market_id}.analysis.fixture.paper_hypothesis",
        "intent_id": f"paper-intent-020-021-{market_id}",
        "source_category": "saved_public_evidence_packet",
        "source_label": "Fixture source",
        "evidence_role": "paper_strategy_evidence_link",
        "local_captured_reference": local_captured_reference,
        "source_url": source_url,
        "freshness_max_age_seconds": 172800,
        "contradiction_notes": contradiction_notes or [],
        "evidence_quality_notes": ["Fixture source record for deterministic refresh tests."],
    }


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_evidence_refresh_defaults_to_no_network(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    request = _request([_source(source_id="563650.public_url", source_url="https://example.org/public-evidence")])
    artifacts = build_public_evidence_refresh_artifacts(request)
    ledger = artifacts["ledger"]

    assert ledger["contract_version"] == REFRESH_LEDGER_CONTRACT
    assert ledger["default_no_network_mode"] is True
    assert ledger["network_used"] is False
    assert ledger["external_api_calls_performed"] is False
    assert ledger["run_mode"] == "local_dry_run_no_network"
    assert ledger["pending_approval_packet_ready"] is True


def test_public_evidence_refresh_creates_pending_approval_packet_for_source_url() -> None:
    request = _request([_source(source_id="563650.public_url", source_url="https://example.org/public-evidence")])
    packet = build_public_evidence_refresh_artifacts(request)["pending_approval_packet"]

    assert packet is not None
    assert packet["contract_version"] == PENDING_APPROVAL_PACKET_CONTRACT
    assert packet["operator_approval_granted"] is False
    assert packet["network_used"] is False
    assert packet["requested_source_url_count"] == 1
    assert "authenticated endpoints" in packet["blocked_scope"]
    assert "wallet, private key, signing, order, custody, or settlement paths" in packet["blocked_scope"]


def test_public_evidence_refresh_validates_saved_local_evidence_record() -> None:
    request = _request(
        [
            _source(
                source_id="563650.local_saved_public_evidence.1",
                local_captured_reference=SAVED_PUBLIC_EVIDENCE_563650,
            )
        ]
    )
    ledger = build_public_evidence_refresh_artifacts(request)["ledger"]
    record = ledger["records"][0]

    assert validate_public_evidence_refresh_ledger(ledger) == []
    assert record["market_id"] == "563650"
    assert record["source_category"] == "saved_public_evidence_packet"
    assert record["source_url"] == "https://www.supremecourt.gov/docket/docket.aspx"
    assert record["captured_at"] == "2026-05-10T13:16:55Z"
    assert record["freshness_status"] == "fresh_enough"
    assert record["contradiction_status"] == "no_contradiction_noted"
    assert record["network_used"] is False


def test_public_evidence_refresh_detects_stale_missing_and_contradiction_notes() -> None:
    request = _request(
        [
            _source(source_id="563650.stale", local_captured_reference=STALE_FIXTURE),
            _source(source_id="563650.contradiction", local_captured_reference=CONTRADICTION_FIXTURE),
            _source(source_id="597964.missing", market_id="597964"),
        ]
    )
    ledger = build_public_evidence_refresh_artifacts(request)["ledger"]
    quality = ledger["quality_ledger"]

    assert ledger["summary_counts"]["stale_records"] == 1
    assert ledger["summary_counts"]["missing_source_reference_records"] == 1
    assert ledger["summary_counts"]["contradiction_note_records"] == 1
    assert quality["freshness_status_counts"]["stale"] == 1
    gap_types = {row["gap_type"] for row in quality["missing_evidence_gaps"]}
    assert {"stale_source_evidence", "missing_source_reference"}.issubset(gap_types)
    contradiction_record = next(
        row for row in ledger["records"] if row["contradiction_status"] == "contradiction_note_present"
    )
    assert contradiction_record["contradiction_notes"]


def test_public_evidence_refresh_rejects_authenticated_or_trading_api_endpoint() -> None:
    request = _request([_source(source_id="563650.api", source_url="https://api.polymarket.com/markets")])

    try:
        build_public_evidence_refresh_artifacts(request)
    except ValueError as exc:
        assert "blocked or non-public endpoint" in str(exc)
    else:
        raise AssertionError("blocked endpoint should be rejected")


def test_daily_dashboard_shows_source_evidence_status(tmp_path) -> None:
    result = run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    dashboard = _load_json(tmp_path / "paper_daily_dashboard.json")
    refresh_ledger = _load_json(tmp_path / "public_evidence_refresh_ledger.json")
    quality_ledger = _load_json(tmp_path / "public_evidence_quality_ledger.json")
    strategy_ledger = _load_json(tmp_path / "paper_strategy_evaluation_ledger.json")

    assert result.source_evidence_refresh_path
    assert (tmp_path / "public_evidence_refresh_request.json").exists()
    assert (tmp_path / "public_evidence_refresh_report.md").exists()
    assert dashboard["source_evidence_refresh_status"]["network_used"] is False
    assert dashboard["source_evidence_refresh_status"]["external_api_calls_performed"] is False
    assert dashboard["counts"]["source_evidence_refresh_record_count"] == 6
    assert dashboard["counts"]["source_evidence_gap_count"] == 4
    assert refresh_ledger["summary_counts"]["local_captured_references"] == 2
    assert refresh_ledger["summary_counts"]["missing_source_reference_records"] == 4
    assert quality_ledger["summary_counts"]["markets_with_gaps"] == 4
    market_status = {row["market_id"]: row["source_gap_status"] for row in dashboard["tracked_markets"]}
    assert market_status["563650"] == "covered_with_local_evidence"
    assert market_status["597964"] == "gaps_present"
    assert "source_evidence_refresh_status" in strategy_ledger
    assert any(
        "saved_public_evidence_packet_missing" in record["missing_future_evaluation_data"]
        for record in strategy_ledger["records"]
    )


def test_public_evidence_refresh_introduces_no_runtime_network_wallet_order_or_signing_code() -> None:
    module_text = Path("pm_bot/source_quality/public_evidence_refresh.py").read_text(encoding="utf-8")
    blocked_runtime_snippets = [
        "import requests",
        "urllib.request",
        "http.client",
        "socket.",
        "Authorization",
        "Bearer ",
        "place_order",
        "submit_order",
        "sign_transaction",
        "private_key =",
    ]

    assert all(snippet not in module_text for snippet in blocked_runtime_snippets)


def test_daily_source_refresh_does_not_invent_outcome_resolution_or_pnl(tmp_path) -> None:
    run_paper_daily_loop(PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path))
    refresh_ledger = _load_json(tmp_path / "public_evidence_refresh_ledger.json")
    strategy_summary = _load_json(tmp_path / "paper_strategy_evaluation_summary.json")
    safety = _load_json(tmp_path / "paper_daily_safety_scan.json")

    assert refresh_ledger["outcome_resolution_invented"] is False
    assert refresh_ledger["pnl_invented"] is False
    assert strategy_summary["paper_realized_pnl_usd"] is None
    assert strategy_summary["paper_unrealized_pnl_usd"] is None
    assert strategy_summary["unresolved_pnl_not_invented"] is True
    assert safety["safety_ok"] is True
    assert safety["safety_flags"]["wallet_used"] is False
    assert safety["safety_flags"]["signing_used"] is False
    assert safety["safety_flags"]["trading_endpoint_used"] is False

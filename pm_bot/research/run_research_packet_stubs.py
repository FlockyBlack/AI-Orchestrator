import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-006-RESEARCH-PACKET-STUBS"
SCHEMA_VERSION = "research_packet_stubs.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = ROOT / "pm_bot" / "research" / "expected_market_research_candidate_queue.v1.json"
DEFAULT_LIMIT = 10
SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "api_used": False,
    "network_used": False,
    "credentials_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
    "runtime_wiring_changed": False,
    "dispatcher_touched": False,
    "prompt_automation_added": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build deterministic offline research packet stubs from a local queue artifact.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE.relative_to(ROOT)))
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    return parser.parse_args(argv[1:])


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _round_number(value):
    if value is None:
        return None
    return round(float(value), 4)


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _selected_shortlist_candidates(queue_payload, limit):
    candidates = queue_payload.get("operator_shortlist_candidates")
    if not isinstance(candidates, list):
        candidates = [
            row
            for row in queue_payload.get("top_n_candidates", [])
            if row.get("operator_shortlist") or row.get("research_tier") == "lower_risk_operator_shortlist"
        ]
    selected = [
        row
        for row in candidates
        if row.get("operator_shortlist") is True and row.get("research_tier") == "lower_risk_operator_shortlist"
    ]
    selected.sort(key=lambda row: (row.get("shortlist_rank") is None, row.get("shortlist_rank") or 0, _text(row.get("market_id")), _text(row.get("title"))))
    return selected[: max(0, int(limit))]


def _source_plan(packet_type, title):
    if packet_type == "political_event":
        return (
            "Template only: confirm the market's own resolution rules, then check official election authority records, "
            f"candidate or party statements, and credible news coverage for '{title}'. Do not fetch sources in this stub."
        )
    if packet_type == "legal_event":
        return (
            "Template only: confirm the market's own resolution rules, then check official court dockets, order lists, "
            f"case filings, and credible legal/news coverage for '{title}'. Do not fetch sources in this stub."
        )
    if packet_type == "crypto_threshold_hit":
        return (
            "Template only: confirm the market's own resolution rules, then check the specified benchmark, exchange or "
            f"index source, timestamp rules, and credible market coverage for '{title}'. Do not fetch sources in this stub."
        )
    if packet_type == "diplomatic_event":
        return (
            "Template only: confirm the market's own resolution rules, then check official government or multilateral "
            f"statements and credible international news coverage for '{title}'. Do not fetch sources in this stub."
        )
    return f"Template only: confirm the market's own resolution rules and credible source path for '{title}'. Do not fetch sources in this stub."


def _resolution_summary(packet_type, title, deadline):
    if packet_type == "political_event":
        return (
            f"Stub summary only: determine whether the named political/election outcome in '{title}' occurs by {deadline}; "
            "the full market rules must be copied from the local market artifact before completion."
        )
    if packet_type == "legal_event":
        return (
            f"Stub summary only: determine whether the legal/court event in '{title}' occurs by {deadline}; "
            "the full market rules and official docket criteria must be copied before completion."
        )
    if packet_type == "crypto_threshold_hit":
        return (
            f"Stub summary only: determine whether the crypto threshold in '{title}' is hit by {deadline}; "
            "the benchmark, timezone, and threshold rules must be copied before completion."
        )
    if packet_type == "diplomatic_event":
        return (
            f"Stub summary only: determine whether the diplomatic event in '{title}' occurs by {deadline}; "
            "the full market rules and official-recognition criteria must be copied before completion."
        )
    return f"Stub summary only: determine whether '{title}' resolves Yes by {deadline}; full criteria are still required."


def _search_queries(row, packet_type):
    title = _text(row.get("title"))
    category = _text(row.get("category"))
    market_id = _text(row.get("market_id"))
    deadline = _text(row.get("deadline"))
    base = [
        f'"{title}" "resolution criteria"',
        f'"{title}" "{deadline}"',
        f'"{category}" "{title}"',
        f'"Polymarket" "{market_id}" "{title}"',
    ]
    if packet_type == "political_event":
        base.extend(
            [
                f'"{title}" official election results',
                f'"{category}" election authority official results',
            ]
        )
    elif packet_type == "legal_event":
        base.extend(
            [
                f'"{title}" Supreme Court docket',
                f'"{title}" order list filing',
            ]
        )
    elif packet_type == "crypto_threshold_hit":
        base.extend(
            [
                f'"{title}" price benchmark',
                f'"{title}" exchange price index',
            ]
        )
    elif packet_type == "diplomatic_event":
        base.extend(
            [
                f'"{title}" official statement',
                f'"{title}" Reuters AP official',
            ]
        )
    return base


def _official_sources_to_check(row, packet_type):
    title = _text(row.get("title"))
    category = _text(row.get("category"))
    market_id = _text(row.get("market_id"))
    if packet_type == "political_event":
        return [
            f"Polymarket market rules and resolution criteria for market_id {market_id}",
            f"Official election authority results or notices for category '{category}'",
            f"Official candidate, party, or government pages named by '{title}'",
        ]
    if packet_type == "legal_event":
        return [
            f"Polymarket market rules and resolution criteria for market_id {market_id}",
            "Supreme Court docket and order lists relevant to the named case or event",
            f"Official court filings or orders matching '{title}'",
        ]
    if packet_type == "crypto_threshold_hit":
        return [
            f"Polymarket market rules and resolution criteria for market_id {market_id}",
            "Official benchmark, exchange, or index source specified by the market rules",
            f"Timestamp and threshold definitions for '{title}'",
        ]
    if packet_type == "diplomatic_event":
        return [
            f"Polymarket market rules and resolution criteria for market_id {market_id}",
            "Official government, treaty, or multilateral organization statements named by the market",
            f"Official statements matching '{title}'",
        ]
    return [
        f"Polymarket market rules and resolution criteria for market_id {market_id}",
        f"Official primary source named by '{title}'",
    ]


def _credible_news_sources_to_check(row, packet_type):
    title = _text(row.get("title"))
    category = _text(row.get("category"))
    if packet_type == "legal_event":
        return [
            f"Reuters or Associated Press coverage query for '{title}'",
            f"SCOTUSblog or comparable legal reporting query for '{title}'",
            f"Major newspaper legal desk query for '{category}'",
        ]
    if packet_type == "crypto_threshold_hit":
        return [
            f"Reuters markets coverage query for '{title}'",
            f"CoinDesk or The Block market coverage query for '{title}'",
            f"Bloomberg or Wall Street Journal markets query for '{category}'",
        ]
    if packet_type == "diplomatic_event":
        return [
            f"Reuters international coverage query for '{title}'",
            f"Associated Press international coverage query for '{title}'",
            f"BBC or Financial Times query for '{category}'",
        ]
    return [
        f"Reuters coverage query for '{title}'",
        f"Associated Press coverage query for '{title}'",
        f"Major local or national outlet query for '{category}'",
    ]


def _evidence_slots():
    return {
        "official_resolution_criteria": [],
        "official_yes_evidence": [],
        "official_no_evidence": [],
        "credible_news_yes_evidence": [],
        "credible_news_no_evidence": [],
        "uncertainty_factors": [],
        "source_reliability_notes": [],
    }


def _missing_information(packet_type):
    missing = [
        "full_market_resolution_criteria_text",
        "official_source_urls",
        "credible_news_source_urls",
        "yes_evidence",
        "no_or_counterevidence",
        "source_timestamps",
        "source_reliability_review",
        "operator_edge_assessment",
        "operator_risk_review",
    ]
    if packet_type == "crypto_threshold_hit":
        missing.append("benchmark_and_timezone_rules")
    if packet_type == "legal_event":
        missing.append("official_docket_or_order_identifier")
    if packet_type == "political_event":
        missing.append("official_election_authority_identifier")
    if packet_type == "diplomatic_event":
        missing.append("official_statement_or_treaty_identifier")
    return missing


def _packet_stub(row):
    packet_type = row.get("suggested_research_packet_type") or row.get("packet_type") or "unsupported"
    title = _text(row.get("title") or row.get("question"))
    deadline = _text(row.get("deadline")) or "the market deadline"
    return {
        "shortlist_rank": row.get("shortlist_rank"),
        "market_id": _text(row.get("market_id")),
        "title": title,
        "question": _text(row.get("question")) or title,
        "category": row.get("category"),
        "packet_type": packet_type,
        "current_yes_price": _round_number(row.get("yes_price")),
        "liquidity": _round_number(row.get("liquidity")),
        "deadline": row.get("deadline"),
        "resolution_criteria_summary": _resolution_summary(packet_type, title, deadline),
        "why_selected_for_research": row.get("why_selected_for_research"),
        "why_not_bet_yet": row.get("why_not_bet_yet"),
        "source_plan": _source_plan(packet_type, title),
        "search_queries": _search_queries(row, packet_type),
        "official_sources_to_check": _official_sources_to_check(row, packet_type),
        "credible_news_sources_to_check": _credible_news_sources_to_check(row, packet_type),
        "evidence_slots": _evidence_slots(),
        "missing_information": _missing_information(packet_type),
        "completion_status": "stub_only",
    }


def build_research_packet_stubs(queue_path=None, limit=DEFAULT_LIMIT):
    queue_file = _resolve_path(queue_path) if queue_path else DEFAULT_QUEUE
    queue_payload = _load_json(queue_file)
    selected = _selected_shortlist_candidates(queue_payload, limit)
    packet_stubs = [_packet_stub(row) for row in selected]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "queue_artifact_path": str(queue_file),
        "queue_schema_version": queue_payload.get("schema_version"),
        "selection_source": "operator_shortlist_candidates",
        "selected_count": len(packet_stubs),
        "selected_market_ids": [stub["market_id"] for stub in packet_stubs],
        "packet_stubs": packet_stubs,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads only the saved local PMBOT research candidate queue artifact.",
            "Emits stub-only query plans; it does not fetch, verify, or conclude anything online.",
            "Evidence slots are intentionally empty placeholders.",
            "Does not create completed dossiers, paper orders, real orders, trades, wallet actions, prompt automation, runtime wiring, or dispatcher changes.",
        ],
    }


def main(argv):
    args = _parse_args(argv)
    report = build_research_packet_stubs(args.queue, args.limit)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

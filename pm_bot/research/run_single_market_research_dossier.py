import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-001-SINGLE-MARKET-RESEARCH-DOSSIER"
SCHEMA_VERSION = "single_market_research_dossier.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET = ROOT / "pm_bot" / "research" / "single_market_research_packet.v1.json"
MIN_EDGE_FOR_PAPER_CANDIDATE = 0.05
SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "api_used": False,
    "network_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
    "runtime_wiring_changed": False,
    "dispatcher_touched": False,
    "prompt_automation_added": False,
}

SOURCE_TYPE_WEIGHTS = {
    "official_statement": 3.0,
    "court_record": 3.0,
    "news": 2.0,
    "analysis": 1.5,
    "social": 0.75,
    "other": 1.0,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build a deterministic offline single-market research dossier.")
    parser.add_argument("--packet", default=str(DEFAULT_PACKET.relative_to(ROOT)))
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_probability(value):
    if value is None:
        return None
    return round(max(0.0, min(1.0, float(value))), 4)


def _contains_any(text, needles):
    lowered = str(text or "").lower()
    return any(needle in lowered for needle in needles)


def _evidence_direction(source):
    note = source.get("excerpt_or_note", "")
    if _contains_any(note, ("[yes]", "supports yes", "supports_yes", "yes evidence")):
        return "yes"
    if _contains_any(note, ("[no]", "supports no", "supports_no", "no evidence")):
        return "no"
    return "uncertainty"


def _reliability_multiplier(source):
    hint = str(source.get("reliability_hint") or "").lower()
    if _contains_any(hint, ("low", "weak", "rumor", "unverified")):
        return 0.4
    if _contains_any(hint, ("medium", "corroborated", "reputable")):
        return 0.75
    if _contains_any(hint, ("high", "primary", "official", "court")):
        return 1.0
    return 0.6


def _source_weight(source):
    source_type = source.get("source_type")
    base = SOURCE_TYPE_WEIGHTS.get(source_type, SOURCE_TYPE_WEIGHTS["other"])
    return round(base * _reliability_multiplier(source), 4)


def _reliability_level(weight):
    if weight >= 2.0:
        return "strong"
    if weight >= 1.0:
        return "medium"
    return "weak"


def _source_note(source, direction, weight):
    return {
        "source_id": source.get("source_id"),
        "source_type": source.get("source_type"),
        "title": source.get("title"),
        "url": source.get("url"),
        "published_at": source.get("published_at"),
        "evidence_direction": direction,
        "reliability_hint": source.get("reliability_hint"),
        "reliability_level": _reliability_level(weight),
        "weight": weight,
    }


def _evidence_item(source, weight):
    return {
        "source_id": source.get("source_id"),
        "source_type": source.get("source_type"),
        "title": source.get("title"),
        "published_at": source.get("published_at"),
        "url": source.get("url"),
        "excerpt_or_note": source.get("excerpt_or_note"),
        "reliability_hint": source.get("reliability_hint"),
        "weight": weight,
    }


def _uncertainty_factor(source, direction, weight):
    note = source.get("excerpt_or_note", "")
    if direction == "uncertainty" or _contains_any(note, ("[uncertainty]", "uncertainty", "unknown", "pending", "could slip")):
        return {
            "source_id": source.get("source_id"),
            "title": source.get("title"),
            "excerpt_or_note": note,
            "reliability_hint": source.get("reliability_hint"),
            "weight": weight,
        }
    return None


def _analyze_sources(sources):
    yes_evidence = []
    no_evidence = []
    uncertainty_factors = []
    reliability_notes = []
    yes_score = 0.0
    no_score = 0.0
    reliable_sources = 0

    for source in sources:
        direction = _evidence_direction(source)
        weight = _source_weight(source)
        level = _reliability_level(weight)
        reliability_notes.append(_source_note(source, direction, weight))
        if level in ("strong", "medium"):
            reliable_sources += 1
        if direction == "yes":
            yes_evidence.append(_evidence_item(source, weight))
            yes_score += weight
        elif direction == "no":
            no_evidence.append(_evidence_item(source, weight))
            no_score += weight
        uncertainty = _uncertainty_factor(source, direction, weight)
        if uncertainty is not None:
            uncertainty_factors.append(uncertainty)

    return {
        "yes_evidence": yes_evidence,
        "no_evidence": no_evidence,
        "uncertainty_factors": uncertainty_factors,
        "source_reliability_notes": reliability_notes,
        "yes_score": round(yes_score, 4),
        "no_score": round(no_score, 4),
        "reliable_sources": reliable_sources,
    }


def _missing_information(packet, source_analysis, yes_price):
    missing = []
    if not str(packet.get("resolution_criteria") or "").strip():
        missing.append("resolution_criteria")
    if yes_price is None:
        missing.append("yes_price")
    sources = packet.get("sources")
    if not isinstance(sources, list) or not sources:
        missing.append("sources")
    if not source_analysis["yes_evidence"]:
        missing.append("yes_evidence")
    if not source_analysis["no_evidence"]:
        missing.append("no_evidence")
    if source_analysis["reliable_sources"] < 2:
        missing.append("strong_or_medium_sources")
    return missing


def _probability_estimate_range(yes_price, source_analysis):
    if yes_price is None:
        return {
            "low": None,
            "midpoint": None,
            "high": None,
            "method": "unavailable_missing_yes_price",
        }
    score_delta = source_analysis["yes_score"] - source_analysis["no_score"]
    midpoint = _round_probability(yes_price + (score_delta * 0.025))
    reliable_sources = source_analysis["reliable_sources"]
    uncertainty_count = len(source_analysis["uncertainty_factors"])
    one_sided_penalty = 0.06 if not source_analysis["yes_evidence"] or not source_analysis["no_evidence"] else 0.0
    weak_source_penalty = 0.04 if reliable_sources < 2 else 0.0
    width = max(
        0.08,
        0.24 - min(0.12, reliable_sources * 0.025) + min(0.08, uncertainty_count * 0.02) + one_sided_penalty + weak_source_penalty,
    )
    low = _round_probability(midpoint - (width / 2.0))
    high = _round_probability(midpoint + (width / 2.0))
    return {
        "low": low,
        "midpoint": midpoint,
        "high": high,
        "method": "deterministic_source_weighted_fixture_heuristic",
    }


def _edge_estimate(yes_price, probability_range):
    if yes_price is None or probability_range["low"] is None:
        return {
            "market_yes_price": yes_price,
            "range_low_edge": None,
            "midpoint_edge": None,
            "range_high_edge": None,
            "range_overlaps_market": None,
        }
    return {
        "market_yes_price": round(yes_price, 4),
        "range_low_edge": round(probability_range["low"] - yes_price, 4),
        "midpoint_edge": round(probability_range["midpoint"] - yes_price, 4),
        "range_high_edge": round(probability_range["high"] - yes_price, 4),
        "range_overlaps_market": probability_range["low"] <= yes_price <= probability_range["high"],
    }


def _decision(packet, source_analysis, missing, probability_range, edge):
    reason_codes = []
    if "resolution_criteria" in missing:
        reason_codes.append("missing_resolution_criteria")
        return "no_action", reason_codes
    if "yes_price" in missing:
        reason_codes.append("missing_yes_price")
        return "no_action", reason_codes
    if "sources" in missing:
        reason_codes.append("no_sources")
        return "no_action", reason_codes
    if source_analysis["reliable_sources"] < 2:
        reason_codes.append("weak_sources")
        return "no_action", reason_codes
    if "yes_evidence" in missing or "no_evidence" in missing:
        reason_codes.append("one_sided_sources")
        return "watchlist", reason_codes
    if edge["range_overlaps_market"]:
        reason_codes.append("probability_range_overlaps_market")
        return "watchlist", reason_codes
    if edge["range_low_edge"] is not None and edge["range_low_edge"] >= MIN_EDGE_FOR_PAPER_CANDIDATE:
        reason_codes.append("positive_edge_range_above_market")
        reason_codes.append("paper_candidate_label_only")
        return "paper_candidate", reason_codes
    if edge["range_high_edge"] is not None and edge["range_high_edge"] < 0:
        reason_codes.append("estimated_range_below_market")
        return "no_action", reason_codes
    reason_codes.append("insufficient_edge")
    return "watchlist", reason_codes


def _human_review_note(decision, reason_codes):
    if "missing_resolution_criteria" in reason_codes:
        return "No action: resolution criteria are missing, so the market cannot be evaluated safely."
    if "weak_sources" in reason_codes:
        return "No action: the packet relies on weak sources and cannot support a paper-candidate label."
    if "one_sided_sources" in reason_codes:
        return "Watchlist only: the packet is one-sided and needs counterevidence before paper review."
    if "probability_range_overlaps_market" in reason_codes:
        return "Watchlist only: the deterministic probability range overlaps the market price."
    if decision == "paper_candidate":
        return "Paper candidate label only: local evidence clears conservative offline checks; no paper order is created."
    if decision == "no_action":
        return "No action: conservative offline checks do not support further review."
    return "Watchlist only: continue manual research before any paper workflow."


def build_single_market_research_dossier(root: Path, packet_path=None):
    packet_file = _resolve_path(packet_path) if packet_path else DEFAULT_PACKET
    packet = _load_json(packet_file)
    sources = packet.get("sources") if isinstance(packet.get("sources"), list) else []
    yes_price = _float_or_none(packet.get("yes_price"))
    no_price = _float_or_none(packet.get("no_price"))
    source_analysis = _analyze_sources(sources)
    missing = _missing_information(packet, source_analysis, yes_price)
    probability_range = _probability_estimate_range(yes_price, source_analysis)
    edge = _edge_estimate(yes_price, probability_range)
    decision, reason_codes = _decision(packet, source_analysis, missing, probability_range, edge)
    summary = {
        "market_id": packet.get("market_id"),
        "sources_count": len(sources),
        "yes_evidence_count": len(source_analysis["yes_evidence"]),
        "no_evidence_count": len(source_analysis["no_evidence"]),
        "uncertainty_factor_count": len(source_analysis["uncertainty_factors"]),
        "decision": decision,
        "paper_orders_created": 0,
        "workspace_state_written": False,
        "safety_flags": SAFETY_FLAGS,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "packet_path": str(packet_file),
        "market": {
            "market_id": packet.get("market_id"),
            "market_title": packet.get("market_title"),
            "market_question": packet.get("market_question"),
            "resolution_criteria": packet.get("resolution_criteria"),
            "yes_price": yes_price,
            "no_price": no_price,
            "current_date": packet.get("current_date"),
        },
        "implied_probability_from_yes_price": _round_probability(yes_price),
        "yes_evidence": source_analysis["yes_evidence"],
        "no_evidence": source_analysis["no_evidence"],
        "uncertainty_factors": source_analysis["uncertainty_factors"],
        "source_reliability_notes": source_analysis["source_reliability_notes"],
        "missing_information": missing,
        "probability_estimate_range": probability_range,
        "edge_estimate_vs_market": edge,
        "decision": decision,
        "reason_codes": reason_codes,
        "human_review_note": _human_review_note(decision, reason_codes),
        "operator_notes": packet.get("operator_notes", []),
        "paper_orders_created": 0,
        "workspace_state_written": False,
        "summary": summary,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads a local manually curated packet only; no live web fetching, network, external API, credentials, wallet access, orders, or trading are included.",
            "Probability range is a deterministic fixture heuristic for research review only, not a calibrated statistical model.",
            "Paper-candidate output is a label only and never creates paper orders or writes workspace state.",
        ],
    }


def _md(value):
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    market = report["market"]
    summary = report["summary"]
    lines = [
        "# Single-Market Research Dossier",
        "",
        f"- Market ID: {market['market_id']}",
        f"- Title: {market['market_title']}",
        f"- Question: {market['market_question']}",
        f"- Current date: {market['current_date']}",
        f"- Yes price: {market['yes_price']}",
        f"- No price: {market['no_price']}",
        f"- Implied probability from Yes price: {report['implied_probability_from_yes_price']}",
        f"- Decision: {report['decision']}",
        f"- Reason codes: {json.dumps(report['reason_codes'], sort_keys=True)}",
        f"- Paper orders created: {report['paper_orders_created']}",
        "",
        "## Resolution Criteria",
        "",
        market["resolution_criteria"] or "",
        "",
        "## Probability And Edge",
        "",
        f"- Probability estimate range: {json.dumps(report['probability_estimate_range'], sort_keys=True)}",
        f"- Edge estimate vs market: {json.dumps(report['edge_estimate_vs_market'], sort_keys=True)}",
        "",
        "## Evidence Summary",
        "",
        f"- Sources: {summary['sources_count']}",
        f"- Yes evidence: {summary['yes_evidence_count']}",
        f"- No evidence: {summary['no_evidence_count']}",
        f"- Uncertainty factors: {summary['uncertainty_factor_count']}",
        f"- Missing information: {json.dumps(report['missing_information'], sort_keys=True)}",
        "",
        "## Yes Evidence",
        "",
    ]
    if report["yes_evidence"]:
        for item in report["yes_evidence"]:
            lines.append(f"- {item['source_id']}: {item['title']} (weight={item['weight']})")
    else:
        lines.append("- None")
    lines.extend(["", "## No Evidence", ""])
    if report["no_evidence"]:
        for item in report["no_evidence"]:
            lines.append(f"- {item['source_id']}: {item['title']} (weight={item['weight']})")
    else:
        lines.append("- None")
    lines.extend(["", "## Source Reliability", "", "| source_id | type | direction | reliability | weight | hint |", "| --- | --- | --- | --- | --- | --- |"])
    for item in report["source_reliability_notes"]:
        lines.append(
            f"| {_md(item['source_id'])} | {_md(item['source_type'])} | {_md(item['evidence_direction'])} | "
            f"{_md(item['reliability_level'])} | {_md(item['weight'])} | {_md(item['reliability_hint'])} |"
        )
    lines.extend(
        [
            "",
            "## Human Review Note",
            "",
            report["human_review_note"],
            "",
            "## Safety",
            "",
            "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    report = build_single_market_research_dossier(ROOT, args.packet)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

import argparse
import json
import re
import sys
from pathlib import Path


TASK_ID = "PMBOT-BRAIN-033-CRYPTO-THRESHOLD-HIT-TRIAGE"
SCHEMA_VERSION = "v1"
DEFAULT_SOURCE = Path(r"C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json")
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

ASSET_PATTERNS = (
    ("BTC", re.compile(r"\bbtc\b|\bbitcoin\b", re.IGNORECASE)),
    ("ETH", re.compile(r"\beth\b|\bethereum\b", re.IGNORECASE)),
)
THRESHOLD_WORD_RE = re.compile(r"\b(hit|reach|touch)\b", re.IGNORECASE)
MONEY_RE = re.compile(r"(?P<target_text>\$?\s*(?P<number>[0-9][0-9,]*(?:\.[0-9]+)?)\s*(?P<suffix>[kmb])?)", re.IGNORECASE)
THRESHOLD_RE = re.compile(
    r"\b(?P<phrase>hit|reach|touch)\s+"
    r"(?P<target_text>\$?\s*(?P<number>[0-9][0-9,]*(?:\.[0-9]+)?)\s*(?P<suffix>[kmb])?)\s+"
    r"(?P<relation>by|before)\s+"
    r"(?P<trigger>[^?]+)",
    re.IGNORECASE,
)
MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}
MONTH_DATE_RE = re.compile(
    r"\b("
    + "|".join(MONTHS)
    + r")\s+([0-9]{1,2})(?:st|nd|rd|th)?(?:,)?\s+([0-9]{4})\b",
    re.IGNORECASE,
)
END_OF_YEAR_RE = re.compile(r"\bend\s+of\s+([0-9]{4})\b", re.IGNORECASE)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Produce an offline triage report for saved crypto threshold-hit Gamma markets.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _market_rows(payload):
    if isinstance(payload, list):
        return payload, {}, "top_level_list"
    if isinstance(payload, dict):
        for key in ("markets", "data", "results"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows, payload, f"object_{key}_list"
    return [], {}, "unsupported"


def _looks_like_gamma_markets(rows):
    for row in rows:
        if not isinstance(row, dict):
            continue
        has_identity = row.get("id") is not None or row.get("conditionId") is not None
        has_market_shape = any(key in row for key in ("question", "title", "outcomes", "outcomePrices", "clobTokenIds"))
        if has_identity and has_market_shape:
            return True
    return False


def _primary_text(row):
    return str(row.get("question") or row.get("title") or "")


def _text_parts(row):
    parts = []
    for key in ("question", "title", "slug", "description", "category"):
        value = row.get(key) if isinstance(row, dict) else None
        if value:
            parts.append(str(value))
    for tag in _json_list(row.get("tags") if isinstance(row, dict) else None):
        if isinstance(tag, dict):
            value = tag.get("label") or tag.get("name") or tag.get("slug") or tag.get("id")
            if value:
                parts.append(str(value))
        elif tag:
            parts.append(str(tag))
    for event in _json_list(row.get("events") if isinstance(row, dict) else None):
        if isinstance(event, dict):
            for key in ("title", "slug"):
                value = event.get(key)
                if value:
                    parts.append(str(value))
    return " ".join(parts)


def _first_present(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return None


def _title(row):
    return str(row.get("title") or row.get("question") or "")


def _question(row):
    return str(row.get("question") or row.get("title") or "")


def _market_id(row):
    value = _first_present(row, "id", "marketId", "market_id", "conditionId", "condition_id")
    return str(value) if value is not None else "unknown"


def _condition_id(row):
    value = _first_present(row, "conditionId", "condition_id")
    return str(value) if value is not None else None


def _slug(row):
    value = row.get("slug")
    return str(value) if value is not None else None


def _float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _outcome_names(row):
    return [str(item).strip() for item in _json_list(row.get("outcomes")) if str(item).strip()]


def _outcome_prices(row):
    prices = []
    for item in _json_list(row.get("outcomePrices")):
        price = _float_or_none(item)
        if price is not None:
            prices.append(price)
    return prices


def _outcome_shape(names):
    lowered = [name.lower() for name in names]
    if len(lowered) == 2 and set(lowered) == {"yes", "no"}:
        return "yes_no"
    if len(lowered) > 2:
        return "multi_outcome"
    return "unknown"


def _current_prices(names, prices):
    current = {}
    for index, name in enumerate(names):
        if index < len(prices):
            current[name] = prices[index]
    return current


def _price_for(current_prices, outcome_name):
    for name, price in current_prices.items():
        if name.lower() == outcome_name:
            return price
    return None


def _asset_candidates(row):
    text = _text_parts(row)
    return [asset for asset, pattern in ASSET_PATTERNS if pattern.search(text)]


def _scale_numeric(value, suffix):
    number = float(value.replace(",", ""))
    suffix = str(suffix or "").lower()
    if suffix == "k":
        return number * 1000
    if suffix == "m":
        return number * 1000000
    if suffix == "b":
        return number * 1000000000
    return number


def _format_number(value):
    if value is None:
        return None
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def _normalize_target_text(value):
    return re.sub(r"\s+", "", str(value))


def _target_from_match(match):
    if match is None:
        return None, None
    target = _scale_numeric(match.group("number"), match.group("suffix"))
    return _format_number(target), _normalize_target_text(match.group("target_text"))


def _money_anywhere(text):
    return _target_from_match(MONEY_RE.search(text))


def _clean_trigger(value):
    return str(value).strip().strip(" .")


def _parse_deadline_date(value):
    text = str(value or "")
    match = MONTH_DATE_RE.search(text)
    if match:
        month = MONTHS[match.group(1).lower()]
        day = int(match.group(2))
        year = match.group(3)
        return f"{year}-{month}-{day:02d}"
    match = END_OF_YEAR_RE.search(text)
    if match:
        return f"{match.group(1)}-12-31"
    return None


def _threshold_details(text):
    match = THRESHOLD_RE.search(text)
    if match is None:
        return {
            "phrase": None,
            "target": None,
            "target_display": None,
            "relation": None,
            "deadline": None,
            "deadline_date": None,
            "event_trigger": None,
            "market_type": "ambiguous_threshold_hit",
        }
    target, target_display = _target_from_match(match)
    relation = match.group("relation").lower()
    trigger = _clean_trigger(match.group("trigger"))
    if relation == "by":
        market_type = "threshold_hit_by_date"
        deadline = trigger
        deadline_date = _parse_deadline_date(trigger)
        event_trigger = None
    elif relation == "before":
        market_type = "threshold_hit_before_event"
        deadline = None
        deadline_date = None
        event_trigger = trigger
    else:
        market_type = "ambiguous_threshold_hit"
        deadline = None
        deadline_date = None
        event_trigger = None
    return {
        "phrase": match.group("phrase").lower(),
        "target": target,
        "target_display": target_display,
        "relation": relation,
        "deadline": deadline,
        "deadline_date": deadline_date,
        "event_trigger": event_trigger,
        "market_type": market_type,
    }


def _candidate_status(asset_candidates, details, outcome_shape):
    if not asset_candidates:
        return "rejected", "unsupported_asset", "Question does not identify BTC, Bitcoin, ETH, or Ethereum."
    if len(asset_candidates) > 1:
        return "rejected", "ambiguous_asset", "Question identifies more than one supported crypto asset."
    if details["target"] is None:
        return "rejected", "missing_target", "Threshold-hit phrase does not include a numeric target."
    if outcome_shape != "yes_no":
        return "rejected", "unsupported_outcome_shape", "Market outcomes are not a binary Yes/No shape."
    if details["market_type"] == "ambiguous_threshold_hit":
        return "rejected", "ambiguous_threshold_hit", "Threshold-hit phrase does not include a clear by-date or before-event trigger."
    return "supported", None, None


def _reason_counts(candidates):
    counts = {}
    for row in candidates:
        reason_code = row["reason_code"]
        if reason_code:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _fixed_counts(keys, rows, field):
    counts = {key: 0 for key in keys}
    for row in rows:
        value = row[field]
        counts[value] = counts.get(value, 0) + 1
    return counts


def _asset_counts(candidates):
    counts = {"BTC": 0, "ETH": 0, "ambiguous": 0, "unsupported": 0}
    for row in candidates:
        asset = row["asset"]
        if asset in ("BTC", "ETH"):
            counts[asset] += 1
        elif row["asset_candidates"]:
            counts["ambiguous"] += 1
        else:
            counts["unsupported"] += 1
    return counts


def _build_candidate(row, source_index):
    text = _primary_text(row)
    details = _threshold_details(text)
    asset_candidates = _asset_candidates(row)
    asset = asset_candidates[0] if len(asset_candidates) == 1 else None
    outcomes = _outcome_names(row)
    prices = _outcome_prices(row)
    outcome_shape = _outcome_shape(outcomes)
    current_prices = _current_prices(outcomes, prices)
    status, reason_code, reason = _candidate_status(asset_candidates, details, outcome_shape)
    return {
        "source_index": source_index,
        "triage_status": status,
        "market_type": details["market_type"],
        "asset": asset,
        "asset_candidates": asset_candidates,
        "target": details["target"],
        "target_display": details["target_display"],
        "phrase": details["phrase"],
        "deadline": details["deadline"],
        "deadline_date": details["deadline_date"],
        "event_trigger": details["event_trigger"],
        "market_id": _market_id(row),
        "condition_id": _condition_id(row),
        "title": _title(row),
        "question": _question(row),
        "slug": _slug(row),
        "outcome_shape": outcome_shape,
        "outcomes": outcomes,
        "current_prices": current_prices,
        "yes_price": _price_for(current_prices, "yes"),
        "no_price": _price_for(current_prices, "no"),
        "liquidity": _float_or_none(_first_present(row, "liquidityNum", "liquidity_num", "liquidity")),
        "volume": _float_or_none(_first_present(row, "volumeNum", "volume_num", "volume")),
        "best_bid": _float_or_none(_first_present(row, "bestBid", "best_bid")),
        "best_ask": _float_or_none(_first_present(row, "bestAsk", "best_ask")),
        "reason_code": reason_code,
        "reason": reason,
    }


def _is_candidate(row):
    if not isinstance(row, dict):
        return False
    text = _primary_text(row)
    if THRESHOLD_WORD_RE.search(text) is None:
        return False
    has_direct_threshold_target = THRESHOLD_RE.search(text) is not None
    return has_direct_threshold_target or bool(_asset_candidates(row))


def build_crypto_threshold_hit_triage_report(root: Path, source_path=None, payload=None):
    del root
    source = Path(source_path) if source_path else DEFAULT_SOURCE
    data = payload if payload is not None else _load_json(source)
    rows, metadata, top_level_shape = _market_rows(data)
    gamma_shape_detected = _looks_like_gamma_markets(rows)

    candidates = [
        _build_candidate(row, index)
        for index, row in enumerate(rows)
        if _is_candidate(row)
    ]
    supported = [row for row in candidates if row["triage_status"] == "supported"]
    rejected = [row for row in candidates if row["triage_status"] != "supported"]
    crypto_candidates = [row for row in candidates if row["asset"] in ("BTC", "ETH") or row["asset_candidates"]]
    summary = {
        "total_markets_seen": len(rows),
        "threshold_hit_like_markets_found": len(candidates),
        "threshold_hit_crypto_candidates_found": len(crypto_candidates),
        "supported_triage_candidates": len(supported),
        "rejected_ambiguous_candidates": len(rejected),
        "market_type_counts": _fixed_counts(
            ("threshold_hit_by_date", "threshold_hit_before_event", "ambiguous_threshold_hit"),
            candidates,
            "market_type",
        ),
        "supported_market_type_counts": _fixed_counts(
            ("threshold_hit_by_date", "threshold_hit_before_event", "ambiguous_threshold_hit"),
            supported,
            "market_type",
        ),
        "reason_counts": _reason_counts(candidates),
        "asset_counts": _asset_counts(candidates),
        "candidate_table_count": len(candidates),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_path": str(source),
        "source_shape": "polymarket_gamma_markets_response" if gamma_shape_detected else "unsupported",
        "top_level_shape": top_level_shape,
        "gamma_market_list_detected": gamma_shape_detected,
        "metadata_keys": sorted(metadata.keys()) if isinstance(metadata, dict) else [],
        "summary": summary,
        "supported_triage_candidates": supported,
        "rejected_ambiguous_candidates": rejected,
        "candidate_table": candidates,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads a local saved JSON file only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.",
            "Threshold-hit candidates are triaged only and are not converted into the existing crypto numeric above/below scorer input.",
            "No paper orders, runtime wiring, dispatcher changes, or prompt automation are included.",
        ],
    }


def _md(value):
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Crypto Threshold-Hit Triage Report",
        "",
        f"- Source: {report['source_path']}",
        f"- Source shape: {report['source_shape']}",
        f"- Top-level shape: {report['top_level_shape']}",
        f"- Gamma market list detected: {str(report['gamma_market_list_detected']).lower()}",
        f"- Total markets seen: {summary['total_markets_seen']}",
        f"- Threshold-hit-like markets found: {summary['threshold_hit_like_markets_found']}",
        f"- Threshold-hit crypto candidates found: {summary['threshold_hit_crypto_candidates_found']}",
        f"- Supported triage candidates: {summary['supported_triage_candidates']}",
        f"- Rejected/ambiguous candidates: {summary['rejected_ambiguous_candidates']}",
        f"- Market type counts: {json.dumps(summary['market_type_counts'], sort_keys=True)}",
        f"- Supported market type counts: {json.dumps(summary['supported_market_type_counts'], sort_keys=True)}",
        f"- Reason counts: {json.dumps(summary['reason_counts'], sort_keys=True)}",
        "",
        "## Candidate Table",
        "",
        "| market_id | question | status | asset | target | type | deadline | event | yes | no | liquidity | reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if report["candidate_table"]:
        for row in report["candidate_table"]:
            lines.append(
                f"| {_md(row['market_id'])} | {_md(row['question'])} | {_md(row['triage_status'])} | "
                f"{_md(row['asset'] or ','.join(row['asset_candidates']))} | {_md(row['target_display'])} | "
                f"{_md(row['market_type'])} | {_md(row['deadline_date'] or row['deadline'])} | {_md(row['event_trigger'])} | "
                f"{_md(row['yes_price'])} | {_md(row['no_price'])} | {_md(row['liquidity'])} | {_md(row['reason_code'])} |"
            )
    else:
        lines.append("|  | None |  |  |  |  |  |  |  |  |  |  |")
    lines.extend(["", "## Safety Flags", ""])
    lines.append(
        "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false"
    )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_crypto_threshold_hit_triage_report(root, args.source)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

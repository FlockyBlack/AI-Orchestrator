import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


TASK_ID = "PMBOT-BRAIN-032-REAL-GAMMA-CRYPTO-NUMERIC-ADAPTER"
SCHEMA_VERSION = "v1"
DEFAULT_SOURCE = Path(r"C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_001.json")
TOP_CANDIDATE_LIMIT = 10
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

ASSET_KEYWORDS = ("BTC", "ETH", "SOL", "XRP", "crypto", "bitcoin", "ethereum")
ASSET_PATTERNS = {
    "BTC": re.compile(r"\bbtc\b", re.IGNORECASE),
    "ETH": re.compile(r"\beth\b", re.IGNORECASE),
    "SOL": re.compile(r"\bsol\b|solana", re.IGNORECASE),
    "XRP": re.compile(r"\bxrp\b|ripple", re.IGNORECASE),
    "crypto": re.compile(r"\bcrypto\b|cryptocurrency", re.IGNORECASE),
    "bitcoin": re.compile(r"\bbitcoin\b", re.IGNORECASE),
    "ethereum": re.compile(r"\bethereum\b", re.IGNORECASE),
}
ASSET_DETECTION = (
    ("BTC", re.compile(r"\bbtc\b|\bbitcoin\b", re.IGNORECASE)),
    ("ETH", re.compile(r"\beth\b|\bethereum\b", re.IGNORECASE)),
    ("SOL", re.compile(r"\bsol\b|solana", re.IGNORECASE)),
    ("XRP", re.compile(r"\bxrp\b|ripple", re.IGNORECASE)),
    ("crypto", re.compile(r"\bcrypto\b|cryptocurrency", re.IGNORECASE)),
)
ABOVE_RE = re.compile(r"(?:\babove\b|\bover\b|\bhigher\s+than\b|\bgreater\s+than\b|>)", re.IGNORECASE)
BELOW_RE = re.compile(r"(?:\bbelow\b|\bunder\b|\blower\s+than\b|\bless\s+than\b|<)", re.IGNORECASE)
UP_RE = re.compile(r"\bup\b", re.IGNORECASE)
DOWN_RE = re.compile(r"\bdown\b", re.IGNORECASE)
MONEY_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kmb])?", re.IGNORECASE)
PHRASE_NUMBER_RE = re.compile(
    r"(?:\babove\b|\bover\b|\bhigher\s+than\b|\bgreater\s+than\b|\bbelow\b|\bunder\b|\blower\s+than\b|\bless\s+than\b|>|<)\s*\$?\s*"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kmb]|years?|%)?",
    re.IGNORECASE,
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Produce an offline triage report for saved Polymarket Gamma markets.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_helpers(root: Path):
    paper_dir = root / "pm_bot" / "paper"
    scoring_dir = root / "pm_bot" / "scoring"
    return {
        "importer": _load_module(paper_dir / "run_manual_snapshot_workspace_import.py", "pmbot_real_market_triage_importer"),
        "adapter": _load_module(scoring_dir / "adapt_live_shaped_crypto_snapshot.py", "pmbot_real_market_triage_adapter"),
    }


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


def _text_parts(row):
    parts = []
    for key in ("question", "title", "slug", "description", "category"):
        value = row.get(key) if isinstance(row, dict) else None
        if value:
            parts.append(str(value))
    for tag in _json_list(row.get("tags") if isinstance(row, dict) else None):
        if isinstance(tag, dict):
            label = tag.get("label") or tag.get("name") or tag.get("slug") or tag.get("id")
            if label:
                parts.append(str(label))
        elif tag:
            parts.append(str(tag))
    for event in _json_list(row.get("events") if isinstance(row, dict) else None):
        if isinstance(event, dict):
            for key in ("title", "slug"):
                value = event.get(key)
                if value:
                    parts.append(str(value))
    return " ".join(parts)


def _title(row):
    return str(row.get("question") or row.get("title") or "")


def _market_id(row):
    value = row.get("id") or row.get("marketId") or row.get("market_id") or row.get("conditionId") or row.get("condition_id")
    return str(value) if value is not None else "unknown"


def _slug(row):
    value = row.get("slug")
    return str(value) if value is not None else None


def _category(row):
    value = row.get("category")
    if value:
        return str(value).strip()
    for event in _json_list(row.get("events")):
        if isinstance(event, dict):
            title = event.get("title") or event.get("slug")
            if title:
                return str(title).strip()
    return None


def _tags(row):
    tags = []
    for tag in _json_list(row.get("tags")):
        if isinstance(tag, dict):
            value = tag.get("label") or tag.get("name") or tag.get("slug") or tag.get("id")
            if value:
                tags.append(str(value).strip())
        elif tag:
            tags.append(str(tag).strip())
    return tags


def _count_bool(rows, key):
    counts = {"true": 0, "false": 0, "unknown": 0}
    for row in rows:
        value = row.get(key) if isinstance(row, dict) else None
        if value is True:
            counts["true"] += 1
        elif value is False:
            counts["false"] += 1
        else:
            counts["unknown"] += 1
    return counts


def _increment(counts, key):
    counts[key] = counts.get(key, 0) + 1


def _sorted_counts(counts):
    return {key: counts[key] for key in sorted(counts)}


def _outcome_names(row):
    return [str(item).strip() for item in _json_list(row.get("outcomes")) if str(item).strip()]


def _outcome_shape(row):
    names = [name.lower() for name in _outcome_names(row)]
    if len(names) > 2:
        return "multi_outcome"
    if len(names) == 2 and set(names) == {"yes", "no"}:
        return "yes_no"
    if len(names) == 2 and set(names) == {"up", "down"}:
        return "up_down"
    return "unknown"


def _asset_keyword_counts(rows):
    counts = {keyword: 0 for keyword in ASSET_KEYWORDS}
    for row in rows:
        text = _text_parts(row)
        for keyword in ASSET_KEYWORDS:
            if ASSET_PATTERNS[keyword].search(text):
                counts[keyword] += 1
    return counts


def _detected_asset(row):
    text = _text_parts(row)
    hits = [asset for asset, pattern in ASSET_DETECTION if pattern.search(text)]
    return hits[0] if len(hits) == 1 else None


def _detect_side(text):
    above = ABOVE_RE.search(text) is not None
    below = BELOW_RE.search(text) is not None
    if above == below:
        return None
    return "above" if above else "below"


def _has_above_below(text):
    return ABOVE_RE.search(text) is not None or BELOW_RE.search(text) is not None


def _has_up_down(text):
    return UP_RE.search(text) is not None or DOWN_RE.search(text) is not None


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


def _detect_numeric_target(row):
    text = _text_parts(row)
    for pattern in (MONEY_RE, PHRASE_NUMBER_RE):
        match = pattern.search(text)
        if match:
            return _format_number(_scale_numeric(match.group(1), match.group(2) if match.lastindex and match.lastindex >= 2 else None))
    return None


def _support_type(asset, outcome_shape, numeric_target, above_below, up_down):
    if outcome_shape == "multi_outcome":
        return "multi_outcome"
    if asset in ("BTC", "ETH") and numeric_target and above_below and outcome_shape == "yes_no":
        return "crypto_numeric_above_below"
    if asset in ("BTC", "ETH") and (up_down or outcome_shape == "up_down"):
        return "crypto_up_down_directional"
    if outcome_shape == "yes_no" and not asset:
        return "non_crypto_binary"
    if above_below and numeric_target:
        return "non_crypto_binary"
    return "unsupported"


def _why(raw_record, rejection):
    if rejection is None:
        return "actionable: real Gamma crypto numeric adapter accepted"
    return f"rejected: {rejection['reason_code']} - {rejection['reason']}"


def _adapter_result(importer, adapter, row):
    canonical = importer._polymarket_market_to_canonical(row)
    if canonical is None:
        return None, {
            "market_id": _market_id(row),
            "question": _title(row),
            "reason_code": "unsupported_gamma_market_shape",
            "reason": "Gamma market row could not be converted to the canonical snapshot shape.",
        }
    return adapter._adapt_snapshot(canonical)


def _candidate_priority(candidate):
    support_rank = {
        "crypto_numeric_above_below": 0,
        "crypto_up_down_directional": 1,
        "non_crypto_binary": 2,
        "multi_outcome": 3,
        "unsupported": 4,
    }
    actionable_rank = 0 if candidate["current_adapter_actionable"] else 1
    numeric_rank = 0 if candidate["detected_numeric_target"] is not None else 1
    return (
        actionable_rank,
        support_rank.get(candidate["suggested_next_support_type"], 9),
        numeric_rank,
        candidate["source_index"],
        candidate["market_id"],
    )


def _rejected_candidate_priority(candidate):
    numeric_rank = 0 if candidate["detected_numeric_target"] is not None else 1
    asset_rank = 0 if candidate["detected_asset"] in ("BTC", "ETH") else 1
    return (
        asset_rank,
        numeric_rank,
        candidate["source_index"],
        candidate["market_id"],
    )


def _build_candidate(importer, adapter, row, source_index):
    raw_record, rejection = _adapter_result(importer, adapter, row)
    text = _text_parts(row)
    outcome_shape = _outcome_shape(row)
    asset = _detected_asset(row)
    numeric_target = _detect_numeric_target(row)
    above_below = _has_above_below(text)
    up_down = _has_up_down(text)
    return {
        "source_index": source_index,
        "title": _title(row),
        "market_id": _market_id(row),
        "slug": _slug(row),
        "detected_asset": asset,
        "detected_side_or_outcome_shape": _detect_side(text) or outcome_shape,
        "outcome_shape": outcome_shape,
        "detected_numeric_target": numeric_target,
        "current_adapter_actionable": rejection is None,
        "why_actionable_or_rejected": _why(raw_record, rejection),
        "suggested_next_support_type": _support_type(asset, outcome_shape, numeric_target, above_below, up_down),
    }


def _strip_candidate_sort_fields(candidate):
    return {key: value for key, value in candidate.items() if key != "source_index"}


def build_real_market_triage_report(root: Path, source_path=None):
    source = Path(source_path) if source_path else DEFAULT_SOURCE
    helpers = _load_helpers(root)
    importer = helpers["importer"]
    adapter = helpers["adapter"]
    payload = _load_json(source)
    rows, metadata, top_level_shape = _market_rows(payload)
    gamma_shape_detected = _looks_like_gamma_markets(rows)

    active_counts = _count_bool(rows, "active")
    closed_counts = _count_bool(rows, "closed")
    category_counts = {}
    tag_counts = {}
    outcome_shape_counts = {"yes_no": 0, "up_down": 0, "multi_outcome": 0, "unknown": 0}
    numeric_target_detected = 0
    above_below_phrase_detected = 0
    up_down_phrase_detected = 0
    crypto_numeric_actionable = 0
    rejection_counts = {}
    candidates = []

    for index, row in enumerate(rows):
        category = _category(row)
        if category:
            _increment(category_counts, category)
        for tag in _tags(row):
            _increment(tag_counts, tag)

        shape = _outcome_shape(row)
        outcome_shape_counts[shape] += 1
        text = _text_parts(row)
        if _detect_numeric_target(row) is not None:
            numeric_target_detected += 1
        if _has_above_below(text):
            above_below_phrase_detected += 1
        if _has_up_down(text):
            up_down_phrase_detected += 1

        _raw, rejection = _adapter_result(importer, adapter, row)
        if rejection is None:
            crypto_numeric_actionable += 1
        else:
            _increment(rejection_counts, rejection["reason_code"])

        candidates.append(_build_candidate(importer, adapter, row, index))

    supported_candidates = [
        _strip_candidate_sort_fields(candidate)
        for candidate in sorted(
            [candidate for candidate in candidates if candidate["current_adapter_actionable"]],
            key=_candidate_priority,
        )[:TOP_CANDIDATE_LIMIT]
    ]
    rejected_candidates = [
        _strip_candidate_sort_fields(candidate)
        for candidate in sorted(
            [candidate for candidate in candidates if not candidate["current_adapter_actionable"]],
            key=_rejected_candidate_priority,
        )[:TOP_CANDIDATE_LIMIT]
    ]
    top_candidates = [
        _strip_candidate_sort_fields(candidate)
        for candidate in sorted(candidates, key=_candidate_priority)[:TOP_CANDIDATE_LIMIT]
    ]
    source_shape = "polymarket_gamma_markets_response" if gamma_shape_detected else "unsupported"
    summary = {
        "total_markets_seen": len(rows),
        "active_counts": active_counts,
        "closed_counts": closed_counts,
        "category_counts": _sorted_counts(category_counts),
        "tag_counts": _sorted_counts(tag_counts),
        "asset_keyword_counts": _asset_keyword_counts(rows),
        "outcome_shape_counts": outcome_shape_counts,
        "numeric_target_detected": numeric_target_detected,
        "above_below_phrase_detected": above_below_phrase_detected,
        "up_down_phrase_detected": up_down_phrase_detected,
        "real_gamma_crypto_numeric_adapted": crypto_numeric_actionable,
        "crypto_numeric_actionable_after_adapter_update": crypto_numeric_actionable,
        "current_crypto_numeric_actionable": crypto_numeric_actionable,
        "adapter_rejection_reason_counts": _sorted_counts(rejection_counts),
        "supported_candidate_count": len(supported_candidates),
        "still_rejected_candidate_count": len(rejected_candidates),
        "top_candidate_count": len(top_candidates),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_path": str(source),
        "source_shape": source_shape,
        "top_level_shape": top_level_shape,
        "gamma_market_list_detected": gamma_shape_detected,
        "metadata_keys": sorted(metadata.keys()) if isinstance(metadata, dict) else [],
        "summary": summary,
        "supported_candidates": supported_candidates,
        "still_rejected_candidates": rejected_candidates,
        "top_candidates": top_candidates,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads a local saved JSON file only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.",
            "Adapter support is limited to unambiguous Yes/No BTC, Bitcoin, ETH, or Ethereum numeric above/below markets.",
            "Suggested support types are deterministic triage labels for product readiness only, not runtime wiring.",
        ],
    }


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Real Market Triage Report",
        "",
        f"- Source: {report['source_path']}",
        f"- Source shape: {report['source_shape']}",
        f"- Top-level shape: {report['top_level_shape']}",
        f"- Gamma market list detected: {str(report['gamma_market_list_detected']).lower()}",
        f"- Total markets seen: {summary['total_markets_seen']}",
        f"- Active counts: {json.dumps(summary['active_counts'], sort_keys=True)}",
        f"- Closed counts: {json.dumps(summary['closed_counts'], sort_keys=True)}",
        f"- Real Gamma crypto numeric adapted: {summary['real_gamma_crypto_numeric_adapted']}",
        f"- Crypto numeric actionable after adapter update: {summary['crypto_numeric_actionable_after_adapter_update']}",
        f"- Adapter rejection reason counts: {json.dumps(summary['adapter_rejection_reason_counts'], sort_keys=True)}",
        f"- Numeric target detected: {summary['numeric_target_detected']}",
        f"- Above/below phrase detected: {summary['above_below_phrase_detected']}",
        f"- Up/down phrase detected: {summary['up_down_phrase_detected']}",
        "",
        "## Asset Keyword Counts",
        "",
    ]
    for keyword, count in summary["asset_keyword_counts"].items():
        lines.append(f"- {keyword}: {count}")
    lines.extend(["", "## Outcome Shape Counts", ""])
    for key, count in summary["outcome_shape_counts"].items():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Category Counts", ""])
    if summary["category_counts"]:
        for key, count in summary["category_counts"].items():
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- None")
    lines.extend(["", "## Tag Counts", ""])
    if summary["tag_counts"]:
        for key, count in summary["tag_counts"].items():
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Supported Candidates",
        "",
        "| market_id | question | asset | shape_or_side | target | support_type | reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    if report["supported_candidates"]:
        for row in report["supported_candidates"]:
            lines.append(
                f"| {row['market_id']} | {row['title']} | {row['detected_asset'] or ''} | {row['detected_side_or_outcome_shape']} | "
                f"{row['detected_numeric_target'] or ''} | {row['suggested_next_support_type']} | {row['why_actionable_or_rejected']} |"
            )
    else:
        lines.append("|  | None |  |  |  |  | Strict parser found no Yes/No BTC, Bitcoin, ETH, or Ethereum market with one numeric target and one clear above/below side. |")
    lines.extend([
        "",
        "## Still Rejected Candidates",
        "",
        "| market_id | question | asset | shape_or_side | target | support_type | reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in report["still_rejected_candidates"]:
        lines.append(
            f"| {row['market_id']} | {row['title']} | {row['detected_asset'] or ''} | {row['detected_side_or_outcome_shape']} | "
            f"{row['detected_numeric_target'] or ''} | {row['suggested_next_support_type']} | {row['why_actionable_or_rejected']} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false",
        "",
    ])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_real_market_triage_report(root, args.source)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

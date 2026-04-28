import argparse
import json
import re
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "execution_allowed": False,
    "trading_allowed": False,
}

SCORING_CONFIG = {
    "edge_buffer": 0.025,
    "min_candidate_edge": 0.04,
    "min_liquidity_usd": 50000,
    "watch_liquidity_usd": 25000,
    "max_spread": 0.05,
    "watch_spread": 0.08,
}

ASSET_ALIASES = {
    "BTC": ("btc", "bitcoin"),
    "ETH": ("eth", "ethereum"),
}
ASSET_PATTERNS = {
    asset: re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(alias) for alias in aliases) + r")(?![A-Za-z0-9])", re.IGNORECASE)
    for asset, aliases in ASSET_ALIASES.items()
}
ABOVE_RE = re.compile(r"(?:\babove\b|\bover\b|\bhigher\s+than\b|\bgreater\s+than\b|>)", re.IGNORECASE)
BELOW_RE = re.compile(r"(?:\bbelow\b|\bunder\b|\blower\s+than\b|\bless\s+than\b|<)", re.IGNORECASE)
MONEY_TARGET_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kmb])?", re.IGNORECASE)
PHRASE_TARGET_RE = re.compile(
    r"(?:\babove\b|\bover\b|\bhigher\s+than\b|\bgreater\s+than\b|\bbelow\b|\bunder\b|\blower\s+than\b|\bless\s+than\b|>|<)"
    r"\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kmb])?",
    re.IGNORECASE,
)


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Normalize fixture crypto numeric markets for PMBOT scoring.")
    parser.add_argument("raw_fixture", help="Path to raw crypto numeric market fixture records.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _question(record):
    return str(record.get("question") or record.get("title") or "")


def _asset(question):
    hits = [asset for asset, pattern in ASSET_PATTERNS.items() if pattern.search(question)]
    return hits[0] if len(hits) == 1 else None


def _side(question):
    above = ABOVE_RE.search(question) is not None
    below = BELOW_RE.search(question) is not None
    if above == below:
        return None
    return "above" if above else "below"


def _scale_target(value, suffix):
    target = float(value.replace(",", ""))
    suffix = str(suffix or "").lower()
    if suffix == "k":
        return target * 1000
    if suffix == "m":
        return target * 1000000
    if suffix == "b":
        return target * 1000000000
    return target


def _unique_targets(matches):
    values = []
    for match in matches:
        target = _scale_target(match.group(1), match.group(2))
        if target not in values:
            values.append(target)
    return values


def _target_price(question):
    money_targets = _unique_targets(MONEY_TARGET_RE.finditer(question))
    if len(money_targets) == 1:
        return money_targets[0]
    if len(money_targets) > 1:
        return None

    phrase_targets = _unique_targets(PHRASE_TARGET_RE.finditer(question))
    if len(phrase_targets) == 1:
        return phrase_targets[0]
    return None


def _has_ambiguous_settlement(question):
    lowered = question.lower()
    return any(token in lowered for token in ("intraday", "touch", "anytime", "between", "range", "all time high"))


def _missing_market_data(record):
    required = ("market_yes_price", "liquidity_usd", "spread")
    return [field for field in required if field not in record or record[field] is None]


def _rejection(code, record, reason):
    return {
        "market_id": record.get("market_id", "unknown"),
        "question": _question(record),
        "reason_code": code,
        "reason": reason,
    }


def _normalize_record(record):
    question = _question(record)
    category = str(record.get("category", "")).lower()
    if category and category != "crypto":
        return None, _rejection("non_crypto_market", record, "Record category is not crypto.")

    asset = record.get("asset") if record.get("asset") in ASSET_ALIASES else _asset(question)
    if asset is None:
        return None, _rejection("non_crypto_market", record, "Question does not identify BTC or ETH.")

    if _has_ambiguous_settlement(question):
        return None, _rejection("ambiguous_settlement", record, "Question uses ambiguous settlement wording.")

    target_price = record.get("target_price_candidate")
    if target_price is None:
        target_price = _target_price(question)
    if target_price is None:
        return None, _rejection("missing_target", record, "Question does not include a numeric target price.")

    side = record.get("side_candidate") if record.get("side_candidate") in ("above", "below") else _side(question)
    if side is None:
        return None, _rejection("unclear_side", record, "Question does not clearly specify above or below.")

    expiry = record.get("expiry")
    if not expiry:
        return None, _rejection("missing_expiry", record, "Record does not include an expiry date.")

    missing_fields = _missing_market_data(record)
    if missing_fields:
        return None, _rejection("missing_market_data", record, f"Record is missing market data: {', '.join(missing_fields)}.")

    return {
        "market_id": record["market_id"],
        "title": question,
        "asset": asset,
        "side": side,
        "target_price": target_price,
        "expiry": expiry,
        "current_price": float(record.get("current_price", 0.0)),
        "market_yes_price": float(record["market_yes_price"]),
        "liquidity_usd": float(record["liquidity_usd"]),
        "spread": float(record["spread"]),
        "risk_level": record.get("risk_level", "medium"),
        "thirty_day_change_pct": float(record.get("thirty_day_change_pct", 0.0)),
        "volatility_30d_pct": float(record.get("volatility_30d_pct", 50.0)),
    }, None


def build_intake_report(raw_fixture):
    normalized = []
    rejected = []
    for record in raw_fixture["raw_markets"]:
        normalized_record, rejection = _normalize_record(record)
        if rejection is not None:
            rejected.append(rejection)
        else:
            normalized.append(normalized_record)

    reason_counts = {}
    for item in rejected:
        reason_counts[item["reason_code"]] = reason_counts.get(item["reason_code"], 0) + 1

    normalized_fixture = {
        "schema_version": "v1",
        "fixture_id": "crypto_numeric_intake_normalized_v1",
        "fixture_only": True,
        "paper_only": True,
        "scoring_config": SCORING_CONFIG,
        "markets": normalized,
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-008-CRYPTO-NUMERIC-MARKET-INTAKE",
        "source_fixture_id": raw_fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "summary": {
            "raw_markets": len(raw_fixture["raw_markets"]),
            "normalized_supported": len(normalized),
            "rejected": len(rejected),
            "rejection_reasons": reason_counts,
        },
        "normalized_scorer_fixture": normalized_fixture,
        "rejections": rejected,
        "review_note": "Offline fixture intake only. Output is normalized for paper scoring review.",
    }


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# PMBOT Crypto Numeric Market Intake",
        "",
        "Offline fixture intake for crypto numeric market records.",
        "",
        "## Summary",
        "",
        f"- Raw markets: {summary['raw_markets']}",
        f"- Normalized supported: {summary['normalized_supported']}",
        f"- Rejected: {summary['rejected']}",
        "",
        "## Rejection Reasons",
        "",
    ]
    for code, count in sorted(summary["rejection_reasons"].items()):
        lines.append(f"- {code}: {count}")
    lines.extend(["", "## Normalized Markets", "", "| market_id | asset | side | target_price | expiry | yes_price | liquidity | spread |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    for row in report["normalized_scorer_fixture"]["markets"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['target_price']:.2f} | {row['expiry']} | "
            f"{row['market_yes_price']:.4f} | {row['liquidity_usd']:.2f} | {row['spread']:.4f} |"
        )
    lines.extend(["", "## Rejections", "", "| market_id | reason_code | reason |", "| --- | --- | --- |"])
    for row in report["rejections"]:
        lines.append(f"| {row['market_id']} | {row['reason_code']} | {row['reason']} |")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    report = build_intake_report(_load_json(Path(args.raw_fixture)))
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

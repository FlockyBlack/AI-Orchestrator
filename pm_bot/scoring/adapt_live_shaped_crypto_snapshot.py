import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "network_used": False,
    "api_used": False,
    "credentials_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
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


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Adapt offline live-shaped crypto snapshots into raw market intake records.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _question(snapshot):
    return str(snapshot.get("question") or snapshot.get("title") or "")


def _market_text(snapshot):
    parts = []
    for key in ("question", "title", "slug"):
        value = snapshot.get(key)
        if value:
            parts.append(str(value))
    return " ".join(parts)


def _asset(text):
    hits = [asset for asset, pattern in ASSET_PATTERNS.items() if pattern.search(text)]
    if len(hits) == 1:
        return hits[0], None
    if len(hits) > 1:
        return None, "ambiguous_asset"
    return None, "unsupported_asset"


def _side(text):
    above = ABOVE_RE.search(text) is not None
    below = BELOW_RE.search(text) is not None
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


def _target_price(text):
    money_targets = _unique_targets(MONEY_TARGET_RE.finditer(text))
    if len(money_targets) == 1:
        return money_targets[0], None
    if len(money_targets) > 1:
        return None, "unsupported_gamma_numeric_shape"

    phrase_targets = _unique_targets(PHRASE_TARGET_RE.finditer(text))
    if len(phrase_targets) == 1:
        return phrase_targets[0], None
    if len(phrase_targets) > 1:
        return None, "unsupported_gamma_numeric_shape"
    return None, "missing_target"


def _outcome_names(snapshot):
    outcomes = snapshot.get("outcomes", [])
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except json.JSONDecodeError:
            outcomes = []
    names = []
    for outcome in outcomes:
        if isinstance(outcome, dict):
            name = outcome.get("name")
        else:
            name = outcome
        if name is not None and str(name).strip():
            names.append(str(name).strip().lower())
    return names


def _outcome_shape(snapshot):
    names = _outcome_names(snapshot)
    if len(names) == 2 and set(names) == {"yes", "no"}:
        return "yes_no"
    return "unsupported"


def _yes_price(snapshot):
    if snapshot.get("yes_price") is not None:
        return float(snapshot["yes_price"])
    for outcome in snapshot.get("outcomes", []):
        if str(outcome.get("name", "")).lower() == "yes" and outcome.get("price") is not None:
            return float(outcome["price"])
    return None


def _liquidity(snapshot):
    value = snapshot.get("liquidity_num", snapshot.get("liquidity"))
    return None if value is None else float(value)


def _spread(snapshot):
    if snapshot.get("spread") is not None:
        return float(snapshot["spread"])
    bid = snapshot.get("best_bid")
    ask = snapshot.get("best_ask")
    if bid is not None and ask is not None:
        return round(float(ask) - float(bid), 4)
    return 0.05


def _rejection(code, snapshot, reason):
    return {
        "market_id": snapshot.get("condition_id") or snapshot.get("market_id") or "unknown",
        "question": _question(snapshot),
        "reason_code": code,
        "reason": reason,
    }


def _adapt_snapshot(snapshot):
    market_id = snapshot.get("condition_id") or snapshot.get("market_id")
    if not market_id:
        return None, _rejection("missing_market_id", snapshot, "Snapshot does not include a condition_id or market_id.")

    question = _question(snapshot)
    if not question:
        return None, _rejection("missing_question", snapshot, "Snapshot does not include a question or title.")

    price = _yes_price(snapshot)
    if price is None:
        return None, _rejection("missing_price", snapshot, "Snapshot does not include a Yes outcome price.")

    liquidity = _liquidity(snapshot)
    if liquidity is None:
        return None, _rejection("missing_liquidity", snapshot, "Snapshot does not include liquidity.")

    expiry = snapshot.get("end_date_iso") or snapshot.get("expiry") or snapshot.get("endDate")
    if not expiry:
        return None, _rejection("missing_expiry", snapshot, "Snapshot does not include an expiry date.")

    text = _market_text(snapshot) or question
    asset, asset_error = _asset(text)
    if asset_error == "ambiguous_asset":
        return None, _rejection("ambiguous_asset", snapshot, "Question identifies more than one supported crypto asset.")
    if asset is None:
        return None, _rejection("unsupported_asset", snapshot, "Question does not identify supported BTC or ETH asset.")

    side = _side(text)
    if side is None:
        return None, _rejection("ambiguous_side", snapshot, "Question does not specify exactly one above/below side.")

    target_price, target_error = _target_price(text)
    if target_error == "missing_target":
        return None, _rejection("missing_target", snapshot, "Question does not include a numeric target price.")
    if target_error == "unsupported_gamma_numeric_shape":
        return None, _rejection("unsupported_gamma_numeric_shape", snapshot, "Question does not include exactly one numeric target price.")

    if _outcome_shape(snapshot) != "yes_no":
        return None, _rejection("unsupported_outcome_shape", snapshot, "Snapshot outcomes are not exactly Yes and No.")

    context = snapshot.get("oracle_context", {})
    return {
        "market_id": market_id,
        "category": "crypto",
        "question": question,
        "asset": asset,
        "side_candidate": side,
        "target_price_candidate": target_price,
        "expiry": expiry,
        "market_yes_price": price,
        "liquidity_usd": liquidity,
        "spread": _spread(snapshot),
        "current_price": float(context.get("current_price", snapshot.get("current_price", 0.0))),
        "risk_level": context.get("risk_level", snapshot.get("risk_level", "medium")),
        "thirty_day_change_pct": float(context.get("thirty_day_change_pct", snapshot.get("thirty_day_change_pct", 0.0))),
        "volatility_30d_pct": float(context.get("volatility_30d_pct", snapshot.get("volatility_30d_pct", 50.0))),
    }, None


def _reason_counts(rejections):
    counts = {}
    for item in rejections:
        counts[item["reason_code"]] = counts.get(item["reason_code"], 0) + 1
    return counts


def _chain_check(root: Path, raw_fixture):
    scoring_dir = root / "pm_bot" / "scoring"
    intake = _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_live_shape_adapter_intake")
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_live_shape_adapter_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_live_shape_adapter_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_live_shape_adapter_planner")
    intake_report = intake.build_intake_report(raw_fixture)
    score_report = scorer.score_fixture(intake_report["normalized_scorer_fixture"])
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)
    passed = (
        intake_report["summary"]["normalized_supported"] == len(raw_fixture["raw_markets"])
        and score_report["markets_scored"] == len(raw_fixture["raw_markets"])
    )
    return {
        "passed": passed,
        "normalized_supported": intake_report["summary"]["normalized_supported"],
        "markets_scored": score_report["markets_scored"],
        "paper_candidates": review_table["group_counts"]["paper_candidate"],
        "watchlist": review_table["group_counts"]["watchlist"],
        "rejected_after_scoring": review_table["group_counts"]["reject"],
        "paper_limit_orders": order_plan["paper_order_count"],
    }


def build_adapter_report(root: Path):
    fixture = _load_json(root / "pm_bot" / "scoring" / "crypto_numeric_live_shaped_snapshot_fixture.v1.json")
    adapted = []
    rejections = []
    for snapshot in fixture["markets"]:
        raw_record, rejection = _adapt_snapshot(snapshot)
        if rejection is not None:
            rejections.append(rejection)
        else:
            adapted.append(raw_record)
    raw_fixture = {
        "schema_version": "v1",
        "fixture_id": "crypto_numeric_live_shaped_adapted_raw_markets_v1",
        "fixture_only": True,
        "paper_only": True,
        "raw_markets": adapted,
    }
    chain_check = _chain_check(root, raw_fixture)
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-015-LIVE-SHAPED-MARKET-SNAPSHOT-ADAPTER",
        "source_fixture_id": fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "adapter_summary": {
            "snapshot_markets": len(fixture["markets"]),
            "adapted_raw_markets": len(adapted),
            "adapter_rejections": len(rejections),
            "rejection_reasons": _reason_counts(rejections),
            "intake_chain_check_passed": chain_check["passed"],
        },
        "adapted_raw_fixture": raw_fixture,
        "adapter_rejections": rejections,
        "intake_chain_check": chain_check,
        "limitations": [
            "Uses fixture live-shaped snapshots only; no live fetcher, network, or external API is implemented.",
            "Adapter output targets the existing crypto numeric raw market intake format and does not replace the intake chain.",
            "Current price, volatility, and momentum are fixture fields, not live market data.",
        ],
        "review_note": "Offline adapter for future read-only market data shape compatibility only.",
    }


def render_markdown(report):
    summary = report["adapter_summary"]
    chain = report["intake_chain_check"]
    lines = [
        "# PMBOT Live-Shaped Crypto Snapshot Adapter",
        "",
        "Offline fixture adapter from read-only-market-shaped snapshots to crypto numeric raw market intake records.",
        "",
        "## Summary",
        "",
        f"- Snapshot markets: {summary['snapshot_markets']}",
        f"- Adapted raw markets: {summary['adapted_raw_markets']}",
        f"- Adapter rejections: {summary['adapter_rejections']}",
        f"- Intake chain check passed: {str(summary['intake_chain_check_passed']).lower()}",
        f"- Chain markets scored: {chain['markets_scored']}",
        f"- Chain paper candidates: {chain['paper_candidates']}",
        f"- Chain watchlist: {chain['watchlist']}",
        f"- Chain rejected after scoring: {chain['rejected_after_scoring']}",
        "",
        "## Rejection Reasons",
        "",
    ]
    for code, count in sorted(summary["rejection_reasons"].items()):
        lines.append(f"- {code}: {count}")
    lines.extend(["", "## Adapted Raw Markets", "", "| market_id | asset | side | target | expiry | yes_price | liquidity | spread |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    for row in report["adapted_raw_fixture"]["raw_markets"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side_candidate']} | {row['target_price_candidate']:.2f} | "
            f"{row['expiry']} | {row['market_yes_price']:.4f} | {row['liquidity_usd']:.2f} | {row['spread']:.4f} |"
        )
    lines.extend(["", "## Adapter Rejections", "", "| market_id | reason_code | reason |", "| --- | --- | --- |"])
    for row in report["adapter_rejections"]:
        lines.append(f"| {row['market_id']} | {row['reason_code']} | {row['reason']} |")
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; live_fetcher_implemented=false; network_used=false; api_used=false; credentials_used=false; wallet_used=false; real_order_created=false; trading_allowed=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_adapter_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

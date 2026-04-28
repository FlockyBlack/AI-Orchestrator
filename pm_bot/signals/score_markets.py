import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def score_market(normalized_market):
    prices = normalized_market["prices"]
    outcomes = normalized_market["outcomes"]
    sorted_outcomes = sorted(outcomes, key=lambda name: prices[name], reverse=True)
    lead_outcome = sorted_outcomes[0]
    lead_price = prices[lead_outcome]
    price_sum = normalized_market["price_sum"]
    binary_bonus = 0.15 if normalized_market["has_binary_outcomes"] else 0.0
    liquidity_bonus = 0.1 if normalized_market["liquidity"] >= 10000 else 0.0
    confidence = round(min(0.99, lead_price + binary_bonus + liquidity_bonus), 2)
    reasons = [
        f"lead_outcome:{lead_outcome}",
        f"lead_price:{lead_price:.2f}",
        f"binary_market:{str(normalized_market['has_binary_outcomes']).lower()}",
        f"price_sum:{price_sum:.2f}",
        f"liquidity_bucket:{'deep' if normalized_market['liquidity'] >= 10000 else 'shallow'}",
    ]
    if abs(price_sum - 1.0) < 0.000001:
        safety_classification = "bounded_fixture_market"
    else:
        safety_classification = "review_fixture_market"
    return {
        "schema_version": "v1",
        "market_id": normalized_market["market_id"],
        "title": normalized_market["title"],
        "lead_outcome": lead_outcome,
        "confidence": confidence,
        "reasons": reasons,
        "safety_classification": safety_classification,
        "recommendation_type": "research_only",
        "execution_allowed": False,
        "trading_allowed": False,
        "wallet_required": False,
        "private_key_required": False,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: score_markets.py <normalized_market_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(score_market(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

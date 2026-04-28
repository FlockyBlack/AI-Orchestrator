import json
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "execution_allowed": False,
    "trading_allowed": False,
}

MAX_EXTENSION_FOR_PAPER_CANDIDATE = 0.055
RICH_MARKET_PRICE_FOR_EXTENSION_GUARD = 0.60


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def _directional_gap(market):
    current_price = float(market["current_price"])
    target_price = float(market["target_price"])
    if market["side"] == "above":
        return (current_price - target_price) / target_price
    if market["side"] == "below":
        return (target_price - current_price) / target_price
    raise ValueError(f"unsupported side: {market['side']}")


def _directional_momentum(market):
    momentum = float(market["thirty_day_change_pct"]) / 100.0
    if market["side"] == "above":
        return momentum
    if market["side"] == "below":
        return -momentum
    raise ValueError(f"unsupported side: {market['side']}")


def _model_probability(market):
    liquidity = float(market["liquidity_usd"])
    liquidity_component = 0.02 if liquidity >= 100000 else 0.0 if liquidity >= 50000 else -0.05
    probability = (
        0.50
        + (_directional_gap(market) * 3.0)
        + (_directional_momentum(market) * 1.2)
        - ((float(market["volatility_30d_pct"]) / 100.0) * 0.15)
        + liquidity_component
    )
    return round(_clamp(probability, 0.05, 0.95), 4)


def _liquidity_status(market, config):
    liquidity = float(market["liquidity_usd"])
    if liquidity >= float(config["min_liquidity_usd"]):
        return "pass"
    if liquidity >= float(config["watch_liquidity_usd"]):
        return "watch"
    return "fail"


def _spread_status(market, config):
    spread = float(market["spread"])
    if spread <= float(config["max_spread"]):
        return "pass"
    if spread <= float(config["watch_spread"]):
        return "watch"
    return "fail"


def _risk_status(market):
    risk_level = market["risk_level"]
    if risk_level == "low":
        return "pass"
    if risk_level == "medium":
        return "watch"
    return "fail"


def _extension_status(market):
    if (
        _directional_gap(market) >= MAX_EXTENSION_FOR_PAPER_CANDIDATE
        and float(market["market_yes_price"]) >= RICH_MARKET_PRICE_FOR_EXTENSION_GUARD
    ):
        return "watch"
    return "pass"


def _decision(edge_after_buffer, liquidity_status, spread_status, risk_status, extension_status, config):
    if (
        edge_after_buffer <= 0
        or liquidity_status == "fail"
        or spread_status == "fail"
        or risk_status == "fail"
    ):
        return "reject"
    if (
        edge_after_buffer < float(config["min_candidate_edge"])
        or liquidity_status == "watch"
        or spread_status == "watch"
        or risk_status == "watch"
        or extension_status == "watch"
    ):
        return "watchlist"
    return "paper_candidate"


def _explanation(market, raw_edge, edge_after_buffer, liquidity_status, spread_status, risk_status, extension_status, decision):
    return (
        f"{market['asset']} {market['side']} {market['target_price']} by {market['expiry']} "
        f"scores model_probability={market['model_probability']:.4f} vs market_probability="
        f"{market['market_probability']:.4f}; raw_edge={raw_edge:.4f}, edge_after_buffer="
        f"{edge_after_buffer:.4f}; liquidity={liquidity_status}, spread={spread_status}, "
        f"risk={risk_status}, extension={extension_status}; decision={decision}. Offline fixture paper scoring only."
    )


def score_market(market, config):
    model_probability = _model_probability(market)
    market_probability = round(float(market["market_yes_price"]), 4)
    raw_edge = round(model_probability - market_probability, 4)
    edge_after_buffer = round(raw_edge - float(config["edge_buffer"]), 4)
    liquidity_status = _liquidity_status(market, config)
    spread_status = _spread_status(market, config)
    risk_status = _risk_status(market)
    extension_status = _extension_status(market)
    decision = _decision(edge_after_buffer, liquidity_status, spread_status, risk_status, extension_status, config)
    enriched = dict(market)
    enriched["model_probability"] = model_probability
    enriched["market_probability"] = market_probability
    return {
        "market_id": market["market_id"],
        "asset": market["asset"],
        "side": market["side"],
        "target_price": market["target_price"],
        "expiry": market["expiry"],
        "current_price": market["current_price"],
        "market_yes_price": market["market_yes_price"],
        "model_probability": model_probability,
        "market_probability": market_probability,
        "raw_edge": raw_edge,
        "edge_after_buffer": edge_after_buffer,
        "liquidity_status": liquidity_status,
        "spread_status": spread_status,
        "risk_status": risk_status,
        "decision": decision,
        "explanation": _explanation(enriched, raw_edge, edge_after_buffer, liquidity_status, spread_status, risk_status, extension_status, decision),
        **SAFETY_FLAGS,
    }


def score_fixture(payload):
    config = payload["scoring_config"]
    scores = [score_market(market, config) for market in payload["markets"]]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-001-CRYPTO-NUMERIC-MARKET-SCORER",
        "fixture_id": payload["fixture_id"],
        "deterministic": True,
        "offline_only": True,
        "paper_only": True,
        "execution_allowed": False,
        "trading_allowed": False,
        "markets_scored": len(scores),
        "scores": scores,
    }


def main(argv):
    if len(argv) != 2:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "error": "usage: crypto_numeric_market_scorer.py <crypto_numeric_fixture_file>",
                },
                separators=(",", ":"),
            )
        )
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(score_fixture(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

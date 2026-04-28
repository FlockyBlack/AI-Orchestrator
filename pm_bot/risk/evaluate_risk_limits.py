import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_risk_limits(payload):
    limits = payload["limits"]
    positions = list(payload["positions"])
    total_notional = round(sum(float(item["notional"]) for item in positions), 2)
    largest_position = round(max(float(item["notional"]) for item in positions), 2) if positions else 0.0
    market_count = len({item["market_id"] for item in positions})
    category_count = len({item["category"] for item in positions})

    breaches = []
    if total_notional > float(limits["max_total_notional"]):
        breaches.append("max_total_notional")
    if largest_position > float(limits["max_position_notional"]):
        breaches.append("max_position_notional")
    if market_count > int(limits["max_open_markets"]):
        breaches.append("max_open_markets")
    if category_count > int(limits["max_category_exposure_count"]):
        breaches.append("max_category_exposure_count")

    return {
        "schema_version": "v1",
        "evaluation_mode": "offline_fixture",
        "position_count": len(positions),
        "market_count": market_count,
        "category_count": category_count,
        "total_notional": total_notional,
        "largest_position_notional": largest_position,
        "breaches": breaches,
        "approved": not breaches,
        "execution_allowed": False,
        "trading_allowed": False,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: evaluate_risk_limits.py <risk_fixture_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(evaluate_risk_limits(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

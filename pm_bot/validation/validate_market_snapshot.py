import json
import sys
from pathlib import Path

REQUIRED_KEYS = [
    "market_id",
    "slug",
    "title",
    "category",
    "outcomes",
    "prices",
    "liquidity",
    "volume",
    "close_time",
    "source_type",
    "collected_at",
    "risk_notes",
]
FORBIDDEN_KEYS = {
    "network",
    "api_url",
    "live_market_id",
    "wallet_address",
    "private_key",
    "order_payload",
    "execution_mode",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_snapshot(path: str):
    data = _load_json(Path(path))
    errors = []

    if not isinstance(data, dict):
        errors.append("snapshot_must_be_object")
        data = {}

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing:{key}")

    forbidden_present = sorted(FORBIDDEN_KEYS.intersection(data.keys()))
    for key in forbidden_present:
        errors.append(f"forbidden_field:{key}")

    outcomes = data.get("outcomes")
    if "outcomes" in data:
        if not isinstance(outcomes, list):
            errors.append("outcomes_must_be_list")
            outcomes = []
        elif len(outcomes) < 2:
            errors.append("outcomes_requires_at_least_two")

    prices = data.get("prices")
    if "prices" in data:
        if not isinstance(prices, dict):
            errors.append("prices_must_be_object")
            prices = {}
        elif isinstance(outcomes, list):
            for outcome in outcomes:
                if outcome not in prices:
                    errors.append(f"missing_price:{outcome}")

    if data.get("source_type") != "fixture":
        errors.append("source_type_must_be_fixture")

    result = {
        "status": "valid" if not errors else "invalid",
        "file": str(Path(path)),
        "errors": errors,
        "outcome_count": len(outcomes) if isinstance(outcomes, list) else 0,
        "source_type": data.get("source_type"),
        "offline_only": True,
    }
    return result


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "file": None, "errors": ["usage: validate_market_snapshot.py <file>"], "outcome_count": 0, "source_type": None, "offline_only": True}, separators=(",", ":")))
        return 2
    result = validate_snapshot(argv[1])
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

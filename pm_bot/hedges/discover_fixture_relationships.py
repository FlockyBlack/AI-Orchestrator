import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def discover_relationships(markets):
    relationships = []
    ordered_markets = sorted(markets, key=lambda item: item["market_id"])
    for index, left in enumerate(ordered_markets):
        for right in ordered_markets[index + 1:]:
            shared = []
            if left["event_key"] == right["event_key"]:
                shared.append(("shared_event_key", 0.95))
            if left["mutually_exclusive_group"] and left["mutually_exclusive_group"] == right["mutually_exclusive_group"]:
                shared.append(("mutually_exclusive_group", 0.91))
            for relationship_type, confidence in shared:
                relationships.append(
                    {
                        "left_market_id": left["market_id"],
                        "right_market_id": right["market_id"],
                        "relationship_type": relationship_type,
                        "confidence": confidence,
                        "research_only": True,
                        "execution_allowed": False,
                        "trading_allowed": False,
                    }
                )
    return {
        "schema_version": "v1",
        "market_count": len(ordered_markets),
        "relationship_count": len(relationships),
        "relationships": relationships,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: discover_fixture_relationships.py <fixture_related_markets_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(discover_relationships(payload["markets"]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

import argparse
import json
from pathlib import Path


def _parse_args():
    parser = argparse.ArgumentParser(description="Normalize a fixture market snapshot.")
    parser.add_argument("snapshot_path")
    parser.add_argument("--output")
    return parser.parse_args()


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_snapshot(snapshot):
    outcomes = list(snapshot["outcomes"])
    prices = {name: snapshot["prices"][name] for name in outcomes}
    price_sum = round(sum(prices.values()), 6)
    lowered = {value.strip().lower() for value in outcomes}
    has_binary_outcomes = lowered == {"yes", "no"}
    return {
        "schema_version": "v1",
        "market_id": snapshot["market_id"],
        "slug": snapshot["slug"],
        "title": snapshot["title"],
        "category": snapshot["category"],
        "outcomes": outcomes,
        "prices": prices,
        "liquidity": snapshot["liquidity"],
        "volume": snapshot["volume"],
        "close_time": snapshot["close_time"],
        "collected_at": snapshot["collected_at"],
        "outcome_count": len(outcomes),
        "price_sum": price_sum,
        "has_binary_outcomes": has_binary_outcomes,
        "normalized_source": "fixture_only",
        "risk_notes": list(snapshot["risk_notes"]),
    }


def _validate_output_path(output_path: Path, root: Path):
    allowed_root = (root / "pm_bot" / "normalization").resolve()
    resolved = output_path.resolve()
    try:
        resolved.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("--output must stay under pm_bot/normalization/") from exc


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    snapshot_path = Path(args.snapshot_path)
    if not snapshot_path.is_absolute():
        snapshot_path = (root / snapshot_path).resolve()
    normalized = normalize_snapshot(_load_json(snapshot_path))
    rendered = json.dumps(normalized, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (root / output_path).resolve()
        _validate_output_path(output_path, root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def calculate_fee_slippage(payload):
    quantity = int(payload["quantity"])
    entry_price = float(payload["entry_price"])
    exit_price = float(payload["exit_price"])
    fee_bps = int(payload["fee_bps"])
    slippage_bps = int(payload["slippage_bps"])

    gross_notional = round((entry_price + exit_price) * quantity, 4)
    fee_cost = round(gross_notional * (fee_bps / 10000), 4)
    slippage_cost = round(gross_notional * (slippage_bps / 10000), 4)
    total_cost = round(fee_cost + slippage_cost, 4)

    return {
        "schema_version": "v1",
        "accounting_mode": "offline_fixture",
        "market_id": payload["market_id"],
        "quantity": quantity,
        "gross_notional": gross_notional,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "fee_cost": fee_cost,
        "slippage_cost": slippage_cost,
        "total_cost": total_cost,
        "currency": "USD",
        "execution_allowed": False,
        "trading_allowed": False,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: calculate_fee_slippage.py <accounting_fixture_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(calculate_fee_slippage(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

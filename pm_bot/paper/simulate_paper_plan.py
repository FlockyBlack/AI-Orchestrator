import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def simulate_paper_plan(plan):
    entry_price = float(plan["entry_price"])
    exit_price = float(plan["exit_price"])
    quantity = int(plan["quantity"])
    slippage_bps = int(plan["assumed_slippage_bps"])
    side = plan["side"].lower()

    slippage = round(slippage_bps / 10000, 4)
    if side == "buy":
        effective_entry = round(entry_price + slippage, 4)
        effective_exit = round(exit_price - slippage, 4)
        gross_pnl = round((effective_exit - effective_entry) * quantity, 4)
    else:
        effective_entry = round(entry_price - slippage, 4)
        effective_exit = round(exit_price + slippage, 4)
        gross_pnl = round((effective_entry - effective_exit) * quantity, 4)

    return {
        "schema_version": "v1",
        "simulation_mode": "paper_only",
        "market_id": plan["market_id"],
        "side": side,
        "quantity": quantity,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "assumed_slippage_bps": slippage_bps,
        "effective_entry_price": effective_entry,
        "effective_exit_price": effective_exit,
        "gross_pnl": gross_pnl,
        "currency": "USD",
        "execution_allowed": False,
        "trading_allowed": False,
        "custody_access_required": False,
        "credential_material_required": False,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: simulate_paper_plan.py <paper_plan_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(simulate_paper_plan(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

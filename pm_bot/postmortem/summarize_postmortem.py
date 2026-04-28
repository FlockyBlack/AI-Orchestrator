import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize_postmortem(payload):
    gross_pnl = float(payload["gross_pnl"])
    total_cost = float(payload["total_cost"])
    net_pnl = round(gross_pnl - total_cost, 4)
    breach_count = len(payload["risk_breaches"])
    grade = "pass" if net_pnl > 0 and breach_count == 0 else "review"
    return {
        "schema_version": "v1",
        "postmortem_mode": "offline_fixture",
        "market_id": payload["market_id"],
        "net_pnl": net_pnl,
        "risk_breach_count": breach_count,
        "grade": grade,
        "key_findings": [
            f"net_pnl:{net_pnl:.4f}",
            f"risk_breach_count:{breach_count}",
            f"decision_basis:{payload['decision_basis']}",
        ],
        "recommended_action": "tighten_limits_before_any_future_paper_iteration" if breach_count else "retain_current_limits",
        "execution_allowed": False,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: summarize_postmortem.py <postmortem_fixture_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(summarize_postmortem(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

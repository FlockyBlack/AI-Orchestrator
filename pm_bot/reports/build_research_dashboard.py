import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_research_dashboard(payload):
    signal = payload["signal"]
    risk = payload["risk"]
    accounting = payload["accounting"]
    paper = payload["paper"]

    headline = f"{signal['lead_outcome']} leads at {signal['confidence']:.2f} confidence"
    gates = {
        "research_only": signal["recommendation_type"] == "research_only",
        "risk_approved": risk["approved"],
        "execution_blocked": not (
            signal["execution_allowed"] or risk["execution_allowed"] or accounting["execution_allowed"] or paper["execution_allowed"]
        ),
    }
    return {
        "schema_version": "v1",
        "dashboard_mode": "offline_fixture",
        "market_id": signal["market_id"],
        "headline": headline,
        "lead_outcome": signal["lead_outcome"],
        "confidence": signal["confidence"],
        "gross_pnl": paper["gross_pnl"],
        "total_cost": accounting["total_cost"],
        "net_pnl_after_costs": round(paper["gross_pnl"] - accounting["total_cost"], 4),
        "risk_breaches": list(risk["breaches"]),
        "safety_gates": gates,
        "trading_allowed": False,
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "error": "usage: build_research_dashboard.py <dashboard_fixture_file>"}, separators=(",", ":")))
        return 2
    payload = _load_json(Path(argv[1]))
    print(json.dumps(build_research_dashboard(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

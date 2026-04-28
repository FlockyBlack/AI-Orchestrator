import argparse
import json
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "execution_allowed": False,
    "trading_allowed": False,
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build the PMBOT crypto numeric operator review table.")
    parser.add_argument("score_report", help="Path to crypto numeric scorer JSON output.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _short_reason(row):
    reasons = []
    if float(row["edge_after_buffer"]) <= 0:
        reasons.append("buffered edge is not positive")
    elif row["decision"] == "paper_candidate":
        reasons.append("positive buffered edge clears review gates")
    elif row["decision"] == "watchlist":
        reasons.append("positive buffered edge needs operator review")

    if row["liquidity_status"] == "fail":
        reasons.append("liquidity gate failed")
    elif row["liquidity_status"] == "watch":
        reasons.append("liquidity needs review")
    if row["spread_status"] == "fail":
        reasons.append("spread gate failed")
    elif row["spread_status"] == "watch":
        reasons.append("spread needs review")
    if row["risk_status"] == "fail":
        reasons.append("risk gate failed")
    elif row["risk_status"] == "watch":
        reasons.append("risk needs review")

    return "; ".join(reasons) if reasons else "operator review only"


def _review_row(row):
    return {
        "market_id": row["market_id"],
        "asset": row["asset"],
        "side": row["side"],
        "market_probability": row["market_probability"],
        "model_probability": row["model_probability"],
        "edge_after_buffer": row["edge_after_buffer"],
        "liquidity_status": row["liquidity_status"],
        "spread_status": row["spread_status"],
        "risk_status": row["risk_status"],
        "decision": row["decision"],
        "short_reason": _short_reason(row),
    }


def build_review_table(score_report):
    rows = [_review_row(row) for row in score_report["scores"]]
    group_counts = {
        "paper_candidate": sum(1 for row in rows if row["decision"] == "paper_candidate"),
        "watchlist": sum(1 for row in rows if row["decision"] == "watchlist"),
        "reject": sum(1 for row in rows if row["decision"] == "reject"),
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-002-CRYPTO-NUMERIC-REVIEW-TABLE",
        "source_report_id": score_report["report_id"],
        "fixture_id": score_report["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "operator_review_only": True,
        "group_counts": group_counts,
        "rows": rows,
        "review_note": "Output is for paper-only operator review. No execution, trading, order placement, or runtime action is allowed.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Crypto Numeric Review Table",
        "",
        "Paper-only operator review table for deterministic crypto numeric scorer output.",
        "",
        f"- Paper candidates: {report['group_counts']['paper_candidate']}",
        f"- Watchlist: {report['group_counts']['watchlist']}",
        f"- Rejected: {report['group_counts']['reject']}",
        "",
        "| market_id | asset | side | market_probability | model_probability | edge_after_buffer | liquidity | spread | risk | decision | short_reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['market_probability']:.4f} | "
            f"{row['model_probability']:.4f} | {row['edge_after_buffer']:.4f} | {row['liquidity_status']} | "
            f"{row['spread_status']} | {row['risk_status']} | {row['decision']} | {row['short_reason']} |"
        )
    lines.extend(["", f"- {report['review_note']}", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    score_report = _load_json(Path(args.score_report))
    report = build_review_table(score_report)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
